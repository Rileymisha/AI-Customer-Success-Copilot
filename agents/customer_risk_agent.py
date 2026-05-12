# -*- coding: utf-8 -*-
"""
客户风险分析代理（Customer Risk Analysis Agent）
=================================================

使用 DeepSeek 大模型对客户进行多维度风险分析。

典型用法::

    from agents.customer_risk_agent import CustomerRiskAgent
    from src.ai_cs_copilot.pipelines.customer_analytics import load_customer_csv

    df = load_customer_csv(Path("data/sample_customer_data.csv"))
    agent = CustomerRiskAgent()
    results = agent.analyze(df)
    agent.save_report(results, Path("reports/risk_analysis_report.md"))
"""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from src.ai_cs_copilot.config import settings
from src.ai_cs_copilot.pipelines.customer_analytics import (
    annotate_risk_levels,
    load_customer_csv,
)

try:
    from src.ai_cs_copilot.services.rag_service import RAGService

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("RAGService 导入失败，RAG 功能不可用")

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ===========================================================================
# Prompt 模板（集中管理，便于后续评审与迭代）
# ===========================================================================

_SYSTEM_PROMPT: str = (
    "你是一名资深的客户成功经理（Customer Success Manager），"
    "在 B2B SaaS 公司工作超过 10 年，负责过多个年客单价百万级的客户群体。\n"
    "\n"
    "## 核心能力\n"
    "- 通过客户行为数据预判流失风险\n"
    "- 制定数据驱动的客户经营策略\n"
    "- 设计可量化的客户运营动作\n"
    "\n"
    "## 分析原则\n"
    "1. 数据驱动：每一个结论都必须有具体数据支撑，引用客户的实际指标\n"
    "2. 风险优先：优先识别可能流失的高风险客户，分析其根本原因\n"
    "3. 价值导向：兼顾客户价值与风险，制定差异化策略\n"
    "4. 可执行性：所有经营建议和运营动作必须是具体、可操作的\n"
    "\n"
    "## 输出要求\n"
    "- 严格按照 JSON 格式输出，不要包含其他文字\n"
    "- 风险评分范围 0-100，分数越高表示风险越大\n"
    "- 高风险客户评分 >= 60，中风险 30-59，低风险 < 30\n"
    "- 风险原因必须引用具体指标数值（如：登录天数仅 3 天）\n"
    "- 经营建议需包含短期（1-4 周）和长期（1-3 个月）两个层面\n"
    "- 客户运营动作需具体到执行方式（如「安排产品培训」、「高层电话回访」等可落地动作）"
)

_USER_PROMPT_HEADER: str = (
    "请分析以下 {count} 个客户的数据，为每位客户输出风险评估结果。\n"
    "\n"
    "## 风险判定规则\n"
    "| 维度 | 判定条件 | 风险等级 |\n"
    "|---|---|---|\n"
    "| 登录活跃度 | login_days < 5 | 高 |\n"
    "| 登录活跃度 | 5 <= login_days < 10 | 中 |\n"
    "| 功能采用 | ticket_usage_rate < 20% 且 marketing_usage_rate < 20% | 高 |\n"
    "| 功能采用 | ticket_usage_rate < 40% 或 marketing_usage_rate < 30% | 中 |\n"
    "| 续费状态 | renewal_days_left < 0（已逾期） | 高 |\n"
    "| 续费状态 | 0 <= renewal_days_left < 30（即将到期） | 中 |\n"
    "| 投诉情况 | complaint_count > 8 | 高 |\n"
    "| 投诉情况 | complaint_count > 3 | 中 |\n"
    "| 客户价值 | monthly_gmv >= 200000 且 login_days >= 20 且 ticket_usage_rate >= 80% 且 complaint_count <= 1 | 高价值 |\n"
    "\n"
    "## 客户数据\n"
    "{customer_data}\n\n"
)

_USER_PROMPT_FOOTER: str = """\
请严格按照以下格式输出 JSON 数组，不要包含任何其他文字：

```json
[
  {
    "customer_name": "客户名称",
    "risk_level": "高/中/低",
    "customer_type": "高价值/正常/高风险",
    "risk_score": 0-100,
    "risk_reason": "风险原因描述，必须引用具体指标数值",
    "business_suggestion": "经营建议，包含短期和长期策略",
    "customer_actions": [
      "具体行动1（含执行方式）",
      "具体行动2（含执行方式）",
      "具体行动3（含执行方式）"
    ]
  }
]
```"""


# ===========================================================================
# 内部工具函数
# ===========================================================================


def _format_as_markdown_table(df: pd.DataFrame) -> str:
    """
    将 DataFrame 格式化为 Markdown 表格。

    只包含风险分析相关的核心字段，避免依赖 tabulate 第三方包。
    """
    cols = [
        "customer_name", "industry", "monthly_gmv", "login_days",
        "ticket_usage_rate", "marketing_usage_rate", "employee_count",
        "renewal_days_left", "complaint_count", "region", "risk_level",
    ]
    available = [c for c in cols if c in df.columns]
    if not available:
        raise ValueError("DataFrame 中不包含任何可用于分析的字段")

    header = "| " + " | ".join(available) + " |"
    separator = "| " + " | ".join(["---"] * len(available)) + " |"

    rows: list[str] = []
    for _, row in df[available].iterrows():
        cells = []
        for col in available:
            val = row[col]
            cells.append("" if pd.isna(val) else str(val))
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header, separator] + rows)


def _extract_json(text: str) -> list[dict[str, Any]]:
    """
    从 LLM 回复中提取 JSON 数组，兼容多种返回格式。

    处理顺序：
    1. 直接解析纯 JSON 文本
    2. 从 ```json ... ``` 代码块中提取
    3. 从 ``` ... ``` 代码块中提取
    4. 从文本中正则匹配顶层 [...] 数组
    """
    text = text.strip()

    # 1. 直接解析
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # 2. ```json ... ``` 代码块
    for pattern in [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                parsed = json.loads(match.group(1).strip())
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                continue

    # 3. 正则匹配顶层 JSON 数组
    array_match = re.search(r'(\[[\s\S]*?\])', text)
    if array_match:
        try:
            parsed = json.loads(array_match.group(1).strip())
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass

    raise ValueError("无法从 LLM 回复中解析出有效的 JSON 数组")


def _validate_result_item(item: dict[str, Any]) -> list[str]:
    """校验单条结果的必填字段，返回缺失字段列表。"""
    required = [
        "customer_name", "risk_level", "customer_type",
        "risk_score", "risk_reason", "business_suggestion", "customer_actions",
    ]
    return [f for f in required if f not in item]


# ===========================================================================
# Agent 主类
# ===========================================================================


class CustomerRiskAgent:
    """
    AI 驱动的客户风险分析代理。

    使用 DeepSeek 大模型，结合规则预评分 + AI 深度分析的两阶段流程，
    对客户数据进行多维度风险评估。

    **输入**: 包含客户指标（login_days、monthly_gmv、complaint_count 等）的 DataFrame
    **输出**: 结构化分析结果列表（JSON），每项包含风险等级、原因、建议与运营动作

    使用示例::

        agent = CustomerRiskAgent()
        df = load_customer_csv(Path("data/sample_customer_data.csv"))
        results = agent.analyze(df)
        agent.save_report(results, Path("reports/risk_analysis_report.md"))

    启用 RAG 知识库增强::

        from src.ai_cs_copilot.services.rag_service import RAGService

        rag = RAGService()
        agent = CustomerRiskAgent(rag_service=rag)
        results = agent.analyze(df)
        # Agent 会自动检测客户问题并检索知识库，生成更有依据的建议
    """

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.1,
        max_retries: int = 2,
        rag_service: Any | None = None,
    ) -> None:
        """
        参数:
            model: DeepSeek 模型名（默认读取 settings.deepseek_model）
            temperature: 生成温度，越低越稳定（默认 0.1）
            max_retries: API 重试次数（默认 2）
            rag_service: RAGService 实例（可选），传入后 Agent 会自动检索知识库
        """
        self.model = model or settings.deepseek_model
        self.temperature = temperature
        self.max_retries = max_retries
        self._client: OpenAI | None = None
        self.rag_service = rag_service

    def _get_client(self) -> OpenAI:
        """懒加载创建 DeepSeek 客户端。"""
        if self._client is None:
            api_key = settings.deepseek_api_key
            if not api_key or api_key.strip().lower().startswith("sk-your"):
                raise ValueError(
                    "未配置有效的 DEEPSEEK_API_KEY，请在 .env 文件中设置"
                )
            self._client = OpenAI(
                api_key=api_key,
                base_url=settings.deepseek_base_url.rstrip("/"),
            )
        return self._client

    # ------------------------------------------------------------------
    # 核心分析
    # ------------------------------------------------------------------

    def _identify_issues_and_query_rag(self, df_with_risk: pd.DataFrame) -> str:
        """
        根据客户数据自动诊断问题类型，检索知识库获取参考信息。

        检测维度：
        - 登录天数低 → low_login_solutions.md
        - 投诉多 → customer_retention.md
        - 续约逾期/即将到期 → renewal_strategy.md
        - 营销功能使用率低 → marketing_growth.md

        参数:
            df_with_risk: 已标注风险的客户 DataFrame

        返回:
            知识库检索结果文本，用于注入 Prompt
        """
        if self.rag_service is None:
            return ""

        logger.info("正在检测客户问题并检索知识库...")
        context = self.rag_service.diagnose_and_retrieve(df_with_risk)
        if context:
            logger.info("知识库检索完成，找到相关参考内容")
        else:
            logger.info("未找到匹配的知识库内容")
        return context

    def analyze(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        对全部客户进行风险分析。

        **处理流程**:
        1. 校验输入数据完整
        2. 规则预评分（调用 customer_analytics.annotate_risk_levels）
        3. 格式化数据 → 构造 Prompt
        4. 调用 DeepSeek 进行 AI 深度分析
        5. 解析并校验返回的 JSON 结果

        参数:
            df: 客户数据，需包含以下字段：
                - customer_name, industry, monthly_gmv, login_days
                - ticket_usage_rate, marketing_usage_rate
                - renewal_days_left, complaint_count

        返回:
            分析结果列表，每个元素的结构：:

                {
                    "customer_name": "客户名称",
                    "risk_level": "高/中/低",
                    "customer_type": "高价值/正常/高风险",
                    "risk_score": 0-100,
                    "risk_reason": "风险原因",
                    "business_suggestion": "经营建议",
                    "customer_actions": ["行动1", "行动2", ...]
                }
        """
        # ---------- 输入校验 ----------
        if df is None or df.empty:
            raise ValueError("输入数据为空，请先加载客户数据")

        required_cols = [
            "customer_name", "monthly_gmv", "login_days",
            "ticket_usage_rate", "marketing_usage_rate",
            "renewal_days_left", "complaint_count", "industry",
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"数据缺少必要字段：{', '.join(missing)}")

        # ---------- 规则预评分 ----------
        logger.info("正在进行规则预评分...")
        df_with_risk = annotate_risk_levels(df)
        high_count = len(df_with_risk[df_with_risk["risk_level"] == "高"])
        logger.info("规则评分完成：高风险 %d 个，总计 %d 个客户", high_count, len(df_with_risk))

        # ---------- 数据格式化 ----------
        customer_data_text = _format_as_markdown_table(df_with_risk)
        logger.debug("格式化后的客户数据：\n%s", customer_data_text)

        # ---------- RAG 知识库检索（Agent 分析前先查知识库） ----------
        rag_context = self._identify_issues_and_query_rag(df_with_risk)

        # ---------- AI 深度分析（注入 RAG 上下文） ----------
        logger.info("正在调用 DeepSeek（%s）进行 AI 风险分析...", self.model)
        raw_response = self._call_llm(customer_data_text, len(df_with_risk), rag_context=rag_context)

        # ---------- JSON 解析 ----------
        logger.info("正在解析 AI 分析结果...")
        results = _extract_json(raw_response)
        logger.info("成功解析 %d 条分析结果", len(results))

        # ---------- 字段完整性校验 ----------
        for item in results:
            missing_fields = _validate_result_item(item)
            if missing_fields:
                logger.warning(
                    "客户 %s 缺少字段：%s",
                    item.get("customer_name", "未知"),
                    ", ".join(missing_fields),
                )

        return results

    def _call_llm(self, customer_data_text: str, count: int, rag_context: str = "") -> str:
        """
        调用 DeepSeek Chat API，包含自动重试逻辑。

        参数:
            customer_data_text: Markdown 格式的客户数据
            count: 客户数量
            rag_context: 知识库检索结果（可选），注入 Prompt 增强生成质量

        返回:
            LLM 返回的原始文本

        异常:
            ValueError: 鉴权失败或重试耗尽时抛出
        """
        user_prompt_parts = [
            _USER_PROMPT_HEADER.format(
                count=count, customer_data=customer_data_text,
            ),
        ]

        # 注入 RAG 知识库参考内容（让 LLM 优先参考）
        if rag_context:
            user_prompt_parts.extend([
                rag_context,
                "",
                "请优先参考以上知识库内容来制定客户策略，并结合实际客户数据给出具体建议。\n",
            ])

        user_prompt_parts.append(_USER_PROMPT_FOOTER)
        user_prompt = "".join(user_prompt_parts)

        client = self._get_client()
        last_error: Exception | None = None

        for attempt in range(1 + self.max_retries):
            if attempt > 0:
                logger.info("正在重试（第 %d/%d 次）...", attempt, self.max_retries)

            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    timeout=180.0,
                )

                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("模型返回内容为空")

                return content.strip()

            except AuthenticationError as exc:
                logger.error("DeepSeek 鉴权失败：%s", exc)
                raise ValueError(
                    "DeepSeek 鉴权失败，请检查 DEEPSEEK_API_KEY 是否正确"
                ) from exc

            except (RateLimitError, APITimeoutError, APIConnectionError) as exc:
                logger.warning("API 调用失败（第 %d 次）：%s — %s", attempt + 1, type(exc).__name__, exc)
                last_error = exc

            except APIError as exc:
                logger.error("DeepSeek API 错误：%s", exc)
                last_error = exc

        raise ValueError(
            f"调用 DeepSeek 失败（已重试 {self.max_retries} 次）：{last_error}"
        )

    # ------------------------------------------------------------------
    # 报告输出
    # ------------------------------------------------------------------

    @staticmethod
    def generate_markdown_report(results: list[dict[str, Any]]) -> str:
        """
        将分析结果生成为可读的 Markdown 报告。

        参数:
            results: analyze() 返回的分析结果列表

        返回:
            Markdown 格式的完整报告文本
        """
        lines: list[str] = [
            "# 客户风险分析报告",
            "",
            f"**生成时间**：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**分析客户数**：{len(results)}",
            "",
            "---",
            "",
        ]

        # ---- 统计概览 ----
        high_risk = [r for r in results if r.get("risk_level") == "高"]
        mid_risk = [r for r in results if r.get("risk_level") == "中"]
        low_risk = [r for r in results if r.get("risk_level") == "低"]
        high_value = [r for r in results if r.get("customer_type") == "高价值"]

        lines.append("## 一、分析概览\n")
        lines.append("| 指标 | 数量 |")
        lines.append("|---|---|")
        lines.append(f"| 高风险客户 | {len(high_risk)} |")
        lines.append(f"| 中风险客户 | {len(mid_risk)} |")
        lines.append(f"| 低风险客户 | {len(low_risk)} |")
        lines.append(f"| 高价值客户 | {len(high_value)} |")
        lines.append("")

        # ---- 高风险客户详情 ----
        if high_risk:
            lines.append("## 二、高风险客户详情\n")
            for r in high_risk:
                actions = r.get("customer_actions", [])
                actions_text = "\n".join(
                    f"{i+1}. {a}" for i, a in enumerate(actions)
                )
                lines.extend([
                    f"### {r.get('customer_name', '未知')}",
                    "",
                    f"- **风险评分**：{r.get('risk_score', 'N/A')}",
                    f"- **风险原因**：{r.get('risk_reason', 'N/A')}",
                    "",
                    "**经营建议**：",
                    r.get('business_suggestion', 'N/A'),
                    "",
                    "**建议运营动作**：",
                    actions_text,
                    "",
                ])

        # ---- 高价值客户 ----
        if high_value:
            lines.append("## 三、高价值客户\n")
            for r in high_value:
                lines.append(
                    f"- **{r.get('customer_name', '未知')}**"
                    f" — {r.get('business_suggestion', '')}"
                )
            lines.append("")

        # ---- 总结 ----
        lines.append("## 四、总结与行动建议\n")
        if high_risk:
            lines.append(
                f"需立即对 **{len(high_risk)} 个高风险客户** 启动挽回流程，"
                "由 CSM 主管和销售总监联合跟进。\n"
            )
        if high_value:
            lines.append(
                f"对 **{len(high_value)} 个高价值客户** 安排季度复盘，"
                "确保客户满意度，预防竞对撬动。\n"
            )

        return "\n".join(lines)

    def save_report(
        self,
        results: list[dict[str, Any]],
        output_path: str | Path,
        fmt: str = "markdown",
    ) -> Path:
        """
        将分析结果保存到文件。

        参数:
            results: analyze() 返回的结果列表
            output_path: 输出文件路径
            fmt: 输出格式 — "markdown"（默认）或 "json"

        返回:
            实际写入的文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            content = json.dumps(results, ensure_ascii=False, indent=2)
        else:
            content = self.generate_markdown_report(results)

        output_path.write_text(content, encoding="utf-8")
        logger.info("风险分析报告已保存到：%s", output_path)
        return output_path


# ===========================================================================
# 独立运行入口
# ===========================================================================


def main() -> None:
    """
    命令行入口：从 data/sample_customer_data.csv 加载数据，
    运行全量分析，同时输出 JSON 结果和 Markdown 报告。
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    csv_path = Path("data/sample_customer_data.csv")
    if not csv_path.exists():
        logger.error("找不到客户数据文件：%s", csv_path)
        sys.exit(1)

    logger.info("正在加载客户数据：%s", csv_path)
    df = load_customer_csv(csv_path)

    # 初始化 RAG 知识库（可选，因此处只为演示，异常不影响主流程）
    rag = None
    if RAG_AVAILABLE:
        try:
            from src.ai_cs_copilot.services.rag_service import RAGService

            rag = RAGService()
            logger.info("RAG 知识库初始化成功")
        except Exception as exc:
            logger.warning("RAG 知识库初始化失败（不影响主流程）：%s", exc)

    agent = CustomerRiskAgent(rag_service=rag)
    try:
        results = agent.analyze(df)
    except Exception as exc:
        logger.error("分析失败：%s", exc)
        sys.exit(1)

    # 保存 JSON 原始结果
    json_path = Path("reports/risk_analysis_results.json")
    agent.save_report(results, json_path, fmt="json")

    # 保存 Markdown 可读报告
    md_path = Path("reports/risk_analysis_report.md")
    agent.save_report(results, md_path, fmt="markdown")

    print(f"\n分析完成！共分析 {len(results)} 个客户。")
    print(f"  - JSON 结果：{json_path}")
    print(f"  - Markdown 报告：{md_path}")


if __name__ == "__main__":
    main()

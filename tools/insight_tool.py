# -*- coding: utf-8 -*-
"""
AI 经营洞察生成工具（Insight Generation Tool）
=============================================

调用 DeepSeek LLM，基于已分析的客户数据生成结构化经营洞察，
包括执行摘要、风险分析、分层策略和行动计划建议。

设计原则:
    - 非关键工具：API 调用失败时降级，不影响管线其他步骤
    - 数据驱动：所有洞察必须引用实际数据，禁止编造
    - 结构化输出：生成的内容可直接用于 Markdown 报告和 PPT

Tool Calling 注册:
    name: "insight_generation"
    依赖: data_analysis 的输出（df_annotated, categories）
    产出: context.insights（结构化洞察文本）
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd

from tools.base_tool import BaseTool, ToolError, ToolParameter, ToolSpec

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt 模板
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "你是一名资深客户成功经理（Customer Success Manager），"
    "擅长 B2B SaaS 客户经营分析与策略制定。\n"
    "\n"
    "## 核心能力\n"
    "- 通过客户行为数据预判流失风险\n"
    "- 制定数据驱动的分层经营策略\n"
    "- 设计可量化的跟进计划\n"
    "\n"
    "## 输出要求\n"
    "1. 每个结论必须有具体数据支撑\n"
    "2. 区分短期（本周）和长期（本月）行动\n"
    "3. 语言简洁、专业、适合管理层阅读\n"
    "4. 严格按照 Markdown 格式输出"
)

_USER_PROMPT_TEMPLATE = (
    "请基于以下客户经营数据，生成一份结构化的经营洞察分析。\n"
    "\n"
    "---\n"
    "{customer_summary}\n"
    "---\n"
    "\n"
    "请按以下结构输出（Markdown 格式）：\n"
    "\n"
    "## 经营概况\n"
    "用 2-3 句话概括整体经营状况，包括客户总数、月均 GMV、行业分布等关键指标。\n"
    "\n"
    "## 风险分析\n"
    "- 高风险客户数量与特征总结（提到具体指标，如登录天数、投诉数）\n"
    "- 中风险客户的主要风险类型\n"
    "- 整体风险趋势判断\n"
    "\n"
    "## 分层经营策略\n"
    "- 高风险客户：具体挽回策略和跟进节奏\n"
    "- 高价值客户：维护策略和预防竞对撬动\n"
    "- 增长潜力客户：uplift 策略和辅导计划\n"
    "\n"
    "## 重点客户清单\n"
    "列出 TOP 5 需重点关注客户，每个客户包含：\n"
    "- 客户名称、行业、风险等级\n"
    "- 核心问题（引用具体数据）\n"
    "- 建议动作\n"
    "\n"
    "## 本周行动计划\n"
    "列出 3-5 条本周内可执行的具体行动项，含负责人建议和优先级。"
)


def _build_customer_summary(
    df: pd.DataFrame,
    categories: dict[str, Any],
) -> str:
    """将分析结果压缩为 LLM 提示词用的摘要文本。"""
    lines = [f"### 客户数据概览（共 {len(df)} 个客户）"]

    # 基本统计
    avg_gmv = df["monthly_gmv"].mean()
    risk_counts = df["risk_level"].value_counts().to_dict()
    lines.append(f"- 月均 GMV：¥{avg_gmv:,.0f}")
    lines.append(f"- 行业数：{df['industry'].nunique()}  |  区域数：{df['region'].nunique()}")
    lines.append(f"- 高风险：{risk_counts.get('高', 0)} 个")
    lines.append(f"- 中风险：{risk_counts.get('中', 0)} 个")
    lines.append(f"- 低风险：{risk_counts.get('低', 0)} 个")

    # 分类统计
    high_risk = categories.get("high_risk", [])
    high_value = categories.get("high_value", [])
    growth = categories.get("growth", [])
    lines.append(f"- 高价值客户：{len(high_value)} 个")
    lines.append(f"- 增长潜力客户：{len(growth)} 个")

    # 高风险客户详情
    if high_risk:
        lines.append("\n### 高风险客户明细")
        for c in high_risk[:10]:
            name = c.get("customer_name", "")
            industry = c.get("industry", "")
            gmv = c.get("monthly_gmv", 0)
            login = c.get("login_days", 0)
            complaints = c.get("complaint_count", 0)
            renewal = c.get("renewal_days_left", 0)
            lines.append(
                f"- {name}（{industry}）| "
                f"GMV ¥{gmv:,} | 登录 {login}天 | "
                f"投诉 {complaints}次 | 续约 {renewal}天"
            )

    # 高价值客户
    if high_value:
        lines.append("\n### 高价值客户")
        for c in high_value[:5]:
            name = c.get("customer_name", "")
            industry = c.get("industry", "")
            gmv = c.get("monthly_gmv", 0)
            lines.append(f"- {name}（{industry}）| GMV ¥{gmv:,}")

    return "\n".join(lines)


class InsightGenerationTool(BaseTool):
    """
    AI 经营洞察生成工具。

    调用 DeepSeek LLM，基于客户数据分析结果生成结构化的
    经营洞察，包括风险分析、分层策略、行动计划等。
    """

    @property
    def name(self) -> str:
        return "insight_generation"

    @property
    def description(self) -> str:
        return (
            "AI 经营洞察生成工具：调用 DeepSeek 大模型，基于客户数据生成"
            "结构化的经营洞察，包含经营概况、风险分析、分层策略和行动计划。"
        )

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(
                    name="df",
                    type="object",
                    description="已标注风险等级的 DataFrame",
                    required=True,
                ),
                ToolParameter(
                    name="categories",
                    type="object",
                    description="客户分类结果",
                    required=True,
                ),
            ],
        )

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        生成 AI 经营洞察。

        参数:
            df: 已标注风险等级的 DataFrame
            categories: 客户分类结果

        返回:
            {
                "insights": "结构化洞察文本（Markdown）"
            }
        """
        df: pd.DataFrame | None = kwargs.get("df")
        categories: dict | None = kwargs.get("categories")

        if df is None or df.empty:
            raise ToolError("缺少有效的 DataFrame 参数")
        if not categories:
            raise ToolError("缺少有效的 categories 参数")

        # 检查 API 配置
        from src.ai_cs_copilot.config import settings

        api_key = settings.deepseek_api_key
        if not api_key or not api_key.strip() or api_key.strip().lower().startswith("sk-your"):
            logger.warning("DeepSeek API key 未配置，跳过 AI 洞察生成")
            return {
                "insights": "（AI 洞察：未配置 API Key，请设置 DEEPSEEK_API_KEY 后重新生成）",
            }

        # 构建摘要数据
        customer_summary = _build_customer_summary(df, categories)
        user_prompt = _USER_PROMPT_TEMPLATE.format(customer_summary=customer_summary)

        try:
            # 复用 llm_service 的 API 调用
            from src.ai_cs_copilot.services.llm_service import (
                LlmInvokeError,
                _create_deepseek_client,
            )

            client = _create_deepseek_client()
            model = settings.deepseek_model

            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                timeout=120.0,
            )

            content = completion.choices[0].message.content
            if not content or not content.strip():
                raise ToolError("模型返回内容为空")

            insights = content.strip()
            logger.info("AI 洞察生成成功（%d 字符）", len(insights))

            return {"insights": insights}

        except LlmInvokeError as exc:
            # API 配置/鉴权/限流错误 — 非关键失败，降级
            logger.warning("AI 洞察生成失败（降级）：%s", exc.user_message)
            return {
                "insights": (
                    "## AI 经营洞察\n\n"
                    f"（AI 洞察暂时不可用：{exc.user_message}）\n\n"
                    "请检查 API 配置后重新生成。以下为基于规则引擎的简要分析。"
                ),
            }

        except Exception as exc:
            logger.warning("AI 洞察生成异常（降级）：%s", exc)
            return {
                "insights": (
                    "## AI 经营洞察\n\n"
                    "（AI 洞察暂时不可用，请稍后重试）\n\n"
                    f"错误信息：{exc}"
                ),
            }

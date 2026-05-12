# -*- coding: utf-8 -*-
"""
企业报告工作流（Enterprise Report Workflow）
============================================

核心工作流调度器，将数据加载、分析、RAG 检索、AI 洞察、
图表与报告生成串联为一条可执行的 Pipeline。

工作流步骤::

    1. load_data          → 读取 CSV
    2. analyze_data       → 规则风险评分
    3. identify_risks     → 客户分类（高风险/高价值/增长）
    4. retrieve_knowledge → RAG 知识库检索（可选）
    5. generate_insights  → DeepSeek AI 经营洞察
    6. generate_charts    → matplotlib 可视化图表
    7. generate_report    → Markdown 企业报告
    8. generate_ppt       → PPT 演示文稿

用法::

    from workflows.report_workflow import ReportWorkflow

    wf = ReportWorkflow()
    ctx = wf.run("data/sample_customer_data.csv")
    # ctx.markdown_path → 报告路径
    # ctx.ppt_path      → PPT 路径
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from openai import OpenAI

from src.ai_cs_copilot.config import settings
from src.ai_cs_copilot.pipelines.customer_analytics import (
    annotate_risk_levels,
    load_customer_csv,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# 数据类：工作流上下文
# ===========================================================================


@dataclass
class WorkflowContext:
    """
    工作流上下文，贯穿整个 Pipeline。

    每个步骤将其输出写入此上下文，后续步骤从中读取。
    """

    # 输入
    data_source: str = "data/sample_customer_data.csv"

    # 各步骤输出
    df: pd.DataFrame | None = None
    df_annotated: pd.DataFrame | None = None
    categories: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    rag_context: str = ""
    insights: str = ""
    chart_paths: dict[str, str] = field(default_factory=dict)
    markdown_path: str = ""
    ppt_path: str = ""

    # 运行时
    errors: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class WorkflowStep:
    """工作流步骤定义。"""

    name: str
    description: str
    fn: Callable[[WorkflowContext], None]
    critical: bool = False  # True 表示此步骤失败则终止整个工作流


# ===========================================================================
# AI 洞察 Prompt
# ===========================================================================

_INSIGHT_SYSTEM_PROMPT: str = (
    "你是一名资深的客户成功策略分析师，负责为企业管理层撰写经营分析报告。\n"
    "请基于客户数据和分析结果，输出结构化经营洞察。\n"
    "\n"
    "输出必须包含以下五个部分（使用 Markdown 格式）：\n"
    "1. 执行摘要：用 3-5 句话概括核心结论\n"
    "2. 关键发现：列出 3-5 条数据驱动的洞察\n"
    "3. 风险分析：重点分析高风险客户的问题模式\n"
    "4. 经营建议：分短期和长期给出可执行建议\n"
    "5. 行动计划：列出具体步骤、负责人和时间节点\n"
    "\n"
    "要求：\n"
    "- 所有结论必须有数据支撑\n"
    "- 引用具体的客户数据和指标\n"
    "- 语言专业、简洁、可执行"
)


# ===========================================================================
# 工作流主类
# ===========================================================================


class ReportWorkflow:
    """
    企业报告工作流调度器。

    支持自定义步骤和灵活编排。默认注册 8 个步骤，
    可通过 ``add_step()`` 扩展或 ``steps`` 属性重新编排。
    """

    def __init__(self, rag_service: Any | None = None) -> None:
        """
        参数:
            rag_service: RAGService 实例（可选，用于知识库检索）
        """
        self.rag_service = rag_service
        self.steps: list[WorkflowStep] = []
        self._register_default_steps()

    def _register_default_steps(self) -> None:
        """注册默认工作流步骤。"""
        self.steps = [
            WorkflowStep("load_data", "加载客户数据", self._step_load_data, critical=True),
            WorkflowStep("analyze_data", "风险评分", self._step_analyze_data, critical=True),
            WorkflowStep("identify_risks", "客户分类", self._step_identify_risks, critical=True),
            WorkflowStep("retrieve_knowledge", "知识库检索", self._step_retrieve_knowledge, critical=False),
            WorkflowStep("generate_insights", "AI 经营洞察", self._step_generate_insights, critical=False),
            WorkflowStep("generate_charts", "生成图表", self._step_generate_charts, critical=False),
            WorkflowStep("generate_report", "生成 Markdown 报告", self._step_generate_report, critical=False),
            WorkflowStep("generate_ppt", "生成 PPT", self._step_generate_ppt, critical=False),
        ]

    def add_step(
        self,
        name: str,
        description: str,
        fn: Callable[[WorkflowContext], None],
        critical: bool = False,
    ) -> None:
        """添加自定义步骤。"""
        self.steps.append(WorkflowStep(name, description, fn, critical))

    # ------------------------------------------------------------------
    # 运行工作流
    # ------------------------------------------------------------------

    def run(self, data_source: str | None = None) -> WorkflowContext:
        """
        执行完整工作流。

        参数:
            data_source: CSV 文件路径（默认使用 settings 中的配置）

        返回:
            包含所有步骤输出的 WorkflowContext

        异常:
            如果 critical 步骤失败则抛出异常
        """
        ctx = WorkflowContext()
        if data_source:
            ctx.data_source = data_source

        logger.info("=" * 60)
        logger.info("企业报告工作流启动 — %d 个步骤", len(self.steps))
        logger.info("=" * 60)

        for step in self.steps:
            logger.info("[%s] %s ...", step.name, step.description)
            try:
                step.fn(ctx)
                logger.info("[%s] 完成 ✓", step.name)
            except Exception as exc:
                ctx.errors.append((step.name, str(exc)))
                logger.error("[%s] 失败: %s", step.name, exc)
                if step.critical:
                    logger.critical("关键步骤失败，终止工作流")
                    raise
                logger.warning("非关键步骤失败，继续执行")

        # 输出摘要
        logger.info("=" * 60)
        logger.info("工作流完成")
        logger.info("  Markdown 报告: %s", ctx.markdown_path or "(未生成)")
        logger.info("  PPT: %s", ctx.ppt_path or "(未生成)")
        if ctx.errors:
            logger.warning("  异常步骤: %d 个", len(ctx.errors))
        logger.info("=" * 60)

        return ctx

    # ------------------------------------------------------------------
    # 各步骤实现
    # ------------------------------------------------------------------

    def _step_load_data(self, ctx: WorkflowContext) -> None:
        """步骤 1：加载客户数据。"""
        csv_path = Path(ctx.data_source)
        if not csv_path.exists():
            # 尝试从项目根目录查找
            csv_path = Path(".") / ctx.data_source
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {ctx.data_source}")

        ctx.df = load_customer_csv(csv_path)
        ctx.data_source = str(csv_path)
        logger.info("加载 %d 条客户记录", len(ctx.df))

    def _step_analyze_data(self, ctx: WorkflowContext) -> None:
        """步骤 2：规则风险评分。"""
        if ctx.df is None:
            raise ValueError("数据未加载")

        ctx.df_annotated = annotate_risk_levels(ctx.df)
        risk_counts = ctx.df_annotated["risk_level"].value_counts()
        logger.info("风险分布: %s", risk_counts.to_dict())

    def _step_identify_risks(self, ctx: WorkflowContext) -> None:
        """步骤 3：客户分类。"""
        if ctx.df_annotated is None:
            raise ValueError("数据未分析")

        df = ctx.df_annotated

        # 高风险客户
        high_risk_df = df[df["risk_level"] == "高"]
        ctx.categories["high_risk"] = high_risk_df.to_dict("records")

        # 高价值客户：GMV >= 200k + 高活跃 + 高采用 + 低投诉
        high_value_df = df[
            (df["monthly_gmv"] >= 200000)
            & (df["login_days"] >= 20)
            & (df["ticket_usage_rate"] >= 80)
            & (df["complaint_count"] <= 1)
        ]
        ctx.categories["high_value"] = high_value_df.to_dict("records")

        # 增长客户：GMV 8-18 万 + 活跃 >= 15 + 采用率 >= 60 + 低投诉
        growth_df = df[
            (df["monthly_gmv"] >= 80000)
            & (df["monthly_gmv"] < 200000)
            & (df["login_days"] >= 15)
            & (df["ticket_usage_rate"] >= 60)
            & (df["complaint_count"] <= 2)
        ]
        ctx.categories["growth"] = growth_df.to_dict("records")

        logger.info(
            "分类: 高风险 %d, 高价值 %d, 增长 %d",
            len(ctx.categories["high_risk"]),
            len(ctx.categories["high_value"]),
            len(ctx.categories["growth"]),
        )

    def _step_retrieve_knowledge(self, ctx: WorkflowContext) -> None:
        """步骤 4：RAG 知识库检索（可选）。"""
        if self.rag_service is None or ctx.df_annotated is None:
            ctx.rag_context = ""
            return

        logger.info("正在检索知识库...")
        ctx.rag_context = self.rag_service.diagnose_and_retrieve(ctx.df_annotated)
        if ctx.rag_context:
            logger.info("知识库检索成功，获取 %d 字参考内容", len(ctx.rag_context))
        else:
            logger.info("知识库未命中相关文档")

    def _step_generate_insights(self, ctx: WorkflowContext) -> None:
        """步骤 5：DeepSeek AI 经营洞察。"""
        if ctx.df_annotated is None:
            raise ValueError("数据未分析")

        # 构建概览文本
        df = ctx.df_annotated
        overview_lines = [
            f"客户总数: {len(df)}",
            f"行业数: {df['industry'].nunique()}",
            f"区域数: {df['region'].nunique()}",
            f"月均 GMV: ¥{df['monthly_gmv'].mean():,.0f}",
            f"高风险客户: {len(ctx.categories.get('high_risk', []))}",
            f"高价值客户: {len(ctx.categories.get('high_value', []))}",
            "",
            "风险分布:",
        ]
        for level in ["高", "中", "低"]:
            count = len(df[df["risk_level"] == level])
            overview_lines.append(f"  {level}: {count}")

        user_prompt = (
            f"## 客户数据概览\n"
            + "\n".join(overview_lines)
            + "\n\n"
            + (
                f"## 知识库参考\n{ctx.rag_context}\n\n"
                if ctx.rag_context
                else ""
            )
            + "请基于以上数据输出经营洞察报告。"
        )

        # 调用 DeepSeek
        api_key = settings.deepseek_api_key
        if not api_key or "sk-your" in api_key.lower():
            ctx.insights = (
                "**AI 洞察不可用**：未配置有效的 DEEPSEEK_API_KEY。\n\n"
                "请配置 .env 文件中的 DEEPSEEK_API_KEY 后重试。"
            )
            return

        client = OpenAI(api_key=api_key, base_url=settings.deepseek_base_url.rstrip("/"))

        try:
            response = client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": _INSIGHT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                timeout=180.0,
            )
            ctx.insights = response.choices[0].message.content or ""
            logger.info("AI 洞察生成成功，%d 字", len(ctx.insights))
        except Exception as exc:
            logger.error("AI 洞察生成失败: %s", exc)
            ctx.insights = f"**AI 洞察生成失败**：{exc}\n\n请检查 API 配置后重试。"

    def _step_generate_charts(self, ctx: WorkflowContext) -> None:
        """步骤 6：生成可视化图表。"""
        if ctx.df_annotated is None:
            raise ValueError("数据未分析")

        try:
            from visualizations.chart_generator import ChartGenerator

            gen = ChartGenerator(output_dir="visualizations")
            ctx.chart_paths = gen.generate_all(ctx.df_annotated)
            logger.info("生成 %d 张图表", len(ctx.chart_paths))
        except ImportError as exc:
            logger.warning("图表生成依赖缺失: %s", exc)
            ctx.chart_paths = {}
        except Exception as exc:
            logger.error("图表生成失败: %s", exc)
            ctx.chart_paths = {}

    def _step_generate_report(self, ctx: WorkflowContext) -> None:
        """步骤 7：生成 Markdown 报告。"""
        if ctx.df_annotated is None:
            raise ValueError("数据未分析")

        try:
            from services.report_generator import ReportGenerator

            gen = ReportGenerator()
            ctx.markdown_path = gen.generate(
                df=ctx.df_annotated,
                categories=ctx.categories,
                insights=ctx.insights,
                chart_paths=ctx.chart_paths,
                data_source=ctx.data_source,
                output_path="reports/enterprise_report.md",
            )
        except Exception as exc:
            logger.error("报告生成失败: %s", exc)
            ctx.markdown_path = ""

    def _step_generate_ppt(self, ctx: WorkflowContext) -> None:
        """步骤 8：生成 PPT。"""
        if ctx.df_annotated is None:
            raise ValueError("数据未分析")

        try:
            from services.ppt_generator import PPTGenerator

            gen = PPTGenerator()
            ctx.ppt_path = gen.generate(
                df=ctx.df_annotated,
                categories=ctx.categories,
                insights=ctx.insights,
                chart_paths=ctx.chart_paths,
                output_path="reports/enterprise_report.pptx",
            )
        except ImportError as exc:
            logger.warning("PPT 生成依赖缺失: %s", exc)
            ctx.ppt_path = ""
        except Exception as exc:
            logger.error("PPT 生成失败: %s", exc)
            ctx.ppt_path = ""


# ===========================================================================
# 独立运行入口
# ===========================================================================


def main() -> None:
    """命令行入口：运行完整报告工作流。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # 尝试初始化 RAG
    rag = None
    try:
        from src.ai_cs_copilot.services.rag_service import RAGService

        rag = RAGService()
        logger.info("RAG 知识库已加载")
    except Exception as exc:
        logger.info("RAG 不可用（不影响主流程）: %s", exc)

    csv_path = "data/sample_customer_data.csv"
    wf = ReportWorkflow(rag_service=rag)

    try:
        ctx = wf.run(csv_path)
    except Exception as exc:
        logger.critical("工作流执行失败: %s", exc)
        sys.exit(1)

    # 输出结果
    print("\n" + "=" * 60)
    print("  企业报告生成完成！")
    if ctx.markdown_path:
        print(f"  📄 Markdown: {ctx.markdown_path}")
    if ctx.ppt_path:
        print(f"  📊 PPT:      {ctx.ppt_path}")
    print(f"  图表数:     {len(ctx.chart_paths)}")
    if ctx.errors:
        print(f"  异常:       {len(ctx.errors)} 个步骤有警告")
    print("=" * 60)


if __name__ == "__main__":
    main()

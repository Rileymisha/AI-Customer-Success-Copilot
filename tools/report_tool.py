# -*- coding: utf-8 -*-
"""
Markdown 报告生成工具（Report Tool）
====================================

封装 ``ReportGenerator``，生成结构化的 Markdown 企业分析报告。

Tool Calling 设计:
    Agent 在最后阶段调用此工具，将之前所有工具的输出
    （分析结果、RAG 知识、图表路径、AI 洞察）整合为一份可读的企业报告。

报告结构:
    1. 执行摘要
    2. 客户风险分布（含图表）
    3. 高风险客户清单
    4. 高价值客户
    5. 增长潜力客户
    6. 行业与区域分析（含图表）
    7. AI 经营洞察
    8. 行动计划
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from tools.base_tool import BaseTool, ToolError, ToolParameter, ToolSpec


class ReportTool(BaseTool):
    """
    Markdown 报告生成工具。

    将数据分析、RAG 知识、AI 洞察和图表整合为一份结构化的
    Markdown 企业报告，包含执行摘要、风险分析、客户清单、AI 洞察与行动计划。
    """

    @property
    def name(self) -> str:
        return "report_generation"

    @property
    def description(self) -> str:
        return (
            "Markdown 报告生成工具：将客户分析结果、风险分类、AI 经营洞察和图表整合为"
            "结构化 Markdown 企业报告，包含执行摘要、风险分布、客户清单、AI 洞察与行动计划。"
        )

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            parameters=[
                ToolParameter(name="df", type="object", description="已标注风险等级的 DataFrame", required=True),
                ToolParameter(name="categories", type="object", description="客户分类结果字典", required=True),
                ToolParameter(name="insights", type="string", description="AI 经营洞察文本", required=True),
                ToolParameter(name="chart_paths", type="object", description="图表路径字典", required=True),
            ],
        )

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        生成 Markdown 报告。

        参数:
            df: 已标注风险等级的 DataFrame
            categories: 客户分类结果
            insights: AI 洞察文本
            chart_paths: 图表路径
            data_source: 数据来源说明（可选）

        返回:
            {
                "markdown_path": "reports/enterprise_report.md",
                "markdown_content": "报告全文文本"
            }
        """
        df: pd.DataFrame | None = kwargs.get("df")
        categories: dict | None = kwargs.get("categories")
        insights: str = kwargs.get("insights", "")
        chart_paths: dict = kwargs.get("chart_paths", {})
        data_source: str = kwargs.get("data_source", "AI Agent 自动分析")

        if df is None:
            raise ToolError("缺少必要参数：df")
        if not categories:
            raise ToolError("缺少必要参数：categories")

        try:
            from services.report_generator import ReportGenerator

            rg = ReportGenerator()
            markdown_path = rg.generate(
                df=df,
                categories=categories,
                insights=insights,
                chart_paths=chart_paths,
                data_source=data_source,
                output_path="reports/enterprise_report.md",
            )

            # 读取生成的报告全文
            md_content = Path(markdown_path).read_text(encoding="utf-8")

            return {
                "markdown_path": markdown_path,
                "markdown_content": md_content,
            }

        except Exception as exc:
            raise ToolError(f"Markdown 报告生成失败：{exc}") from exc

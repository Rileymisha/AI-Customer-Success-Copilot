# -*- coding: utf-8 -*-
"""
PPT 报告生成工具（PPT Tool）
============================

封装 ``PPTGenerator``，生成企业经营分析 PPT 演示文稿。

Tool Calling 设计:
    Agent 在最后阶段调用此工具，生成面向管理层的专业演示文稿。
    与 report_tool 共享相同的输入数据，但输出格式不同（PPT vs Markdown），
    体现了"同一数据，多格式输出"的设计思想。

PPT 结构:
    第 1 页: 封面
    第 2 页: 执行摘要
    第 3 页: 客户风险分布（饼图）
    第 4 页: 高风险客户详情（表格）
    第 5 页: 高价值客户
    第 6 页: 行业与区域分析（图表）
    第 7 页: AI 经营洞察
    第 8 页: 行动计划
    第 9 页: 结束页
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from tools.base_tool import BaseTool, ToolError, ToolParameter, ToolSpec


class PPTTool(BaseTool):
    """
    PPT 演示文稿生成工具。

    将分析结果、图表和 AI 洞察转化为专业的 PPT 演示文稿，
    包含封面、执行摘要、风险分析、高价值客户、图表展示、AI 洞察、行动计划等页面。
    """

    @property
    def name(self) -> str:
        return "ppt_generation"

    @property
    def description(self) -> str:
        return (
            "PPT 演示文稿生成工具：将客户分析结果、图表和 AI 洞察转化为专业 PPT，"
            "包含封面、执行摘要、风险分析、高价值客户、图表展示、AI 洞察、行动计划等幻灯片。"
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
        生成 PPT 演示文稿。

        参数:
            df: 已标注风险等级的 DataFrame
            categories: 客户分类结果
            insights: AI 洞察文本
            chart_paths: 图表路径

        返回:
            {
                "ppt_path": "reports/enterprise_report.pptx"
            }
        """
        df: pd.DataFrame | None = kwargs.get("df")
        categories: dict | None = kwargs.get("categories")
        insights: str = kwargs.get("insights", "")
        chart_paths: dict = kwargs.get("chart_paths", {})

        if df is None:
            raise ToolError("缺少必要参数：df")
        if not categories:
            raise ToolError("缺少必要参数：categories")

        try:
            from services.ppt_generator import PPTGenerator

            pg = PPTGenerator()
            ppt_path = pg.generate(
                df=df,
                categories=categories,
                insights=insights,
                chart_paths=chart_paths,
                output_path="reports/enterprise_report.pptx",
            )

            return {"ppt_path": ppt_path}

        except Exception as exc:
            raise ToolError(f"PPT 生成失败：{exc}") from exc

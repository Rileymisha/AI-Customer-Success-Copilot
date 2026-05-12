# -*- coding: utf-8 -*-
"""
图表生成工具（Chart Tool）
=========================

封装 ``ChartGenerator``，根据客户数据自动生成全套分析图表（PNG）。

Tool Calling 设计:
    Agent 在数据分析完成后调用此工具，准备可视化素材。
    生成的图表路径会传入 report_tool 和 ppt_tool，嵌入报告文档。

功能:
    - GMV 排行柱状图（前 10 名）
    - 风险分布饼图（高 / 中 / 低）
    - 行业分布柱状图
    - 区域分布柱状图
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from tools.base_tool import BaseTool, ToolError, ToolParameter, ToolSpec


class ChartTool(BaseTool):
    """
    图表生成工具。

    根据客户数据自动生成 4 张分析图表（matplotlib PNG），
    供 Markdown 报告和 PPT 引用。
    """

    @property
    def name(self) -> str:
        return "chart_generation"

    @property
    def description(self) -> str:
        return (
            "图表生成工具：根据客户数据自动生成全套分析图表 PNG，"
            "包括 GMV 排行柱状图、风险分布饼图、行业分布柱状图、区域分布柱状图。"
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
                    description="已标注风险等级的 DataFrame（需含 risk_level 列）",
                    required=True,
                ),
            ],
        )

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        生成全套图表。

        参数:
            df: 已标注风险等级的 DataFrame

        返回:
            {
                "chart_paths": {
                    "gmv_bar": "visualizations/gmv_bar.png",
                    "risk_pie": "visualizations/risk_pie.png",
                    "industry_bar": "visualizations/industry_bar.png",
                    "region_bar": "visualizations/region_bar.png"
                }
            }
        """
        df: pd.DataFrame | None = kwargs.get("df")
        if df is None:
            raise ToolError("缺少必要参数：df")

        if "risk_level" not in df.columns:
            raise ToolError("数据缺少 risk_level 列，请先执行数据标注")

        try:
            from visualizations.chart_generator import ChartGenerator

            cg = ChartGenerator(output_dir="visualizations")
            chart_paths = cg.generate_all(df)

            return {"chart_paths": chart_paths}

        except Exception as exc:
            raise ToolError(f"图表生成失败：{exc}") from exc

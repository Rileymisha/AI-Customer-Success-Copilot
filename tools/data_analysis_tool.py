# -*- coding: utf-8 -*-
"""
数据分析工具（Data Analysis Tool）
=================================

对客户经营数据执行风险评分、风险等级标注、客户分类等分析操作。
封装了 ``customer_analytics`` 模块的核心能力，作为 Agent 的可调用工具。

功能:
    1. 风险评分   → 为每个客户计算风险分数
    2. 风险等级标注 → 高 / 中 / 低
    3. 客户分类    → 高风险 / 高价值 / 增长潜力
    4. 生成 LLM 上下文摘要

Tool Calling 设计:
    本工具注册为 "data_analysis"，Agent 在分析阶段优先调用它。
    它的输出（df_annotated、categories）会被写入 AgentContext，
    供后续的 rag_query、chart_generation 等工具使用。
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from tools.base_tool import BaseTool, ToolError, ToolParameter, ToolSpec


class DataAnalysisTool(BaseTool):
    """
    客户数据分析工具。

    对 DataFrame 执行完整的数据分析流程:
    - 风险评分与等级标注
    - 客户分层分类（高风险 / 高价值 / 增长潜力）
    - 生成 LLM 可读的分析摘要
    """

    @property
    def name(self) -> str:
        return "data_analysis"

    @property
    def description(self) -> str:
        return (
            "客户经营数据分析工具：对客户数据执行风险评分、风险等级标注（高/中/低）、"
            "客户分类（高风险/高价值/增长潜力），并生成可用于 LLM 提示词的文本摘要。"
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
                    description="客户数据 DataFrame，需包含 monthly_gmv、login_days、complaint_count 等字段",
                    required=True,
                ),
            ],
        )

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        执行数据分析流程。

        参数:
            df: 客户数据 DataFrame

        返回:
            {
                "df_annotated": DataFrame（已标注 risk_level 列）,
                "categories": {
                    "high_risk": [dict, ...],
                    "high_value": [dict, ...],
                    "growth": [dict, ...]
                },
                "context_text": 给 LLM 的摘要文本
            }

        异常:
            ToolError: 数据为空或缺少必要字段时抛出
        """
        df: pd.DataFrame | None = kwargs.get("df")
        if df is None:
            raise ToolError("缺少必要参数：df")
        if df.empty:
            raise ToolError("数据为空，无法分析")

        # ---- 第 1 步：风险评分与等级标注 ----
        from src.ai_cs_copilot.pipelines.customer_analytics import (
            annotate_risk_levels,
            dataframe_to_brief_context,
        )

        df_annotated = annotate_risk_levels(df)

        # ---- 第 2 步：客户分类 ----
        # 高风险客户（risk_level == "高"）
        high_risk = df_annotated[df_annotated["risk_level"] == "高"].to_dict("records")

        # 高价值客户：月 GMV >= 200000 且 登录天数 >= 20
        high_value = df_annotated[
            (df_annotated["monthly_gmv"] >= 200000)
            & (df_annotated["login_days"] >= 20)
        ].to_dict("records")

        # 增长潜力客户：月 GMV 80000~200000 且 登录天数 >= 15
        growth = df_annotated[
            (df_annotated["monthly_gmv"] >= 80000)
            & (df_annotated["monthly_gmv"] < 200000)
            & (df_annotated["login_days"] >= 15)
        ].to_dict("records")

        categories = {
            "high_risk": high_risk,
            "high_value": high_value,
            "growth": growth,
        }

        # ---- 第 3 步：生成摘要（给 LLM 的上下文） ----
        context_text = dataframe_to_brief_context(df_annotated, max_rows=10)

        return {
            "df_annotated": df_annotated,
            "categories": categories,
            "context_text": context_text,
        }

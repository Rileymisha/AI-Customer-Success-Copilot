# -*- coding: utf-8 -*-
"""
多工具 AI 智能体（Multi-Tool AI Agent）工具包
============================================

本包提供了 5 个独立的企业报告生成工具 + 1 个智能编排 Agent，
基于 LangChain Tool Calling 思想设计。

工具列表:
- DataAnalysisTool: 客户数据分析与风险标注
- RAGQueryTool: 知识库检索（RAG）
- ChartTool: 图表生成（matplotlib PNG）
- ReportTool: Markdown 报告生成
- PPTTool: PPT 演示文稿生成
- MultiToolAgent: 多工具编排智能体

使用方式::

    from tools import MultiToolAgent, DataAnalysisTool

    agent = MultiToolAgent()
    result = agent.run(task="生成企业经营分析报告", df=customer_df)

注意:
    工具内部会 import ``src/ai_cs_copilot/`` 下的模块，
    确保项目根目录下的 ``src`` 已在 ``sys.path`` 中（Streamlit 入口 ``app.py`` 已处理）。
"""

from tools.base_tool import BaseTool, ToolError, ToolParameter, ToolSpec
from tools.data_analysis_tool import DataAnalysisTool
from tools.rag_query_tool import RAGQueryTool
from tools.chart_tool import ChartTool
from tools.report_tool import ReportTool
from tools.ppt_tool import PPTTool
from tools.agent import MultiToolAgent, AgentContext, AgentResult

__all__ = [
    # 基类
    "BaseTool",
    "ToolError",
    "ToolParameter",
    "ToolSpec",
    # 工具
    "DataAnalysisTool",
    "RAGQueryTool",
    "ChartTool",
    "ReportTool",
    "PPTTool",
    # 智能体
    "MultiToolAgent",
    "AgentContext",
    "AgentResult",
]

# -*- coding: utf-8 -*-
"""
RAG 知识库查询工具（RAG Query Tool）
=====================================

封装 ``RAGService``，根据客户数据特征自动诊断问题并检索企业内部知识库。

Tool Calling 设计:
    Agent 在数据标注后调用此工具，将检索到的知识上下文注入后续步骤，
    使 AI 生成的洞察和建议有企业内部知识作为依据（检索增强生成）。

功能:
    - 自动诊断客户数据中的问题模式（低登录、高投诉、逾期等）
    - 根据问题模式从知识库检索相关策略文档
    - 返回结构化的参考上下文文本
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from tools.base_tool import BaseTool, ToolError, ToolParameter, ToolSpec


class RAGQueryTool(BaseTool):
    """
    RAG 知识库检索工具。

    根据客户数据特征自动诊断问题 → 查询知识库 → 返回参考上下文。
    让 Agent 的决策有企业知识作为依据（RAG = Retrieval-Augmented Generation）。
    """

    @property
    def name(self) -> str:
        return "rag_query"

    @property
    def description(self) -> str:
        return (
            "RAG 知识库检索工具：根据客户数据特征自动诊断问题 "
            "（低登录率、高投诉、续约逾期、低功能使用率等），"
            "从企业内部知识库检索相关策略文档，返回参考上下文。"
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
                    description="客户数据 DataFrame（含 login_days、complaint_count、renewal_days_left 等字段）",
                    required=True,
                ),
            ],
        )

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        执行 RAG 知识库检索。

        参数:
            df: 客户数据 DataFrame

        返回:
            {
                "rag_context": 知识库检索结果文本（可用于 LLM 提示词）
            }
        """
        df: pd.DataFrame | None = kwargs.get("df")
        if df is None:
            raise ToolError("缺少必要参数：df")

        try:
            from src.ai_cs_copilot.services.rag_service import RAGService

            rag = RAGService()
            rag_context = rag.diagnose_and_retrieve(df)

            return {
                "rag_context": rag_context or "（知识库未返回相关内容）",
            }

        except ImportError:
            # RAG 依赖未安装时返回友好提示，不崩溃
            return {
                "rag_context": (
                    "（RAG 知识库依赖未安装，跳过知识检索。"
                    "如需使用：pip install langchain-community faiss-cpu sentence-transformers）"
                ),
            }
        except Exception as exc:
            raise ToolError(f"RAG 知识库检索失败：{exc}") from exc

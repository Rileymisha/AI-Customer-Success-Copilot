# -*- coding: utf-8 -*-
"""
多工具 AI 智能体（Multi-Tool AI Agent）
=======================================

基于 LangChain **Tool Calling** 思想设计的多工具编排智能体。

核心概念:
---------
1. Tool（工具）: 每个工具是一个独立的功能单元，有 name、description、parameters
2. Tool Calling（工具调用）: Agent 分析任务 → 决定调用哪些工具 → 按序执行
3. Context（上下文）: 工具间的数据通过共享的 AgentContext 传递

工作流程:
---------
用户输入任务 → Agent 分析任务 → 规划工具序列 → 依次执行工具 → 汇总结果

与 LangChain Tool Calling 的对应关系:
-------------------------------------
    LangChain Agent               → 本 MultiToolAgent
    LangChain Tool                → 本 BaseTool 子类
    Tool.name / .description      → 本 ToolSpec
    AgentExecutor.run()           → 本 run()
    intermediate_steps            → AgentContext.execution_log

为什么用规则 Pipeline + 预留 LLM 规划?
---------------------------------------
企业报告生成是"确定性 + 创造性"混合场景:
- 确定性部分（数据标注、分类、图表）→ 规则 Pipeline，速度快、无幻觉
- 创造性部分（经营洞察）→ 由 LLM 生成，预留 LLM 规划接口供扩展
- 这种"规则 + AI"双轨制与企业报告系统的设计哲学一致（详见 MULTI_AGENT_ARCHITECTURE.md）
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from tools.base_tool import BaseTool, ToolError

logger = logging.getLogger(__name__)


# ===========================================================================
# Agent 运行时数据结构
# ===========================================================================


@dataclass
class AgentContext:
    """
    智能体上下文 - 在工具链中传递的共享数据总线。

    类似 LangChain 的 AgentExecutor 中的 intermediate_steps，
    每个工具执行后将结果写入 context，供后续工具读取。

    属性:
        task: 用户输入的任务描述
        df: 原始客户数据
        df_annotated: 已标注风险等级的数据
        categories: 客户分类结果
        rag_context: RAG 知识库检索结果
        insights: AI 经营洞察
        chart_paths: 图表文件路径
        markdown_path: Markdown 报告路径
        ppt_path: PPT 文件路径
        execution_log: 执行日志（每个步骤的记录）
        start_time: 开始执行的时间
    """
    task: str = ""
    df: Optional[pd.DataFrame] = None
    df_annotated: Optional[pd.DataFrame] = None
    categories: Optional[Dict[str, Any]] = None
    rag_context: str = ""
    insights: str = ""
    chart_paths: Optional[Dict[str, str]] = None
    markdown_path: str = ""
    ppt_path: str = ""
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    start_time: str = ""


@dataclass
class AgentResult:
    """
    智能体执行结果。

    返回给调用方的完整结果，包含所有工具的输出和可读摘要。

    属性:
        success: 是否全部成功
        context: 完整的 AgentContext（含所有工具的输出）
        summary: 人类可读的执行摘要文本
        error: 失败时的错误信息（success=False 时）
    """
    success: bool = True
    context: Optional[AgentContext] = None
    summary: str = ""
    error: str = ""


# ===========================================================================
# 预设工具链（Pipeline）
# ===========================================================================

# Agent 默认的工具执行顺序（Pipeline 模式）
# 每个元素是 (步骤名, 工具名, 是否关键步骤)
# 关键步骤失败 → 终止整个流程；非关键步骤失败 → 跳过继续
_DEFAULT_PIPELINE: List[tuple] = [
    ("数据标注与分类", "data_analysis", True),
    ("AI 经营洞察生成", "insight_generation", False),
    ("知识库检索", "rag_query", False),
    ("图表生成", "chart_generation", False),
    ("Markdown 报告生成", "report_generation", False),
    ("PPT 生成", "ppt_generation", False),
]


# ===========================================================================
# 多工具智能体
# ===========================================================================


class MultiToolAgent:
    """
    多工具 AI 智能体 - 自动编排工具调用链。

    用法::

        agent = MultiToolAgent()
        result = agent.run(task="生成企业经营分析报告", df=customer_df)

        if result.success:
            print(result.summary)
            print(result.context.markdown_path)
            print(result.context.ppt_path)

    设计思想:
    ---------
    1. 工具注册: 所有工具注册到 agent.tools 字典，通过 name 索引
    2. 任务规划: agent 分析任务描述，确定工具调用序列
    3. 顺序执行: 按规划顺序调用工具，前一个的输出作为后一个的输入
    4. 错误处理: 关键步骤失败终止，非关键步骤跳过
    5. 结果汇总: 所有工具的输出汇总到 AgentResult
    """

    def __init__(self) -> None:
        # 工具注册表：name → BaseTool 实例
        self.tools: Dict[str, BaseTool] = {}
        # 默认工具链（Pipeline 步骤定义）
        self.pipeline: List[tuple] = list(_DEFAULT_PIPELINE)
        # 是否使用 LLM 进行任务规划（默认使用规则 Pipeline）
        self.use_llm_planning: bool = False

        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """
        注册 Agent 自带的默认工具集。

        对应 LangChain Tool Calling 中的 tool registration::

            tools = [
                Tool(name="data_analysis", description="...", func=...),
                Tool(name="rag_query", description="...", func=...),
                ...
            ]
            llm.bind_tools(tools)
        """
        from tools.data_analysis_tool import DataAnalysisTool
        from tools.insight_tool import InsightGenerationTool
        from tools.rag_query_tool import RAGQueryTool
        from tools.chart_tool import ChartTool
        from tools.report_tool import ReportTool
        from tools.ppt_tool import PPTTool

        self.register_tool(DataAnalysisTool())
        self.register_tool(InsightGenerationTool())
        self.register_tool(RAGQueryTool())
        self.register_tool(ChartTool())
        self.register_tool(ReportTool())
        self.register_tool(PPTTool())

    def register_tool(self, tool: BaseTool) -> None:
        """
        注册一个工具到 Agent。

        参数:
            tool: BaseTool 子类实例
        """
        self.tools[tool.name] = tool
        logger.debug("已注册工具: %s - %s", tool.name, tool.description)

    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """
        获取所有已注册工具的规格说明。

        类似 LangChain 中将工具列表传给 LLM 时的格式转换::

            llm.bind_tools([tool1, tool2, ...])

        返回:
            [{"name": "data_analysis", "description": "...", "parameters": [...]}, ...]
        """
        specs = []
        for _name, tool in self.tools.items():
            spec = tool.spec
            specs.append({
                "name": spec.name,
                "description": spec.description,
                "parameters": [
                    {"name": p.name, "type": p.type, "description": p.description, "required": p.required}
                    for p in spec.parameters
                ],
            })
        return specs

    # ------------------------------------------------------------------
    # 任务规划
    # ------------------------------------------------------------------

    def _plan(self, task: str) -> List[tuple]:
        """
        根据任务描述规划工具执行序列。

        目前使用规则 Pipeline（默认流程），未来可扩展 LLM 规划::

            给定任务: "生成企业经营分析报告"
            LLM 分析后决定: ["data_analysis", "rag_query", "chart", "report", "ppt"]

        参数:
            task: 任务描述文本

        返回:
            步骤列表，每个元素为 (步骤名, 工具名, 是否关键)
        """
        if self.use_llm_planning:
            # ---- 预留 LLM 规划接口 ----
            # TODO: 调用 LLM 分析 task，动态决定工具序列
            # 伪代码:
            #   prompt = f"根据任务「{task}」，从 {list(self.tools.keys())} 中选择工具序列"
            #   response = llm.invoke(prompt)
            #   return parse_response(response)
            pass

        # 默认返回预设 Pipeline
        return list(self.pipeline)

    # ------------------------------------------------------------------
    # 主执行入口
    # ------------------------------------------------------------------

    def run(
        self,
        task: str = "生成企业经营分析报告",
        df: Optional[pd.DataFrame] = None,
        insights: str = "",
    ) -> AgentResult:
        """
        执行完整的 Agent 工作流。

        这是 Agent 的主入口方法，对应 LangChain 的 AgentExecutor.run()。

        参数:
            task: 任务描述（用于规划工具调用）
            df: 客户数据 DataFrame
            insights: 可选的 AI 洞察文本（若已预先通过 LLM 生成）

        返回:
            AgentResult: 执行结果（含所有工具的输出）
        """
        # ---- 初始化上下文 ----
        context = AgentContext(
            task=task,
            df=df,
            insights=insights,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        logger.info("Agent 开始执行任务: %s", task)

        # ---- 任务规划 ----
        steps = self._plan(task)
        context.execution_log.append({
            "step": "task_planning",
            "status": "success",
            "message": f"规划完成：{len(steps)} 个步骤",
            "steps": [s[0] for s in steps],
        })

        # ---- 按序执行工具 ----
        for step_name, tool_name, is_critical in steps:
            log_entry: Dict[str, Any] = {
                "step": step_name,
                "tool": tool_name,
                "status": "running",
                "message": "",
            }

            try:
                self._execute_tool(tool_name, context)
                log_entry["status"] = "success"
                log_entry["message"] = f"工具 {tool_name} 执行成功"
                logger.info("步骤 [%s] 完成: %s", step_name, tool_name)

            except ToolError as exc:
                log_entry["status"] = "failed"
                log_entry["message"] = str(exc)
                logger.warning("步骤 [%s] 失败: %s", step_name, exc)

                if is_critical:
                    context.execution_log.append(log_entry)
                    error_msg = f"关键步骤 [{step_name}] 失败：{exc}"
                    logger.error(error_msg)
                    return AgentResult(
                        success=False,
                        context=context,
                        summary=self._build_summary(context),
                        error=error_msg,
                    )
                # 非关键步骤失败，跳过继续
                log_entry["message"] += "（非关键步骤，已跳过）"
                context.execution_log.append(log_entry)
                continue

            except Exception as exc:
                # 未预期的异常
                log_entry["status"] = "error"
                log_entry["message"] = f"未预期错误：{exc}"
                logger.exception("步骤 [%s] 异常", step_name)

                if is_critical:
                    context.execution_log.append(log_entry)
                    return AgentResult(
                        success=False,
                        context=context,
                        summary=self._build_summary(context),
                        error=f"关键步骤 [{step_name}] 异常：{exc}",
                    )
                context.execution_log.append(log_entry)
                continue

            context.execution_log.append(log_entry)

        # ---- 汇总结果 ----
        summary = self._build_summary(context)
        logger.info("Agent 任务完成: %s", task)

        return AgentResult(
            success=True,
            context=context,
            summary=summary,
        )

    def _execute_tool(self, tool_name: str, context: AgentContext) -> Dict[str, Any]:
        """
        执行单个工具，并将结果写入上下文。

        根据 context 中的当前数据决定传给工具的参数。
        每个工具只从 context 读取自己需要的字段，不关心其他工具的数据。

        参数:
            tool_name: 工具名称（必须在 tools 中已注册）
            context: 当前 Agent 上下文（会被修改）

        返回:
            工具执行结果字典

        异常:
            ToolError: 工具执行失败时抛出
            KeyError: 工具未注册时抛出
        """
        if tool_name not in self.tools:
            raise ToolError(f"工具未注册：{tool_name}")

        tool = self.tools[tool_name]

        # 根据工具名称准备不同的输入参数
        if tool_name == "data_analysis":
            result = tool.run(df=context.df)
            context.df_annotated = result.get("df_annotated")
            context.categories = result.get("categories")
            if not context.insights:
                context.insights = result.get("context_text", "")
            return result

        elif tool_name == "insight_generation":
            df = context.df_annotated if context.df_annotated is not None else context.df
            result = tool.run(df=df, categories=context.categories or {})
            # 仅当 LLM 返回了非占位符内容时才覆盖 insights
            ai_insights = result.get("insights", "")
            if ai_insights and not ai_insights.startswith("（AI 洞察"):
                context.insights = ai_insights
            return result

        elif tool_name == "rag_query":
            df = context.df_annotated if context.df_annotated is not None else context.df
            result = tool.run(df=df)
            context.rag_context = result.get("rag_context", "")
            return result

        elif tool_name == "chart_generation":
            df = context.df_annotated if context.df_annotated is not None else context.df
            result = tool.run(df=df)
            context.chart_paths = result.get("chart_paths")
            return result

        elif tool_name == "report_generation":
            result = tool.run(
                df=context.df_annotated or context.df,
                categories=context.categories or {},
                insights=context.insights or "（由 AI Agent 自动生成）",
                chart_paths=context.chart_paths or {},
                data_source=f"AI Agent 自动分析 - {context.task}",
            )
            context.markdown_path = result.get("markdown_path", "")
            return result

        elif tool_name == "ppt_generation":
            result = tool.run(
                df=context.df_annotated or context.df,
                categories=context.categories or {},
                insights=context.insights or "（由 AI Agent 自动生成）",
                chart_paths=context.chart_paths or {},
            )
            context.ppt_path = result.get("ppt_path", "")
            return result

        else:
            # 通用调用方式：直接传入整个 context
            return tool.run(context=context)

    def _build_summary(self, context: AgentContext) -> str:
        """
        构建人类可读的执行摘要。

        参数:
            context: 执行完成的 AgentContext

        返回:
            格式化的摘要文本
        """
        lines = [
            "=" * 50,
            "AI Agent 执行报告",
            "=" * 50,
            f"任务：{context.task}",
            f"执行时间：{context.start_time}",
            "",
            "执行步骤：",
        ]

        for entry in context.execution_log:
            icon = "✓" if entry.get("status") == "success" else "✗"
            lines.append(f"  {icon} {entry['step']}: {entry.get('message', '')}")

        lines.extend(["", "产出物："])

        if context.categories:
            lines.append(
                f"  - 客户分类：高风险 {len(context.categories.get('high_risk', []))} 个 / "
                f"高价值 {len(context.categories.get('high_value', []))} 个 / "
                f"增长 {len(context.categories.get('growth', []))} 个"
            )
        if context.rag_context:
            lines.append("  - RAG 知识库：已检索")
        if context.chart_paths:
            lines.append(f"  - 图表：{len(context.chart_paths)} 张")
        if context.markdown_path:
            lines.append(f"  - Markdown 报告：{context.markdown_path}")
        if context.ppt_path:
            lines.append(f"  - PPT 演示文稿：{context.ppt_path}")

        lines.append("=" * 50)
        return "\n".join(lines)

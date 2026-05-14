# -*- coding: utf-8 -*-
"""
多工具 AI 智能体（Multi-Tool AI Agent）
=======================================

基于 LangChain Tool Calling 思想设计的多工具编排智能体。

核心概念:
---------
1. Tool（工具）: 每个工具是一个独立的功能单元，有 name、description、parameters
2. Agent Loop（智能体循环）: Agent 在循环中调用 LLM 决策 → 执行工具 → 观察结果 → 再决策
3. Context（上下文）: 工具间的数据通过共享的 AgentContext 传递

工作流程:
---------
用户输入任务 → Agent 进入 LLM 决策循环：
  每轮: LLM 思考当前状态 → 决定调哪个工具 → 执行 → 观察结果 → 下一轮
  直到: LLM 判定任务完成 → 汇总结果

与 LangChain Tool Calling 的对应关系:
-------------------------------------
    LangChain Agent               → 本 MultiToolAgent
    LangChain Tool                → 本 BaseTool 子类
    Tool.name / .description      → 本 ToolSpec
    AgentExecutor.run()           → 本 run()
    intermediate_steps            → AgentContext.execution_log
"""

from __future__ import annotations

import json
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
        execution_log: 执行日志（每轮决策和执行记录）
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
# LLM 决策系统提示词
# ===========================================================================

_AGENT_SYSTEM_PROMPT = (
    "你是一个 AI Agent 调度器，负责分析客户数据并生成企业经营报告。\n"
    "每轮你可以调用一个工具，观察结果后再决定下一步。\n"
    "\n"
    "## 可用工具\n"
    "{tool_descriptions}\n"
    "\n"
    "## 规则\n"
    "1. 每次只能调用一个工具\n"
    "2. 注意工具之间的依赖关系：需要前置数据齐了再调下游工具\n"
    "3. 如果某个工具失败（如 API 不可用），可以跳过它继续\n"
    "4. 所有必要的工具都执行完毕后，输出 finish\n"
    "5. 最多执行 15 轮，超出限制会自动结束\n"
    "\n"
    "## 输出格式\n"
    "你只能输出以下 JSON（不要包含其他文字）：\n"
    "\n"
    "如果调用工具：\n"
    '{{"reasoning": "为什么调这个工具", "action": "call_tool", "tool": "工具名称"}}\n'
    "\n"
    "如果任务完成：\n"
    '{{"reasoning": "任务完成总结", "action": "finish", "summary": "做了什么、产出是什么"}}\n'
)

# ===========================================================================
# 预设工具链（Pipeline，作为 LLM 决策的 fallback）
# ===========================================================================

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

    两种模式：
    - LLM 决策模式（默认）: 每轮由 LLM 决定调什么工具，支持错误反馈和动态调整
    - Pipeline 模式（降级）: 按固定顺序执行工具，use_llm_planning=False

    用法::

        agent = MultiToolAgent()
        result = agent.run(task="生成企业经营分析报告", df=customer_df)

        if result.success:
            print(result.summary)
            print(result.context.markdown_path)
            print(result.context.ppt_path)
    """

    def __init__(self) -> None:
        # 工具注册表：name → BaseTool 实例
        self.tools: Dict[str, BaseTool] = {}
        # 默认工具链（Pipeline 模式用）
        self.pipeline: List[tuple] = list(_DEFAULT_PIPELINE)
        # LLM 决策模式开关（True=LLM循环, False=固定Pipeline）
        self.use_llm_planning: bool = True

        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """注册 Agent 自带的默认工具集。"""
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

        返回:
            [{"name": "...", "description": "...", "parameters": [...]}, ...]
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
    # LLM 决策循环
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        """从已注册的工具生成 LLM 系统提示中的工具描述。"""
        lines = []
        for name, tool in self.tools.items():
            spec = tool.spec
            params_desc = ", ".join(p.name for p in spec.parameters) if spec.parameters else "无"
            lines.append(f"- {name}: {tool.description}（需要参数: {params_desc}）")
        return _AGENT_SYSTEM_PROMPT.format(tool_descriptions="\n".join(lines))

    def _has_ai_insights(self, insights: str) -> bool:
        """判断 insights 是否为真正的 AI 分析结果（而非 data_analysis 的摘要）。"""
        if not insights:
            return False
        # data_analysis 填充的 context_text 通常 < 500 字符且无 Markdown 标题
        # AI 洞察通常 > 1000 字符且包含 ## 分节
        if len(insights) < 500:
            return False
        if "## " in insights:
            return True
        return "经营" in insights and "风险" in insights

    def _build_context_state(self, context: AgentContext) -> str:
        """构建当前上下文中各数据的就绪状态。"""
        checks = [
            ("df", "原始数据", context.df is not None),
            ("df_annotated", "风险标注", context.df_annotated is not None),
            ("categories", "客户分类", bool(context.categories)),
            ("rag_context", "知识库参考", bool(context.rag_context)),
            ("insights", "AI 洞察", self._has_ai_insights(context.insights)),
            ("chart_paths", "图表", bool(context.chart_paths)),
            ("markdown_path", "Markdown 报告", bool(context.markdown_path)),
            ("ppt_path", "PPT", bool(context.ppt_path)),
        ]
        lines = ["## 当前数据状态\n", "| 数据 | 说明 | 状态 |"]
        lines.append("|------|------|------|")
        for key, label, ready in checks:
            icon = "✅ 就绪" if ready else "⏳ 未生成"
            lines.append(f"| {key} | {label} | {icon} |")
        return "\n".join(lines)

    def _build_execution_history(self, context: AgentContext) -> str:
        """构建已执行的轮次历史。"""
        if not context.execution_log:
            return "## 执行历史\n\n（尚未执行任何工具）\n"

        lines = ["## 执行历史\n"]
        for entry in context.execution_log:
            r = entry.get("round", "?")
            tool = entry.get("tool", "?")
            status = entry.get("status", "?")
            icon = "✅" if status == "success" else "❌"
            reasoning = entry.get("reasoning", "")
            result_summary = entry.get("result_summary", "")
            error = entry.get("error", "")
            lines.append(f"### 第 {r} 轮: {tool}")
            if reasoning:
                lines.append(f"决策理由: {reasoning}")
            lines.append(f"结果: {icon} {status}")
            if result_summary:
                lines.append(f"产出: {result_summary}")
            if error:
                lines.append(f"错误: {error}")
            lines.append("")
        return "\n".join(lines)

    def _get_client(self) -> Any:
        """创建 DeepSeek 客户端（懒加载）。"""
        from src.ai_cs_copilot.config import settings
        from openai import OpenAI

        api_key = settings.deepseek_api_key
        if not api_key or api_key.strip().lower().startswith("sk-your"):
            return None
        return OpenAI(
            api_key=api_key,
            base_url=settings.deepseek_base_url.rstrip("/"),
        )

    def _llm_decide_next(self, context: AgentContext, round_num: int) -> Dict[str, Any]:
        """
        调用 LLM 决定下一步操作。

        返回:
            {"action": "call_tool"|"finish", "tool": "tool_name", "reasoning": "...", "summary": "..."}

        异常:
            ValueError: LLM 调用失败或返回无法解析
        """
        from src.ai_cs_copilot.config import settings

        client = self._get_client()
        if client is None:
            raise ValueError("未配置有效的 DEEPSEEK_API_KEY")

        system_prompt = self._build_system_prompt()
        context_state = self._build_context_state(context)
        history = self._build_execution_history(context)

        round_info = f"## 第 {round_num} 轮\n当前是你的第 {round_num} 轮决策。请根据当前状态决定下一步。"

        user_prompt = f"{context_state}\n\n{history}\n{round_info}"

        logger.info("--- Agent 第 %d 轮 LLM 决策 ---", round_num)

        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    timeout=60.0,
                )

                content = response.choices[0].message.content
                if not content:
                    continue

                # 提取 JSON（兼容 ```json 包裹和纯文本）
                text = content.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()

                decision = json.loads(text)

                # 校验字段
                if "action" not in decision or decision["action"] not in ("call_tool", "finish"):
                    raise ValueError(f"无效的 action: {decision.get('action')}")

                if decision["action"] == "call_tool":
                    tool_name = decision.get("tool", "")
                    if tool_name not in self.tools:
                        raise ValueError(f"未注册的工具: {tool_name}，可用工具: {list(self.tools.keys())}")

                logger.info("Agent 决策: %s | reasoning: %s",
                            decision.get("action") + (f" → {decision.get('tool')}" if decision.get("action") == "call_tool" else ""),
                            decision.get("reasoning", ""))

                return decision

            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("LLM 返回解析失败（第 %d 次）: %s", attempt + 1, exc)
                logger.debug("原始返回: %s", content if 'content' in dir() else "N/A")
                continue
            except Exception as exc:
                logger.warning("LLM 调用异常（第 %d 次）: %s", attempt + 1, exc)
                continue

        raise ValueError("LLM 决策失败，已重试 2 次")

    # ------------------------------------------------------------------
    # 任务规划（LLM 模式 / Pipeline 模式）
    # ------------------------------------------------------------------

    def _plan(self, task: str) -> List[tuple]:
        """
        根据任务描述规划工具执行序列。

        参数:
            task: 任务描述文本

        返回:
            步骤列表，每个元素为 (步骤名, 工具名, 是否关键)
        """
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

        参数:
            task: 任务描述
            df: 客户数据 DataFrame
            insights: 可选的 AI 洞察文本（若已预先生成）

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

        if self.use_llm_planning:
            return self._run_llm_loop(context)
        else:
            return self._run_pipeline(context)

    def _run_pipeline(self, context: AgentContext) -> AgentResult:
        """Pipeline 模式：按固定顺序执行工具（保留的 fallback 路径）。"""
        steps = self._plan(context.task)
        context.execution_log.append({
            "step": "task_planning",
            "status": "success",
            "message": f"规划完成：{len(steps)} 个步骤",
            "steps": [s[0] for s in steps],
        })

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
                log_entry["message"] += "（非关键步骤，已跳过）"
                context.execution_log.append(log_entry)
                continue

            except Exception as exc:
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

        summary = self._build_summary(context)
        return AgentResult(success=True, context=context, summary=summary)

    def _run_llm_loop(self, context: AgentContext) -> AgentResult:
        """
        LLM 决策模式：每轮由 LLM 决定调什么工具，支持错误反馈和动态调整。

        Agent 核心循环：
          1. 构建当前状态摘要 + 执行历史
          2. LLM 决定：调哪个工具，或结束
          3. 执行工具 → 记录结果 → 回到 1
          4. 到 finish 或超限 → 汇总返回
        """
        max_rounds = 15
        tool_failures: Dict[str, int] = {}

        for round_num in range(1, max_rounds + 1):
            # ---- LLM 决策 ----
            try:
                decision = self._llm_decide_next(context, round_num)
            except ValueError as exc:
                error_msg = f"LLM 决策失败：{exc}，降级为 Pipeline 模式"
                logger.warning(error_msg)
                return self._run_pipeline(context)

            # ----- LLM 决定结束 ----
            if decision["action"] == "finish":
                logger.info("Agent 决定结束: %s", decision.get("summary", ""))
                context.execution_log.append({
                    "round": round_num,
                    "tool": "finish",
                    "status": "success",
                    "reasoning": decision.get("reasoning", ""),
                    "result_summary": decision.get("summary", "任务完成"),
                })
                break

            # ---- LLM 决定调工具 ----
            tool_name = decision["tool"]

            # 连续失败检查
            if tool_failures.get(tool_name, 0) >= 3:
                logger.warning("工具 %s 已连续失败 3 次，跳过", tool_name)
                context.execution_log.append({
                    "round": round_num,
                    "tool": tool_name,
                    "status": "skipped",
                    "reasoning": decision.get("reasoning", ""),
                    "result_summary": f"跳过 {tool_name}（已连续失败 3 次）",
                })
                continue

            # ---- 执行工具 ----
            log_entry: Dict[str, Any] = {
                "round": round_num,
                "tool": tool_name,
                "status": "running",
                "reasoning": decision.get("reasoning", ""),
                "result_summary": "",
                "error": "",
            }

            try:
                logger.info("第 %d 轮: 调用 %s（reasoning: %s）",
                            round_num, tool_name, decision.get("reasoning", ""))
                self._execute_tool(tool_name, context)
                log_entry["status"] = "success"
                log_entry["result_summary"] = self._summarize_tool_result(tool_name, context)
                logger.info("第 %d 轮: %s 执行成功 ✓", round_num, tool_name)

            except ToolError as exc:
                log_entry["status"] = "failed"
                log_entry["error"] = str(exc)
                log_entry["result_summary"] = f"执行失败：{exc}"
                tool_failures[tool_name] = tool_failures.get(tool_name, 0) + 1
                logger.warning("第 %d 轮: %s 失败（已失败 %d 次）: %s",
                               round_num, tool_name, tool_failures[tool_name], exc)

            except Exception as exc:
                log_entry["status"] = "error"
                log_entry["error"] = f"未预期异常：{exc}"
                log_entry["result_summary"] = f"异常：{exc}"
                tool_failures[tool_name] = tool_failures.get(tool_name, 0) + 1
                logger.exception("第 %d 轮: %s 异常", round_num, tool_name)

            context.execution_log.append(log_entry)

        else:
            # max_rounds 到了还没 finish
            logger.warning("Agent 达到最大轮次 %d 自动结束", max_rounds)
            context.execution_log.append({
                "round": max_rounds + 1,
                "tool": "force_finish",
                "status": "success",
                "reasoning": "达到最大执行轮次，自动结束",
                "result_summary": f"已执行 {max_rounds} 轮，自动终止",
            })

        summary = self._build_summary(context)
        return AgentResult(success=True, context=context, summary=summary)

    def _summarize_tool_result(self, tool_name: str, context: AgentContext) -> str:
        """工具执行后，从 context 中提取关键结果供 LLM 观察。"""
        if tool_name == "data_analysis":
            if context.df_annotated is not None:
                risk_counts = context.df_annotated["risk_level"].value_counts().to_dict()
                return f"已标注风险等级：高 {risk_counts.get('高', 0)} 个、中 {risk_counts.get('中', 0)} 个、低 {risk_counts.get('低', 0)} 个"
            return "数据标注完成"
        if tool_name == "insight_generation":
            return f"AI 洞察生成成功（{len(context.insights)} 字符）" if context.insights else "AI 洞察未生成"
        if tool_name == "rag_query":
            return f"知识库检索完成（{len(context.rag_context)} 字符）" if context.rag_context else "知识库未命中"
        if tool_name == "chart_generation":
            count = len(context.chart_paths) if context.chart_paths else 0
            return f"已生成 {count} 张图表"
        if tool_name == "report_generation":
            return f"Markdown 报告已保存到 {context.markdown_path}" if context.markdown_path else "报告未生成"
        if tool_name == "ppt_generation":
            return f"PPT 已保存到 {context.ppt_path}" if context.ppt_path else "PPT 未生成"
        return "执行完成"

    # ------------------------------------------------------------------
    # 工具执行
    # ------------------------------------------------------------------

    def _execute_tool(self, tool_name: str, context: AgentContext) -> Dict[str, Any]:
        """
        执行单个工具，并将结果写入上下文。

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
                df=context.df_annotated if context.df_annotated is not None else context.df,
                categories=context.categories or {},
                insights=context.insights or "（由 AI Agent 自动生成）",
                chart_paths=context.chart_paths or {},
                data_source=f"AI Agent 自动分析 - {context.task}",
            )
            context.markdown_path = result.get("markdown_path", "")
            return result

        elif tool_name == "ppt_generation":
            result = tool.run(
                df=context.df_annotated if context.df_annotated is not None else context.df,
                categories=context.categories or {},
                insights=context.insights or "（由 AI Agent 自动生成）",
                chart_paths=context.chart_paths or {},
            )
            context.ppt_path = result.get("ppt_path", "")
            return result

        else:
            return tool.run(context=context)

    # ------------------------------------------------------------------
    # 结果汇总
    # ------------------------------------------------------------------

    def _build_summary(self, context: AgentContext) -> str:
        """构建人类可读的执行摘要。"""
        lines = [
            "=" * 50,
            "AI Agent 执行报告",
            "=" * 50,
            f"任务：{context.task}",
            f"执行时间：{context.start_time}",
            f"模式：{'LLM 决策循环' if self.use_llm_planning else '固定 Pipeline'}",
            "",
            "执行步骤：",
        ]

        for entry in context.execution_log:
            if "step" in entry:
                icon = "[OK]" if entry.get("status") == "success" else "[FAIL]"
                lines.append(f"  {icon} {entry['step']}: {entry.get('message', '')}")
            elif "round" in entry:
                if entry.get("status") == "success":
                    icon = "[OK]"
                elif entry.get("status") == "skipped":
                    icon = "[SKIP]"
                else:
                    icon = "[FAIL]"
                tool = entry.get("tool", "")
                if tool == "finish":
                    lines.append(f"  {icon} 结束: {entry.get('result_summary', '')}")
                elif tool == "force_finish":
                    lines.append(f"  {icon} 强制结束: {entry.get('result_summary', '')}")
                else:
                    result = entry.get("result_summary", "")
                    lines.append(f"  {icon} 第{entry['round']}轮 {tool}: {result}")

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

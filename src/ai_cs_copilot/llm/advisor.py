# -*- coding: utf-8 -*-
"""
大模型经营建议生成器（兼容层）
==============================

历史说明：
    早期版本使用 LangChain 直连可配置网关；当前项目「生成报告」主路径已切换为
    ``services/llm_service.py``（DeepSeek + OpenAI 兼容 SDK）。

初学者提示：
    保留 ``generate_business_advice`` 这个旧函数名，是为了让其他模块在不大改代码的情况下
    仍能 import；其内部会转发到 ``generate_business_report``。
"""

from __future__ import annotations

from ai_cs_copilot.services.llm_service import generate_business_report


def generate_business_advice(
    *,
    data_context: str,
    focus: str = "识别风险客户并给出可执行的经营改进建议",
) -> str:
    """
    兼容旧接口：等价于调用 ``generate_business_report``。

    参数:
        data_context: 客户分析数据（文本）；
        focus: 分析侧重点。

    返回:
        模型生成的经营分析报告文本。
    """
    return generate_business_report(customer_analysis_data=data_context, analysis_focus=focus)

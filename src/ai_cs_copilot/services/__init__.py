# -*- coding: utf-8 -*-
"""
服务层（Services）
==================

把「与外部系统打交道」的逻辑集中放在 services/，例如大模型 API、邮件网关等。
页面层（Streamlit）只负责展示与交互，便于单元测试与替换实现。
"""

from ai_cs_copilot.services.llm_service import LlmInvokeError, generate_business_report

__all__ = ["LlmInvokeError", "generate_business_report"]

# -*- coding: utf-8 -*-
"""大模型相关导出：兼容层 + DeepSeek 服务入口。"""

from ai_cs_copilot.llm.advisor import generate_business_advice
from ai_cs_copilot.services.llm_service import generate_business_report

__all__ = ["generate_business_advice", "generate_business_report"]

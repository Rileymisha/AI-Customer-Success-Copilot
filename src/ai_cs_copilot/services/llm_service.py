# -*- coding: utf-8 -*-
"""
大模型服务（DeepSeek — OpenAI 兼容接口）
==========================================

本模块使用官方 ``openai`` Python SDK，通过 ``base_url`` 指向 DeepSeek，
从而与 OpenAI 的 Chat Completions 协议兼容。

初学者提示：
    1. **密钥**：只从环境变量 / ``settings`` 读取，不要写死在代码里。
    2. **超时**：网络调用必须设 ``timeout``，避免页面一直卡住。
    3. **异常**：把 SDK 抛出的异常「翻译」成业务异常 ``LlmInvokeError``，
       让上层（Streamlit）可以用统一方式展示友好提示。
"""

from __future__ import annotations

import logging
from typing import Final

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from ai_cs_copilot.config import settings

# -----------------------------------------------------------------------------
# 日志：记录「发生了什么」，但绝不打印 API Key 或完整客户隐私字段
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# =============================================================================
# 示例 Prompt（企业项目中常把 Prompt 集中管理，便于评审与版本迭代）
# =============================================================================

# 系统提示词：定义角色、输出风格与合规边界
DEFAULT_SYSTEM_PROMPT: Final[str] = (
    "你是一名资深客户成功（Customer Success）经理，擅长 B2B SaaS 与订阅制业务。\n"
    "请基于用户提供的「客户经营与风险分析数据」，用专业、清晰的中文撰写经营分析报告。\n"
    "\n"
    "输出结构建议包含：\n"
    "1) 执行摘要（3-6 条要点）\n"
    "2) 关键发现（数据驱动，指出趋势/异常）\n"
    "3) 风险客户清单（客户编号 + 风险原因 + 建议动作）\n"
    "4) 分行业/分层的经营策略（可表格化）\n"
    "5) 30/60/90 天跟进计划（可表格化）\n"
    "\n"
    "硬性要求：\n"
    "- 不要编造数据中不存在的客户编号或指标；信息不足请明确写出假设。\n"
    "- 若数据样本较少，请在结论中提示「样本有限，建议扩大数据范围再决策」。\n"
)


def _build_default_user_prompt(*, customer_analysis_data: str, analysis_focus: str) -> str:
    """
    构造默认的用户提示词（把「分析侧重点」与「客户数据」拼装在一起）。

    参数:
        customer_analysis_data: 上游流水线整理好的客户分析文本（例如表格字符串）；
        analysis_focus: 本次分析希望模型额外关注的方向。

    返回:
        发送给模型的 user message 文本。
    """
    return (
        f"【分析侧重点】\n{analysis_focus}\n\n"
        f"【客户分析数据】\n{customer_analysis_data}\n\n"
        "请输出一份可直接发给内部管理层的经营分析报告（使用 Markdown 标题与列表）。"
    )


class LlmInvokeError(Exception):
    """
    大模型调用失败时抛出的业务异常。

    说明：
        - ``args[0]`` / str(exception) 默认等于 ``user_message``，便于 Streamlit 直接展示；
        - ``original_error`` 保留底层异常，便于排查（不要在 UI 上完整展示堆栈给最终用户）。
    """

    def __init__(self, user_message: str, *, original_error: BaseException | None = None) -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.original_error = original_error


def _is_placeholder_api_key(api_key: str) -> bool:
    """判断是否为明显占位符，避免误把示例配置当成真实密钥。"""
    key = (api_key or "").strip()
    if not key:
        return True
    lowered = key.lower()
    if lowered.startswith("sk-your") or lowered.startswith("your-"):
        return True
    if lowered in {"changeme", "replace_me", "placeholder"}:
        return True
    return False


def _create_deepseek_client() -> OpenAI:
    """
    创建 DeepSeek 的 OpenAI 兼容客户端。

    返回:
        已配置 api_key / base_url 的 ``OpenAI`` 实例。

    异常:
        LlmInvokeError: 当密钥缺失或为占位符时抛出。
    """
    if _is_placeholder_api_key(settings.deepseek_api_key):
        raise LlmInvokeError(
            "未检测到有效的 DEEPSEEK_API_KEY。请将 .env.example 复制为 .env，并填写 DeepSeek 密钥。",
        )

    # DeepSeek 官方推荐 base_url 为 https://api.deepseek.com（SDK 会自动拼接具体路径）
    base_url = settings.deepseek_base_url.rstrip("/")
    return OpenAI(api_key=settings.deepseek_api_key, base_url=base_url)


def generate_business_report(
    *,
    customer_analysis_data: str,
    analysis_focus: str | None = None,
    system_prompt: str | None = None,
) -> str:
    """
    调用 DeepSeek API，基于客户分析数据生成「AI 经营分析报告」。

    参数:
        customer_analysis_data: 客户分析数据（文本）。通常是 Pandas 汇总后的表格字符串，
            或上游规则引擎输出的要点列表；
        analysis_focus: 分析侧重点；若为空则使用内置默认描述；
        system_prompt: 可选自定义系统提示词；不传则使用 ``DEFAULT_SYSTEM_PROMPT``。

    返回:
        模型生成的 Markdown/纯文本报告。

    异常:
        LlmInvokeError: 参数不合法、鉴权失败、限流、超时、连接失败或服务端错误等。
    """
    # -------------------------- 入参校验（越早失败，越容易定位问题） --------------------------
    text = (customer_analysis_data or "").strip()
    if not text:
        raise LlmInvokeError("客户分析数据为空：请先加载数据并完成风险标注，再生成报告。")

    focus = (analysis_focus or "").strip() or "识别风险客户并给出可执行的经营改进建议与跟进节奏建议。"
    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    user_prompt = _build_default_user_prompt(customer_analysis_data=text, analysis_focus=focus)

    # -------------------------- 调用 DeepSeek（OpenAI 兼容 Chat Completions） --------------------------
    client = _create_deepseek_client()
    model = settings.deepseek_model

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            timeout=120.0,
        )
    except AuthenticationError as exc:
        # 401：密钥错误或未开通权限
        logger.warning("DeepSeek AuthenticationError: %s", exc.__class__.__name__)
        raise LlmInvokeError(
            "鉴权失败：请检查 .env 中的 DEEPSEEK_API_KEY 是否正确、是否已开通 API 权限。",
            original_error=exc,
        ) from exc
    except RateLimitError as exc:
        # 429：触发限流
        logger.warning("DeepSeek RateLimitError: %s", exc.__class__.__name__)
        raise LlmInvokeError(
            "触发限流：请求过于频繁或账户额度不足。请稍后重试，或到 DeepSeek 控制台检查用量。",
            original_error=exc,
        ) from exc
    except APITimeoutError as exc:
        logger.warning("DeepSeek APITimeoutError: %s", exc.__class__.__name__)
        raise LlmInvokeError(
            "请求超时：网络不稳定或服务响应过慢。请稍后重试，或适当减少纳入提示词的数据量。",
            original_error=exc,
        ) from exc
    except APIConnectionError as exc:
        logger.warning("DeepSeek APIConnectionError: %s", exc.__class__.__name__)
        raise LlmInvokeError(
            "网络连接失败：请检查本机网络、代理/VPN、防火墙，以及 DEEPSEEK_BASE_URL 是否可访问。",
            original_error=exc,
        ) from exc
    except APIError as exc:
        # 其他 4xx/5xx 或 SDK 包装的服务端错误
        logger.exception("DeepSeek APIError")
        raise LlmInvokeError(f"大模型服务返回错误：{str(exc)}", original_error=exc) from exc
    except Exception as exc:  # noqa: BLE001 — 兜底：避免 Streamlit 直接暴露难以理解的异常类型
        logger.exception("Unexpected error when calling DeepSeek")
        raise LlmInvokeError(
            "调用大模型时发生未知错误。请打开 DEBUG=true 查看服务端日志，或联系开发人员排查。",
            original_error=exc,
        ) from exc

    # -------------------------- 解析响应（兼容 content 为空的情况） --------------------------
    try:
        choice0 = completion.choices[0]
        content = choice0.message.content
    except (IndexError, AttributeError) as exc:
        raise LlmInvokeError("模型返回内容为空或结构异常：请重试，或检查模型名称是否正确。", original_error=exc) from exc

    if content is None or not str(content).strip():
        raise LlmInvokeError("模型返回内容为空：请重试，或尝试调整提示词/减少输入长度。")

    return str(content).strip()

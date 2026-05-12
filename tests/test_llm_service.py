# -*- coding: utf-8 -*-
"""
llm_service 单元测试（使用 Mock，避免真实调用 DeepSeek API）
============================================================
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


from ai_cs_copilot.services.llm_service import (  # noqa: E402
    LlmInvokeError,
    generate_business_report,
)


@pytest.fixture
def deepseek_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """注入一份「看起来像真实 key」的配置，避免触发占位符校验。"""
    monkeypatch.setattr(
        "ai_cs_copilot.services.llm_service.settings",
        SimpleNamespace(
            deepseek_api_key="sk-test-not-real-key",
            deepseek_base_url="https://api.deepseek.com",
            deepseek_model="deepseek-chat",
        ),
    )


def test_generate_business_report_success(deepseek_settings: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """成功路径：应调用 chat.completions.create，并返回模型文本。"""
    fake_completion = SimpleNamespace(
        choices=[
            SimpleNamespace(message=SimpleNamespace(content="# 经营分析报告\n生成成功。")),
        ]
    )
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_completion

    monkeypatch.setattr("ai_cs_copilot.services.llm_service.OpenAI", lambda **kwargs: fake_client)

    out = generate_business_report(customer_analysis_data="customer_id=C1, risk=高")
    assert "经营分析报告" in out
    fake_client.chat.completions.create.assert_called_once()
    kwargs = fake_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "deepseek-chat"
    assert len(kwargs["messages"]) == 2
    assert kwargs["messages"][0]["role"] == "system"
    assert kwargs["messages"][1]["role"] == "user"


def test_empty_customer_data_raises() -> None:
    """空数据应在调用 SDK 之前失败。"""
    with pytest.raises(LlmInvokeError) as excinfo:
        generate_business_report(customer_analysis_data="   ")
    assert "为空" in str(excinfo.value)


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """未配置密钥应给出明确提示。"""
    monkeypatch.setattr(
        "ai_cs_copilot.services.llm_service.settings",
        SimpleNamespace(
            deepseek_api_key="",
            deepseek_base_url="https://api.deepseek.com",
            deepseek_model="deepseek-chat",
        ),
    )
    with pytest.raises(LlmInvokeError) as excinfo:
        generate_business_report(customer_analysis_data="有数据")
    assert "DEEPSEEK_API_KEY" in str(excinfo.value)


def test_api_timeout_mapped_to_friendly_error(deepseek_settings: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """超时类异常应被包装为 LlmInvokeError（便于 Streamlit 展示）。"""
    from openai import APITimeoutError

    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = APITimeoutError("timeout")

    monkeypatch.setattr("ai_cs_copilot.services.llm_service.OpenAI", lambda **kwargs: fake_client)

    with pytest.raises(LlmInvokeError) as excinfo:
        generate_business_report(customer_analysis_data="customer_id=C1")
    assert "超时" in str(excinfo.value)

# -*- coding: utf-8 -*-
"""
配置模块（使用 python-dotenv + pydantic-settings）
====================================================

企业项目中常见做法：
1. 敏感信息（API Key）放在 .env，由 dotenv 加载到环境变量。
2. 用 Settings 类集中读取、校验配置，避免在业务代码里到处 os.getenv。

初学者提示：
    - ``load_dotenv()`` 会尝试从当前工作目录加载 .env 文件。
    - 若 Streamlit 从项目根目录启动，通常能正确找到根目录下的 .env。
"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_and_load_dotenv() -> None:
    """
    从项目根目录加载 .env 文件。

    说明：
        Streamlit 的工作目录一般是项目根；若从子目录运行脚本，
        这里会向上查找包含 .env 或 .env.example 的目录作为「项目根」的启发式参考。
    """
    # 本文件位于 src/ai_cs_copilot/config.py，向上两级通常为项目根（含 pyproject.toml）
    here = Path(__file__).resolve()
    for parent in [here.parent.parent.parent, *here.parents]:
        env_file = parent / ".env"
        if env_file.is_file():
            load_dotenv(env_file)
            return
    # 若未找到 .env，仍然调用一次 load_dotenv()：会从 cwd 查找
    load_dotenv()


_find_and_load_dotenv()


class Settings(BaseSettings):
    """
    应用全局配置。

    字段名与环境变量名默认一致（大写），例如 OPENAI_API_KEY。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI 或兼容接口的密钥（切勿打印到日志或界面）
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")

    # 兼容网关的基础 URL，末尾一般带 /v1
    openai_api_base: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="OPENAI_API_BASE",
    )

    # 模型名称，需与网关实际部署一致
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")

    # -------------------------------------------------------------------------
    # DeepSeek（OpenAI 兼容 SDK）：Streamlit「生成报告」默认走该配置
    # -------------------------------------------------------------------------
    # DeepSeek API Key（推荐单独命名，避免与其他供应商密钥混淆）
    deepseek_api_key: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")

    # DeepSeek OpenAI 兼容 Base URL（官方默认：https://api.deepseek.com）
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        validation_alias="DEEPSEEK_BASE_URL",
    )

    # DeepSeek 模型名（示例使用 deepseek-chat；若控制台有更新以控制台为准）
    deepseek_model: str = Field(default="deepseek-chat", validation_alias="DEEPSEEK_MODEL")

    # 调试模式：为 True 时可在日志中输出更多诊断信息（仍不要打印密钥）
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # SQLite 数据库文件路径（相对于项目根目录，由调用方解析为绝对路径）
    database_url: str = Field(
        default="sqlite:///storage/copilot.db",
        validation_alias="DATABASE_URL",
    )

    # 客户经营数据 CSV：相对项目根目录的路径，或 Windows/macOS 绝对路径（Streamlit 默认读取该文件）
    customer_data_csv: str = Field(
        default="data/sample_customer_data.csv",
        validation_alias="CUSTOMER_DATA_CSV",
    )


# 全局单例：各模块 ``from ai_cs_copilot.config import settings`` 即可
settings = Settings()

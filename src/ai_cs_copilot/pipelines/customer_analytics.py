# -*- coding: utf-8 -*-
"""
客户经营数据分析流水线
=======================

基于更新后的企业数据集，按以下维度评估客户：
- 登录活跃度（login_days）
- 产品功能采用率（ticket_usage_rate / marketing_usage_rate）
- 续费紧迫度（renewal_days_left）
- 投诉频率（complaint_count）
"""

from __future__ import annotations

from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd


class RiskLevel(str, Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


def load_customer_csv(csv_path: Path) -> pd.DataFrame:
    # utf-8-sig 兼容有 BOM 的 CSV（Excel 导出常带 BOM）
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    return df


def load_customer_csv_bytes(data: bytes, *, source_name: str = "uploaded.csv") -> pd.DataFrame:
    if not data or not data.strip():
        raise ValueError(f"CSV 内容为空：{source_name}")
    buffer: BinaryIO = BytesIO(data)
    try:
        return pd.read_csv(buffer, encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"CSV 编码解析失败（{source_name}）：请使用 UTF-8 保存文件，或在 Excel 中「另存为 CSV UTF-8」。"
        ) from exc


def _score_row(row: pd.Series) -> float:
    """
    根据新字段计算风险分数（分数越高越危险）。

    规则逻辑：
        - 登录天数过低 → 产品粘性不足
        - 工单/营销使用率过低 → 功能采用不佳，续费意愿低
        - 续费剩余天数 < 0 → 已逾期，流失风险极高
        - 投诉过多 → 满意度差
    """
    login_days = float(row.get("login_days", 0) or 0)
    ticket_rate = float(row.get("ticket_usage_rate", 0) or 0)
    marketing_rate = float(row.get("marketing_usage_rate", 0) or 0)
    renewal_days = float(row.get("renewal_days_left", 0) or 0)
    complaints = float(row.get("complaint_count", 0) or 0)

    score = 0.0

    # 登录天数 < 10 天，越少越危险
    if login_days < 10:
        score += (10 - login_days) * 1.5

    # 工单使用率 < 40% ，产品未被采纳
    if ticket_rate < 40:
        score += (40 - ticket_rate) * 0.3

    # 营销使用率 < 30%
    if marketing_rate < 30:
        score += (30 - marketing_rate) * 0.2

    # 续费已逾期（负数），每逾期一天加 0.5
    if renewal_days < 0:
        score += abs(renewal_days) * 0.5
    elif renewal_days < 30:
        score += (30 - renewal_days) * 0.3

    # 投诉超过 3 次，每多 1 次加 5 分
    if complaints > 3:
        score += (complaints - 3) * 5

    return score


def annotate_risk_levels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["risk_score"] = out.apply(_score_row, axis=1)

    def level_from_score(s: float) -> str:
        if s >= 25:
            return RiskLevel.HIGH.value
        if s >= 10:
            return RiskLevel.MEDIUM.value
        return RiskLevel.LOW.value

    out["risk_level"] = out["risk_score"].map(level_from_score)
    return out


def dataframe_to_brief_context(df: pd.DataFrame, max_rows: int = 8) -> str:
    """
    将部分客户数据压缩为给大模型阅读的简短上下文。
    """
    cols = [
        c
        for c in [
            "customer_name",
            "industry",
            "monthly_gmv",
            "login_days",
            "ticket_usage_rate",
            "marketing_usage_rate",
            "renewal_days_left",
            "complaint_count",
            "risk_level",
        ]
        if c in df.columns
    ]
    sample = df[cols].head(max_rows)
    return sample.to_string(index=False)

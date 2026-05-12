# -*- coding: utf-8 -*-
"""
客户分析模块的单元测试（入门示例）
====================================
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# 允许在未安装为包的情况下运行 pytest
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ai_cs_copilot.pipelines.customer_analytics import RiskLevel, annotate_risk_levels


def test_annotate_risk_levels_adds_columns() -> None:
    """验证风险标注会新增 risk_score 与 risk_level 列。"""
    # 构造「极端负面指标」，使 risk_score >= 25，对应风险等级「高」
    df = pd.DataFrame(
        [
            {
                "customer_id": "X1",
                "active_days_30d": 0,
                "revenue_mom_pct": -40,
                "support_tickets_30d": 12,
            }
        ]
    )
    out = annotate_risk_levels(df)
    assert "risk_score" in out.columns
    assert "risk_level" in out.columns
    assert out.loc[0, "risk_level"] == RiskLevel.HIGH.value

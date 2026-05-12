# -*- coding: utf-8 -*-
"""data_paths 模块单元测试"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from ai_cs_copilot.pipelines.data_paths import resolve_customer_csv_path  # noqa: E402


def test_resolve_relative_to_project_root() -> None:
    root = Path("D:/proj")
    p = resolve_customer_csv_path(root, "data/x.csv")
    assert p == (root / "data" / "x.csv").resolve()


def test_resolve_absolute() -> None:
    root = Path("D:/proj")
    p = resolve_customer_csv_path(root, "D:/other/y.csv")
    assert p.name == "y.csv"


def test_resolve_empty_falls_back_to_sample() -> None:
    root = Path("D:/proj")
    p = resolve_customer_csv_path(root, "  ")
    assert "sample_customer_data.csv" in p.name

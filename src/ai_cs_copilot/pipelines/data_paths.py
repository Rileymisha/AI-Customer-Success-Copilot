# -*- coding: utf-8 -*-
"""
客户数据文件路径解析
====================

将 .env 或 Streamlit 文本框中的「相对 / 绝对路径」统一解析为 ``Path``，
供 ``load_customer_csv`` 使用。
"""

from __future__ import annotations

from pathlib import Path


def resolve_customer_csv_path(project_root: Path, path_str: str) -> Path:
    """
    将用户或配置中的路径字符串解析为绝对 Path。

    规则：
        - 空字符串：回退到项目内示例文件 ``data/sample_customer_data.csv``；
        - 绝对路径（含盘符）：直接 ``resolve()``；
        - 否则视为相对 ``project_root`` 的路径（例如 ``data/my.csv``）。
    """
    raw = (path_str or "").strip()
    if not raw:
        return (project_root / "data" / "sample_customer_data.csv").resolve()
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate.resolve()
    return (project_root / candidate).resolve()

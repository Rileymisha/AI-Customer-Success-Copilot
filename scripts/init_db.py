# -*- coding: utf-8 -*-
"""
数据库初始化脚本
================

在项目根目录执行::

    python scripts/init_db.py

作用：
    创建 ``storage/copilot.db`` 并初始化分析报告的表结构。

初学者提示：
    将「一次性运维操作」放在 scripts/ 目录，是常见企业项目习惯。
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    # 将 src 加入 Python 路径，便于在未 pip install -e . 时直接运行
    root = Path(__file__).resolve().parents[1]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from ai_cs_copilot.db.sqlite_store import SQLiteStore

    db_path = root / "storage" / "copilot.db"
    store = SQLiteStore(db_path)
    store.init_schema()
    print(f"数据库已就绪：{db_path}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
SQLite 持久化存储
=================

用途：
    将「分析报告生成记录」等结构化数据存入本地 SQLite，
    便于审计、回放与后续扩展为多用户场景。

初学者提示：
    sqlite3 是 Python 标准库，无需额外安装数据库服务，适合原型与企业内网部署。
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterable, Mapping


class SQLiteStore:
    """
    轻量级 SQLite 访问封装。

    参数:
        db_path: 数据库文件的绝对路径。
    """

    def __init__(self, db_path: Path) -> None:
        # 确保父目录存在，否则 connect 可能失败
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取数据库连接的上下文管理器。

        使用 ``with store.connect() as conn:`` 可自动提交/关闭。
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """
        初始化数据表（若不存在则创建）。

        当前表：
            - analysis_reports：保存每次生成的报告摘要与正文片段。
        """
        ddl = """
        CREATE TABLE IF NOT EXISTS analysis_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            risk_level TEXT,
            summary TEXT,
            report_excerpt TEXT,
            model_name TEXT,
            created_at TEXT NOT NULL
        );
        """
        with self.connect() as conn:
            conn.execute(ddl)

    def insert_report(
        self,
        *,
        customer_id: str,
        risk_level: str,
        summary: str,
        report_excerpt: str,
        model_name: str,
    ) -> int:
        """
        插入一条分析报告记录。

        返回:
            新插入行的自增主键 id。
        """
        created_at = datetime.now(timezone.utc).isoformat()
        sql = """
        INSERT INTO analysis_reports
        (customer_id, risk_level, summary, report_excerpt, model_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        with self.connect() as conn:
            cur = conn.execute(
                sql,
                (customer_id, risk_level, summary, report_excerpt, model_name, created_at),
            )
            return int(cur.lastrowid)

    def list_recent_reports(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        查询最近若干条报告记录，按时间倒序。

        返回:
            每行转为普通 dict，便于 Streamlit 展示。
        """
        sql = """
        SELECT id, customer_id, risk_level, summary, model_name, created_at
        FROM analysis_reports
        ORDER BY id DESC
        LIMIT ?;
        """
        with self.connect() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
        return [dict(r) for r in rows]

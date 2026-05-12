# -*- coding: utf-8 -*-
"""
Markdown 报告生成器
====================

将工作流分析结果格式化为结构化 Markdown 企业报告。
支持嵌入图表、AI 洞察、风险分类与行动建议。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Markdown 报告生成器。

    接收工作流的分析上下文，生成结构化企业报告。
    """

    def generate(
        self,
        df: pd.DataFrame,
        categories: dict[str, Any],
        insights: str,
        chart_paths: dict[str, str],
        data_source: str = "sample_customer_data.csv",
        output_path: str | Path = "reports/enterprise_report.md",
    ) -> str:
        """
        生成完整的 Markdown 企业报告。

        参数:
            df: 已标注风险的客户数据
            categories: 分类结果 {"high_risk": [...], "high_value": [...], "growth": [...]}
            insights: AI 生成的经营洞察文本
            chart_paths: 图表路径 {"gmv_bar": ..., "risk_pie": ..., ...}
            data_source: 数据来源说明
            output_path: 输出路径

        返回:
            写入的文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        high_risk = categories.get("high_risk", [])
        high_value = categories.get("high_value", [])
        growth = categories.get("growth", [])

        # ---------- 统计指标 ----------
        total = len(df)
        risk_counts = df["risk_level"].value_counts().to_dict()
        avg_gmv = df["monthly_gmv"].mean()
        high_complaint = len(df[df["complaint_count"] > 3])

        lines: list[str] = [
            "# 企业经营分析报告",
            "",
            f"**生成时间**：{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**数据来源**：{data_source}",
            "",
            "---",
            "",
            "## 一、执行摘要",
            "",
            f"本次共分析 **{total}** 个客户，覆盖 "
            f"{df['industry'].nunique()} 个行业、{df['region'].nunique()} 个区域。",
            "",
            "| 指标 | 数值 |",
            "|---|---|",
            f"| 客户总数 | {total} |",
            f"| 高风险客户 | {len(high_risk)} |",
            f"| 高价值客户 | {len(high_value)} |",
            f"| 增长潜力客户 | {len(growth)} |",
            f"| 月均 GMV | ¥{avg_gmv:,.0f} |",
            f"| 高投诉客户（>3 次） | {high_complaint} |",
            "",
        ]

        # ---------- 风险分布 ----------
        lines.extend([
            "## 二、客户风险分布",
            "",
            f"![客户风险分布]({chart_paths.get('risk_pie', '')})",
            "",
            "| 风险等级 | 数量 | 占比 |",
            "|---|---|---|",
        ])
        for level in ["高", "中", "低"]:
            count = risk_counts.get(level, 0)
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"| {level} | {count} | {pct:.1f}% |")
        lines.append("")

        # ---------- 高风险客户 ----------
        if high_risk:
            lines.extend([
                "## 三、高风险客户清单",
                "",
                "以下客户需优先干预：",
                "",
                "| 客户 | 行业 | GMV | 登录天数 | 投诉次数 | 续约状态 | 建议动作 |",
                "|---|---|---|---|---|---|---|",
            ])
            for c in high_risk:
                lines.append(
                    f"| {c.get('customer_name', '')} "
                    f"| {c.get('industry', '')} "
                    f"| ¥{c.get('monthly_gmv', 0):,} "
                    f"| {c.get('login_days', '')}天 "
                    f"| {c.get('complaint_count', '')}次 "
                    f"| {'已逾期' if c.get('renewal_days_left', 0) < 0 else '正常'} "
                    f"| {c.get('suggestion', '优先跟进')} |"
                )
            lines.append("")

        # ---------- 高价值客户 ----------
        if high_value:
            lines.extend([
                "## 四、高价值客户",
                "",
                "以下客户是收入核心贡献者，需重点维护：",
                "",
            ])
            for c in high_value:
                lines.append(
                    f"- **{c.get('customer_name', '')}**"
                    f" — 月 GMV ¥{c.get('monthly_gmv', 0):,}"
                    f"，{c.get('industry', '')}行业"
                    f"，登录活跃 {c.get('login_days', 0)}/月"
                )
            lines.append("")

        # ---------- 增长客户 ----------
        if growth:
            lines.extend([
                "## 五、增长潜力客户",
                "",
                "以下客户使用活跃度高，具备升级或扩展潜力：",
                "",
            ])
            for c in growth:
                lines.append(
                    f"- **{c.get('customer_name', '')}**"
                    f" — 月 GMV ¥{c.get('monthly_gmv', 0):,}"
                    f"，功能采用率 {c.get('ticket_usage_rate', 0)}%"
                )
            lines.append("")

        # ---------- 行业与区域 ----------
        lines.extend([
            "## 六、行业与区域分析",
            "",
            f"![行业分布]({chart_paths.get('industry_bar', '')})",
            "",
            f"![区域分布]({chart_paths.get('region_bar', '')})",
            "",
            f"![GMV 排行]({chart_paths.get('gmv_bar', '')})",
            "",
        ])

        # ---------- AI 洞察 ----------
        lines.extend([
            "## 七、AI 经营洞察",
            "",
            insights,
            "",
        ])

        # ---------- 行动计划 ----------
        lines.extend([
            "---",
            "## 八、行动计划",
            "",
        ])
        if high_risk:
            lines.append(
                f"### 紧急（本周）\n"
                f"- 对 **{len(high_risk)} 个高风险客户** 启动 1 对 1 挽回流程\n"
                f"- CSM 主管 + 销售总监联合跟进\n"
            )
        lines.extend([
            "### 短期（本月）\n"
            "- 高价值客户季度复盘\n"
            "- 增长潜力客户 CSM 重点辅导\n"
            "- 高风险客户专项改善计划追踪\n",
            "",
            "### 长期（本季度）\n"
            "- 优化产品 onboarding 流程，降低低登录率\n"
            "- 建立客户健康度监控体系\n"
            "- 行业标杆案例传播，提升整体活跃度\n",
        ])

        # ---------- 页脚 ----------
        lines.extend([
            "---",
            "*本报告由 AI-Customer-Success-Copilot Enterprise Reporting System 自动生成*",
            "",
        ])

        content = "\n".join(lines)
        output_path.write_text(content, encoding="utf-8")
        logger.info("企业报告已保存: %s", output_path)
        return str(output_path)

# -*- coding: utf-8 -*-
"""
PPT 报告生成器
==============

使用 python-pptx 自动生成企业经营分析演示文稿，
包含封面、风险分析、数据趋势、AI 建议、行动计划等幻灯片。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 颜色方案
# ---------------------------------------------------------------------------
_COLOR_PRIMARY = RGBColor(0x2C, 0x3E, 0x50)   # 深蓝灰
_COLOR_ACCENT = RGBColor(0x34, 0x98, 0xDB)    # 蓝色强调
_COLOR_RED = RGBColor(0xE7, 0x4C, 0x3C)       # 红色（高风险）
_COLOR_GREEN = RGBColor(0x2E, 0xCC, 0x71)     # 绿色（低风险）
_COLOR_ORANGE = RGBColor(0xF3, 0x9C, 0x12)    # 橙色（中风险）
_COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
_COLOR_LIGHT_GRAY = RGBColor(0xEC, 0xF0, 0xF1)
_COLOR_DARK = RGBColor(0x2C, 0x3E, 0x50)


class PPTGenerator:
    """
    PPT 报告生成器。

    用法::

        gen = PPTGenerator()
        gen.generate(context, "reports/enterprise_report.pptx")
    """

    def __init__(self) -> None:
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.33)
        self.prs.slide_height = Inches(7.5)

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def generate(
        self,
        df: Any,
        categories: dict[str, Any],
        insights: str,
        chart_paths: dict[str, str],
        output_path: str | Path = "reports/enterprise_report.pptx",
    ) -> str:
        """
        生成完整 PPT。

        参数:
            df: 客户数据 DataFrame
            categories: 分类结果
            insights: AI 洞察文本
            chart_paths: 图表路径
            output_path: 输出路径

        返回:
            PPT 文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import pandas as pd
        total = len(df)
        high_risk = categories.get("high_risk", [])
        high_value = categories.get("high_value", [])
        growth = categories.get("growth", [])

        # ---- 各页幻灯片 ----
        self._add_cover(total, high_risk, high_value, growth)
        self._add_executive_summary(total, high_risk, high_value, growth, df)
        self._add_risk_chart_slide(chart_paths.get("risk_pie", ""))
        self._add_high_risk_detail(high_risk)
        self._add_high_value_slide(high_value)
        self._add_charts_slide(chart_paths)
        self._add_ai_insights(insights)
        self._add_action_plan(high_risk)
        self._add_closing()

        self.prs.save(str(output_path))
        logger.info("PPT 已保存: %s", output_path)
        return str(output_path)

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _add_slide(self) -> Any:
        """添加空白幻灯片。"""
        layout = self.prs.slide_layouts[6]  # blank
        return self.prs.slides.add_slide(layout)

    def _add_title_bar(self, slide: Any, title: str) -> None:
        """在幻灯片顶部添加标题栏。"""
        bar = slide.shapes.add_shape(
            1, Inches(0), Inches(0), self.prs.slide_width, Inches(1.0)
        )
        bar.fill.solid()
        bar.fill.fore_color.rgb = _COLOR_PRIMARY
        bar.line.fill.background()

        txBox = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.15), Inches(12), Inches(0.7)
        )
        tf = txBox.text_frame
        tf.text = title
        tf.paragraphs[0].font.size = Pt(28)
        tf.paragraphs[0].font.color.rgb = _COLOR_WHITE
        tf.paragraphs[0].font.bold = True

    def _add_body_text(
        self, slide: Any, left: float, top: float, width: float, height: float,
        text: str, font_size: int = 14,
    ) -> None:
        """添加正文文本框。"""
        txBox = slide.shapes.add_textbox(
            Inches(left), Inches(top), Inches(width), Inches(height)
        )
        tf = txBox.text_frame
        tf.word_wrap = True
        for i, line in enumerate(text.strip().split("\n")):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.text = line
            p.font.size = Pt(font_size)
            p.font.color.rgb = _COLOR_DARK
            p.space_after = Pt(4)

    # ------------------------------------------------------------------
    # 各页幻灯片
    # ------------------------------------------------------------------

    def _add_cover(self, total: int, high_risk: list, high_value: list, growth: list) -> None:
        """封面页。"""
        slide = self._add_slide()
        # 背景色
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = _COLOR_PRIMARY

        # 主标题
        txBox = slide.shapes.add_textbox(
            Inches(1), Inches(1.5), Inches(11), Inches(1.5)
        )
        tf = txBox.text_frame
        tf.text = "企业经营分析报告"
        tf.paragraphs[0].font.size = Pt(44)
        tf.paragraphs[0].font.color.rgb = _COLOR_WHITE
        tf.paragraphs[0].font.bold = True
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER

        # 副标题
        import pandas as pd
        txBox2 = slide.shapes.add_textbox(
            Inches(1), Inches(3.2), Inches(11), Inches(1.0)
        )
        tf2 = txBox2.text_frame
        tf2.text = f"AI-Customer-Success-Copilot 自动生成  |  {pd.Timestamp.now().strftime('%Y-%m-%d')}"
        tf2.paragraphs[0].font.size = Pt(18)
        tf2.paragraphs[0].font.color.rgb = _COLOR_LIGHT_GRAY
        tf2.paragraphs[0].alignment = PP_ALIGN.CENTER

        # 关键数字
        metrics = [
            (f"{total}", "总客户数"),
            (f"{len(high_risk)}", "高风险客户"),
            (f"{len(high_value)}", "高价值客户"),
            (f"{len(growth)}", "增长客户"),
        ]
        for i, (num, label) in enumerate(metrics):
            x = 1.5 + i * 3
            txNum = slide.shapes.add_textbox(
                Inches(x), Inches(4.8), Inches(2.5), Inches(0.8)
            )
            tfNum = txNum.text_frame
            tfNum.text = num
            tfNum.paragraphs[0].font.size = Pt(36)
            tfNum.paragraphs[0].font.color.rgb = _COLOR_ACCENT
            tfNum.paragraphs[0].font.bold = True
            tfNum.paragraphs[0].alignment = PP_ALIGN.CENTER

            txLabel = slide.shapes.add_textbox(
                Inches(x), Inches(5.5), Inches(2.5), Inches(0.5)
            )
            tfLabel = txLabel.text_frame
            tfLabel.text = label
            tfLabel.paragraphs[0].font.size = Pt(14)
            tfLabel.paragraphs[0].font.color.rgb = _COLOR_LIGHT_GRAY
            tfLabel.paragraphs[0].alignment = PP_ALIGN.CENTER

    def _add_executive_summary(
        self, total: int, high_risk: list, high_value: list, growth: list, df: Any,
    ) -> None:
        """执行摘要页。"""
        slide = self._add_slide()
        self._add_title_bar(slide, "执行摘要")

        import pandas as pd
        avg_gmv = df["monthly_gmv"].mean()
        risk_counts = df["risk_level"].value_counts().to_dict()

        text = (
            f"本次共分析 {total} 个客户，覆盖 "
            f"{df['industry'].nunique()} 个行业、{df['region'].nunique()} 个区域。\n\n"
            f"客户风险分布：高风险 {risk_counts.get('高', 0)} 个、"
            f"中风险 {risk_counts.get('中', 0)} 个、"
            f"低风险 {risk_counts.get('低', 0)} 个\n\n"
            f"月均 GMV：¥{avg_gmv:,.0f}\n"
            f"高价值客户：{len(high_value)} 个\n"
            f"增长潜力客户：{len(growth)} 个"
        )
        self._add_body_text(slide, 0.8, 1.3, 11, 5, text, font_size=16)

    def _add_risk_chart_slide(self, chart_path: str) -> None:
        """风险分布图表页。"""
        slide = self._add_slide()
        self._add_title_bar(slide, "客户风险分布")

        if chart_path:
            slide.shapes.add_picture(
                chart_path, Inches(1.5), Inches(1.5), Inches(5), Inches(5)
            )

        text = (
            "风险等级定义：\n\n"
            "• 高风险：续费逾期 / 登录天数 < 5 / 投诉 > 8\n"
            "• 中风险：部分指标不达标，需关注\n"
            "• 低风险：正常经营，常规维护\n\n"
            "重点关注：高风险客户需立即启动挽回流程"
        )
        self._add_body_text(slide, 7.5, 1.5, 5, 5, text, font_size=14)

    def _add_high_risk_detail(self, high_risk: list) -> None:
        """高风险客户详情页。"""
        slide = self._add_slide()
        self._add_title_bar(slide, f"高风险客户（{len(high_risk)} 个）")

        if not high_risk:
            self._add_body_text(slide, 0.8, 1.5, 11, 1, "暂无高风险客户。")
            return

        # 表格
        rows = min(len(high_risk) + 1, 11)
        cols = 6
        table = slide.shapes.add_table(
            rows, cols, Inches(0.5), Inches(1.3), Inches(12), Inches(5.5)
        ).table

        headers = ["客户名称", "行业", "月 GMV", "登录天数", "投诉", "建议动作"]
        for j, h in enumerate(headers):
            cell = table.cell(0, j)
            cell.text = h
            cell.fill.solid()
            cell.fill.fore_color.rgb = _COLOR_PRIMARY
            for p in cell.text_frame.paragraphs:
                p.font.color.rgb = _COLOR_WHITE
                p.font.bold = True
                p.font.size = Pt(11)

        for i, c in enumerate(high_risk[:10]):
            vals = [
                str(c.get("customer_name", "")),
                str(c.get("industry", "")),
                f"¥{c.get('monthly_gmv', 0):,}",
                f"{c.get('login_days', '')}天",
                f"{c.get('complaint_count', '')}次",
                "紧急跟进",
            ]
            for j, v in enumerate(vals):
                cell = table.cell(i + 1, j)
                cell.text = v
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(10)
                    p.font.color.rgb = _COLOR_DARK

    def _add_high_value_slide(self, high_value: list) -> None:
        """高价值客户页。"""
        slide = self._add_slide()
        self._add_title_bar(slide, f"高价值客户（{len(high_value)} 个）")

        if not high_value:
            self._add_body_text(slide, 0.8, 1.5, 11, 1, "暂无高价值客户。")
            return

        text_lines = []
        for c in high_value:
            text_lines.append(
                f"• {c.get('customer_name', '')}"
                f"  |  月 GMV ¥{c.get('monthly_gmv', 0):,}"
                f"  |  {c.get('industry', '')}"
                f"  |  活跃 {c.get('login_days', 0)}天"
            )
        self._add_body_text(slide, 0.8, 1.3, 11, 5, "\n".join(text_lines), font_size=14)

        # 建议
        note = (
            "\n\n维护建议：配备专属 CSM | 季度高层拜访 | 提前 90 天续约 | 优先响应需求"
        )
        self._add_body_text(slide, 0.8, 6.0, 11, 1, note, font_size=12)

    def _add_charts_slide(self, chart_paths: dict[str, str]) -> None:
        """行业与区域分析页。"""
        slide = self._add_slide()
        self._add_title_bar(slide, "行业与区域分析")

        # 两张图并排
        if chart_paths.get("industry_bar"):
            slide.shapes.add_picture(
                chart_paths["industry_bar"],
                Inches(0.3), Inches(1.3), Inches(6.2), Inches(3.8),
            )
        if chart_paths.get("region_bar"):
            slide.shapes.add_picture(
                chart_paths["region_bar"],
                Inches(6.8), Inches(1.3), Inches(6.2), Inches(3.8),
            )
        if chart_paths.get("gmv_bar"):
            slide.shapes.add_picture(
                chart_paths["gmv_bar"],
                Inches(2), Inches(5.2), Inches(9), Inches(2.2),
            )

    def _add_ai_insights(self, insights: str) -> None:
        """AI 经营洞察页。"""
        slide = self._add_slide()
        self._add_title_bar(slide, "AI 经营洞察")
        self._add_body_text(slide, 0.8, 1.3, 11.5, 5.5, insights, font_size=13)

    def _add_action_plan(self, high_risk: list) -> None:
        """行动计划页。"""
        slide = self._add_slide()
        self._add_title_bar(slide, "行动计划")

        urgent_text = (
            "### 紧急（本周）\n"
            f"1. 对 {len(high_risk)} 个高风险客户启动 1 对 1 挽回流程\n"
            "2. CSM 主管 + 销售总监联合跟进逾期客户\n"
            "3. 投诉客户 48 小时内完成闭环"
        )
        short_text = (
            "### 短期（本月）\n"
            "1. 高价值客户季度复盘会议\n"
            "2. 增长潜力客户 CSM 重点辅导计划\n"
            "3. 高风险客户专项改善方案实施"
        )
        long_text = (
            "### 长期（本季度）\n"
            "1. 产品 Onboarding 流程优化\n"
            "2. 客户健康度监控体系上线\n"
            "3. 行业标杆案例传播推广"
        )

        self._add_body_text(slide, 0.8, 1.3, 5.5, 5, urgent_text, font_size=13)
        self._add_body_text(slide, 6.8, 1.3, 5.5, 5, short_text, font_size=13)
        self._add_body_text(slide, 0.8, 4.5, 11, 2.5, long_text, font_size=13)

    def _add_closing(self) -> None:
        """结束页。"""
        slide = self._add_slide()
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = _COLOR_PRIMARY

        txBox = slide.shapes.add_textbox(
            Inches(1), Inches(2.5), Inches(11), Inches(2)
        )
        tf = txBox.text_frame
        tf.text = "谢谢"
        tf.paragraphs[0].font.size = Pt(48)
        tf.paragraphs[0].font.color.rgb = _COLOR_WHITE
        tf.paragraphs[0].font.bold = True
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER

        txBox2 = slide.shapes.add_textbox(
            Inches(1), Inches(4.5), Inches(11), Inches(1)
        )
        tf2 = txBox2.text_frame
        tf2.text = "本报告由 AI_CS_Copilot Enterprise Reporting 自动生成"
        tf2.paragraphs[0].font.size = Pt(14)
        tf2.paragraphs[0].font.color.rgb = _COLOR_LIGHT_GRAY
        tf2.paragraphs[0].alignment = PP_ALIGN.CENTER

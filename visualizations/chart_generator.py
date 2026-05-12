# -*- coding: utf-8 -*-
"""
数据可视化图表生成器
=====================

使用 matplotlib 生成企业分析所需的各类图表，
保存为 PNG 图片供 PPT 和 Markdown 报告引用。

功能:
- GMV 排行柱状图
- 风险分布饼图
- 行业分布柱状图
- 区域分布柱状图
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 设置 matplotlib 非交互后端（避免 GUI 弹窗）
matplotlib.use("Agg")

# 中文字体设置（按优先级尝试多个系统字体）
_ZH_FONTS = [
    "Microsoft YaHei",      # Windows
    "SimHei",               # Windows
    "WenQuanYi Micro Hei",  # Linux
    "Noto Sans CJK SC",     # Linux
    "Noto Sans SC",         # Linux
    "DejaVu Sans",          # Fallback
]
for _f in _ZH_FONTS:
    try:
        plt.rcParams["font.sans-serif"] = [_f]
        plt.rcParams["axes.unicode_minus"] = False
        # 快速验证字体是否可用
        fig, ax = plt.subplots(figsize=(0.1, 0.1))
        ax.set_title("测")
        plt.close(fig)
        break
    except Exception:
        continue

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 颜色方案
# ---------------------------------------------------------------------------
_RISK_COLORS: dict[str, str] = {
    "高": "#E74C3C",  # 红色
    "中": "#F39C12",  # 橙色
    "低": "#2ECC71",  # 绿色
}

_BAR_COLOR: str = "#3498DB"       # 柱状图主色
_BAR_COLOR_HIGHLIGHT: str = "#E74C3C"  # 高亮色


class ChartGenerator:
    """
    图表生成器。

    用法::

        gen = ChartGenerator(output_dir="visualizations")
        chart_paths = gen.generate_all(df)
    """

    def __init__(self, output_dir: str | Path = "visualizations") -> None:
        """
        参数:
            output_dir: 图表输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 公共入口
    # ------------------------------------------------------------------

    def generate_all(self, df: pd.DataFrame) -> dict[str, str]:
        """
        生成全套图表，返回图片路径字典。

        参数:
            df: 已标注风险的客户数据（需含 risk_level, monthly_gmv, industry, region 列）

        返回::

            {
                "gmv_bar": "visualizations/gmv_bar.png",
                "risk_pie": "visualizations/risk_pie.png",
                "industry_bar": "visualizations/industry_bar.png",
                "region_bar": "visualizations/region_bar.png",
            }
        """
        return {
            "gmv_bar": self.create_gmv_bar_chart(df),
            "risk_pie": self.create_risk_pie_chart(df),
            "industry_bar": self.create_industry_chart(df),
            "region_bar": self.create_region_chart(df),
        }

    # ------------------------------------------------------------------
    # GMV 排行柱状图
    # ------------------------------------------------------------------

    def create_gmv_bar_chart(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        filename: str = "gmv_bar.png",
    ) -> str:
        """
        绘制月度 GMV 前 N 名客户柱状图。

        参数:
            df: 客户数据
            top_n: 显示前几名（默认 10）
            filename: 输出文件名

        返回:
            图片文件的绝对/相对路径
        """
        sorted_df = df.sort_values("monthly_gmv", ascending=False).head(top_n)

        fig, ax = plt.subplots(figsize=(12, 6))

        names = sorted_df["customer_name"].tolist()
        values = sorted_df["monthly_gmv"].tolist()

        bars = ax.barh(
            range(len(names)),
            values,
            color=_BAR_COLOR,
            edgecolor="white",
            height=0.6,
        )

        # 高亮前三名
        for i in range(min(3, len(bars))):
            bars[i].set_color(_BAR_COLOR_HIGHLIGHT)

        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(names, fontsize=10)
        ax.invert_yaxis()  # 最高的在最上面
        ax.set_xlabel("月 GMV（元）", fontsize=12)
        ax.set_title(f"月度 GMV 前 {top_n} 名客户", fontsize=14, fontweight="bold")
        ax.grid(axis="x", alpha=0.3)

        # 在柱状末端标注数值
        for i, v in enumerate(values):
            ax.text(v + 5000, i, f"¥{v:,.0f}", va="center", fontsize=9)

        plt.tight_layout()
        output_path = str(self.output_dir / filename)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("GMV 柱状图已保存: %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # 风险分布饼图
    # ------------------------------------------------------------------

    def create_risk_pie_chart(
        self,
        df: pd.DataFrame,
        filename: str = "risk_pie.png",
    ) -> str:
        """
        绘制客户风险等级分布饼图。

        参数:
            df: 需含 risk_level 列
            filename: 输出文件名
        """
        if "risk_level" not in df.columns:
            raise ValueError("数据缺少 risk_level 列，请先调用 annotate_risk_levels")

        counts = df["risk_level"].value_counts()
        labels = counts.index.tolist()
        sizes = counts.values.tolist()
        colors = [_RISK_COLORS.get(l, "#95A5A6") for l in labels]

        fig, ax = plt.subplots(figsize=(8, 8))

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            textprops={"fontsize": 12},
        )
        for t in autotexts:
            t.set_color("white")
            t.set_fontweight("bold")

        ax.set_title("客户风险等级分布", fontsize=14, fontweight="bold")

        plt.tight_layout()
        output_path = str(self.output_dir / filename)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("风险饼图已保存: %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # 行业分布柱状图
    # ------------------------------------------------------------------

    def create_industry_chart(
        self,
        df: pd.DataFrame,
        filename: str = "industry_bar.png",
    ) -> str:
        """
        绘制行业客户数量分布图。
        """
        if "industry" not in df.columns:
            raise ValueError("数据缺少 industry 列")

        counts = df["industry"].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = plt.cm.Set2(np.linspace(0, 1, len(counts)))

        bars = ax.bar(
            range(len(counts)),
            counts.values,
            color=colors,
            edgecolor="white",
            width=0.6,
        )

        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels(counts.index.tolist(), fontsize=10, rotation=20)
        ax.set_ylabel("客户数量", fontsize=12)
        ax.set_title("客户行业分布", fontsize=14, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

        for bar, v in zip(bars, counts.values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,
                str(v),
                ha="center",
                fontsize=10,
            )

        plt.tight_layout()
        output_path = str(self.output_dir / filename)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("行业分布图已保存: %s", output_path)
        return output_path

    # ------------------------------------------------------------------
    # 区域分布柱状图
    # ------------------------------------------------------------------

    def create_region_chart(
        self,
        df: pd.DataFrame,
        filename: str = "region_bar.png",
    ) -> str:
        """
        绘制区域客户数量分布图。
        """
        if "region" not in df.columns:
            raise ValueError("数据缺少 region 列")

        counts = df["region"].value_counts()

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = plt.cm.Pastel1(np.linspace(0, 1, len(counts)))

        bars = ax.bar(
            range(len(counts)),
            counts.values,
            color=colors,
            edgecolor="gray",
            width=0.6,
        )

        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels(counts.index.tolist(), fontsize=10)
        ax.set_ylabel("客户数量", fontsize=12)
        ax.set_title("客户区域分布", fontsize=14, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)

        for bar, v in zip(bars, counts.values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,
                str(v),
                ha="center",
                fontsize=10,
            )

        plt.tight_layout()
        output_path = str(self.output_dir / filename)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        logger.info("区域分布图已保存: %s", output_path)
        return output_path

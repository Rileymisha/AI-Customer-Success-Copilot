# -*- coding: utf-8 -*-
"""
AI-Customer-Success-Copilot — Streamlit 应用入口
====================================

运行方式（在项目根目录）::

    streamlit run app.py

说明：
    本文件负责「页面编排」：加载数据、调用分析模块与大模型、展示结果。
    「生成报告」按钮会调用 ``services/llm_service.py``，通过 **OpenAI 兼容 SDK**
    请求 **DeepSeek**（默认 ``https://api.deepseek.com`` + ``deepseek-chat``）。
    复杂业务逻辑请放在 ``src/ai_cs_copilot/`` 中，便于测试与复用。

初学者提示：
    Streamlit 是「脚本式」UI：从上到下执行，交互控件会触发重新运行整页脚本。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# 路径设置：确保可以 import 本地包 ai_cs_copilot（无需先 pip install -e .）
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_cs_copilot.config import settings  # noqa: E402
from ai_cs_copilot.db.sqlite_store import SQLiteStore  # noqa: E402
from ai_cs_copilot.pipelines.customer_analytics import (  # noqa: E402
    annotate_risk_levels,
    dataframe_to_brief_context,
    load_customer_csv,
    load_customer_csv_bytes,
)
from ai_cs_copilot.pipelines.data_paths import resolve_customer_csv_path  # noqa: E402
from ai_cs_copilot.services.llm_service import LlmInvokeError, generate_business_report  # noqa: E402

# 企业报告系统（图表 + Markdown + PPT）
from services.report_generator import ReportGenerator  # noqa: E402
from services.ppt_generator import PPTGenerator  # noqa: E402
from visualizations.chart_generator import ChartGenerator  # noqa: E402


def get_sqlite_store() -> SQLiteStore:
    """构造 SQLite 存储路径（与 scripts/init_db.py 保持一致）。"""
    db_path = PROJECT_ROOT / "storage" / "copilot.db"
    store = SQLiteStore(db_path)
    store.init_schema()
    return store


def main() -> None:
    """应用主函数：配置页面、侧边栏、主体内容。"""
    st.set_page_config(
        page_title="AI 客户成功助手",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("AI-Customer-Success-Copilot — AI 客户成功助手")
    st.caption("分析客户经营数据 · 识别风险 · 生成经营建议与报告草案")

    # -------------------------------------------------------------------------
    # 侧边栏：配置与说明（把「不常改」的内容放侧边栏是常见布局）
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.header("项目说明")
        st.markdown(
            """
            - **数据**：上传 CSV 覆盖默认文件，或用环境变量 ``CUSTOMER_DATA_CSV`` 永久换源
            - **密钥**：请在项目根目录配置 ``.env``（参考 ``.env.example``）  
            - **大模型**：默认使用 **DeepSeek**（OpenAI 兼容接口）  
            - **数据库**：SQLite 文件位于 ``storage/copilot.db``  
            """
        )
        st.divider()
        st.subheader("客户数据 CSV")
        st.caption("上传文件会替换默认数据，文件请尽量使用 **UTF-8** 编码。")
        uploaded = st.file_uploader("上传 CSV（可选）", type=["csv"], key="customer_csv_upload")
        st.divider()
        st.subheader("DeepSeek 配置（来自环境变量）")
        st.text(f"模型：{settings.deepseek_model}")
        st.text(f"Base URL：{settings.deepseek_base_url}")
        masked = (
            "(未配置)"
            if not settings.deepseek_api_key
            else settings.deepseek_api_key[:4] + "****" + settings.deepseek_api_key[-2:]
        )
        st.text(f"DEEPSEEK_API_KEY：{masked}")

    # -------------------------------------------------------------------------
    # 数据加载与风险标注（上传优先；否则使用 .env 的 CUSTOMER_DATA_CSV）
    # -------------------------------------------------------------------------
    data_source_label = ""

    if uploaded is not None:
        try:
            df_raw = load_customer_csv_bytes(uploaded.getvalue(), source_name=uploaded.name)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        data_source_label = f"上传文件：{uploaded.name}"
    else:
        csv_path = resolve_customer_csv_path(PROJECT_ROOT, settings.customer_data_csv)
        if not csv_path.is_file():
            st.error(f"未找到 CSV 文件：{csv_path}\n\n请检查 .env 中的 CUSTOMER_DATA_CSV，或上传 CSV。")
            st.stop()
        try:
            df_raw = load_customer_csv(csv_path)
        except Exception as exc:  # noqa: BLE001
            st.error(f"读取 CSV 失败：{exc}")
            st.stop()
        data_source_label = f"磁盘文件：{csv_path}"

    df = annotate_risk_levels(df_raw)
    st.session_state["_last_data_source"] = data_source_label

    tab_overview, tab_risk, tab_report, tab_history = st.tabs(
        ["数据总览", "风险客户", "AI 报告生成", "历史记录"]
    )

    with tab_overview:
        st.subheader("客户经营数据")
        st.caption(f"当前数据来源：{st.session_state.get('_last_data_source', '')}")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            label="下载当前表格为 CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="customer_export.csv",
            mime="text/csv",
        )

    with tab_risk:
        st.subheader("风险客户筛选")
        level = st.selectbox("按风险等级筛选", ["全部", "高", "中", "低"])
        filtered = df if level == "全部" else df[df["risk_level"] == level]
        st.metric("当前筛选客户数", len(filtered))
        st.dataframe(filtered, use_container_width=True, hide_index=True)

    with tab_report:
        st.subheader("调用 DeepSeek 生成经营分析报告（OpenAI 兼容 SDK）")
        focus = st.text_input(
            "分析侧重点（可修改）",
            value="识别高风险客户并给出分层经营策略与跟进节奏建议",
        )
        max_rows = st.slider("纳入提示词的客户行数（越大越耗 token）", 3, 10, 8)

        if st.button("生成报告", type="primary"):
            context = dataframe_to_brief_context(df, max_rows=max_rows)
            try:
                with st.spinner("正在调用 DeepSeek API，请稍候…"):
                    # 将 Pandas 汇总后的文本作为「客户分析数据」输入给大模型服务层
                    report_text = generate_business_report(
                        customer_analysis_data=context,
                        analysis_focus=focus,
                    )
            except LlmInvokeError as exc:
                # 业务层已翻译为人类可读提示
                st.error(f"生成失败：{exc.user_message}")
                if settings.debug and exc.original_error is not None:
                    st.exception(exc.original_error)
                st.info("请检查 .env 中的 DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL、网络与账户额度。")
            except Exception as exc:  # noqa: BLE001 — 兜底：避免页面直接崩溃
                st.error(f"生成失败（未预期错误）：{exc}")
                st.info("若问题持续，请将 DEBUG=true 后重试，并把日志提供给开发人员。")
            else:
                st.success("生成完成")
                st.session_state["_last_report_text"] = report_text
                st.markdown(report_text)

                # 将摘要写入 SQLite，便于审计（正文只存前 2000 字，避免库过大）
                store = get_sqlite_store()
                high_names = ",".join(df.loc[df["risk_level"] == "高", "customer_name"].astype(str).tolist())
                summary = f"已生成报告；高风险客户：{high_names[:200]}"
                store.insert_report(
                    customer_id=high_names or "N/A",
                    risk_level="高" if (df["risk_level"] == "高").any() else "中/低",
                    summary=summary,
                    report_excerpt=report_text[:2000],
                    model_name=settings.deepseek_model,
                )

                report_path = PROJECT_ROOT / "reports" / "latest_report.md"
                report_path.write_text(report_text, encoding="utf-8")
                st.caption(f"已同步保存 Markdown 草案：{report_path}")

        st.divider()

        # ------------------------------------------------------------------
        # 企业报告生成（图表 + Markdown + PPT）
        # ------------------------------------------------------------------
        st.subheader("企业报告生成")
        st.caption("自动生成数据图表、Markdown 报告与 PPT 演示文稿")

        if st.button("生成企业报告 & PPT", type="secondary"):
            try:
                with st.spinner("正在生成图表和分析报告..."):
                    # 1. 分类客户
                    h_risk = df[df["risk_level"] == "高"].to_dict("records")
                    h_value = df[
                        (df["monthly_gmv"] >= 200000) & (df["login_days"] >= 20)
                    ].to_dict("records")
                    growth = df[
                        (df["monthly_gmv"] >= 80000)
                        & (df["monthly_gmv"] < 200000)
                        & (df["login_days"] >= 15)
                    ].to_dict("records")
                    categories = {
                        "high_risk": h_risk,
                        "high_value": h_value,
                        "growth": growth,
                    }

                    # 2. 图表
                    cg = ChartGenerator(output_dir="visualizations")
                    charts = cg.generate_all(df)

                    # 3. AI 洞察（尝试取已生成的内容，否则用占位符）
                    insights = (
                        st.session_state.get("_last_report_text", "")
                        or "AI 洞察：请先在「生成报告」生成内容后再生成 PPT。"
                    )

                    # 4. Markdown
                    rg = ReportGenerator()
                    rg.generate(df, categories, insights, charts)

                    # 5. PPT
                    pg = PPTGenerator()
                    pg.generate(df, categories, insights, charts)

                st.success("企业报告生成完成")
                st.markdown(
                    "- **Markdown**: `reports/enterprise_report.md`\n"
                    "- **PPT**: `reports/enterprise_report.pptx`\n"
                    "- **图表**: `visualizations/*.png`"
                )

                # 读取文件内容供下载
                md_bytes = Path("reports/enterprise_report.md").read_bytes()
                ppt_bytes = Path("reports/enterprise_report.pptx").read_bytes()

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="下载 Markdown 报告",
                        data=md_bytes,
                        file_name="enterprise_report.md",
                        mime="text/markdown",
                        use_container_width=True,
                    )
                with col2:
                    st.download_button(
                        label="下载 PPT",
                        data=ppt_bytes,
                        file_name="enterprise_report.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True,
                    )

                # 展示图表预览
                st.subheader("图表预览")
                chart_cols = st.columns(4)
                for idx, (name, path) in enumerate(charts.items()):
                    with chart_cols[idx % 4]:
                        st.image(path, caption=name, use_container_width=True)

            except Exception as exc:
                st.error(f"企业报告生成失败：{exc}")

        # ------------------------------------------------------------------
        # AI Agent 多工具智能体
        # ------------------------------------------------------------------
        st.divider()
        st.subheader("AI Agent 多工具智能体")
        st.caption(
            "基于 LangChain **Tool Calling** 思想，Agent 自动编排 "
            "数据分析 → RAG 知识检索 → 图表 → Markdown 报告 → PPT 全流程"
        )

        if st.button("AI Agent 一键生成完整报告", type="primary"):
            try:
                with st.spinner("🤖 Agent 正在规划工具链并逐步执行..."):
                    from tools.agent import MultiToolAgent

                    agent = MultiToolAgent()
                    insights = st.session_state.get("_last_report_text", "")
                    result = agent.run(
                        task="生成企业经营分析报告",
                        df=df,
                        insights=insights,
                    )

                if result.success:
                    st.success("✅ AI Agent 执行完成")
                    st.code(result.summary, language="text")

                    # 读取文件供下载
                    md_path = Path("reports/enterprise_report.md")
                    ppt_path = Path("reports/enterprise_report.pptx")

                    col1, col2 = st.columns(2)
                    with col1:
                        if md_path.exists():
                            st.download_button(
                                label="下载 Markdown 报告",
                                data=md_path.read_bytes(),
                                file_name="enterprise_report.md",
                                mime="text/markdown",
                                use_container_width=True,
                                key="agent_md_download",
                            )
                    with col2:
                        if ppt_path.exists():
                            st.download_button(
                                label="下载 PPT",
                                data=ppt_path.read_bytes(),
                                file_name="enterprise_report.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True,
                                key="agent_ppt_download",
                            )

                    # 图表预览
                    ctx = result.context
                    if ctx and ctx.chart_paths:
                        st.subheader("Agent 生成的图表")
                        chart_cols = st.columns(4)
                        for idx, (name, path) in enumerate(ctx.chart_paths.items()):
                            with chart_cols[idx % 4]:
                                st.image(str(path), caption=name, use_container_width=True)

                else:
                    st.error(f"Agent 执行失败：{result.error}")
                    st.info("请检查数据是否正常，或查看执行日志了解详情。")

            except Exception as exc:
                st.error(f"Agent 执行异常：{exc}")
                st.info("若问题持续，请尝试先生成 DeepSeek 报告或使用「企业报告生成」按钮。")

    with tab_history:
        st.subheader("近期生成记录（SQLite）")
        store = get_sqlite_store()
        rows = store.list_recent_reports(limit=30)
        if not rows:
            st.info("暂无历史记录。请先在「AI 报告生成」页成功生成一次。")
        else:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

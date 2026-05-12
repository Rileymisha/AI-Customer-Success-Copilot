# -*- coding: utf-8 -*-
"""
RAG 知识库检索服务（Retrieval-Augmented Generation Service）
=============================================================

基于 LangChain + FAISS 构建本地知识库检索系统。

使用方式::

    from src.ai_cs_copilot.services.rag_service import RAGService

    rag = RAGService()
    context = rag.build_context("客户登录天数低，如何提升活跃度")
    print(context)  # 返回知识库中相关片段
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 可选依赖检查（避免未安装相关包时直接崩溃）
# ---------------------------------------------------------------------------
try:
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # HuggingFaceEmbeddings：优先使用 langchain-huggingface（新），兜底 langchain_community（旧）
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings

    RAG_IMPORT_OK = True
except ImportError:  # noqa: F841
    RAG_IMPORT_OK = False

logger = logging.getLogger(__name__)


# ===========================================================================
# 常量
# ===========================================================================

_DEFAULT_KB_DIR: str = "knowledge_base"
_DEFAULT_PERSIST_DIR: str = "storage/faiss_index"
_DEFAULT_EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_DEFAULT_CHUNK_SIZE: int = 600
_DEFAULT_CHUNK_OVERLAP: int = 120

# 不同客户问题与知识库的检索查询映射
ISSUE_QUERY_MAP: dict[str, str] = {
    "登录活跃度": "客户登录天数低 活跃度下降 如何提高登录频率",
    "客户投诉": "客户投诉处理 投诉太多 客户满意度提升方法",
    "续约逾期": "客户续约逾期 续费策略 客户挽回方案",
    "续约即将到期": "客户即将到期 续约跟进 提前续约策略",
    "功能使用率低": "产品功能使用率低 客户采用率提升 产品落地",
    "营销功能低": "营销功能使用率低 客户增长 交叉销售",
    "高价值客户": "高价值客户维护 大客户管理 客户成功策略",
    "GMV 下降": "客户 GMV 下降 经营改善 收入提升方案",
}


# ===========================================================================
# RAG 服务
# ===========================================================================


class RAGService:
    """
    知识库检索服务。

    基于 LangChain + FAISS 实现本地 RAG，支持：
    - 自动加载 knowledge_base 目录中的 Markdown 文档
    - 文档切块与向量化
    - 相似度检索
    - 索引持久化（避免每次重启重复构建）

    当 RAG 依赖未安装时，``query()`` 和 ``build_context()`` 会返回空结果，
    不会影响主流程运行。
    """

    def __init__(
        self,
        kb_dir: str | Path = _DEFAULT_KB_DIR,
        persist_dir: str | Path = _DEFAULT_PERSIST_DIR,
        embedding_model: str = _DEFAULT_EMBEDDING_MODEL,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = _DEFAULT_CHUNK_OVERLAP,
    ) -> None:
        """
        参数:
            kb_dir: 知识库文档目录路径
            persist_dir: FAISS 索引持久化目录
            embedding_model: SentenceTransformer 模型名称
            chunk_size: 文档切块大小（字符数）
            chunk_overlap: 切块重叠大小（字符数）
        """
        self.kb_dir = Path(kb_dir)
        self.persist_dir = Path(persist_dir)
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._vector_store: Any = None  # FAISS 实例

        if not RAG_IMPORT_OK:
            logger.warning(
                "RAG 依赖未安装。请执行：pip install langchain-community faiss-cpu sentence-transformers"
            )
            return

        self._initialize()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _get_embeddings(self) -> HuggingFaceEmbeddings:
        """
        创建 HuggingFace 本地嵌入模型。

        模型默认使用 paraphrase-multilingual-MiniLM-L12-v2，
        支持中文等多语言文本的向量化。
        """
        logger.info("正在加载嵌入模型：%s（首次加载会自动下载）", self.embedding_model)
        return HuggingFaceEmbeddings(model_name=self.embedding_model)

    def _initialize(self) -> None:
        """
        加载已有索引或构建新索引。

        流程：
        1. 检查 persist_dir 是否存在已有索引
        2. 存在则加载，不存在则调用 _build_index() 新建
        """
        if self.persist_dir.exists() and list(self.persist_dir.iterdir()):
            logger.info("正在加载本地 FAISS 索引：%s", self.persist_dir)
            self._vector_store = FAISS.load_local(
                str(self.persist_dir),
                self._get_embeddings(),
                allow_dangerous_deserialization=True,
            )
            logger.info("FAISS 索引加载成功")
        else:
            logger.info("未找到本地索引，开始构建...")
            self._build_index()

    def _build_index(self) -> None:
        """
        从知识库目录构建 FAISS 向量索引。

        完整流程：
        1. 加载所有 .md 文件
        2. 文档切块（RecursiveCharacterTextSplitter）
        3. 向量化（HuggingFaceEmbeddings）
        4. 存入 FAISS
        5. 保存索引到磁盘
        """
        # ---- 第 1 步：加载文档 ----
        if not self.kb_dir.exists():
            logger.warning("知识库目录不存在：%s", self.kb_dir)
            return

        loader = DirectoryLoader(
            str(self.kb_dir),
            glob="**/*.md",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        docs = loader.load()
        if not docs:
            logger.warning("知识库目录中没有找到 .md 文档：%s", self.kb_dir)
            return
        logger.info("加载了 %d 篇知识文档", len(docs))

        # ---- 第 2 步：文档切块 ----
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", "。", " ", ""],
        )
        chunks = splitter.split_documents(docs)
        logger.info("切块完成：共 %d 个文本块", len(chunks))

        # ---- 第 3 步：构建向量索引 ----
        logger.info("正在生成 Embedding 并构建 FAISS 索引（首次运行会下载模型，可能需要 1-2 分钟）...")
        self._vector_store = FAISS.from_documents(chunks, self._get_embeddings())

        # ---- 第 4 步：持久化 ----
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._vector_store.save_local(str(self.persist_dir))
        logger.info("FAISS 索引已保存到：%s", self.persist_dir)

    def rebuild_index(self) -> None:
        """
        强制重建索引（当知识库文档更新时调用）。
        """
        logger.info("强制重建 FAISS 索引...")
        self._vector_store = None
        self._build_index()

    # ------------------------------------------------------------------
    # 检索接口
    # ------------------------------------------------------------------

    def query(self, query_text: str, k: int = 2) -> list[Any]:
        """
        查询最相关的知识片段。

        参数:
            query_text: 检索查询文本
            k: 返回的最相似文档数量（默认 2）

        返回:
            LangChain Document 对象列表，每个包含 page_content 和 metadata

        异常:
            RuntimeError: FAISS 索引未初始化时抛出
        """
        if not RAG_IMPORT_OK:
            logger.warning("RAG 依赖未安装，无法检索")
            return []

        if self._vector_store is None:
            logger.warning("FAISS 索引未初始化，请检查知识库目录")
            return []

        results = self._vector_store.similarity_search(query_text, k=k)
        logger.debug("查询「%s」→ 命中 %d 条结果", query_text, len(results))
        return results

    def build_context(
        self,
        query_text: str,
        k: int = 2,
        sep: str = "\n\n---\n\n",
    ) -> str:
        """
        查询知识库并拼接为可直接注入 Prompt 的上下文文本。

        参数:
            query_text: 检索查询
            k: 返回片段数
            sep: 片段间的分隔符

        返回:
            拼接后的文本，若无命中则返回空字符串
        """
        docs = self.query(query_text, k=k)
        if not docs:
            return ""

        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "未知来源")
            context_parts.append(
                f"[参考 {i}]（来源：{Path(source).name}）\n{doc.page_content}"
            )

        return sep.join(context_parts)

    def diagnose_and_retrieve(self, df: Any) -> str:
        """
        根据客户数据的整体特征自动诊断问题并检索相关知识。

        传入 DataFrame，自动检测：
        - 是否存在低登录客户 → 检索 low_login_solutions
        - 是否存在高投诉客户 → 检索 customer_retention
        - 是否存在逾期客户 → 检索 renewal_strategy
        - 是否存在低营销使用率客户 → 检索 marketing_growth

        参数:
            df: 客户数据 DataFrame（需包含 login_days, complaint_count 等字段）

        返回:
            汇总的 RAG 上下文文本
        """
        import pandas as pd

        if df is None or df.empty:
            return ""

        queries: list[str] = []

        # 登录天数低
        if "login_days" in df.columns:
            low_login = df[pd.to_numeric(df["login_days"], errors="coerce") < 10]
            if len(low_login) > 0:
                queries.append(ISSUE_QUERY_MAP["登录活跃度"])

        # 投诉多
        if "complaint_count" in df.columns:
            high_complaint = df[pd.to_numeric(df["complaint_count"], errors="coerce") > 3]
            if len(high_complaint) > 0:
                queries.append(ISSUE_QUERY_MAP["客户投诉"])

        # 续约逾期或即将到期
        if "renewal_days_left" in df.columns:
            overdue = df[pd.to_numeric(df["renewal_days_left"], errors="coerce") < 0]
            if len(overdue) > 0:
                queries.append(ISSUE_QUERY_MAP["续约逾期"])
            else:
                expiring = df[
                    (pd.to_numeric(df["renewal_days_left"], errors="coerce") >= 0)
                    & (pd.to_numeric(df["renewal_days_left"], errors="coerce") < 30)
                ]
                if len(expiring) > 0:
                    queries.append(ISSUE_QUERY_MAP["续约即将到期"])

        # 营销功能使用率低
        if "marketing_usage_rate" in df.columns:
            low_mkt = df[pd.to_numeric(df["marketing_usage_rate"], errors="coerce") < 30]
            if len(low_mkt) > 0:
                queries.append(ISSUE_QUERY_MAP["营销功能低"])

        # 去重并检索
        seen: set[str] = set()
        context_parts: list[str] = []
        for q in queries:
            if q in seen:
                continue
            seen.add(q)
            ctx = self.build_context(q, k=1)
            if ctx:
                context_parts.append(f"### {q}\n{ctx}")

        if not context_parts:
            return ""

        return (
            "## 知识库参考内容\n"
            "以下内容来自企业内部知识库，请优先参考这些知识来制定客户策略：\n\n"
            + "\n\n".join(context_parts)
        )

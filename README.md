<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/DeepSeek-API-4A6CF7?style=for-the-badge&logo=deepseek&logoColor=white" alt="DeepSeek">
  <img src="https://img.shields.io/badge/LangChain-0.2%2B-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/FAISS-RAG-00A86B?style=for-the-badge&logo=facebook&logoColor=white" alt="FAISS">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License">
</p>

<h1 align="center">
  🤖 AI Customer Success Copilot
</h1>

<p align="center">
  <b>Enterprise-Grade AI-Powered Customer Success Intelligence Platform</b><br>
  <i>Agentic Workflow · RAG Knowledge Base · Multi-Tool Orchestration · Automated Reporting</i>
</p>

<p align="center">
  <a href="#-system-architecture">System Architecture</a> •
  <a href="#-ai-agent-workflow">AI Agent Workflow</a> •
  <a href="#-rag-knowledge-base">RAG Knowledge Base</a> •
  <a href="#-multi-tool-agent-architecture">Multi-Tool Agent</a> •
  <a href="#-quick-start">Quick Start</a>
</p>

---

## 📋 Table of Contents

- [1. Project Overview](#-project-overview)
- [2. Project Background](#-project-background)
- [3. Business Pain Points](#-business-pain-points)
- [4. Core Features](#-core-features)
- [5. AI Agent Workflow](#-ai-agent-workflow)
- [6. RAG Knowledge Base Architecture](#-rag-knowledge-base-architecture)
- [7. Multi-Tool Agent Architecture](#-multi-tool-agent-architecture)
- [8. Technology Stack](#-technology-stack)
- [9. Project Directory Structure](#-project-directory-structure)
- [10. Installation Guide](#-installation-guide)
- [11. Environment Configuration](#-environment-configuration)
- [12. Streamlit Quick Start](#-streamlit-quick-start)
- [13. Demo Screenshots](#-demo-screenshots)
- [14. System Architecture Diagram](#-system-architecture-diagram)
- [15. Workflow Flowchart](#-workflow-flowchart)
- [16. Project Highlights](#-project-highlights)
- [17. Enterprise Use Cases](#-enterprise-use-cases)
- [18. Future Roadmap](#-future-roadmap)
- [19. Author & License](#-author--license)

---

<br>

## 🚀 1. Project Overview

**AI Customer Success Copilot** is an enterprise-level, AI-driven customer success intelligence platform built for B2B SaaS Customer Success Managers (CSMs). It automatically ingests customer operational data, performs multi-dimensional risk scoring, retrieves relevant knowledge from a local RAG knowledge base, invokes LLMs for deep business insights, and generates structured enterprise reports — all orchestrated by an intelligent **Multi-Tool AI Agent**.

> **Core Philosophy**: Replace manual, spreadsheet-based customer health reviews with an intelligent, automated, and extensible Agentic pipeline.

```python
# One line to run the entire enterprise reporting pipeline
from tools.agent import MultiToolAgent

agent = MultiToolAgent()
result = agent.run(task="生成企业经营分析报告", df=customer_data)
# → Markdown Report + PPT + Charts + RAG Context
```

### ✨ What Makes This Project Different?

| Dimension | Traditional Approach | AI Copilot Approach |
|-----------|-------------------|-------------------|
| Risk Assessment | Manual spreadsheet review | Rule engine + AI dual-track scoring |
| Knowledge Access | Scattered documents, tribal knowledge | Centralized RAG vector knowledge base |
| Report Generation | Hours of manual writing | 30-second automated generation |
| Tool Orchestration | Hard-coded scripts | Dynamic Multi-Tool Agent (Tool Calling) |
| Error Handling | Single point of failure | Pipeline with critical/non-critical step isolation |

---

<br>

## 🏢 2. Project Background

In B2B SaaS enterprises, Customer Success Managers (CSMs) are responsible for hundreds of customer accounts simultaneously. The core challenge is **identifying at-risk customers before they churn** and **proactively engaging them with data-driven strategies**.

### The Problem Space

```
┌─────────────────────────────────────────────────────────────────┐
│                    CSM's Weekly Reality                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊  Raw Data Sprawl: 分散在 CRM、产品数据库、Excel 中的客户数据     │
│  📋  Manual Reporting: CSM 每周花 4-6 小时手工做报告                │
│  🧠  Knowledge Silos: 高绩效 CSM 的经验分散在 Slack/wiki 中        │
│  🔄  Inconsistent Follow-up: 风险响应依赖个人经验，缺乏标准化流程    │
│  📉  Reactive Not Proactive: 发现风险时往往已经太晚                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The traditional CSM workflow is **reactive, manual, and non-scalable**. When a CSM manages 50+ accounts, it's impossible to give each account the deep, data-driven attention it deserves. This project was built to **augment CSM capabilities with AI**, enabling them to focus on high-value strategic interventions rather than data gathering and report writing.

---

<br>

## 🎯 3. Enterprise Business Pain Points

This project directly addresses 6 critical pain points in enterprise customer success operations:

<br>

### 🥇 Pain Point 1: Customer Churn Detection is Too Late

Most CS teams discover churn risk during quarterly business reviews — by then, the customer has already mentally checked out.

**Solution**: Real-time risk scoring engine with 10+ behavioral indicators (login frequency, feature adoption, renewal proximity, complaint velocity) that flags at-risk customers weeks before they churn.

<br>

### 🥇 Pain Point 2: Knowledge is Trapped in Silos

High-performing CSMs develop deep expertise in handling specific scenarios (renewal negotiations, feature adoption coaching, complaint resolution), but this knowledge never gets institutionalized.

**Solution**: RAG-powered knowledge base that stores and retrieves best practices, enabling every CSM to perform at the level of the top performer.

<br>

### 🥇 Pain Point 3: Report Creation is a Time Sink

CSMs spend 20-30% of their week manually creating reports for internal reviews and client QBRs (Quarterly Business Reviews).

**Solution**: Automated report generation pipeline that produces structured Markdown reports and professional PPT presentations with embedded charts in under 30 seconds.

<br>

### 🥇 Pain Point 4: Inconsistent Risk Assessment

Without standardized risk criteria, different CSMs assess the same customer differently, leading to inconsistent prioritization.

**Solution**: Rule-based, deterministic risk scoring engine with transparent, auditable scoring criteria (vs. opaque ML black boxes).

<br>

### 🥇 Pain Point 5: Disconnected Toolchain

CSMs jump between CRM, analytics tools, Excel, and PowerPoint to produce a single customer health report.

**Solution**: Multi-Tool Agent architecture that seamlessly orchestrates data analysis, knowledge retrieval, charting, and report generation in a single pipeline.

<br>

### 🥇 Pain Point 6: Lack of AI Governance

Many AI solutions are black boxes — you can't explain why a customer was flagged as high risk.

**Solution**: Dual-track architecture where rule engine provides **deterministic, auditable** scoring, and AI adds **creative, contextual** insights. Two systems cross-validate each other.

---

<br>

## ⚡ 4. Core Features

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Feature Overview                                  │
│                                                                      │
│   📊 Data Overview      ──  Interactive customer data table          │
│   🚨 Risk Assessment    ──  Dual-track risk scoring (Rules + AI)     │
│   🧠 RAG Knowledge Base ──  FAISS-powered enterprise knowledge       │
│   🤖 AI Analysis Agent  ──  DeepSeek-powered deep customer analysis  │
│   📈 Chart Generation   ──  Auto-generated matplotlib charts (4)     │
│   📝 Markdown Report    ──  Structured enterprise report (8 sections)│
│   📽️ PPT Generation     ──  Professional 9-slide PPT deck            │
│   🧩 Multi-Tool Agent   ──  LangChain Tool Calling orchestration     │
│   🔄 Workflow Pipeline  ──  8-step automated pipeline                │
│   📜 History Tracking   ──  SQLite-backed report archive              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Feature Breakdown

| Feature | Description | Technology |
|---------|-------------|-----------|
| **📊 Data Overview** | Interactive table with all customer metrics, CSV upload & download | Streamlit + Pandas |
| **🚨 Risk Scoring Engine** | 4-dimensional risk scoring (login, adoption, renewal, complaints) | Custom rule engine |
| **🧠 RAG Knowledge Base** | Auto-diagnose customer issues → retrieve relevant strategies | LangChain + FAISS |
| **🤖 AI Risk Agent** | Two-stage analysis: rule pre-score + DeepSeek deep analysis | DeepSeek API |
| **📈 Auto Charts** | GMV ranking, risk distribution pie, industry bar, region bar | matplotlib |
| **📝 Enterprise Report** | Executive summary, risk analysis, customer list, AI insights, action plan | ReportGenerator |
| **📽️ PPT Deck** | 9-slide professional presentation with embedded charts | python-pptx |
| **🧩 Multi-Tool Agent** | 5 independent tools orchestrated via LangChain Tool Calling | Custom Agent |
| **🔧 Workflow Pipeline** | 8-step Pipeline with critical/non-critical step isolation | Custom Pipeline |
| **📜 History** | All reports archived in SQLite with timeline view | SQLite + Pandas |

---

<br>

## 🤖 5. AI Agent Workflow

### Multi-Tool Agent Execution Flow

The system's intelligence is powered by a **Multi-Tool AI Agent** that automatically plans and executes a sequence of tool calls based on the task description.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    User Clicks "Generate Report"                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     MultiToolAgent (Orchestrator)                     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    Task Planning (_plan)                        │   │
│  │  "生成企业经营分析报告" → Analyze task → Generate tool sequence │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                  │                                     │
│                                  ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    Tool Execution Pipeline                       │   │
│  │                                                                  │   │
│  │  Step 1  [Critical]  data_analysis    ──  Risk scoring + classify│   │
│  │       │                                                          │   │
│  │       ▼                                                          │   │
│  │  Step 2  [Optional]  rag_query        ──  Knowledge base search  │   │
│  │       │                                                          │   │
│  │       ▼                                                          │   │
│  │  Step 3  [Optional]  chart_generation  ──  matplotlib charts (4) │   │
│  │       │                                                          │   │
│  │       ▼                                                          │   │
│  │  Step 4  [Optional]  report_generation  ──  Markdown report      │   │
│  │       │                                                          │   │
│  │       ▼                                                          │   │
│  │  Step 5  [Optional]  ppt_generation    ──  PPT deck (9 slides)   │   │
│  │                                                                  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                  │                                     │
│                                  ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    Result Aggregation                            │   │
│  │  ✓ Execution log with per-step status                           │   │
│  │  ✓ Summary report for user                                      │   │
│  │  ✓ All artifacts: MD + PPT + Charts                             │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### Error Handling Strategy

```
┌───────────────────────────────────────────────────────┐
│              Pipeline Error Isolation                   │
│                                                         │
│  data_analysis     [CRITICAL]  ──  Fail → STOP         │
│  rag_query         [NON-CRIT]  ──  Fail → SKIP → CONTINUE│
│  chart_generation  [NON-CRIT]  ──  Fail → SKIP → CONTINUE│
│  report_generation [NON-CRIT]  ──  Fail → SKIP → CONTINUE│
│  ppt_generation    [NON-CRIT]  ──  Fail → SKIP → CONTINUE│
│                                                         │
│  Business Impact:                                        │
│  - RAG dependency missing? → Skip, report still generated│
│  - Chart library error? → Skip, MD report still works   │
│  - PPT generation failed? → Markdown report still ready │
└───────────────────────────────────────────────────────┘
```

### LangChain Tool Calling Correspondence

| LangChain Concept | This Project's Implementation |
|------------------|------------------------------|
| `Tool.name` | `BaseTool.name` (`"data_analysis"`, `"rag_query"`, etc.) |
| `Tool.description` | `BaseTool.description` (human-readable task description) |
| `Tool.args_schema` | `ToolSpec.parameters` (JSON Schema-style parameter list) |
| `Tool._run()` | `BaseTool.run(**kwargs)` (execution logic) |
| `AgentExecutor.run()` | `MultiToolAgent.run(task, df)` (main entry point) |
| `intermediate_steps` | `AgentContext.execution_log` (per-step log) |
| `AgentFinish` | `AgentResult` (final output with summary) |

---

<br>

## 📚 6. RAG Knowledge Base Architecture

The system implements a **local Retrieval-Augmented Generation (RAG)** system using LangChain + FAISS, enabling the AI agent to ground its analysis in enterprise-specific knowledge.

### Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                         RAG Pipeline                                │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Knowledge    │    │  Text Split  │    │  Vectorize   │          │
│  │  Documents    │───→│  Recursive   │───→│  HuggingFace │          │
│  │  (*.md)       │    │  Chunk(600)  │    │  Embeddings  │          │
│  └──────────────┘    └──────────────┘    └──────┬───────┘          │
│                                                  │                   │
│                                                  ▼                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Retrieve    │    │  Query       │    │  FAISS       │          │
│  │  Similarity  │←───│  Diagnose    │←───│  Vector      │          │
│  │  Search (k=2)│    │  Customer    │    │  Index       │          │
│  └──────┬───────┘    └──────────────┘    └──────────────┘          │
│         │                                                           │
│         ▼                                                           │
│  ┌────────────────────────────────────────────────────────┐        │
│  │              Context Assembly (build_context)           │        │
│  │  "## 知识库参考内容\n[参考 1]（来源：renewal_strategy.md）\n..."  │
│  └────────────────────────────────────────────────────────┘        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Knowledge Base Documents

| Document | Topic | Query Trigger |
|----------|-------|--------------|
| `low_login_solutions.md` | 低登录活跃度解决方案 | `login_days < 10` |
| `customer_retention.md` | 客户投诉处理与留存 | `complaint_count > 3` |
| `renewal_strategy.md` | 续约策略与客户挽回 | `renewal_days_left < 0` |
| `marketing_growth.md` | 营销功能采用与增长 | `marketing_usage_rate < 30%` |

### Technical Details

| Component | Technology | Configuration |
|-----------|-----------|---------------|
| Document Loader | LangChain `DirectoryLoader` + `TextLoader` | Glob: `**/*.md` |
| Text Splitter | `RecursiveCharacterTextSplitter` | Chunk: 600 / Overlap: 120 |
| Embedding Model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384-dim, multilingual |
| Vector Store | FAISS (CPU) | Persisted to `storage/faiss_index/` |
| Similarity Search | FAISS `similarity_search(k=2)` | Top 2 chunks per query |
| Fallback | Graceful degradation if deps missing | Warning log + empty result |

---

<br>

## 🧩 7. Multi-Tool Agent Architecture

The **Multi-Tool Agent** is the brain of the system. Unlike traditional hard-coded pipelines, it follows the **LangChain Tool Calling** paradigm: each tool is independently registered with its name, description, and parameters; the agent analyzes the task and orchestrates tool execution.

### Tool Registration Pattern

```python
# Each tool self-registers with metadata
class DataAnalysisTool(BaseTool):
    @property
    def name(self) -> str:
        return "data_analysis"

    @property
    def description(self) -> str:
        return "客户经营数据分析工具：对客户数据执行风险评分..."

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            parameters=[ToolParameter(name="df", type="object", ...)],
        )

# Agent registers and orchestrates
agent = MultiToolAgent()
agent.register_tool(DataAnalysisTool())
agent.register_tool(RAGQueryTool())
agent.register_tool(ChartTool())
agent.register_tool(ReportTool())
agent.register_tool(PPTTool())
```

### Context Data Bus (AgentContext)

Tools never call each other directly. They communicate through a shared context object:

```
AgentContext (Shared Data Bus)
│
├── df: DataFrame              # Raw customer data
├── df_annotated: DataFrame    # After risk scoring (added risk_level column)
├── categories: Dict           # classified: {high_risk, high_value, growth}
├── rag_context: str           # RAG knowledge base results
├── chart_paths: Dict          # {gmv_bar, risk_pie, industry_bar, region_bar}
├── markdown_path: str         # Path to generated .md report
├── ppt_path: str              # Path to generated .pptx file
└── execution_log: List        # Per-step execution trace
```

### Design Philosophy

```
┌────────────────────────────────────────────────────────────────┐
│            "Rule Engine + AI" Dual-Track Philosophy             │
│                                                                │
│   ┌─────────────────────┐    ┌─────────────────────┐           │
│   │   Rule Engine       │    │   AI (LLM)          │           │
│   │   (Deterministic)   │    │   (Creative)        │           │
│   ├─────────────────────┤    ├─────────────────────┤           │
│   │ ✓ Risk Scoring      │    │ ✓ Business Insights  │           │
│   │ ✓ Customer Classify  │    │ ✓ Strategy Suggestions│          │
│   │ ✓ Chart Generation   │    │ ✓ Action Plans      │           │
│   │ ✓ Report Formatting  │    │ ✓ Open-ended Analysis│          │
│   │                      │    │                      │          │
│   │ Fast (ms) │ Cheap    │    │ Creative │ Flexible  │          │
│   │ 0 Hallucination      │    │ May Hallucinate      │          │
│   └─────────────────────┘    └─────────────────────┘           │
│                         │                                      │
│                         ▼                                      │
│              ┌─────────────────────┐                           │
│              │   Best of Both      │                           │
│              │   Rules for safety  │                           │
│              │   AI for creativity │                           │
│              └─────────────────────┘                           │
└────────────────────────────────────────────────────────────────┘
```

### 5 Registered Tools

| Tool | Name | Dependencies | Is Critical | Output |
|------|------|-------------|-------------|--------|
| 🏷️ Data Analysis | `data_analysis` | None | ✅ Yes | `df_annotated`, `categories` |
| 🔍 RAG Query | `rag_query` | langchain, FAISS | ❌ No | `rag_context` string |
| 📈 Chart Generation | `chart_generation` | matplotlib | ❌ No | `chart_paths` dict (4 PNGs) |
| 📝 Markdown Report | `report_generation` | None | ❌ No | `markdown_path` string |
| 📽️ PPT Generation | `ppt_generation` | python-pptx | ❌ No | `ppt_path` string |

---

<br>

## 🛠️ 8. Technology Stack

```
┌────────────────────────────────────────────────────────────────┐
│                    Technology Stack                             │
│                                                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│   │  Frontend    │  │  Backend    │  │  AI/ML      │           │
│   │─────────────│  │─────────────│  │─────────────│           │
│   │ Streamlit   │  │ Python 3.10 │  │ DeepSeek    │           │
│   │ Pandas      │  │ LangChain   │  │ OpenAI SDK  │           │
│   │ matplotlib  │  │ FAISS (CPU) │  │ sentence-   │           │
│   │             │  │ SQLite      │  │ transformers│           │
│   │             │  │ python-pptx │  │             │           │
│   └─────────────┘  └─────────────┘  └─────────────┘           │
│                                                                │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Architecture Patterns                                   │  │
│   │──────────────────────────────────────────────────────────│  │
│   │  ✔ Tool Calling (LangChain-style)                       │  │
│   │  ✔ Pipeline / Workflow Pattern                          │  │
│   │  ✔ RAG (Retrieval-Augmented Generation)                 │  │
│   │  ✔ Agentic Orchestration                                │  │
│   │  ✔ Dual-Track (Rule + AI)                               │  │
│   │  ✔ Repository Pattern (SQLite)                          │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Detailed Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **UI Framework** | Streamlit | ≥ 1.28 | Interactive web dashboard |
| **Data Processing** | Pandas | ≥ 2.0 | CSV loading, transformation, analysis |
| **Risk Engine** | Custom Rule Engine | — | Deterministic risk scoring (no ML black box) |
| **LLM Provider** | DeepSeek (via OpenAI SDK) | — | AI insights, strategy generation |
| **LLM SDK** | OpenAI Python | ≥ 1.40 | OpenAI-compatible API client |
| **RAG Framework** | LangChain | ≥ 0.2 | Document loading, splitting, retrieval |
| **Vector Store** | FAISS (CPU) | ≥ 1.7 | Local vector similarity search |
| **Embeddings** | sentence-transformers | ≥ 2.2 | Multilingual text vectorization |
| **Charting** | matplotlib | ≥ 3.7 | 4 types of analysis charts (150dpi PNG) |
| **PPT Generation** | python-pptx | ≥ 0.6 | 9-slide professional deck |
| **Database** | SQLite | — | Report history persistence |
| **Config** | pydantic-settings | ≥ 2.0 | Type-safe environment config |
| **Tool Agent** | Custom MultiToolAgent | — | LangChain Tool Calling orchestration |
| **Workflow** | Custom Pipeline | — | 8-step sequential pipeline |

---

<br>

## 📁 9. Project Directory Structure

```
AI-Customer-Success-Copilot/
│
├── 🚀 app.py                          # Streamlit application entry point
├── 🧪 pyproject.toml                  # Project metadata & build config
├── 📦 requirements.txt                # Python dependencies
├── ⚙️ .env.example                    # Environment variable template
├── 📄 .gitignore
│
├── 📊 data/                           # Customer data layer
│   ├── sample_customer_data.csv       # Sample dataset (35 customers, 10 columns)
│   └── customer_behavior_rules.md     # Risk classification rule documentation
│
├── 🧠 src/ai_cs_copilot/             # Core business logic package
│   ├── __init__.py
│   ├── config.py                      # pydantic-settings configuration
│   ├── db/                            # SQLite data access layer
│   │   ├── __init__.py
│   │   └── sqlite_store.py           # Report persistence
│   ├── pipelines/                     # Data processing pipelines
│   │   ├── __init__.py
│   │   ├── customer_analytics.py     # Risk scoring engine + data loading
│   │   └── data_paths.py            # CSV path resolution
│   ├── services/                      # Service layer
│   │   ├── __init__.py
│   │   ├── llm_service.py           # DeepSeek LLM wrapper
│   │   └── rag_service.py           # LangChain + FAISS RAG service
│   └── llm/                          # Backward-compat LLM exports
│       └── __init__.py
│
├── 🤖 agents/                         # AI Agent layer
│   ├── __init__.py
│   └── customer_risk_agent.py        # DeepSeek-powered risk analysis agent
│
├── 🧩 tools/                          # Multi-Tool Agent system
│   ├── __init__.py
│   ├── base_tool.py                   # Abstract BaseTool class
│   ├── data_analysis_tool.py         # Risk scoring & customer classification
│   ├── rag_query_tool.py             # RAG knowledge base query
│   ├── chart_tool.py                 # matplotlib chart generation
│   ├── report_tool.py                # Markdown report generation
│   ├── ppt_tool.py                   # PPT generation
│   └── agent.py                      # MultiToolAgent orchestrator
│
├── 🔄 workflows/                      # Workflow orchestration
│   ├── __init__.py
│   └── report_workflow.py            # 8-step Pipeline workflow
│
├── 📚 knowledge_base/                 # RAG knowledge base documents
│   ├── low_login_solutions.md        # Low login activity solutions
│   ├── customer_retention.md         # Customer retention strategies
│   ├── renewal_strategy.md           # Renewal & churn prevention
│   └── marketing_growth.md          # Marketing adoption growth
│
├── 📋 services/                       # Report/PPT generation services
│   ├── __init__.py
│   ├── report_generator.py           # Markdown enterprise report generator
│   └── ppt_generator.py             # python-pptx PPT generator
│
├── 📊 visualizations/                 # Chart output directory
│   ├── chart_generator.py            # matplotlib chart engine
│   ├── gmv_bar.png                   # GMV ranking bar chart
│   ├── risk_pie.png                  # Risk distribution pie chart
│   ├── industry_bar.png              # Industry distribution
│   └── region_bar.png                # Regional distribution
│
├── 📁 reports/                        # Generated report outputs
│   ├── enterprise_report.md          # Latest enterprise report (Markdown)
│   ├── enterprise_report.pptx        # Latest enterprise report (PPT)
│   ├── latest_report.md              # Latest LLM-generated report
│   └── risk_analysis_report.md       # AI risk analysis report
│
├── 🎨 templates/                      # Report templates
│   └── report_template.md            # Markdown report template reference
│
├── 🗃️ storage/                        # Data persistence
│   ├── copilot.db                    # SQLite database (report history)
│   └── faiss_index/                  # FAISS vector store index
│
├── 📜 scripts/                        # Utility scripts
│   └── init_db.py                   # Database initialization script
│
├── 🧪 tests/                          # Unit tests
│
├── 📚 docs/                           # Architecture documentation
│   ├── SYSTEM_ARCHITECTURE.md        # System architecture document
│   ├── RAG_ARCHITECTURE.md           # RAG architecture document
│   └── MULTI_AGENT_ARCHITECTURE.md   # Multi-Tool Agent architecture
│
└── 🔧 .claude/                        # Claude Code config
    └── settings.local.json
```

---

<br>

## 🔧 10. Installation Guide

### Prerequisites

- Python 3.10+
- pip (Python package manager)
- Git
- DeepSeek API key (or any OpenAI-compatible API key)

### Step-by-Step Installation

```bash
# Step 1: Clone the repository
git clone https://github.com/Rileymisha/AI-Customer-Success-Copilot.git
cd AI-Customer-Success-Copilot

# Step 2: Create and activate virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.\.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate

# Step 3: Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Step 4: Configure environment variables
cp .env.example .env
# Edit .env with your API key (see Environment Configuration section)

# Step 5: Initialize the SQLite database
python scripts/init_db.py

# Step 6: (Optional) Pre-build the FAISS index
python -c "from src.ai_cs_copilot.services.rag_service import RAGService; RAGService()"

# Step 7: Launch the application
streamlit run app.py
```

### Docker (Coming Soon)

```dockerfile
# Future: Docker support
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
```

---

<br>

## ⚙️ 11. Environment Configuration

Create a `.env` file in the project root directory by copying `.env.example`:

```ini
# ═══════════════════════════════════════════════
#  AI Customer Success Copilot - Configuration
# ═══════════════════════════════════════════════

# ── DeepSeek API Configuration ─────────────────
# Get your API key from: https://platform.deepseek.com
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# ── Alternative: OpenAI-Compatible Endpoint ────
# If using a different provider, configure these:
# OPENAI_API_KEY=sk-your-openai-api-key
# OPENAI_API_BASE=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini

# ── Customer Data ──────────────────────────────
# Path to customer CSV (relative to project root or absolute path)
CUSTOMER_DATA_CSV=data/sample_customer_data.csv

# ── Debug Mode ────────────────────────────────
# Set to true for verbose logging (don't use in production)
DEBUG=false
```

### Configuration Parameters

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | ✅ Yes | — | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | ❌ No | `https://api.deepseek.com` | API endpoint base URL |
| `DEEPSEEK_MODEL` | ❌ No | `deepseek-chat` | Model name |
| `CUSTOMER_DATA_CSV` | ❌ No | `data/sample_customer_data.csv` | Custom CSV data file path |
| `DEBUG` | ❌ No | `false` | Debug logging toggle |

---

<br>

## 🚀 12. Streamlit Quick Start

```bash
# Launch the Streamlit app
streamlit run app.py

# Or specify a custom port
streamlit run app.py --server.port=8501

# Or run in headless mode (no browser auto-open)
streamlit run app.py --server.headless=true
```

### Web Interface Overview

Once launched, open `http://localhost:8501` in your browser:

```
┌──────────────────────────────────────────────────────────────────┐
│  AI-Customer-Success-Copilot — AI 客户成功助手                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐  ┌──────────────────────────────────────────────┐  │
│  │ Sidebar   │  │  Tab 1: 📊 Data Overview                     │  │
│  │           │  │  ┌──────────────────────────────────────┐   │  │
│  │ Project   │  │  │ Customer data table with all metrics  │   │  │
│  │ Info      │  │  │ + Download CSV button                  │   │  │
│  │           │  │  └──────────────────────────────────────┘   │  │
│  │ CSV       │  │                                              │  │
│  │ Upload    │  │  Tab 2: 🚨 Risk Filtering                   │  │
│  │           │  │  ┌──────────────────────────────────────┐   │  │
│  │ DeepSeek  │  │  │ Filter by risk level: High/Med/Low   │   │  │
│  │ Config    │  │  └──────────────────────────────────────┘   │  │
│  └──────────┘  │                                              │  │
│                │  Tab 3: 🤖 AI Report Generation              │  │
│                │  ┌──────────────────────────────────────┐   │  │
│                │  │ 1. DeepSeek Report (LLM-generated)    │   │  │
│                │  │ 2. Enterprise Report & PPT            │   │  │
│                │  │ 3. AI Agent One-Click Generation      │   │  │
│                │  └──────────────────────────────────────┘   │  │
│                │                                              │  │
│                │  Tab 4: 📜 History (SQLite)                 │  │
│                │  ┌──────────────────────────────────────┐   │  │
│                │  │ Recent 30 report records              │   │  │
│                │  └──────────────────────────────────────┘   │  │
│                └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### How to Use

1. **Data Source**: Either upload your own CSV via sidebar or use the default sample data
2. **Risk Filtering**: Navigate to "风险客户" tab to filter by risk level
3. **Generate AI Report**: In "AI 报告生成" tab, click "生成报告" for DeepSeek insights
4. **Enterprise Report**: Click "生成企业报告 & PPT" for charts + Markdown + PPT
5. **AI Agent**: Click "AI Agent 一键生成完整报告" for fully automated orchestration
6. **Download**: Use download buttons to save Markdown report or PPT deck
7. **History**: Check "历史记录" tab for all previously generated reports

---

<br>

## 🖼️ 13. Demo Screenshots

> *Screenshots will be added after deployment. Below are placeholders for the GitHub README.*

```
┌─────────────────────────────────────────────────────────────────┐
│  📸 Screenshot 1: Data Overview Tab                              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  Customer Name │ Industry │ GMV │ Login │ Risk Level    │     │
│  │──────────────────────────────────────────────────────────│     │
│  │  GreenField    │ Retail   │ 450K │ 25    │ 🟢 低         │     │
│  │  BlueOcean     │ Tech     │ 120K │  3    │ 🔴 高         │     │
│  │  ...           │ ...      │ ...  │ ...   │ ...           │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  📸 Screenshot 2: AI Report Output                              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │  # 企业经营分析报告                                        │     │
│  │                                                          │     │
│  │  ## 一、执行摘要                                          │     │
│  │  本次共分析 35 个客户，覆盖 6 个行业...                    │     │
│  │                                                          │     │
│  │  ## 二、客户风险分布                                      │     │
│  │  [Risk Pie Chart Image]                                  │     │
│  │                                                          │     │
│  │  ## 三、高风险客户清单                                    │     │
│  │  | 客户 | GMV | 投诉 | 建议动作 |                        │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  📸 Screenshot 3: Enterprise Report Downloads                   │
│                                                                   │
│  ┌────────────────────────┐  ┌────────────────────────┐          │
│  │  📥 Download Markdown   │  │  📥 Download PPT       │          │
│  │  enterprise_report.md   │  │  enterprise_report.pptx│          │
│  └────────────────────────┘  └────────────────────────┘          │
│                                                                   │
│  [Chart Preview: GMV Bar] [Risk Pie] [Industry] [Region]         │
└─────────────────────────────────────────────────────────────────┘
```

---

<br>

## 🏗️ 14. System Architecture Diagram

```
┌═══════════════════════════════════════════════════════════════════════════┐
║                                                                           ║
║                AI CUSTOMER SUCCESS COPILOT — SYSTEM ARCHITECTURE           ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

                                ┌──────────────┐
                                │   End User    │
                                │   (CSM)       │
                                └──────┬───────┘
                                       │
                                ┌──────▼───────┐
                                │  Streamlit   │
                                │  Web UI      │
                                │  (app.py)    │
                                └──────┬───────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
   ┌──────────────┐           ┌────────────────┐           ┌──────────────┐
   │   Data       │           │   Report Tab   │           │  Multi-Tool  │
   │   Processing │           │  (3 Options)    │           │  Agent       │
   │   Pipeline   │           │                │           │  (tools/)    │
   │              │           │  ┌──────────┐  │           │              │
   │ CSV Load     │           │  │ DeepSeek │  │           │ data_analysis│
   │ Risk Score   │           │  │ Report   │  │           │     ↓        │
   │ Classify     │           │  ├──────────┤  │           │ rag_query    │
   │              │           │  │Enterprise│  │           │     ↓        │
   └──────┬───────┘           │  │ Report   │  │           │ chart_gen    │
          │                   │  ├──────────┤  │           │     ↓        │
          │                   │  │ AI Agent │  │           │ report_gen   │
          │                   │  │ One-Click│  │           │     ↓        │
          │                   │  └──────────┘  │           │ ppt_gen      │
          │                   └────────────────┘           └──────┬───────┘
          │                                                       │
          └──────────────────────────┬────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
           ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
           │   RAG        │ │   LLM        │ │   Output     │
           │   Knowledge  │ │   (DeepSeek) │ │   Generation │
           │   Base       │ │              │ │              │
           │              │ │ Chat Complet.│ │ Markdown     │
           │ FAISS Index  │ │ Risk Analysis│ │ PPT (9 slid) │
           │ Embeddings   │ │ AI Insights  │ │ Charts (4)   │
           └──────┬───────┘ └──────────────┘ └──────────────┘
                  │
         ┌────────┴────────┐
         ▼                 ▼
   ┌────────────┐   ┌────────────┐
   │ Knowledge  │   │ Persisted  │
   │ Documents  │   │ FAISS      │
   │ (*.md)     │   │ Index      │
   └────────────┘   └────────────┘

═════════════════════════════════════════════════════════════════════════════
  Data Layer                    Logic Layer                       Output Layer
═════════════════════════════════════════════════════════════════════════════
```

---

<br>

## 🔄 15. Workflow Flowchart

```
═══ DATA INGESTION ══════════════════════════════════════════════════════════

    ┌──────────────────┐
    │  CSV File        │
    │  (Upload / Env)  │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐     ┌──────────────────┐
    │  Load CSV        │────▶│  Parse Columns   │
    │  (utf-8-sig)     │     │  Validate Schema │
    └──────────────────┘     └────────┬─────────┘
                                      │
═══ RISK SCORING ═════════════════════╪══════════════════════════════════════
                                      │
             ┌────────────────────────▼────────────────────────┐
             │             Rule-Based Risk Scoring Engine       │
             │                                                  │
             │  login_days < 10   → (10 - days) × 1.5          │
             │  ticket_rate < 40  → (40 - rate) × 0.3          │
             │  marketing_rate < 30→ (30 - rate) × 0.2         │
             │  renewal_days < 0  → abs(days) × 0.5            │
             │  complaint > 3     → (count - 3) × 5            │
             │                                                  │
             │  score < 10  → LOW (🟢)                          │
             │  score 10-24 → MEDIUM (🟡)                       │
             │  score ≥ 25  → HIGH (🔴)                         │
             └──────────────────────┬───────────────────────────┘
                                    │
═══ KNOWLEDGE RETRIEVAL ═══════════╪══════════════════════════════════════
                                    │
             ┌──────────────────────▼───────────────────────────┐
             │           RAG Knowledge Retrieval                │
             │                                                  │
             │  Detect Issues → Build Queries → FAISS Search    │
             │     ↓                    ↓              ↓        │
             │  Low Login          "登录天数低..."    Similarity │
             │  High Complaints    "客户投诉..."     Search k=2 │
             │  Renewal Overdue    "续约逾期..."                 │
             │  Low Adoption       "功能使用率低..."              │
             └──────────────────────┬───────────────────────────┘
                                    │
═══ REPORT GENERATION ═════════════╪══════════════════════════════════════
                                    │
             ┌──────────────────────▼───────────────────────────┐
             │          Multi-Format Report Generation          │
             │                                                  │
             │  ┌────────────────┐  ┌────────────────┐         │
             │  │  Charts (4)    │  │  AI Insights    │         │
             │  │  ──────────    │  │  ──────────     │         │
             │  │  • GMV Bar     │  │  DeepSeek LLM   │         │
             │  │  • Risk Pie    │  │  Analysis +     │         │
             │  │  • Industry    │  │  RAG Context    │         │
             │  │  • Region      │  │                 │         │
             │  └────────────────┘  └────────────────┘         │
             │                                                  │
             │         ▼                        ▼               │
             │  ┌────────────────┐  ┌────────────────┐         │
             │  │  Markdown      │  │  PPT (9 slides) │         │
             │  │  8-Section     │  │  Professional   │         │
             │  │  Enterprise    │  │  Management     │         │
             │  │  Report        │  │  Presentation   │         │
             │  └────────────────┘  └────────────────┘         │
             └──────────────────────────────────────────────────┘

═══ OUTPUT ═════════════════════════════════════════════════════════════════

    📄 enterprise_report.md      📽️ enterprise_report.pptx      📊 Chart PNGs
```

---

<br>

## 💎 16. Project Highlights

### 🧩 True Agentic Architecture

Unlike simple "LLM wrappers," this project implements a **complete Agentic system** with tool registration, context passing, error isolation, and extensible pipeline design. The Multi-Tool Agent follows LangChain's Tool Calling paradigm.

### 🔀 Dual-Track "Rule + AI" Design

Deterministic rule engine handles what it's good at (scoring, classification, formatting) while AI handles what it's good at (insights, strategies, natural language). They cross-validate each other — rules catch AI hallucination, AI adds context rules miss.

### 📦 Production-Grade Code Organization

- **Separation of concerns**: `tools/` (Agent & Tools) vs `services/` (Report/PPT) vs `workflows/` (Pipeline) vs `agents/` (Risk AI) vs `src/` (Core)
- **Enterprise patterns**: Pipeline, Orchestrator, Repository, Factory
- **Type safety**: Full type hints, pydantic-settings, dataclasses
- **Error resilience**: Critical/non-critical step isolation, graceful degradation

### 🧠 Local RAG with Zero External Dependencies

The entire RAG pipeline runs **locally** — no external vector database, no cloud embedding API, no GPU required. FAISS CPU + sentence-transformers provide production-grade retrieval on a laptop.

### 🎯 CSM-Domain Specific

Built specifically for B2B SaaS Customer Success use cases, not generic chatbot. The risk scoring engine, knowledge base topics, report structure, and PPT slides are all designed with CSM workflows in mind.

### 📊 Multi-Format Output

One analysis pipeline produces **4 output formats**: raw DataFrame, structured Markdown report, professional PPT deck, and 4 types of data visualization charts — all from a single user click.

---

<br>

## 🏭 17. Enterprise Use Cases

### Use Case 1: Weekly Customer Health Review

```mermaid
Scenario: CSM reviews 50+ customer accounts every Monday
┌─────────────────────────────────────────────────────────────────────┐
│ 1. CSM opens the dashboard                                         │
│ 2. Uploads latest customer data CSV                                 │
│ 3. Clicks "AI Agent 一键生成完整报告"                                  │
│ 4. Agent runs: Scoring → RAG → Charts → MD Report → PPT            │
│ 5. CSM gets:                                                       │
│    ✓ Risk-prioritized customer list                                 │
│    ✓ AI-generated insights & action items                           │
│    ✓ PPT ready for weekly team meeting                              │
│ 6. Time saved: 4 hours → 30 seconds                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Use Case 2: Quarterly Business Review (QBR) Preparation

```markdown
Traditional: CSM spends 2-3 days pulling data, making charts, writing reports
AI Copilot: Upload data → Click → 30 seconds → Full QBR package ready
```

### Use Case 3: New CSM Onboarding

```markdown
New CSMs get access to:
- Institutional knowledge via RAG (not just "ask your buddy")
- Standardized risk assessment methodology
- Auto-generated reports they can learn from
- Reduces ramp time from 3 months to ~1 month
```

### Use Case 4: Executive Dashboard

```markdown
VP of Customer Success gets:
- Automated portfolio health summary
- Risk trend analysis
- Data-driven resource allocation recommendations
- Consistent reporting across all CSMs
```

### Target Audience

| Role | Value |
|------|-------|
| **Customer Success Manager** | Automated reporting, risk prioritization, AI-suggested actions |
| **CS Team Lead / Director** | Portfolio-wide risk visibility, consistent reporting standards |
| **VP of Customer Success** | Data-driven decision support, scalable CS operations |
| **SaaS Founder / CTO** | Demo-ready AI + analytics engineering showcase |
| **AI Engineer** | Reference architecture for Tool Calling + RAG + Workflow |

---

<br>

## 🔭 18. Future Roadmap

### Short Term (Next)

- [ ] **LLM Tool Planning**: Enable dynamic tool selection via DeepSeek LLM analysis
- [ ] **Email Report Delivery**: Auto-send generated reports via email
- [ ] **PDF Export**: Add WeasyPrint or ReportLab PDF generation
- [ ] **CRM Integration**: HubSpot/Salesforce data sync via API

### Medium Term (Next Quarter)

- [ ] **Churn Prediction ML Model**: Add LightGBM/XGBoost predictive model alongside rule engine
- [ ] **Multi-Tenant Support**: Organization-level data isolation
- [ ] **Scheduled Reports**: Cron-based auto-reporting with email delivery
- [ ] **Interactive Charts**: Upgrade from matplotlib PNG to Plotly interactive

### Long Term (Next Half)

- [ ] **Real-Time Dashboard**: WebSocket-based live customer health monitoring
- [ ] **Multi-LLM Support**: Plug-and-play switching between GPT-4o, Claude, DeepSeek, local models
- [ ] **REST API**: Expose report generation as RESTful API for external integration
- [ ] **RBAC**: Role-based access control for enterprise deployment
- [ ] **Docker Deployment**: Containerized deployment with docker-compose

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Development Roadmap                               │
│                                                                      │
│  Q2 2026                    Q3 2026                    Q4 2026       │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────┐ │
│  │ LLM Tool Planning  │  │ Churn Prediction   │  │ Real-Time Dash │ │
│  │ Email Reports      │  │ Multi-Tenant       │  │ Multi-LLM      │ │
│  │ PDF Export         │  │ Scheduled Reports  │  │ REST API       │ │
│  │ CRM Integration    │  │ Interactive Charts │  │ RBAC + Docker  │ │
│  └────────────────────┘  └────────────────────┘  └────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

<br>

## 👨‍💻 19. Author & License

### Author

**Rileymisha**

- GitHub: [@Rileymisha](https://github.com/Rileymisha)
- Project: [AI-Customer-Success-Copilot](https://github.com/Rileymisha/AI-Customer-Success-Copilot)

### License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 Rileymisha

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

### Acknowledgments

- [DeepSeek](https://deepseek.com) for their powerful and cost-effective LLM API
- [LangChain](https://langchain.com) for the RAG framework and Tool Calling inspiration
- [Streamlit](https://streamlit.io) for the rapid UI development framework
- [FAISS](https://github.com/facebookresearch/faiss) for the vector search library

---

<p align="center">
  <b>Built with ❤️ for Customer Success Teams Everywhere</b><br>
  <i>AI Customer Success Copilot — Turning Data into Retention</i>
</p>

<p align="center">
  <a href="#-table-of-contents">Back to Top</a> •
  <a href="https://github.com/Rileymisha/AI-Customer-Success-Copilot/issues">Report Bug</a> •
  <a href="https://github.com/Rileymisha/AI-Customer-Success-Copilot/discussions">Discussion</a>
</p>

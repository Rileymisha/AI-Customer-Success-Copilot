# AI-Customer-Success-Copilot Enterprise Reporting — 系统架构

## 一、工作流架构

### 整体架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        用户入口                                   │
│              Streamlit App / CLI / API                           │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Workflow 层（编排层）                         │
│              workflows/report_workflow.py                        │
│                                                                  │
│  1.load_data → 2.analyze → 3.identify → 4.retrieve(knowledge)   │
│           → 5.insights(LLM) → 6.charts → 7.report → 8.ppt       │
└──┬───────────┬───────────┬───────────┬───────────────────────────┘
   │           │           │           │
   ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐
│数据层   │ │分析层   │ │知识层   │ │ 生成层          │
│pipeline│ │pipeline│ │RAG     │ │ Report/PPT/Chart│
│CSV加载 │ │风险评分 │ │FAISS   │ │ 生成器          │
└────────┘ └────────┘ └────────┘ └────────────────┘
```

### 设计思想：Pipeline 模式

整个系统采用 **Pipeline（管道）模式**：

```
输入数据 → Step 1 → Step 2 → ... → Step N → 输出成果
```

每个步骤：
- 有明确的输入和输出
- 只做一件事
- 通过 WorkflowContext 共享数据
- 可以单独替换、升级、跳过

### 为什么用 Pipeline？

| 场景 | 传统写法 | Pipeline 写法 |
|---|---|---|
| 新增一个图表步骤 | 修改整个函数，加 import 和调用 | 加一个 step 注册就行 |
| 跳过 PPT 生成 | 改代码注释掉 | 从 steps 列表移除该 step |
| 某个步骤报错 | 整个流程崩溃 | 非关键步骤失败不影响后续 |
| 替换图表库 | 改所有相关代码 | 只替换 ChartGenerator 实现 |

---

## 二、为什么模块化

### 模块划分

```
src/ai_cs_copilot/
├── services/          # 服务层（LLM、RAG）
│   ├── llm_service.py
│   └── rag_service.py
├── pipelines/         # 数据管道（CSV加载、风险评分）
│   └── customer_analytics.py
├── config.py          # 配置

顶层的 services/
├── report_generator.py   # Markdown 报告生成
├── ppt_generator.py      # PPT 生成

visualizations/
└── chart_generator.py    # 图表生成

workflows/
└── report_workflow.py    # 工作流编排

agents/
└── customer_risk_agent.py # AI 代理
```

### 模块化的好处

1. **可替换性**：想换图表库（matplotlib → plotly）只需要改 `chart_generator.py`
2. **可测试性**：每个模块可以单独写单元测试
3. **并行开发**：不同开发者可以同时改不同模块
4. **关注点分离**：工作流不关心图表怎么画，图表不关心数据怎么加载

### 为什么分 services/ 和 workflows/

| 层级 | 职责 | 例子 |
|---|---|---|
| `services/` | **做什么**：具体的业务操作 | 生成 Markdown、生成 PPT、调用 LLM |
| `workflows/` | **什么时候做**：编排顺序 | 先加载数据、再分析、再生成报告 |

**类比：餐厅厨房**
- `services/` = 厨师：切菜、炒菜、装盘
- `workflows/` = 主厨：决定先切菜再炒菜，哪道菜先做

---

## 三、企业 AI 报告系统原理

### 报告生成流程

```
原始数据
    │
    ▼
┌──────────────┐
│ 规则引擎      │ ← 确定性：风险评分、客户分类
│ (Pandas)     │    速度快、无幻觉
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ RAG 知识库    │ ← 企业知识：策略文档、历史案例
│ (FAISS)      │    让 AI 的回答有据可依
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 大模型 (LLM)  │ ← 生成能力：洞察、建议、计划
│ (DeepSeek)   │    创造性、自然语言
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 报告生成      │ ← 格式化输出
│ (MD / PPT)   │    Markdown 给团队、PPT 给管理层
└──────────────┘
```

### 为什么用规则引擎 + AI 两条腿？

| 能力 | 规则引擎 | 大模型 |
|---|---|---|
| 一致性 | 每次结果一样 | 可能不同 |
| 速度 | 毫秒级 | 秒级 |
| 成本 | 几乎为零 | 按 token 计费 |
| 创造性 | 零 | 强 |
| 幻觉 | 无 | 有 |

**最佳实践**：确定性的事（风险评分、分类）用规则引擎；创造性的事（洞察、建议）用 AI。

---

## 四、工作流编排思想

### 错误处理策略

```
每个步骤要么成功、要么失败

critical=True 的步骤：          critical=False 的步骤：
  加载数据                         生成图表
  风险评分                         生成报告
  客户分类                         生成 PPT
  │                                │
  ▼                                ▼
失败则终止整个工作流            失败则跳过，继续执行后续步骤
```

### 上下文传递

```
WorkflowContext（贯穿整个 Pipeline）
├── data_source:     "sample_customer_data.csv"
├── df:              DataFrame（原始数据）
├── df_annotated:    DataFrame（已标注风险）
├── categories:      {"high_risk": [...], "high_value": [...], "growth": [...]}
├── rag_context:     "知识库检索结果..."
├── insights:        "AI 经营洞察..."
├── chart_paths:     {"gmv_bar": "vis/gmv.png", ...}
├── markdown_path:   "reports/report.md"
├── ppt_path:        "reports/report.pptx"
└── errors:          [("step_name", "error message"), ...]
```

每个步骤只修改 context 中属于自己的那部分，不关心其他步骤的数据。

### 可扩展性

```python
# 添加自定义步骤
wf = ReportWorkflow()
wf.add_step("send_email", "发送邮件报告", send_email_fn)

# 或者完全自定义执行顺序
wf.steps = [wf.steps[0], wf.steps[1], my_custom_step]
```

---

## 五、技术栈

| 组件 | 技术 | 用途 |
|---|---|---|
| 工作流引擎 | 自实现 Pipeline | 步骤编排与调度 |
| 数据加载 | Pandas | CSV 读取与处理 |
| 风险评分 | 自制规则引擎 | 客户风险量化 |
| 知识库 | LangChain + FAISS | 文档检索 |
| Embedding | sentence-transformers | 文本向量化 |
| 大模型 | DeepSeek (OpenAI 兼容) | 经营洞察生成 |
| 图表 | matplotlib | PNG 图表 |
| 报告 | Markdown | 团队可读报告 |
| 演示 | python-pptx | 管理层 PPT |

## 六、文件一览

```
workflows/
└── report_workflow.py       # 主工作流调度器

services/
├── report_generator.py      # Markdown 报告生成
└── ppt_generator.py         # PPT 报告生成

visualizations/
└── chart_generator.py       # matplotlib 图表生成

templates/
└── report_template.md       # 报告模板参考

reports/                     # 输出目录
├── enterprise_report.md
└── enterprise_report.pptx

visualizations/              # 图表输出目录
├── gmv_bar.png
├── risk_pie.png
├── industry_bar.png
└── region_bar.png

SYSTEM_ARCHITECTURE.md       # 本架构文档
```

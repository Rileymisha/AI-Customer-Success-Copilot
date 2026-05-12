# Multi-Tool AI Agent 架构文档

## 一、什么是 Tool Calling？

### 核心思想

**Tool Calling（工具调用）** 是让 AI 模型能够调用外部工具的能力。它不是让模型"思考"答案，而是让模型"决定"需要调用什么工具来获取答案。

```
传统 LLM:  用户问题 → LLM 生成文本 → 返回文本
Tool Calling: 用户问题 → LLM 决定调什么工具 → 执行工具 → 工具结果 → LLM 整合 → 返回
```

### 现实类比

> 你是一位主厨（Agent），厨房里有各种工具（Tools）：刀、砧板、锅、炉灶。
> 客人点了一份"番茄炒蛋"（Task），你决定：
> 1. 用「刀+砧板」切番茄
> 2. 用「碗」打鸡蛋
> 3. 用「锅+炉灶」炒菜
>
> 你不是自己变成这些工具，而是**决定什么时候用什么工具**。

### LangChain 的 Tool Calling

在 LangChain 中，Tool Calling 通过以下方式实现:

```python
# 1. 定义工具
def search_web(query: str) -> str:
    """搜索网络信息"""
    return search(query)

# 2. 注册工具
tools = [Tool(name="search", func=search_web, description="搜索网络信息")]

# 3. 绑定到 LLM
llm_with_tools = llm.bind_tools(tools)

# 4. Agent 自动决定调用哪些工具
result = agent_executor.run("查找最新的市场数据")
```

---

## 二、本项目 Tool Calling 实现

### 整体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                      用户点击「AI Agent 一键生成」                     │
└─────────────────────────┬────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     MultiToolAgent（编排层）                          │
│                                                                      │
│  1. 任务规划 (_plan) → 分析任务描述，决定工具序列                      │
│  2. 工具调用 (_execute_tool) → 按序执行每个工具                        │
│  3. 上下文传递 (AgentContext) → 数据在工具间流转                      │
│  4. 错误处理 → 关键步骤失败终止，非关键跳过                            │
│  5. 结果汇总 → 生成执行摘要                                           │
└──┬───────────┬───────────┬───────────┬───────────┬───────────────────┘
   │           │           │           │           │
   ▼           ▼           ▼           ▼           ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│数据     │ │RAG     │ │图表     │ │Markdown│ │PPT     │
│分析工具  │ │查询工具 │ │生成工具 │ │报告工具 │ │生成工具 │
│data_   │ │rag_    │ │chart_  │ │report_ │ │ppt_    │
│analysis │ │query   │ │genera- │ │genera- │ │genera- │
│         │ │        │ │tion    │ │tion    │ │tion    │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
```

### AgentContext: 工具间的数据总线

每个工具不直接调用另一个工具，而是通过 AgentContext 共享数据:

```
AgentContext 中的数据流:

task: "生成企业经营分析报告"
df: DataFrame（原始数据）
    │
    ▼  data_analysis 工具执行
df_annotated: DataFrame（已标注风险等级）
categories: {"high_risk": [...], "high_value": [...], "growth": [...]}
    │
    ▼  rag_query 工具执行
rag_context: "知识库检索结果..."
    │
    ▼  chart_generation 工具执行
chart_paths: {"gmv_bar": "vis/gmv.png", "risk_pie": "vis/risk_pie.png", ...}
    │
    ▼  report_generation 工具执行
markdown_path: "reports/enterprise_report.md"
    │
    ▼  ppt_generation 工具执行
ppt_path: "reports/enterprise_report.pptx"
```

### 工具注册机制

```python
# 每个工具独立注册，Agent 通过 name 索引
agent.register_tool(DataAnalysisTool())
agent.register_tool(RAGQueryTool())
agent.register_tool(ChartTool())
agent.register_tool(ReportTool())
agent.register_tool(PPTTool())

# Agent 获取所有工具的规格说明
specs = agent.get_tool_specs()
# → [
#     {"name": "data_analysis", "description": "客户经营数据分析工具...", "parameters": [...]},
#     {"name": "rag_query", "description": "RAG 知识库检索工具...", "parameters": [...]},
#     ...
#   ]
```

---

## 三、Agent 如何选择工具？

### 当前实现: 规则 Pipeline

目前 Agent 使用预设的 Pipeline 顺序执行工具:

```python
_DEFAULT_PIPELINE = [
    ("数据标注与分类", "data_analysis", True),    # 关键步骤
    ("知识库检索", "rag_query", False),             # 非关键
    ("图表生成", "chart_generation", False),        # 非关键
    ("Markdown 报告生成", "report_generation", False), # 非关键
    ("PPT 生成", "ppt_generation", False),          # 非关键
]
```

为什么选择规则 Pipeline 而非纯 LLM 规划?

| 维度 | 规则 Pipeline | LLM 动态规划 |
|------|--------------|-------------|
| **确定性** | 每次执行顺序一致 | 可能不同 |
| **速度** | 无需额外 LLM 调用 | 需要先调用 LLM 规划 |
| **可靠性** | 不会规划出错 | 可能选错工具或顺序 |
| **适用场景** | 标准化流程（适合报告生成） | 开放性问题（适合通用助手） |

### 未来扩展: LLM 动态规划

预留了 LLM 规划接口:

```python
def _plan(self, task: str) -> List[tuple]:
    if self.use_llm_planning:
        # TODO: 调用 LLM 分析 task，动态决定工具序列
        pass
    return list(self.pipeline)
```

启用 LLM 规划后，Agent 会:
1. 分析任务描述 → 理解用户需要什么
2. 查看可用工具列表（name + description + parameters）
3. 决定调用哪些工具、以什么顺序调用
4. 动态生成执行计划

---

## 四、为什么企业应用偏好 Tool Agent？

### 1. 可观测性（Observability）

```
传统代码: 数据 → 处理 → 报告（黑盒，很难知道中间发生了什么）
Tool Agent: 数据 → 工具① → 工具② → 工具③（每步都可观测、可记录）
```

每个工具的执行都有日志，可以精确知道:
- 哪个工具在执行
- 执行了多久
- 成功还是失败
- 输出了什么

### 2. 容错性（Fault Tolerance）

```
传统代码: A→B→C→D，B 崩溃则全部失败
Tool Agent: A→B→C→D，B 失败（非关键）→ 跳过 B，继续 C→D
```

### 3. 可测试性（Testability）

每个工具可以独立测试:

```python
# 单独测试数据分析工具
tool = DataAnalysisTool()
result = tool.run(df=test_data)
assert "risk_level" in result["df_annotated"].columns

# 单独测试图表工具
chart_tool = ChartTool()
result = chart_tool.run(df=test_data_annotated)
assert len(result["chart_paths"]) == 4
```

### 4. 可替换性（Replaceability）

```
想换图表库? 只改 ChartTool 的实现
想换 LLM? 只改 RAGQueryTool 或其他 LLM 相关工具
想新增输出格式? 加一个新工具，注册到 Agent 即可
```

### 5. 人机协作（Human-in-the-Loop）

企业场景中，关键决策点可以插入人工审核:

```
Agent 执行 → 数据标注完成 → 【人工确认】 → 继续生成报告
```

---

## 五、多工具工作流设计哲学

### 原则 1: 每个工具只做一件事

| 工具 | 职责 | 不做的事 |
|------|------|---------|
| DataAnalysisTool | 分析数据、标注风险 | 画图、生成报告 |
| RAGQueryTool | 检索知识库 | 分析数据 |
| ChartTool | 生成图表 PNG | 写报告 |
| ReportTool | 生成 Markdown | 生成 PPT |
| PPTTool | 生成 PPT | 写 Markdown |

### 原则 2: 工具间无直接依赖

工具不直接调用其他工具，通过 AgentContext 共享数据:

```python
# ❌ 错误: 工具直接依赖其他工具
class ChartTool:
    def run(self, df):
        categories = DataAnalysisTool().run(df)  # 不要这样做!
        ...

# ✅ 正确: 工具只依赖 context 中的数据
class ChartTool:
    def run(self, df):
        # 只处理 df，不关心数据从哪来
        ...
```

### 原则 3: 可插拔设计

```
tools/                    # 工具目录，每个工具可独立增删
├── base_tool.py          # 抽象基类
├── data_analysis_tool.py # 数据分析工具
├── rag_query_tool.py     # RAG 检索工具
├── chart_tool.py         # 图表工具
├── report_tool.py        # 报告工具
├── ppt_tool.py           # PPT 工具
└── agent.py              # Agent 编排器
```

### 原则 4: "规则 + AI" 双轨制

```
┌──────────────────────────────────────────────────┐
│                  任务描述                          │
│            "生成企业经营分析报告"                   │
└────────────────┬─────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  规则引擎     │  │  AI 大模型   │
│  (确定性)     │  │  (创造性)    │
│              │  │              │
│  • 风险评分   │  │  • 经营洞察  │
│  • 客户分类   │  │  • 策略建议  │
│  • 图表生成   │  │  • 行动计划  │
│  快/稳/省     │  │  灵活/智能   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └──────┬──────────┘
              ▼
     ┌──────────────┐
     │  最终报告     │
     │  规则保准度    │
     │  + AI 添创意  │
     └──────────────┘
```

这一思想与已有的企业报告系统（SYSTEM_ARCHITECTURE.md）完全一致。

---

## 六、与传统 Workflow Pipeline 的对比

| 维度 | 传统 Workflow (report_workflow.py) | Tool Agent (tools/agent.py) |
|------|-----------------------------------|---------------------------|
| **模式** | Pipeline（硬编码步骤顺序） | Agent（可动态规划步骤） |
| **数据传递** | WorkflowContext（数据类） | AgentContext（数据类） |
| **错误处理** | critical / non-critical | 关键/非关键步骤 |
| **可扩展性** | 修改 steps 列表 | 注册/注销工具 |
| **LLM 参与** | 仅生成洞察 | 规划 + 洞察 |
| **设计思想** | 步骤编排 | 工具调用 |

### 什么时候用哪个？

- **标准化报告生成** → 传统 Workflow（更稳定、更快）
- **需要灵活编排的任务** → Tool Agent（可扩展性更强）
- **两者可以协同**: Workflow 作为 Agent 的一个"大工具"被调用

---

## 七、文件一览

```
tools/                          # 工具包目录
├── __init__.py                 # 包初始化，导出所有工具和 Agent
├── base_tool.py                # BaseTool 抽象基类 + ToolSpec + ToolParameter
├── data_analysis_tool.py       # 数据分析工具（风险评分、分类）
├── rag_query_tool.py           # RAG 知识库检索工具
├── chart_tool.py               # 图表生成工具（matplotlib PNG）
├── report_tool.py              # Markdown 报告生成工具
├── ppt_tool.py                 # PPT 演示文稿生成工具
└── agent.py                    # MultiToolAgent 多工具编排智能体

MULTI_AGENT_ARCHITECTURE.md     # 本架构文档
```

---

*本文档由 AI-Customer-Success-Copilot 自动生成，遵循 LangChain Tool Calling 设计思想*

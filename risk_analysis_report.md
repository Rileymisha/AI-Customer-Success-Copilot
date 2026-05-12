# 客户风险分析报告

## 报告说明

本报告由 `CustomerRiskAgent` 自动生成，基于 DeepSeek 大模型对客户数据进行多维度风险分析。

### 数据来源
- 客户基础信息与行为指标（CSV 文件）
- 规则引擎预评分结果

### 分析方法
1. **规则预评分**：基于 `customer_analytics.py` 中的量化公式计算基础风险分
2. **AI 深度分析**：将规则评分结果与原始数据一起送入 DeepSeek，由模型输出结构化的分析结论

---

## 报告结构

### 一、分析概览
展示整体客户分布情况：

| 指标 | 数量 |
|---|---|
| 高风险客户 | N |
| 中风险客户 | N |
| 低风险客户 | N |
| 高价值客户 | N |

### 二、高风险客户详情
每位高风险客户单独列出，包含：
- **风险评分**：0-100 的量化分数
- **风险原因**：AI 分析的具体原因（引用实际指标）
- **经营建议**：短期（1-4 周）与长期（1-3 个月）策略
- **建议运营动作**：可执行的落地动作列表

### 三、高价值客户
列出所有高价值客户及其维护建议。

### 四、总结与行动建议
整体行动优先级与资源分配建议。

---

## 输出格式

Agent 同时支持两种输出格式：

- **JSON**（`reports/risk_analysis_results.json`）— 供程序进一步处理
- **Markdown**（`reports/risk_analysis_report.md`）— 供团队直接阅读

## 风险判定标准

| 维度 | 判定条件 | 风险等级 |
|---|---|---|
| 登录活跃度 | login_days < 5 | 高 |
| 登录活跃度 | 5 <= login_days < 10 | 中 |
| 功能采用 | ticket_usage_rate < 20% 且 marketing_usage_rate < 20% | 高 |
| 功能采用 | ticket_usage_rate < 40% 或 marketing_usage_rate < 30% | 中 |
| 续费状态 | renewal_days_left < 0（已逾期） | 高 |
| 续费状态 | 0 <= renewal_days_left < 30（即将到期） | 中 |
| 投诉情况 | complaint_count > 8 | 高 |
| 投诉情况 | complaint_count > 3 | 中 |
| 客户价值 | monthly_gmv >= 200000 + login_days >= 20 + ticket_usage_rate >= 80% + complaint_count <= 1 | 高价值 |

## 使用方式

```python
from pathlib import Path
from agents.customer_risk_agent import CustomerRiskAgent
from src.ai_cs_copilot.pipelines.customer_analytics import load_customer_csv

# 加载数据
df = load_customer_csv(Path("data/sample_customer_data.csv"))

# 创建 Agent 并分析
agent = CustomerRiskAgent()
results = agent.analyze(df)

# 保存报告
agent.save_report(results, Path("reports/risk_analysis_report.md"))
```

## 输出 JSON 结构

```json
{
  "customer_name": "客户名称",
  "risk_level": "高/中/低",
  "customer_type": "高价值/正常/高风险",
  "risk_score": 0-100,
  "risk_reason": "风险原因描述，引用具体指标",
  "business_suggestion": "经营建议，含短期和长期策略",
  "customer_actions": [
    "行动1（含执行方式）",
    "行动2（含执行方式）",
    "行动3（含执行方式）"
  ]
}
```

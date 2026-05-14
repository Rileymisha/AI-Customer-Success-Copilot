<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/DeepSeek-API-4A6CF7?style=for-the-badge&logo=deepseek&logoColor=white" alt="DeepSeek">
  <img src="https://img.shields.io/badge/LangChain-0.2%2B-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/FAISS-RAG-00A86B?style=for-the-badge&logo=facebook&logoColor=white" alt="FAISS">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License">
</p>

# AI-Customer-Success-Copilot

给 B2B SaaS 客户成功团队用的自动化分析工具。上传客户经营数据，自动做风险评分、知识库检索、AI 分析，然后生成经营分析报告和 PPT。

原来手动做一套周报要 4-5 小时，点一下 30 秒出完。

---

## 快速开始

```bash
git clone https://github.com/Rileymisha/AI-Customer-Success-Copilot.git
cd AI-Customer-Success-Copilot
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 编辑填入 DeepSeek API Key
streamlit run app.py
```

## 功能

| 功能 | 说明 |
|------|------|
| 风险评分 | 根据登录天数、功能使用率、续约天数、投诉数等维度打分，分高/中/低三档 |
| AI 深度分析 | DeepSeek 对高风险客户做归因和建议 |
| RAG 知识库 | 本地 FAISS 向量库，自动匹配客户问题到应对策略（低登录、投诉处理、续约挽留等） |
| 自动图表 | 4 张 matplotlib 图表：GMV 排名、风险分布、行业分布、地区分布 |
| 经营分析报告 | 8 个章节的 Markdown 报告，含执行摘要、风险分析、AI 洞察、行动方案 |
| PPT 生成 | 9 页幻灯片，图表自动嵌入 |
| 一键全自动 | AI Agent 串联上述所有步骤，一次点击出完整报告 + PPT + 图表 |

## 页面说明

四个 Tab：
- **数据概览** — 客户数据表格，支持 CSV 上传下载
- **风险客户** — 按风险等级筛选
- **AI 报告生成** — 三个入口：DeepSeek 文本分析 / 生成报告 & PPT / AI Agent 一键全自动
- **历史记录** — SQLite 存储的报告存档

## 项目结构

```
├── app.py                          # Streamlit 入口
├── src/ai_cs_copilot/             # 业务逻辑
│   ├── config.py                  # 配置
│   ├── pipelines/                 # 数据处理管线
│   └── services/                  # LLM / RAG 服务
├── agents/                        # AI 风险分析代理
├── tools/                         # Multi-Tool Agent（5 个工具）
├── workflows/                     # Pipeline 编排
├── knowledge_base/                # RAG 知识文档
├── services/                      # 报告 / PPT 生成
└── visualizations/                # 图表引擎
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | 否 | 默认 `https://api.deepseek.com` |
| `CUSTOMER_DATA_CSV` | 否 | 自定义 CSV 路径 |

## 技术栈

- **前端**: Streamlit, Pandas, matplotlib
- **后端**: Python 3.10, LangChain, FAISS (CPU), SQLite, python-pptx
- **AI**: DeepSeek API, sentence-transformers（本地向量化）

核心思路是规则引擎做确定性的风险评分（可解释、可审计），AI 做洞察和建议，两套互相补充。

---

## License

MIT © Rileymisha

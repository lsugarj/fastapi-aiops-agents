# fastapi-aiops-agents
一、总体架构（生产级）
FastAPI API Layer
   ↓
Agent Layer（多Agent编排）
   ↓
LLM Service（统一封装）
   ↓
LiteLLM（多模型适配）
   ↓
OpenAI / Claude / Ollama / vLLM

二、项目结构
fastapi-aiops-agents/
├── app/
│   ├── api/                 # 路由层
│   │   └── v1/
│   │       └── agent.py
│   │
│   ├── agents/              # Agent层（核心）
│   │   ├── base.py
│   │   ├── aiops_agent.py
│   │   ├── log_agent.py
│   │   └── trace_agent.py
│   │
│   ├── llm/                 # LLM抽象层（关键）
│   │   ├── base.py
│   │   ├── litellm_client.py
│   │   └── router.py
│   │
│   ├── tools/               # 工具层（AIOps能力）
│   │   ├── prometheus.py
│   │   ├── loki.py
│   │   ├── jaeger.py
│   │   └── k8s.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   │
│   ├── schemas/
│   │   └── agent.py
│   │
│   └── main.py
│
├── pyproject.toml
└── README.md
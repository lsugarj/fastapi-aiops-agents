# fastapi-aiops-agents

一个生产级的 FastAPI + 多 Agent AIOps 框架，当前内置 Kubernetes 智能巡检 Agent，并集成日志、指标、链路追踪（OpenTelemetry）等基础可观测能力。

## 架构设计

### 分层架构

```
Client
  │
  ▼
FastAPI API Layer (路由 / Schema / 异常处理)
  │
  ▼
Agent Layer (BaseAgent + 领域 Agent：K8s / Log / Trace)
  │
  ├─(需要外部信息时)→ Tools Layer (Kubernetes / Prometheus / Loki / Jaeger)
  │
  ▼
LLM Layer (LLMRouter + LiteLLMClient)
  │
  ▼
DeepSeek / OpenAI / Anthropic / 其他 LiteLLM 兼容模型
```

### 关键设计点

- Agent 工具调用闭环：Agent 通过固定格式触发工具调用，再把工具结果回灌给 LLM 继续推理，直到生成最终报告
- 多模型路由：通过 LLMRouter 统一封装模型客户端，按名称选择（默认 deepseek）
- 生产可观测：内置 Metrics/Trace/Logging middleware，并提供 `/metrics`、`/healthz` 等标准端点
- 配置集中化：`config/config.toml` 统一管理应用、LLM、Kubernetes、日志与 OTEL 配置

## 项目结构

```
fastapi-aiops-agents/
├── app/
│   ├── main.py                     # FastAPI 入口：路由、middleware、异常处理、metrics
│   ├── api/
│   │   └── v1/
│   │       └── kubernetes_agent.py # K8s Agent API：/chat /inspect /health 等
│   ├── agents/
│   │   ├── base.py                 # Agent 基类：工具调用解析与迭代执行
│   │   ├── kubernetes_agent.py     # AIOpsAgent：K8s 智能巡检（可工具调用）
│   │   ├── log_agent.py            # LogAgent：日志分析
│   │   └── trace_agent.py          # TraceAgent：链路分析
│   ├── tools/
│   │   ├── kubernetes.py           # K8sTools：节点/Pod/Deployment/日志/异常 Pod 等
│   │   ├── prometheus.py
│   │   ├── loki.py
│   │   └── jaeger.py
│   ├── llm/
│   │   ├── router.py               # LLMRouter：多模型客户端统一入口
│   │   ├── litellm_client.py       # LiteLLMClient：通过 LiteLLM 调用各类模型
│   │   └── base.py                 # LLMResponse 等基础抽象
│   ├── schemas/
│   │   ├── agent.py                # ChatRequest/AgentResponse/AgentType 等
│   │   └── response.py             # ResponseModel/Response（包含 trace_id）
│   ├── middlewares/                # 统一日志、trace、metrics 等中间件
│   ├── exceptions/                 # 业务异常码与统一处理
│   └── core/                       # 配置、日志、trace、metrics 等基础设施
├── config/
│   └── config.toml                 # 全局配置
├── tests/                          # 单元测试
├── OBSERVABILITY.md                # 可观测说明
├── debug.py                        # 本地开发启动脚本
└── pyproject.toml
```

## 快速开始（拿来即用）

### 1) 安装依赖

使用 Poetry：

```bash
poetry install
```

或直接使用 pip（不推荐但可用）：

```bash
python -m pip install -e .
```

### 2) 配置

修改 [config.toml](file:///Users/lj/projects/fastapi-aiops-agents/config/config.toml)：

- `llm.deepseek_api_key / deepseek_base_url / deepseek_default_model`
- `kubernetes.kubeconfig_path / kubernetes_context`

说明：
- 本地运行默认读取 `~/.kube/config`
- 生产部署到集群内时，建议改造为 in-cluster 配置方式（或挂载 kubeconfig）

### 3) 启动服务

```bash
python debug.py
```

或：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8888
```

### 4) 访问端点

- 健康检查：`GET /healthz`
- Prometheus 指标：`GET /metrics`
- K8s Agent 健康：`GET /api/v1/agents/kubernetes/health`

## Kubernetes 智能巡检 Agent 使用

### 集群巡检

`POST /api/v1/agents/kubernetes/inspect?namespace=default`

```bash
curl -X POST "http://127.0.0.1:8888/api/v1/agents/kubernetes/inspect?namespace=default"
```

### 通用对话（支持命名空间上下文）

`POST /api/v1/agents/kubernetes/chat`

```bash
curl -X POST "http://127.0.0.1:8888/api/v1/agents/kubernetes/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "请检查是否存在异常 Pod，并给出排障建议",
    "agent_type": "aiops",
    "namespace": "default",
    "session_id": "demo"
  }'
```

### Pod 日志分析

`POST /api/v1/agents/kubernetes/analyze-logs?pod_name=xxx&namespace=default`

```bash
curl -X POST "http://127.0.0.1:8888/api/v1/agents/kubernetes/analyze-logs?pod_name=my-pod&namespace=default"
```

## 单元测试

```bash
python -m pytest
```

测试覆盖点包括：
- Agent 工具调用格式解析
- K8sTools kubeconfig/context 参数加载
- AIOpsAgent 工具调用闭环
- API 路由返回结构（ResponseModel + trace_id）

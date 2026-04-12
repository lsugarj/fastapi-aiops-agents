# 🚀 FastAPI 可观测性架构（Logging / Tracing / Metrics）

本项目基于现代可观测性体系设计，覆盖日志（Logging）、链路追踪（Tracing）、指标监控（Metrics），并统一接入观测后端，实现企业级监控与问题定位能力。

---

## 🧱 架构总览

```text
FastAPI
  ├── Logging（JSON + trace_id）
  ├── Tracing（OpenTelemetry）
  ├── Metrics（Prometheus）
  ↓
Collector / Export
  ├── Loki（日志）
  ├── Tempo（链路）
  └── Prometheus（指标）
```

---

## 📊 一、Logging（日志）

### ✅ 设计目标

* 结构化日志（JSON 格式）
* 自动注入 `trace_id`（打通 Tracing）
* 支持日志分级（INFO / DEBUG / ERROR）
* 支持日志轮转（按天切割）
* 可无缝接入日志平台（Loki / ELK）

### 🛠 技术选型

* 标准库：`logging`
* JSON 格式化：自定义 `Formatter`
* 上下文传递：`contextvars`
* 中间件：注入 `trace_id`

### 📌 示例日志

```json
{
  "timestamp": "2026-04-07T10:00:00Z",
  "level": "INFO",
  "message": "request success",
  "trace_id": "abc123",
  "path": "/api/user",
  "method": "GET"
}
```

---

## 🔗 二、Tracing（链路追踪）

### ✅ 设计目标

* 全链路追踪请求生命周期
* 自动关联 `trace_id` 与日志
* 支持分布式系统调用分析
* 可视化调用链路

### 🛠 技术选型

* 标准方案：OpenTelemetry
* FastAPI 自动埋点：`opentelemetry-instrumentation-fastapi`
* 导出器：OTLP

### 🔄 数据流

```text
Request → FastAPI → OpenTelemetry → OTLP Export → Tempo
```

### 📌 能力

* 请求耗时分析
* 慢接口定位
* 服务依赖拓扑
* 异常链路回溯

---

## 📈 三、Metrics（指标监控）

### ✅ 设计目标

* 采集服务关键指标
* 支持实时监控与报警
* 提供接口级性能分析

### 🛠 技术选型

* Prometheus Client：`prometheus_client`
* FastAPI 集成：中间件 + `/metrics` endpoint

### 📌 常见指标

| 指标                              | 说明      |
| ------------------------------- | ------- |
| `http_requests_total`           | 请求总数    |
| `http_request_duration_seconds` | 请求耗时    |
| `http_exceptions_total`         | 异常次数    |
| `in_progress_requests`          | 当前处理请求数 |

---

## 📦 四、Collector / Export（采集与导出）

### 统一出口（推荐架构）

```text
FastAPI
   ↓
OpenTelemetry Collector
   ↓
├── Loki（Logs）
├── Tempo（Traces）
└── Prometheus（Metrics）
```

### 🛠 组件说明

| 组件                      | 作用        |
| ----------------------- | --------- |
| Loki                    | 日志存储与查询   |
| Tempo                   | 分布式链路追踪   |
| Prometheus              | 指标采集与监控   |
| OpenTelemetry Collector | 数据统一收集与转发 |

---

## 🔥 五、核心设计亮点

### 1️⃣ 三位一体（Logs + Traces + Metrics）

* 日志中包含 `trace_id`
* Trace 可反查日志
* Metrics 可定位异常趋势

👉 实现真正的 **可观测闭环**

---

### 2️⃣ 低侵入设计

* 使用中间件自动注入
* 业务代码无需关心埋点细节

---

### 3️⃣ 高扩展性

* 支持接入：

  * ELK / Kafka（日志）
  * Jaeger（替代 Tempo）
  * Grafana（统一展示）

---

### 4️⃣ 云原生友好

* 支持 Kubernetes
* 支持 Sidecar / Agent 模式
* 标准 OTLP 协议

---

## 📊 六、可视化（推荐）

* Grafana（统一看板）

  * Logs（Loki）
  * Traces（Tempo）
  * Metrics（Prometheus）

---

## 🧩 七、适用场景

* 微服务架构
* 高并发 API 服务
* 分布式系统排障
* 企业级监控体系

---

## 🏁 总结

本架构通过：

* **Logging（结构化日志）**
* **Tracing（全链路追踪）**
* **Metrics（指标监控）**

结合：

* **Loki + Tempo + Prometheus**

构建完整的 **可观测性体系（Observability Stack）**，帮助系统实现：

* 快速定位问题
* 精准性能分析
* 可视化系统运行状态

---

## 📎 后续扩展（TODO）

* [ ] 接入告警系统（Alertmanager）
* [ ] Trace 与日志自动关联跳转
* [ ] 多环境隔离（dev / staging / prod）
* [ ] SLA / SLO 监控体系
* [ ] 自动化 Dashboard

---

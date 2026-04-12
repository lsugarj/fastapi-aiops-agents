"""Kubernetes 工具集"""
import json
from kubernetes import client, config
from app.core.logging import get_logger
from app.core.config import get_settings

kubernetes_config = get_settings().kubernetes

logger = get_logger(__name__)


class K8sTools:
    """K8s 巡检工具集"""

    def __init__(self):
        """初始化 K8s 客户端"""
        try:
            config.load_kube_config(
                config_file=kubernetes_config.kubeconfig_path,
                context=kubernetes_config.kubernetes_config
            )
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info("K8s 客户端初始化成功")
        except Exception as e:
            logger.warning(f"K8s 客户端初始化失败，将使用模拟模式: {e}")
            self.core_v1 = None
            self.apps_v1 = None

    def _safe_call(self, func, default=None):
        """安全调用 K8s API"""
        if self.core_v1 is None:
            return default
        try:
            return func()
        except Exception as e:
            logger.error(f"K8s API 调用失败: {e}")
            return default

    async def get_nodes_status(self) -> str:
        """获取所有节点状态"""

        def _get():
            nodes = self.core_v1.list_node()
            result = []
            for node in nodes.items:
                conditions = {c.type: c.status for c in node.status.conditions}
                result.append({
                    "name": node.metadata.name,
                    "ready": conditions.get("Ready") == "True",
                    "status": conditions,
                    "kubelet_version": node.status.node_info.kubelet_version,
                    "capacity_cpu": node.status.capacity.get("cpu"),
                    "capacity_memory": node.status.capacity.get("memory"),
                    "allocatable_cpu": node.status.allocatable.get("cpu"),
                    "allocatable_memory": node.status.allocatable.get("memory")
                })
            return json.dumps(result, ensure_ascii=False, indent=2)

        return self._safe_call(_get, json.dumps([{"error": "无法连接 K8s API"}], indent=2))

    async def get_pods(self, namespace: str = "default") -> str:
        """获取 Pod 列表"""

        def _get():
            pods = self.core_v1.list_namespaced_pod(namespace)
            result = []
            for pod in pods.items:
                # 计算重启次数
                restarts = 0
                if pod.status.container_statuses:
                    restarts = sum(c.restart_count for c in pod.status.container_statuses)

                # 获取状态原因
                status_reason = pod.status.reason or pod.status.phase
                if pod.status.container_statuses:
                    for cs in pod.status.container_statuses:
                        if cs.state.waiting:
                            status_reason = cs.state.waiting.reason
                            break
                        if cs.state.terminated:
                            status_reason = cs.state.terminated.reason
                            break

                result.append({
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "status_reason": status_reason,
                    "node": pod.spec.node_name,
                    "restarts": restarts,
                    "age": pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else None
                })
            return json.dumps(result, ensure_ascii=False, indent=2)

        return self._safe_call(_get, json.dumps([{"error": f"无法获取 {namespace} 的 Pods"}], indent=2))

    async def get_deployments(self, namespace: str = "default") -> str:
        """获取 Deployment 状态"""

        def _get():
            deps = self.apps_v1.list_namespaced_deployment(namespace)
            result = []
            for dep in deps.items:
                ready = dep.status.ready_replicas or 0
                desired = dep.spec.replicas or 0
                available = dep.status.available_replicas or 0

                result.append({
                    "name": dep.metadata.name,
                    "ready_replicas": ready,
                    "desired_replicas": desired,
                    "available_replicas": available,
                    "unavailable_replicas": dep.status.unavailable_replicas or 0,
                    "is_healthy": ready == desired and ready > 0
                })
            return json.dumps(result, ensure_ascii=False, indent=2)

        return self._safe_call(_get, json.dumps([{"error": f"无法获取 {namespace} 的 Deployments"}], indent=2))

    async def get_pod_logs(self, pod_name: str, namespace: str = "default", lines: int = 100) -> str:
        """获取 Pod 日志"""

        def _get():
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=lines
            )
            # 截取过长的日志
            if len(logs) > 5000:
                logs = logs[-5000:] + "\n... [日志已截断]"
            return logs

        result = self._safe_call(_get, f"[错误] 无法获取 Pod {pod_name} 的日志")
        return result

    async def get_namespace_summary(self) -> str:
        """获取所有命名空间摘要"""

        def _get():
            namespaces = self.core_v1.list_namespace()
            summary = []
            for ns in namespaces:
                ns_name = ns.metadata.name
                pods = self.core_v1.list_namespaced_pod(ns_name)

                pod_status = {"Running": 0, "Pending": 0, "Failed": 0, "Unknown": 0, "CrashLoopBackOff": 0}
                for pod in pods.items:
                    status = pod.status.phase
                    if status == "Running":
                        pod_status["Running"] += 1
                    elif status == "Pending":
                        pod_status["Pending"] += 1
                    elif status == "Failed":
                        # 检查是否是 CrashLoopBackOff
                        if pod.status.container_statuses:
                            for cs in pod.status.container_statuses:
                                if cs.state.waiting and cs.state.waiting.reason == "CrashLoopBackOff":
                                    pod_status["CrashLoopBackOff"] += 1
                                    break
                        else:
                            pod_status["Failed"] += 1
                    else:
                        pod_status["Unknown"] += 1

                summary.append({
                    "namespace": ns_name,
                    "pod_count": len(pods.items),
                    "pod_status": pod_status,
                    "status": ns.status.phase
                })
            return json.dumps(summary, ensure_ascii=False, indent=2)

        return self._safe_call(_get, json.dumps([{"error": "无法获取命名空间摘要"}], indent=2))

    async def get_pod_anomalies(self, namespace: str = "default") -> str:
        """获取异常 Pod"""

        def _get():
            pods = self.core_v1.list_namespaced_pod(namespace)
            anomalies = []

            for pod in pods.items:
                is_anomaly = False
                anomaly_type = None

                # 检查状态异常
                if pod.status.phase in ["Pending", "Failed", "Unknown"]:
                    is_anomaly = True
                    anomaly_type = pod.status.phase

                # 检查容器状态异常
                if pod.status.container_statuses:
                    for cs in pod.status.container_statuses:
                        if cs.state.waiting:
                            reason = cs.state.waiting.reason
                            if reason in ["CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull"]:
                                is_anomaly = True
                                anomaly_type = reason
                                break
                        if cs.state.terminated and cs.state.terminated.exit_code != 0:
                            is_anomaly = True
                            anomaly_type = f"Terminated (exit {cs.state.terminated.exit_code})"
                            break

                if is_anomaly:
                    anomalies.append({
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "anomaly_type": anomaly_type,
                        "restarts": sum(c.restart_count for c in
                                        pod.status.container_statuses) if pod.status.container_statuses else 0,
                        "node": pod.spec.node_name
                    })

            return json.dumps(anomalies, ensure_ascii=False, indent=2)

        return self._safe_call(_get, json.dumps([{"error": "无法获取异常 Pod"}], indent=2))


# 全局工具实例
k8s_tools = K8sTools()
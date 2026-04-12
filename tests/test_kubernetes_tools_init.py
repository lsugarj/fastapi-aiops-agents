from app.core.config import get_settings


def test_k8s_tools_load_kube_config_context(monkeypatch):
    from app.tools import kubernetes as k8s_module

    called = {}

    def _fake_load_kube_config(*, config_file=None, context=None, **kwargs):
        called["config_file"] = config_file
        called["context"] = context

    class _FakeCoreV1Api:
        pass

    class _FakeAppsV1Api:
        pass

    monkeypatch.setattr(k8s_module.config, "load_kube_config", _fake_load_kube_config)
    monkeypatch.setattr(k8s_module.client, "CoreV1Api", _FakeCoreV1Api)
    monkeypatch.setattr(k8s_module.client, "AppsV1Api", _FakeAppsV1Api)

    tools = k8s_module.K8sTools()

    assert tools.core_v1 is not None
    assert tools.apps_v1 is not None
    assert called["config_file"] == get_settings().kubernetes.kubeconfig_path
    assert called["context"] == get_settings().kubernetes.kubernetes_context


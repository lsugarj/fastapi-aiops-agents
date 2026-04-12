import tomllib
from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from typing import Any, Dict


class AppConfig(BaseModel):
    name: str
    env: str
    host: str
    port: int

class LoggingConfig(BaseModel):
    dir: str
    level: str
    max_bytes: str
    backup_count: int

class OpentelemetryConfig(BaseModel):
    otel_exporter_endpoint: str

class LLMConfig(BaseModel):
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_default_model: str
    openai_api_key: str
    anthropic_api_key: str
    agent_max_iterations: int
    agent_temperature: float

class KubernetesConfig(BaseModel):
    kubeconfig_path: str
    kubernetes_context: str

class Settings(BaseModel):
    app: AppConfig
    logging: LoggingConfig
    opentelemetry: OpentelemetryConfig
    llm: LLMConfig
    kubernetes: KubernetesConfig


def load_config() -> Dict[str, Any]:
    base_path = Path(__file__).resolve().parent.parent.parent

    # 1. 读取主配置
    with open(base_path / "config/config.toml", "rb") as f:
        base_config = tomllib.load(f)

    return base_config


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    toml_config = load_config()

    return Settings(**toml_config)
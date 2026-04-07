from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from se_model.llm_config import LLMConfig, creat_config


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL_NAME = "qwen3.5-plus"


class ModelConfigStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def _default_payload(self) -> dict[str, str]:
        return {
            "base_url": DEFAULT_BASE_URL,
            "api_key": os.getenv("DASHSCOPE_API_KEY", "").strip(),
            "model_name": DEFAULT_MODEL_NAME,
        }

    def _normalize_payload(self, payload: dict[str, object] | None) -> dict[str, str]:
        raw = payload or {}
        default = self._default_payload()
        return {
            "base_url": str(raw.get("base_url") or default["base_url"]).strip(),
            "api_key": str(raw.get("api_key") or default["api_key"]).strip(),
            "model_name": str(raw.get("model_name") or default["model_name"]).strip(),
        }

    def load(self) -> LLMConfig:
        payload: dict[str, object] | None = None
        if self.file_path.exists():
            try:
                import json

                payload = json.loads(self.file_path.read_text(encoding="utf-8"))
            except Exception:
                payload = None
        normalized = self._normalize_payload(payload)
        config = creat_config(
            api_key=normalized["api_key"],
            base_url=normalized["base_url"],
            model_name=normalized["model_name"],
        )
        config.validate()
        return config

    def load_or_initialize(self) -> LLMConfig:
        if not self.file_path.exists():
            config = creat_config(**self._default_payload())
            self.save(config)
            return config

        try:
            config = self.load()
        except Exception:
            config = creat_config(**self._default_payload())
            self.save(config)
            return config

        self.save(config)
        return config

    def save(self, config: LLMConfig) -> None:
        config.validate()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        import json

        self.file_path.write_text(
            json.dumps(asdict(config), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        clean = (api_key or "").strip()
        if not clean:
            return ""
        if len(clean) <= 8:
            return "*" * len(clean)
        return f"{clean[:4]}{'*' * max(len(clean) - 8, 4)}{clean[-4:]}"

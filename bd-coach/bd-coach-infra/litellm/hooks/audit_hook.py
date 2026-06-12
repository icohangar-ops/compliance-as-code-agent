"""Audit hook — logs every LLM call metadata to Postgres-compatible JSONL."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from litellm.integrations.custom_logger import CustomLogger


class AuditHook(CustomLogger):
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        persona = (kwargs.get("litellm_params") or {}).get("metadata", {}).get("persona", "UNKNOWN")
        payload = {
            "ts": time.time(),
            "event": "llm.call",
            "persona": persona,
            "model": kwargs.get("model"),
            "latency_ms": int((end_time - start_time).total_seconds() * 1000),
        }
        self._append(payload)

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        payload = {
            "ts": time.time(),
            "event": "llm.error",
            "model": kwargs.get("model"),
            "error": str(response_obj),
        }
        self._append(payload)

    @staticmethod
    def _append(payload: dict[str, Any]) -> None:
        os.makedirs("/var/log/bd-coach", exist_ok=True)
        with open("/var/log/bd-coach/audit.jsonl", "a") as f:
            f.write(json.dumps(payload) + "\n")

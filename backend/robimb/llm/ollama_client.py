"""Minimal HTTP client for local Ollama models."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

LOGGER = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_ENDPOINT") or "http://localhost:11434"
DEFAULT_MODEL = os.environ.get("ROBIMB_OLLAMA_MODEL") or "phi3:mini"
DEFAULT_TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT") or "120.0")


@dataclass(frozen=True)
class OllamaConfig:
    """Configuration for the Ollama client."""

    base_url: str = DEFAULT_OLLAMA_URL
    timeout: float = DEFAULT_TIMEOUT


class OllamaClient:
    """Very small wrapper over the Ollama HTTP API."""

    def __init__(self, config: Optional[OllamaConfig] = None):
        self._config = config or OllamaConfig()

    def generate(
        self,
        model_name: str,
        prompt: str,
        *,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Call the /api/generate endpoint and return the generated text."""

        if not model_name:
            raise ValueError("model_name must be provided")
        if not prompt:
            raise ValueError("prompt must be non-empty")

        url = self._config.base_url.rstrip("/") + "/api/generate"
        payload: Dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }
        if options:
            payload["options"] = options

        try:
            response = requests.post(url, json=payload, timeout=self._config.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            LOGGER.error("ollama_timeout", extra={"url": url, "timeout": self._config.timeout})
            raise RuntimeError(f"Ollama timeout after {self._config.timeout}s") from exc
        except requests.RequestException as exc:
            LOGGER.error("ollama_error", extra={"url": url, "error": str(exc)})
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

        if not isinstance(data, dict):
            raise RuntimeError("Unexpected Ollama response format")

        output = data.get("response")
        if not output:
            raise RuntimeError("Empty response from Ollama")
        return str(output)


def generate(
    model_name: str,
    prompt: str,
    *,
    endpoint: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
    options: Optional[Dict[str, Any]] = None,
) -> str:
    """Convenience function mirroring :meth:`OllamaClient.generate`."""

    client = OllamaClient(OllamaConfig(base_url=endpoint or DEFAULT_OLLAMA_URL, timeout=timeout))
    return client.generate(model_name=model_name, prompt=prompt, options=options)

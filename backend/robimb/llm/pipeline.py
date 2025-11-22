"""Pipeline that orchestrates deterministic cues with a compact Ollama prompt."""
from __future__ import annotations

import copy
import hashlib
import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from ..config import get_settings
from ..extraction.fuse import CandidateSource, Fuser, FusePolicy
from ..extraction.orchestrator import Orchestrator, OrchestratorConfig
from ..extraction.schema_registry import CategorySchema, PropertySpec, load_category_schema
from ..extraction.validators import validate_properties
from ..registry.schemas import slugify
from .ollama_client import DEFAULT_MODEL, DEFAULT_OLLAMA_URL, DEFAULT_TIMEOUT, OllamaClient, OllamaConfig
from .prompting import build_llm_prompt

LOGGER = logging.getLogger(__name__)

__all__ = ["LLMExtractionConfig", "LLMPropertyExtractor", "RuleCandidateGenerator"]


class _ExtractionCache:
    """Tiny LRU cache to avoid repeated LLM calls on identical inputs."""

    def __init__(self, max_size: int):
        self._store: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max(1, max_size)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key not in self._store:
            return None
        value = self._store.pop(key)
        # refresh LRU order
        self._store[key] = value
        return copy.deepcopy(value)

    def put(self, key: str, value: Dict[str, Any]) -> None:
        self._store[key] = copy.deepcopy(value)
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)


@dataclass
class LLMExtractionConfig:
    """Configuration for the Ollama-based property extractor."""

    model: str = DEFAULT_MODEL
    endpoint: str = DEFAULT_OLLAMA_URL
    timeout: float = DEFAULT_TIMEOUT
    registry_path: str = field(default_factory=lambda: str(get_settings().registry_path))
    use_rule_candidates: bool = True
    cache_size: int = 128
    temperature: float = 0.0


class RuleCandidateGenerator:
    """Reuse deterministic parsers/matchers to propose candidate values."""

    def __init__(self, registry_path: str | Path, *, enable_matcher: bool = True):
        cfg = OrchestratorConfig(
            source_priority=["parser", "matcher"],
            enable_matcher=enable_matcher,
            enable_llm=False,
            registry_path=str(registry_path),
            use_qa=False,
            fusion_mode="fuse",
            qa_null_threshold=0.0,
            qa_confident_threshold=0.0,
        )
        self._orchestrator = Orchestrator(
            fuse=Fuser(policy=FusePolicy.VALIDATE_THEN_MAX_CONF, source_priority=cfg.source_priority),
            llm=None,
            cfg=cfg,
        )

    def build(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        try:
            result = self._orchestrator.extract_document(doc)
        except Exception as exc:  # pragma: no cover - robustness
            LOGGER.warning("rule_candidates_failed", extra={"error": str(exc)})
            return {}
        return {
            prop_id: payload.get("value")
            for prop_id, payload in (result.get("properties") or {}).items()
            if payload.get("value") is not None
        }


class LLMPropertyExtractor:
    """Orchestrate rule-based hints with an Ollama prompt to fill property JSON."""

    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
        config: Optional[LLMExtractionConfig] = None,
        *,
        prompt_builder=build_llm_prompt,
        candidate_generator: Optional[RuleCandidateGenerator] = None,
    ) -> None:
        self._config = config or LLMExtractionConfig()
        self._llm = llm_client or OllamaClient(
            OllamaConfig(base_url=self._config.endpoint, timeout=self._config.timeout)
        )
        self._prompt_builder = prompt_builder
        self._candidate_generator = candidate_generator or (
            RuleCandidateGenerator(self._config.registry_path) if self._config.use_rule_candidates else None
        )
        self._cache = _ExtractionCache(self._config.cache_size) if self._config.cache_size > 0 else None

    def extract(self, doc: Dict[str, Any], property_filter: Optional[Sequence[str]] = None) -> Dict[str, Any]:
        text_id = self._resolve_text_id(doc)
        category_id, text, category, schema = self._prepare_doc(doc)
        selected_properties = self._select_properties(category.properties, property_filter)
        candidates = self._candidate_generator.build(doc) if self._candidate_generator else {}
        if property_filter:
            allowed = set(property_filter)
            candidates = {k: v for k, v in candidates.items() if k in allowed}

        prompt = self._prompt_builder(category_id, text, selected_properties, candidates=candidates)
        cache_key = self._cache_key(category_id, text, candidates, property_filter)
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        raw_response = self._llm.generate(
            self._config.model,
            prompt,
            options={"temperature": self._config.temperature},
        )
        llm_payload = self._parse_response(raw_response)

        properties_payload = self._build_payload(selected_properties, llm_payload)
        validation = self._attach_validation(
            category_id,
            properties_payload,
            ignore_required=bool(property_filter),
        )

        base_doc = {k: v for k, v in doc.items() if k != "_qa_predictions"}
        result = {
            **base_doc,
            "text_id": text_id,
            "categoria": category_id,
            "properties": properties_payload,
            "validation": {
                "status": "ok" if validation.ok else "failed",
                "errors": [
                    {
                        "property_id": issue.property_id,
                        "code": issue.code,
                        "message": issue.message,
                    }
                    for issue in validation.errors
                ],
            },
            "confidence_overall": self._confidence_overall(properties_payload),
            "_llm_choices": {
                "model": self._config.model,
                "endpoint": self._config.endpoint,
            },
        }

        if self._cache:
            self._cache.put(cache_key, result)
        return result

    # ------------------------------------------------------------------#
    # Internal helpers
    # ------------------------------------------------------------------#
    def _prepare_doc(self, doc: Dict[str, Any]) -> tuple[str, str, CategorySchema, Dict[str, Any]]:
        category_id = self._resolve_category(doc)
        category, schema = load_category_schema(category_id, registry_path=self._config.registry_path)
        text = doc.get("text", "") or ""
        return category_id, text, category, schema

    def _select_properties(
        self, properties: Sequence[PropertySpec], property_filter: Optional[Sequence[str]]
    ) -> Sequence[PropertySpec]:
        if not property_filter:
            return properties
        allowed = set(property_filter)
        filtered = tuple(prop for prop in properties if prop.id in allowed)
        return filtered or properties

    def _resolve_category(self, doc: Dict[str, Any]) -> str:
        category = doc.get("categoria") or doc.get("category") or doc.get("cat")
        if not category:
            raise ValueError("Categoria mancante nell'input")
        return slugify(str(category))

    def _resolve_text_id(self, doc: Dict[str, Any]) -> Optional[str]:
        for key in ("text_id", "id", "idx", "row_id"):
            if key in doc:
                return str(doc.get(key))
        return None

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            start = response_text.find("{")
            end = response_text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise RuntimeError("LLM must return a JSON object") from None
            parsed = json.loads(response_text[start : end + 1])
        if not isinstance(parsed, dict):
            raise RuntimeError("LLM must return a JSON object")
        return parsed

    def _build_payload(self, properties: Sequence[PropertySpec], llm_payload: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
        payload: Dict[str, Dict[str, Any]] = {}
        for prop in properties:
            value = llm_payload.get(prop.id)
            source = CandidateSource.QA_LLM.value if value is not None else None
            confidence = 0.65 if value is not None else 0.0
            payload[prop.id] = {
                "value": value,
                "source": source,
                "raw": None,
                "span": None,
                "confidence": confidence,
                "unit": prop.unit if value is not None else None,
                "normalized": None,
                "errors": [],
            }
        return payload

    def _attach_validation(
        self,
        category_id: str,
        properties: Dict[str, Dict[str, Any]],
        *,
        ignore_required: bool = False,
    ):
        validation_input = {
            key: value for key, value in properties.items() if value.get("source")
        }
        validation = validate_properties(
            category_id,
            validation_input,
            registry_path=self._config.registry_path,
        )
        if ignore_required:
            validation.errors = [
                issue for issue in validation.errors if issue.code != "missing_required"
            ]
        for issue in validation.errors:
            if ignore_required and issue.code == "missing_required":
                continue
            target = properties.setdefault(
                issue.property_id,
                {
                    "value": None,
                    "source": None,
                    "raw": None,
                    "span": None,
                    "confidence": 0.0,
                    "unit": None,
                    "errors": [],
                    "normalized": None,
                },
            )
            target.setdefault("errors", []).append(issue.message)
        for prop_id, normalized in validation.normalized.items():
            if prop_id in properties:
                properties[prop_id]["normalized"] = normalized.value
        return validation

    def _confidence_overall(self, properties: Mapping[str, Mapping[str, Any]]) -> float:
        confidences = [
            float(payload.get("confidence") or 0.0)
            for payload in properties.values()
            if payload.get("value") is not None
        ]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _cache_key(
        self,
        category: str,
        text: str,
        candidates: Mapping[str, Any],
        property_filter: Optional[Sequence[str]] = None,
    ) -> str:
        serialized = json.dumps(
            {
                "category": category,
                "text": text,
                "candidates": {k: v for k, v in candidates.items() if v is not None},
                "model": self._config.model,
                "properties": sorted(property_filter) if property_filter else None,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

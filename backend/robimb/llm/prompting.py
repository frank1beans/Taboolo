"""Compact prompt builder for Ollama-based property extraction."""
from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from ..extraction.schema_registry import PropertySpec

__all__ = ["build_llm_prompt"]


def _summarize_properties(properties: Sequence[PropertySpec]) -> str:
    summary_parts = []
    for prop in properties:
        meta = []
        if prop.type:
            meta.append(prop.type)
        if prop.unit:
            meta.append(f"unit={prop.unit}")
        if prop.enum:
            meta.append("enum=" + "|".join(prop.enum))
        descriptor = prop.id
        if meta:
            descriptor = f"{descriptor} ({', '.join(meta)})"
        summary_parts.append(descriptor)
    return "; ".join(summary_parts)


def build_llm_prompt(
    category_id: str,
    description: str,
    properties: Sequence[PropertySpec],
    *,
    candidates: Mapping[str, Any] | None = None,
) -> str:
    """Build a concise, deterministic prompt for the small LLM."""

    schema_stub = {prop.id: None for prop in properties}
    prop_summary = _summarize_properties(properties)
    trimmed_candidates = {k: v for k, v in (candidates or {}).items() if v is not None}
    candidate_json = json.dumps(trimmed_candidates, ensure_ascii=False)

    prompt_parts = [
        f"Categoria: {category_id}",
        "Estrai le proprieta tecniche dal testo seguente.",
        "Rispondi SOLO con un JSON valido contenente tutti i campi richiesti.",
        f"Campi: {prop_summary}",
        "Testo:",
        (description or "").strip() or "<vuoto>",
    ]
    if trimmed_candidates:
        prompt_parts.extend(
            [
                "Suggerimenti (possono essere errati):",
                candidate_json,
            ]
        )
    prompt_parts.extend(
        [
            "Restituisci esclusivamente il JSON con questi campi:",
            json.dumps(schema_stub, ensure_ascii=False),
        ]
    )
    return "\n".join(prompt_parts)

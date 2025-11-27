from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)

# Lazy-loaded robimb parsers and matchers
_robimb_parsers_loaded = False
_parse_thickness = None
_parse_dimensions = None
_parse_fire_class = None
_parse_thermal_transmittance = None
_parse_sound_insulation = None
_parse_acoustic_coefficient = None
_parse_flow_rate = None
_parse_ral_colors = None
_parse_labeled_dimensions = None
_MaterialMatcher = None
_BrandMatcher = None


# Supercategoria WBS -> (schema file name, category_id per roBERT)
SUPER_CATEGORY_SCHEMA = {
    11: ("controsoffitti.json", "controsoffitti"),
    10: ("opere_di_pavimentazione.json", "opere_di_pavimentazione"),
    9: ("opere_di_rivestimento.json", "opere_di_rivestimento"),
    12: ("opere_da_cartongessista.json", "opere_da_cartongessista"),
    16: ("opere_da_serramentista.json", "opere_da_serramentista"),
    18: ("opere_da_falegname.json", "opere_da_falegname"),
    25: ("apparecchi_sanitari_accessori.json", "apparecchi_sanitari_accessori"),
}

# Nome supercategoria -> id (fallback sul testo wbs6_description)
SUPER_CATEGORY_BY_NAME = {
    "controsoffitti": 11,
    "pavimentazione": 10,
    "rivestimento": 9,
    "cartongessista": 12,
    "cartongesso": 12,
    "serramentista": 16,
    "falegname": 18,
    "apparecchi sanitari": 25,
    "sanitari": 25,
}

REGISTRY_REL_PATH = Path("resources") / "data" / "properties" / "registry.json"
DEFAULT_OLLAMA_MODEL = os.environ.get("ROBERT_OLLAMA_MODEL") or os.environ.get("ROBIMB_OLLAMA_MODEL") or "phi3:mini"
DEFAULT_OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT") or "http://localhost:11434"


class PropertyExtractor:
    """Wrapper sugli estrattori roBERT: usa matchers/parser preconfigurati, senza LLM."""

    def __init__(self) -> None:
        self.orchestrator = None
        self._material_matcher = None
        self._brand_matcher = None
        self._llm_extractor = None
        self._llm_use_rules = os.environ.get("PROPERTY_LLM_USE_RULES", "1") not in {"0", "false", "False"}
        self._llm_enabled = os.environ.get("PROPERTY_LLM_ENABLED", "1") not in {"0", "false", "False"}
        # Se roBERT è stato spostato sotto backend/, puntiamo lì; in fallback restiamo compatibili con il vecchio layout
        candidate_under_backend = Path(__file__).resolve().parents[2] / "roBERT"
        legacy_root = Path(__file__).resolve().parents[4] / "roBERT"
        self.base_dir = candidate_under_backend if candidate_under_backend.exists() else legacy_root
        self.registry_path = self.base_dir / REGISTRY_REL_PATH
        self._ensure_sys_path()
        self._init_orchestrator()
        self._load_robimb_parsers()
        self._init_llm_extractor()

    def _ensure_sys_path(self) -> None:
        src_dir = self.base_dir / "src"
        if src_dir.exists():
            src_str = str(src_dir)
            if src_str not in sys.path:
                # Prepend to shadow eventual site-packages installs of robimb
                sys.path.insert(0, src_str)

    def _init_orchestrator(self) -> None:
        try:
            from robimb.extraction.fuse import Fuser
            from robimb.extraction.orchestrator import Orchestrator, OrchestratorConfig
            # Disabilitiamo LLM/QA: usiamo solo i matchers/parsings già pronti
            cfg = OrchestratorConfig(
                enable_llm=False,
                use_qa=False,
                registry_path=str(self.registry_path),
            )
            self.orchestrator = Orchestrator(fuse=Fuser(), llm=None, cfg=cfg)
        except Exception as exc:  # pragma: no cover - robustezza
            logger.exception("Impossibile inizializzare gli estrattori roBERT: %s", exc)
            self.orchestrator = None

    def _init_llm_extractor(self) -> None:
        if not self._llm_enabled:
            logger.info("LLM extractor disabilitato via variabile d'ambiente")
            return
        try:
            from robimb.llm.pipeline import LLMExtractionConfig, LLMPropertyExtractor, RuleCandidateGenerator
            from robimb.llm.ollama_client import OllamaClient, OllamaConfig

            cache_size = int(os.environ.get("PROPERTY_LLM_CACHE", "128"))
            model_name = os.environ.get("ROBERT_OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
            endpoint = os.environ.get("OLLAMA_ENDPOINT") or DEFAULT_OLLAMA_ENDPOINT

            llm_cfg = LLMExtractionConfig(
                model=model_name,
                endpoint=endpoint,
                registry_path=str(self.registry_path),
                use_rule_candidates=self._llm_use_rules,
                cache_size=cache_size,
            )
            client = OllamaClient(OllamaConfig(base_url=llm_cfg.endpoint, timeout=llm_cfg.timeout))
            candidate_generator = RuleCandidateGenerator(llm_cfg.registry_path) if llm_cfg.use_rule_candidates else None
            self._llm_extractor = LLMPropertyExtractor(
                llm_client=client,
                config=llm_cfg,
                candidate_generator=candidate_generator,
            )
            logger.info("LLM extractor inizializzato con modello %s", model_name)
        except Exception as exc:  # pragma: no cover - robustezza
            logger.warning("Impossibile inizializzare LLM extractor: %s", exc)
            self._llm_extractor = None

    def _load_robimb_parsers(self) -> None:
        """Carica i parser e matcher di robimb per il fallback."""
        global _robimb_parsers_loaded, _parse_thickness, _parse_dimensions, _parse_fire_class
        global _parse_thermal_transmittance, _parse_sound_insulation, _parse_acoustic_coefficient
        global _parse_flow_rate, _parse_ral_colors, _parse_labeled_dimensions
        global _MaterialMatcher, _BrandMatcher

        if _robimb_parsers_loaded:
            return

        try:
            from robimb.extraction.parsers.thickness import parse_thickness
            from robimb.extraction.parsers import dimensions
            from robimb.extraction.parsers.fire_class import parse_fire_class
            from robimb.extraction.parsers.thermal import parse_thermal_transmittance
            from robimb.extraction.parsers.sound_insulation import parse_sound_insulation
            from robimb.extraction.parsers.acoustic import parse_acoustic_coefficient
            from robimb.extraction.parsers.flow_rate import parse_flow_rate
            from robimb.extraction.parsers.colors import parse_ral_colors
            from robimb.extraction.parsers.labeled_dimensions import parse_labeled_dimensions
            from robimb.extraction.matchers.materials import MaterialMatcher
            from robimb.extraction.matchers.brands import BrandMatcher

            _parse_thickness = parse_thickness
            _parse_dimensions = dimensions.parse_dimensions
            _parse_fire_class = parse_fire_class
            _parse_thermal_transmittance = parse_thermal_transmittance
            _parse_sound_insulation = parse_sound_insulation
            _parse_acoustic_coefficient = parse_acoustic_coefficient
            _parse_flow_rate = parse_flow_rate
            _parse_ral_colors = parse_ral_colors
            _parse_labeled_dimensions = parse_labeled_dimensions
            _MaterialMatcher = MaterialMatcher
            _BrandMatcher = BrandMatcher

            self._material_matcher = MaterialMatcher()
            self._brand_matcher = BrandMatcher()
            _robimb_parsers_loaded = True
            logger.info("Parser e matcher robimb caricati con successo")
        except Exception as exc:
            logger.warning("Impossibile caricare i parser robimb: %s", exc)
            _robimb_parsers_loaded = False

    def list_property_categories(self) -> list[dict[str, Any]]:
        """Ritorna l'elenco delle categorie e propriet�� definite nel registry roBERT."""
        try:
            from robimb.extraction.schema_registry import load_registry

            registry = load_registry(self.registry_path)
        except Exception as exc:  # pragma: no cover - robustezza
            logger.warning("Impossibile leggere il registry delle propriet��: %s", exc)
            return []

        categories: list[dict[str, Any]] = []
        for cat in registry.list():
            categories.append(
                {
                    "id": cat.id,
                    "name": cat.name,
                    "required": list(cat.required),
                    "properties": [
                        {
                            "id": spec.id,
                            "title": spec.title,
                            "type": spec.type,
                            "unit": spec.unit,
                            "enum": list(spec.enum) if spec.enum else None,
                        }
                        for spec in cat.properties
                    ],
                }
            )
        return categories

    def _category_from_entry(self, entry: dict[str, Any]) -> Optional[str]:
        super_id = self._resolve_supercategory(entry)
        if super_id:
            _, category_id = SUPER_CATEGORY_SCHEMA.get(super_id, (None, None))
            return category_id
        return None

    def _resolve_supercategory(self, entry: dict[str, Any]) -> Optional[int]:
        # Prova prima dal codice WBS (es. 11.x -> 11)
        wbs_code = entry.get("wbs6_code") or entry.get("wbs_code")
        if isinstance(wbs_code, str):
            match = re.match(r"(\d{1,3})", wbs_code.strip())
            if match:
                code = int(match.group(1))
                if code in SUPER_CATEGORY_SCHEMA:
                    return code

        # Fallback: cerca parole chiave nella descrizione WBS
        wbs_desc = entry.get("wbs6_description") or entry.get("wbs_description")
        if isinstance(wbs_desc, str):
            lowered = wbs_desc.lower()
            for keyword, code in SUPER_CATEGORY_BY_NAME.items():
                if keyword in lowered:
                    return code
        return None

    def extract_properties(self, entry: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Applica gli estrattori roBERT già preparati sui testi elenco prezzi."""
        if not self.orchestrator:
            return None

        description = entry.get("description") or entry.get("item_description") or ""
        if not description:
            return None

        super_id = self._resolve_supercategory(entry)
        primary_result: Optional[dict[str, Any]] = None

        if super_id:
            schema_file, category_id = SUPER_CATEGORY_SCHEMA.get(super_id, (None, None))
            if category_id:
                doc = {
                    "text_id": entry.get("product_id") or entry.get("code") or "item",
                    "category_id": category_id,
                    "text": description,
                    "wbs6_code": entry.get("wbs6_code") or entry.get("wbs_code"),
                    "wbs6_description": entry.get("wbs6_description") or entry.get("wbs_description"),
                }
                try:
                    result = self.orchestrator.extract_document(doc)
                except Exception as exc:  # pragma: no cover - robustezza
                    logger.exception("Errore durante l'estrazione proprietà roBERT: %s", exc)
                    result = None

                if result:
                    properties = result.get("properties") or {}
                    if properties:
                        primary_result = {
                            "schema_id": category_id,
                            "schema_file": schema_file,
                            "properties": properties,
                            "confidence_overall": result.get("confidence_overall", 0.0),
                            "validation": result.get("validation"),
                            "predicted_wbs": {
                                "category": result.get("categoria"),
                                "wbs6": None,
                                "wbs7": None,
                            },
                        }
                    predicted = result.get("predicted_wbs")
                    if predicted and primary_result:
                        primary_result["predicted_wbs"] = predicted

        fallback = self._extract_with_rules(description)
        if primary_result and fallback:
            merged = dict(primary_result)
            merged_props = dict(primary_result.get("properties") or {})
            for key, payload in (fallback.get("properties") or {}).items():
                merged_props.setdefault(key, payload)
            merged["properties"] = merged_props
            merged.setdefault("extras", {})["fallback_rules"] = True
            primary_result = merged

        final_result = primary_result or fallback

        # WBS prediction (roBERTino) se disponibile
        if final_result is not None and not entry.get("wbs6_code"):
            try:
                from app.services.wbs_predictor import predict_wbs

                wbs6_preds = predict_wbs(description, level=6, top_k=1)
                wbs7_preds = predict_wbs(description, level=7, top_k=1)
                predicted_wbs = {
                    "wbs6": wbs6_preds[0] if wbs6_preds else None,
                    "wbs7": wbs7_preds[0] if wbs7_preds else None,
                }
                extras = final_result.setdefault("extras", {})
                extras["predicted_wbs"] = predicted_wbs
            except Exception as exc:  # pragma: no cover - robustezza
                logger.warning("Predizione WBS fallita: %s", exc)

        return final_result

    def extract_properties_llm(
        self,
        entry: dict[str, Any],
        *,
        category_id: Optional[str] = None,
        property_filter: Optional[List[str]] = None,
    ) -> Optional[dict[str, Any]]:
        """Estrae propriet�� usando il pipeline LLM/Ollama."""
        if not self._llm_extractor:
            logger.debug("LLM extractor non disponibile - restituisco None")
            return None

        description = entry.get("description") or entry.get("item_description") or ""
        if not description:
            return None

        resolved_category = category_id or self._category_from_entry(entry)
        if not resolved_category:
            return None

        doc = {
            "text": description,
            "categoria": resolved_category,
            "text_id": entry.get("product_id") or entry.get("code") or "item",
            "wbs6_code": entry.get("wbs6_code") or entry.get("wbs_code"),
            "wbs6_description": entry.get("wbs6_description") or entry.get("wbs_description"),
        }
        try:
            result = self._llm_extractor.extract(doc, property_filter=property_filter)
            if property_filter:
                result.setdefault("extras", {})["property_filter"] = property_filter
            result.setdefault("strategy", "llm_ollama")
            return result
        except Exception as exc:  # pragma: no cover - robustezza
            logger.warning("LLM extraction failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Rule-based fallback extractor usando i parser di robimb
    # ------------------------------------------------------------------
    def _extract_with_rules(self, description: str) -> Optional[dict[str, Any]]:
        """Estrae proprietà usando i parser di robimb come fallback."""
        properties: Dict[str, Any] = {}

        # Usa i parser robimb se disponibili
        if _robimb_parsers_loaded:
            # Materiale via MaterialMatcher
            if self._material_matcher:
                matches = list(self._material_matcher.find(description))
                if matches:
                    best = max(matches, key=lambda m: m.score)
                    properties["materiale"] = {
                        "raw": best.surface,
                        "normalized": best.value,
                        "confidence": 0.65 * float(best.score),
                        "source": "matcher",
                    }

            # Spessore via parse_thickness
            if _parse_thickness:
                for match in _parse_thickness(description):
                    properties["spessore_mm"] = {
                        "raw": match.raw,
                        "normalized": match.value_mm,
                        "confidence": 0.85,
                        "unit": "mm",
                        "source": "parser",
                    }
                    break  # Prendi solo il primo

            # Dimensioni via parse_dimensions
            if _parse_dimensions:
                for match in _parse_dimensions(description):
                    values = list(match.values_mm)
                    if values:
                        if len(values) >= 2:
                            formatted = f"{int(values[0])}x{int(values[1])}"
                            if len(values) >= 3:
                                formatted += f"x{int(values[2])}"
                        else:
                            formatted = str(int(values[0]))
                        properties["dimensioni_mm"] = {
                            "raw": match.raw,
                            "normalized": formatted,
                            "confidence": 0.85,
                            "unit": "mm",
                            "source": "parser",
                        }
                        break

            # Classe resistenza al fuoco via parse_fire_class
            if _parse_fire_class:
                for match in _parse_fire_class(description):
                    properties["classe_resistenza_fuoco"] = {
                        "raw": match.raw,
                        "normalized": match.value,
                        "confidence": 0.85,
                        "source": "parser",
                    }
                    break

            # Trasmittanza termica
            if _parse_thermal_transmittance:
                for match in _parse_thermal_transmittance(description):
                    properties["trasmittanza_termica"] = {
                        "raw": match.raw,
                        "normalized": match.value,
                        "confidence": 0.88,
                        "unit": "W/m²K",
                        "source": "parser",
                    }
                    break

            # Isolamento acustico
            if _parse_sound_insulation:
                for match in _parse_sound_insulation(description):
                    properties["isolamento_acustico_db"] = {
                        "raw": match.raw,
                        "normalized": match.value,
                        "confidence": 0.85,
                        "unit": "dB",
                        "source": "parser",
                    }
                    break

            # Coefficiente fonoassorbimento
            if _parse_acoustic_coefficient:
                for match in _parse_acoustic_coefficient(description):
                    properties["coefficiente_fonoassorbimento"] = {
                        "raw": match.raw,
                        "normalized": match.value,
                        "confidence": 0.85,
                        "source": "parser",
                    }
                    break

            # Portata
            if _parse_flow_rate:
                for match in _parse_flow_rate(description):
                    properties["portata_l_min"] = {
                        "raw": match.raw,
                        "normalized": match.value,
                        "confidence": 0.88,
                        "unit": match.unit,
                        "source": "parser",
                    }
                    break

            # Colore RAL
            if _parse_ral_colors:
                for match in _parse_ral_colors(description):
                    properties["colore_ral"] = {
                        "raw": description[match.span[0]:match.span[1]],
                        "normalized": match.code,
                        "confidence": 0.85,
                        "source": "parser",
                    }
                    break

            # Marchio via BrandMatcher
            if self._brand_matcher:
                matches = list(self._brand_matcher.find(description))
                if matches:
                    brand, span, score = matches[0]
                    properties["marchio"] = {
                        "raw": description[span[0]:span[1]],
                        "normalized": brand,
                        "confidence": 0.70 * float(score),
                        "source": "matcher",
                    }

            # Peso (fallback regex)
            weight = self._detect_weight(description.lower())
            if weight:
                properties["peso"] = weight

            # Regole additive leggere anche quando robimb è disponibile
            self._maybe_add(properties, "finitura", self._detect_finish(description), 0.5)
            self._maybe_add(properties, "diametro_mm", self._detect_diameter(description), 0.55)
            self._maybe_add(properties, "classe_reazione_fuoco", self._detect_fire_rating(description), 0.6)
            self._maybe_add(properties, "grado_protezione_ip", self._detect_ip_grade(description), 0.55)
            self._maybe_add(properties, "grado_protezione_ik", self._detect_ik_grade(description), 0.5)
            self._maybe_add(properties, "trasmittanza_u_w_m2k", self._detect_u_value(description), 0.6)
            self._maybe_add(properties, "conduttivita_lambda_w_mk", self._detect_lambda(description), 0.58)
            self._maybe_add(properties, "isolamento_acustico_rw_db", self._detect_rw(description), 0.55)

        else:
            # Fallback basilare se robimb non è caricato
            text = description.lower()

            # Materiale basilare
            material_keywords = {
                "acciaio": ("acciaio", "inox", "aisi"),
                "calcestruzzo": ("calcestruzzo", "cls", "cemento"),
                "alluminio": ("alluminio", "allum."),
                "legno": ("legno", "abete", "lamellare", "pino"),
                "vetro": ("vetro", "stratificato"),
                "pvc": ("pvc",),
                "ghisa": ("ghisa",),
            }
            for material, tokens in material_keywords.items():
                if any(token in text for token in tokens):
                    properties["materiale"] = {
                        "raw": material,
                        "normalized": material,
                        "confidence": 0.5,
                    }
                    break

            # Spessore basilare
            match = re.search(r"spessore\s*([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m)?", text)
            if match:
                value = match.group(1)
                unit = match.group(2) or "mm"
                try:
                    num = float(value.replace(",", "."))
                    if unit.startswith("cm"):
                        num *= 10.0
                    elif unit == "m":
                        num *= 1000.0
                    properties["spessore_mm"] = {
                        "raw": match.group(0),
                        "normalized": round(num, 2),
                        "confidence": 0.5,
                        "unit": "mm",
                    }
                except ValueError:
                    pass

            # Peso
            weight = self._detect_weight(text)
            if weight:
                properties["peso"] = weight

            self._maybe_add(properties, "finitura", self._detect_finish(description), 0.45)
            self._maybe_add(properties, "diametro_mm", self._detect_diameter(description), 0.5)
            self._maybe_add(properties, "dimensioni_mm", self._detect_dimensions(description), 0.5)
            self._maybe_add(properties, "classe_reazione_fuoco", self._detect_fire_rating(description), 0.55)
            self._maybe_add(properties, "grado_protezione_ip", self._detect_ip_grade(description), 0.55)
            self._maybe_add(properties, "grado_protezione_ik", self._detect_ik_grade(description), 0.5)
            self._maybe_add(properties, "trasmittanza_u_w_m2k", self._detect_u_value(description), 0.55)
            self._maybe_add(properties, "conduttivita_lambda_w_mk", self._detect_lambda(description), 0.52)
            self._maybe_add(properties, "isolamento_acustico_rw_db", self._detect_rw(description), 0.5)

        if not properties:
            return None

        return {
            "schema_id": "rules",
            "schema_file": None,
            "properties": properties,
            "confidence_overall": 0.6 if _robimb_parsers_loaded else 0.35,
            "strategy": "robimb_parsers" if _robimb_parsers_loaded else "basic_rules",
        }

    # ------------------------------------------------------------------
    # Regole e parser leggeri aggiuntivi
    # ------------------------------------------------------------------
    def _maybe_add(
        self,
        properties: Dict[str, Any],
        key: str,
        value: Any,
        confidence: float | None = None,
    ) -> None:
        if value is None:
            return
        if isinstance(value, dict):
            properties.setdefault(key, value)
            return
        properties.setdefault(
            key,
            {
                "raw": value,
                "normalized": value,
                "confidence": confidence or 0.5,
            },
        )

    def _detect_finish(self, text: str) -> Optional[str]:
        lowered = text.lower()
        finish_tokens = (
            "zincato a caldo",
            "zincatura a caldo",
            "zincato",
            "verniciato",
            "verniciatura",
            "anodizzato",
            "satinato",
            "lucido",
            "grezzo",
            "brunito",
            "cromato",
            "verniciato a polveri",
        )
        for token in finish_tokens:
            if token in lowered:
                return token
        ral = re.search(r"ral\s*([0-9]{3,4})", lowered)
        if ral:
            return f"ral{ral.group(1)}"
        return None

    def _detect_diameter(self, text: str) -> Optional[float]:
        match = re.search(r"[øØ◊]?\s*([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m)\b", text.lower())
        if not match:
            return None
        value, unit = match.groups()
        try:
            num = float(value.replace(",", "."))
        except ValueError:
            return None
        unit = unit.lower()
        if unit.startswith("cm"):
            num *= 10.0
        elif unit == "m":
            num *= 1000.0
        return round(num, 2)

    def _detect_dimensions(self, text: str) -> Optional[str]:
        # 120x60 cm, 30x30, 2.5x1 m, oppure 1200x600x50
        lowered = text.lower()
        triple = re.search(
            r"([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m)?\s*[x×*]\s*([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m)?\s*[x×*]\s*([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m)?",
            lowered,
        )
        if triple:
            a, unit_a, b, unit_b, c, unit_c = triple.groups()
            try:
                nums = [float(a.replace(",", ".")), float(b.replace(",", ".")), float(c.replace(",", "."))]
            except ValueError:
                return None
            unit = unit_a or unit_b or unit_c or "mm"
            factor = 1.0
            if unit.startswith("cm"):
                factor = 10.0
            elif unit == "m":
                factor = 1000.0
            vals = [round(n * factor) for n in nums]
            return f"{vals[0]}x{vals[1]}x{vals[2]}"
        match = re.search(
            r"([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m)?\s*[x×*]\s*([0-9]+(?:[.,][0-9]+)?)\s*(mm|cm|m)?",
            lowered,
        )
        if not match:
            return None
        a, unit_a, b, unit_b = match.groups()
        unit = unit_a or unit_b or "mm"
        try:
            a_num = float(a.replace(",", "."))
            b_num = float(b.replace(",", "."))
        except ValueError:
            return None
        factor = 1.0
        if unit.startswith("cm"):
            factor = 10.0
        elif unit == "m":
            factor = 1000.0
        return f"{round(a_num * factor)}x{round(b_num * factor)}"

    def _detect_fire_rating(self, text: str) -> Optional[str]:
        match = re.search(r"\b(REI?\s*[0-9]{2,3}|EI\s*[0-9]{2,3})\b", text.upper())
        if match:
            return re.sub(r"\s+", "", match.group(1))
        return None

    def _detect_ip_grade(self, text: str) -> Optional[str]:
        match = re.search(r"\bIP\s*([0-9]{2})\b", text.upper())
        if match:
            return f"IP{match.group(1)}"
        return None

    def _detect_ik_grade(self, text: str) -> Optional[str]:
        match = re.search(r"\bIK\s*([0-9]{2})\b", text.upper())
        if match:
            return f"IK{match.group(1)}"
        return None

    def _detect_u_value(self, text: str) -> Optional[float]:
        match = re.search(r"\bU\s*=?\s*([0-9]+(?:[.,][0-9]+)?)\s*(W/M2K|W/M²K)?", text.upper())
        if not match:
            return None
        try:
            return round(float(match.group(1).replace(",", ".")), 3)
        except ValueError:
            return None

    def _detect_lambda(self, text: str) -> Optional[float]:
        match = re.search(r"[λL]\s*=?\s*([0-9]+(?:[.,][0-9]+)?)\s*(W/MK)?", text.upper())
        if not match:
            return None
        try:
            return round(float(match.group(1).replace(",", ".")), 3)
        except ValueError:
            return None

    def _detect_rw(self, text: str) -> Optional[float]:
        match = re.search(r"\bRW\s*=?\s*([0-9]+(?:[.,][0-9]+)?)\s*D?B\b", text.upper())
        if not match:
            return None
        try:
            return float(match.group(1).replace(",", "."))
        except ValueError:
            return None

    def _detect_weight(self, text: str) -> Optional[dict[str, Any]]:
        """Estrae peso da testo (kg/mq o kg/m)."""
        match_mq = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*kg\s*/\s*m[q²2]", text)
        if match_mq:
            value = float(match_mq.group(1).replace(",", "."))
            return {
                "raw": f"{value} kg/mq",
                "normalized": value,
                "unit": "kg/mq",
                "confidence": 0.6,
            }
        match_ml = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*kg\s*/\s*m", text)
        if match_ml:
            value = float(match_ml.group(1).replace(",", "."))
            return {
                "raw": f"{value} kg/m",
                "normalized": value,
                "unit": "kg/m",
                "confidence": 0.55,
            }
        return None


property_extractor_service = PropertyExtractor()

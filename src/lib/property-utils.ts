import type { PropertyExtractionResult } from "@/types/api";

type UnknownRecord = Record<string, unknown>;

const isRecord = (value: unknown): value is UnknownRecord =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const toStringSafe = (value: unknown): string | null =>
  typeof value === "string" && value.trim().length > 0 ? value : null;

const toNumberSafe = (value: unknown): number | null => {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

/**
 * Normalize raw property extraction payloads (LLM/rules) into the UI-friendly shape.
 */
export function normalizeExtractedProperties(raw: unknown): PropertyExtractionResult | null {
  if (!isRecord(raw)) {
    return null;
  }

  const resultObj = isRecord(raw.result) ? raw.result : null;
  const dataObj = isRecord(raw.data) ? raw.data : null;

  const propsCandidate = raw.properties ?? resultObj?.properties ?? dataObj?.properties;
  if (!isRecord(propsCandidate)) {
    return null;
  }

  const categoryId =
    toStringSafe(raw.category_id) ||
    toStringSafe(raw.schema_id) ||
    toStringSafe(raw.category) ||
    toStringSafe(raw.categoria) ||
    "sconosciuta";

  const missingRaw = raw.missing_required ?? resultObj?.missing_required ?? dataObj?.missing_required;
  const missing_required: string[] = Array.isArray(missingRaw)
    ? (missingRaw.filter((item) => typeof item === "string") as string[])
    : [];

  return {
    category_id: categoryId,
    properties: propsCandidate,
    missing_required,
  };
}

/**
 * Helper to read pre-calculated properties stored inside item.extra_metadata.
 */
export function getItemExtractedProperties(
  item: { extra_metadata?: Record<string, unknown> | null } | null | undefined,
): PropertyExtractionResult | null {
  if (!item?.extra_metadata || !isRecord(item.extra_metadata)) {
    return null;
  }
  const raw =
    item.extra_metadata.extracted_properties ??
    item.extra_metadata.properties ??
    item.extra_metadata;
  return normalizeExtractedProperties(raw);
}

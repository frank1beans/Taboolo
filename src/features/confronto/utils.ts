import { ImpresaView, OffertaRecord } from "./types";

/**
 * Utility functions per il confronto offerte
 */

export const slugifyFieldId = (value: string): string =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .toLowerCase() || "impresa";

export const getImpresaFieldPrefix = (impresa: ImpresaView): string => {
  // Usa solo il nomeImpresa che già include il round se presente (es. "CEV (Round 1)")
  // Non aggiungere manualmente il round number per evitare duplicazioni
  const base = impresa.nomeImpresa || `impresa_${impresa.roundNumber ?? "unknown"}`;
  return slugifyFieldId(base);
};

export const getImpresaHeaderLabel = (impresa: ImpresaView): string => {
  if (impresa.roundNumber != null) {
    const roundLabel = impresa.roundLabel ?? `Round ${impresa.roundNumber}`;
    return `${impresa.nomeImpresa} - ${roundLabel}`;
  }
  return impresa.nomeImpresa;
};

export const resolveOfferta = (
  impresa: ImpresaView,
  offerteByLabel: Record<string, OffertaRecord>,
  normalizedOffers: Map<string, OffertaRecord>
): OffertaRecord | null => {
  const candidates = new Set<string>();

  const addBaseLabel = (base?: string | null) => {
    if (!base) return;
    const trimmed = base.trim();
    if (!trimmed) return;
    candidates.add(trimmed);
    if (impresa.roundNumber != null) {
      candidates.add(`${trimmed} (Round ${impresa.roundNumber})`);
      candidates.add(`${trimmed} Round ${impresa.roundNumber}`);
      candidates.add(`${trimmed} - Round ${impresa.roundNumber}`);
    }
    if (impresa.roundLabel) {
      candidates.add(`${trimmed} (${impresa.roundLabel})`);
      candidates.add(`${trimmed} - ${impresa.roundLabel}`);
    }
  };

  addBaseLabel(impresa.nomeImpresa);
  addBaseLabel(impresa.impresaOriginale);
  addBaseLabel(impresa.normalizedLabel);

  const normalizedCandidates = Array.from(candidates)
    .map((candidate) => candidate.toLowerCase())
    .filter((candidate) => candidate.length > 0);

  for (const candidate of normalizedCandidates) {
    const match = normalizedOffers.get(candidate);
    if (match) return match;
  }

  for (const [label, offerta] of Object.entries(offerteByLabel)) {
    const normalizedLabel = label.trim().toLowerCase();
    if (
      normalizedCandidates.some(
        (candidate) =>
          normalizedLabel.includes(candidate) || candidate.includes(normalizedLabel)
      )
    ) {
      return offerta;
    }
  }

  return null;
};

export const COLOR_PALETTE = [
  { bg: { light: "#f0f9ff", dark: "#0c4a6e" }, border: { light: "#bae6fd", dark: "#0ea5e9" } }, // Sky
  { bg: { light: "#fffbeb", dark: "#451a03" }, border: { light: "#fde68a", dark: "#d97706" } }, // Amber
  { bg: { light: "#f0fdf4", dark: "#14532d" }, border: { light: "#bbf7d0", dark: "#22c55e" } }, // Green
  { bg: { light: "#faf5ff", dark: "#581c87" }, border: { light: "#e9d5ff", dark: "#a855f7" } }, // Purple
  { bg: { light: "#f8fafc", dark: "#1e293b" }, border: { light: "#e2e8f0", dark: "#64748b" } }, // Slate
];

export const getColorForIndex = (index: number, isDarkMode: boolean) => {
  const colorSet = COLOR_PALETTE[index % COLOR_PALETTE.length];
  return {
    bg: isDarkMode ? colorSet.bg.dark : colorSet.bg.light,
    border: isDarkMode ? colorSet.border.dark : colorSet.border.light,
  };
};

export const clamp = (v: number, min: number, max: number) => Math.max(min, Math.min(max, v));

export const getDeltaVisual = (val: number | null | undefined) => {
  if (val == null) {
    return { text: "–", bg: undefined, color: undefined, icon: "" };
  }
  const abs = clamp(Math.abs(val), 0, 100);
  const opacity = 0.12 + abs / 900; // più visibile
  // Riferimento: progetto. Più alto = peggio (rosso), più basso = meglio (verde).
  const isGood = val < 0;
  const bg = isGood
    ? `rgba(34,197,94,${opacity})`
    : val > 0
      ? `rgba(239,68,68,${opacity})`
      : `rgba(148,163,184,0.2)`;
  const color = isGood ? "#166534" : val > 0 ? "#b91c1c" : "#475569";
  const icon = isGood ? "↓" : val > 0 ? "↑" : "•";
  const text = `${val > 0 ? "+" : ""}${val.toFixed(2)}%`;
  return { text, bg, color, icon };
};

export const getHeatmapBg = (delta: number | null | undefined, baseBg: string) => {
  if (delta == null) return baseBg;
  const abs = clamp(Math.abs(delta), 0, 80);
  const tint = 0.1 + abs / 500; // intensità leggermente più alta
  return delta > 0
    ? `rgba(239,68,68,${tint})`
    : delta < 0
      ? `rgba(34,197,94,${tint})`
      : baseBg;
};

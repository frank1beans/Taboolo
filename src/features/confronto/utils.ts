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
  { bg: { light: "#dbeafe", dark: "#1e3a5f" }, border: { light: "#60a5fa", dark: "#3b82f6" } },
  { bg: { light: "#fef3c7", dark: "#451a03" }, border: { light: "#fbbf24", dark: "#f59e0b" } },
  { bg: { light: "#dcfce7", dark: "#14532d" }, border: { light: "#4ade80", dark: "#10b981" } },
  { bg: { light: "#f3e8ff", dark: "#4c1d95" }, border: { light: "#c084fc", dark: "#a855f7" } },
  { bg: { light: "#f1f5f9", dark: "#1e293b" }, border: { light: "#94a3b8", dark: "#64748b" } },
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

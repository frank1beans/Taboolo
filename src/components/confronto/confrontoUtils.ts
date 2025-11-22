/**
 * Utility functions per il confronto offerte
 */

export interface ImpresaView {
  nomeImpresa: string;
  roundNumber: number | null;
  roundLabel: string | null;
  impresaOriginale: string | null;
  normalizedLabel: string | null;
}

export interface OffertaRecord {
  quantita?: number;
  prezzoUnitario?: number;
  importoTotale?: number;
  criticita?: string;
  note?: string;
}

export interface ConfrontoRow {
  id: string;
  codice: string;
  descrizione: string;
  descrizione_estesa?: string | null;
  um: string;
  quantita: number;
  prezzoUnitarioProgetto: number;
  importoTotaleProgetto: number;
  wbs6Code?: string | null;
  wbs6Description?: string | null;
  wbs7Code?: string | null;
  wbs7Description?: string | null;
  mediaPrezzi?: number | null;
  minimoPrezzi?: number | null;
  massimoPrezzi?: number | null;
  deviazionePrezzi?: number | null;
  [key: string]: any;
}

export const slugifyFieldId = (value: string): string =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .toLowerCase() || "impresa";

export const getImpresaFieldPrefix = (impresa: ImpresaView): string => {
  const base =
    impresa.roundNumber != null
      ? `${impresa.nomeImpresa}_round_${impresa.roundNumber}`
      : impresa.nomeImpresa;
  return slugifyFieldId(base ?? `impresa_${impresa.roundNumber ?? "all"}`);
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

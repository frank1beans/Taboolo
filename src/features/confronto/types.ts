export interface ImpresaView {
    nomeImpresa: string;
    roundNumber: number | null;
    roundLabel: string | null;
    impresaOriginale: string | null;
    normalizedLabel: string | null;
    colore?: string;
}

export interface OffertaRecord {
    quantita?: number;
    prezzoUnitario?: number;
    importoTotale?: number;
    deltaQuantita?: number | null;
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
    hasQuantityMismatch?: boolean;
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

export interface VoceConfronto {
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
    offerte: Record<string, OffertaRecord>;
}

export interface ConfrontoData {
    voci: VoceConfronto[];
    imprese: ImpresaView[];
    rounds: Array<{
        numero: number;
        label: string;
        imprese: string[];
        impreseCount: number;
    }>;
}

export interface ConfrontoOfferteProps {
    commessaId: string;
    selectedRound?: number | "all";
    selectedImpresa?: string;
    onRoundChange?: (round: number | "all") => void;
    onImpresaChange?: (impresa: string | undefined) => void;
    onNavigateToCharts?: () => void;
}

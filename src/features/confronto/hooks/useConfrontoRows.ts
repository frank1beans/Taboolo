/**
 * Hook per generare le righe del confronto offerte
 */

import { useMemo } from "react";
import {
  getImpresaFieldPrefix,
  resolveOfferta,
} from "../utils";
import {
  ConfrontoRow,
  ImpresaView,
  OffertaRecord,
} from "../types";

interface ConfrontoVoce {
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
  offerte?: Record<string, OffertaRecord>;
}

interface UseConfrontoRowsOptions {
  voci: ConfrontoVoce[] | undefined;
  filteredImprese: ImpresaView[];
}

export function useConfrontoRows({ voci, filteredImprese }: UseConfrontoRowsOptions): ConfrontoRow[] {
  return useMemo<ConfrontoRow[]>(() => {
    if (!voci) return [];

    return voci.map((voce, index) => {
      const offerteByLabel: Record<string, OffertaRecord> = voce.offerte ?? {};
      const normalizedOffers = new Map<string, OffertaRecord>();
      Object.entries(offerteByLabel).forEach(([label, offerta]) => {
        normalizedOffers.set(label.trim().toLowerCase(), offerta);
      });

      const row: ConfrontoRow = {
        id: `${voce.codice}-${index}`,
        codice: voce.codice,
        descrizione: voce.descrizione,
        descrizione_estesa: voce.descrizione_estesa,
        um: voce.um,
        quantita: voce.quantita,
        prezzoUnitarioProgetto: voce.prezzoUnitarioProgetto,
        importoTotaleProgetto: voce.importoTotaleProgetto,
        wbs6Code: voce.wbs6Code,
        wbs6Description: voce.wbs6Description,
        wbs7Code: voce.wbs7Code,
        wbs7Description: voce.wbs7Description,
      };

      const prezziVisibili: number[] = [];
      const offerCache = new Map<string, OffertaRecord | null>();

      // Process each impresa
      filteredImprese.forEach((impresa) => {
        const fieldPrefix = getImpresaFieldPrefix(impresa);
        const offerta = resolveOfferta(impresa, offerteByLabel, normalizedOffers);
        offerCache.set(fieldPrefix, offerta);

        if (offerta && typeof offerta.prezzoUnitario === "number") {
          row[`${fieldPrefix}_prezzoUnitario`] = offerta.prezzoUnitario;
          prezziVisibili.push(offerta.prezzoUnitario);
        } else {
          row[`${fieldPrefix}_prezzoUnitario`] = null;
        }

        row[`${fieldPrefix}_importoTotale`] =
          offerta && typeof offerta.importoTotale === "number" ? offerta.importoTotale : null;

        if (offerta && offerta.prezzoUnitario != null && voce.prezzoUnitarioProgetto) {
          row[`${fieldPrefix}_deltaPerc`] =
            ((offerta.prezzoUnitario - voce.prezzoUnitarioProgetto) /
              voce.prezzoUnitarioProgetto) *
            100;
        } else {
          row[`${fieldPrefix}_deltaPerc`] = null;
        }
      });

      // Calculate statistics
      if (prezziVisibili.length) {
        const somma = prezziVisibili.reduce((acc, curr) => acc + curr, 0);
        const media = somma / prezziVisibili.length;
        const minimo = Math.min(...prezziVisibili);
        const massimo = Math.max(...prezziVisibili);
        const deviazione =
          prezziVisibili.length > 1
            ? Math.sqrt(
              prezziVisibili.reduce((acc, curr) => acc + Math.pow(curr - media, 2), 0) /
              prezziVisibili.length
            )
            : 0;

        row.mediaPrezzi = media;
        row.minimoPrezzi = minimo;
        row.massimoPrezzi = massimo;
        row.deviazionePrezzi = deviazione;

        // Calculate delta from media for each impresa
        filteredImprese.forEach((impresa) => {
          const fieldPrefix = getImpresaFieldPrefix(impresa);
          const offerta = offerCache.get(fieldPrefix);
          if (!offerta || offerta.prezzoUnitario == null || Math.abs(media) < 1e-9) {
            row[`${fieldPrefix}_deltaMedia`] = null;
            return;
          }
          row[`${fieldPrefix}_deltaMedia`] = ((offerta.prezzoUnitario - media) / media) * 100;
        });
      } else {
        row.mediaPrezzi = null;
        row.minimoPrezzi = null;
        row.massimoPrezzi = null;
        row.deviazionePrezzi = null;
        filteredImprese.forEach((impresa) => {
          const fieldPrefix = getImpresaFieldPrefix(impresa);
          row[`${fieldPrefix}_deltaMedia`] = null;
        });
      }

      return row;
    });
  }, [voci, filteredImprese]);
}

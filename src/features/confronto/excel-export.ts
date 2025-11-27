import { ExcelJSColumnConfig, exportToExcelJS } from "@/lib/grid-utils";
import { ConfrontoRow, ImpresaView } from "./types";
import { getImpresaFieldPrefix } from "./utils";

export async function exportConfrontoToExcel(
    filteredRowData: ConfrontoRow[],
    filteredImprese: ImpresaView[],
    commessaId: string
) {
    if (!filteredRowData.length) return;

    const toNumber = (v: any) => {
        if (v === null || v === undefined || v === "") return null;
        const num = typeof v === "number" ? v : Number(v);
        return Number.isFinite(num) ? num : null;
    };

    const colLetter = (index: number) => {
        let n = index + 1;
        let s = "";
        while (n > 0) {
            const r = (n - 1) % 26;
            s = String.fromCharCode(65 + r) + s;
            n = Math.floor((n - 1) / 26);
        }
        return s;
    };

    // Palette colori per Excel header - usiamo colori più visibili e consistenti con ag-grid
    const excelHeaderPalette = [
        { argb: "FFE0E7FF" }, // Indigo chiaro
        { argb: "FFFEF3C7" }, // Amber chiaro
        { argb: "FFD1FAE5" }, // Green chiaro
        { argb: "FFF3E8FF" }, // Purple chiaro
        { argb: "FFFFE4E6" }, // Rose chiaro
        { argb: "FFCFFAFE" }, // Cyan chiaro
        { argb: "FFF1F5F9" }, // Slate chiaro
    ];

    const columns: ExcelJSColumnConfig[] = [
        { header: "Codice", field: "codice", width: 16 },
        {
            header: "Descrizione",
            field: "descrizione",
            width: 80,
            style: {
                alignment: { wrapText: true, vertical: "top" }
            }
        },
        { header: "UM", field: "um", width: 8 },
        { header: "Q.tà progetto", field: "quantita", width: 12, style: { numFmt: "#,##0.00" } },
        { header: "P.U. Progetto", field: "prezzoUnitarioProgetto", width: 14, style: { numFmt: "€ #,##0.00" } },
        { header: "Importo Progetto", field: "importoTotaleProgetto", width: 16, style: { numFmt: "€ #,##0.00" } },
        { header: "Media offerte", field: "mediaPrezzi", width: 14, style: { numFmt: "€ #,##0.00" } },
        { header: "Prezzo minimo", field: "minimoPrezzi", width: 14, style: { numFmt: "€ #,##0.00" } },
        { header: "Prezzo massimo", field: "massimoPrezzi", width: 14, style: { numFmt: "€ #,##0.00" } },
        { header: "Deviazione std.", field: "deviazionePrezzi", width: 14, style: { numFmt: "€ #,##0.00" } },
    ];

    const deltaColumns: number[] = [];
    const deltaMediaColumns: number[] = [];
    const priceColumns: number[] = [];
    const importoColumns: number[] = [];
    const deltaQtyColumns: number[] = [];

    const colLetterFromField = (field: string) => {
        const idx = columns.findIndex((c) => c.field === field);
        return colLetter(idx);
    };

    // Colonne di riferimento progetto (fisse nella parte iniziale della tabella)
    const qtyProjColLetter = colLetterFromField("quantita"); // Q.tà progetto
    const puProjColLetter = colLetterFromField("prezzoUnitarioProgetto"); // P.U. Progetto
    const importoProjColLetter = colLetterFromField("importoTotaleProgetto"); // Importo Progetto
    const mediaColLetter = colLetterFromField("mediaPrezzi"); // Media offerte

    filteredImprese.forEach((impresa, idx) => {
        const prefix = getImpresaFieldPrefix(impresa);
        const puKey = `${prefix}_prezzoUnitario`;
        const deltaKey = `${prefix}_deltaPerc`;
        const importoKey = `${prefix}_importoTotale`;
        const qtyKey = `${prefix}_quantita`;
        const deltaQtyKey = `${prefix}_deltaQuantita`;
        const deltaMediaKey = `${prefix}_deltaMedia`;

        // Colore header per questa impresa
        const headerColor = excelHeaderPalette[idx % excelHeaderPalette.length];

        const qtyColumnIndex = columns.length;
        const deltaQtyColumnIndex = columns.length + 1;
        const puColumnIndex = columns.length + 2;
        const importoColumnIndex = columns.length + 3;
        const deltaColumnIndex = columns.length + 4;
        const deltaMediaIndex = columns.length + 5;

        columns.push(
            {
                header: `${impresa.nomeImpresa} Q.tà`,
                field: qtyKey,
                width: 12,
                style: { numFmt: "#,##0.00" },
                headerStyle: {
                    fill: { type: "pattern", pattern: "solid", fgColor: headerColor },
                    font: { bold: true, color: { argb: "FF0F172A" } },
                },
            },
            {
                header: `${impresa.nomeImpresa} Δ Q.tà`,
                field: deltaQtyKey,
                width: 12,
                style: { numFmt: "#,##0.00" },
                headerStyle: {
                    fill: { type: "pattern", pattern: "solid", fgColor: headerColor },
                    font: { bold: true, color: { argb: "FF0F172A" } },
                },
            },
            {
                header: `${impresa.nomeImpresa} P.U.`,
                field: puKey,
                width: 14,
                style: { numFmt: "€ #,##0.00" },
                headerStyle: {
                    fill: { type: "pattern", pattern: "solid", fgColor: headerColor },
                    font: { bold: true, color: { argb: "FF0F172A" } },
                },
                cellStyle: (row: any) => {
                    const puVal = toNumber(row[puKey]);
                    const puProgetto = toNumber(row.prezzoUnitarioProgetto);

                    // Trova il minimo e massimo prezzo tra tutte le imprese per questa riga
                    let minPrice = Number.POSITIVE_INFINITY;
                    let maxPrice = Number.NEGATIVE_INFINITY;
                    filteredImprese.forEach((imp) => {
                        const impPrefix = getImpresaFieldPrefix(imp);
                        const impPu = toNumber(row[`${impPrefix}_prezzoUnitario`]);
                        if (impPu !== null) {
                            minPrice = Math.min(minPrice, impPu);
                            maxPrice = Math.max(maxPrice, impPu);
                        }
                    });

                    const isBest = puVal !== null && puVal === minPrice && minPrice !== Number.POSITIVE_INFINITY;
                    const isWorst = puVal !== null && puVal === maxPrice && maxPrice !== Number.NEGATIVE_INFINITY;

                    if (puVal === null) return null;

                    const style: any = {
                        numFmt: "€ #,##0.00"
                    };

                    // Sfondo verde se sotto il prezzo progetto, rosso se sopra
                    if (puProgetto !== null) {
                        if (puVal < puProgetto) {
                            style.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFD1FAE5" } };
                        } else if (puVal > puProgetto) {
                            style.fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFFECACA" } };
                        }
                    }

                    // Bordo per migliore/peggiore
                    if (isBest) {
                        style.border = {
                            top: { style: "medium", color: { argb: "FF22C55E" } },
                            bottom: { style: "medium", color: { argb: "FF22C55E" } },
                            left: { style: "medium", color: { argb: "FF22C55E" } },
                            right: { style: "medium", color: { argb: "FF22C55E" } },
                        };
                    } else if (isWorst) {
                        style.border = {
                            top: { style: "medium", color: { argb: "FFEF4444" } },
                            bottom: { style: "medium", color: { argb: "FFEF4444" } },
                            left: { style: "medium", color: { argb: "FFEF4444" } },
                            right: { style: "medium", color: { argb: "FFEF4444" } },
                        };
                    }

                    return style;
                },
            },
            {
                header: `${impresa.nomeImpresa} Importo`,
                field: importoKey,
                width: 16,
                style: { numFmt: "€ #,##0.00" },
                headerStyle: {
                    fill: { type: "pattern", pattern: "solid", fgColor: headerColor },
                    font: { bold: true, color: { argb: "FF0F172A" } },
                },
                cellStyle: (row: any) => {
                    const importoVal = toNumber(row[importoKey]);
                    const importoProgetto = toNumber(row.importoTotaleProgetto);
                    if (importoVal === null || importoProgetto === null) return null;

                    // Verde se sotto l'importo progetto (migliore)
                    if (importoVal < importoProgetto) {
                        return {
                            fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFD1FAE5" } },
                        };
                    }
                    // Rosso se sopra l'importo progetto (peggiore)
                    if (importoVal > importoProgetto) {
                        return {
                            fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFFECACA" } },
                        };
                    }
                    return null;
                },
            },
            {
                header: `${impresa.nomeImpresa} Δ progetto`,
                field: deltaKey,
                width: 14,
                style: { numFmt: "0.00%" },
                headerStyle: {
                    fill: { type: "pattern", pattern: "solid", fgColor: headerColor },
                    font: { bold: true, color: { argb: "FF0F172A" } },
                },
            },
            {
                header: `${impresa.nomeImpresa} Δ media`,
                field: deltaMediaKey,
                width: 14,
                style: { numFmt: "0.00%" },
                headerStyle: {
                    fill: { type: "pattern", pattern: "solid", fgColor: headerColor },
                    font: { bold: true, color: { argb: "FF0F172A" } },
                },
            },
        );

        deltaColumns.push(deltaColumnIndex);
        deltaMediaColumns.push(deltaMediaIndex);
        priceColumns.push(puColumnIndex);
        importoColumns.push(importoColumnIndex);
        deltaQtyColumns.push(deltaQtyColumnIndex);
    });

    const mediaIdx = columns.findIndex((c) => c.field === "mediaPrezzi");

    const data = filteredRowData.map((row, rowIdx) => {
        const excelRow = rowIdx + 2; // header is row 1

        // Usa descrizione_estesa se disponibile, altrimenti descrizione
        // Preserva i caratteri di a capo nel testo
        const descrizioneCompleta = row.descrizione_estesa || row.descrizione || "";

        const base: Record<string, any> = {
            codice: row.codice,
            descrizione: descrizioneCompleta,
            um: row.um,
            quantita: toNumber(row.quantita),
            prezzoUnitarioProgetto: toNumber(row.prezzoUnitarioProgetto),
            importoTotaleProgetto: { formula: `D${excelRow}*E${excelRow}` },
        };

        // Per-impresa
        filteredImprese.forEach((impresa) => {
            const prefix = getImpresaFieldPrefix(impresa);
            const puCol = columns.findIndex((c) => c.field === `${prefix}_prezzoUnitario`);
            const deltaCol = columns.findIndex((c) => c.field === `${prefix}_deltaPerc`);
            const importoCol = columns.findIndex((c) => c.field === `${prefix}_importoTotale`);
            const deltaMediaCol = columns.findIndex((c) => c.field === `${prefix}_deltaMedia`);
            const qtyCol = columns.findIndex((c) => c.field === `${prefix}_quantita`);
            const deltaQtyCol = columns.findIndex((c) => c.field === `${prefix}_deltaQuantita`);

            const puVal = toNumber(row[`${prefix}_prezzoUnitario`]);
            const qtyVal = toNumber(row[`${prefix}_quantita`]);

            const puRef = colLetter(puCol) + excelRow;
            const qtyRef = colLetter(qtyCol) + excelRow;
            const mediaRef = mediaIdx >= 0 ? colLetter(mediaIdx) + excelRow : null;

            base[`${prefix}_prezzoUnitario`] = puVal;
            base[`${prefix}_deltaPerc`] =
                puVal !== null ? { formula: `(${puRef}-E${excelRow})/E${excelRow}` } : null;
            base[`${prefix}_importoTotale`] =
                puVal !== null || qtyVal !== null
                    ? { formula: `${qtyRef}*${puRef}` }
                    : toNumber(row[`${prefix}_importoTotale`]);
            base[`${prefix}_deltaMedia`] =
                mediaRef && puVal !== null ? { formula: `(${puRef}-${mediaRef})/${mediaRef}` } : null;
            base[`${prefix}_quantita`] = qtyVal;
            base[`${prefix}_deltaQuantita`] =
                qtyVal !== null ? { formula: `${qtyRef}-D${excelRow}` } : null;
        });

        // Aggregati riga su tutte le imprese (media/min/max/dev) calcolati come formule
        // IMPORTANTE: Raccogliamo i riferimenti ai P.U. (prezzi unitari) di ogni impresa
        const puRefs: string[] = [];
        filteredImprese.forEach((impresa) => {
            const prefix = getImpresaFieldPrefix(impresa);
            const puColIdx = columns.findIndex((c) => c.field === `${prefix}_prezzoUnitario`);
            if (puColIdx >= 0) {
                const colRef = `${colLetter(puColIdx)}${excelRow}`;
                puRefs.push(colRef);
            }
        });

        if (puRefs.length > 0) {
            const avgFormula = `AVERAGE(${puRefs.join(",")})`;
            base.mediaPrezzi = { formula: avgFormula };
            base.minimoPrezzi = { formula: `MIN(${puRefs.join(",")})` };
            base.massimoPrezzi = { formula: `MAX(${puRefs.join(",")})` };
            // IMPORTANTE: ExcelJS richiede nomi di funzioni INGLESI, Excel li convertirà automaticamente
            base.deviazionePrezzi = { formula: `STDEV.P(${puRefs.join(",")})` };
        } else {
            base.mediaPrezzi = toNumber(row.mediaPrezzi);
            base.minimoPrezzi = toNumber(row.minimoPrezzi);
            base.massimoPrezzi = toNumber(row.massimoPrezzi);
            base.deviazionePrezzi = toNumber(row.deviazionePrezzi);
        }

        return base;
    });

    const conditionalFormatting: any[] = [];

    // Per ogni impresa, applica formattazioni condizionali che confrontano con il progetto/media
    filteredImprese.forEach((impresa, impresaIdx) => {
        const prefix = getImpresaFieldPrefix(impresa);
        const puColIdx = columns.findIndex((c) => c.field === `${prefix}_prezzoUnitario`);
        const deltaColIdx = columns.findIndex((c) => c.field === `${prefix}_deltaPerc`);
        const importoColIdx = columns.findIndex((c) => c.field === `${prefix}_importoTotale`);
        const deltaMediaColIdx = columns.findIndex((c) => c.field === `${prefix}_deltaMedia`);
        const deltaQtyColIdx = columns.findIndex((c) => c.field === `${prefix}_deltaQuantita`);

        // Prezzo Unitario: confronta con prezzo progetto della stessa riga (colonna E)
        if (puColIdx >= 0) {
            const puCol = colLetter(puColIdx);
            const range = `${puCol}2:${puCol}${data.length + 1}`;
            // Verde se minore del progetto (meglio)
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "expression",
                    formula: `${puCol}2<E2`,
                    style: {
                        fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFD1FAE5" } },
                    }
                }],
            });
            // Rosso se maggiore del progetto (peggio)
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "expression",
                    formula: `${puCol}2>E2`,
                    style: {
                        fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFFECACA" } },
                    }
                }],
            });
        }

        // Delta progetto: verde <0, rosso >0
        if (deltaColIdx >= 0) {
            const deltaCol = colLetter(deltaColIdx);
            const range = `${deltaCol}2:${deltaCol}${data.length + 1}`;
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "cellIs",
                    operator: "lessThan",
                    value: 0,
                    style: {
                        font: { color: { argb: "FF16A34A" }, bold: true }
                    }
                }],
            });
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "cellIs",
                    operator: "greaterThan",
                    value: 0,
                    style: {
                        font: { color: { argb: "FFDC2626" }, bold: true }
                    }
                }],
            });
        }

        // Importo: confronta con importo progetto della stessa riga (colonna F)
        if (importoColIdx >= 0) {
            const importoCol = colLetter(importoColIdx);
            const range = `${importoCol}2:${importoCol}${data.length + 1}`;
            // Verde se minore del progetto
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "expression",
                    formula: `${importoCol}2<F2`,
                    style: {
                        fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFD1FAE5" } },
                    }
                }],
            });
            // Rosso se maggiore del progetto
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "expression",
                    formula: `${importoCol}2>F2`,
                    style: {
                        fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFFECACA" } },
                    }
                }],
            });
        }

        // Delta media: verde <0, rosso >0
        if (deltaMediaColIdx >= 0) {
            const deltaMediaCol = colLetter(deltaMediaColIdx);
            const range = `${deltaMediaCol}2:${deltaMediaCol}${data.length + 1}`;
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "cellIs",
                    operator: "lessThan",
                    value: 0,
                    style: {
                        font: { color: { argb: "FF16A34A" }, bold: true }
                    }
                }],
            });
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "cellIs",
                    operator: "greaterThan",
                    value: 0,
                    style: {
                        font: { color: { argb: "FFDC2626" }, bold: true }
                    }
                }],
            });
        }

        // Delta quantità: evidenzia se diverso da zero
        if (deltaQtyColIdx >= 0) {
            const deltaQtyCol = colLetter(deltaQtyColIdx);
            const range = `${deltaQtyCol}2:${deltaQtyCol}${data.length + 1}`;
            conditionalFormatting.push({
                range,
                rules: [{
                    type: "expression",
                    formula: `${deltaQtyCol}2<>0`,
                    style: {
                        fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFFFF3CD" } },
                        font: { bold: true, color: { argb: "FF92400E" } }
                    }
                }],
            });
        }
    });

    await exportToExcelJS({
        fileName: `confronto-offerte-${commessaId}.xlsx`,
        sheetName: "Confronto",
        columns,
        data,
        headerStyle: {
            font: { bold: true, color: { argb: "FF0F172A" } },
            fill: { type: "pattern", pattern: "solid", fgColor: { argb: "FFE2E8F0" } },
        },
        dataStyle: { font: { size: 11 } },
        conditionalFormatting,
        enableAutoFilter: true,
        freezeRows: 1,
        freezeColumns: 1,
    });
}

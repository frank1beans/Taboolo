"""Script per sostituire la logica del parser con testa-coda"""
from pathlib import Path

# Nuovo codice da inserire
NEW_CODE = """    cleaned_rows = []
    for row in data_rows:
        if not _row_has_values(row):
            continue

        codice = _combine_code(row, code_indexes)
        descrizione = _combine_text(row, description_indexes)
        raw_price = _cell_to_float(row, price_index)
        quantita = _cell_to_float(row, quantity_index) if quantity_index is not None else None
        progressivo_value = _cell_to_progressive(row, progressive_index)

        # Elimina righe di riepilogo tipo "Totale opere generali"
        if descrizione and descrizione.lower().startswith("totale ") and not progressivo_value:
            continue

        # Elimina righe di titolo capitolo: hanno (codice o descrizione) ma NON progressivo/quantità/prezzo
        if (codice or descrizione) and progressivo_value is None and quantita is None and raw_price is None:
            continue

        cleaned_rows.append(row)

    # =====================================================================
    # STEP 2: IDENTIFICA PROGRESSIVI (TESTE)
    # =====================================================================
    progressivo_indexes = []
    for idx, row in enumerate(cleaned_rows):
        progressivo_value = _cell_to_progressive(row, progressive_index)
        if progressivo_value is not None:
            progressivo_indexes.append((idx, progressivo_value, row))

    # =====================================================================
    # STEP 3: COSTRUISCI BLOCCHI E CREA VOCI
    # =====================================================================
    for i, (testa_idx, progressivo, testa_row) in enumerate(progressivo_indexes):
        # Determina fine blocco
        if i + 1 < len(progressivo_indexes):
            fine_blocco_idx = progressivo_indexes[i + 1][0]
        else:
            fine_blocco_idx = len(cleaned_rows)

        blocco = cleaned_rows[testa_idx:fine_blocco_idx]

        # Trova ultima riga non vuota (CODA)
        coda_row = None
        for row in reversed(blocco):
            if _row_has_values(row):
                coda_row = row
                break

        if coda_row is None:
            continue

        # Dalla TESTA: codice, descrizione
        codice = _combine_code(testa_row, code_indexes)
        descrizione = _combine_text(testa_row, description_indexes)

        # Dalla CODA: quantità, prezzo
        quantita = _cell_to_float(coda_row, quantity_index) if quantity_index is not None else None
        raw_price = _cell_to_float(coda_row, price_index)

        # Prezzo e importo
        prezzo_value = _sanitize_price_candidate(raw_price) if raw_price is not None else None
        importo_value = None
        if prezzo_value is not None and quantita is not None:
            prezzo_rounded = round(prezzo_value, 4)
            _, importo_value = _calculate_line_amount(quantita, prezzo_rounded)
            prezzo_value = prezzo_rounded

        voce_descrizione = descrizione or codice or f"Voce progressivo {progressivo}"

        # WBS levels
        wbs_levels: list[ParsedWbsLevel] = []
        normalized_code_value = _normalize_wbs7_code(codice)
        if _looks_like_wbs7_code(normalized_code_value):
            wbs_levels.append(
                ParsedWbsLevel(
                    level=7,
                    code=normalized_code_value,
                    description=voce_descrizione,
                )
            )

        voci.append(
            ParsedVoce(
                ordine=ordine,
                progressivo=progressivo,
                codice=codice,
                descrizione=voce_descrizione,
                wbs_levels=wbs_levels,
                unita_misura=None,
                quantita=quantita,
                prezzo_unitario=prezzo_value,
                importo=importo_value,
                note=None,
                metadata=None,
            )
        )
        ordine += 1
"""

# Leggi il file
parser_path = Path('app/services/importers/parser.py')
content = parser_path.read_text(encoding='utf-8')

# Marker di inizio e fine
start_marker = '    cleaned_rows = []\n    for row in data_rows:'
end_marker = '\n    computo = ParsedComputo('

start_pos = content.find(start_marker)
end_pos = content.find(end_marker, start_pos)

if start_pos == -1 or end_pos == -1:
    print("ERRORE: Non trovato il blocco da sostituire")
    exit(1)

# Costruisci il nuovo contenuto
new_content = content[:start_pos] + NEW_CODE + content[end_pos:]

# Backup
backup_path = parser_path.with_suffix('.py.backup')
backup_path.write_text(content, encoding='utf-8')
print(f"OK Backup salvato: {backup_path}")

# Scrivi il nuovo file
parser_path.write_text(new_content, encoding='utf-8')
print(f"OK Parser aggiornato: {parser_path}")
print(f"\nRighe vecchio codice: {content.count(chr(10))}")
print(f"Righe nuovo codice: {new_content.count(chr(10))}")
print(f"\nOK SOSTITUZIONE COMPLETATA!")

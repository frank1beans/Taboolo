# Importers overview

Pipeline suddivisa per responsabilità, così un nuovo dev sa dove mettere le mani:

## 📘 Nomenclatura unificata

**Termini standard** (usati consistentemente nel codice):

- **MC** (Computo Metrico) = File completo con quantità + prezzi + WBS
  - Chiamato `ComputoTipo.progetto` nel DB (legacy)
  - Metodo import: `import_computo_metrico()`
  - Variabili: `computo_metrico_base`, `mc_base_voci`

- **LC** (Lista Lavorazioni) = File ritorno con solo prezzi unitari (elenco prezzi)
  - Matching basato su codici e descrizioni vs listino prezzi
  - Import: `import_ritorno_gara()` con `sheet_price_column` specificato

- **Ritorno gara** = File ritorno generico (può essere LC o MC-based)
  - Chiamato `ComputoTipo.ritorno` nel DB
  - Metodo import: `import_ritorno_gara()` (autodetect LC/MC mode)
  - MC-based se mancano colonne prezzi → usa matching progressivi/quantità

- **Import batch single-file** = Modalità multi-impresa da un unico file
  - Metodo: `import_batch_single_file()`
  - Un file Excel con colonne comuni + colonne specifiche per impresa
  - Transazioni separate per ogni impresa (importazione robusta)
  - Se un'impresa fallisce, le altre vengono comunque importate
  - Esempio struttura file:
    ```
    | Prog | Codice | Descrizione | Qta_A | Prezzo_A | Qta_B | Prezzo_B |
    |------|--------|-------------|-------|----------|-------|----------|
    | 1    | A001   | Scavo       | 100   | 50.00    | 120   | 48.00    |
    ```

## Struttura moduli

- **`common.py`**: Utilità condivise (normalizzazioni WBS, arrotondamenti, `_WbsNormalizeContext` e insert bulk).
  Classe base: `BaseImportService`

- **`parser.py`**: Parsing Excel custom (auto-detect colonne, blocchi Totale, progressivi).
  Funzione principale: `_parse_custom_return_excel()`

- **`matching/`**: Modulo di allineamento/abbinamento (struttura modulare).
  - `config.py`: Costanti e soglie configurabili
  - `normalization.py`: Normalizzazione token e text processing
  - `report.py`: Generazione report e warning
  - `legacy.py`: Logica matching completa (da suddividere incrementalmente)
  - `__init__.py`: Re-export per retrocompatibilità

  Responsabilità:
  - Matching progressivi vs descrizioni
  - Matching con listino prezzi
  - Normalizzazione token (codici, descrizioni)
  - Generazione report e warning
  - Validazioni (zero guard, duplicati)

- **`lc.py`**: Orchestrazione import ritorni LC.
  Classe: `LcImportService` (estende `BaseImportService`)
  Responsabilità:
  - Round management (new/replace)
  - Persistenza computo e offerte
  - Integrazione parser + matching
  - Sincronizzazione voci normalizzate

- **`mc.py`**: Import computi di progetto MC.
  Classe: `McImportService` (estende `LcImportService`)
  Responsabilità:
  - Import computo progetto da Excel/SIX
  - Riuso pipeline LC per ritorni MC

- **`__init__.py`**: Re-export delle classi/funzioni usate fuori dal package.

## Compatibilità

I vecchi file `importer_*.py` (nella directory parent) restano come proxy per retrocompatibilità, ma il codice vivo è qui.

## Best practices

- ✅ Tutte le utility di calcolo (`_calculate_line_amount`, `_ceil_*`) sono definite **solo** in `common.py`
- ✅ Le classi service ereditano da `BaseImportService` e non fanno override inutili
- ✅ Import espliciti (no wildcard `import *`)
- ✅ Funzioni helper con naming prefix `_` (private al modulo)
- ✅ Costanti e configurazione estratte in moduli dedicati

## Refactoring roadmap

### ✅ Completato
- Rimossi errori critici (duplicazioni, bug variabili undefined)
- Eliminati override inutili e funzioni duplicate
- Creata struttura modulare `matching/` con:
  - `config.py`: Costanti e soglie
  - `normalization.py`: Token/text utils
  - `report.py`: Report generation

### 🚧 In corso (opzionale)
Suddivisione incrementale di `matching/legacy.py` (2000+ righe) in:

1. **`matching/progressive.py`** (TODO):
   - `_align_progressive_return()`
   - `_build_project_description_buckets()`
   - `_assign_wrapper_preferences()`
   - Logica matching basato su progressivi

2. **`matching/description.py`** (TODO):
   - `_align_description_only_return()`
   - `_match_by_description_similarity()`
   - `_match_excel_entry_fuzzy()`
   - Logica matching basato su descrizioni

3. **`matching/pricelist.py`** (TODO):
   - `_build_price_list_lookup()`
   - `_match_price_list_item_entry()`
   - `_match_price_list_item_semantic()`
   - Matching con listino prezzi

4. **`matching/totals.py`** (TODO):
   - `_align_totals_return()`
   - `_distribute_group_targets()`
   - `_apply_rounding_to_match()`
   - Logica matching con totali di gruppo

5. **`matching/validation.py`** (TODO):
   - `_detect_forced_zero_violations()`
   - `_detect_duplicate_progressivi()`
   - `_requires_zero_guard()`

### Note implementazione
- Mantenere retrocompatibilità tramite `matching/__init__.py`
- Spostare funzioni gradualmente da `legacy.py` ai nuovi moduli
- Aggiornare import in `lc.py` solo quando necessario
- Testare ogni modulo incrementalmente

## 📋 Esempi d'uso

### Import batch single-file

Importa ritorni gara per più imprese da un unico file Excel:

```python
from pathlib import Path
from sqlmodel import Session
from app.services.importers import LcImportService

service = LcImportService()

# File Excel con struttura:
# | Progressivo | Codice | Descrizione | Qta_ImpresaA | Prezzo_ImpresaA | Qta_ImpresaB | Prezzo_ImpresaB |
file_path = Path("/path/to/ritorni_multi_imprese.xlsx")

result = service.import_batch_single_file(
    session=session,
    commessa_id=123,
    file=file_path,
    originale_nome="ritorni_multi_imprese.xlsx",
    imprese_config=[
        {
            "nome_impresa": "Impresa A S.r.l.",
            "colonna_prezzo": "E",        # Colonna con prezzi Impresa A
            "colonna_quantita": "D",       # Colonna con quantità Impresa A (opzionale)
            "round_number": 1,
            "round_mode": "new"
        },
        {
            "nome_impresa": "Impresa B S.p.a.",
            "colonna_prezzo": "G",        # Colonna con prezzi Impresa B
            "colonna_quantita": "F",       # Colonna con quantità Impresa B (opzionale)
            "round_number": 1,
            "round_mode": "new"
        },
        {
            "nome_impresa": "Impresa C",
            "colonna_prezzo": "I",        # Colonna con prezzi Impresa C
            "colonna_quantita": None,      # Nessuna quantità (modalità LC)
            "round_number": 1,
            "round_mode": "new"
        }
    ],
    sheet_name=None,                      # Foglio di default
    sheet_progressive_column="A",         # Colonna progressivi (comune)
    sheet_code_columns=["B"],             # Colonne codice (comuni)
    sheet_description_columns=["C"],      # Colonne descrizione (comuni)
)

# Analisi risultati
print(f"✅ Successi: {result['success_count']}/{result['total']}")
print(f"❌ Fallimenti: {result['failed_count']}/{result['total']}")

for impresa in result['success']:
    computo = result['computi'][impresa]
    print(f"✓ {impresa}: Computo ID {computo.id}, Round {computo.round_number}")

for failure in result['failed']:
    print(f"✗ {failure['impresa']}: {failure['error']}")
```

**Caratteristiche**:
- ✅ Transazioni separate: Se un'impresa fallisce, le altre vengono comunque importate
- ✅ Gestione errori robusta: Colonne vuote o errori di parsing non bloccano l'intero batch
- ✅ Report dettagliato: Successi e fallimenti con dettagli completi
- ✅ Riusa logica esistente: Ogni impresa viene processata come `import_ritorno_gara()` separato
- ✅ Supporta LC e MC: Specifichi `colonna_quantita` per MC mode, ometti per LC mode

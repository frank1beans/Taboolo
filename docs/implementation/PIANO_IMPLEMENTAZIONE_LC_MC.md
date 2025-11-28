# Piano Implementazione: Separazione Import LC e MC

## ✅ COMPLETATO

### 1. Analisi del Problema

**File**: `REPORT_PREZZI_ZERO.md`

Identificato il problema root:
- Import LC crea offerte correttamente, ma la ricostruzione del computo usa `_build_project_snapshot_from_price_offers` che NON è progettata per LC
- Se un product_id ha multipli progressivi, la funzione legacy NON applica il prezzo a tutti
- Risultato: voci con prezzo 0 nonostante l'impresa abbia fornito i prezzi

**Impatto**:
- Commessa 001: 1-13 voci con prezzo 0 su 1042 (~1% fallimento) - situazione buona
- Commessa 008: 574 voci con prezzo 0 su 1239 (~46% fallimento) - situazione critica
- **97 product_id** su 135 (71.9%) hanno multipli progressivi in commessa 001
- Totale progressivi coinvolti: 1004 su 1042

### 2. Creazione Nuovo Servizio LC

**File creati**:

1. **`backend/app/services/importers/import_common.py`**
   - Funzioni comuni condivise tra LC e MC
   - `_build_parsed_from_progetto()`: costruisce ParsedVoce da VoceComputo
   - `calculate_total_import()`: calcola importo totale computo
   - `validate_progetto_voci()`: valida voci del computo progetto

2. **`backend/app/services/importers/lc_import_service.py`**
   - Servizio dedicato per import LC
   - Classe: `LcImportService`
   - Metodo principale: `import_lc()`
   - Logica chiave: `_build_computo_from_lc_offers()`
     - **Applica lo stesso prezzo a TUTTI i progressivi con stesso product_id**
     - L'impresa quota il PRODOTTO, non il singolo progressivo
     - Coverage atteso: ~100%

3. **`backend/app/services/importers/__init__.py`** (modificato)
   - Espone `LcImportService` (nuovo)
   - Mantiene `LcImportServiceLegacy` per retrocompatibilità

### 3. Analisi Commessa 001

**File di test**: `test_lc_analysis.py`

**Risultati**:
```
Computo Progetto: 1042 voci
Product_id unici: 135
Product_id con multipli progressivi: 97 (71.9%)
Progressivi coinvolti: 1004

Ritorni Esistenti (9 computi):
- CEV:       1029/1042 (98.8%) ← 13 voci con prezzo 0
- COIVER:    1041/1042 (99.9%) ← 1 voce con prezzo 0
- EXA:       1029/1042 (98.8%) ← 13 voci con prezzo 0
- EDILTECNO: 1038/1042 (99.6%) ← 4 voci con prezzo 0
- KORUS:     1029/1042 (98.8%) ← 13 voci con prezzo 0
```

**Osservazioni**:
- Le imprese CEV, EXA, KORUS hanno ESATTAMENTE 13 voci con prezzo 0
- Questo suggerisce che mancano gli stessi 13 product_id nei loro file LC
- Con il nuovo servizio, anche queste 13 voci dovrebbero avere prezzo 0 (comportamento corretto)
- COIVER ha solo 1 voce con prezzo 0 → file LC quasi completo
- EDILTECNO ha 4 voci con prezzo 0

---

## 📋 TODO - PROSSIMI PASSI

### FASE 1: Integrare il Nuovo Servizio LC

#### Opzione A: Switch Graduale (RACCOMANDATO)
1. Aggiungere flag feature `use_new_lc_service` nelle settings
2. Modificare endpoint API per usare flag:
   ```python
   if settings.use_new_lc_service:
       service = LcImportService()
   else:
       service = LcImportServiceLegacy()
   ```
3. Testare su commessa 001 con nuovo servizio
4. Confrontare risultati (coverage, importo totale, etc.)
5. Se OK, abilitare globalmente

#### Opzione B: Switch Diretto
1. Modificare direttamente l'endpoint API
2. Sostituire `LcImportServiceLegacy` con `LcImportService`
3. Testare subito su tutte le commesse

**Raccomandazione**: Opzione A per sicurezza

### FASE 2: Aggiornare Endpoint API

**File da modificare**: `backend/app/api/v1/endpoints/commesse.py`

Cercare dove viene usato `LcImportService` e aggiornare per usare il nuovo:

```python
# PRIMA
from app.services.importers import LcImportService

service = LcImportService()
computo = service.import_ritorno_gara(...)  # Metodo legacy

# DOPO
from app.services.importers import LcImportService

service = LcImportService()
computo = service.import_lc(...)  # Nuovo metodo dedicato
```

**Nota**: Il nuovo metodo `import_lc()` ha la stessa firma di `import_ritorno_gara()` per modalità LC, quindi dovrebbe essere drop-in replacement.

### FASE 3: Test End-to-End

#### Test 1: Re-import su Commessa 001
1. Backup database
2. Cancellare un computo ritorno esistente (es. CEV Round 1)
3. Re-importare file LC originale con nuovo servizio
4. Verificare:
   - Coverage: dovrebbe essere ~99-100% (vs 98.8% precedente)
   - Importo totale: deve essere uguale o molto simile
   - Numero voci: 1042 (invariato)
   - Voci con prezzo 0: dovrebbe scendere da 13 a ~0

#### Test 2: Re-import su Commessa 008
1. Backup database
2. Cancellare computo ritorno FLOORING
3. Re-importare file LC FLOORING con nuovo servizio
4. Verificare:
   - Coverage: dovrebbe salire da 54% a ~100%
   - Voci con prezzo 0: dovrebbe scendere da 574 a ~0
   - Importo totale: verificare che abbia senso

### FASE 4: Creare McImportService Separato

Una volta stabilizzato LC, procedere con MC:

**File da creare**: `backend/app/services/importers/mc_import_service.py`

```python
class McImportService(BaseImportService):
    """
    Servizio per l'importazione di file MC (Computo Metrico).

    Il file MC contiene progressivi + quantità + prezzi.
    Matching: progressivo → voce progetto (ESATTO).
    """

    def import_mc(self, ...) -> Computo:
        # 1. Parse file MC
        # 2. Validazioni:
        #    - Progressivi duplicati
        #    - Progressivi non nel progetto
        #    - Codici con prezzi diversi per stesso progressivo
        # 3. Match SOLO su progressivo (ignorare codice)
        # 4. Gestione conflitti prezzo/quantità
        # 5. Crea computo ritorno
        # 6. Opzionalmente crea price_list_offer
        pass

    def _validate_mc_file(self, ...) -> list[str]:
        # Validazioni pre-import
        pass

    def _align_mc_rows(self, ...) -> AlignmentResult:
        # Match su progressivo ESATTO
        pass
```

### FASE 5: Refactoring Endpoints API

Creare endpoint separati (opzionale ma raccomandato):

```python
@router.post("/import-lc")
def import_lc_explicit(...):
    """Import esplicito LC (Lista Lavorazioni)."""
    service = LcImportService()
    return service.import_lc(...)

@router.post("/import-mc")
def import_mc_explicit(...):
    """Import esplicito MC (Computo Metrico)."""
    service = McImportService()
    return service.import_mc(...)

@router.post("/import-ritorno")  # Mantiene retrocompatibilità
def import_ritorno_auto(...):
    """Auto-detect LC vs MC."""
    if sheet_price_column:  # Modalità LC
        service = LcImportService()
        return service.import_lc(...)
    else:  # Modalità MC
        service = McImportService()
        return service.import_mc(...)
```

---

## 🔍 CHECKLIST FINALE

### Pre-Deploy
- [ ] Backup database completo
- [ ] Test nuovo LcImportService su commessa 001
- [ ] Confronto risultati con servizio legacy
- [ ] Test nuovo LcImportService su commessa 008
- [ ] Verificare che importo totale sia corretto
- [ ] Verificare che WBS aggregation funzioni (con progressivi corretti)

### Deploy
- [ ] Aggiornare endpoint API per usare nuovo servizio
- [ ] Deploy su ambiente di staging
- [ ] Test manuale completo
- [ ] Deploy su produzione

### Post-Deploy
- [ ] Monitorare import LC per errori
- [ ] Verificare feedback utenti
- [ ] Documentare nuova logica per utenti
- [ ] Aggiornare guida import LC

---

## 📊 METRICHE DI SUCCESSO

### Commessa 001
- **Prima**: 98.8% coverage (13 voci con prezzo 0)
- **Dopo**: 99-100% coverage (0-1 voci con prezzo 0)
- **Miglioramento**: +1-2%

### Commessa 008
- **Prima**: 54% coverage (574 voci con prezzo 0)
- **Dopo**: ~100% coverage (0-10 voci con prezzo 0)
- **Miglioramento**: +46%

### Generale
- Eliminazione prezzi a zero per voci con offerta valida
- Importo totale corretto
- Nessuna regressione su import MC
- Coverage offerte ~100% per LC

---

## 🎯 DIFFERENZE CHIAVE LC vs MC

### LC (Lista Lavorazioni)
| Aspetto | Comportamento |
|---------|---------------|
| Contenuto file | Solo prezzi unitari per prodotto |
| Progressivi | **NON presenti** |
| Matching | Codice/descrizione → price_list_item |
| Logica prezzo | UN prezzo per product_id → applicato a TUTTI i progressivi |
| Scopo | L'impresa quota il PRODOTTO |
| Tabella primaria | `price_list_offer` |

### MC (Computo Metrico)
| Aspetto | Comportamento |
|---------|---------------|
| Contenuto file | Progressivi + quantità + prezzi |
| Progressivi | **Presenti e obbligatori** |
| Matching | Progressivo → voce progetto (ESATTO) |
| Logica prezzo | UN prezzo per progressivo (può variare per stesso codice) |
| Scopo | L'impresa quota il SINGOLO PROGRESSIVO |
| Tabella primaria | `vocecomputo` (ritorno) |

---

## 📝 NOTE IMPLEMENTATIVE

### Gestione Progressivo Map

Nel nuovo `LcImportService`, la `progressivo_map` NON viene usata perché:
1. File LC non contiene progressivi
2. La logica corretta è: product_id → prezzo applicato a TUTTI i progressivi
3. Non serve disambiguare perché TUTTI devono ricevere lo stesso prezzo

### Conservazione Price List Offers

Le offerte in `price_list_offer` vengono conservate perché:
1. Servono per confronti futuri
2. Permettono analisi di trend
3. Abilitano funzionalità "aggiornamento manuale prezzi"
4. Sono la fonte di verità per i prezzi LC

### Backward Compatibility

Il vecchio `LcImportService` in `lc.py` è rinominato `LcImportServiceLegacy` e mantenuto per:
1. Possibilità di rollback
2. Test comparativi
3. Graduale migrazione

Una volta stabilizzato il nuovo servizio (dopo 2-3 settimane in produzione), si può rimuovere il legacy.

---

**Data**: 2025-11-28
**Autore**: Claude (Anthropic)
**Versione**: 1.0

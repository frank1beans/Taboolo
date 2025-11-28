# Report: Analisi Prezzi a Zero nell'Importazione LC

## Problema
Durante l'importazione dei file LC (Lista Lavorazioni) delle imprese, **574 voci su 1239 (46%)** hanno prezzo = 0, nonostante l'impresa abbia fornito i prezzi nel file.

## Causa Root
Il problema è dovuto al fatto che **multipli progressivi del computo condividono lo stesso `product_id`**, ma il sistema LC non gestisce correttamente questa situazione.

### Esempio Concreto: Progressivo 10

**Nel Computo Progetto**, ci sono 3 voci con lo stesso `product_id` (20654):
- Progressivo 10: quantità 239.05
- Progressivo 90: quantità 49.32
- Progressivo 160: quantità 170.77

**Nel File LC dell'impresa FLOORING**:
- È stata fornita UN'UNICA voce per il codice `L005.030.23` (product_id 20654)
- Prezzo: 6.6346
- Quantità: 170.77 (corrisponde esattamente al progressivo 160!)

**Risultato nell'Import**:
- Viene creata UN'UNICA offerta (`price_list_offer`) per `product_id` 20654
- Questa offerta contiene prezzo 6.6346 e quantità 170.77

**Problema nella Ricostruzione del Computo**:
La funzione `_build_project_snapshot_from_price_offers` (file `legacy.py:641`) prende TUTTE le voci del progetto e, per ciascuna, cerca il prezzo dall'offerta usando il `product_id`.

```python
# Riga 660-661 in legacy.py
target_item = product_index.get(product_id) if product_id else None
prezzo = offer_price_map.get(target_item.id) if target_item else None
```

**Ma**: se ci sono multipli progressivi con lo stesso `product_id`, TUTTI i progressivi vengono processati, ma **l'offerta è una sola**!

## Flusso del Problema

```
File LC dell'Impresa
    ↓
  Codice: L005.030.23
  Prezzo: 6.6346
  Quantità: 170.77
    ↓
[Matching su codice/descrizione]
    ↓
price_list_item (ID: 2096, product_id: 20654)
    ↓
price_list_offer creata
    ↓
[Ricostruzione computo da offerte]
    ↓
Cerca product_id 20654 in TUTTE le voci progetto
    ↓
Trova 3 progressivi (10, 90, 160) con stesso product_id
    ↓
PROBLEMA: Come assegnare l'offerta?
    ↓
Il sistema assegna lo stesso prezzo a TUTTI?
O solo al primo? O a nessuno?
```

## Analisi del Codice

### 1. Import LC (`lc.py:339-351`)
```python
return self._import_lc_return(
    ...
    progetto_voci=None,  # in LC il progressivo non è previsto ← PROBLEMA!
    ...
)
```

**Problema**: `progetto_voci` è None, quindi non viene costruita la `progressivo_map` che potrebbe aiutare.

### 2. Sync Offers (`lc.py:914-1062`)
La funzione `_sync_price_list_offers` crea offerte mappando voci LC → price_list_item usando:
- Matching su codice
- Matching su descrizione
- Matching su embedding semantico

Ma NON usa il progressivo perché:
1. Il file LC non contiene progressivi
2. `progetto_voci` è None

### 3. Rebuild Computo (`legacy.py:641-682`)
La funzione `_build_project_snapshot_from_price_offers` ricostruisce il computo da offerte:
- Cicla su TUTTE le voci del progetto
- Per ogni voce, cerca il prezzo dall'offerta usando `product_id`
- **NON distingue tra multipli progressivi con stesso product_id**

## Impatto

Analizzando il database:
- **394 product_id** unici nel listino prezzi
- **1239 voci** nel computo progetto
- Rapporto: **~3.1 voci per product_id** in media

Molti product_id sono usati da multipli progressivi:
- `L014.030.01`: **28 progressivi diversi**
- `L022.030.01`: **22 progressivi diversi**
- `L016.020.01`: **14 progressivi diversi**
- E molti altri...

## Possibili Soluzioni

### Opzione 1: Applicare Prezzo a TUTTI i Progressivi con Stesso Product_ID
**PRO**:
- Semplice da implementare
- Mantiene compatibilità con formato LC standard

**CONTRO**:
- Non rispetta l'intento dell'impresa se ha fornito una voce specifica
- Potrebbe sovrastimare/sottostimare costi

### Opzione 2: Richiedere Progressivi nei File LC
**PRO**:
- Matching preciso
- Nessuna ambiguità

**CONTRO**:
- Richiede modifica formato file LC
- Le imprese devono conoscere i progressivi

### Opzione 3: Match su Quantità quando Product_ID Duplicato
Se un product_id è usato da multipli progressivi, usare la quantità per disambiguare:
- Cerca il progressivo con quantità più vicina alla quantità nell'offerta

**PRO**:
- Migliore approssimazione dell'intento
- Non richiede modifiche ai file LC

**CONTRO**:
- Potrebbe fallire se quantità sono simili
- Logica complessa

### Opzione 4 (RACCOMANDATA): Gestione Ibrida
1. Se esiste SOLO UN progressivo per product_id → usa quell'offerta
2. Se esistono MULTIPLI progressivi:
   a. Se c'è un match esatto sulla quantità → usa solo quello
   b. Altrimenti → applica a TUTTI i progressivi con warning

**PRO**:
- Gestisce entrambi i casi correttamente
- Warning chiari per l'utente

**CONTRO**:
- Implementazione più complessa

## Raccomandazione

Implementare **Opzione 4**: gestione ibrida con match su quantità quando disponibile.

### Modifiche Necessarie

1. **`_build_project_snapshot_from_price_offers` (`legacy.py:641`)**:
   - Costruire un indice `product_id → [progressivi]`
   - Per ogni product_id con multipli progressivi:
     - Se offerta ha quantità → match sul progressivo con quantità più vicina
     - Altrimenti → applica a tutti con warning

2. **`_sync_price_list_offers` (`lc.py:914`)**:
   - Salvare la quantità nell'offerta (già fatto)
   - Passare `progetto_voci` invece di None

3. **Report Warnings**:
   - Aggiungere warning quando product_id ha multipli progressivi
   - Indicare quali progressivi hanno ricevuto il prezzo e quali no

## Test Case da Verificare

- [ ] Product_id con singolo progressivo → prezzo applicato correttamente
- [ ] Product_id con multipli progressivi e match quantità esatto → prezzo solo al progressivo corretto
- [ ] Product_id con multipli progressivi senza match quantità → prezzo a tutti con warning
- [ ] Verificare che importo totale sia corretto
- [ ] Verificare che non ci siano regressioni su import MC

---

**Data**: 2025-11-28
**Commessa Analizzata**: Commessa 8
**Computo Progetto**: ID 23 (1239 voci)
**Computo Ritorno**: ID 27 - FLOORING (574 voci con prezzo 0)

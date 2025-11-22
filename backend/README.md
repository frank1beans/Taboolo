# Backend FastAPI (Python)

Questo backend espone le API richieste dall'app React per gestire **commesse**, import di file Excel (computo metrico di progetto + ritorni di gara) e l'esportazione del file aggregato `Tabulazioni_raw.xlsx`.

## Prerequisiti

- Python 3.10+
- `pip` o `uv` per installare i pacchetti indicati in `requirements.txt`

## Setup rapido

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# oppure source .venv/bin/activate su macOS/Linux
pip install -r requirements.txt
```

Per avviare il server in locale:

```bash
uvicorn app.main:app --reload
```

Il database SQLite e i file caricati vengono salvati nella cartella `storage/` (creata automaticamente al primo avvio). In produzione potrà essere montata su un volume persistente.

## Struttura cartelle

```
backend/
├── app/
│   ├── api/               # Router FastAPI
│   ├── core/              # Config, logging
│   ├── db/                # Motore, sessioni, modelli SQLModel
│   ├── excel/             # Parser e logica di import dai file
│   └── services/          # Business logic (commesse, computi, ritorni)
├── storage/               # File salvati + database.sqlite (generata a runtime)
├── requirements.txt
└── README.md
```

## Roadmap API (bozza)

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `POST` | `/commesse` | Crea una nuova commessa vuota |
| `POST` | `/commesse/{id}/computo-progetto` | Carica il file Excel del computo di progetto |
| `POST` | `/commesse/{id}/ritorni` | Carica il file Excel di un ritorno di gara (impresa) |
| `GET`  | `/commesse` | Lista commesse + stato import |
| `GET`  | `/commesse/{id}` | Dettaglio commessa con computi/ritorni |
| `GET`  | `/computi/{id}/wbs` | Albero WBS calcolato + lista lavorazioni aggregata |

| `GET`  | `/commesse/{id}/export` | Esporta il file aggregato `Tabulazioni_raw.xlsx` |

Nei prossimi step verranno implementati:

- Abbinamento automatico tra computo metrico estimativo e ritorni di gara
- Generazione dell'export aggregato `Tabulazioni_raw.xlsx`
- Endpoint per aggiornare/eliminare computi e ricarichi
- Script di packaging (eseguibile standalone) una volta stabilizzate le API

## Testing rapido

Puoi eseguire `python backend/scripts/import_test.py` per importare il file di esempio e vedere in console il numero di voci salvate, il primo nodo WBS e le prime aggregazioni calcolate.

## Migrazioni database

Il database SQLite viene gestito tramite Alembic. Dopo aver aggiornato il codice esegui:

```bash
cd backend
pip install -r requirements.txt  # se necessario
alembic upgrade head
```

Questo comando porta il database all'ultima revisione (inclusi i campi `commessa.stato` e `wbs7.commessa_id`). Se parti da dati legacy puoi riallineare lo schema WBS normalizzato tramite:

```bash
python scripts/backfill_wbs6.py
```

## Performance e accesso ai dati

Linee guida e snippet per spostare calcoli numerici su dataframe colonnari (Pandas/Polars, DuckDB) sono raccolti in
[`docs/backend/PERFORMANCE_DATAFRAMES.md`](../docs/backend/PERFORMANCE_DATAFRAMES.md). Valuta questo approccio quando le
query SQL + loop Python non bastano più per analisi WBS o confronti tra offerte.

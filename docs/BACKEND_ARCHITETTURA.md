# Architettura Backend

Questa panoramica descrive i blocchi principali del backend Taboolo e offre riferimenti diretti alla documentazione per-script disponibile in `backend/docs`.

## Layer applicativi

| Layer | Percorso | Descrizione |
|-------|----------|-------------|
| API | `backend/app/api` | Endpoint FastAPI, middleware e dipendenze condivise. |
| Dominio | `backend/app/domain` | Modelli e servizi di dominio (commesse, computi, catalogo, utenti, wbs, impostazioni). |
| Servizi | `backend/app/services` | Logica di orchestrazione trasversale: analisi dati, import, NLP, storage e calcolo WBS. |
| DB/Core | `backend/app/db` – `backend/app/core` | Gestione sessioni, configurazioni, sicurezza e logging. |
| Excel/NLP | `backend/app/excel`, `backend/app/services/nlp` | Parser di file e pipeline ML dedicate. |
| Script operativi | `backend/scripts` | Utility CLI di manutenzione (FAISS, import, embedding, semantic search). |
| Motore Robimb | `backend/robimb` | Toolkit per estrazione proprietà, training, inferenza e reporting AI. |
| Migrazioni | `backend/migrations` | Script Alembic per evolvere il database. |
| Test | `backend/tests` | Suite unit test e regressioni sugli importer MC/LC. |

## Flussi principali

1. **Richieste API** attraversano `app/api/v1/endpoints`, delegano al dominio (es. `app/domain/commesse`) e sfruttano servizi trasversali.
2. **Processi di import** partono da `app/services/importer.py` e utilizzano parser/segnatura in `app/services/importers/*`.
3. **Analisi e dashboard** vivono in `app/services/analysis` e vengono alimentate da cache/wbs services.
4. **Motore Robimb** fornisce pipeline ML autonome (CLI in `robimb/cli`) ma richiamabili dal backend tramite servizi NLP.

## Documentazione di dettaglio

- **Indice e guida**: `backend/docs/README.md`
- **Catalogo script**: `backend/docs/SCRIPT_REFERENCE.md`
- **Workflow di aggiornamento**: `docs/DOCUMENTAZIONE_SCRIPT.md`

Consulta sempre il catalogo per capire come un file interagisce con gli altri: ogni sezione riporta dipendenze, classi, funzioni e entrypoint CLI.

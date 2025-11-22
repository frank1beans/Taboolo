# Accesso ai dati per analisi veloci

Questo progetto oggi legge le voci di computo con query SQLModel/SQLAlchemy e costruisce la struttura di analisi iterando in Python. Per dataset medi va bene, ma con molte voci l'overhead di oggetti Python e loop cresce.

## Perché passare a dataframe
- **Memoria colonnare**: librerie come Pandas/Polars o DuckDB tengono i dati in blocchi continui (Arrow/Parquet) e sfruttano SIMD/parallelismo nei `groupby`/`agg`.
- **Meno oggetti Python**: invece di costruire migliaia di `VoceComputo`, lavori su array nativi che si mappano direttamente a calcoli di somma/media/min/max.
- **Join e filtri mirati**: puoi pre-filtrare per `commessa_id`, `round_number` o `impresa` in SQL e consegnare alle analisi solo le colonne necessarie.

## Lettura diretta da SQL in dataframe
Punto di partenza suggerito (riutilizza il bind della sessione):

Consulta `InsightsService._load_voci_dataframe` per un esempio concreto di caricamento SQL → Pandas già pronto all’uso dentro il servizio di analisi. La funzione carica le voci di computo per una lista di computi, preserva l’ordinamento e restituisce `SimpleNamespace` compatibili con la logica esistente.

```python
import pandas as pd
import polars as pl


def load_voci_df(session, commessa_id: int) -> pl.DataFrame:
    engine = session.get_bind()
    query = """
        SELECT v.id, v.computo_id, v.codice, v.descrizione, v.quantita, v.prezzo_unitario,
               v.importo, v.wbs6_code, v.wbs6_description, v.wbs7_code, v.wbs7_description,
               c.tipo, c.round_number, c.impresa
        FROM voce_computo v
        JOIN computo c ON c.id = v.computo_id
        WHERE c.commessa_id = :commessa_id
    """
    pdf = pd.read_sql_query(query, engine, params={"commessa_id": commessa_id})
    return pl.from_pandas(pdf)
```

Da qui puoi calcolare media/min/max/importi per WBS con una sola chiamata:

```python
voci_df = load_voci_df(session, commessa_id)
wbs_summary = (
    voci_df.group_by("wbs6_code", "tipo")
    .agg(
        pl.col("importo").sum().alias("importo_totale"),
        pl.col("prezzo_unitario").mean().alias("prezzo_medio"),
        pl.col("importo").min().alias("importo_min"),
        pl.col("importo").max().alias("importo_max"),
    )
)
```

## Alternative e ottimizzazioni
- **DuckDB + Arrow**: `duckdb.query("... FROM voce_computo WHERE commessa_id = ?", [id]).pl()` restituisce direttamente un dataframe Polars senza passaggi intermedi.
- **Cache/materializzazione**: salvare i dataframe in Parquet (per `commessa/round`) dopo l'import e riusarli per le API riduce i round-trip verso SQLite/Postgres.
- **Paginazione WBS**: se si chiede il dettaglio di una sola WBS, aggiungere un filtro SQL e caricare solo quella porzione nel dataframe.
- **Profiling**: prima di migrare blocchi di logica, misurare `groupby`/join attuali per individuare i punti critici che beneficiano di colonnare/parallelismo.

Queste tecniche permettono di mantenere la logica di business in Python, spostando il lavoro numerico su runtime ottimizzati per la manipolazione di colonne, riducendo latenza e CPU.

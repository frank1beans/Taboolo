# Documentazione degli script backend

Questa guida spiega come è organizzata la documentazione per singolo file Python e come mantenerla aggiornata.

## Dove trovare le informazioni

| Risorsa | Percorso | Contenuto |
|---------|----------|-----------|
| Guida rapida | `docs/README.md` | Contesto generale e convenzioni. |
| Architettura | `docs/BACKEND_ARCHITETTURA.md` | Relazione tra layer dell'applicazione. |
| Catalogo completo | `backend/docs/SCRIPT_REFERENCE.md` | Sezione dedicata a **ogni** file `.py` del backend con classi, funzioni, costanti e dipendenze. |
| Script di generazione | `backend/scripts/generate_backend_docs.py` | Produce il catalogo precedente in modo deterministico. |

## Processo di aggiornamento

1. **Modifica o aggiungi** uno script sotto `backend/`.
2. **Rigenera il catalogo** eseguendo:
   ```bash
   cd backend
   python scripts/generate_backend_docs.py
   ```
3. **Verifica il diff** di `backend/docs/SCRIPT_REFERENCE.md`.
4. **Versiona** il file insieme alle modifiche di codice.

## Contenuto del catalogo

Per ogni modulo troverai:

- numero di linee e breve descrizione (docstring se presente, altrimenti sintesi automatica);
- dipendenze importate (prime 12 mostrate, con conteggio totale);
- classi e funzioni pubbliche con firme e docstring;
- costanti dichiarate in uppercase;
- presenza di entry point CLI;
- eventuali errori di parsing segnalati in chiaro.

Questo formato nasce per coprire tutta la codebase senza lasciare zone scoperte. Se uno script inizia a crescere, valuta di aggiungere una docstring dettagliata: verrà riportata automaticamente nel catalogo.

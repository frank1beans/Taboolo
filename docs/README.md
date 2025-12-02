# Documentazione Taboolo

Questa cartella contiene la nuova struttura documentale condivisa per il progetto. Tutto il materiale precedente è stato rimosso e sostituito con una raccolta focalizzata sul backend.

## Struttura aggiornata

- `README.md` (questo file) – panoramica rapida e convenzioni.
- `BACKEND_ARCHITETTURA.md` – descrizione sintetica dei componenti applicativi principali.
- `DOCUMENTAZIONE_SCRIPT.md` – istruzioni su come navigare e aggiornare il catalogo dettagliato degli script.
- `../backend/docs` – sorgente della documentazione per ogni file Python; contiene sia un indice sia il catalogo completo generato automaticamente.

## Convenzioni principali

1. **Lingua**: tutti i testi devono essere in italiano chiaro.
2. **Percorsi**: indicare sempre i path relativi alla cartella del repository (es. `backend/app/services/...`).
3. **Aggiornamenti**: ogni modifica al codice che crea/modifica uno script deve accompagnarsi all’aggiornamento del catalogo in `backend/docs`.

## Come contribuire

1. Leggi `BACKEND_ARCHITETTURA.md` per capire il contesto funzionale.
2. Consulta `DOCUMENTAZIONE_SCRIPT.md` per sapere come trovare lo script che ti interessa.
3. Quando aggiungi/modifichi file Python, esegui lo script di generazione (vedi istruzioni nel file sopra) e versiona i risultati.

Per dubbi o miglioramenti, apri una issue dedicata citando il file oggetto della modifica.

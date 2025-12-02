# Documentazione backend

Questa cartella contiene l'intera documentazione tecnica del backend Taboolo. Tutti i file precedenti sono stati rimossi e sostituiti da una struttura minima ma completa:

- `README.md` (questo file): spiega come è organizzato il materiale.
- `SCRIPT_REFERENCE.md`: catalogo generato automaticamente che descrive ogni file `.py` sotto `backend/`.

## Obiettivi

1. **Copertura totale** – nessuno script rimane senza descrizione o riferimento.
2. **Aggiornamento rapido** – basta eseguire uno script per rigenerare tutto.
3. **Uniformità** – stesso layout per ogni modulo (linee, docstring, classi, funzioni, costanti, entry point).

## Come rigenerare il catalogo

```bash
cd backend
python scripts/generate_backend_docs.py
```

Lo script legge tutti i file `.py`, estrae docstring, firme e import e sovrascrive `SCRIPT_REFERENCE.md`. Il risultato è deterministico e ordinato per cartella.

## Quando aggiornare

- creazione di un nuovo script;
- modifica sostanziale della docstring;
- spostamento di file tra cartelle;
- refactor che cambia classi/funzioni esposte.

Ricorda di includere sempre il catalogo aggiornato nel commit: è la fonte di verità per tutto il backend.

# 🚀 Setup Backend Python

Guida rapida per eseguire il backend FastAPI del progetto Taboo Measure Maker.

## 📋 Prerequisiti

- Python 3.10 o superiore
- pip (gestore pacchetti Python)

## 🔧 Installazione

### 1. Naviga nella cartella backend

```bash
cd backend
```

### 2. Crea un ambiente virtuale (consigliato)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

## ▶️ Avvio del Server

### Metodo 1: Script Python (Consigliato)

```bash
python run.py
```

### Metodo 2: Uvicorn diretto

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Verifica che funzioni

Una volta avviato, dovresti vedere:

```
🚀 Avvio Taboo Measure Maker Backend...
📍 API disponibile su: http://localhost:8000
📚 Documentazione Swagger: http://localhost:8000/docs
```

### Test rapido

1. Apri il browser su: **http://localhost:8000/docs**
2. Dovresti vedere la documentazione interattiva Swagger UI
3. Prova l'endpoint `/api/v1/commesse` per verificare che risponda

## 📂 Struttura Database

Il backend crea automaticamente:
- Un database SQLite in `storage/database.sqlite`
- La cartella `storage/` per i file caricati

Queste cartelle vengono create automaticamente al primo avvio.

## 🔗 Collegamento con il Frontend

Il frontend React (su http://localhost:8080) è già configurato per comunicare con il backend su `http://localhost:8000/api/v1`.

Una volta che entrambi sono in esecuzione, puoi:
1. Aprire http://localhost:8080 nel browser
2. Navigare in una commessa
3. Caricare un file Excel (.xlsx/.xls)
4. Il backend lo processerà e caricherà i dati

## 🐛 Risoluzione Problemi

### Errore: "ModuleNotFoundError"
```bash
# Assicurati di aver attivato l'ambiente virtuale e installato le dipendenze
pip install -r requirements.txt
```

### Errore: "Address already in use"
```bash
# La porta 8000 è già occupata, cambia porta nel run.py o termina il processo esistente
# Su Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Su Mac/Linux:
lsof -ti:8000 | xargs kill -9
```

### CORS Error dal frontend
Il backend è già configurato con CORS aperto per lo sviluppo. Se hai problemi, verifica che il frontend stia chiamando `http://localhost:8000/api/v1` e non un altro URL.

## 📝 Note Importanti

- **Sviluppo**: Il server si ricarica automaticamente quando modifichi i file Python
- **Database**: Usa SQLite per semplicità (file `storage/database.sqlite`)
- **File Upload**: I file caricati vengono salvati in `storage/commessa_XXXX/uploads/`
- **Log**: I log del server appaiono direttamente nel terminale

## 🧪 Test Upload

Per testare l'upload di un file Excel:

1. Backend attivo su http://localhost:8000
2. Frontend attivo su http://localhost:8080
3. Vai su una commessa nel frontend
4. Carica un file Excel tramite l'interfaccia
5. Controlla i log del backend nel terminale
6. Verifica che la struttura WBS sia stata creata

## 📚 API Endpoints Disponibili

- `GET /api/v1/commesse` - Lista commesse
- `POST /api/v1/commesse` - Crea nuova commessa
- `GET /api/v1/commesse/{id}` - Dettagli commessa
- `POST /api/v1/commesse/{id}/computo-progetto` - Upload computo progetto
- `POST /api/v1/commesse/{id}/ritorni` - Upload ritorno gara
- `GET /api/v1/computi/{id}/wbs` - Struttura WBS di un computo

Documentazione completa: http://localhost:8000/docs

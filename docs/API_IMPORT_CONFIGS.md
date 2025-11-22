# API Import Configurations

## Nuove API per Configurazioni Import Ritorni Gara

### Endpoint Base
```
/api/v1/import-configs
```

---

## 📋 Lista Configurazioni

**GET** `/api/v1/import-configs`

**Query Parameters**:
- `commessa_id` (optional): Filtra per commessa specifica. Se omesso, mostra tutte (globali + specifiche)

**Response**:
```json
[
  {
    "id": 1,
    "nome": "Formato Impresa ABC",
    "impresa": "Impresa ABC S.r.l.",
    "sheet_name": "Offerta",
    "code_columns": "A,B",
    "description_columns": "C",
    "price_column": "J",
    "quantity_column": "H",
    "note": "Formato standard usato dall'impresa ABC",
    "commessa_id": null,
    "created_at": "2025-01-12T10:30:00",
    "updated_at": "2025-01-12T10:30:00"
  }
]
```

---

## ➕ Crea Configurazione

**POST** `/api/v1/import-configs`

**Query Parameters**:
- `commessa_id` (optional): Associa la configurazione a una commessa specifica. Se omesso, la configurazione è globale

**Body**:
```json
{
  "nome": "Formato Impresa XYZ",
  "impresa": "Impresa XYZ S.p.A.",
  "sheet_name": "Foglio1",
  "code_columns": "A",
  "description_columns": "B,C",
  "price_column": "G",
  "quantity_column": "H",
  "note": "Usa sempre il foglio 'Foglio1'"
}
```

**Response**: Stesso formato della lista, con `id` generato

---

## 📝 Aggiorna Configurazione

**PUT** `/api/v1/import-configs/{config_id}`

**Body**: Stesso formato della creazione

---

## 🗑️ Elimina Configurazione

**DELETE** `/api/v1/import-configs/{config_id}`

**Response**: 204 No Content

---

## 🔍 Recupera Singola Configurazione

**GET** `/api/v1/import-configs/{config_id}`

---

## 💡 Use Case Workflow

### 1. Primo Upload Ritorno Gara
```typescript
// Utente compila manualmente sheet_name, colonne, ecc.
const uploadParams = {
  file: selectedFile,
  impresa: "Impresa ABC",
  sheetName: "Offerta",
  codeColumns: ["A", "B"],
  descriptionColumns: ["C"],
  priceColumn: "J",
  quantityColumn: "H",
  // ...
};

// Upload
await api.uploadRitorno(commessaId, uploadParams);

// Salva configurazione per riutilizzo
await api.createImportConfig({
  nome: "Formato Impresa ABC",
  impresa: "Impresa ABC",
  sheet_name: "Offerta",
  code_columns: "A,B",
  description_columns: "C",
  price_column: "J",
  quantity_column: "H",
  note: "Auto-saved da upload del 2025-01-12"
});
```

### 2. Upload Successivi
```typescript
// Lista configurazioni
const configs = await api.listImportConfigs();

// Mostra select con configurazioni salvate
<Select onChange={handleConfigSelect}>
  {configs.map(config => (
    <Option value={config.id}>{config.nome} ({config.impresa})</Option>
  ))}
</Select>

// Quando selezione una config, auto-compila i campi
const selectedConfig = configs.find(c => c.id === configId);
setSheetName(selectedConfig.sheet_name);
setCodeColumns(selectedConfig.code_columns.split(','));
// etc...
```

---

## 🎯 Campi della Configurazione

| Campo | Tipo | Descrizione | Esempio |
|-------|------|-------------|---------|
| `nome` | `string` | Nome descrittivo della configurazione | "Formato Impresa ABC" |
| `impresa` | `string?` | Nome impresa associata (opzionale) | "Impresa ABC S.r.l." |
| `sheet_name` | `string?` | Nome del foglio Excel | "Offerta" |
| `code_columns` | `string?` | Colonne codice (comma-separated) | "A,B" |
| `description_columns` | `string?` | Colonne descrizione | "C" |
| `price_column` | `string?` | Colonna prezzo unitario | "J" |
| `quantity_column` | `string?` | Colonna quantità fornita dall'impresa | "H" |
| `note` | `string?` | Note libere | "Usa sempre foglio 1" |
| `commessa_id` | `int?` | Commessa associata (null = globale) | `123` o `null` |

---

## 🔑 Configurazioni Globali vs Specifiche

### Globali (`commessa_id: null`)
- Visibili in tutte le commesse
- Utili per formati standard di imprese ricorrenti

### Specifiche (`commessa_id: 123`)
- Visibili solo nella commessa associata
- Utili per formati custom di una specifica gara

**Esempio Query**:
```
GET /api/v1/import-configs?commessa_id=123
```
Ritorna: configurazioni globali + configurazioni specifiche per commessa 123

---

## 🚀 TODO Frontend

1. **Aggiungere select "Usa configurazione salvata"** in `RoundUploadDialog`
2. **Auto-compilare campi** quando selezionata una config
3. **Bottone "Salva questa configurazione"** dopo upload riuscito
4. **Gestire configurazioni** da pagina Settings/Impostazioni

---

## 📦 Modello Database

```sql
CREATE TABLE import_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    impresa TEXT,
    sheet_name TEXT,
    code_columns TEXT,
    description_columns TEXT,
    price_column TEXT,
    quantity_column TEXT,
    note TEXT,
    commessa_id INTEGER REFERENCES commessa(id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

**Autore**: Claude Code
**Data**: 2025-01-12
**Status**: Backend implementato ✅ | Frontend da completare ⏳

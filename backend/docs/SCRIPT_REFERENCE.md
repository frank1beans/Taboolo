# Catalogo script backend

Documento generato automaticamente da `backend/scripts/generate_backend_docs.py`.
Totale script indicizzati: **234** distribuiti in 6 macro-cartelle.

## app (98 script)

### `app/__init__.py`
- **Linee**: 5
- **Descrizione**: FastAPI backend per l'importazione e gestione delle commesse Taboo.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/__init__.py`
- **Linee**: 8
- **Descrizione**: API package - HTTP layer for the application. Note: The main router has been moved to app.api.router for better organization. For backward compatibility, we re-export it here.
- **Dipendenze principali (1)**: `app.api.router.api_router`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/deps.py`
- **Linee**: 78
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (16)**: `app.core.security.InvalidTokenError`, `app.core.security.decode_access_token`, `app.core.settings`, `app.db.get_session`, `app.db.models.User`, `app.db.models.UserRole`, `fastapi.Cookie`, `fastapi.Depends`, `fastapi.HTTPException`, `fastapi.Request`, `fastapi.security.OAuth2PasswordBearer`, `fastapi.status`, ... (+4)
- **Classi**: nessuna.
- **Funzioni**:
  - `_extract_token(request: Request, bearer: str | None, cookie_token: str | None)` - Nessuna docstring.
  - `get_current_user(request: Request, token: Annotated[str | None, Depends(oauth2_scheme)], session: DBSession, access_cookie: str | None = Cookie(default=None, alias=settings.access_token_cookie_name, include_in_schema=False))` - Recupera l'utente autenticato a partire da un Bearer token JWT.
  - `require_role(allowed_roles: Sequence[UserRole])` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/middleware.py`
- **Linee**: 161
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (13)**: `__future__.annotations`, `app.core.security.InvalidTokenError`, `app.core.security.decode_access_token`, `app.core.settings`, `app.db.models.AuditLog`, `app.db.session.engine`, `fastapi.Request`, `fastapi.responses.JSONResponse`, `hashlib.sha256`, `logging`, `sqlmodel.Session`, `typing.Awaitable`, ... (+1)
- **Classi**: nessuna.
- **Funzioni**:
  - `async _extract_user_id(request: Request)` - Prova a recuperare l'ID utente dal token JWT presente nell'header Authorization Bearer o nel cookie di access token. Restituisce None se non è possibile estrarlo in modo sicuro.
  - `_is_https(request: Request)` - Determina se la richiesta è stata fatta via HTTPS, tenendo conto dei proxy (es. Render/NGINX) che usano X-Forwarded-Proto.
  - `async audit_and_security_middleware(request: Request, call_next: Callable[[Request], Awaitable])` - Middleware globale che: - verifica HTTPS (se richiesto) - limita la dimensione del payload - registra audit di ogni chiamata API v1
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/router.py`
- **Linee**: 19
- **Descrizione**: Main API router aggregator.
- **Dipendenze principali (9)**: `app.api.v1.endpoints.auth`, `app.api.v1.endpoints.commesse`, `app.api.v1.endpoints.computi`, `app.api.v1.endpoints.dashboard`, `app.api.v1.endpoints.import_configs`, `app.api.v1.endpoints.profile`, `app.api.v1.endpoints.settings`, `app.core.settings`, `fastapi.APIRouter`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/__init__.py`
- **Linee**: 1
- **Descrizione**: API v1 package.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/__init__.py`
- **Linee**: 4
- **Descrizione**: API v1 endpoints.
- **Dipendenze principali (7)**: `auth`, `commesse`, `computi`, `dashboard`, `import_configs`, `profile`, `settings`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/auth.py`
- **Linee**: 225
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 6 funzioni.
- **Dipendenze principali (32)**: `app.api.deps.DBSession`, `app.api.deps.get_current_user`, `app.core.security.InvalidTokenError`, `app.core.security.SlidingWindowRateLimiter`, `app.core.security.create_access_token`, `app.core.security.create_refresh_token`, `app.core.security.decode_refresh_token`, `app.core.security.enforce_rate_limit`, `app.core.security.hash_password`, `app.core.security.token_fingerprint`, `app.core.security.verify_password`, `app.core.settings`, ... (+20)
- **Classi**: nessuna.
- **Funzioni**:
  - `register_user(session: DBSession, payload: UserCreate = Body(...))` - Nessuna docstring.
  - `_persist_refresh_token(session: Session, user: User, refresh_token: str, replaced_by: RefreshToken | None = None)` - Nessuna docstring.
  - `_set_auth_cookies(response: Response, access_token: str, refresh_token: str)` - Nessuna docstring.
  - `login(request: Request, response: Response, session: DBSession, credentials: LoginRequest = Body(...))` - Nessuna docstring.
  - `refresh_token(request: Request, response: Response, session: DBSession)` - Nessuna docstring.
  - `logout(request: Request, response: Response, session: DBSession, user: User = Depends(get_current_user))` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/commesse.py`
- **Linee**: 1336
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 38 funzioni.
- **Dipendenze principali (81)**: `app.api.deps.DBSession`, `app.api.deps.UserRole`, `app.api.deps.get_current_user`, `app.api.deps.require_role`, `app.core.security.SlidingWindowRateLimiter`, `app.core.security.enforce_rate_limit`, `app.core.settings`, `app.db.models.Commessa`, `app.db.models.CommessaPreferences`, `app.db.models.CommessaPreferencesBase`, `app.db.models.CommessaPreferencesRead`, `app.db.models.Computo`, ... (+69)
- **Classi**: nessuna.
- **Funzioni**:
  - `_parse_column_list(value: str | None)` - Normalizza una stringa di colonne tipo 'A,B,C' in lista maiuscola.
  - `_ensure_excel_file(upload: UploadFile)` - Nessuna docstring.
  - `_get_commessa_or_404(session: DBSession, commessa_id: int)` - Nessuna docstring.
  - `_parse_optional_commessa_id(raw: int | str | None, field_name: str = 'commessa_id')` - Accetta ID commessa anche come stringa vuota e lo normalizza a int o None.
  - `_ensure_six_or_xml_file(file: UploadFile)` - Nessuna docstring.
  - `list_price_catalog(session: DBSession, search: str | None = Query(default=None, description='Filtro testuale su codice, descrizione e WBS.'), commessa_id: int | str | None = Query(default=None, description='Limita i risultati alla commessa indicata.'), business_unit: str | None = Query(default=None, description='Filtra per Business Unit esatta.'))` - Elenco prezzi aggregato di tutte le commesse.
  - `semantic_search_price_catalog(session: DBSession, query: str = Query(..., description='Testo da cercare nel catalogo prezzi', min_length=2), commessa_id: int | str | None = Query(default=None, description='Limita la ricerca alla commessa indicata.'), top_k: int = Query(default=50, ge=1, le=200, description='Numero massimo di risultati da restituire.'), min_score: float = Query(default=0.2, ge=-1.0, le=1.0, description='Soglia minima di similarità coseno per mostrare una voce.'))` - Nessuna docstring.
  - `list_price_catalog_summary(session: DBSession)` - Riepilogo del catalogo prezzi raggruppato per business unit e commessa.
  - `list_commesse(session: DBSession)` - Nessuna docstring.
  - `create_commessa(payload: CommessaCreate, session: DBSession)` - Nessuna docstring.
  - `get_commessa(commessa_id: int, session: DBSession)` - Nessuna docstring.
  - `update_commessa(commessa_id: int, payload: CommessaCreate, session: DBSession)` - Nessuna docstring.
  - `delete_commessa(commessa_id: int, session: DBSession)` - Nessuna docstring.
  - `async import_commessa_bundle(request: Request, session: DBSession, file: UploadFile = File(...), overwrite: bool = Query(False, description='Sovrascrive la commessa esistente con lo stesso codice, se presente.'), current_user: User = Depends(get_current_user))` - Nessuna docstring.
  - `export_commessa_bundle(commessa_id: int, session: DBSession, request: Request, current_user: User = Depends(get_current_user))` - Nessuna docstring.
  - `get_commessa_wbs(commessa_id: int, session: DBSession)` - Nessuna docstring.
  - `async upload_wbs_structure(commessa_id: int, session: DBSession, file: UploadFile = File(...))` - Nessuna docstring.
  - `async update_wbs_structure(commessa_id: int, session: DBSession, file: UploadFile = File(...))` - Nessuna docstring.
  - `list_wbs_visibility(commessa_id: int, session: DBSession)` - Nessuna docstring.
  - `update_wbs_visibility(commessa_id: int, session: DBSession, payload: List[WbsVisibilityUpdateSchema] = Body(default=[]))` - Nessuna docstring.
  - `async inspect_commessa_six(commessa_id: int, request: Request, session: DBSession, file: UploadFile = File(...))` - Nessuna docstring.
  - `async preview_commessa_six(commessa_id: int, request: Request, session: DBSession, file: UploadFile = File(...))` - Nessuna docstring.
  - `async import_commessa_six(commessa_id: int, request: Request, session: DBSession, file: UploadFile = File(...), preventivo_id: str | None = Form(default=None), compute_embeddings: bool = Form(default=False), extract_properties: bool = Form(default=False))` - Nessuna docstring.
  - `get_commessa_price_catalog(commessa_id: int, session: DBSession, used_only: bool = Query(False, description='Se true, restituisce solo le voci realmente utilizzate nel computo progetto della commessa.'))` - Recupera l'elenco prezzi associato alla commessa.
  - `get_commessa_analisi(commessa_id: int, session: DBSession, round_number: int | None = Query(None, alias='round'), impresa: str | None = None)` - Nessuna docstring.
  - `get_commessa_confronto(commessa_id: int, session: DBSession)` - Nessuna docstring.
  - `get_commessa_wbs6_dettaglio(commessa_id: int, wbs6_id: str, session: DBSession, round_number: int | None = Query(None, alias='round'), impresa: str | None = None)` - Nessuna docstring.
  - `get_commessa_trend_round(commessa_id: int, session: DBSession, impresa: str | None = None)` - Nessuna docstring.
  - `get_commessa_trend_round_legacy(commessa_id: int, session: DBSession, impresa: str | None = None)` - Nessuna docstring.
  - `get_commessa_heatmap_competitivita(commessa_id: int, session: DBSession, round_number: int | None = Query(None, alias='round'))` - Nessuna docstring.
  - `get_commessa_heatmap_competitivita_legacy(commessa_id: int, session: DBSession, round_number: int | None = Query(None, alias='round'))` - Nessuna docstring.
  - `async upload_computo_progetto(commessa_id: int, request: Request, session: DBSession, file: UploadFile = File(...))` - Nessuna docstring.
  - `async upload_ritorno_gara(commessa_id: int, request: Request, session: DBSession, impresa: str = Form(..., min_length=1), mode: str | None = Form(default=None), round_mode: str = Form('auto'), round_number: int | None = Form(default=None), sheet_name: str | None = Form(default=None), code_columns: str | None = Form(default=None), description_columns: str | None = Form(default=None), price_column: str | None = Form(default=None), quantity_column: str | None = Form(default=None), progressive_column: str | None = Form(default=None), file: UploadFile = File(...))` - Nessuna docstring.
  - `async upload_ritorni_batch_single_file(commessa_id: int, request: Request, session: DBSession, file: UploadFile = File(...), imprese_config: str = Form(..., description='JSON array con colonne prezzo/quantità per impresa'), mode: str | None = Form(default=None), sheet_name: str | None = Form(default=None), code_columns: str | None = Form(default=None), description_columns: str | None = Form(default=None), progressive_column: str | None = Form(default=None))` - Importa ritorni di gara per più imprese partendo da un unico file Excel.
  - `update_manual_offer_price(commessa_id: int, payload: ManualPriceUpdateRequest, session: DBSession)` - Nessuna docstring.
  - `delete_computo(commessa_id: int, computo_id: int, session: DBSession)` - Nessuna docstring.
  - `get_commessa_preferences(commessa_id: int, session: DBSession)` - Ottieni le preferenze della commessa. Crea automaticamente se non esistono.
  - `update_commessa_preferences(commessa_id: int, payload: CommessaPreferencesBase, session: DBSession)` - Aggiorna le preferenze della commessa.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/computi.py`
- **Linee**: 21
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 1 funzioni.
- **Dipendenze principali (7)**: `app.api.deps.DBSession`, `app.api.deps.UserRole`, `app.api.deps.require_role`, `app.schemas.ComputoWbsSummary`, `app.services.WbsAnalysisService`, `fastapi.APIRouter`, `fastapi.HTTPException`
- **Classi**: nessuna.
- **Funzioni**:
  - `get_computo_wbs(computo_id: int, session: DBSession)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/dashboard.py`
- **Linee**: 18
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 1 funzioni.
- **Dipendenze principali (6)**: `app.api.deps.DBSession`, `app.api.deps.UserRole`, `app.api.deps.require_role`, `app.schemas.DashboardStatsSchema`, `app.services.analysis.dashboard.DashboardService`, `fastapi.APIRouter`
- **Classi**: nessuna.
- **Funzioni**:
  - `get_dashboard_stats(session: DBSession)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/import_configs.py`
- **Linee**: 95
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 5 funzioni.
- **Dipendenze principali (13)**: `app.api.deps.DBSession`, `app.api.deps.UserRole`, `app.api.deps.require_role`, `app.db.models.ImportConfig`, `app.db.models.ImportConfigBase`, `app.db.models.ImportConfigRead`, `fastapi.APIRouter`, `fastapi.HTTPException`, `fastapi.Query`, `fastapi.status`, `sqlalchemy.select`, `typing.List`, ... (+1)
- **Classi**: nessuna.
- **Funzioni**:
  - `list_import_configs(session: DBSession, commessa_id: Optional[int] = Query(default=None, description='Filtra per commessa (null = globali)'))` - Elenca tutte le configurazioni import salvate.
  - `create_import_config(payload: ImportConfigBase, session: DBSession, commessa_id: Optional[int] = Query(default=None, description='Commessa associata (null = globale)'))` - Crea una nuova configurazione import.
  - `get_import_config(config_id: int, session: DBSession)` - Recupera una configurazione import specifica.
  - `update_import_config(config_id: int, payload: ImportConfigBase, session: DBSession)` - Aggiorna una configurazione import esistente.
  - `delete_import_config(config_id: int, session: DBSession)` - Elimina una configurazione import.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/profile.py`
- **Linee**: 74
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (14)**: `app.api.deps.DBSession`, `app.api.deps.UserRole`, `app.api.deps.get_current_user`, `app.api.deps.require_role`, `app.domain.users.models.User`, `app.domain.users.models.UserProfile`, `app.schemas.ProfileUpdate`, `app.schemas.UserProfileRead`, `app.schemas.UserRead`, `app.services.record_audit_log`, `fastapi.APIRouter`, `fastapi.Depends`, ... (+2)
- **Classi**: nessuna.
- **Funzioni**:
  - `get_me(current_user: User = Depends(get_current_user))` - Nessuna docstring.
  - `get_profile(session: DBSession, current_user: User = Depends(get_current_user))` - Nessuna docstring.
  - `update_profile(request: Request, payload: ProfileUpdate, session: DBSession, current_user: User = Depends(get_current_user))` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/endpoints/settings.py`
- **Linee**: 923
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 28 funzioni.
- **Dipendenze principali (49)**: `app.api.deps.DBSession`, `app.api.deps.UserRole`, `app.api.deps.require_role`, `app.db.models_wbs.Impresa`, `app.domain.catalog.models.PriceListItem`, `app.domain.catalog.models.PriceListOffer`, `app.domain.catalog.models.PropertyFeedback`, `app.domain.catalog.models.PropertyLexicon`, `app.domain.catalog.models.PropertyOverride`, `app.domain.catalog.models.PropertyPattern`, `app.domain.computi.models.Computo`, `app.domain.computi.models.ComputoTipo`, ... (+37)
- **Classi**: nessuna.
- **Funzioni**:
  - `_serialize_settings(settings: Settings)` - Nessuna docstring.
  - `_configure_nlp_service(settings: Settings)` - Nessuna docstring.
  - `_warmup_nlp_model()` - Nessuna docstring.
  - `get_settings(session: DBSession)` - Recupera le impostazioni globali (singola riga).
  - `update_settings(payload: SettingsUpdate, session: DBSession)` - Aggiorna le impostazioni globali.
  - `regenerate_embeddings(session: DBSession, commessa_id: Optional[int] = Query(default=None, description='ID della commessa per cui rigenerare gli embedding. Se non specificato, rigenera per tutte le commesse.'))` - Rigenera gli embedding semantici per il catalogo prezzi di una commessa o di tutte le commesse.
  - `_load_property_schemas()` - Nessuna docstring.
  - `_extract_properties_payload(payload: ExtractRequest)` - Nessuna docstring.
  - `get_property_schemas_public()` - Schema proprietà accessibile senza autenticazione.
  - `extract_properties_public(payload: ExtractRequest)` - Estrae proprietà (public) tramite regole deterministiche.
  - `get_property_schemas_private()` - Schema proprietà autenticato (stesso output del public).
  - `extract_properties_private(payload: ExtractRequest)` - Estrazione proprietà autenticata (stesso comportamento del public).
  - `regenerate_properties(session: DBSession, commessa_id: Optional[int] = Query(default=None, description='ID della commessa per cui rigenerare le proprieta. Se non specificato, rigenera per tutte le commesse.'))` - Ricalcola le proprieta estratte per le voci elenco prezzi (pipeline ibrida unica).
  - `_update_fields(model, updates: dict)` - Nessuna docstring.
  - `list_property_lexicon(session: DBSession)` - Nessuna docstring.
  - `create_property_lexicon(payload: PropertyLexiconCreate, session: DBSession)` - Nessuna docstring.
  - `update_property_lexicon(lex_id: int, payload: PropertyLexiconUpdate, session: DBSession)` - Nessuna docstring.
  - `delete_property_lexicon(lex_id: int, session: DBSession)` - Nessuna docstring.
  - `list_property_patterns(session: DBSession)` - Nessuna docstring.
  - `create_property_pattern(payload: PropertyPatternCreate, session: DBSession)` - Nessuna docstring.
  - `update_property_pattern(pattern_id: int, payload: PropertyPatternUpdate, session: DBSession)` - Nessuna docstring.
  - `delete_property_pattern(pattern_id: int, session: DBSession)` - Nessuna docstring.
  - `get_property_override(item_id: int, session: DBSession)` - Nessuna docstring.
  - `upsert_property_override(item_id: int, payload: PropertyOverridePayload, session: DBSession)` - Nessuna docstring.
  - `create_property_feedback(item_id: int, payload: PropertyFeedbackPayload, session: DBSession)` - Nessuna docstring.
  - `_sanitize_impresa_label(label: str | None)` - Nessuna docstring.
  - `_get_or_create_impresa(session: DBSession, label: str | None)` - Nessuna docstring.
  - `normalize_imprese(session: DBSession, commessa_id: Optional[int] = Query(default=None, description='ID della commessa per cui normalizzare le imprese. Se non specificato, normalizza tutte.'))` - Uniforma le etichette delle imprese su tutti i ritorni (rimuove suffissi tipo '(2)' e riallinea gli offer).
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/api/v1/schemas/__init__.py`
- **Linee**: 1
- **Descrizione**: API v1 schemas (Request/Response DTOs).
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/core/__init__.py`
- **Linee**: 3
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (1)**: `config.settings`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/core/config.py`
- **Linee**: 218
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 1 funzioni.
- **Dipendenze principali (8)**: `pathlib.Path`, `pydantic.Field`, `pydantic.field_validator`, `pydantic.model_validator`, `pydantic_settings.BaseSettings`, `pydantic_settings.SettingsConfigDict`, `secrets`, `sys`
- **Classi**:
  - `Settings` (bases: BaseSettings) - Configurazione centrale dell'applicazione. Metodi: `effective_database_url`.
- **Funzioni**:
  - `_default_storage_root()` - Return the storage folder depending on the runtime (source vs PyInstaller).
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/core/logging.py`
- **Linee**: 35
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 1 funzioni.
- **Dipendenze principali (6)**: `__future__.annotations`, `app.core.settings`, `json`, `logging`, `logging.LogRecord`, `typing.Any`
- **Classi**:
  - `JsonFormatter` (bases: logging.Formatter) - Nessuna docstring. Metodi: `format`.
- **Funzioni**:
  - `configure_logging()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/core/security.py`
- **Linee**: 113
- **Descrizione**: Modulo senza docstring. Contiene 2 classi e 9 funzioni.
- **Dipendenze principali (16)**: `__future__.annotations`, `app.core.settings`, `datetime.datetime`, `datetime.timedelta`, `datetime.timezone`, `fastapi.HTTPException`, `fastapi.status`, `hashlib.sha256`, `jose.JWTError`, `jose.jwt`, `passlib.context.CryptContext`, `threading.Lock`, ... (+4)
- **Classi**:
  - `InvalidTokenError` (bases: Exception) - Eccezione applicativa per token non valido o scaduto. Metodi: nessun metodo pubblico.
  - `SlidingWindowRateLimiter` (bases: object) - Rate limiting in-memory con finestra mobile (thread-safe). Metodi: `hit`.
- **Funzioni**:
  - `hash_password(plain_password: str)` - Nessuna docstring.
  - `verify_password(plain_password: str, hashed_password: str)` - Nessuna docstring.
  - `_build_payload(subject: str, email: str, role: str, expires_delta: timedelta)` - Nessuna docstring.
  - `create_access_token(*, subject: str, email: str, role: str, expires_minutes: int | None = None)` - Nessuna docstring.
  - `create_refresh_token(*, subject: str, email: str, role: str, expires_minutes: int | None = None)` - Nessuna docstring.
  - `decode_access_token(token: str)` - Nessuna docstring.
  - `decode_refresh_token(token: str)` - Nessuna docstring.
  - `token_fingerprint(token: str)` - Nessuna docstring.
  - `enforce_rate_limit(limiter: SlidingWindowRateLimiter, key: str)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/db/__init__.py`
- **Linee**: 6
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (5)**: `init_db.init_db`, `models`, `models_wbs`, `session.engine`, `session.get_session`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/db/init_db.py`
- **Linee**: 133
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 5 funzioni.
- **Dipendenze principali (13)**: `app.core.security.hash_password`, `app.core.settings`, `app.db.models.User`, `app.db.models.UserProfile`, `app.db.models.UserRole`, `app.db.session.engine`, `logging`, `sqlalchemy.exc.SQLAlchemyError`, `sqlalchemy.inspect`, `sqlalchemy.text`, `sqlmodel.SQLModel`, `sqlmodel.Session`, ... (+1)
- **Classi**: nessuna.
- **Funzioni**:
  - `init_db()` - Crea tutte le tabelle e applica gli aggiornamenti necessari.
  - `_ensure_settings_columns()` - Aggiunge le nuove colonne NLP alla tabella settings se mancanti.
  - `_ensure_price_list_item_columns()` - Aggiunge colonne mancanti su price_list_item (preventivo_id, created_at, updated_at).
  - `_healthcheck()` - Verifica la raggiungibilità del DB (ISO A.17).
  - `_ensure_seed_admin()` - Crea un utente amministratore predefinito per ambienti demo/sviluppo.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/db/models.py`
- **Linee**: 101
- **Descrizione**: Database models - Compatibility layer. IMPORTANT: This file now serves as a compatibility layer for backward compatibility. All models have been moved to their respective domain packages: - Users & Auth: app.domain.users.models - Commesse: app.domain.commesse.models - Computi & Voci: app.domain.computi.models -...
- **Dipendenze principali (33)**: `__future__.annotations`, `app.db.models_wbs.*`, `app.domain.catalog.models.PriceListItem`, `app.domain.catalog.models.PriceListOffer`, `app.domain.catalog.models.PropertyFeedback`, `app.domain.catalog.models.PropertyLexicon`, `app.domain.catalog.models.PropertyOverride`, `app.domain.catalog.models.PropertyPattern`, `app.domain.commesse.models.Commessa`, `app.domain.commesse.models.CommessaBase`, `app.domain.commesse.models.CommessaPreferences`, `app.domain.commesse.models.CommessaPreferencesBase`, ... (+21)
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/db/models_wbs.py`
- **Linee**: 255
- **Descrizione**: Modulo senza docstring. Contiene 9 classi e 0 funzioni.
- **Dipendenze principali (7)**: `__future__.annotations`, `datetime.datetime`, `enum.Enum`, `sqlmodel.Field`, `sqlmodel.SQLModel`, `sqlmodel.UniqueConstraint`, `typing.Optional`
- **Classi**:
  - `WbsSpaziale` (bases: SQLModel) - Nodo spaziale della WBS (livelli 1-5) normalizzato per commessa. Metodi: nessun metodo pubblico.
  - `Wbs6` (bases: SQLModel) - Nodo analitico WBS6 (codice A### obbligatorio). Metodi: nessun metodo pubblico.
  - `Wbs7` (bases: SQLModel) - Nodo opzionale WBS7 (sotto-articolazione della WBS6). Metodi: nessun metodo pubblico.
  - `WbsVisibilityKind` (bases: str, Enum) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsVisibility` (bases: SQLModel) - Preferenze di visibilità per i raggruppatori WBS (livelli 1-7). Metodi: nessun metodo pubblico.
  - `Impresa` (bases: SQLModel) - Anagrafica imprese normalizzata per offerte e round. Metodi: nessun metodo pubblico.
  - `Voce` (bases: SQLModel) - Voce analitica normalizzata. Ogni voce appartiene ad una commessa e deve avere sempre una WBS6 di riferimento. La WBS7 è opzionale (se esiste nel computo originale). Metodi: nessun metodo pubblico.
  - `VoceProgetto` (bases: SQLModel) - Quantità e prezzi di progetto associati ad una voce normalizzata. Metodi: nessun metodo pubblico.
  - `VoceOfferta` (bases: SQLModel) - Importi offerta delle imprese per singola voce. Ogni riga identifica una voce, un computo (ritorno), un round e un'impresa. Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/db/session.py`
- **Linee**: 53
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 2 funzioni.
- **Dipendenze principali (7)**: `app.core.settings`, `contextlib.contextmanager`, `sqlalchemy.engine.make_url`, `sqlalchemy.text`, `sqlmodel.Session`, `sqlmodel.create_engine`, `typing.Generator`
- **Classi**: nessuna.
- **Funzioni**:
  - `get_session()` - Nessuna docstring.
  - `session_scope()` - Context manager esplicito per operazioni di servizio.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/__init__.py`
- **Linee**: 1
- **Descrizione**: Domain layer - Business logic and models.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/catalog/__init__.py`
- **Linee**: 18
- **Descrizione**: Catalog domain (price lists and products).
- **Dipendenze principali (6)**: `models.PriceListItem`, `models.PriceListOffer`, `models.PropertyFeedback`, `models.PropertyLexicon`, `models.PropertyOverride`, `models.PropertyPattern`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/catalog/models.py`
- **Linee**: 142
- **Descrizione**: Catalog domain models (price lists, products, properties).
- **Dipendenze principali (9)**: `__future__.annotations`, `datetime.datetime`, `sqlalchemy.Column`, `sqlalchemy.JSON`, `sqlmodel.Field`, `sqlmodel.SQLModel`, `sqlmodel.UniqueConstraint`, `typing.Any`, `typing.Optional`
- **Classi**:
  - `PriceListItem` (bases: SQLModel) - Voce dell'elenco prezzi importata da STR Vision, arricchita con metadati. Metodi: nessun metodo pubblico.
  - `PriceListOffer` (bases: SQLModel) - Prezzi offerti dalle imprese per singola voce di elenco prezzi. Metodi: nessun metodo pubblico.
  - `PropertyLexicon` (bases: SQLModel) - Dizionario gestibile via UI per brand/materiali/modelli/keyword/regex. Metodi: nessun metodo pubblico.
  - `PropertyPattern` (bases: SQLModel) - Pattern o regex aggiuntivi per una proprietà specifica. Metodi: nessun metodo pubblico.
  - `PropertyOverride` (bases: SQLModel) - Override manuali per le proprietà estratte di una voce di elenco prezzi. Metodi: nessun metodo pubblico.
  - `PropertyFeedback` (bases: SQLModel) - Feedback puntuali per training futuro (span opzionale). Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/catalog/price_service.py`
- **Linee**: 205
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (14)**: `__future__.annotations`, `app.core.config.settings`, `app.db.models.Commessa`, `app.db.models.PriceListItem`, `app.services.nlp.embedding_service.semantic_embedding_service`, `app.services.nlp.property_extraction.extract_properties_auto`, `logging`, `sqlalchemy.exc.OperationalError`, `sqlite3`, `sqlmodel.Session`, `time`, `typing.Any`, ... (+2)
- **Classi**:
  - `PriceCatalogService` (bases: object) - Gestisce la persistenza delle voci di elenco prezzi multi-commessa. Metodi: `replace_catalog`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/catalog/search_service.py`
- **Linee**: 327
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 4 funzioni.
- **Dipendenze principali (16)**: `app.api.deps.DBSession`, `app.db.models.Commessa`, `app.db.models.PriceListItem`, `app.services.nlp.extract_construction_attributes`, `app.services.price_list_faiss_service`, `app.services.semantic_embedding_service`, `app.services.serialization_service.collect_price_list_offers`, `app.services.serialization_service.collect_project_quantities`, `app.services.serialization_service.serialize_price_list_item`, `logging`, `numpy`, `re`, ... (+4)
- **Classi**: nessuna.
- **Funzioni**:
  - `tokenize_query(text: str)` - Nessuna docstring.
  - `lexical_boost(tokens: set[str], item: PriceListItem)` - Nessuna docstring.
  - `attribute_boost(item_attrs: dict, query_attrs: dict)` - Calcola boost per match attributi strutturati.
  - `search_catalog(session: DBSession, query: str, commessa_id: int | None = None, top_k: int = 50, min_score: float = 0.2)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/commesse/__init__.py`
- **Linee**: 4
- **Descrizione**: Commesse domain.
- **Dipendenze principali (5)**: `models.Commessa`, `models.CommessaBase`, `models.CommessaPreferences`, `models.CommessaRead`, `models.CommessaStato`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/commesse/bundle_service.py`
- **Linee**: 5
- **Descrizione**: Domain-level compatibility wrapper for bundle import/export logic.
- **Dipendenze principali (2)**: `app.services.commessa_bundle.CommessaBundleService`, `app.services.commessa_bundle.commessa_bundle_service`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/commesse/models.py`
- **Linee**: 83
- **Descrizione**: Commesse domain models.
- **Dipendenze principali (9)**: `__future__.annotations`, `datetime.datetime`, `enum.Enum`, `sqlalchemy.Column`, `sqlalchemy.JSON`, `sqlmodel.Field`, `sqlmodel.SQLModel`, `typing.Any`, `typing.Optional`
- **Classi**:
  - `CommessaStato` (bases: str, Enum) - Stati possibili per una commessa. Metodi: nessun metodo pubblico.
  - `CommessaBase` (bases: SQLModel) - Base model per Commessa con campi comuni. Metodi: nessun metodo pubblico.
  - `Commessa` (bases: CommessaBase) - Commessa (progetto) - entità principale del dominio. Metodi: nessun metodo pubblico.
  - `CommessaRead` (bases: CommessaBase) - Schema di lettura per Commessa. Metodi: nessun metodo pubblico.
  - `CommessaPreferencesBase` (bases: SQLModel) - Preferenze e impostazioni specifiche per la commessa. Metodi: nessun metodo pubblico.
  - `CommessaPreferences` (bases: CommessaPreferencesBase) - Tabella preferenze commessa. Metodi: nessun metodo pubblico.
  - `CommessaPreferencesRead` (bases: CommessaPreferencesBase) - Schema di lettura per CommessaPreferences. Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/commesse/service.py`
- **Linee**: 9
- **Descrizione**: Domain-level wrapper that forwards to the application service implementation. This keeps the planned import path ``app.domain.commesse.service`` working without duplicating the logic that actually lives in ``app.services.commesse``.
- **Dipendenze principali (1)**: `app.services.commesse.CommesseService`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/computi/__init__.py`
- **Linee**: 26
- **Descrizione**: Computi domain.
- **Dipendenze principali (10)**: `models.Computo`, `models.ComputoBase`, `models.ComputoRead`, `models.ComputoTipo`, `models.ImportConfig`, `models.ImportConfigBase`, `models.ImportConfigRead`, `models.VoceBase`, `models.VoceComputo`, `models.VoceRead`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/computi/models.py`
- **Linee**: 127
- **Descrizione**: Computi domain models.
- **Dipendenze principali (9)**: `__future__.annotations`, `datetime.datetime`, `enum.Enum`, `sqlalchemy.Column`, `sqlalchemy.JSON`, `sqlmodel.Field`, `sqlmodel.SQLModel`, `typing.Any`, `typing.Optional`
- **Classi**:
  - `ComputoTipo` (bases: str, Enum) - Tipo di computo metrico. Metodi: nessun metodo pubblico.
  - `ComputoBase` (bases: SQLModel) - Base model per Computo con campi comuni. Metodi: nessun metodo pubblico.
  - `Computo` (bases: ComputoBase) - Computo metrico - elenco prezzi e quantità per una commessa. Metodi: nessun metodo pubblico.
  - `ComputoRead` (bases: ComputoBase) - Schema di lettura per Computo. Metodi: nessun metodo pubblico.
  - `VoceBase` (bases: SQLModel) - Base model per singola voce di computo. Metodi: nessun metodo pubblico.
  - `VoceComputo` (bases: VoceBase) - Singola voce (riga) di un computo metrico. Metodi: nessun metodo pubblico.
  - `VoceRead` (bases: VoceBase) - Schema di lettura per VoceComputo. Metodi: nessun metodo pubblico.
  - `ImportConfigBase` (bases: SQLModel) - Configurazione salvata per import ritorni di gara. Metodi: nessun metodo pubblico.
  - `ImportConfig` (bases: ImportConfigBase) - Configurazione import salvata nel database. Metodi: nessun metodo pubblico.
  - `ImportConfigRead` (bases: ImportConfigBase) - Schema di lettura per ImportConfig. Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/settings/__init__.py`
- **Linee**: 4
- **Descrizione**: Global settings domain.
- **Dipendenze principali (3)**: `models.Settings`, `models.SettingsBase`, `models.SettingsRead`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/settings/models.py`
- **Linee**: 47
- **Descrizione**: Global settings models.
- **Dipendenze principali (5)**: `__future__.annotations`, `datetime.datetime`, `sqlmodel.Field`, `sqlmodel.SQLModel`, `typing.Optional`
- **Classi**:
  - `SettingsBase` (bases: SQLModel) - Base model per settings globali dell'applicazione. Metodi: nessun metodo pubblico.
  - `Settings` (bases: SettingsBase) - Settings globali salvati nel database. Metodi: nessun metodo pubblico.
  - `SettingsRead` (bases: SettingsBase) - Schema di lettura per Settings. Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/users/__init__.py`
- **Linee**: 4
- **Descrizione**: Users domain.
- **Dipendenze principali (3)**: `models.User`, `models.UserProfile`, `models.UserRole`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/users/models.py`
- **Linee**: 75
- **Descrizione**: User domain models.
- **Dipendenze principali (9)**: `__future__.annotations`, `datetime.datetime`, `enum.Enum`, `sqlalchemy.Column`, `sqlalchemy.JSON`, `sqlmodel.Field`, `sqlmodel.SQLModel`, `typing.Any`, `typing.Optional`
- **Classi**:
  - `UserRole` (bases: str, Enum) - User roles for authorization. Metodi: nessun metodo pubblico.
  - `User` (bases: SQLModel) - User model for authentication and authorization. Metodi: nessun metodo pubblico.
  - `UserProfile` (bases: SQLModel) - Extended user profile with preferences and settings. Metodi: nessun metodo pubblico.
  - `RefreshToken` (bases: SQLModel) - Refresh token for JWT authentication. Metodi: nessun metodo pubblico.
  - `AuditLog` (bases: SQLModel) - Audit log for tracking user actions. Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/wbs/__init__.py`
- **Linee**: 1
- **Descrizione**: WBS (Work Breakdown Structure) domain.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/wbs/models.py`
- **Linee**: 3
- **Descrizione**: WBS domain models.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/wbs/wbs_import.py`
- **Linee**: 5
- **Descrizione**: Domain-level compatibility wrapper for WBS import services.
- **Dipendenze principali (1)**: `app.services.wbs_import.*`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/wbs/wbs_predictor.py`
- **Linee**: 5
- **Descrizione**: Domain-level compatibility wrapper for WBS predictor utilities.
- **Dipendenze principali (1)**: `app.services.wbs_predictor.*`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/domain/wbs/wbs_visibility.py`
- **Linee**: 5
- **Descrizione**: Domain-level compatibility wrapper for WBS visibility services.
- **Dipendenze principali (1)**: `app.services.wbs_visibility.*`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/excel/__init__.py`
- **Linee**: 3
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (4)**: `parser.ParsedComputo`, `parser.ParsedVoce`, `parser.ParsedWbsLevel`, `parser.parse_computo_excel`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/excel/parser.py`
- **Linee**: 937
- **Descrizione**: Modulo senza docstring. Contiene 3 classi e 25 funzioni.
- **Dipendenze principali (12)**: `__future__.annotations`, `dataclasses.dataclass`, `decimal.Decimal`, `decimal.ROUND_HALF_UP`, `logging`, `openpyxl.load_workbook`, `pathlib.Path`, `re`, `typing.Any`, `typing.Iterable`, `typing.Sequence`, `unicodedata`
- **Classi**:
  - `ParsedWbsLevel` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ParsedVoce` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ParsedComputo` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `parse_computo_excel(path: Path, sheet_name: str | None = None, *, price_column: str | None = None, quantity_column: str | None = None)` - Nessuna docstring.
  - `_parse_computo_estimativo(titolo: str | None, rows: list[list], *, price_column: str | None = None, quantity_column: str | None = None)` - Nessuna docstring.
  - `_parse_lista_lavorazioni(titolo: str | None, rows: list[list])` - Nessuna docstring.
  - `_ensure_wbs_hierarchy(levels: list[ParsedWbsLevel], codice: str | None, descrizione: str | None, *, level6_description: str | None = None)` - Garantisce che la gerarchia WBS si fermi alla WBS6 (formato A###). Tutte le voci con codice tipo A001.010 o A001.010.001 vengono assegnate alla WBS6 base (A001).
  - `_sanitize_level6_description(description: str | None, base_code: str | None)` - Nessuna docstring.
  - `_pick_sheet(workbook, requested: str)` - Nessuna docstring.
  - `_iter_rows(ws, max_rows: int | None = None)` - Nessuna docstring.
  - `_is_lista_lavorazioni(rows: list[list])` - Nessuna docstring.
  - `_find_header_row(rows: list[list])` - Nessuna docstring.
  - `_find_header_row_lista(rows: list[list])` - Nessuna docstring.
  - `_normalize_header(value)` - Nessuna docstring.
  - `_row_is_empty(row: Sequence)` - Nessuna docstring.
  - `_is_total_row(row: Sequence)` - Nessuna docstring.
  - `_is_section_row(row: Sequence)` - Nessuna docstring.
  - `_is_item_row(row: Sequence)` - Nessuna docstring.
  - `_sanitize_code(value)` - Nessuna docstring.
  - `_generate_fallback_code(progressivo: int | None, descrizione: str | None, ordine: int)` - Nessuna docstring.
  - `_extract_description(cell_value, code: str | None)` - Nessuna docstring.
  - `_guess_wbs_level(code: str | None, current: Sequence[ParsedWbsLevel | None])` - Nessuna docstring.
  - `_collect_measure_rows(rows: list[list], start_index: int, *, quantita_idx: int = 9, prezzo_idx: int = 10, importo_idx: int = 11, unita_idx: int | None = None, progressivo_idx: int = 1, codice_idx: int = 2, descr_idx: int = 3)` - Nessuna docstring.
  - `_sanitize_text(value)` - Nessuna docstring.
  - `_row_has_detrazione(row: Sequence)` - Riconosce righe di misura marcate come detrazioni.
  - `_to_float(value, decimals: int = 2)` - Converte un valore in float, arrotondando al numero di decimali specificato.
  - `_to_int(value)` - Nessuna docstring.
  - `_slugify(value: str)` - Nessuna docstring.
- **Costanti dichiarate (3)**: `MAX_WBS_LEVELS`, `_WBS6_PATTERN`, `_WBS7_PATTERN`
- **Entry point CLI**: Assente.

### `app/main.py`
- **Linee**: 131
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (17)**: `app.api.middleware.audit_and_security_middleware`, `app.api.router.api_router`, `app.core.logging.configure_logging`, `app.core.settings`, `app.db.init_db`, `app.db.session.engine`, `app.domain.settings.models.Settings`, `app.services.nlp.embedding_service.semantic_embedding_service`, `app.services.nlp.property_extraction.init_model`, `app.services.nlp.property_extraction.init_property_prototypes`, `contextlib.asynccontextmanager`, `dotenv.load_dotenv`, ... (+5)
- **Classi**: nessuna.
- **Funzioni**:
  - `_build_cors_origins()` - Normalizza e applica politiche di sicurezza CORS in modo centralizzato.
  - `async lifespan(app: FastAPI)` - Lifespan centralizza logica di startup/shutdown e viene eseguito una sola volta per process (non ad ogni import del modulo).
  - `create_app()` - Factory dell'app FastAPI. Nota architetturale: l'entrypoint espone i router definiti in app.api.v1.endpoints, utilizza SQLModel (app.domain.*/models) con engine condiviso in app.db.session e carica le configurazioni da app.core.settings. I servizi applicativi sono organizzati nel package app.services (orchestration)...
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/schemas.py`
- **Linee**: 835
- **Descrizione**: Modulo senza docstring. Contiene 90 classi e 0 funzioni.
- **Dipendenze principali (12)**: `app.db.models.CommessaStato`, `app.db.models.ComputoTipo`, `app.db.models.SettingsRead`, `app.db.models.UserRole`, `datetime.datetime`, `pydantic.BaseModel`, `pydantic.ConfigDict`, `pydantic.EmailStr`, `pydantic.field_validator`, `string`, `typing.Any`, `typing.Optional`
- **Classi**:
  - `VoceSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `UserBase` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `UserCreate` (bases: BaseModel) - Nessuna docstring. Metodi: `validate_password`.
  - `UserRead` (bases: UserBase) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `LoginRequest` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `TokenResponse` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `UserProfileBase` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `UserProfileRead` (bases: UserProfileBase) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ProfileUpdate` (bases: UserProfileBase) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ComputoSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `CommessaCreate` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `CommessaSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `CommessaDetailSchema` (bases: CommessaSchema) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PriceListItemSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PriceListOfferSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ManualPriceUpdateRequest` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ManualPriceUpdateResponse` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PriceListItemSearchResultSchema` (bases: PriceListItemSchema) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PriceCatalogCommessaSummarySchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PriceCatalogBusinessUnitSummarySchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PriceCatalogSummarySchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsNodeSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsSpazialeSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `Wbs6NodeSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `Wbs7NodeSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `CommessaWbsSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsImportStatsSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SixImportReportSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SixPreventivoOptionSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SixPreventiviPreviewSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SixInspectionPriceListSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SixInspectionGroupSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SixPreventivoInspectSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SixInspectionSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsVisibilitySchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsVisibilityUpdateSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsPathEntrySchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AggregatedVoceSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ComputoWbsSummary` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SettingsUpdate` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `NlpModelOption` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SettingsResponse` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertySchemaField` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyCategorySchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertySchemaResponse` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ExtractRequest` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ExtractedPropertiesResponse` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyLexiconBase` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyLexiconCreate` (bases: PropertyLexiconBase) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyLexiconUpdate` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyLexiconRead` (bases: PropertyLexiconBase) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyPatternBase` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyPatternCreate` (bases: PropertyPatternBase) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyPatternUpdate` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyPatternRead` (bases: PropertyPatternBase) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyOverridePayload` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyOverrideRead` (bases: PropertyOverridePayload) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyFeedbackPayload` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyFeedbackRead` (bases: PropertyFeedbackPayload) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyExtractionRequest` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `PropertyExtractionResult` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `DashboardActivitySchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `DashboardStatsSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ConfrontoVoceOffertaSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ConfrontoVoceSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ConfrontoImpresaSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ConfrontoRoundSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ConfrontoOfferteSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiConfrontoImportoSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiDistribuzioneItemSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiVoceCriticaSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiWBS6CriticitaSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiWBS6VoceSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiWBS6TrendSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiRoundSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiImpresaSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiFiltriSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiThresholdsSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalisiCommessaSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `TrendEvoluzioneOffertaSchema` (bases: BaseModel) - Dati di un'offerta in uno specifico round. Metodi: nessun metodo pubblico.
  - `TrendEvoluzioneImpresaSchema` (bases: BaseModel) - Dati trend di un'impresa attraverso i round. Metodi: nessun metodo pubblico.
  - `TrendEvoluzioneSchema` (bases: BaseModel) - Schema per il grafico Trend Evoluzione Prezzi tra Round. Metodi: nessun metodo pubblico.
  - `HeatmapCategoriaSchema` (bases: BaseModel) - Definizione categoria WBS6 nella heatmap. Metodi: nessun metodo pubblico.
  - `HeatmapImpresaCategoriaSchema` (bases: BaseModel) - Offerta di un'impresa per una specifica categoria. Metodi: nessun metodo pubblico.
  - `HeatmapImpresaSchema` (bases: BaseModel) - Dati completi di un'impresa nella heatmap. Metodi: nessun metodo pubblico.
  - `HeatmapCompetitivitaSchema` (bases: BaseModel) - Schema per il grafico Heatmap Competitività. Metodi: nessun metodo pubblico.
  - `ImportConfigCreateSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ImportConfigSchema` (bases: ImportConfigCreateSchema) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ImportBatchSingleFileFailureSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ImportBatchSingleFileResultSchema` (bases: BaseModel) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (1)**: `PASSWORD_MAX_LENGTH_BYTES`
- **Entry point CLI**: Assente.

### `app/services/__init__.py`
- **Linee**: 83
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 1 funzioni.
- **Dipendenze principali (34)**: `analysis.AnalysisCacheService`, `analysis.AnalysisService`, `analysis.ComparisonService`, `analysis.CoreAnalysisService`, `analysis.DashboardService`, `analysis.TrendsService`, `analysis.WbsAnalysisService`, `app.services.catalog_search_service`, `app.services.serialization_service`, `audit.record_audit_log`, `commessa_bundle.CommessaBundleService`, `commessa_bundle.commessa_bundle_service`, ... (+22)
- **Classi**: nessuna.
- **Funzioni**:
  - `__getattr__(name)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/__init__.py`
- **Linee**: 17
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (7)**: `analysis.AnalysisService`, `cache.AnalysisCacheService`, `comparison.ComparisonService`, `core.CoreAnalysisService`, `dashboard.DashboardService`, `trends.TrendsService`, `wbs_analysis.WbsAnalysisService`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/analysis.py`
- **Linee**: 276
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (16)**: `app.db.models.Computo`, `app.db.models.VoceComputo`, `app.schemas.AnalisiCommessaSchema`, `app.schemas.AnalisiConfrontoImportoSchema`, `app.schemas.AnalisiFiltriSchema`, `app.schemas.AnalisiImpresaSchema`, `app.schemas.AnalisiRoundSchema`, `app.schemas.AnalisiThresholdsSchema`, `app.schemas.AnalisiWBS6CriticitaSchema`, `app.schemas.AnalisiWBS6TrendSchema`, `app.schemas.AnalisiWBS6VoceSchema`, `app.services.analysis.core.CoreAnalysisService`, ... (+4)
- **Classi**:
  - `AnalysisService` (bases: object) - Nessuna docstring. Metodi: `get_commessa_analisi`, `get_commessa_wbs6_dettaglio`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/cache.py`
- **Linee**: 90
- **Descrizione**: Modulo senza docstring. Contiene 2 classi e 0 funzioni.
- **Dipendenze principali (12)**: `app.db.models.Computo`, `app.db.models.PriceListItem`, `app.db.models.PriceListOffer`, `app.db.models.VoceComputo`, `dataclasses.dataclass`, `datetime.datetime`, `datetime.timedelta`, `sqlalchemy.func`, `sqlmodel.Session`, `sqlmodel.select`, `threading.RLock`, `typing.Optional`
- **Classi**:
  - `_InsightsCacheEntry` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `AnalysisCacheService` (bases: object) - Nessuna docstring. Metodi: `compute_dataset_version`, `try_get`, `store`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (3)**: `_INSIGHTS_CACHE`, `_INSIGHTS_CACHE_LOCK`, `_INSIGHTS_CACHE_TTL`
- **Entry point CLI**: Assente.

### `app/services/analysis/comparison.py`
- **Linee**: 78
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (7)**: `app.schemas.ConfrontoImpresaSchema`, `app.schemas.ConfrontoOfferteSchema`, `app.schemas.ConfrontoRoundSchema`, `app.schemas.ConfrontoVoceOffertaSchema`, `app.schemas.ConfrontoVoceSchema`, `app.services.analysis.core.CoreAnalysisService`, `sqlmodel.Session`
- **Classi**:
  - `ComparisonService` (bases: object) - Nessuna docstring. Metodi: `get_commessa_confronto`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/core.py`
- **Linee**: 1148
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 1 funzioni.
- **Dipendenze principali (25)**: `__future__.annotations`, `app.db.models.Commessa`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.PriceListOffer`, `app.db.models.Settings`, `app.db.models.VoceComputo`, `app.db.models_wbs.Voce`, `app.schemas.AnalisiDistribuzioneItemSchema`, `app.schemas.AnalisiVoceCriticaSchema`, `app.services.analysis.cache.AnalysisCacheService`, `app.services.wbs_visibility.WbsVisibilityService`, ... (+13)
- **Classi**:
  - `CoreAnalysisService` (bases: object) - Nessuna docstring. Metodi: `load_thresholds`, `classify_delta`, `prepare_commessa_data`, `build_distribuzione`, `build_voci_critiche`, `build_wbs6_analisi`, `normalize_imprese`, `build_rounds`, `determine_allowed_offerte`, `filter_entries`.
- **Funzioni**:
  - `_safe_float(value: Any)` - Converte numeri o stringhe numeriche (anche con virgola) in float, altrimenti None.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/dashboard.py`
- **Linee**: 50
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (8)**: `app.db.models.Commessa`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.schemas.DashboardActivitySchema`, `app.schemas.DashboardStatsSchema`, `sqlalchemy.func`, `sqlmodel.Session`, `sqlmodel.select`
- **Classi**:
  - `DashboardService` (bases: object) - Nessuna docstring. Metodi: `get_dashboard_stats`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/insights.py`
- **Linee**: 2
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/trends.py`
- **Linee**: 323
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (17)**: `app.db.models.Computo`, `app.db.models.VoceComputo`, `app.schemas.AnalisiFiltriSchema`, `app.schemas.AnalisiRoundSchema`, `app.schemas.HeatmapCategoriaSchema`, `app.schemas.HeatmapCompetitivitaSchema`, `app.schemas.HeatmapImpresaCategoriaSchema`, `app.schemas.HeatmapImpresaSchema`, `app.schemas.TrendEvoluzioneImpresaSchema`, `app.schemas.TrendEvoluzioneOffertaSchema`, `app.schemas.TrendEvoluzioneSchema`, `app.services.analysis.core.CoreAnalysisService`, ... (+5)
- **Classi**:
  - `TrendsService` (bases: object) - Nessuna docstring. Metodi: `get_commessa_trend_round`, `get_commessa_heatmap_competitivita`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/analysis/wbs_analysis.py`
- **Linee**: 265
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 6 funzioni.
- **Dipendenze principali (15)**: `__future__.annotations`, `app.db.models.Computo`, `app.db.models.VoceComputo`, `app.excel.parser.MAX_WBS_LEVELS`, `app.schemas.AggregatedVoceSchema`, `app.schemas.ComputoWbsSummary`, `app.schemas.WbsNodeSchema`, `app.schemas.WbsPathEntrySchema`, `app.services.wbs_visibility.WbsVisibilityService`, `re`, `sqlmodel.Session`, `sqlmodel.select`, ... (+3)
- **Classi**:
  - `WbsAnalysisService` (bases: object) - Calcola aggregazioni WBS e lista lavorazioni per un computo. Metodi: `get_wbs_summary`.
- **Funzioni**:
  - `_build_wbs_tree(voci: Iterable[VoceComputo])` - Nessuna docstring.
  - `_convert_tree(children: Dict[Tuple[int, str | None, str | None], dict])` - Nessuna docstring.
  - `_aggregate_voci(voci: Iterable[VoceComputo])` - Nessuna docstring.
  - `_normalize_wbs_codes(wbs6: str | None, wbs7: str | None, codice: str | None)` - Nessuna docstring.
  - `_extract_wbs_parts(*candidates: str | None)` - Nessuna docstring.
  - `_normalize_voci_wbs(voci: Iterable[VoceComputo])` - Nessuna docstring.
- **Costanti dichiarate (2)**: `_BASE_WBS_RE`, `_BASE_WITH_SECOND_RE`
- **Entry point CLI**: Assente.

### `app/services/audit.py`
- **Linee**: 43
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 2 funzioni.
- **Dipendenze principali (5)**: `__future__.annotations`, `app.db.models.AuditLog`, `hashlib.sha256`, `sqlmodel.Session`, `typing.Optional`
- **Classi**: nessuna.
- **Funzioni**:
  - `_safe_hash(payload: bytes | str | None)` - Nessuna docstring.
  - `record_audit_log(session: Session, *, user_id: Optional[int], action: str, endpoint: Optional[str] = None, ip_address: Optional[str] = None, method: Optional[str] = None, payload: bytes | str | None = None, outcome: Optional[str] = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/audit/__init__.py`
- **Linee**: 4
- **Descrizione**: Audit services - logging and tracking.
- **Dipendenze principali (1)**: `app.services.audit.audit_service.record_audit_log`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/audit/audit_service.py`
- **Linee**: 43
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 2 funzioni.
- **Dipendenze principali (5)**: `__future__.annotations`, `app.db.models.AuditLog`, `hashlib.sha256`, `sqlmodel.Session`, `typing.Optional`
- **Classi**: nessuna.
- **Funzioni**:
  - `_safe_hash(payload: bytes | str | None)` - Nessuna docstring.
  - `record_audit_log(session: Session, *, user_id: Optional[int], action: str, endpoint: Optional[str] = None, ip_address: Optional[str] = None, method: Optional[str] = None, payload: bytes | str | None = None, outcome: Optional[str] = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/catalog_search_service.py`
- **Linee**: 327
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 4 funzioni.
- **Dipendenze principali (16)**: `app.api.deps.DBSession`, `app.db.models.Commessa`, `app.db.models.PriceListItem`, `app.services.nlp.extract_construction_attributes`, `app.services.nlp.price_list_faiss_service`, `app.services.nlp.semantic_embedding_service`, `app.services.serialization_service.collect_price_list_offers`, `app.services.serialization_service.collect_project_quantities`, `app.services.serialization_service.serialize_price_list_item`, `logging`, `numpy`, `re`, ... (+4)
- **Classi**: nessuna.
- **Funzioni**:
  - `tokenize_query(text: str)` - Nessuna docstring.
  - `lexical_boost(tokens: set[str], item: PriceListItem)` - Nessuna docstring.
  - `attribute_boost(item_attrs: dict, query_attrs: dict)` - Calcola boost per match attributi strutturati.
  - `search_catalog(session: DBSession, query: str, commessa_id: int | None = None, top_k: int = 50, min_score: float = 0.2)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/commessa_bundle.py`
- **Linee**: 727
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 1 funzioni.
- **Dipendenze principali (35)**: `__future__.annotations`, `app.core.settings`, `app.db.models.Commessa`, `app.db.models.CommessaPreferences`, `app.db.models.Computo`, `app.db.models.ImportConfig`, `app.db.models.PriceListItem`, `app.db.models.PriceListOffer`, `app.db.models.VoceComputo`, `app.db.models_wbs.Impresa`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceOfferta`, ... (+23)
- **Classi**:
  - `CommessaBundleService` (bases: object) - Gestione esportazione/importazione bundle commessa. Metodi: `is_bundle_file`, `export_commessa`, `import_bundle_from_upload`, `import_bundle`.
- **Funzioni**:
  - `_parse_datetime(value: str | datetime | None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/commesse.py`
- **Linee**: 145
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (10)**: `__future__.annotations`, `app.db.models.Commessa`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.VoceComputo`, `app.schemas.CommessaCreate`, `sqlmodel.Session`, `sqlmodel.select`, `storage.storage_service`, `typing.Sequence`
- **Classi**:
  - `CommesseService` (bases: object) - Nessuna docstring. Metodi: `list_commesse`, `get_commessa`, `get_commessa_with_computi`, `create_commessa`, `update_commessa`, `add_computo`, `delete_computo`, `delete_commessa`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importer.py`
- **Linee**: 384
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (15)**: `__future__.annotations`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.PriceListItem`, `app.db.models.PriceListOffer`, `app.db.models.VoceComputo`, `app.services.importers.LcImportService`, `app.services.importers.McImportService`, `datetime.datetime`, `logging`, `pathlib.Path`, `sqlmodel.Session`, ... (+3)
- **Classi**:
  - `ImportService` (bases: object) - Facade unificato per import LC e MC con routing automatico. Delega ai servizi dedicati basandosi sulla modalità: - LC (Lista Lavorazioni): solo prezzi → LcImportService - MC (Computo Metrico): progressivi + quantità + prezzi → McImportService Metodi: `import_computo_ritorno`, `import_computo_progetto`, `import_batch_single_file`, `update_manual_offer_price`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/__init__.py`
- **Linee**: 20
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (9)**: `common.BaseImportService`, `common._WbsNormalizeContext`, `lc.LcImportService`, `lc.parse_lc_return_excel`, `matching._ReturnAlignmentResult`, `matching._align_return_rows`, `matching._build_matching_report`, `mc.McImportService`, `mc.parse_mc_return_excel`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/common.py`
- **Linee**: 451
- **Descrizione**: Modulo senza docstring. Contiene 2 classi e 11 funzioni.
- **Dipendenze principali (22)**: `__future__.annotations`, `app.db.models.Computo`, `app.db.models.PriceListItem`, `app.db.models.VoceComputo`, `app.db.models_wbs.Impresa`, `app.db.models_wbs.Voce`, `app.db.models_wbs.Wbs6`, `app.db.models_wbs.Wbs7`, `app.db.models_wbs.WbsSpaziale`, `app.excel.ParsedVoce`, `app.excel.ParsedWbsLevel`, `app.excel.parser.MAX_WBS_LEVELS`, ... (+10)
- **Classi**:
  - `BaseImportService` (bases: object) - Metodi e utilità condivise tra import MC e LC. Metodi: nessun metodo pubblico.
  - `_WbsNormalizeContext` (bases: object) - Gestisce la creazione/ricerca dei nodi WBS e delle voci normalizzate. Metodi: `ensure_voce`, `get_voce_from_legacy`, `get_or_create_impresa`, `resolve_price_list_item_id`.
- **Funzioni**:
  - `sanitize_impresa_label(label: str | None)` - Normalizza il nome impresa rimuovendo suffissi duplicati e spazi superflui.
  - `_ceil_decimal_value(value: float | Decimal | int, exponent: str)` - Nessuna docstring.
  - `_ceil_quantity(value: float | Decimal | int | None)` - Nessuna docstring.
  - `_ceil_amount(value: float | Decimal | int | None)` - Nessuna docstring.
  - `_calculate_line_amount(quantita: float | Decimal | None, prezzo: float | None)` - Calcola importo da quantità e prezzo usando logica consistente con importer. Restituisce (quantita, importo) arrotondati.
  - `_normalize_wbs6_code(value: Optional[str])` - Nessuna docstring.
  - `_normalize_wbs7_code(value: Optional[str])` - Nessuna docstring.
  - `_looks_like_wbs7_code(value: Optional[str])` - Nessuna docstring.
  - `_map_wbs_levels(levels: Sequence)` - Nessuna docstring.
  - `_normalize_commessa_tag(commessa_id: int | None, commessa_code: str | None)` - Nessuna docstring.
  - `_build_global_voce_code(commessa_tag: str | None, parsed: ParsedVoce)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/import_common.py`
- **Linee**: 104
- **Descrizione**: Funzioni comuni condivise tra LcImportService e McImportService.
- **Dipendenze principali (7)**: `__future__.annotations`, `app.db.models.VoceComputo`, `app.excel.ParsedVoce`, `app.services.importers.common._ceil_amount`, `decimal.Decimal`, `logging`, `typing.Sequence`
- **Classi**: nessuna.
- **Funzioni**:
  - `_build_parsed_from_progetto(voce: VoceComputo, quantita: float | None, prezzo_unitario: float | None, importo: float | None)` - Costruisce un ParsedVoce da una VoceComputo del progetto. Funzione comune usata sia da LC che da MC per creare voci del computo ritorno basandosi su voci del computo progetto.
  - `calculate_total_import(voci: Sequence[ParsedVoce])` - Calcola l'importo totale di un computo da una lista di voci. Args: voci: Lista di voci parsed Returns: Importo totale arrotondato
  - `validate_progetto_voci(voci: Sequence[VoceComputo])` - Valida che le voci del computo progetto siano utilizzabili. Raises: ValueError: Se le voci non sono valide
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/lc/__init__.py`
- **Linee**: 5
- **Descrizione**: LC (Lista Comparativa) import module.
- **Dipendenze principali (2)**: `importer.LcImportService`, `parser.parse_lc_return_excel`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/lc/importer.py`
- **Linee**: 585
- **Descrizione**: LcImportService - Servizio dedicato per l'importazione di file LC (Lista Lavorazioni). LOGICA LC: - File contiene solo PREZZI UNITARI per ciascun prodotto (codice/descrizione) - NON contiene progressivi (è un listino prezzi puro) - L'impresa quota il PRODOTTO, non il singolo progressivo - Un prezzo per product_id →...
- **Dipendenze principali (32)**: `__future__.annotations`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.PriceListItem`, `app.db.models.PriceListOffer`, `app.db.models.VoceComputo`, `app.db.models_wbs.Impresa`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceOfferta`, `app.excel.ParsedVoce`, `app.services.commesse.CommesseService`, `app.services.importers.common.BaseImportService`, ... (+20)
- **Classi**:
  - `LcImportService` (bases: BaseImportService) - Servizio per l'importazione di file LC (Lista Lavorazioni). Il file LC contiene solo prezzi unitari per prodotto, senza progressivi. Ogni prezzo viene applicato a TUTTI i progressivi che usano quel product_id. Metodi: `import_lc`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/lc/parser.py`
- **Linee**: 190
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (28)**: `__future__.annotations`, `app.excel.ParsedComputo`, `app.excel.ParsedVoce`, `app.excel.ParsedWbsLevel`, `app.services.importers.common._calculate_line_amount`, `app.services.importers.common._ceil_amount`, `app.services.importers.parser_utils._CustomReturnParseResult`, `app.services.importers.parser_utils._apply_column_filter`, `app.services.importers.parser_utils._cell_has_content`, `app.services.importers.parser_utils._cell_to_float`, `app.services.importers.parser_utils._cell_to_progressive`, `app.services.importers.parser_utils._columns_to_indexes`, ... (+16)
- **Classi**: nessuna.
- **Funzioni**:
  - `parse_lc_return_excel(file_path: Path, sheet_name: str | None, code_columns: Sequence[str], description_columns: Sequence[str], price_column: str, quantity_column: str | None = None, progressive_column: str | None = None)` - Parser LC lineare: una riga = una voce, senza combinare header/totali.
  - `_has_values(rows: list, indexes: Sequence[int])` - Nessuna docstring.
  - `_ensure_indexes_lc(name: str, columns: Sequence[str], data_rows, header_row, warnings: list[str], suggestions)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/matching/__init__.py`
- **Linee**: 79
- **Descrizione**: Matching module - Sistema di allineamento e abbinamento voci. Struttura modulare: - config: Costanti e configurazione - normalization: Normalizzazione token e text processing - report: Generazione report e warning - legacy: Logica di matching completa (da suddividere incrementalmente) TODO: Migrare gradualmente...
- **Dipendenze principali (21)**: `config`, `legacy._ReturnAlignmentResult`, `legacy._align_return_rows`, `legacy._build_description_price_map`, `legacy._build_lc_matching_report`, `legacy._build_matching_report`, `legacy._build_price_list_lookup`, `legacy._build_project_snapshot_from_price_offers`, `legacy._detect_duplicate_progressivi`, `legacy._detect_forced_zero_violations`, `legacy._format_quantity_value`, `legacy._has_progressivi`, ... (+9)
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/matching/config.py`
- **Linee**: 74
- **Descrizione**: Configurazione e costanti per il sistema di matching.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (17)**: `DESCRIPTION_MIN_RATIO`, `FORCED_ZERO_CODE_PREFIXES`, `FORCED_ZERO_DESCRIPTION_KEYWORDS`, `HEAD_TAIL_WORD_LIMIT`, `JACCARD_MIN_THRESHOLD`, `JACCARD_PREFERENCE_DELTA`, `JACCARD_PREFERENCE_THRESHOLD`, `MAX_CANDIDATES_FILTER`, `MAX_CANDIDATES_FINAL`, `MIN_TOKEN_LENGTH`, `MIN_TOKEN_LENGTH_DESCRIPTION`, `MIN_WORD_TOKEN_LENGTH`, ... (+5)
- **Entry point CLI**: Assente.

### `app/services/importers/matching/legacy.py`
- **Linee**: 2102
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 68 funzioni.
- **Dipendenze principali (32)**: `__future__.annotations`, `app.db.models.PriceListItem`, `app.db.models.VoceComputo`, `app.excel.ParsedVoce`, `app.excel.ParsedWbsLevel`, `app.excel.parser.MAX_WBS_LEVELS`, `app.services.importers.common._build_global_voce_code`, `app.services.importers.common._calculate_line_amount`, `app.services.importers.common._ceil_amount`, `app.services.importers.common._ceil_quantity`, `app.services.importers.common._looks_like_wbs7_code`, `app.services.importers.common._map_wbs_levels`, ... (+20)
- **Classi**:
  - `_ReturnAlignmentResult` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_collect_return_only_labels(wrappers: Sequence[dict[str, Any]], satisfied_group_keys: set[str] | None = None)` - Nessuna docstring.
  - `_align_progressive_return(progetto_voci: Sequence[VoceComputo], indice_ritorno: dict[str, list[dict[str, Any]]], ritorno_wrappers: Sequence[dict[str, Any]])` - Nessuna docstring.
  - `_align_totals_return(progetto_voci: Sequence[VoceComputo], indice_ritorno: dict[str, list[dict[str, Any]]], ritorno_wrappers: Sequence[dict[str, Any]], wbs_wrapper_map: dict[str, list[dict[str, Any]]], description_price_map: dict[str, list[float]], excel_group_targets: dict[str, Decimal], excel_group_labels: dict[str, str], excel_group_details: dict[str, dict[str, Any]])` - Nessuna docstring.
  - `_align_return_rows(progetto_voci: Sequence[VoceComputo], ritorno_voci: Sequence[ParsedVoce], *, prefer_progressivi: bool, description_price_map: dict[str, list[float]])` - Nessuna docstring.
  - `_align_description_only_return(progetto_voci: Sequence[VoceComputo], ritorno_voci: Sequence[ParsedVoce], description_price_map: dict[str, list[float]])` - Nessuna docstring.
  - `_build_parsed_from_progetto(voce: VoceComputo, quantita: float | None, prezzo_unitario: float | None, importo: float | None)` - Nessuna docstring.
  - `_build_project_snapshot_from_price_offers(progetto_voci: Sequence[VoceComputo], price_items: Sequence[PriceListItem], offer_price_map: dict[int, float])` - Nessuna docstring.
  - `_build_return_index(voci: Sequence[ParsedVoce])` - Nessuna docstring.
  - `_build_wbs_wrapper_map(wrappers: Sequence[dict[str, Any]])` - Nessuna docstring.
  - `_build_wbs_price_map(wbs_wrapper_map: dict[str, list[dict[str, Any]]])` - Nessuna docstring.
  - `_build_description_price_map(ritorno_voci: Sequence[ParsedVoce])` - Nessuna docstring.
  - `_build_price_list_lookup(items: Sequence[PriceListItem])` - Nessuna docstring.
  - `_match_price_list_item_entry(parsed: ParsedVoce, code_map: dict[str, list[PriceListItem]], signature_map: dict[str, list[PriceListItem]], description_map: dict[str, list[PriceListItem]], head_signature_map: dict[str, list[PriceListItem]], tail_signature_map: dict[str, list[PriceListItem]], embedding_map: dict[str, list[tuple[PriceListItem, list[float]]]])` - Nessuna docstring.
  - `_select_price_list_item_candidate(candidates: Sequence[PriceListItem], parsed: ParsedVoce)` - Nessuna docstring.
  - `_parsed_wbs6_code(parsed: ParsedVoce)` - Nessuna docstring.
  - `_description_signature(description: str | None, unit: str | None, wbs6_code: str | None)` - Nessuna docstring.
  - `_description_signature_from_parsed(voce: ParsedVoce)` - Nessuna docstring.
  - `_description_signature_from_model(voce: VoceComputo)` - Nessuna docstring.
  - `_head_tail_signatures(description: str | None, limit: int = _HEAD_TAIL_WORD_LIMIT)` - Nessuna docstring.
  - `_tokenize_words(text: str)` - Nessuna docstring.
  - `_match_price_list_item_semantic(parsed: ParsedVoce, embedding_map: dict[str, list[tuple[PriceListItem, list[float]]]])` - Nessuna docstring.
  - `_build_matching_report(legacy_pairs: Sequence[tuple[VoceComputo | None, ParsedVoce]], excel_only_labels: Sequence[str] | None = None, excel_only_groups: Sequence[str] | None = None, quantity_mismatches: Sequence[str] | None = None, quantity_totals: dict[str, float] | None = None)` - Nessuna docstring.
  - `_describe_parsed_voce(voce: ParsedVoce)` - Nessuna docstring.
  - `_log_unmatched_price_entries(entries: Sequence[ParsedVoce], limit: int = 5)` - Nessuna docstring.
  - `_log_price_conflicts(conflicts: Iterable[dict[str, Any]], limit: int = 5)` - Nessuna docstring.
  - `_build_lc_matching_report(summary: dict[str, Any])` - Nessuna docstring.
  - `_build_project_description_buckets(progetto_voci: Sequence[VoceComputo])` - Nessuna docstring.
  - `_assign_wrapper_preferences(wrappers: Sequence[dict[str, Any]], project_buckets: dict[str, list[tuple[VoceComputo, set[str]]]])` - Nessuna docstring.
  - `_filter_entries_by_primary(entries: Sequence[tuple[ParsedVoce, VoceComputo]], primary: str | None)` - Nessuna docstring.
  - `_keys_from_voce_progetto(voce: VoceComputo)` - Nessuna docstring.
  - `_keys_from_parsed_voce(voce: ParsedVoce)` - Nessuna docstring.
  - `_append_token(target: list[str], value: str | None)` - Nessuna docstring.
  - `_descr_tokens(text: str | None)` - Nessuna docstring.
  - `_append_description_tokens(target: list[str], value: str | None)` - Tokenizza la descrizione in modo leggero: - intera descrizione / riga - singole parole con lunghezza >= 3 (abbassata da 4 a 3) Niente n-gram, altrimenti esplode il numero di chiavi.
  - `_normalize_token(value: str | None)` - Nessuna docstring.
  - `_pick_match(index: dict[str, list[dict[str, Any]]], keys: Sequence[str], voce_progetto: VoceComputo | None = None)` - Versione ottimizzata: usa token pre-calcolati e limita il numero di candidati.
  - `_claim_wbs_bucket(bucket: list[dict[str, Any]] | None, voce_progetto: VoceComputo | None)` - Nessuna docstring.
  - `_voce_label(voce: VoceComputo)` - Nessuna docstring.
  - `_sum_project_quantities(voci: Sequence[VoceComputo])` - Nessuna docstring.
  - `_format_quantity_value(value: Decimal)` - Nessuna docstring.
  - `_progress_price_key(voce: VoceComputo | None)` - Nessuna docstring.
  - `_has_progressivi(voci: Sequence[ParsedVoce])` - Nessuna docstring.
  - `_quantities_match(project_value: float | None, offered_value: float | None, tolerance: float = 0.0001)` - Nessuna docstring.
  - `_prices_match(first_value: float | None, second_value: float | None, tolerance: float = 0.01)` - Nessuna docstring.
  - `_shorten_label(label: str, limit: int = 120)` - Nessuna docstring.
  - `_match_by_description_similarity(voce_progetto: VoceComputo | None, candidates: Sequence[dict[str, Any]], *, min_ratio: float = 0.3)` - Nessuna docstring.
  - `_match_excel_entry_fuzzy(voce_progetto: VoceComputo, excel_entries: Sequence[dict[str, Any]], candidate_indices: list[int], *, min_ratio: float = 0.3)` - Nessuna docstring.
  - `_detect_forced_zero_violations(voci: Sequence[ParsedVoce])` - Nessuna docstring.
  - `_is_nonzero(value: float | None, tolerance: float = 1e-06)` - Nessuna docstring.
  - `_is_forced_zero_voce(voce: ParsedVoce)` - Nessuna docstring.
  - `_requires_zero_guard(code: str | None, description: str | None)` - Nessuna docstring.
  - `_build_zero_guard_entry(codice: str | None, descrizione: str | None, quantita: float | None, prezzo: float | None, importo: float | None)` - Nessuna docstring.
  - `_detect_duplicate_progressivi(voci: Sequence[ParsedVoce])` - Nessuna docstring.
  - `_normalize_code_token(code: str | None)` - Nessuna docstring.
  - `_normalize_description_token(text: str | None)` - Nessuna docstring.
  - `_format_quantity_for_warning(value: float)` - Nessuna docstring.
  - `_jaccard_similarity(a: set[str], b: set[str])` - Nessuna docstring.
  - `_price_bundle(voce: ParsedVoce)` - Nessuna docstring.
  - `_stabilize_return_price(value: float, reference_price: float | None)` - Nessuna docstring.
  - `_wbs_key_from_model(voce: VoceComputo)` - Nessuna docstring.
  - `_wbs_key_from_parsed(voce: ParsedVoce)` - Nessuna docstring.
  - `_wbs_base_key_from_parsed(voce: ParsedVoce)` - Nessuna docstring.
  - `_split_wbs_key(key: str | None)` - Nessuna docstring.
  - `_base_wbs_key_from_key(key: str | None)` - Nessuna docstring.
  - `_collect_code_tokens(code: str | None)` - Nessuna docstring.
  - `_collect_description_tokens(text: str | None)` - Nessuna docstring.
  - `_distribute_group_targets(excel_targets: dict[str, Decimal], matched_entries: dict[str, list[ParsedVoce]], project_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]], project_code_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]], project_primary_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]], project_description_groups: dict[str, list[tuple[ParsedVoce, VoceComputo]]], excel_details: dict[str, dict[str, Any]])` - Nessuna docstring.
  - `_apply_rounding_to_match(entries: Sequence[ParsedVoce], target_total: Decimal)` - Nessuna docstring.
- **Costanti dichiarate (6)**: `_FORCED_ZERO_CODE_PREFIXES`, `_FORCED_ZERO_DESCRIPTION_KEYWORDS`, `_HEAD_TAIL_WORD_LIMIT`, `_SEMANTIC_DEFAULT_BUCKET`, `_SEMANTIC_MIN_SCORE`, `_WORD_TOKENIZER`
- **Entry point CLI**: Assente.

### `app/services/importers/matching/normalization.py`
- **Linee**: 382
- **Descrizione**: Utilità di normalizzazione token e text processing per il matching.
- **Dipendenze principali (12)**: `__future__.annotations`, `app.db.models.VoceComputo`, `app.excel.ParsedVoce`, `app.excel.ParsedWbsLevel`, `config.HEAD_TAIL_WORD_LIMIT`, `config.MIN_TOKEN_LENGTH_DESCRIPTION`, `config.MIN_WORD_TOKEN_LENGTH`, `config.STOPWORDS`, `re`, `typing.Optional`, `typing.Sequence`, `unicodedata`
- **Classi**: nessuna.
- **Funzioni**:
  - `normalize_token(value: str | None)` - Normalizza un token generico rimuovendo accenti e caratteri non alfanumerici.
  - `normalize_code_token(code: str | None)` - Normalizza un codice (solo maiuscole, no separatori).
  - `normalize_description_token(text: str | None)` - Normalizza una descrizione (lowercase, no accenti, spazi normalizzati).
  - `tokenize_words(text: str)` - Tokenizza il testo in parole (solo alfanumerici).
  - `extract_description_tokens(text: str | None)` - Estrae token da descrizione: - Testo completo normalizzato (se >= MIN_TOKEN_LENGTH_DESCRIPTION) - Righe separate normalizzate - Singole parole (escludendo stopwords)
  - `collect_code_tokens(code: str | None)` - Estrae token progressivi da codice: - Codice completo normalizzato - Prefissi progressivi (es: "ABC123" -> {"ABC123", "ABC", "ABCABC123"})
  - `collect_description_tokens(text: str | None)` - Raccoglie token da descrizione per indexing: - Testo completo (se abbastanza lungo) - Singoli segmenti >= 4 caratteri
  - `build_head_tail_signatures(description: str | None, limit: int = HEAD_TAIL_WORD_LIMIT)` - Costruisce signature head e tail dalla descrizione. Usate per matching fuzzy quando non c'è match esatto.
  - `build_description_signature(description: str | None, unit: str | None = None, wbs6_code: str | None = None)` - Costruisce signature univoca da descrizione. Nota: unit e wbs6_code sono opzionali per retrocompatibilità, ma attualmente ci si basa solo sulla descrizione normalizzata.
  - `build_description_signature_from_parsed(voce: ParsedVoce)` - Costruisce signature da ParsedVoce.
  - `build_description_signature_from_model(voce: VoceComputo)` - Costruisce signature da VoceComputo.
  - `build_wbs_key_from_model(voce: VoceComputo)` - Costruisce chiave WBS da VoceComputo. Formato: "primary|secondary" dove: - primary: wbs_6 o wbs_5 - secondary: wbs_7 o descrizione
  - `build_wbs_key_from_parsed(voce: ParsedVoce)` - Costruisce chiave WBS completa da ParsedVoce. Formato: "primary|secondary|description"
  - `build_wbs_base_key_from_parsed(voce: ParsedVoce)` - Costruisce chiave WBS base (senza descrizione) da ParsedVoce. Formato: "primary|secondary"
  - `split_wbs_key(key: str | None)` - Splitta chiave WBS in (primary, secondary).
  - `build_base_wbs_key_from_key(key: str | None)` - Estrae la parte "base" di una chiave WBS (primary|secondary, senza description).
  - `append_token_to_list(target: list[str], value: str | None)` - Aggiunge un token normalizzato alla lista (no duplicati).
  - `append_description_tokens_to_list(target: list[str], value: str | None)` - Tokenizza descrizione e aggiunge alla lista: - Testo completo / righe - Singole parole (escl. stopwords)
  - `build_keys_from_voce_progetto(voce: VoceComputo)` - Costruisce lista di chiavi di ricerca da VoceComputo per matching. Include: descrizioni, progressivo, codici WBS, codice voce.
  - `build_keys_from_parsed_voce(voce: ParsedVoce)` - Costruisce lista di chiavi di ricerca da ParsedVoce per matching. Include: descrizioni, codice, livelli WBS, progressivo.
- **Costanti dichiarate (1)**: `_WORD_TOKENIZER`
- **Entry point CLI**: Assente.

### `app/services/importers/matching/report.py`
- **Linee**: 185
- **Descrizione**: Generazione report e warning per matching.
- **Dipendenze principali (9)**: `__future__.annotations`, `app.db.models.PriceListItem`, `app.db.models.VoceComputo`, `app.excel.ParsedVoce`, `decimal.Decimal`, `logging`, `typing.Any`, `typing.Iterable`, `typing.Sequence`
- **Classi**: nessuna.
- **Funzioni**:
  - `voce_label(voce: VoceComputo)` - Genera label descrittiva per VoceComputo.
  - `shorten_label(label: str, limit: int = 120)` - Accorcia label troppo lunga.
  - `format_quantity_value(value: Decimal)` - Formatta Decimal quantità per display (rimuove zeri trailing).
  - `format_quantity_for_warning(value: float)` - Formatta float quantità per warning (rimuove zeri trailing).
  - `describe_parsed_voce(voce: ParsedVoce)` - Descrizione breve ParsedVoce (codice @ prezzo).
  - `build_matching_report(legacy_pairs: Sequence[tuple[VoceComputo | None, ParsedVoce]], excel_only_labels: Sequence[str] | None = None, excel_only_groups: Sequence[str] | None = None, quantity_mismatches: Sequence[str] | None = None, quantity_totals: dict[str, float] | None = None)` - Costruisce report di matching tra progetto e ritorno. Include: voci matched, missing, excel_only, quantity mismatches.
  - `build_lc_matching_report(summary: dict[str, Any])` - Costruisce report specifico per import LC (basato su listino prezzi).
  - `log_unmatched_price_entries(entries: Sequence[ParsedVoce], limit: int = 5)` - Log warning per entry non matched con listino.
  - `log_price_conflicts(conflicts: Iterable[dict[str, Any]], limit: int = 5)` - Log warning per conflitti prezzi multipli.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/mc/__init__.py`
- **Linee**: 5
- **Descrizione**: MC (Computo Metrico) import module.
- **Dipendenze principali (2)**: `importer.McImportService`, `parser.parse_mc_return_excel`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/mc/importer.py`
- **Linee**: 835
- **Descrizione**: McImportService - Servizio dedicato per l'importazione di file MC (Computo Metrico). LOGICA MC: - File contiene PROGRESSIVI + QUANTITÀ + PREZZI - Match ESATTO su progressivo (ignorare codice se in conflitto) - Ogni progressivo può avere prezzo diverso anche con stesso codice - L'impresa quota il SINGOLO PROGRESSIVO,...
- **Dipendenze principali (45)**: `__future__.annotations`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.PriceListItem`, `app.db.models.PriceListOffer`, `app.db.models.VoceComputo`, `app.db.models_wbs.Impresa`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceOfferta`, `app.excel.ParsedVoce`, `app.excel.parse_computo_excel`, `app.services.commesse.CommesseService`, ... (+33)
- **Classi**:
  - `McImportService` (bases: BaseImportService) - Servizio per l'importazione di file MC (Computo Metrico). Il file MC contiene progressivi + quantità + prezzi. Match ESATTO su progressivo, ogni progressivo può avere prezzo diverso anche con stesso codice prodotto. Metodi: `import_mc`, `import_computo_metrico`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/mc/parser.py`
- **Linee**: 26
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 1 funzioni.
- **Dipendenze principali (4)**: `app.services.importers.parser_utils._CustomReturnParseResult`, `app.services.importers.parser_utils._parse_custom_return_excel`, `pathlib.Path`, `typing.Sequence`
- **Classi**: nessuna.
- **Funzioni**:
  - `parse_mc_return_excel(file_path: Path, sheet_name: str | None, code_columns: Sequence[str], description_columns: Sequence[str], price_column: str, quantity_column: str | None = None, progressive_column: str | None = None)` - Wrapper esplicito per il parser MC (combine_totals=True).
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/importers/parser_utils.py`
- **Linee**: 710
- **Descrizione**: Modulo senza docstring. Contiene 3 classi e 28 funzioni.
- **Dipendenze principali (18)**: `__future__.annotations`, `app.excel.ParsedComputo`, `app.excel.ParsedVoce`, `app.excel.ParsedWbsLevel`, `app.services.importers.common._calculate_line_amount`, `app.services.importers.common._ceil_amount`, `app.services.importers.common._looks_like_wbs7_code`, `app.services.importers.common._normalize_wbs7_code`, `dataclasses.dataclass`, `decimal.Decimal`, `openpyxl.load_workbook`, `openpyxl.utils.column_index_from_string`, ... (+6)
- **Classi**:
  - `_ColumnProfile` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `_ColumnSuggestion` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `_CustomReturnParseResult` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_parse_custom_return_excel(file_path: Path, sheet_name: str | None, code_columns: Sequence[str], description_columns: Sequence[str], price_column: str, quantity_column: str | None = None, progressive_column: str | None = None, *, combine_totals: bool = True)` - Nessuna docstring.
  - `_select_sheet(workbook, requested_name: str | None)` - Nessuna docstring.
  - `_rows_to_dataframe(rows: Sequence[Sequence[Any]])` - Nessuna docstring.
  - `_drop_empty_columns(rows: Sequence[Sequence[Any]])` - Rimuove colonne totalmente vuote usando pandas per evitare offset errati quando il file contiene colonne segnaposto o intere colonne vuote. Restituisce righe ripulite, numero colonne eliminate e gli indici originali mantenuti.
  - `_apply_column_filter(rows: Sequence[Sequence[Any]], kept_indexes: Sequence[int])` - Nessuna docstring.
  - `_ratio(values: Sequence[str], predicate)` - Nessuna docstring.
  - `_looks_numeric(value: str)` - Nessuna docstring.
  - `_looks_currency(value: str)` - Nessuna docstring.
  - `_looks_code(value: str)` - Nessuna docstring.
  - `_looks_text(value: str)` - Nessuna docstring.
  - `_pick_column_profile(index: int, sample_rows: list[list[str]])` - Nessuna docstring.
  - `_detect_column_suggestions(rows: list, header_idx: int)` - Nessuna docstring.
  - `_locate_header_row(rows: list)` - Nessuna docstring.
  - `_columns_to_indexes(columns: Sequence[str], name: str, *, header_row: Sequence[str], required: bool = True)` - Nessuna docstring.
  - `_single_column_index(column: str | None, name: str, *, header_row: Sequence[str], required: bool = True)` - Nessuna docstring.
  - `_resolve_column_reference(reference: str, header_row: Sequence[str])` - Nessuna docstring.
  - `_normalize_header_text(value)` - Nessuna docstring.
  - `_row_has_values(row)` - Nessuna docstring.
  - `_column_has_values(rows: Sequence[Sequence[Any]], indexes: Sequence[int])` - Nessuna docstring.
  - `_sanitize_price_candidate(value: float)` - Nessuna docstring.
  - `_has_external_formula(cell)` - Nessuna docstring.
  - `_cell_has_content(value)` - Nessuna docstring.
  - `_combine_text(row, indexes: Sequence[int])` - Nessuna docstring.
  - `_combine_code(row, indexes: Sequence[int])` - Nessuna docstring.
  - `_cell_to_text(value)` - Nessuna docstring.
  - `_extract_code_from_text(text: str | None)` - Nessuna docstring.
  - `_cell_to_float(row, index: int)` - Nessuna docstring.
  - `_cell_to_progressive(row, index: int | None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/nlp.py`
- **Linee**: 924
- **Descrizione**: Modulo senza docstring. Contiene 3 classi e 2 funzioni.
- **Dipendenze principali (17)**: `__future__.annotations`, `app.core.config.settings`, `faiss`, `huggingface_hub.snapshot_download`, `logging`, `numpy`, `os`, `pathlib.Path`, `psycopg2`, `psycopg2.extensions.connection`, `re`, `sentence_transformers.SentenceTransformer`, ... (+5)
- **Classi**:
  - `SemanticEmbeddingService` (bases: object) - Gestisce il calcolo degli embedding semantici. ATTENZIONE: - Questa versione NON usa più RoBERTino / ONNX come feature extractor. - Usa un modello SentenceTransformer pensato per semantic search con cosine similarity. - L'API pubblica è compatibile con la versione precedente (metodi e payload). Metodi: `configure`, `download_model`, `iter_metadata_slots`, `extract_embedding_payload`, `is_available`, `embed_texts`, `embed_text`, `warmup`, `prepare_price_list_metadata`.
  - `DocumentFaissPipeline` (bases: object) - Pipeline per indicizzare e cercare documenti con FAISS e SentenceTransformer. Metodi: `get_db_connection`, `load_documents`, `load_model`, `configure`, `generate_embeddings`, `build_index`, `save_index`, `load_index`, `build_index_from_db`, `semantic_search`.
  - `PriceListFaissService` (bases: object) - Servizio FAISS per ricerca semantica veloce su PriceListItem. Costruisce e gestisce indici FAISS usando gli embedding già salvati in extra_metadata.nlp.vector. Supporta indici per commessa o globali. Metodi: `build_index`, `load_index`, `search`, `index_exists`, `delete_index`.
- **Funzioni**:
  - `extract_construction_attributes(text: str)` - Estrae attributi strutturati da descrizioni di voci edilizie. Utile per ricerca ibrida semantica + attributi specifici.
  - `get_available_semantic_models()` - Ritorna la lista dei modelli configurabili per la ricerca semantica.
- **Costanti dichiarate (2)**: `AVAILABLE_SEMANTIC_MODELS`, `DEFAULT_SEMANTIC_MODEL_ID`
- **Entry point CLI**: Assente.

### `app/services/nlp/__init__.py`
- **Linee**: 23
- **Descrizione**: NLP services - embeddings and property extraction.
- **Dipendenze principali (8)**: `app.services.nlp.embedding_service.DocumentFaissPipeline`, `app.services.nlp.embedding_service.PriceListFaissService`, `app.services.nlp.embedding_service.SemanticEmbeddingService`, `app.services.nlp.embedding_service.document_faiss_pipeline`, `app.services.nlp.embedding_service.extract_construction_attributes`, `app.services.nlp.embedding_service.get_available_semantic_models`, `app.services.nlp.embedding_service.price_list_faiss_service`, `app.services.nlp.embedding_service.semantic_embedding_service`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/nlp/embedding_service.py`
- **Linee**: 924
- **Descrizione**: Modulo senza docstring. Contiene 3 classi e 2 funzioni.
- **Dipendenze principali (17)**: `__future__.annotations`, `app.core.config.settings`, `faiss`, `huggingface_hub.snapshot_download`, `logging`, `numpy`, `os`, `pathlib.Path`, `psycopg2`, `psycopg2.extensions.connection`, `re`, `sentence_transformers.SentenceTransformer`, ... (+5)
- **Classi**:
  - `SemanticEmbeddingService` (bases: object) - Gestisce il calcolo degli embedding semantici. ATTENZIONE: - Questa versione NON usa più RoBERTino / ONNX come feature extractor. - Usa un modello SentenceTransformer pensato per semantic search con cosine similarity. - L'API pubblica è compatibile con la versione precedente (metodi e payload). Metodi: `configure`, `download_model`, `iter_metadata_slots`, `extract_embedding_payload`, `is_available`, `embed_texts`, `embed_text`, `warmup`, `prepare_price_list_metadata`.
  - `DocumentFaissPipeline` (bases: object) - Pipeline per indicizzare e cercare documenti con FAISS e SentenceTransformer. Metodi: `get_db_connection`, `load_documents`, `load_model`, `configure`, `generate_embeddings`, `build_index`, `save_index`, `load_index`, `build_index_from_db`, `semantic_search`.
  - `PriceListFaissService` (bases: object) - Servizio FAISS per ricerca semantica veloce su PriceListItem. Costruisce e gestisce indici FAISS usando gli embedding già salvati in extra_metadata.nlp.vector. Supporta indici per commessa o globali. Metodi: `build_index`, `load_index`, `search`, `index_exists`, `delete_index`.
- **Funzioni**:
  - `extract_construction_attributes(text: str)` - Estrae attributi strutturati da descrizioni di voci edilizie. Utile per ricerca ibrida semantica + attributi specifici.
  - `get_available_semantic_models()` - Ritorna la lista dei modelli configurabili per la ricerca semantica.
- **Costanti dichiarate (2)**: `AVAILABLE_SEMANTIC_MODELS`, `DEFAULT_SEMANTIC_MODEL_ID`
- **Entry point CLI**: Assente.

### `app/services/nlp/property_extraction.py`
- **Linee**: 1234
- **Descrizione**: Modulo senza docstring. Contiene 9 classi e 49 funzioni.
- **Dipendenze principali (25)**: `__future__.annotations`, `app.db.models.PropertyLexicon`, `app.db.models.PropertyOverride`, `app.db.models.PropertyPattern`, `app.db.session.engine`, `dataclasses.dataclass`, `datetime.datetime`, `datetime.timedelta`, `functools.lru_cache`, `json`, `os`, `pathlib.Path`, ... (+13)
- **Classi**:
  - `NumberWithUnit` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ClassMatch` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `BrandMatch` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `NormativaMatch` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `MaterialKeyword` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `BaseFeatures` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ExtractedProperties` (bases: TypedDict) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `CategorySchema` (bases: TypedDict) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `EmbeddingResolver` (bases: object) - Nessuna docstring. Metodi: `is_enabled`, `resolve`.
- **Funzioni**:
  - `normalize_text(text: str)` - Nessuna docstring.
  - `_strip_accents(value: str)` - Nessuna docstring.
  - `_normalize_for_match(value: str)` - Nessuna docstring.
  - `_context_window(text: str, start: int, end: int, radius: int = 50)` - Nessuna docstring.
  - `_load_json(path: Path)` - Nessuna docstring.
  - `load_category_schema()` - Nessuna docstring.
  - `_refresh_lexicon_cache(session: Session | None = None)` - Nessuna docstring.
  - `_get_lexicon(type_name: str, session: Session | None = None)` - Nessuna docstring.
  - `_dynamic_brand_synonyms(session: Session | None = None)` - Nessuna docstring.
  - `_dynamic_material_synonyms(session: Session | None = None)` - Nessuna docstring.
  - `_refresh_pattern_cache(session: Session | None = None)` - Nessuna docstring.
  - `_get_patterns(session: Session | None = None)` - Nessuna docstring.
  - `_normalize_unit(unit_raw: str)` - Nessuna docstring.
  - `_parse_float(value: str)` - Nessuna docstring.
  - `extract_numbers(text: str)` - Nessuna docstring.
  - `_canonical_fire(raw: str)` - Nessuna docstring.
  - `extract_classes(text: str)` - Nessuna docstring.
  - `extract_brands(text: str)` - Nessuna docstring.
  - `extract_normative(text: str)` - Nessuna docstring.
  - `extract_materials(text: str)` - Nessuna docstring.
  - `extract_base_features(text: str)` - Nessuna docstring.
  - `_build_resolver(model: SentenceTransformer | None)` - Nessuna docstring.
  - `init_model()` - Nessuna docstring.
  - `init_property_prototypes()` - Nessuna docstring.
  - `_to_mm(value: float, unit: Unit)` - Nessuna docstring.
  - `_first_class_by_kind(classes: List[ClassMatch], kind: str)` - Nessuna docstring.
  - `_join_normative(feats: BaseFeatures)` - Nessuna docstring.
  - `_extract_stratigrafia(original_text: str)` - Estrae frasi che descrivono lastre/pannelli/orditura (cartongesso, controsoffitti). Split primario su ; / newline / bullet, fallback a punti e match inline.
  - `_extract_ral(text: str)` - Nessuna docstring.
  - `_extract_fonoassorbimento(text_norm: str)` - Nessuna docstring.
  - `_dimension_pair_from_text(text: str)` - Nessuna docstring.
  - `_dimension_triplet_from_text(text: str)` - Nessuna docstring.
  - `_format_mm(value: float | None)` - Nessuna docstring.
  - `_material_candidates(feats: BaseFeatures, allowed: set[str])` - Nessuna docstring.
  - `_brand_value(feats: BaseFeatures)` - Nessuna docstring.
  - `_match_property_patterns(text: str, category_id: str, property_id: str, session: Session | None = None)` - Applica pattern dinamici su testo grezzo e ritorna [(valore, contesto)].
  - `map_controsoffitti(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver)` - Nessuna docstring.
  - `map_opere_da_cartongessista(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver)` - Nessuna docstring.
  - `map_opere_di_rivestimento(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver)` - Nessuna docstring.
  - `map_opere_di_pavimentazione(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver)` - Nessuna docstring.
  - `map_opere_da_serramentista(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver)` - Nessuna docstring.
  - `map_apparecchi_sanitari_accessori(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver)` - Nessuna docstring.
  - `map_opere_da_falegname(text: str, text_norm: str, feats: BaseFeatures, resolver: EmbeddingResolver)` - Nessuna docstring.
  - `extract_properties_from_text(text: str, category_id: str)` - Nessuna docstring.
  - `extract_properties(text: str, category_id: str)` - Nessuna docstring.
  - `list_categories()` - Nessuna docstring.
  - `guess_category_id(entry: dict[str, Any])` - Best-effort heuristics to infer category from WBS/description when not provided explicitly.
  - `_apply_override(result: ExtractedProperties, price_list_item_id: Optional[int], session: Session | None = None)` - Nessuna docstring.
  - `extract_properties_auto(entry: dict[str, Any], session: Session | None = None, apply_override: bool = True)` - Convenience wrapper che prova a inferire la categoria e applica override da DB se presenti.
- **Costanti dichiarate (19)**: `BRAND_SYNONYMS`, `CATEGORY_REQUIRED`, `EI_REGEX`, `EMBEDDINGS_DISABLED`, `FIRE_CLASS_REGEX`, `INSULATION_KEYWORDS`, `MATERIAL_SYNONYMS`, `MODEL_NAME`, `NUMBER_PATTERN`, `PEI_REGEX`, `PROPERTY_PROTOTYPES`, `PROPERTY_PROTOTYPE_EMB`, ... (+7)
- **Entry point CLI**: Assente.

### `app/services/nlp/property_extractor.py`
- **Linee**: 736
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (32)**: `__future__.annotations`, `app.services.wbs_predictor.predict_wbs`, `logging`, `os`, `pathlib.Path`, `re`, `robimb.extraction.fuse.Fuser`, `robimb.extraction.matchers.brands.BrandMatcher`, `robimb.extraction.matchers.materials.MaterialMatcher`, `robimb.extraction.orchestrator.Orchestrator`, `robimb.extraction.orchestrator.OrchestratorConfig`, `robimb.extraction.parsers.acoustic.parse_acoustic_coefficient`, ... (+20)
- **Classi**:
  - `PropertyExtractor` (bases: object) - Wrapper sugli estrattori roBERT: usa matchers/parser preconfigurati, senza LLM. Metodi: `list_property_categories`, `extract_properties`, `extract_properties_llm`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (5)**: `DEFAULT_OLLAMA_ENDPOINT`, `DEFAULT_OLLAMA_MODEL`, `REGISTRY_REL_PATH`, `SUPER_CATEGORY_BY_NAME`, `SUPER_CATEGORY_SCHEMA`
- **Entry point CLI**: Assente.

### `app/services/price_catalog.py`
- **Linee**: 205
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (14)**: `__future__.annotations`, `app.core.config.settings`, `app.db.models.Commessa`, `app.db.models.PriceListItem`, `logging`, `nlp.semantic_embedding_service`, `property_extraction.extract_properties_auto`, `sqlalchemy.exc.OperationalError`, `sqlite3`, `sqlmodel.Session`, `time`, `typing.Any`, ... (+2)
- **Classi**:
  - `PriceCatalogService` (bases: object) - Gestisce la persistenza delle voci di elenco prezzi multi-commessa. Metodi: `replace_catalog`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/property_extraction.py`
- **Linee**: 9
- **Descrizione**: Compatibility shim for the legacy import path. All logic now lives in ``app.services.nlp.property_extraction``; this module simply re-exports everything to avoid code drift across duplicated files.
- **Dipendenze principali (1)**: `app.services.nlp.property_extraction.*`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/property_extractor.py`
- **Linee**: 9
- **Descrizione**: Compatibility shim for the legacy property extractor path. The real implementation lives in ``app.services.nlp.property_extractor``; this file keeps existing imports working while avoiding duplicated code.
- **Dipendenze principali (1)**: `app.services.nlp.property_extractor.*`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/serialization_service.py`
- **Linee**: 164
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 4 funzioni.
- **Dipendenze principali (12)**: `app.api.deps.DBSession`, `app.db.models.Commessa`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.PriceListItem`, `app.db.models.PriceListOffer`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceProgetto`, `app.services.wbs_predictor.predict_wbs`, `sqlalchemy.func`, `typing.Any`, `typing.Sequence`
- **Classi**: nessuna.
- **Funzioni**:
  - `serialize_price_list_item(item: PriceListItem, commessa: Commessa, offers: Sequence[PriceListOffer] | None = None, project_quantities: dict[int, float] | None = None)` - Nessuna docstring.
  - `serialize_price_list_offer(offer: PriceListOffer)` - Nessuna docstring.
  - `collect_price_list_offers(session: DBSession, item_ids: Sequence[int])` - Nessuna docstring.
  - `collect_project_quantities(session: DBSession, commessa_id: int | None = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/six_import_service.py`
- **Linee**: 1874
- **Descrizione**: Modulo senza docstring. Contiene 8 classi e 6 funzioni.
- **Dipendenze principali (37)**: `__future__.annotations`, `app.db.models.Commessa`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.VoceComputo`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceOfferta`, `app.db.models_wbs.VoceProgetto`, `app.db.models_wbs.Wbs6`, `app.db.models_wbs.Wbs7`, `app.db.models_wbs.WbsSpaziale`, `app.excel.ParsedComputo`, ... (+25)
- **Classi**:
  - `PreventivoSelectionError` (bases: ValueError) - Richiede che l'utente scelga un preventivo specifico. Metodi: nessun metodo pubblico.
  - `_GroupValue` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `_ProductEntry` (bases: object) - Nessuna docstring. Metodi: `pick_price`.
  - `_AggregatedVoce` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `_MisuraContext` (bases: object) - Nessuna docstring. Metodi: `has_references`.
  - `PreventivoOption` (bases: object) - Nessuna docstring. Metodi: `label`.
  - `SixImportService` (bases: object) - Importa file STR Vision (.six o .xml) popolando WBS, elenco prezzi e computo di progetto. Metodi: `import_six_file`, `inspect_content`, `inspect_details`.
  - `SixParser` (bases: object) - Nessuna docstring. Metodi: `list_preventivi`, `inspect_structure`, `export_price_catalog`, `parse`.
- **Funzioni**:
  - `_load_xml_bytes(file_path: Path)` - Nessuna docstring.
  - `_load_xml_from_upload(file_bytes: bytes, filename: str | None)` - Nessuna docstring.
  - `_normalize_xml_bytes(data: bytes, suffix: str | None)` - Nessuna docstring.
  - `_to_float(value: str | None)` - Nessuna docstring.
  - `_to_int(value: str | None)` - Nessuna docstring.
  - `_evaluate_numeric_expression(text: str)` - Nessuna docstring.
- **Costanti dichiarate (3)**: `MEASURE_QUANTUM`, `_BIN_OPS`, `_UNARY_OPS`
- **Entry point CLI**: Assente.

### `app/services/storage.py`
- **Linee**: 268
- **Descrizione**: Modulo senza docstring. Contiene 2 classi e 0 funzioni.
- **Dipendenze principali (12)**: `__future__.annotations`, `app.core.settings`, `dataclasses.dataclass`, `datetime.datetime`, `fastapi.HTTPException`, `fastapi.UploadFile`, `fastapi.status`, `hashlib.sha256`, `logging`, `mimetypes`, `pathlib.Path`, `shutil`
- **Classi**:
  - `StorageSaveResult` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `StorageService` (bases: object) - Nessuna docstring. Metodi: `commessa_dir`, `save_upload`, `delete_file`, `delete_commessa_dir`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/storage/__init__.py`
- **Linee**: 5
- **Descrizione**: Storage services - file storage and serialization.
- **Dipendenze principali (2)**: `storage_service.StorageService`, `storage_service.storage_service`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/storage/serialization.py`
- **Linee**: 164
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 4 funzioni.
- **Dipendenze principali (12)**: `app.api.deps.DBSession`, `app.db.models.Commessa`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.PriceListItem`, `app.db.models.PriceListOffer`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceProgetto`, `app.services.wbs_predictor.predict_wbs`, `sqlalchemy.func`, `typing.Any`, `typing.Sequence`
- **Classi**: nessuna.
- **Funzioni**:
  - `serialize_price_list_item(item: PriceListItem, commessa: Commessa, offers: Sequence[PriceListOffer] | None = None, project_quantities: dict[int, float] | None = None)` - Nessuna docstring.
  - `serialize_price_list_offer(offer: PriceListOffer)` - Nessuna docstring.
  - `collect_price_list_offers(session: DBSession, item_ids: Sequence[int])` - Nessuna docstring.
  - `collect_project_quantities(session: DBSession, commessa_id: int | None = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/storage/storage_service.py`
- **Linee**: 268
- **Descrizione**: Modulo senza docstring. Contiene 2 classi e 0 funzioni.
- **Dipendenze principali (12)**: `__future__.annotations`, `app.core.settings`, `dataclasses.dataclass`, `datetime.datetime`, `fastapi.HTTPException`, `fastapi.UploadFile`, `fastapi.status`, `hashlib.sha256`, `logging`, `mimetypes`, `pathlib.Path`, `shutil`
- **Classi**:
  - `StorageSaveResult` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `StorageService` (bases: object) - Nessuna docstring. Metodi: `commessa_dir`, `save_upload`, `delete_file`, `delete_commessa_dir`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/wbs_import.py`
- **Linee**: 898
- **Descrizione**: Modulo senza docstring. Contiene 8 classi e 0 funzioni.
- **Dipendenze principali (23)**: `__future__.annotations`, `app.db.models.Commessa`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceOfferta`, `app.db.models_wbs.VoceProgetto`, `app.db.models_wbs.Wbs6`, `app.db.models_wbs.Wbs7`, `app.db.models_wbs.WbsSpaziale`, `dataclasses.dataclass`, `datetime.datetime`, `difflib.SequenceMatcher`, `io.BytesIO`, ... (+11)
- **Classi**:
  - `ParsedSpatialLevel` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ParsedWbsRow` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsImportStats` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `Wbs6NormalizationMatch` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `Wbs7NormalizationMatch` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsNormalizationResult` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsImportService` (bases: object) - Parser e persistenza per file Excel WBS. Metodi: `import_from_upload`, `fetch_commessa_wbs`, `build_normalization_plan_from_excel`, `update_spatial_node`, `update_wbs6_node`, `update_wbs7_node`.
  - `_WbsPersistenceContext` (bases: object) - Upsert atomico dei nodi WBS con statistiche di import. Metodi: `persist`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (4)**: `HEADER_ALIASES`, `HEADER_MARKERS`, `WBS6_CODE_RE`, `WBS7_CODE_RE`
- **Entry point CLI**: Assente.

### `app/services/wbs_predictor.py`
- **Linee**: 68
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (8)**: `__future__.annotations`, `app.core.config.settings`, `functools.lru_cache`, `robimb.inference.category.CategoryInference`, `typing.Any`, `typing.Dict`, `typing.List`, `typing.Optional`
- **Classi**: nessuna.
- **Funzioni**:
  - `_lazy_import_category_inference()` - Nessuna docstring.
  - `_load_predictor(model_path: str | None)` - Nessuna docstring.
  - `predict_wbs(text: str, *, level: int = 6, top_k: int = 3, max_length: int = 320, return_scores: bool = True)` - Predice etichette WBS6/WBS7 usando il modello roBERTino configurato. Args: text: descrizione da classificare level: 6 o 7 top_k: numero di predizioni da restituire max_length: lunghezza massima tokenizzata return_scores: include i punteggi Returns: Lista di dict {"label": ..., "score": ...}
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/services/wbs_visibility.py`
- **Linee**: 190
- **Descrizione**: Modulo senza docstring. Contiene 3 classi e 0 funzioni.
- **Dipendenze principali (10)**: `__future__.annotations`, `app.db.models_wbs.Wbs6`, `app.db.models_wbs.Wbs7`, `app.db.models_wbs.WbsSpaziale`, `app.db.models_wbs.WbsVisibility`, `app.db.models_wbs.WbsVisibilityKind`, `dataclasses.dataclass`, `sqlmodel.Session`, `sqlmodel.select`, `typing.Iterable`
- **Classi**:
  - `WbsVisibilityEntry` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `_NodeDescriptor` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `WbsVisibilityService` (bases: object) - Gestisce le preferenze di visibilità dei raggruppatori WBS (1-7). Metodi: `list_visibility`, `update_visibility`, `hidden_codes_by_level`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `app/utils/__init__.py`
- **Linee**: 1
- **Descrizione**: Shared utility functions.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

## migrations (17 script)

### `migrations/env.py`
- **Linee**: 60
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 2 funzioni.
- **Dipendenze principali (9)**: `__future__.annotations`, `alembic.context`, `app.core.settings`, `app.db.models`, `app.db.models_wbs`, `logging.config.fileConfig`, `sqlalchemy.engine_from_config`, `sqlalchemy.pool`, `sqlmodel.SQLModel`
- **Classi**: nessuna.
- **Funzioni**:
  - `run_migrations_offline()` - Nessuna docstring.
  - `run_migrations_online()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20250204_wbs_schema.py`
- **Linee**: 149
- **Descrizione**: create WBS normalized schema Revision ID: 20250204_wbs_schema Revises: Create Date: 2025-02-04 10:00:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20250207_wbs_import.py`
- **Linee**: 83
- **Descrizione**: add commessa stato and wbs7 commessa link Revision ID: 20250207_wbs_import Revises: 20250204_wbs_schema Create Date: 2025-02-07 10:00:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20250208_wbs_visibility.py`
- **Linee**: 48
- **Descrizione**: add wbs visibility table Revision ID: 20250208_wbs_visibility Revises: 20250207_wbs_import Create Date: 2025-02-08 09:00:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20250218_drop_import_config_wbs_columns.py`
- **Linee**: 30
- **Descrizione**: Remove WBS6 columns from import_config. Revision ID: 20250218_drop_import_config_wbs_columns Revises: 20250218_nlp_settings Create Date: 2025-02-18
- **Dipendenze principali (4)**: `alembic.op`, `sqlalchemy`, `typing.Sequence`, `typing.Union`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20250218_nlp_settings.py`
- **Linee**: 61
- **Descrizione**: Add semantic model settings columns. Revision ID: 20250218_nlp_settings Revises: 20251117_price_list_offer Create Date: 2025-02-18
- **Dipendenze principali (4)**: `alembic.op`, `sqlalchemy`, `typing.Sequence`, `typing.Union`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251110_130728_add_analisi_thresholds.py`
- **Linee**: 41
- **Descrizione**: add analisi thresholds columns Revision ID: 20251110_130728_add_analisi_thresholds Revises: 20250208_wbs_visibility Create Date: 2025-11-10 13:07:28.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (2)**: `DEFAULT_ALTA`, `DEFAULT_MEDIA`
- **Entry point CLI**: Assente.

### `migrations/versions/20251111_price_catalog.py`
- **Linee**: 111
- **Descrizione**: add price catalog and metadata columns Revision ID: 20251111_price_catalog Revises: 20251110_130728_add_analisi_thresholds Create Date: 2025-11-11 19:30:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251114_import_config_quantity_column.py`
- **Linee**: 29
- **Descrizione**: Add quantity column reference to import configurations Revision ID: 20251114_import_config_quantity_column Revises: 20251111_price_catalog Create Date: 2025-11-14 15:00:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251116_import_config_wbs_columns.py`
- **Linee**: 34
- **Descrizione**: Add WBS6 column mapping to import configurations Revision ID: 20251116_import_config_wbs_columns Revises: 20251114_import_config_quantity_column Create Date: 2025-11-16 10:00:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251117_matching_report.py`
- **Linee**: 29
- **Descrizione**: add matching_report column to computo Revision ID: 20251117_matching_report Revises: 20251117_price_list_offer Create Date: 2025-11-17 22:15:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251117_price_list_offer.py`
- **Linee**: 60
- **Descrizione**: add table for price list offers Revision ID: 20251117_price_list_offer Revises: 20251116_import_config_wbs_columns Create Date: 2025-11-17 21:30:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251117_voce_price_list_link.py`
- **Linee**: 38
- **Descrizione**: add price_list_item link to voce Revision ID: 20251117_voce_price_list_link Revises: 20251117_matching_report Create Date: 2025-11-17 22:40:00.000000
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251118_auth_models.py`
- **Linee**: 79
- **Descrizione**: add auth tables
- **Dipendenze principali (3)**: `__future__.annotations`, `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251119_security_hardening.py`
- **Linee**: 41
- **Descrizione**: Add refresh tokens and extend audit log for ISO hardening Revision ID: 20251119_security Revises: 20251118_auth_models Create Date: 2025-11-19 00:00:00.000000
- **Dipendenze principali (2)**: `alembic.op`, `sqlalchemy`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251120_performance_indexes.py`
- **Linee**: 80
- **Descrizione**: Add performance indexes for query optimization Revision ID: 20251120_perf_idx Revises: 20251119_security Create Date: 2025-11-20 10:00:00.000000 This migration adds missing indexes on frequently filtered columns to improve query performance, especially for: - Insights/Analisi queries - Semantic search - Price list...
- **Dipendenze principali (2)**: `__future__.annotations`, `alembic.op`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `migrations/versions/20251121_add_impresa_to_computo.py`
- **Linee**: 43
- **Descrizione**: Add impresa_id to computo and enforce uniqueness per round Revision ID: 20251121_add_impresa_to_computo Revises: 20251120_performance_indexes Create Date: 2025-11-21
- **Dipendenze principali (4)**: `alembic.op`, `sqlalchemy`, `typing.Sequence`, `typing.Union`
- **Classi**: nessuna.
- **Funzioni**:
  - `upgrade()` - Nessuna docstring.
  - `downgrade()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

## robimb (87 script)

### `robimb/__init__.py`
- **Linee**: 16
- **Descrizione**: robimb – BIM NLP toolkit.
- **Dipendenze principali (1)**: `_version.__version__`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/_version.py`
- **Linee**: 5
- **Descrizione**: Package version definition.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/cli/__init__.py`
- **Linee**: 5
- **Descrizione**: Command line utilities for robimb.
- **Dipendenze principali (2)**: `main.app`, `main.run`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/cli/config.py`
- **Linee**: 138
- **Descrizione**: Utility commands to inspect and validate robimb resource paths.
- **Dipendenze principali (8)**: `__future__.annotations`, `config.ResourcePaths`, `config.get_settings`, `json`, `pathlib.Path`, `typer`, `typing.Dict`, `typing.Tuple`
- **Classi**: nessuna.
- **Funzioni**:
  - `_inventory(paths: ResourcePaths)` - Nessuna docstring.
  - `_check_registry_version(registry_path: Path, expected_version: str)` - Nessuna docstring.
  - `show_paths(config_file: Path = typer.Option(None, '--config-file', exists=True, dir_okay=False, readable=True, help="Configurazione TOML/YAML alternativa da usare al posto delle variabili d'ambiente."), refresh: bool = typer.Option(False, '--refresh', help="Ignora la cache e ricostruisce le impostazioni partendo da variabili d'ambiente o file."), check_registry: bool = typer.Option(True, '--check-registry/--no-check-registry', help='Valida la versione del registry rispetto al riferimento di produzione (0.2.0).'))` - Stampa i percorsi risolti dal resolver ``ResourcePaths`` in formato JSON.
  - `generate_lockfile(output: Path = typer.Option(Path('outputs/resource-paths.json'), '--output', dir_okay=False, writable=True, help="File JSON da produrre con l'inventario dei percorsi."), config_file: Path = typer.Option(None, '--config-file', exists=True, dir_okay=False, readable=True, help="Configurazione TOML/YAML alternativa da usare per l'inventario."))` - Persisti un lockfile dei percorsi per tracciarli nelle pipeline CI/CD.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/cli/convert.py`
- **Linee**: 460
- **Descrizione**: CLI command to prepare datasets, label maps and ontology masks using bundled packs.
- **Dipendenze principali (22)**: `__future__.annotations`, `argparse`, `config.get_settings`, `dataclasses.dataclass`, `json`, `numpy`, `os`, `pathlib.Path`, `reporting.generate_dataset_reports`, `typer`, `typing.Iterable`, `typing.List`, ... (+10)
- **Classi**:
  - `ConversionConfig` (bases: object) - Configuration for dataset conversion leveraging the distributed pack. Metodi: `iter_mlm_sources`.
  - `ConversionArtifacts` (bases: object) - Paths produced by :func:`run_conversion`. Metodi: `as_dict`.
- **Funzioni**:
  - `_find_first_existing(base: Path, candidates: Sequence[str])` - Nessuna docstring.
  - `_iter_pack_bases()` - Nessuna docstring.
  - `_resolve_registry_path()` - Nessuna docstring.
  - `_resolve_extractors_path()` - Nessuna docstring.
  - `_validate_inputs_exist(config: ConversionConfig)` - Nessuna docstring.
  - `run_conversion(config: ConversionConfig)` - Execute the conversion pipeline using the bundled pack for extraction.
  - `build_arg_parser()` - Nessuna docstring.
  - `convert_command(train_file: Path = typer.Option(..., '--train-file', exists=True, dir_okay=False, help='Path to raw training JSONL'), val_file: Optional[Path] = typer.Option(None, '--val-file', exists=True, dir_okay=False, help='Optional validation JSONL'), ontology: Optional[Path] = typer.Option(None, '--ontology', exists=True, dir_okay=False, help='Ontology JSON mapping'), label_maps: Path = typer.Option(..., '--label-maps', dir_okay=False, help='Output path for generated label maps'), out_dir: Path = typer.Option(..., '--out-dir', help='Directory that will receive processed data'), done_uids: Optional[Path] = typer.Option(None, '--done-uids', exists=True, dir_okay=False, help='Text file listing UIDs to skip'), val_split: float = typer.Option(0.2, '--val-split', min=0.0, max=0.5, help='Validation ratio when --val-file is missing'), random_state: int = typer.Option(42, '--random-state', help='Random seed used for deterministic splits'), make_mlm_corpus: bool = typer.Option(False, '--make-mlm-corpus', help='Produce MLM/TAPT corpus'), mlm_output: Optional[Path] = typer.Option(None, '--mlm-output', help='Corpus output path when --make-mlm-corpus is set'), extra_mlm: Optional[List[Path]] = typer.Option(None, '--extra-mlm', help='Additional JSONL files contributing text to the MLM corpus', metavar='PATH', show_default=False), reports_dir: Optional[Path] = typer.Option(None, '--reports-dir', help='Directory where dataset plots and summary files will be saved'), properties_registry: Optional[Path] = typer.Option(DEFAULT_PROPERTIES_REGISTRY, '--properties-registry', exists=True, dir_okay=False, help='Optional registry JSON or knowledge pack containing property schemas'), extractors_pack: Optional[Path] = typer.Option(DEFAULT_EXTRACTORS_PACK, '--extractors-pack', exists=True, dir_okay=False, help='Knowledge pack or extractors JSON used to auto-populate property values'), text_field: str = typer.Option('text', '--text-field', help='Column containing the textual description analysed for property extraction'), extract_properties: bool = typer.Option(False, '--extract-properties/--no-extract-properties', help='Extract properties using legacy system (deprecated - use `robimb extract properties` instead)'))` - Typer entrypoint that proxies to :func:`run_conversion`.
  - `main(argv: List[str] | None = None)` - Nessuna docstring.
- **Costanti dichiarate (7)**: `DEFAULT_EXTRACTORS_PACK`, `DEFAULT_PROPERTIES_REGISTRY`, `_DATA_PROPERTIES_DIR`, `_PACK_ROOT`, `_REQUIRED_EXTRACTORS_CANDIDATES`, `_REQUIRED_REGISTRY_CANDIDATES`, `_SETTINGS`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/cli/evaluate.py`
- **Linee**: 262
- **Descrizione**: Evaluate an exported model on a labelled dataset.
- **Dipendenze principali (23)**: `__future__.annotations`, `argparse`, `dataclasses.dataclass`, `datasets.Dataset`, `json`, `models.label_model.load_label_embed_model`, `models.masked_model.load_masked_model`, `numpy`, `pathlib.Path`, `reporting.generate_prediction_reports`, `torch`, `torch.utils.data.DataLoader`, ... (+11)
- **Classi**:
  - `EvaluationConfig` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_build_dataset(path: Path, max_length: int, tokenizer)` - Nessuna docstring.
  - `evaluate_model(config: EvaluationConfig)` - Nessuna docstring.
  - `validate_model(config: EvaluationConfig)` - Compatibility wrapper for the legacy name used by external scripts.
  - `evaluate_command(model_dir: Path = typer.Option(..., '--model-dir', exists=True, file_okay=True, dir_okay=True), test_file: Path = typer.Option(..., '--test-file', exists=True, dir_okay=False), label_maps: Path = typer.Option(..., '--label-maps', exists=True, dir_okay=False), ontology: Optional[Path] = typer.Option(None, '--ontology', dir_okay=False, help='Optional ontology for reporting'), batch_size: int = typer.Option(64, '--batch-size', help='Batch size for evaluation'), max_length: int = typer.Option(256, '--max-length', help='Tokenizer max length'), output: Optional[Path] = typer.Option(None, '--output', help='Path where metrics JSON should be saved'), predictions: Optional[Path] = typer.Option(None, '--predictions', help='Optional JSONL with detailed predictions'), report_dir: Optional[Path] = typer.Option(None, '--report-dir', help='Directory that will host confusion matrices and analytics'))` - Typer entrypoint delegating to :func:`evaluate_model`.
  - `main(argv: List[str] | None = None)` - Nessuna docstring.
  - `build_arg_parser()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/cli/extract.py`
- **Linee**: 598
- **Descrizione**: CLI entrypoints for the property extraction pipeline.
- **Dipendenze principali (42)**: `__future__.annotations`, `asyncio`, `config.get_settings`, `enum.Enum`, `extraction.fuse.FusePolicy`, `extraction.fuse.Fuser`, `extraction.orchestrator.Orchestrator`, `extraction.orchestrator.OrchestratorConfig`, `extraction.orchestrator_async.AsyncOrchestrator`, `extraction.property_qa.QAExample`, `extraction.property_qa.answer_properties`, `extraction.property_qa.build_properties_for_category`, ... (+30)
- **Classi**:
  - `FusionMode` (bases: str, Enum) - Fusion strategies available for candidate selection. Metodi: nessun metodo pubblico.
  - `Engine` (bases: str, Enum) - Extraction engine selector. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `async _extract_async(records: list, llm_endpoint: Optional[str], llm_model: Optional[str], llm_timeout: float, llm_max_retries: int, schema_registry_path: Path, max_workers: int, fail_fast: bool, logger, trace_id: str, *, use_qa: bool, fusion_mode: str, qa_null_threshold: float, qa_confident_threshold: float)` - Async extraction with concurrent processing.
  - `_extract_with_llm(records: list, *, llm_endpoint: Optional[str], llm_model: Optional[str], llm_timeout: float, llm_temperature: float, schema_registry_path: Path, use_rule_candidates: bool, cache_size: int, fail_fast: bool, logger, trace_id: str)` - Sync LLM extraction using the Ollama orchestrator.
  - `extract_properties(input_path: Path = typer.Option(..., '--input', exists=True, dir_okay=False, help='JSONL with input records'), output_path: Path = typer.Option(..., '--output', dir_okay=False, help='Destination JSONL for extracted properties'), pack_path: Path = typer.Option(_SETTINGS.pack_dir / 'current', '--pack', exists=True, file_okay=False, help='Knowledge pack directory providing prompts and lexicons'), schema_registry_path: Path = typer.Option(_SETTINGS.registry_path, '--schema', exists=True, dir_okay=False, help='Path to the schema registry JSON file'), llm_endpoint: Optional[str] = typer.Option(None, '--llm-endpoint', help='LLM endpoint for QA extraction'), llm_model: Optional[str] = typer.Option(None, '--llm-model', help='LLM model identifier'), llm_timeout: float = typer.Option(30.0, '--llm-timeout', help='Timeout for LLM calls in seconds'), llm_max_retries: int = typer.Option(2, '--llm-max-retries', min=0, help='Maximum retries for LLM calls'), category_filter: Optional[str] = typer.Option(None, '--category-filter', help='Limit extraction to a single category (ID or name)'), confidence_threshold: float = typer.Option(0.6, '--confidence-threshold', min=0.0, max=1.0, help='Minimum confidence accepted in the output'), batch_size: int = typer.Option(16, '--batch-size', min=1, help='Number of records processed per batch'), max_workers: int = typer.Option(4, '--max-workers', min=1, help='Parallel workers for the pipeline'), sample: Optional[int] = typer.Option(None, '--sample', min=1, help='Process only first N records for testing'), log_file: Optional[Path] = typer.Option(None, '--log-file', dir_okay=False, help='Optional JSONL log path'), fail_fast: bool = typer.Option(False, '--fail-fast/--no-fail-fast', help='Abort on validation errors'), dry_run: bool = typer.Option(False, '--dry-run', help='Validate configuration without running the pipeline'), use_qa: bool = typer.Option(True, '--use-qa/--no-qa', help='Enable the QA encoder for property spans'), qa_model_dir: Optional[Path] = typer.Option(None, '--qa-model-dir', exists=True, file_okay=False, help='Directory containing the fine-tuned QA model'), qa_null_th: float = typer.Option(0.25, '--qa-null-th', min=0.0, max=2.0, help='QA no-answer threshold'), fusion: FusionMode = typer.Option(FusionMode.FUSE, '--fusion', case_sensitive=False, help='Fusion strategy between rules and QA (choices: rules_only, qa_only, fuse)'), qa_max_length: int = typer.Option(384, '--qa-max-length', min=32, help='Maximum QA sequence length'), qa_doc_stride: int = typer.Option(128, '--qa-doc-stride', min=16, help='QA sliding window stride'), qa_max_answer_length: int = typer.Option(64, '--qa-max-answer-length', min=1, help='Maximum QA answer length'), engine: Engine = typer.Option(Engine.HYBRID, '--engine', case_sensitive=False, help='Extraction engine: hybrid (regole+QA) o llm (Ollama compatto)'), llm_use_rules: bool = typer.Option(True, '--llm-use-rules/--llm-no-rules', help='Precompila suggerimenti dai parser/matcher prima del prompt LLM'), llm_cache_size: int = typer.Option(128, '--llm-cache-size', min=0, help='Cache LLM per evitare richieste duplicate (0 per disabilitare)'), llm_temperature: float = typer.Option(0.0, '--llm-temperature', min=0.0, max=1.0, help='Temperatura passata al modello Ollama'))` - Nessuna docstring.
  - `train_qa_encoder(model: str = typer.Option(..., '--model', help='Base encoder name or local path'), train_jsonl: Path = typer.Option(..., '--train-jsonl', exists=True, dir_okay=False, help='Training QA JSONL'), eval_jsonl: Optional[Path] = typer.Option(None, '--eval-jsonl', exists=True, dir_okay=False, help='Optional evaluation QA JSONL'), out_dir: Path = typer.Option(..., '--out-dir', help='Directory where the fine-tuned model will be stored'), epochs: int = typer.Option(3, '--epochs', min=1, help='Number of fine-tuning epochs'), batch: int = typer.Option(8, '--batch', min=1, help='Per-device batch size'), lr: float = typer.Option(5e-05, '--lr', min=1e-06, help='Learning rate'), max_length: int = typer.Option(384, '--max-length', min=32, help='Maximum sequence length'), doc_stride: int = typer.Option(128, '--doc-stride', min=16, help='Sliding window stride'), seed: int = typer.Option(42, '--seed', help='Random seed'))` - Fine-tune the extractive QA encoder for property spans.
  - `predict_qa_spans(model_dir: Path = typer.Option(..., '--model-dir', exists=True, file_okay=False, help='Directory containing the fine-tuned QA model'), text: str = typer.Option(..., '--text', help='Text to analyse'), category: str = typer.Option(..., '--category', help='Category identifier'), registry: Path = typer.Option(..., '--registry', exists=True, dir_okay=False, help='Schema registry path'), null_th: float = typer.Option(0.25, '--null-th', min=0.0, max=2.0, help='No-answer threshold'), max_length: int = typer.Option(384, '--max-length', min=32, help='Maximum sequence length'), doc_stride: int = typer.Option(128, '--doc-stride', min=16, help='Sliding window stride'), max_answer_length: int = typer.Option(64, '--max-answer-length', min=1, help='Maximum answer token length'))` - Predict property spans for a single text using a QA encoder.
  - `predict_spans(model_dir: Path = typer.Option(..., '--model-dir', exists=True, file_okay=False, help='Directory containing the trained span extractor model'), input_path: Path = typer.Option(..., '--input', exists=True, dir_okay=False, help='JSONL with input records'), output_path: Path = typer.Option(..., '--output', dir_okay=False, help='Destination JSONL for extracted properties'), property_ids: Optional[str] = typer.Option(None, '--properties', help='Comma-separated list of properties to extract (default: all)'), apply_parsers: bool = typer.Option(True, '--parsers/--no-parsers', help='Apply domain-specific parsers to spans'), text_field: str = typer.Option('text', '--text-field', help='Field name containing the text to extract from'))` - Extract properties using the span-based model.
  - `schemas_command(registry_path: Path = typer.Option(_SETTINGS.registry_path, '--registry', exists=True, dir_okay=False, help='Schema registry JSON file'), list_only: bool = typer.Option(False, '--list', help='List available categories'), show: Optional[str] = typer.Option(None, '--show', help='Show details for the provided category ID or name'), print_schema: bool = typer.Option(False, '--print-schema/--no-print-schema', help='Print the JSON schema body'))` - Inspect the available category schemas.
- **Costanti dichiarate (1)**: `_SETTINGS`
- **Entry point CLI**: Assente.

### `robimb/cli/main.py`
- **Linee**: 90
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (14)**: `_version.__version__`, `config.app`, `convert.convert_command`, `evaluate.evaluate_command`, `extract.app`, `json`, `pack.pack_command`, `pathlib.Path`, `predict.app`, `prepare.app`, `train.app`, `typer`, ... (+2)
- **Classi**: nessuna.
- **Funzioni**:
  - `version_callback(ctx: typer.Context, version: bool = typer.Option(False, '--version', help='Show robimb version and exit', is_eager=True))` - Handle global options before any sub-command executes.
  - `sample_categories_command(dataset: Path = typer.Option(..., '--dataset', exists=True, dir_okay=False, help='JSONL di partenza con le descrizioni'), output: Path = typer.Option(..., '--output', dir_okay=False, help='File JSONL di destinazione con una voce per categoria'), category_field: str = typer.Option('cat', '--category-field', help="Nome del campo che identifica la categoria (default: 'cat')"))` - Estrai la prima voce disponibile per ciascuna categoria nel dataset.
  - `run()` - Entry point compatible with ``python -m robimb.cli.main`` and console scripts.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/cli/pack.py`
- **Linee**: 132
- **Descrizione**: Utilities to pack properties folders into versioned knowledge bundles.
- **Dipendenze principali (11)**: `__future__.annotations`, `config.get_settings`, `datetime.datetime`, `json`, `pathlib.Path`, `re`, `registry.pack_folders_to_monolith`, `shutil`, `typer`, `typing.Mapping`, `typing.Optional`
- **Classi**: nessuna.
- **Funzioni**:
  - `_next_version(pack_root: Path)` - Nessuna docstring.
  - `_dump_json(path: Path, payload: Mapping[str, object])` - Nessuna docstring.
  - `_write_manifest(version_dir: Path, version: str)` - Nessuna docstring.
  - `_update_current_symlink(pack_root: Path, target_dir: Path)` - Nessuna docstring.
  - `_write_empty_components(version_dir: Path)` - Nessuna docstring.
  - `pack_command(properties_root: Path = typer.Option(..., '--properties-root', exists=True, file_okay=False), pack_root: Optional[Path] = typer.Option(None, '--pack-root', help='Directory that will contain versioned bundles'), version: Optional[str] = typer.Option(None, '--version', help='Version label for the new bundle (e.g. v3)'), set_current: bool = typer.Option(True, '--set-current/--no-set-current', help='Update the pack/current symlink'), out_registry: Optional[Path] = typer.Option(None, '--out-registry', help='Optional direct output path for registry.json'), out_extractors: Optional[Path] = typer.Option(None, '--out-extractors', help='Optional direct output path for extractors.json'))` - Pack properties folders into versioned bundles or standalone JSON files.
- **Costanti dichiarate (2)**: `_DEFAULT_PACK_ROOT`, `_EMPTY_COMPONENTS`
- **Entry point CLI**: Assente.

### `robimb/cli/predict.py`
- **Linee**: 284
- **Descrizione**: CLI entrypoints for standalone prediction tasks.
- **Dipendenze principali (13)**: `__future__.annotations`, `inference.category.CategoryInference`, `inference.price_inference.PriceInference`, `inference.span_inference.SpanInference`, `json`, `pathlib.Path`, `tqdm.tqdm`, `typer`, `typing.Any`, `typing.Dict`, `typing.Iterable`, `typing.List`, ... (+1)
- **Classi**: nessuna.
- **Funzioni**:
  - `_validate_single_source(text: Optional[str], input_path: Optional[Path])` - Nessuna docstring.
  - `_load_jsonl(path: Path)` - Nessuna docstring.
  - `_write_jsonl(records: Iterable[Dict[str, Any]], path: Optional[Path])` - Nessuna docstring.
  - `_normalise_text(value: Any)` - Nessuna docstring.
  - `_extract_numeric_properties(data: Any)` - Nessuna docstring.
  - `_maybe_iter(records: List[Any], description: str, enabled: bool)` - Nessuna docstring.
  - `_pretty_print(payload: Dict[str, Any], pretty: bool)` - Nessuna docstring.
  - `predict_category_command(model_dir: Path = typer.Option(..., '--model-dir', exists=True, file_okay=True, help='Directory or HF repo containing the classifier'), text: Optional[str] = typer.Option(None, '--text', help='Single text to classify'), input_path: Optional[Path] = typer.Option(None, '--input', exists=True, dir_okay=False, help='JSONL file with records to classify'), output_path: Optional[Path] = typer.Option(None, '--output', dir_okay=False, help='Where to write predictions (JSONL). Defaults to stdout'), text_field: str = typer.Option('text', '--text-field', help='Field containing the text inside JSONL records'), output_field: str = typer.Option('_category_prediction', '--output-field', help='Field added to each record with prediction payload'), top_k: int = typer.Option(5, '--top-k', min=1, help='Number of top categories to keep'), backend: str = typer.Option('auto', '--backend', case_sensitive=False, help='Backend selector: auto, label-embed, sequence-classifier'), label_map_path: Optional[Path] = typer.Option(None, '--label-map', exists=True, dir_okay=False, help='Optional id2label JSON mapping for sequence classifiers'), device: Optional[str] = typer.Option(None, '--device', help='Force device (cpu/cuda)'), include_scores: bool = typer.Option(False, '--include-scores', help='Include logits/probabilities in output'), hf_token: Optional[str] = typer.Option(None, '--hf-token', envvar='HF_TOKEN', help='Hugging Face token for private repos'), pretty: bool = typer.Option(False, '--pretty', help='Pretty-print JSON for single-text mode'), progress: bool = typer.Option(True, '--progress/--no-progress', help='Show progress bar when processing files'))` - Predict BIM categories for a single text or a JSONL dataset.
  - `predict_properties_command(model_dir: Path = typer.Option(..., '--model-dir', exists=True, file_okay=False, help='Directory containing the span extraction model'), text: Optional[str] = typer.Option(None, '--text', help='Single text to extract properties from'), input_path: Optional[Path] = typer.Option(None, '--input', exists=True, dir_okay=False, help='JSONL dataset with product descriptions'), output_path: Optional[Path] = typer.Option(None, '--output', dir_okay=False, help='Destination JSONL (defaults to stdout)'), text_field: str = typer.Option('text', '--text-field', help='Field with the product description'), output_field: str = typer.Option('_property_predictions', '--output-field', help='Field added to records with extracted properties'), property_ids: List[str] = typer.Option([], '--property-id', '-p', help='Limit extraction to specific property IDs'), apply_parsers: bool = typer.Option(True, '--apply-parsers/--raw-spans', help='Apply domain parsers to spans'), batch_size: int = typer.Option(8, '--batch-size', min=1, help='Batch size for dataset mode'), device: Optional[str] = typer.Option(None, '--device', help='Force device (cpu/cuda)'), pretty: bool = typer.Option(False, '--pretty', help='Pretty-print JSON for single-text mode'), progress: bool = typer.Option(True, '--progress/--no-progress', help='Show progress bar when processing files'))` - Extract properties using the trained span extractor.
  - `predict_price_command(model_dir: Path = typer.Option(..., '--model-dir', exists=True, file_okay=False, help='Directory containing the trained price regressor'), text: Optional[str] = typer.Option(None, '--text', help='Single text to score'), properties_json: Optional[str] = typer.Option(None, '--properties-json', help='Inline JSON with properties for single-text mode'), price_unit: str = typer.Option('cad', '--price-unit', help='Price unit for single-text predictions'), input_path: Optional[Path] = typer.Option(None, '--input', exists=True, dir_okay=False, help='JSONL dataset to score'), output_path: Optional[Path] = typer.Option(None, '--output', dir_okay=False, help='Destination JSONL (defaults to stdout)'), text_field: str = typer.Option('text', '--text-field', help='Field containing the text'), properties_field: str = typer.Option('properties', '--properties-field', help='Field containing extracted properties'), price_unit_field: str = typer.Option('price_unit', '--price-unit-field', help='Field containing the price unit'), default_price_unit: str = typer.Option('cad', '--default-price-unit', help='Fallback unit when missing'), output_field: str = typer.Option('_price_prediction', '--output-field', help='Field added to records with price prediction'), use_properties: bool = typer.Option(True, '--use-properties/--no-properties', help='Use properties when available'), device: Optional[str] = typer.Option(None, '--device', help='Force device (cpu/cuda)'), pretty: bool = typer.Option(False, '--pretty', help='Pretty-print JSON for single-text mode'), progress: bool = typer.Option(True, '--progress/--no-progress', help='Show progress bar when processing files'))` - Predict prices using the regression model.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/cli/prepare.py`
- **Linee**: 697
- **Descrizione**: Data preparation command for robimb CLI. Unified command to prepare datasets for classification, span extraction, and price prediction. Handles validation against ontology and label maps from resources/data/wbs.
- **Dipendenze principali (26)**: `__future__.annotations`, `asyncio`, `config.get_settings`, `extraction.legacy.extract_properties`, `extraction.property_qa.prepare_qa_dataset`, `extraction.qa_llm.AsyncHttpLLM`, `extraction.qa_llm.QALLMConfig`, `extraction.qa_llm.build_prompt`, `extraction.schema_registry.load_registry`, `json`, `pandas`, `pathlib.Path`, ... (+14)
- **Classi**: nessuna.
- **Funzioni**:
  - `normalize_price_unit(raw_unit: str)` - Normalize price_unit to standard format.
  - `async extract_properties_with_llm(text: str, category_id: str, registry_path: Path, llm_client: AsyncHttpLLM)` - Extract properties using LLM for a given category.
  - `async process_records_with_llm(records: pd.DataFrame, registry_path: Path, llm_endpoint: str, llm_model: str = 'gpt-4o-mini')` - Process records and extract properties using LLM.
  - `_convert_to_qa_format(df: pd.DataFrame, registry_path: Path)` - Convert dataframe with extracted properties to QA format for span training. For each record with properties, creates QA examples with: - context: original text - question: property-specific question - answers: extracted value with span position in text
  - `validate_and_prepare_base(input_jsonl: Path, label_maps: LabelMaps, task: str)` - Load and validate base dataset.
  - `prepare_classification(input: Path = typer.Option(..., '--input', exists=True, help='Input JSONL with text, super, cat'), output_dir: Path = typer.Option(..., '--output-dir', help='Output directory for processed datasets'), val_input: Optional[Path] = typer.Option(None, '--val-input', exists=True, help='Optional validation JSONL'), val_split: float = typer.Option(0.2, '--val-split', help='Validation split if no val_input'), ontology: Path = typer.Option('resources/data/wbs/ontology.json', '--ontology', help='Path to ontology.json'), label_maps: Path = typer.Option('resources/data/wbs/label_maps.json', '--label-maps', help='Path to label_maps.json'), registry: Optional[Path] = typer.Option(None, '--registry', help=f'Property registry for extraction (default: {_SETTINGS.registry_path})'), llm_endpoint: Optional[str] = typer.Option(None, '--llm-endpoint', help='LLM endpoint for property extraction (e.g., http://localhost:8000/v1/chat/completions)'), llm_model: str = typer.Option('gpt-4o-mini', '--llm-model', help='LLM model to use for extraction'))` - Prepare dataset for classification (text -> super, cat).
  - `prepare_span(input: Path = typer.Option(..., '--input', exists=True, help='Input JSONL with text, super, cat'), output_dir: Path = typer.Option(..., '--output-dir', help='Output directory for span datasets'), val_input: Optional[Path] = typer.Option(None, '--val-input', exists=True, help='Optional validation JSONL'), val_split: float = typer.Option(0.2, '--val-split', help='Validation split'), registry: Path = typer.Option(_SETTINGS.registry_path, '--registry', help='Property registry path'), ontology: Path = typer.Option('resources/data/wbs/ontology.json', '--ontology', help='Path to ontology.json'), label_maps: Path = typer.Option('resources/data/wbs/label_maps.json', '--label-maps', help='Path to label_maps.json'), llm_endpoint: Optional[str] = typer.Option(None, '--llm-endpoint', help='LLM endpoint for property extraction'), llm_model: str = typer.Option('gpt-4o-mini', '--llm-model', help='LLM model to use'))` - Prepare dataset for span extraction (extract properties with LLM, then create QA format).
  - `prepare_price(input: Path = typer.Option(..., '--input', exists=True, help='Input JSONL with text, price, price_unit'), output_dir: Path = typer.Option(..., '--output-dir', help='Output directory'), val_input: Optional[Path] = typer.Option(None, '--val-input', exists=True, help='Optional validation JSONL'), val_split: float = typer.Option(0.2, '--val-split', help='Validation split'), ontology: Path = typer.Option('resources/data/wbs/ontology.json', '--ontology', help='Path to ontology.json'), label_maps: Path = typer.Option('resources/data/wbs/label_maps.json', '--label-maps', help='Path to label_maps.json'), registry: Optional[Path] = typer.Option(None, '--registry', help=f'Property registry for extraction (default: {_SETTINGS.registry_path})'))` - Prepare dataset for price prediction (text -> price, price_unit).
  - `prepare_all(input: Path = typer.Option(..., '--input', exists=True, help='Input JSONL'), output_dir: Path = typer.Option(..., '--output-dir', help='Root output directory'), val_input: Optional[Path] = typer.Option(None, '--val-input', exists=True, help='Optional validation JSONL'), val_split: float = typer.Option(0.2, '--val-split', help='Validation split'), ontology: Path = typer.Option('resources/data/wbs/ontology.json', '--ontology', help='Path to ontology.json'), label_maps: Path = typer.Option('resources/data/wbs/label_maps.json', '--label-maps', help='Path to label_maps.json'), registry: Optional[Path] = typer.Option(None, '--registry', help=f'Property registry path (default: {_SETTINGS.registry_path})'), llm_endpoint: Optional[str] = typer.Option(None, '--llm-endpoint', help='LLM endpoint for property extraction (e.g., http://localhost:8000/v1/chat/completions)'), llm_model: str = typer.Option('gpt-4o-mini', '--llm-model', help='LLM model to use for extraction'))` - Prepare datasets for ALL tasks (classification, span, price) in one go.
- **Costanti dichiarate (1)**: `_SETTINGS`
- **Entry point CLI**: Assente.

### `robimb/cli/train.py`
- **Linee**: 125
- **Descrizione**: Main entry point for model training commands.
- **Dipendenze principali (18)**: `__future__.annotations`, `argparse`, `pathlib.Path`, `sys`, `training.hier_trainer.HierTrainingArgs`, `training.hier_trainer.build_arg_parser`, `training.hier_trainer.train_hier_model`, `training.label_trainer.LabelTrainingArgs`, `training.label_trainer.build_arg_parser`, `training.label_trainer.train_label_model`, `training.price_trainer.PriceTrainingArgs`, `training.price_trainer.build_arg_parser`, ... (+6)
- **Classi**: nessuna.
- **Funzioni**:
  - `main(argv = None)` - Nessuna docstring.
  - `price_command(train_data: Path = typer.Option(..., '--train-data', help='Path to training JSONL file'), output_dir: Path = typer.Option(..., '--output-dir', help='Directory to save model'), backbone_name: str = typer.Option('dbmdz/bert-base-italian-xxl-cased', '--backbone', help='BERT model name'), use_properties: bool = typer.Option(False, '--use-properties/--no-use-properties', help='Use property features'), property_map: Optional[Path] = typer.Option(None, '--property-map', help='JSON mapping property names to IDs'), property_unit_map: Optional[Path] = typer.Option(None, '--property-unit-map', help='JSON mapping properties to units'), epochs: int = typer.Option(10, '--epochs', help='Number of training epochs'), batch_size: int = typer.Option(16, '--batch-size', help='Training batch size'), learning_rate: float = typer.Option(2e-05, '--learning-rate', help='Learning rate'), val_split: float = typer.Option(0.1, '--val-split', help='Validation split ratio'), max_length: int = typer.Option(512, '--max-length', help='Maximum token length'), property_dim: int = typer.Option(64, '--property-dim', help='Property embedding dimension'), unit_dim: int = typer.Option(32, '--unit-dim', help='Unit embedding dimension'), hidden_dims: str = typer.Option('512,256', '--hidden-dims', help='Hidden layer dimensions'), dropout: float = typer.Option(0.1, '--dropout', help='Dropout rate'), seed: int = typer.Option(42, '--seed', help='Random seed'))` - Train the price regression model.
  - `span_command(train_data: Path = typer.Option(..., '--train-data', help='Path to training JSONL file'), output_dir: Path = typer.Option(..., '--output-dir', help='Directory to save model'), epochs: int = typer.Option(10, '--epochs', help='Number of training epochs'), batch_size: int = typer.Option(16, '--batch-size', help='Training batch size'), learning_rate: float = typer.Option(2e-05, '--learning-rate', help='Learning rate'), val_data: Optional[Path] = typer.Option(None, '--val-data', help='Path to validation JSONL'))` - Train the span-based property extractor.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/config.py`
- **Linee**: 256
- **Descrizione**: Centralized configuration and resource resolution for robimb. This module exposes :func:`get_settings` returning the canonical locations for runtime assets such as the knowledge pack, registry and lexicons. Paths can be customized via environment variables or by pointing ``ROBIMB_CONFIG_FILE`` to a TOML/YAML document.
- **Dipendenze principali (10)**: `__future__.annotations`, `dataclasses.dataclass`, `os`, `pathlib.Path`, `tomllib`, `typing.Any`, `typing.Dict`, `typing.Mapping`, `typing.Optional`, `yaml`
- **Classi**:
  - `ResourcePaths` (bases: object) - Resolved filesystem locations for project resources. Metodi: `as_dict`.
- **Funzioni**:
  - `_normalize_path(value: Optional[str | Path], *, base: Optional[Path])` - Nessuna docstring.
  - `_load_config_file(path: Path)` - Nessuna docstring.
  - `_coalesce_mapping(source: Mapping[str, Any] | None)` - Nessuna docstring.
  - `_build_paths(config_file: Optional[Path])` - Nessuna docstring.
  - `get_settings(*, refresh: bool = False, config_file: str | Path | None = None)` - Return the cached :class:`ResourcePaths` configuration. Parameters ---------- refresh: When ``True`` the cached configuration is discarded and recomputed. config_file: Optional explicit path to the configuration document. When provided the returned instance is not cached globally, allowing callers (e.g. tests) to...
  - `reset_settings()` - Clear the cached configuration (mainly useful for tests).
- **Costanti dichiarate (3)**: `_CONFIG_CACHE`, `_CONFIG_SOURCE`, `_PROJECT_ROOT`
- **Entry point CLI**: Assente.

### `robimb/extraction/__init__.py`
- **Linee**: 72
- **Descrizione**: Schema-first property extraction primitives. The :mod:`robimb.extraction` package now exposes the modern building blocks for the hybrid extractor (schema registry, deterministic parsers, upcoming LLM orchestration). The previous regex-based engine is still available under :mod:`robimb.extraction.legacy` and is re-...
- **Dipendenze principali (32)**: `lexicon.load_norms_by_category`, `lexicon.load_producers_by_category`, `matchers.brands.BrandMatcher`, `matchers.materials.MaterialMatcher`, `normalize.normalize_boolean`, `normalize.normalize_confidence`, `normalize.normalize_dimension_mm`, `normalize.normalize_string`, `parsers.colors.RALColor`, `parsers.colors.parse_ral_colors`, `parsers.dimensions.DimensionMatch`, `parsers.dimensions.parse_dimensions`, ... (+20)
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/cartongesso.py`
- **Linee**: 507
- **Descrizione**: Cartongesso feature extraction and catalog matching.
- **Dipendenze principali (10)**: `__future__.annotations`, `csv`, `dataclasses.dataclass`, `functools.lru_cache`, `pathlib.Path`, `re`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Optional`
- **Classi**:
  - `CartongessoLayer` (bases: object) - Single layer within a cartongesso system. Metodi: nessun metodo pubblico.
  - `CartongessoFeatures` (bases: object) - Structured representation extracted from a description. Metodi: `total_thickness_mm`.
  - `CartongessoCatalog` (bases: object) - Utility to load and match catalog configurations. Metodi: `load`, `match_layers`.
  - `InsulationLayer` (bases: object) - Single insulation layer. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_normalize_lines(text: str)` - Nessuna docstring.
  - `_parse_number(value: str)` - Nessuna docstring.
  - `_to_mm(match: Optional[re.Match[str]])` - Nessuna docstring.
  - `_detect_layer_type(text: str)` - Nessuna docstring.
  - `_extract_layers(lines: List[str])` - Nessuna docstring.
  - `_extract_frames(lines: List[str])` - Extract all frame widths from lines.
  - `_extract_frame(lines: List[str], text: str)` - Extract first frame width (legacy compatibility).
  - `_extract_insulations(lines: List[str])` - Extract all insulation layers from lines.
  - `_extract_insulation(lines: List[str])` - Extract first insulation (legacy compatibility).
  - `_extract_rei(text: str)` - Nessuna docstring.
  - `_extract_reaction_class(text: str)` - Nessuna docstring.
  - `_build_stratigrafia(layers: List[CartongessoLayer], frames: List[float], insulations: List[InsulationLayer])` - Build detailed stratigraphy as structured dictionary. Returns: Dict with: - lastre: List of layer objects with id, spessore_mm, tipologia - orditure: List of frame objects with id, larghezza_mm - isolanti: List of insulation objects with id, materiale, spessore_mm, densita_kg_m3 - sequenza: Human-readable sequence...
  - `extract_cartongesso_features(text: str)` - Nessuna docstring.
  - `summarize_cartongesso_features(features: CartongessoFeatures, text: str = '')` - Summarize cartongesso features including all frames and insulations. Args: features: Extracted features from extract_cartongesso_features text: Original text (needed to extract all frames/insulations)
- **Costanti dichiarate (13)**: `CATALOG_PATH`, `_DENSITY_RE`, `_EI_RE`, `_INSULATION_KEYWORDS`, `_LAYER_KEYWORDS`, `_LAYER_LINE_RE`, `_MM_RE`, `_MONTANTE_RE`, `_ORIDITURA_RE`, `_PASSO_RE`, `_PROJECT_ROOT`, `_REACTION_CLASSES`, ... (+1)
- **Entry point CLI**: Assente.

### `robimb/extraction/domain_heuristics.py`
- **Linee**: 549
- **Descrizione**: Domain-specific heuristics for property extraction. Questo modulo fornisce regole euristiche basate su conoscenza del dominio BIM per inferire proprieta' quando rules/matchers/LLM falliscono.
- **Dipendenze principali (13)**: `__future__.annotations`, `cartongesso.CartongessoFeatures`, `cartongesso.extract_cartongesso_features`, `cartongesso.summarize_cartongesso_features`, `json`, `logging`, `parsers.numbers.parse_number_it`, `re`, `typing.Any`, `typing.Dict`, `typing.List`, `typing.MutableMapping`, ... (+1)
- **Classi**: nessuna.
- **Funzioni**:
  - `infer_material(text: str, category: Optional[str] = None)` - Inferisci materiale usando euristiche dominio. Args: text: Testo descrizione category: Categoria BIM (opzionale) Returns: Dict con value, confidence, source se trovato, None altrimenti
  - `infer_installation_type(text: str)` - Inferisci tipologia installazione da keywords. Args: text: Testo descrizione Returns: Dict con value, confidence, source se trovato, None altrimenti
  - `apply_domain_heuristics(text: str, category: str, existing_properties: Dict[str, Any])` - Applica euristiche dominio per riempire gap nelle proprieta'. Questa funzione viene chiamata DOPO rules/matchers e PRIMA di LLM, per cercare di riempire proprieta' mancanti con conoscenza dominio. Args: text: Testo descrizione category: Categoria BIM existing_properties: Proprieta' gia' estratte Returns: Dict con...
  - `validate_material_consistency(material_value: str, text: str, category: str)` - Valida consistenza del materiale estratto con il contesto. Args: material_value: Valore materiale estratto text: Testo originale category: Categoria BIM Returns: Dict con: - is_valid: bool - confidence_adjustment: float (-1.0 a +1.0) - warnings: list di warning se inconsistente
  - `post_process_properties(text: str, category: str, properties_payload: MutableMapping[str, Dict[str, Any]], logger: Optional[logging.Logger] = None)` - Apply heuristics and material validation to the extraction payload.
  - `_apply_cartongesso_properties(features: CartongessoFeatures, text: str, properties_payload: MutableMapping[str, Dict[str, Any]], log: logging.Logger)` - Populate cartongesso-specific properties from extracted features.
- **Costanti dichiarate (7)**: `DIMENSION_KEYS`, `DIMENSION_LABEL_PATTERNS`, `DIMENSION_RANGE_PATTERNS`, `INSTALLATION_TYPE_KEYWORDS`, `MATERIAL_BY_OBJECT_TYPE`, `MATERIAL_KEYWORDS`, `UNIT_TO_MM`
- **Entry point CLI**: Assente.

### `robimb/extraction/fuse.py`
- **Linee**: 139
- **Descrizione**: Candidate fusion policies for property extraction.
- **Dipendenze principali (11)**: `__future__.annotations`, `enum.Enum`, `logging`, `typing.Any`, `typing.Callable`, `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Sequence`, `typing.TypedDict`, `typing.Union`
- **Classi**:
  - `FusePolicy` (bases: str, Enum) - Supported fusion strategies. Metodi: nessun metodo pubblico.
  - `CandidateSource` (bases: str, Enum) - Possible origins for an extracted candidate. Metodi: nessun metodo pubblico.
  - `Candidate` (bases: TypedDict) - Representation of a candidate produced by an extractor. Metodi: nessun metodo pubblico.
  - `Fuser` (bases: object) - Fuse property candidates according to a configurable policy. Metodi: `fuse`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (1)**: `LOGGER`
- **Entry point CLI**: Assente.

### `robimb/extraction/fusion_policy.py`
- **Linee**: 92
- **Descrizione**: Fusion policy between rule-based and QA candidates.
- **Dipendenze principali (7)**: `__future__.annotations`, `dataclasses.dataclass`, `logging`, `typing.Any`, `typing.Dict`, `typing.Optional`, `typing.Tuple`
- **Classi**:
  - `FusionThresholds` (bases: object) - Threshold configuration for QA-based fusion. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_is_valid(candidate: Optional[CandidateDict])` - Nessuna docstring.
  - `fuse_property_candidates(rules_candidate: Optional[CandidateDict], qa_candidate: Optional[CandidateDict], *, fusion_mode: str = 'fuse', thresholds: FusionThresholds = FusionThresholds())` - Return the fused candidate and a textual reason for logging.
- **Costanti dichiarate (1)**: `LOGGER`
- **Entry point CLI**: Assente.

### `robimb/extraction/legacy.py`
- **Linee**: 473
- **Descrizione**: Regex-based property extraction engine used for backwards compatibility. This module rebuilds the legacy regex matcher so that existing utilities such as dataset conversion can continue to operate.
- **Dipendenze principali (13)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Any`, `typing.Callable`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Mapping`, `typing.MutableMapping`, `typing.Optional`, `typing.Sequence`, ... (+1)
- **Classi**:
  - `Pattern` (bases: object) - Compiled representation of a property extraction rule. Metodi: `matches_tags`.
- **Funzioni**:
  - `_ensure_sequence(value: Any)` - Nessuna docstring.
  - `_compile_regex(pattern: str, flags: Flag)` - Nessuna docstring.
  - `_normalize_pattern_spec(spec: Mapping[str, Any])` - Nessuna docstring.
  - `_compile_patterns(pack: Mapping[str, Any], allowed_properties: Optional[Sequence[str]], target_tags: Optional[Sequence[str]])` - Nessuna docstring.
  - `_cache_key(pack: Mapping[str, Any], allowed_properties: Optional[Sequence[str]], target_tags: Optional[Sequence[str]])` - Nessuna docstring.
  - `_extract_value(match: re.Match[str])` - Nessuna docstring.
  - `_apply_map_enum(value: Any, mapping: Mapping[str, Any])` - Nessuna docstring.
  - `_normalize_bool(value: Any)` - Nessuna docstring.
  - `_to_number(value: Any)` - Nessuna docstring.
  - `_to_mm(value: Any, match: Optional[re.Match[str]])` - Nessuna docstring.
  - `_normalize_spaces(value: Any)` - Nessuna docstring.
  - `_normalize_lower(value: Any)` - Nessuna docstring.
  - `_normalize_upper(value: Any)` - Nessuna docstring.
  - `_normalize_ei(value: Any)` - Nessuna docstring.
  - `_normalize_fire_reaction(value: Any)` - Nessuna docstring.
  - `_normalize_pei(value: Any)` - Nessuna docstring.
  - `_normalize_slip_class(value: Any)` - Nessuna docstring.
  - `_normalize_format(value: Any, match: Optional[re.Match[str]])` - Nessuna docstring.
  - `_apply_normalizers(value: Any, normalizers: Sequence[str], pack_normalizers: Mapping[str, Any], match: Optional[re.Match[str]], property_id: str)` - Nessuna docstring.
  - `_iter_matches(text: str, pattern: Pattern)` - Nessuna docstring.
  - `extract_properties(text: str, pack: Mapping[str, Any], *, allowed_properties: Optional[Sequence[str]] = None, target_tags: Optional[Sequence[str]] = None, collect_many: bool = False)` - Extract property values from *text* using the provided *pack*.
  - `dry_run(samples: Iterable[Any], pack: Mapping[str, Any], *, allowed_properties: Optional[Sequence[str]] = None, target_tags: Optional[Sequence[str]] = None)` - Run the extractor on *samples* returning the collected properties.
  - `validate_extractors_pack(pack: Mapping[str, Any])` - Validate the pack returning a list of problems (empty if valid).
- **Costanti dichiarate (4)**: `_BUILTIN_NORMALIZERS`, `_COMPILED_CACHE`, `_DEFAULT_FLAGS`, `_FLAG_ALIASES`
- **Entry point CLI**: Assente.

### `robimb/extraction/lexicon.py`
- **Linee**: 90
- **Descrizione**: High-level loaders for knowledge pack lexicon resources.
- **Dipendenze principali (8)**: `__future__.annotations`, `config.get_settings`, `json`, `pathlib.Path`, `typing.Any`, `typing.Dict`, `typing.Iterable`, `typing.List`
- **Classi**: nessuna.
- **Funzioni**:
  - `_load_json_resource(default_path: str, path: str | Path | None)` - Nessuna docstring.
  - `_group_standards_by_category(entries: Iterable[Dict[str, Any]])` - Nessuna docstring.
  - `load_norms_by_category(path: str | Path | None = None)` - Return the catalogue of reference standards grouped by category.
  - `load_producers_by_category(path: str | Path | None = None)` - Return the curated list of producers grouped by category.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/matchers/__init__.py`
- **Linee**: 14
- **Descrizione**: Lexical matchers for property extraction.
- **Dipendenze principali (6)**: `brands.BrandMatcher`, `brands.load_brand_dataset`, `materials.MaterialMatcher`, `materials.load_material_lexicon`, `norms.StandardMatcher`, `norms.load_standard_dataset`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/matchers/brands.py`
- **Linee**: 269
- **Descrizione**: Matchers and loaders for the brand lexicon.
- **Dipendenze principali (13)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `json`, `pathlib.Path`, `re`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Optional`, `typing.Sequence`, `typing.Tuple`, ... (+1)
- **Classi**:
  - `BrandDefinition` (bases: object) - Definition for a single brand, including synonyms and categories. Metodi: nessun metodo pubblico.
  - `BrandDataset` (bases: object) - Container for the curated brand lexicon. Metodi: nessun metodo pubblico.
  - `BrandMatcher` (bases: object) - Detect known brands with accent-insensitive matching and category filtering. Metodi: `fallback_value`, `find`.
- **Funzioni**:
  - `_normalize_token(token: str)` - Nessuna docstring.
  - `_normalize_text_with_mapping(text: str)` - Nessuna docstring.
  - `_is_word_boundary(text: str, start: int, end: int)` - Nessuna docstring.
  - `load_brand_dataset(path: str | Path | None = None)` - Load the structured brand dataset from disk.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/matchers/materials.py`
- **Linee**: 224
- **Descrizione**: Lexical matcher for materials and finishes.
- **Dipendenze principali (13)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `json`, `logging`, `pathlib.Path`, `re`, `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Sequence`, `typing.Tuple`, ... (+1)
- **Classi**:
  - `MaterialMatch` (bases: object) - Structure describing a material match within a text. ``value`` intentionally exposes the normalised identifier defined in the lexicon (e.g. ``acciaio_inox``) so that downstream consumers can map the match directly to schema enums. ``canonical`` preserves the human readable label for logging or UI needs. Metodi: nessun metodo pubblico.
  - `MaterialDefinition` (bases: object) - Material entry enriched with synonyms and optional regex. Metodi: nessun metodo pubblico.
  - `MaterialMatcher` (bases: object) - Detect mentions of known materials using lexical and regex cues. Metodi: `find`.
- **Funzioni**:
  - `_default_lexicon_paths()` - Nessuna docstring.
  - `_normalize_token(token: str)` - Nessuna docstring.
  - `_normalize_text_with_mapping(text: str)` - Nessuna docstring.
  - `load_material_lexicon(path: str | Path | None = None)` - Load materials, synonyms and regex patterns from disk.
- **Costanti dichiarate (1)**: `LOGGER`
- **Entry point CLI**: Assente.

### `robimb/extraction/matchers/norms.py`
- **Linee**: 164
- **Descrizione**: Matcher for technical standards and regulatory references.
- **Dipendenze principali (12)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `json`, `pathlib.Path`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Optional`, `typing.Sequence`, `typing.Tuple`, `unicodedata`
- **Classi**:
  - `StandardDefinition` (bases: object) - Definition of a standard including synonyms and category coverage. Metodi: nessun metodo pubblico.
  - `StandardMatch` (bases: object) - Match returned by :class:`StandardMatcher`. Metodi: nessun metodo pubblico.
  - `StandardMatcher` (bases: object) - Accent-insensitive matcher for technical standards. Metodi: `find`.
- **Funzioni**:
  - `_normalize_token(token: str)` - Nessuna docstring.
  - `_normalize_text_with_mapping(text: str)` - Nessuna docstring.
  - `load_standard_dataset(path: str | Path | None = None)` - Load the curated standards dataset from disk.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/normalize.py`
- **Linee**: 68
- **Descrizione**: Normalization helpers for property extraction outputs.
- **Dipendenze principali (5)**: `__future__.annotations`, `math`, `typing.Iterable`, `typing.Optional`, `unicodedata`
- **Classi**: nessuna.
- **Funzioni**:
  - `normalize_string(value: str)` - Trim and collapse spaces while applying Unicode normalisation.
  - `normalize_boolean(value: str)` - Convert Italian yes/no markers to boolean values.
  - `normalize_dimension_mm(values: Iterable[float])` - Round millimetre dimensions to one decimal and pad missing axes with ``None``.
  - `normalize_confidence(value: float | None)` - Clamp confidence scores between 0 and 1.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/orchestrator.py`
- **Linee**: 1211
- **Descrizione**: Orchestrates multi-strategy property extraction with cascading fallbacks.
- **Dipendenze principali (41)**: `__future__.annotations`, `config.get_settings`, `domain_heuristics.post_process_properties`, `fuse.Candidate`, `fuse.CandidateSource`, `fuse.Fuser`, `fusion_policy.FusionThresholds`, `fusion_policy.fuse_property_candidates`, `json`, `logging`, `matchers.brands.BrandMatcher`, `matchers.materials.MaterialMatcher`, ... (+29)
- **Classi**:
  - `OrchestratorConfig` (bases: BaseModel) - Configuration for the property extraction orchestrator. Metodi: nessun metodo pubblico.
  - `Orchestrator` (bases: object) - Coordinate deterministic parsers, matchers and LLM fallbacks. Metodi: `extract_document`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (11)**: `LOGGER`, `PROPERTY_EXTRA_HINTS`, `_EI_CLASS_PATTERN`, `_ISOLANTE_NEGATIVE_PATTERN`, `_ISOLANTE_PATTERN`, `_LENGTH_RANGE_PATTERN`, `_ORDITURA_PATTERN`, `_SKIRTING_PATTERN`, `_TIPOLOGIA_KEYWORDS`, `_TOTAL_THICKNESS_PATTERN`, `_WIDTH_RANGE_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/orchestrator_async.py`
- **Linee**: 177
- **Descrizione**: Async orchestrator for parallel property extraction with LLM.
- **Dipendenze principali (25)**: `__future__.annotations`, `domain_heuristics.post_process_properties`, `fuse.Candidate`, `fuse.CandidateSource`, `fuse.Fuser`, `logging`, `matchers.brands.BrandMatcher`, `matchers.materials.MaterialMatcher`, `orchestrator_base.OrchestratorBase`, `orchestrator_base.OrchestratorConfig`, `parsers.acoustic.parse_acoustic_coefficient`, `parsers.colors.parse_ral_colors`, ... (+13)
- **Classi**:
  - `AsyncOrchestrator` (bases: OrchestratorBase) - Async orchestrator for parallel LLM-based property extraction. Metodi: `extract_document`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (2)**: `LOGGER`, `PROPERTY_EXTRA_HINTS`
- **Entry point CLI**: Assente.

### `robimb/extraction/orchestrator_base.py`
- **Linee**: 990
- **Descrizione**: Shared infrastructure for property extraction orchestrators. This module defines the :class:`OrchestratorBase` template that centralises the deterministic extraction logic (parsers, matchers, validation, payload construction) used by both synchronous and asynchronous orchestrators. Concrete implementations only need...
- **Dipendenze principali (31)**: `__future__.annotations`, `abc.ABC`, `config.get_settings`, `fuse.Candidate`, `fuse.Fuser`, `logging`, `matchers.brands.BrandMatcher`, `matchers.materials.MaterialMatcher`, `matchers.norms.StandardMatcher`, `parsers.colors.parse_ral_colors`, `parsers.dimensions`, `parsers.numbers`, ... (+19)
- **Classi**:
  - `OrchestratorConfig` (bases: BaseModel) - Configuration for the property extraction orchestrators. Metodi: nessun metodo pubblico.
  - `OrchestratorBase` (bases: ABC) - Base class exposing shared extraction utilities. Sub-classes are expected to orchestrate the execution flow (synchronous or asynchronous) while relying on these helpers for deterministic candidate generation, validation and payload construction. Metodi: nessun metodo pubblico.
- **Funzioni**: nessuna.
- **Costanti dichiarate (11)**: `LOGGER`, `_EI_CLASS_PATTERN`, `_ISOLANTE_NEGATIVE_PATTERN`, `_ISOLANTE_PATTERN`, `_LENGTH_RANGE_PATTERN`, `_ORDITURA_PATTERN`, `_SECTION_PROFILE_KEYWORDS`, `_SKIRTING_PATTERN`, `_TIPOLOGIA_KEYWORDS`, `_TOTAL_THICKNESS_PATTERN`, `_WIDTH_RANGE_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/__init__.py`
- **Linee**: 16
- **Descrizione**: Parser primitives for deterministic property extraction.
- **Dipendenze principali (8)**: `dimensions.DimensionMatch`, `dimensions.parse_dimensions`, `numbers.NumberSpan`, `numbers.extract_numbers`, `numbers.parse_number_it`, `units.UnitMatch`, `units.normalize_unit`, `units.scan_units`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/acoustic.py`
- **Linee**: 61
- **Descrizione**: Parser for acoustic absorption coefficient (αw values).
- **Dipendenze principali (5)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `AcousticMatch` (bases: object) - Match for acoustic absorption coefficient. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `parse_acoustic_coefficient(text: str)` - Yield acoustic absorption coefficient matches (αw values).
- **Costanti dichiarate (1)**: `_ACOUSTIC_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/colors.py`
- **Linee**: 36
- **Descrizione**: Parser for RAL colour codes using a curated lexicon.
- **Dipendenze principali (9)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `json`, `pathlib.Path`, `re`, `typing.Dict`, `typing.Iterable`, `typing.Optional`
- **Classi**:
  - `RALColor` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `load_ral_lexicon(path: str | Path | None = None)` - Nessuna docstring.
  - `parse_ral_colors(text: str, lexicon: Optional[Dict[str, str]] = None)` - Nessuna docstring.
- **Costanti dichiarate (1)**: `_RAL_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/dimensions.py`
- **Linee**: 215
- **Descrizione**: Deterministic parsers for dimensional expressions.
- **Dipendenze principali (11)**: `__future__.annotations`, `dataclasses.dataclass`, `itertools.zip_longest`, `numbers.parse_number_it`, `re`, `typing.Iterable`, `typing.Iterator`, `typing.List`, `typing.Sequence`, `typing.Tuple`, `units.normalize_unit`
- **Classi**:
  - `DimensionMatch` (bases: object) - Normalized dimension parsed from text. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_convert_unitless_value(value: float, raw: str, sequence_max: float)` - Nessuna docstring.
  - `_convert(values: Sequence[str], units: Sequence[str | None], fallback_unit: str, explicit_unit: bool)` - Nessuna docstring.
  - `_fallback_unit(global_unit: str | None, *units: str | None)` - Nessuna docstring.
  - `_iter_cross(text: str)` - Nessuna docstring.
  - `_extract_numbers_from_labelled(raw: str)` - Nessuna docstring.
  - `_iter_labelled(text: str)` - Nessuna docstring.
  - `parse_dimensions(text: str)` - Yield normalized dimensions (values in millimetres).
- **Costanti dichiarate (3)**: `_CROSS_PATTERN`, `_LABELLED_PATTERN`, `_UNIT_FACTORS`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/fire_class.py`
- **Linee**: 59
- **Descrizione**: Parser for fire reaction classes (Euroclasses).
- **Dipendenze principali (5)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `FireClassMatch` (bases: object) - Match for fire reaction class. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `parse_fire_class(text: str)` - Yield fire reaction class matches (Euroclasses).
- **Costanti dichiarate (1)**: `_FIRE_CLASS_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/flow_rate.py`
- **Linee**: 87
- **Descrizione**: Parser for flow rate expressions (l/min, l/s, etc.).
- **Dipendenze principali (6)**: `__future__.annotations`, `dataclasses.dataclass`, `numbers.parse_number_it`, `re`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `FlowRateMatch` (bases: object) - Normalized flow rate parsed from text. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_normalize_to_l_per_min(value: float, unit: str)` - Convert flow rate to l/min.
  - `parse_flow_rate(text: str)` - Yield normalized flow rate matches (values in l/min).
- **Costanti dichiarate (1)**: `_FLOW_RATE_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/installation_type.py`
- **Linee**: 53
- **Descrizione**: Parser for installation type (e.g., 'a terra', 'a parete', 'sospeso').
- **Dipendenze principali (5)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `InstallationTypeMatch` (bases: object) - Match for installation type. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `parse_installation_type(text: str)` - Yield installation type matches.
- **Costanti dichiarate (1)**: `_INSTALLATION_PATTERNS`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/labeled_dimensions.py`
- **Linee**: 85
- **Descrizione**: Parser for explicitly labeled dimensions (e.g., 'lunghezza 60 cm', 'larghezza 80 mm').
- **Dipendenze principali (7)**: `__future__.annotations`, `dataclasses.dataclass`, `numbers.parse_number_it`, `re`, `typing.Dict`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `LabeledDimensionMatch` (bases: object) - A dimension with an explicit label. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `parse_labeled_dimensions(text: str)` - Yield explicitly labeled dimension matches (values in mm).
- **Costanti dichiarate (2)**: `_LABELED_DIM_PATTERN`, `_UNIT_TO_MM`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/numbers.py`
- **Linee**: 91
- **Descrizione**: Utilities to parse Italian-formatted numbers and locate them in text.
- **Dipendenze principali (6)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Iterable`, `typing.Iterator`, `typing.Optional`
- **Classi**:
  - `NumberSpan` (bases: object) - Representation of a numeric value extracted from text. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_normalize_numeric_string(raw: str)` - Nessuna docstring.
  - `parse_number_it(raw: str)` - Parse an Italian-formatted number string into a float.
  - `_iter_number_matches(text: str)` - Nessuna docstring.
  - `extract_numbers(text: str)` - Extract numeric spans from ``text`` using Italian number heuristics.
- **Costanti dichiarate (5)**: `_DECIMAL_BODY`, `_NUMBER_PATTERN`, `_SIGN`, `_STRIP_CHARS`, `_THOUSANDS_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/sound_insulation.py`
- **Linee**: 56
- **Descrizione**: Parser for airborne sound insulation values (Rw in dB).
- **Dipendenze principali (5)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `SoundInsulationMatch` (bases: object) - Match describing a sound insulation value in decibel. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `parse_sound_insulation(text: str)` - Nessuna docstring.
- **Costanti dichiarate (1)**: `_SOUND_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/standards.py`
- **Linee**: 56
- **Descrizione**: Parser detecting technical standards codes such as UNI EN ISO.
- **Dipendenze principali (9)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `json`, `pathlib.Path`, `re`, `typing.Dict`, `typing.Iterable`, `typing.Optional`
- **Classi**:
  - `StandardMatch` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `load_standard_prefixes(path: str | Path | None = None)` - Nessuna docstring.
  - `parse_standards(text: str, lexicon: Optional[Dict[str, str]] = None)` - Nessuna docstring.
- **Costanti dichiarate (1)**: `_STANDARD_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/thermal.py`
- **Linee**: 84
- **Descrizione**: Parser for thermal transmittance values (Uw, Uf, Ug).
- **Dipendenze principali (5)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `ThermalTransmittanceMatch` (bases: object) - Match describing a transmittance value in W/m²K. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_normalise_label(label: str)` - Nessuna docstring.
  - `parse_thermal_transmittance(text: str)` - Nessuna docstring.
- **Costanti dichiarate (1)**: `_TRANS_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/thickness.py`
- **Linee**: 76
- **Descrizione**: Parser for explicitly labeled thickness values.
- **Dipendenze principali (6)**: `__future__.annotations`, `dataclasses.dataclass`, `numbers.parse_number_it`, `re`, `typing.Iterator`, `typing.Tuple`
- **Classi**:
  - `ThicknessMatch` (bases: object) - A thickness value with explicit label. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `parse_thickness(text: str)` - Yield explicitly labeled thickness matches (values in mm).
- **Costanti dichiarate (2)**: `_THICKNESS_PATTERN`, `_UNIT_TO_MM`
- **Entry point CLI**: Assente.

### `robimb/extraction/parsers/units.py`
- **Linee**: 193
- **Descrizione**: Canonicalise measurement units used in property extraction.
- **Dipendenze principali (6)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Iterable`, `typing.Iterator`, `typing.Optional`
- **Classi**:
  - `UnitMatch` (bases: object) - Unit mention located in text. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_normalize_token(token: str)` - Lowercase token and strip spaces/underscores/dots after unrolling superscripts.
  - `_alias_to_regex(alias: str)` - Build a regex that matches the alias allowing optional whitespace around slashes and treating underscores as optional separators.
  - `_build_unit_pattern()` - Nessuna docstring.
  - `normalize_unit(token: Optional[str])` - Return the canonical representation of ``token`` if recognised.
  - `_iter_unit_tokens(text: str)` - Nessuna docstring.
  - `scan_units(text: str)` - Find and normalise measurement units inside ``text``.
- **Costanti dichiarate (4)**: `_CANONICAL_UNITS`, `_NORMALIZED_ALIASES`, `_SUPERSCRIPTS`, `_UNIT_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/prompts.py`
- **Linee**: 80
- **Descrizione**: Lightweight prompt templating utilities for the hybrid extractor.
- **Dipendenze principali (8)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `json`, `pathlib.Path`, `re`, `typing.Dict`, `typing.Mapping`
- **Classi**:
  - `PromptTemplate` (bases: object) - A prompt template with metadata and a render helper. Metodi: `render`.
  - `PromptLibrary` (bases: object) - Container mapping prompt identifiers to templates. Metodi: `render`, `template`, `from_path`, `default`.
- **Funzioni**:
  - `load_prompt_library(path: str | Path | None = None)` - Load the prompt library from ``path`` or use the default location.
- **Costanti dichiarate (1)**: `_PLACEHOLDER_PATTERN`
- **Entry point CLI**: Assente.

### `robimb/extraction/property_qa.py`
- **Linee**: 652
- **Descrizione**: Property-aware extractive QA utilities built on top of transformer encoders.
- **Dipendenze principali (27)**: `__future__.annotations`, `argparse`, `dataclasses.dataclass`, `json`, `logging`, `pandas`, `pathlib.Path`, `schema_registry.load_registry`, `torch`, `torch.utils.data.DataLoader`, `torch.utils.data.Dataset`, `transformers.AutoModelForQuestionAnswering`, ... (+15)
- **Classi**:
  - `QAExample` (bases: object) - Single QA training/prediction example. Metodi: `from_json`.
  - `PropertyQADataset` (bases: Dataset) - Torch dataset converting :class:`QAExample` objects into QA features. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `load_registry(registry_path: Path | str)` - Convenience wrapper returning the schema registry object.
  - `default_prompt_for(category_name: str, property_title: str)` - Return a default Italian QA prompt for the given property.
  - `build_properties_for_category(category_id: str, registry_path: Path | str)` - Return list of tuples ``(property_id, question)`` for a category.
  - `prepare_qa_dataset(train_path: Path | str, val_path: Path | str | None, property_registry_path: Path | str, label_maps: Any, val_split: float = 0.2)` - Prepare QA dataset from JSONL with extraction. Returns: Tuple of (train_df, val_df) as pandas DataFrames
  - `make_jsonl_from_rule_outputs(rule_output_path: Path | str, registry_path: Path | str, destination: Path | str)` - Create QA training data from rule-based extraction outputs.
  - `_load_examples(jsonl_path: Path | str)` - Nessuna docstring.
  - `train_property_qa(model_name: str, train_jsonl: Path | str, *, eval_jsonl: Path | str | None = None, out_dir: Path | str, epochs: int = 3, batch_size: int = 8, learning_rate: float = 5e-05, max_length: int = 384, doc_stride: int = 128, seed: int = 42)` - Fine-tune a QA encoder on property-level examples.
  - `predict_with_encoder(model: PreTrainedModel, tokenizer: PreTrainedTokenizerBase, examples: Sequence[QAExample], *, max_length: int = 384, doc_stride: int = 128, max_answer_length: int = 64, null_threshold: float = 0.25, batch_size: int = 8)` - Run extractive QA and return spans per property id.
  - `answer_properties(model_dir: Path | str, text: str, category_id: str, registry_path: Path | str, *, null_threshold: float = 0.25, max_length: int = 384, doc_stride: int = 128, max_answer_length: int = 64)` - High-level helper creating prompts and returning property spans.
  - `_build_arg_parser()` - Nessuna docstring.
  - `_cmd_train(args: argparse.Namespace)` - Nessuna docstring.
  - `_cmd_predict(args: argparse.Namespace)` - Nessuna docstring.
  - `main(argv: Optional[Sequence[str]] = None)` - Nessuna docstring.
- **Costanti dichiarate (1)**: `LOGGER`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/extraction/qa_llm.py`
- **Linee**: 159
- **Descrizione**: Adapters for question-answering large language models.
- **Dipendenze principali (15)**: `__future__.annotations`, `aiohttp`, `asyncio`, `json`, `logging`, `prompts.load_prompt_library`, `pydantic.BaseModel`, `pydantic.Field`, `time`, `typing.Any`, `typing.Dict`, `typing.Optional`, ... (+3)
- **Classi**:
  - `QALLMConfig` (bases: BaseModel) - Configuration for QA-oriented LLM clients. Metodi: nessun metodo pubblico.
  - `QALLM` (bases: Protocol) - Protocol implemented by QA-capable LLM adapters. Metodi: `ask`.
  - `HttpLLM` (bases: QALLM) - HTTP client calling an external LLM endpoint. Metodi: `ask`.
  - `MockLLM` (bases: QALLM) - Fallback implementation used when no endpoint is configured. Metodi: `ask`.
  - `AsyncHttpLLM` (bases: object) - Async HTTP client for parallel LLM requests. Metodi: `ask`.
- **Funzioni**:
  - `build_prompt(text: str, question: str, schema: Dict[str, Any])` - Construct a deterministic prompt instructing the model to output JSON.
- **Costanti dichiarate (1)**: `LOGGER`
- **Entry point CLI**: Assente.

### `robimb/extraction/schema_registry.py`
- **Linee**: 145
- **Descrizione**: Schema registry utilities for property extraction.
- **Dipendenze principali (11)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `functools.lru_cache`, `json`, `pathlib.Path`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Optional`, `typing.Sequence`
- **Classi**:
  - `PropertySpec` (bases: object) - Metadata describing a property expected in a category schema. Metodi: nessun metodo pubblico.
  - `CategorySchema` (bases: object) - Logical schema describing a category. Metodi: `property_ids`.
  - `SchemaRegistry` (bases: object) - Load and query category schemas. Metodi: `list`, `get`.
- **Funzioni**:
  - `load_registry(registry_path: Path | str | None = None)` - Load and cache the registry located at ``registry_path``.
  - `load_category_schema(category_id: str, *, registry_path: Path | str | None = None)` - Return the :class:`CategorySchema` metadata and JSON schema body. Parameters ---------- category_id: Identifier of the category to load. registry_path: Path to the registry JSON file. Defaults to the project-wide registry. Returns ------- tuple[CategorySchema, Dict[str, Any]] The dataclass describing the category...
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/extraction/smart_pipeline.py`
- **Linee**: 338
- **Descrizione**: End-to-end pipeline: Classification + Span Extraction + Parsing. This pipeline combines: 1. roBERTino: BIM category classification 2. Span Extractor: Find relevant text spans for properties 3. Parsers/Regex: Extract structured values from spans
- **Dipendenze principali (16)**: `__future__.annotations`, `dotenv.load_dotenv`, `json`, `os`, `pathlib.Path`, `robimb.extraction.parsers.dimensions.parse_dimension_pattern`, `robimb.extraction.parsers.units.parse_number_with_unit`, `robimb.models.label_model.load_label_embed_model`, `robimb.models.span_extractor.PropertyExtractorPipeline`, `robimb.models.span_extractor.PropertySpanExtractor`, `torch`, `transformers.AutoTokenizer`, ... (+4)
- **Classi**:
  - `SmartExtractionPipeline` (bases: object) - Complete extraction pipeline: classify → find spans → parse values. Metodi: `classify`, `extract_properties`, `process`.
- **Funzioni**:
  - `demo()` - Demo of complete pipeline.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/extraction/validators.py`
- **Linee**: 229
- **Descrizione**: Validation helpers for schema-first property extraction.
- **Dipendenze principali (17)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `fuse.CandidateSource`, `pathlib.Path`, `pydantic.BaseModel`, `pydantic.ConfigDict`, `pydantic.Field`, `pydantic.ValidationError`, `pydantic.field_validator`, `schema_registry.CategorySchema`, `schema_registry.PropertySpec`, ... (+5)
- **Classi**:
  - `PropertyPayload` (bases: BaseModel) - Pydantic model describing the payload of a single property. Metodi: nessun metodo pubblico.
  - `ValidationIssue` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ValidationResult` (bases: object) - Nessuna docstring. Metodi: `ok`.
- **Funzioni**:
  - `_coerce_value(property_spec: PropertySpec, payload: PropertyPayload, errors: list[ValidationIssue])` - Nessuna docstring.
  - `_validate_enum(property_spec: PropertySpec, value: Any, errors: list[ValidationIssue])` - Nessuna docstring.
  - `_validate_unit(property_spec: PropertySpec, payload: PropertyPayload, errors: list[ValidationIssue])` - Nessuna docstring.
  - `_validate_required(category: CategorySchema, provided: Iterable[str], errors: list[ValidationIssue])` - Nessuna docstring.
  - `validate_properties(category_id: str, properties: Mapping[str, Mapping[str, Any]], *, registry_path: str | Path | None = None)` - Validate a property payload against the category schema.
- **Costanti dichiarate (1)**: `ALLOWED_SOURCES`
- **Entry point CLI**: Assente.

### `robimb/inference/__init__.py`
- **Linee**: 7
- **Descrizione**: High level inference helpers exposed by :mod:`robimb`.
- **Dipendenze principali (3)**: `category.CategoryInference`, `price_inference.PriceInference`, `span_inference.SpanInference`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/inference/calibration.py`
- **Linee**: 37
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (6)**: `__future__.annotations`, `dataclasses.dataclass`, `torch`, `torch.nn.functional`, `typing.Optional`, `typing.Tuple`
- **Classi**:
  - `TemperatureCalibrator` (bases: object) - Nessuna docstring. Metodi: `apply`, `fit_from_logits`, `state_dict`, `from_state_dict`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/inference/category.py`
- **Linee**: 437
- **Descrizione**: Category inference utilities. This module exposes :class:`CategoryInference`, a lightweight helper that wraps either the domain-specific :class:`~robimb.models.label_model.LabelEmbedModel` classifier or generic Hugging Face sequence classification checkpoints. The goal is to offer a unified interface for CLI...
- **Dipendenze principali (15)**: `__future__.annotations`, `dataclasses.dataclass`, `json`, `models.label_model.LabelEmbedModel`, `pathlib.Path`, `safetensors.torch.load_file`, `torch`, `torch.nn.functional`, `transformers.AutoConfig`, `transformers.AutoModelForSequenceClassification`, `transformers.AutoTokenizer`, `typing.Dict`, ... (+3)
- **Classi**:
  - `ScoredLabel` (bases: object) - Container for a label scored by the classifier. Metodi: `to_dict`.
  - `CategoryInference` (bases: object) - Unified interface for category prediction models. Metodi: `predict`, `predict_batch`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/inference/price_inference.py`
- **Linee**: 181
- **Descrizione**: Inference utilities for price prediction.
- **Dipendenze principali (15)**: `__future__.annotations`, `dotenv.load_dotenv`, `json`, `models.price_regressor.PRICE_UNIT_MAP`, `models.price_regressor.PricePredictionPipeline`, `models.price_regressor.PriceRegressor`, `models.price_regressor.UNIT_MAP`, `os`, `pathlib.Path`, `safetensors.torch.load_file`, `torch`, `transformers.AutoTokenizer`, ... (+3)
- **Classi**:
  - `PriceInference` (bases: object) - Price prediction inference wrapper. Metodi: `predict`, `predict_batch`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/inference/span_inference.py`
- **Linee**: 264
- **Descrizione**: Inference utilities for span-based property extraction.
- **Dipendenze principali (14)**: `__future__.annotations`, `dotenv.load_dotenv`, `extraction.parsers.dimensions.parse_dimensions`, `extraction.parsers.numbers.extract_numbers`, `json`, `models.span_extractor.PropertyExtractorPipeline`, `models.span_extractor.PropertySpanExtractor`, `os`, `pathlib.Path`, `torch`, `transformers.AutoTokenizer`, `typing.Dict`, ... (+2)
- **Classi**:
  - `SpanInference` (bases: object) - Combines span extraction model with domain-specific parsers. Metodi: `extract_properties`, `extract_batch`.
- **Funzioni**:
  - `apply_parser_to_span(raw_text: str, property_id: str, full_text: str)` - Apply appropriate parser/regex to extracted span. Args: raw_text: The text span extracted by the model property_id: Which property we're extracting full_text: Full context (for better parsing) Returns: Dict with parsed value, unit, confidence, etc.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/llm/__init__.py`
- **Linee**: 15
- **Descrizione**: Lightweight LLM helpers (Ollama client, prompting, orchestration).
- **Dipendenze principali (7)**: `ollama_client.OllamaClient`, `ollama_client.OllamaConfig`, `ollama_client.generate`, `pipeline.LLMExtractionConfig`, `pipeline.LLMPropertyExtractor`, `pipeline.RuleCandidateGenerator`, `prompting.build_llm_prompt`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/llm/ollama_client.py`
- **Linee**: 86
- **Descrizione**: Minimal HTTP client for local Ollama models.
- **Dipendenze principali (8)**: `__future__.annotations`, `dataclasses.dataclass`, `logging`, `os`, `requests`, `typing.Any`, `typing.Dict`, `typing.Optional`
- **Classi**:
  - `OllamaConfig` (bases: object) - Configuration for the Ollama client. Metodi: nessun metodo pubblico.
  - `OllamaClient` (bases: object) - Very small wrapper over the Ollama HTTP API. Metodi: `generate`.
- **Funzioni**:
  - `generate(model_name: str, prompt: str, *, endpoint: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT, options: Optional[Dict[str, Any]] = None)` - Convenience function mirroring :meth:`OllamaClient.generate`.
- **Costanti dichiarate (4)**: `DEFAULT_MODEL`, `DEFAULT_OLLAMA_URL`, `DEFAULT_TIMEOUT`, `LOGGER`
- **Entry point CLI**: Assente.

### `robimb/llm/pipeline.py`
- **Linee**: 301
- **Descrizione**: Pipeline that orchestrates deterministic cues with a compact Ollama prompt.
- **Dipendenze principali (31)**: `__future__.annotations`, `collections.OrderedDict`, `config.get_settings`, `copy`, `dataclasses.dataclass`, `dataclasses.field`, `extraction.fuse.CandidateSource`, `extraction.fuse.FusePolicy`, `extraction.fuse.Fuser`, `extraction.orchestrator.Orchestrator`, `extraction.orchestrator.OrchestratorConfig`, `extraction.schema_registry.CategorySchema`, ... (+19)
- **Classi**:
  - `_ExtractionCache` (bases: object) - Tiny LRU cache to avoid repeated LLM calls on identical inputs. Metodi: `get`, `put`.
  - `LLMExtractionConfig` (bases: object) - Configuration for the Ollama-based property extractor. Metodi: nessun metodo pubblico.
  - `RuleCandidateGenerator` (bases: object) - Reuse deterministic parsers/matchers to propose candidate values. Metodi: `build`.
  - `LLMPropertyExtractor` (bases: object) - Orchestrate rule-based hints with an Ollama prompt to fill property JSON. Metodi: `extract`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (1)**: `LOGGER`
- **Entry point CLI**: Assente.

### `robimb/llm/prompting.py`
- **Linee**: 64
- **Descrizione**: Compact prompt builder for Ollama-based property extraction.
- **Dipendenze principali (6)**: `__future__.annotations`, `extraction.schema_registry.PropertySpec`, `json`, `typing.Any`, `typing.Mapping`, `typing.Sequence`
- **Classi**: nessuna.
- **Funzioni**:
  - `_summarize_properties(properties: Sequence[PropertySpec])` - Nessuna docstring.
  - `build_llm_prompt(category_id: str, description: str, properties: Sequence[PropertySpec], *, candidates: Mapping[str, Any] | None = None)` - Build a concise, deterministic prompt for the small LLM.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/models/__init__.py`
- **Linee**: 12
- **Descrizione**: Model implementations used across the BIM NLP project.
- **Dipendenze principali (5)**: `label_model.LabelEmbedModel`, `label_model.load_label_embed_model`, `masked_model.ArcMarginProduct`, `masked_model.MultiTaskBERTMasked`, `masked_model.load_masked_model`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/models/label_model.py`
- **Linee**: 467
- **Descrizione**: Label embedding classifier with ontology-aware masking. This module exposes :class:`LabelEmbedModel`, a Transformer-based classifier that scores classes by comparing document embeddings with label prototypes. The implementation is adapted from the historical ``robert`` package and refactored to live in the...
- **Dipendenze principali (12)**: `__future__.annotations`, `os`, `safetensors.torch.load_file`, `safetensors.torch.save_file`, `torch`, `torch.nn`, `torch.nn.functional`, `transformers.AutoConfig`, `transformers.AutoModel`, `transformers.AutoTokenizer`, `typing.List`, `typing.Optional`
- **Classi**:
  - `MeanPool` (bases: nn.Module) - Mean pooling that respects the attention mask. Metodi: `forward`.
  - `EmbHead` (bases: nn.Module) - Two-layer projection head with optional L2 normalisation. Metodi: `forward`.
  - `LabelEmbedModel` (bases: nn.Module) - Transformer encoder plus ontology-aware label embeddings. Metodi: `forward`, `save_pretrained`, `from_pretrained`.
- **Funzioni**:
  - `_very_neg_like(t: torch.Tensor)` - Return a tensor filled with a very negative value matching ``t``.
  - `load_label_embed_model(model_dir: str, *, backbone_src: Optional[str] = None, tokenizer = None, config_overrides: Optional[dict] = None, **kwargs)` - Utility to load a model previously exported with :meth:`save_pretrained`.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/models/masked_model.py`
- **Linee**: 459
- **Descrizione**: Hierarchical multi-task classifier with ontology masking and ArcFace support.
- **Dipendenze principali (10)**: `__future__.annotations`, `os`, `safetensors.torch.load_file`, `safetensors.torch.save_file`, `torch`, `torch.nn`, `torch.nn.functional`, `transformers.AutoConfig`, `transformers.AutoModel`, `typing.Optional`
- **Classi**:
  - `MeanPool` (bases: nn.Module) - Nessuna docstring. Metodi: `forward`.
  - `EmbHead` (bases: nn.Module) - Nessuna docstring. Metodi: `forward`.
  - `ArcMarginProduct` (bases: nn.Module) - ArcFace; margin applied only when labels are provided. Metodi: `forward`.
  - `MultiTaskBERTMasked` (bases: nn.Module) - Nessuna docstring. Metodi: `set_super_class_weights`, `set_cat_class_weights`, `forward`, `save_pretrained`, `from_pretrained`.
- **Funzioni**:
  - `_very_neg_like(t: torch.Tensor)` - Nessuna docstring.
  - `load_masked_model(model_dir: str, **kwargs)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/models/price_regressor.py`
- **Linee**: 457
- **Descrizione**: Price regression model for construction products. This model predicts average prices for BIM/construction products based on their descriptions and extracted properties.
- **Dipendenze principali (9)**: `__future__.annotations`, `torch`, `torch.nn`, `transformers.AutoConfig`, `transformers.AutoModel`, `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Tuple`
- **Classi**:
  - `PriceRegressor` (bases: nn.Module) - Regression model for predicting product prices. Uses a transformer backbone to encode product descriptions, optionally conditioning on extracted properties with unit awareness. Metodi: `forward`, `predict_price`.
  - `PricePredictionPipeline` (bases: object) - End-to-end pipeline for price prediction. Metodi: `predict`, `predict_batch`.
- **Funzioni**:
  - `get_unit_id(unit: Optional[str])` - Get unit ID from unit string.
  - `get_price_unit_id(price_unit: Optional[str])` - Get price unit ID from price unit string.
- **Costanti dichiarate (2)**: `PRICE_UNIT_MAP`, `UNIT_MAP`
- **Entry point CLI**: Assente.

### `robimb/models/span_extractor.py`
- **Linee**: 300
- **Descrizione**: Span-based property extraction model. This model learns to find the relevant text span for extracting properties, similar to Question Answering models like BERT for SQuAD.
- **Dipendenze principali (9)**: `__future__.annotations`, `torch`, `torch.nn`, `transformers.AutoConfig`, `transformers.AutoModel`, `typing.Dict`, `typing.List`, `typing.Optional`, `typing.Tuple`
- **Classi**:
  - `PropertySpanExtractor` (bases: nn.Module) - Span extraction model for property values. Given a context (product description) and a property query, predicts start and end positions of the answer span. Metodi: `forward`, `predict_span`.
  - `PropertyExtractorPipeline` (bases: object) - End-to-end pipeline for property extraction. Metodi: `extract`.
- **Funzioni**:
  - `convert_token_span_to_char_span(text: str, token_span: Tuple[int, int], tokenizer, input_ids: torch.Tensor)` - Convert token-level span to character-level span. Args: text: Original text token_span: (start_token_idx, end_token_idx) tokenizer: The tokenizer used input_ids: Token IDs tensor [seq_len] Returns: (start_char, end_char) in original text
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/registry/__init__.py`
- **Linee**: 24
- **Descrizione**: Registry management utilities.
- **Dipendenze principali (15)**: `__future__.annotations`, `loader.RegistryBundle`, `loader.RegistryLoader`, `loader.json_schema_for`, `loader.load_category`, `loader.load_pack`, `loader.load_registry`, `normalizers.PluginRegistry`, `normalizers.get_registered_plugins`, `normalizers.pack_folders_to_monolith`, `normalizers.register_plugins`, `schemas.CategoryDefinition`, ... (+3)
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/registry/loader.py`
- **Linee**: 444
- **Descrizione**: Registry loader capable of resolving the official knowledge pack.
- **Dipendenze principali (17)**: `__future__.annotations`, `config.get_settings`, `dataclasses.dataclass`, `dataclasses.field`, `json`, `normalizers.register_plugins`, `os`, `pathlib`, `schemas.CategoryDefinition`, `schemas.build_category_key`, `schemas.merge_inherited_structures`, `typing.Any`, ... (+5)
- **Classi**:
  - `RegistryBundle` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `RegistryLoader` (bases: object) - High level interface used across the codebase. Metodi: `bundle`, `load_registry`, `load_category`, `json_schema_for`.
- **Funzioni**:
  - `_load_old_style(idx: Dict[str, Any], base: pathlib.Path)` - Nessuna docstring.
  - `_as_dict(payload: Dict[str, Any], key: str)` - Nessuna docstring.
  - `_load_inline(payload: Dict[str, Any])` - Nessuna docstring.
  - `_merge_mapping(base: Mapping[str, Any] | None, override: Mapping[str, Any] | None)` - Nessuna docstring.
  - `_flatten_v4_registry(payload: Mapping[str, Any])` - Nessuna docstring.
  - `_load_optional(base: pathlib.Path, name: str)` - Nessuna docstring.
  - `_load_v4_bundle(base: pathlib.Path, registry_path: pathlib.Path)` - Nessuna docstring.
  - `_maybe_load_v4_from_directory(path: pathlib.Path)` - Nessuna docstring.
  - `_maybe_load_v4_from_file(path: pathlib.Path)` - Nessuna docstring.
  - `load_pack(pack_json_path: str | pathlib.Path)` - Nessuna docstring.
  - `_discover_default_pack()` - Nessuna docstring.
  - `load_registry(source: str | pathlib.Path | None = None)` - Nessuna docstring.
  - `load_category(key: str, *, source: str | pathlib.Path | None = None)` - Nessuna docstring.
  - `json_schema_for(key: str, *, source: str | pathlib.Path | None = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/registry/normalizers.py`
- **Linee**: 110
- **Descrizione**: Utilities dealing with registry-driven normalisers and plugins.
- **Dipendenze principali (12)**: `__future__.annotations`, `importlib`, `json`, `pathlib.Path`, `typing.Any`, `typing.Callable`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Mapping`, `typing.MutableMapping`, `typing.Optional`
- **Classi**:
  - `PluginRegistry` (bases: object) - Keep track of callables declared inside registry payloads. Metodi: `register`, `get`, `as_mapping`.
- **Funzioni**:
  - `_load_plugin(spec: str)` - Nessuna docstring.
  - `register_plugins(kind: str, specs: Iterable[str])` - Nessuna docstring.
  - `get_registered_plugins(kind: str)` - Nessuna docstring.
  - `_read_json_if_exists(path: Path)` - Nessuna docstring.
  - `pack_folders_to_monolith(properties_root: Path, out_registry: Path, out_extractors: Path)` - Re-create the legacy monolith (registry + extractors) from the folder layout.
- **Costanti dichiarate (1)**: `_GLOBAL_REGISTRY`
- **Entry point CLI**: Assente.

### `robimb/registry/schemas.py`
- **Linee**: 260
- **Descrizione**: Pydantic models representing registry categories and property slots.
- **Dipendenze principali (13)**: `__future__.annotations`, `pydantic.BaseModel`, `pydantic.ConfigDict`, `pydantic.Field`, `re`, `typing.Any`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Mapping`, `typing.MutableMapping`, `typing.Optional`, ... (+1)
- **Classi**:
  - `PropertySlot` (bases: BaseModel) - Description of a single property declared inside the registry. Metodi: nessun metodo pubblico.
  - `CategoryDefinition` (bases: BaseModel) - Flattened representation of a category schema. Metodi: `property_ids`, `json_schema`, `from_payload`.
- **Funzioni**:
  - `slugify(value: str)` - Return a deterministic slug suitable for identifiers.
  - `build_category_key(super_name: str, category_name: str)` - Compose the canonical key used to identify a registry category.
  - `build_property_id(super_name: str, category_name: str, slot_name: str, *, inherited: bool = False)` - Return the canonical property identifier used across the pipeline.
  - `merge_inherited_structures(*, base: Mapping[str, Any] | None, override: Mapping[str, Any] | None, super_label: str, category_label: str)` - Create a :class:`CategoryDefinition` merging global and category payloads.
- **Costanti dichiarate (1)**: `_SLUG_RE`
- **Entry point CLI**: Assente.

### `robimb/registry/validators.py`
- **Linee**: 177
- **Descrizione**: Validation helpers migrated from :mod:`robimb.validators.engine`.
- **Dipendenze principali (9)**: `__future__.annotations`, `dataclasses.dataclass`, `re`, `typing.Any`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Mapping`, `typing.Optional`
- **Classi**:
  - `Issue` (bases: object) - Nessuna docstring. Metodi: `as_dict`.
- **Funzioni**:
  - `_to_float(value: Any)` - Nessuna docstring.
  - `_exists(prop: str, props: Mapping[str, Any])` - Nessuna docstring.
  - `_get(prop: str, props: Mapping[str, Any], default: Any = None)` - Nessuna docstring.
  - `_safe_eval(expr: str, env: Dict[str, Any])` - Nessuna docstring.
  - `_match_rule_if(rule: Mapping[str, Any], category_label: str, context: Mapping[str, Any], cat_entry: Optional[Mapping[str, Any]])` - Nessuna docstring.
  - `validate(category_label: str, props: Mapping[str, Any], context: Mapping[str, Any], rules_pack: Mapping[str, Any], *, cat_entry: Optional[Mapping[str, Any]] = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/reporting/__init__.py`
- **Linee**: 11
- **Descrizione**: Visualization utilities for dataset exploration and evaluation reports.
- **Dipendenze principali (3)**: `__future__.annotations`, `dataset_reports.generate_dataset_reports`, `prediction_reports.generate_prediction_reports`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/reporting/dataset_reports.py`
- **Linee**: 124
- **Descrizione**: Generate visual analytics for training and validation datasets.
- **Dipendenze principali (11)**: `__future__.annotations`, `json`, `matplotlib`, `matplotlib.pyplot`, `pandas`, `pathlib.Path`, `seaborn`, `typing.Dict`, `typing.Mapping`, `typing.MutableMapping`, `typing.Optional`
- **Classi**: nessuna.
- **Funzioni**:
  - `_render_bar_plot(counts: MutableMapping[int, int], *, id_to_name: Mapping[int, str], title: str, output_path: Path, top_n: int = DEFAULT_TOP_N)` - Nessuna docstring.
  - `_render_histogram(lengths: pd.Series, title: str, output_path: Path)` - Nessuna docstring.
  - `_compute_basic_stats(df: pd.DataFrame)` - Nessuna docstring.
  - `generate_dataset_reports(train_df: pd.DataFrame, val_df: Optional[pd.DataFrame], *, super_id_to_name: Mapping[int, str], cat_id_to_name: Mapping[int, str], output_dir: Path)` - Create dataset visual reports and summary statistics.
- **Costanti dichiarate (1)**: `DEFAULT_TOP_N`
- **Entry point CLI**: Assente.

### `robimb/reporting/prediction_reports.py`
- **Linee**: 163
- **Descrizione**: Visualization helpers for evaluation and prediction artefacts.
- **Dipendenze principali (13)**: `__future__.annotations`, `collections.Counter`, `json`, `matplotlib`, `matplotlib.pyplot`, `numpy`, `pathlib.Path`, `seaborn`, `sklearn.metrics.classification_report`, `sklearn.metrics.confusion_matrix`, `typing.Dict`, `typing.Iterable`, ... (+1)
- **Classi**: nessuna.
- **Funzioni**:
  - `_top_indices_by_support(support: np.ndarray, limit: int)` - Nessuna docstring.
  - `_plot_confusion(matrix: np.ndarray, labels: Iterable[str], *, title: str, output_path: Path)` - Nessuna docstring.
  - `_normalise_rows(matrix: np.ndarray)` - Nessuna docstring.
  - `_compute_top_confusions(true_ids: np.ndarray, pred_ids: np.ndarray, id_to_name: Mapping[int, str], *, limit: int = 10)` - Nessuna docstring.
  - `generate_prediction_reports(*, pred_super: np.ndarray, pred_cat: np.ndarray, gold_super: np.ndarray, gold_cat: np.ndarray, super_id_to_name: Mapping[int, str], cat_id_to_name: Mapping[int, str], output_dir: Path, prefix: str = 'eval')` - Create evaluation diagnostics and confusion matrix plots.
- **Costanti dichiarate (1)**: `DEFAULT_TOP_N`
- **Entry point CLI**: Assente.

### `robimb/training/__init__.py`
- **Linee**: 11
- **Descrizione**: Training subpackage for robimb.
- **Dipendenze principali (4)**: `hier_trainer.HierTrainingArgs`, `hier_trainer.train_hier_model`, `label_trainer.LabelTrainingArgs`, `label_trainer.train_label_model`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/training/hier_trainer.py`
- **Linee**: 374
- **Descrizione**: Training utilities for the hierarchical masked classifier.
- **Dipendenze principali (31)**: `__future__.annotations`, `argparse`, `dataclasses.dataclass`, `datasets.Dataset`, `json`, `models.masked_model.MultiTaskBERTMasked`, `numpy`, `pandas`, `pathlib.Path`, `shutil`, `torch`, `torch.optim.AdamW`, ... (+19)
- **Classi**:
  - `HierTrainingArgs` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SanitizeGrads` (bases: TrainerCallback) - Nessuna docstring. Metodi: `on_after_backward`.
- **Funzioni**:
  - `set_seed(seed: int)` - Nessuna docstring.
  - `_build_dataset(df: pd.DataFrame, max_length: int, tokenizer, property_meta: Optional[PropertyMetadata])` - Nessuna docstring.
  - `_build_sampler(dataset: Dataset)` - Nessuna docstring.
  - `train_hier_model(args: HierTrainingArgs)` - Nessuna docstring.
  - `build_arg_parser()` - Nessuna docstring.
  - `main(argv: Optional[List[str]] = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/training/label_trainer.py`
- **Linee**: 442
- **Descrizione**: Training utilities for the label embedding classifier.
- **Dipendenze principali (33)**: `__future__.annotations`, `argparse`, `dataclasses.dataclass`, `datasets.Dataset`, `json`, `models.label_model.LabelEmbedModel`, `models.label_model.load_label_embed_model`, `numpy`, `pandas`, `pathlib.Path`, `shutil`, `torch`, ... (+21)
- **Classi**:
  - `LabelTrainingArgs` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `SanitizeGrads` (bases: TrainerCallback) - Nessuna docstring. Metodi: `on_after_backward`.
- **Funzioni**:
  - `set_seed(seed: int)` - Nessuna docstring.
  - `_load_label_texts(path: Optional[str], fallback: Iterable[str])` - Nessuna docstring.
  - `_build_dataset(df: pd.DataFrame, max_length: int, tokenizer, property_meta: Optional[PropertyMetadata])` - Nessuna docstring.
  - `_param_groups(model: LabelEmbedModel, lr_head: float, lr_encoder: float, weight_decay: float)` - Nessuna docstring.
  - `_build_sampler(dataset: Dataset)` - Nessuna docstring.
  - `train_label_model(args: LabelTrainingArgs)` - Nessuna docstring.
  - `build_arg_parser()` - Nessuna docstring.
  - `main(argv: Optional[List[str]] = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/training/price_trainer.py`
- **Linee**: 698
- **Descrizione**: Training utilities for the price regression model.
- **Dipendenze principali (25)**: `__future__.annotations`, `argparse`, `dataclasses.dataclass`, `dotenv.load_dotenv`, `json`, `models.price_regressor.PRICE_UNIT_MAP`, `models.price_regressor.PriceRegressor`, `models.price_regressor.UNIT_MAP`, `models.price_regressor.get_price_unit_id`, `models.price_regressor.get_unit_id`, `numpy`, `os`, ... (+13)
- **Classi**:
  - `PriceTrainingArgs` (bases: object) - Arguments for price regressor training. Metodi: nessun metodo pubblico.
  - `PriceDataset` (bases: Dataset) - Dataset for price regression. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `_convert_to_serializable(obj)` - Convert numpy types to Python native types for JSON serialization.
  - `train_epoch(model: PriceRegressor, dataloader: DataLoader, optimizer: torch.optim.Optimizer, scheduler, device: str, use_properties: bool)` - Train for one epoch.
  - `evaluate(model: PriceRegressor, dataloader: DataLoader, device: str, use_properties: bool)` - Evaluate model.
  - `train_price_model(args: PriceTrainingArgs)` - Train the price regressor model.
  - `build_arg_parser()` - Build argument parser for price regressor training.
  - `main(argv = None)` - Main entry point for price regressor training.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/training/property_utils.py`
- **Linee**: 170
- **Descrizione**: Utility helpers to deal with property prediction targets.
- **Dipendenze principali (12)**: `__future__.annotations`, `dataclasses.dataclass`, `numpy`, `pandas`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Mapping`, `typing.MutableMapping`, `typing.Optional`, `typing.Sequence`, `typing.Tuple`
- **Classi**:
  - `PropertyMetadata` (bases: object) - Aggregated information about property slots present in the dataset. Metodi: `num_slots`, `has_properties`.
- **Funzioni**:
  - `_normalise_schema_type(raw: Optional[Mapping[str, object]])` - Nessuna docstring.
  - `build_property_metadata(dataframes: Iterable[pd.DataFrame], num_cat: int)` - Collect slot metadata from the provided dataframes.
  - `_clean_value(value: object)` - Nessuna docstring.
  - `build_property_targets(batch_properties: Sequence[MutableMapping[str, object] | Mapping[str, object] | None], batch_cat_labels: Sequence[int], metadata: PropertyMetadata)` - Create masks and targets for property prediction.
- **Costanti dichiarate (2)**: `NUMERIC_TYPES`, `SUPPORTED_SCHEMA_TYPES`
- **Entry point CLI**: Assente.

### `robimb/training/span_trainer.py`
- **Linee**: 469
- **Descrizione**: Training utilities for the span-based property extractor.
- **Dipendenze principali (17)**: `__future__.annotations`, `argparse`, `dataclasses.dataclass`, `dotenv.load_dotenv`, `json`, `models.span_extractor.PropertySpanExtractor`, `os`, `pathlib.Path`, `torch`, `torch.utils.data.DataLoader`, `torch.utils.data.Dataset`, `torch.utils.data.random_split`, ... (+5)
- **Classi**:
  - `SpanTrainingArgs` (bases: object) - Arguments for span extractor training. Metodi: nessun metodo pubblico.
  - `PropertyQADataset` (bases: Dataset) - Dataset for property extraction QA pairs. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `train_epoch(model: PropertySpanExtractor, dataloader: DataLoader, optimizer: torch.optim.Optimizer, scheduler, device: str)` - Train for one epoch.
  - `evaluate(model: PropertySpanExtractor, dataloader: DataLoader, device: str)` - Evaluate model.
  - `train_span_model(args: SpanTrainingArgs)` - Train the span extractor model.
  - `build_arg_parser()` - Build argument parser for span extractor training.
  - `main(argv = None)` - Main entry point for span extractor training.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/training/tapt_mlm.py`
- **Linee**: 378
- **Descrizione**: TAPT/MLM su corpus edilizio con XLM-R (o altro) – GPU-first. Feature: - Whole-Word Masking (--wwm) opzionale, altrimenti MLM standard. - LLRD (--llrd) opzionale con AdamW e LR decrescente verso i layer bassi. - Freeze/Unfreeze: congela i primi N layer e sblocca a epoca K. - Early stopping + best model: stop se...
- **Dipendenze principali (19)**: `argparse`, `datasets.Dataset`, `datasets.load_dataset`, `math`, `numpy`, `os`, `pathlib.Path`, `random`, `torch`, `torch.optim.AdamW`, `transformers.AutoModelForMaskedLM`, `transformers.AutoTokenizer`, ... (+7)
- **Classi**:
  - `UnfreezeCallback` (bases: EarlyStoppingCallback) - EarlyStopping + sblocco layer a una certa epoca. Metodi: `on_epoch_begin`.
- **Funzioni**:
  - `set_seed(seed: int)` - Nessuna docstring.
  - `assert_cuda_ready(force_cpu: bool = False)` - Nessuna docstring.
  - `load_text_files(paths: List[str], min_len: int = 5, dedup: bool = True)` - Nessuna docstring.
  - `prepare_mlm_blocks(ds: Dataset, tokenizer: AutoTokenizer, block_size: int)` - Nessuna docstring.
  - `freeze_bottom_n(model, n: int)` - Nessuna docstring.
  - `make_llrd_param_groups(model, base_lr = 1e-05, decay = 0.9, wd = 0.01)` - Layer-Wise LR Decay per XLM-R: - dedup per id(param) per evitare "param in più gruppi" - no_decay per bias/LayerNorm - salta lm_head.decoder.weight se è tied con embeddings
  - `main(argv: Optional[List[str]] = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `robimb/utils/__init__.py`
- **Linee**: 38
- **Descrizione**: Shared utilities for ontology management, data preparation and metrics.
- **Dipendenze principali (15)**: `dataset_prep.LabelMaps`, `dataset_prep.build_mask_and_report`, `dataset_prep.create_or_load_label_maps`, `dataset_prep.prepare_classification_dataset`, `dataset_prep.prepare_mlm_corpus`, `dataset_prep.save_datasets`, `io_utils.ensure_has_weights`, `metrics_utils.make_compute_metrics`, `ontology_utils.Ontology`, `ontology_utils.build_mask_from_ontology`, `ontology_utils.load_label_maps`, `ontology_utils.load_ontology`, ... (+3)
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/data_utils.py`
- **Linee**: 40
- **Descrizione**: Backward compatibility layer for legacy imports. This module preserves the previous public API of ``utils.data_utils`` by re-exporting the new specialised helpers introduced in ``dataset_prep``, ``registry_io`` and ``sampling``.
- **Dipendenze principali (14)**: `__future__.annotations`, `dataset_prep.LabelMaps`, `dataset_prep.build_mask_and_report`, `dataset_prep.create_or_load_label_maps`, `dataset_prep.prepare_classification_dataset`, `dataset_prep.prepare_mlm_corpus`, `dataset_prep.save_datasets`, `registry_io.ExtractorsPack`, `registry_io.build_registry_extractors`, `registry_io.load_extractors_pack`, `registry_io.load_property_registry`, `registry_io.merge_extractors_pack`, ... (+2)
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/dataset_prep.py`
- **Linee**: 469
- **Descrizione**: Dataset preparation helpers for the BIM NLP pipeline.
- **Dipendenze principali (25)**: `__future__.annotations`, `dataclasses.dataclass`, `extraction.legacy.extract_properties`, `json`, `numpy`, `ontology_utils.build_mask_from_ontology`, `ontology_utils.load_label_maps`, `ontology_utils.load_ontology`, `pandas`, `pathlib.Path`, `registry.schemas.CategoryDefinition`, `registry.schemas.build_category_key`, ... (+13)
- **Classi**:
  - `LabelMaps` (bases: object) - Typed wrapper around the four label map dictionaries used by training. Metodi: `as_tuple`.
- **Funzioni**:
  - `create_or_load_label_maps(label_maps_path: str | Path, *, ontology_path: Optional[str | Path] = None)` - Nessuna docstring.
  - `build_mask_and_report(ontology_path: Optional[str | Path], label_maps: LabelMaps)` - Nessuna docstring.
  - `_infer_category(property_registry: Optional[Mapping[str, CategoryDefinition]], super_name: str, cat_name: str)` - Nessuna docstring.
  - `_build_target_tags(super_name: str, cat_name: str)` - Nessuna docstring.
  - `prepare_classification_dataset(train_path: str | Path, val_path: Optional[str | Path], *, label_maps_path: str | Path, ontology_path: Optional[str | Path] = None, done_uids_path: Optional[str | Path] = None, val_split: float = 0.2, random_state: int = 42, properties_registry_path: Optional[str | Path] = None, extractors_pack_path: Optional[str | Path] = None, text_field: str = 'text')` - Nessuna docstring.
  - `prepare_dataset_simple(train_path: str | Path, val_path: Optional[str | Path], *, label_maps_path: str | Path, ontology_path: Optional[str | Path] = None, done_uids_path: Optional[str | Path] = None, val_split: float = 0.2, random_state: int = 42, text_field: str = 'text')` - Prepare dataset without property extraction - just normalize labels and split. This is a simplified version that: - Loads data from JSONL/CSV/Excel/TXT - Maps category labels to IDs - Splits into train/val - Does NOT extract properties
  - `save_datasets(train_df: pd.DataFrame, val_df: pd.DataFrame, out_dir: str | Path)` - Nessuna docstring.
  - `prepare_mlm_corpus(jsonl_files: Iterable[str | Path], out_txt_path: str | Path, *, text_field: str = 'text', min_len: int = 5, dedup: bool = True)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/io_utils.py`
- **Linee**: 18
- **Descrizione**: File-system helpers used across the CLI commands.
- **Dipendenze principali (3)**: `__future__.annotations`, `os`, `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**:
  - `ensure_has_weights(model_dir: str | os.PathLike[str])` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/logging.py`
- **Linee**: 113
- **Descrizione**: Structured logging utilities emitting JSON Lines payloads.
- **Dipendenze principali (10)**: `__future__.annotations`, `datetime.datetime`, `datetime.timezone`, `json`, `logging`, `pathlib.Path`, `typing.Any`, `typing.Mapping`, `typing.MutableMapping`, `uuid.uuid4`
- **Classi**:
  - `JsonLogFormatter` (bases: logging.Formatter) - Format log records as single-line JSON payloads. Metodi: `format`.
- **Funzioni**:
  - `configure_json_logger(log_path: Path | None, level: int = logging.INFO)` - Configure the project logger with a JSONL handler.
  - `flush_handlers(logger: logging.Logger)` - Ensure all handlers flush their buffers.
  - `generate_trace_id()` - Return a unique trace identifier suitable for correlating log events.
  - `log_event(logger: logging.Logger, event: str, *, trace_id: str | None = None, level: int = logging.INFO, message: str | None = None, **fields: Any)` - Emit a structured event on the provided ``logger``.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/metrics_utils.py`
- **Linee**: 140
- **Descrizione**: Metric helpers shared across trainers and the CLI.
- **Dipendenze principali (5)**: `__future__.annotations`, `numpy`, `sklearn.metrics.accuracy_score`, `sklearn.metrics.f1_score`, `typing.Dict`
- **Classi**: nessuna.
- **Funzioni**:
  - `_to_numpy(value)` - Nessuna docstring.
  - `make_compute_metrics(num_super: int, num_cat: int, property_meta = None)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/ontology_utils.py`
- **Linee**: 186
- **Descrizione**: Utilities for working with ontology and label mappings.
- **Dipendenze principali (12)**: `__future__.annotations`, `dataclasses.dataclass`, `json`, `numpy`, `pathlib.Path`, `typing.Dict`, `typing.Iterable`, `typing.List`, `typing.Mapping`, `typing.MutableMapping`, `typing.Optional`, `typing.Tuple`
- **Classi**:
  - `Ontology` (bases: object) - Nessuna docstring. Metodi: `from_mapping`, `super_labels`, `cat_labels`.
- **Funzioni**:
  - `load_ontology(path: str | Path)` - Nessuna docstring.
  - `_invert(mapping: Mapping[str, int])` - Nessuna docstring.
  - `_normalise_name(text: str)` - Nessuna docstring.
  - `_ensure_fallback_label(mapping: Mapping[str, int])` - Return a copy of *mapping* that contains the fallback label at index 0.
  - `load_label_maps(path: str | Path, *, ontology: Optional[Ontology] = None, create_if_missing: bool = False)` - Nessuna docstring.
  - `save_label_maps(path: str | Path, *, super_name_to_id: Mapping[str, int], cat_name_to_id: Mapping[str, int], super_id_to_name: Mapping[int, str], cat_id_to_name: Mapping[int, str])` - Nessuna docstring.
  - `build_mask_from_ontology(ontology_path: str | Path, super_name_to_id: Mapping[str, int], cat_name_to_id: Mapping[str, int])` - Nessuna docstring.
- **Costanti dichiarate (1)**: `FALLBACK_LABEL`
- **Entry point CLI**: Assente.

### `robimb/utils/packing_utils.py`
- **Linee**: 35
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 7 funzioni.
- **Dipendenze principali (3)**: `json`, `pathlib.Path`, `re`
- **Classi**: nessuna.
- **Funzioni**:
  - `slugify_label(label: str)` - Nessuna docstring.
  - `ensure_parent(p: Path)` - Nessuna docstring.
  - `read_json(path: Path)` - Nessuna docstring.
  - `write_json(path: Path, obj)` - Nessuna docstring.
  - `split_property_id(full_property_id: str)` - Nessuna docstring.
  - `trim_property_id_for_global(prop_id: str)` - Nessuna docstring.
  - `trim_property_id_for_category(prop_id: str)` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/registry_io.py`
- **Linee**: 377
- **Descrizione**: Utilities for loading registry definitions and extractor packs.
- **Dipendenze principali (15)**: `__future__.annotations`, `dataclasses.dataclass`, `dataclasses.field`, `json`, `pathlib.Path`, `registry.RegistryLoader`, `registry.load_pack`, `registry.schemas.CategoryDefinition`, `registry.schemas.PropertySlot`, `typing.Any`, `typing.Dict`, `typing.Iterable`, ... (+3)
- **Classi**:
  - `ExtractorsPack` (bases: object) - Typed representation of an extractors configuration. Metodi: `to_mapping`, `from_payload`, `merge`.
- **Funzioni**:
  - `_resolve_pack_json(path: Path)` - Nessuna docstring.
  - `_load_json(path: Path)` - Nessuna docstring.
  - `load_property_registry(path: Path)` - Load a property registry returning :class:`CategoryDefinition` objects.
  - `_load_flat_registry(path: Path)` - Build a registry from the simplified schema-first resources.
  - `_load_flat_patterns(base_dir: Path)` - Load regex patterns from the schema-first extractors pack.
  - `_normalize_extractors_payload(payload: Any)` - Nessuna docstring.
  - `build_registry_extractors(registry: Mapping[str, CategoryDefinition])` - Nessuna docstring.
  - `_infer_slot_normalizers(slot: Mapping[str, Any])` - Nessuna docstring.
  - `load_extractors_pack(path: Path)` - Load an extractors pack from raw JSON or a knowledge pack.
  - `merge_extractors_pack(primary: Optional[ExtractorsPack], secondary: Optional[ExtractorsPack])` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `robimb/utils/sampling.py`
- **Linee**: 67
- **Descrizione**: Sampling utilities for dataset inspection and fixtures.
- **Dipendenze principali (8)**: `__future__.annotations`, `collections.OrderedDict`, `json`, `pandas`, `pathlib.Path`, `typing.Any`, `typing.Dict`, `typing.List`
- **Classi**: nessuna.
- **Funzioni**:
  - `load_jsonl_to_df(path: str | Path)` - Nessuna docstring.
  - `sample_one_record_per_category(path: str | Path, *, category_field: str = 'cat')` - Return the first occurrence for each category found in ``path``.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

## run.py (1 script)

### `run.py`
- **Linee**: 19
- **Descrizione**: Script per avviare il backend FastAPI
- **Dipendenze principali (1)**: `uvicorn`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

## scripts (8 script)

### `scripts/backfill_wbs6.py`
- **Linee**: 313
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 9 funzioni.
- **Dipendenze principali (20)**: `__future__.annotations`, `app.db.engine`, `app.db.models.Commessa`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.VoceComputo`, `app.db.models_wbs.Impresa`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceOfferta`, `app.db.models_wbs.VoceProgetto`, `app.db.models_wbs.Wbs6`, `app.db.models_wbs.Wbs7`, ... (+8)
- **Classi**: nessuna.
- **Funzioni**:
  - `normalize_wbs6(code: Optional[str], fallback: Optional[str])` - Nessuna docstring.
  - `normalize_wbs7(code: Optional[str], fallback: Optional[str])` - Nessuna docstring.
  - `get_or_create_spatial_node(session: Session, cache: Dict[Tuple[int, int, str], WbsSpaziale], commessa_id: int, level: int, code: str, description: Optional[str], parent: Optional[WbsSpaziale])` - Nessuna docstring.
  - `get_or_create_wbs6(session: Session, cache: Dict[Tuple[int, str], Wbs6], commessa_id: int, code: str, description: Optional[str], spatial_leaf: Optional[WbsSpaziale])` - Nessuna docstring.
  - `get_or_create_wbs7(session: Session, cache: Dict[Tuple[int, Optional[str]], Wbs7], commessa_id: int, wbs6_id: int, code: Optional[str], description: Optional[str])` - Nessuna docstring.
  - `get_or_create_impresa(session: Session, cache: Dict[str, Impresa], label: Optional[str])` - Nessuna docstring.
  - `build_spatial_nodes(session: Session, commessa: Commessa)` - Nessuna docstring.
  - `backfill_commessa(session: Session, commessa: Commessa)` - Nessuna docstring.
  - `main()` - Nessuna docstring.
- **Costanti dichiarate (2)**: `WBS6_RE`, `WBS7_RE`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `scripts/build_faiss_index.py`
- **Linee**: 45
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 1 funzioni.
- **Dipendenze principali (5)**: `__future__.annotations`, `app.services.nlp.DocumentFaissPipeline`, `faiss`, `pathlib.Path`, `sys`
- **Classi**: nessuna.
- **Funzioni**:
  - `main()` - Nessuna docstring.
- **Costanti dichiarate (2)**: `BACKEND_ROOT`, `CURRENT_DIR`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `scripts/generate_backend_docs.py`
- **Linee**: 320
- **Descrizione**: Genera la documentazione per ogni script Python presente nella cartella backend. Il risultato viene scritto in backend/docs/SCRIPT_REFERENCE.md con sezioni ordinate per sottocartella. Eseguire questo script dopo aver aggiunto o modificato file .py per mantenere il catalogo aggiornato.
- **Dipendenze principali (11)**: `__future__.annotations`, `ast`, `ast.unparse`, `collections.defaultdict`, `dataclasses.dataclass`, `dataclasses.field`, `pathlib.Path`, `textwrap`, `typing.Iterable`, `typing.List`, `typing.Sequence`
- **Classi**:
  - `ClassInfo` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `FunctionInfo` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
  - `ModuleInfo` (bases: object) - Nessuna docstring. Metodi: nessun metodo pubblico.
- **Funzioni**:
  - `main()` - Nessuna docstring.
  - `analyze_module(path: Path, rel_path: str, category: str)` - Nessuna docstring.
  - `extract_imports(tree: ast.AST)` - Nessuna docstring.
  - `extract_classes(tree: ast.Module)` - Nessuna docstring.
  - `extract_functions(tree: ast.Module)` - Nessuna docstring.
  - `extract_constants(tree: ast.Module)` - Nessuna docstring.
  - `detect_cli_entry(tree: ast.AST)` - Nessuna docstring.
  - `render_module(module: ModuleInfo)` - Nessuna docstring.
  - `render_classes_section(classes: Sequence[ClassInfo])` - Nessuna docstring.
  - `render_functions_section(functions: Sequence[FunctionInfo])` - Nessuna docstring.
  - `render_signature(node: ast.FunctionDef | ast.AsyncFunctionDef)` - Nessuna docstring.
  - `format_argument(arg: ast.arg, default: str | None = None, prefix: str = '')` - Nessuna docstring.
  - `sanitize_docstring(value: str | None, fallback: str)` - Nessuna docstring.
  - `format_list(values: Iterable[str], limit: int = 10)` - Nessuna docstring.
  - `count_defs(tree: ast.Module, types: type | tuple[type, ...])` - Nessuna docstring.
- **Costanti dichiarate (3)**: `BACKEND_ROOT`, `DOC_DIR`, `DOC_PATH`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `scripts/import_test.py`
- **Linee**: 67
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 1 funzioni.
- **Dipendenze principali (12)**: `app.db.engine`, `app.db.init_db`, `app.db.models.VoceComputo`, `app.schemas.CommessaCreate`, `app.services.AnalysisService`, `app.services.CommesseService`, `app.services.import_service`, `pathlib.Path`, `sqlalchemy.func`, `sqlmodel.Session`, `sqlmodel.select`, `sys`
- **Classi**: nessuna.
- **Funzioni**:
  - `main()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `scripts/migrate_imports.py`
- **Linee**: 88
- **Descrizione**: Script to automatically migrate imports from old structure to new structure.
- **Dipendenze principali (3)**: `pathlib.Path`, `re`, `sys`
- **Classi**: nessuna.
- **Funzioni**:
  - `migrate_file(file_path: Path)` - Migrate imports in a single file.
  - `main()` - Main migration function.
- **Costanti dichiarate (1)**: `IMPORT_MAPPINGS`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `scripts/regenerate_embeddings.py`
- **Linee**: 106
- **Descrizione**: Script per rigenerare gli embedding semantici per tutte le voci del price catalog.
- **Dipendenze principali (9)**: `__future__.annotations`, `app.db.models.PriceListItem`, `app.db.models.Settings`, `app.db.session.engine`, `app.services.nlp.semantic_embedding_service`, `logging`, `sqlalchemy.orm.attributes.flag_modified`, `sqlmodel.Session`, `sqlmodel.select`
- **Classi**: nessuna.
- **Funzioni**:
  - `regenerate_embeddings()` - Rigenera gli embedding per tutte le voci del price catalog.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `scripts/replace_parser_logic.py`
- **Linee**: 133
- **Descrizione**: Script per sostituire la logica del parser con testa-coda
- **Dipendenze principali (1)**: `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (1)**: `NEW_CODE`
- **Entry point CLI**: Assente.

### `scripts/semantic_search.py`
- **Linee**: 52
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 2 funzioni.
- **Dipendenze principali (5)**: `__future__.annotations`, `app.services.nlp.DocumentFaissPipeline`, `faiss`, `pathlib.Path`, `sys`
- **Classi**: nessuna.
- **Funzioni**:
  - `semantic_search(query: str, k: int = 10)` - Nessuna docstring.
  - `main()` - Nessuna docstring.
- **Costanti dichiarate (2)**: `BACKEND_ROOT`, `CURRENT_DIR`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

## tests (23 script)

### `tests/__init__.py`
- **Linee**: 1
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/__init__.py`
- **Linee**: 0
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/lc/__init__.py`
- **Linee**: 0
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/__init__.py`
- **Linee**: 0
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/debug/__init__.py`
- **Linee**: 0
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/debug/test_headtail_simple.py`
- **Linee**: 45
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (2)**: `pandas`, `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/debug/test_headtail_with_cleaning.py`
- **Linee**: 83
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (2)**: `pandas`, `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_last_progressivo.py`
- **Linee**: 129
- **Descrizione**: Analisi dell'ultimo progressivo del file
- **Dipendenze principali (2)**: `pandas`, `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_mc_import_flow.py`
- **Linee**: 138
- **Descrizione**: Test per verificare import MC completo
- **Dipendenze principali (12)**: `app.db.engine_from_env`, `app.db.get_session`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.VoceComputo`, `app.excel.parse_computo_excel`, `collections.defaultdict`, `pathlib.Path`, `sqlmodel.Session`, `sqlmodel.create_engine`, `sqlmodel.select`, `sys`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_mc_parser_fix.py`
- **Linee**: 72
- **Descrizione**: Test per verificare che il parser MC con head-tail funzioni
- **Dipendenze principali (3)**: `app.services.importers.parse_mc_return_excel`, `pathlib.Path`, `sys`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_progressivo_2250_discrepancy.py`
- **Linee**: 152
- **Descrizione**: Riproduce la discrepanza di quantità/prezzo per 1C.00.700.0030.b nel flusso MC.
- **Dipendenze principali (16)**: `app.db.engine`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.VoceComputo`, `app.services.importers.matching._align_return_rows`, `app.services.importers.matching._build_description_price_map`, `app.services.importers.matching._has_progressivi`, `app.services.importers.matching.legacy._align_progressive_return`, `app.services.importers.matching.legacy._build_return_index`, `app.services.importers.matching.legacy._wbs_base_key_from_parsed`, `app.services.importers.matching.legacy._wbs_key_from_model`, `app.services.importers.parse_mc_return_excel`, ... (+4)
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (2)**: `FILE_PATH`, `TARGET_PROGRESSIVI`
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_progressivo_2640.py`
- **Linee**: 117
- **Descrizione**: Analisi del progressivo 2640 che ha discrepanza enorme
- **Dipendenze principali (2)**: `pandas`, `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_progressivo_6580.py`
- **Linee**: 98
- **Descrizione**: Analisi progressivo 6580 (L037.040.05)
- **Dipendenze principali (2)**: `pandas`, `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_specific_progressivo.py`
- **Linee**: 106
- **Descrizione**: Test per analizzare progressivo specifico con prezzo mancante
- **Dipendenze principali (2)**: `pandas`, `pathlib.Path`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/importers/mc/test_total_discrepancy.py`
- **Linee**: 164
- **Descrizione**: Script per analizzare la discrepanza nel totale
- **Dipendenze principali (10)**: `app.db.engine`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.VoceComputo`, `app.services.importers.parse_mc_return_excel`, `decimal.Decimal`, `pathlib.Path`, `sqlmodel.Session`, `sqlmodel.select`, `sys`
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/unit/__init__.py`
- **Linee**: 0
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 0 funzioni.
- **Dipendenze principali (0)**: Nessuna
- **Classi**: nessuna.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/unit/test_commesse_storage_cleanup.py`
- **Linee**: 86
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (14)**: `__future__.annotations`, `app.db.models.Commessa`, `app.db.models.CommessaStato`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.services.commesse.CommesseService`, `app.services.storage.storage_service`, `pathlib.Path`, `sqlalchemy.pool.StaticPool`, `sqlmodel.SQLModel`, `sqlmodel.Session`, `sqlmodel.create_engine`, ... (+2)
- **Classi**:
  - `CommesseStorageCleanupTestCase` (bases: unittest.TestCase) - Nessuna docstring. Metodi: `setUp`, `tearDown`, `test_delete_computo_removes_uploaded_file`, `test_delete_commessa_clears_entire_commessa_folder`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `tests/unit/test_description_matching.py`
- **Linee**: 48
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 3 funzioni.
- **Dipendenze principali (3)**: `app.excel.parser.ParsedVoce`, `app.services.importers.matching.legacy._match_by_description_similarity`, `types.SimpleNamespace`
- **Classi**: nessuna.
- **Funzioni**:
  - `_parsed_voce(description: str)` - Nessuna docstring.
  - `test_match_by_description_similarity_selects_closest_candidate()` - Nessuna docstring.
  - `test_match_by_description_similarity_rejects_low_ratio()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/unit/test_importer_custom_excel.py`
- **Linee**: 42
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 1 funzioni.
- **Dipendenze principali (5)**: `__future__.annotations`, `app.services.importers.parser._parse_custom_return_excel`, `openpyxl.Workbook`, `pathlib.Path`, `tempfile.NamedTemporaryFile`
- **Classi**: nessuna.
- **Funzioni**:
  - `test_parse_custom_return_excel_builds_parsed_voci()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/unit/test_importer_progress_checks.py`
- **Linee**: 39
- **Descrizione**: Modulo senza docstring. Contiene 0 classi e 6 funzioni.
- **Dipendenze principali (5)**: `app.services.importers.matching.legacy._has_progressivi`, `app.services.importers.matching.legacy._prices_match`, `app.services.importers.matching.legacy._progress_price_key`, `app.services.importers.matching.legacy._quantities_match`, `types.SimpleNamespace`
- **Classi**: nessuna.
- **Funzioni**:
  - `test_quantities_match_within_tolerance()` - Nessuna docstring.
  - `test_prices_match_handles_small_deltas()` - Nessuna docstring.
  - `test_progress_price_key_normalizes_code()` - Nessuna docstring.
  - `test_progress_price_key_requires_progressivo()` - Nessuna docstring.
  - `test_has_progressivi_detects_entries()` - Nessuna docstring.
  - `test_has_progressivi_returns_false_when_absent()` - Nessuna docstring.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/unit/test_importer_zero_guard.py`
- **Linee**: 69
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (4)**: `__future__.annotations`, `app.excel.parser.ParsedVoce`, `app.services.importers.matching.legacy._detect_forced_zero_violations`, `unittest`
- **Classi**:
  - `ZeroGuardDetectionTestCase` (bases: unittest.TestCase) - Nessuna docstring. Metodi: `test_detects_assistenze_quantity_mismatch`, `test_detects_mark_up_price`, `test_ignores_unrelated_voce`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (0)**: Nessuna
- **Entry point CLI**: Assente.

### `tests/unit/test_six_import_service.py`
- **Linee**: 583
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 0 funzioni.
- **Dipendenze principali (23)**: `__future__.annotations`, `app.db.models.Commessa`, `app.db.models.CommessaStato`, `app.db.models.Computo`, `app.db.models.ComputoTipo`, `app.db.models.PriceListItem`, `app.db.models.VoceComputo`, `app.db.models_wbs.Voce`, `app.db.models_wbs.VoceProgetto`, `app.db.models_wbs.Wbs6`, `app.db.models_wbs.WbsSpaziale`, `app.services.six_import_service.PreventivoSelectionError`, ... (+11)
- **Classi**:
  - `SixImportServiceTestCase` (bases: unittest.TestCase) - Nessuna docstring. Metodi: `setUp`, `tearDown`, `test_inspect_details_returns_structure`, `test_imports_plain_xml_file`, `test_preserves_spatial_wbs_quantities`, `test_imports_from_six_archive`, `test_collapses_duplicate_price_lists`, `test_deduplicates_identical_price_catalog_entries`, `test_requires_preventivo_selection_when_multiple`, `test_inspect_content_lists_preventivi`, `test_infers_quantity_from_reference_notes`, `test_preserves_zero_quantity_voci`.
- **Funzioni**: nessuna.
- **Costanti dichiarate (8)**: `BACKEND_ROOT`, `SAMPLE_XML`, `SAMPLE_XML_DUPLICATE_PRICE_LISTS`, `SAMPLE_XML_MULTI`, `SAMPLE_XML_PRICE_DUPLICATES`, `SAMPLE_XML_REFERENCES`, `SAMPLE_XML_SPATIAL_SPLIT`, `SAMPLE_XML_ZERO`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

### `tests/unit/test_wbs_import.py`
- **Linee**: 126
- **Descrizione**: Modulo senza docstring. Contiene 1 classi e 1 funzioni.
- **Dipendenze principali (18)**: `__future__.annotations`, `app.db.models.Commessa`, `app.db.models.CommessaStato`, `app.db.models_wbs.Wbs6`, `app.db.models_wbs.Wbs7`, `app.db.models_wbs.WbsSpaziale`, `app.services.wbs_import.WbsImportService`, `io.BytesIO`, `openpyxl.Workbook`, `pathlib.Path`, `sqlalchemy.pool.StaticPool`, `sqlmodel.SQLModel`, ... (+6)
- **Classi**:
  - `WbsImportServiceTestCase` (bases: unittest.TestCase) - Nessuna docstring. Metodi: `setUp`, `test_import_creates_wbs_nodes`, `test_update_mode_is_idempotent`.
- **Funzioni**:
  - `_build_sample_workbook()` - Nessuna docstring.
- **Costanti dichiarate (1)**: `BACKEND_ROOT`
- **Entry point CLI**: Presente (`if __name__ == "__main__"`).

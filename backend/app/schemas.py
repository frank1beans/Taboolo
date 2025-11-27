from datetime import datetime
from typing import Any, Optional
import string

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.db.models import CommessaStato, ComputoTipo, SettingsRead, UserRole

PASSWORD_MAX_LENGTH_BYTES = 72


class VoceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    progressivo: Optional[int] = None
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo: Optional[float] = None
    note: Optional[str] = None
    ordine: int
    wbs_1_code: Optional[str] = None
    wbs_1_description: Optional[str] = None
    wbs_2_code: Optional[str] = None
    wbs_2_description: Optional[str] = None
    wbs_3_code: Optional[str] = None
    wbs_3_description: Optional[str] = None
    wbs_4_code: Optional[str] = None
    wbs_4_description: Optional[str] = None
    wbs_5_code: Optional[str] = None
    wbs_5_description: Optional[str] = None
    wbs_6_code: Optional[str] = None
    wbs_6_description: Optional[str] = None
    wbs_7_code: Optional[str] = None
    wbs_7_description: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.viewer
    is_active: bool = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.viewer

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        errors: list[str] = []
        if len(value) < 16:
            errors.append("almeno 16 caratteri")
        if len(value.encode("utf-8")) > PASSWORD_MAX_LENGTH_BYTES:
            errors.append("non piu di 72 byte")
        if not any(ch.isalpha() for ch in value):
            errors.append("almeno una lettera")
        if not any(ch.isupper() for ch in value):
            errors.append("almeno una lettera maiuscola")
        if not any(ch.isdigit() for ch in value):
            errors.append("almeno un numero")
        if not any(ch in string.punctuation for ch in value):
            errors.append("almeno un carattere speciale")

        if errors:
            raise ValueError(
                "La password non rispetta i requisiti: " + ", ".join(errors)
            )
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class UserProfileBase(BaseModel):
    company: Optional[str] = None
    language: Optional[str] = "it-IT"
    settings: Optional[dict[str, Any]] = None


class UserProfileRead(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class ProfileUpdate(UserProfileBase):
    pass


class ComputoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: ComputoTipo
    impresa: Optional[str] = None
    round_number: Optional[int] = None
    importo_totale: Optional[float] = None
    delta_vs_progetto: Optional[float] = None
    percentuale_delta: Optional[float] = None
    note: Optional[str] = None
    file_nome: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    matching_report: Optional[dict[str, Any]] = None


class CommessaCreate(BaseModel):
    nome: str
    codice: str
    descrizione: Optional[str] = None
    note: Optional[str] = None
    business_unit: Optional[str] = None
    revisione: Optional[str] = None
    stato: CommessaStato = CommessaStato.setup


class CommessaSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    codice: str
    descrizione: Optional[str] = None
    note: Optional[str] = None
    business_unit: Optional[str] = None
    revisione: Optional[str] = None
    stato: CommessaStato
    created_at: datetime
    updated_at: datetime


class CommessaDetailSchema(CommessaSchema):
    computi: list[ComputoSchema] = []


class PriceListItemSchema(BaseModel):
    id: int
    commessa_id: int
    commessa_nome: str
    commessa_codice: str
    business_unit: Optional[str] = None
    product_id: str
    item_code: str
    item_description: Optional[str] = None
    unit_id: Optional[str] = None
    unit_label: Optional[str] = None
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    wbs7_code: Optional[str] = None
    wbs7_description: Optional[str] = None
    price_lists: Optional[dict[str, float]] = None
    extra_metadata: Optional[dict[str, Any]] = None
    source_file: Optional[str] = None
    preventivo_id: Optional[str] = None
    project_price: Optional[float] = None
    project_quantity: Optional[float] = None
    offer_prices: Optional[dict[str, dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime
    offers: list["PriceListOfferSchema"] = []


class PriceListOfferSchema(BaseModel):
    id: int
    price_list_item_id: int
    computo_id: int
    impresa_id: Optional[int] = None
    impresa_label: Optional[str] = None
    round_number: Optional[int] = None
    prezzo_unitario: float
    quantita: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class ManualPriceUpdateRequest(BaseModel):
    price_list_item_id: int
    computo_id: int
    prezzo_unitario: float
    quantita: Optional[float] = None


class ManualPriceUpdateResponse(BaseModel):
    offer: PriceListOfferSchema
    computo: ComputoSchema


class PriceListItemSearchResultSchema(PriceListItemSchema):
    score: float
    match_reason: Optional[str] = None


class PriceCatalogCommessaSummarySchema(BaseModel):
    commessa_id: int
    commessa_nome: str
    commessa_codice: str
    business_unit: Optional[str] = None
    items_count: int
    last_updated: Optional[datetime] = None


class PriceCatalogBusinessUnitSummarySchema(BaseModel):
    label: str
    value: Optional[str] = None
    items_count: int
    commesse: list[PriceCatalogCommessaSummarySchema]


class PriceCatalogSummarySchema(BaseModel):
    total_items: int
    total_commesse: int
    business_units: list[PriceCatalogBusinessUnitSummarySchema]


class WbsNodeSchema(BaseModel):
    level: int
    code: Optional[str] = None
    description: Optional[str] = None
    importo: float
    children: list["WbsNodeSchema"] = []


class WbsSpazialeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commessa_id: int
    parent_id: Optional[int] = None
    level: int
    code: str
    description: Optional[str] = None
    importo_totale: Optional[float] = None


class Wbs6NodeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commessa_id: int
    wbs_spaziale_id: Optional[int] = None
    code: str
    description: str
    label: str


class Wbs7NodeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commessa_id: int
    wbs6_id: int
    code: Optional[str] = None
    description: Optional[str] = None


class CommessaWbsSchema(BaseModel):
    commessa_id: int
    spaziali: list[WbsSpazialeSchema]
    wbs6: list[Wbs6NodeSchema]
    wbs7: list[Wbs7NodeSchema]


class WbsImportStatsSchema(BaseModel):
    rows_total: int
    spaziali_inserted: int
    spaziali_updated: int
    wbs6_inserted: int
    wbs6_updated: int
    wbs7_inserted: int
    wbs7_updated: int


class SixImportReportSchema(BaseModel):
    commessa_id: int
    wbs_spaziali: int
    wbs6: int
    wbs7: int
    voci: int
    importo_totale: float
    price_items: Optional[int] = None
    preventivo_id: Optional[str] = None
    voci_stats: Optional[dict[str, int]] = None
    listino_only: bool = False


class SixPreventivoOptionSchema(BaseModel):
    internal_id: str
    code: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    date: Optional[str] = None
    price_list_id: Optional[str] = None
    price_list_label: Optional[str] = None
    rilevazioni: Optional[int] = None
    items: Optional[int] = None
    total_importo: Optional[float] = None


class SixPreventiviPreviewSchema(BaseModel):
    preventivi: list[SixPreventivoOptionSchema]


class SixInspectionPriceListSchema(BaseModel):
    canonical_id: str
    label: str
    aliases: list[str] = []
    priority: int = 0
    products: int = 0
    rilevazioni: int = 0


class SixInspectionGroupSchema(BaseModel):
    grp_id: str
    code: str
    description: Optional[str] = None
    level: Optional[int] = None


class SixPreventivoInspectSchema(BaseModel):
    internal_id: str
    code: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    date: Optional[str] = None
    price_list_id: Optional[str] = None
    rilevazioni: int = 0
    items: int = 0


class SixInspectionSchema(BaseModel):
    preventivi: list[SixPreventivoInspectSchema]
    price_lists: list[SixInspectionPriceListSchema]
    wbs_spaziali: list[SixInspectionGroupSchema]
    wbs6: list[SixInspectionGroupSchema]
    wbs7: list[SixInspectionGroupSchema]
    products_total: int


class WbsVisibilitySchema(BaseModel):
    level: int
    node_id: int
    code: str
    description: Optional[str] = None
    hidden: bool


class WbsVisibilityUpdateSchema(BaseModel):
    level: int
    node_id: int
    hidden: bool


class WbsPathEntrySchema(BaseModel):
    level: int
    code: Optional[str] = None
    description: Optional[str] = None


class AggregatedVoceSchema(BaseModel):
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    quantita_totale: float
    importo_totale: float
    prezzo_unitario: Optional[float] = None
    unita_misura: Optional[str] = None
    wbs_6_code: Optional[str] = None
    wbs_6_description: Optional[str] = None
    wbs_7_code: Optional[str] = None
    wbs_7_description: Optional[str] = None
    wbs_path: list[WbsPathEntrySchema] = []


class ComputoWbsSummary(BaseModel):
    importo_totale: float
    tree: list[WbsNodeSchema]
    voci: list[AggregatedVoceSchema]


class SettingsUpdate(BaseModel):
    delta_minimo_critico: Optional[float] = None
    delta_massimo_critico: Optional[float] = None
    percentuale_cme_alto: Optional[float] = None
    percentuale_cme_basso: Optional[float] = None
    nlp_model_id: Optional[str] = None
    nlp_batch_size: Optional[int] = None
    nlp_max_length: Optional[int] = None


class NlpModelOption(BaseModel):
    id: str
    label: str
    description: str
    dimension: int
    languages: str
    speed: str


class SettingsResponse(BaseModel):
    settings: SettingsRead
    nlp_models: list[NlpModelOption]
    nlp_embeddings_outdated: bool


class PropertySchemaField(BaseModel):
    id: str
    title: Optional[str] = None
    type: Optional[str] = None
    unit: Optional[str] = None
    enum: Optional[list[str]] = None


class PropertyCategorySchema(BaseModel):
    id: str
    name: Optional[str] = None
    required: list[str] = []
    properties: list[PropertySchemaField]


class PropertySchemaResponse(BaseModel):
    categories: list[PropertyCategorySchema]


class ExtractRequest(BaseModel):
    text: str
    category_id: str


class ExtractedPropertiesResponse(BaseModel):
    category_id: str
    properties: dict[str, Any]
    missing_required: list[str] = []


# --- Property lexicon & patterns ---


class PropertyLexiconBase(BaseModel):
    type: str
    canonical: str
    synonyms: Optional[list[str]] = None
    categories: Optional[list[str]] = None
    details: Optional[dict[str, Any]] = None
    active: bool = True


class PropertyLexiconCreate(PropertyLexiconBase):
    pass


class PropertyLexiconUpdate(BaseModel):
    canonical: Optional[str] = None
    synonyms: Optional[list[str]] = None
    categories: Optional[list[str]] = None
    details: Optional[dict[str, Any]] = None
    active: Optional[bool] = None


class PropertyLexiconRead(PropertyLexiconBase):
    id: int
    created_at: datetime
    updated_at: datetime


class PropertyPatternBase(BaseModel):
    category_id: Optional[str] = None
    property_id: Optional[str] = None
    pattern: str
    context_keywords: Optional[list[str]] = None
    priority: int = 0
    active: bool = True


class PropertyPatternCreate(PropertyPatternBase):
    pass


class PropertyPatternUpdate(BaseModel):
    category_id: Optional[str] = None
    property_id: Optional[str] = None
    pattern: Optional[str] = None
    context_keywords: Optional[list[str]] = None
    priority: Optional[int] = None
    active: Optional[bool] = None


class PropertyPatternRead(PropertyPatternBase):
    id: int
    created_at: datetime
    updated_at: datetime


class PropertyOverridePayload(BaseModel):
    category_id: Optional[str] = None
    properties: dict[str, Any]
    source: str = "manual"
    author: Optional[str] = None


class PropertyOverrideRead(PropertyOverridePayload):
    id: int
    price_list_item_id: int
    created_at: datetime
    updated_at: datetime


class PropertyFeedbackPayload(BaseModel):
    category_id: Optional[str] = None
    property_id: Optional[str] = None
    value: Optional[str] = None
    span_start: Optional[int] = None
    span_end: Optional[int] = None
    note: Optional[str] = None
    author: Optional[str] = None


class PropertyFeedbackRead(PropertyFeedbackPayload):
    id: int
    price_list_item_id: int
    created_at: datetime

class PropertyExtractionRequest(BaseModel):
    text: str
    category_id: Optional[str] = None
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    properties: Optional[list[str]] = None
    engine: str = "llm"


class PropertyExtractionResult(BaseModel):
    categoria: str
    properties: dict[str, Any]
    validation: Optional[dict[str, Any]] = None
    confidence_overall: Optional[float] = None
    text_id: Optional[str] = None
    extras: Optional[dict[str, Any]] = None


class DashboardActivitySchema(BaseModel):
    computo_id: int
    computo_nome: str
    tipo: ComputoTipo
    commessa_id: int
    commessa_codice: str
    commessa_nome: str
    created_at: datetime


class DashboardStatsSchema(BaseModel):
    commesse_attive: int
    computi_caricati: int
    ritorni: int
    report_generati: int
    attivita_recente: list[DashboardActivitySchema]


class ConfrontoVoceOffertaSchema(BaseModel):
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    importo_totale: Optional[float] = None
    note: Optional[str] = None
    criticita: Optional[str] = None


class ConfrontoVoceSchema(BaseModel):
    progressivo: Optional[int] = None
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    descrizione_estesa: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario_progetto: Optional[float] = None
    importo_totale_progetto: Optional[float] = None
    offerte: dict[str, ConfrontoVoceOffertaSchema]
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    wbs7_code: Optional[str] = None
    wbs7_description: Optional[str] = None


class ConfrontoImpresaSchema(BaseModel):
    nome: str
    computo_id: int
    impresa: Optional[str] = None
    round_number: Optional[int] = None
    etichetta: Optional[str] = None
    round_label: Optional[str] = None


class ConfrontoRoundSchema(BaseModel):
    numero: int
    label: str
    imprese: list[str]
    imprese_count: int


class ConfrontoOfferteSchema(BaseModel):
    voci: list[ConfrontoVoceSchema]
    imprese: list[ConfrontoImpresaSchema]
    rounds: list[ConfrontoRoundSchema]


class AnalisiConfrontoImportoSchema(BaseModel):
    nome: str
    tipo: ComputoTipo
    importo: float
    delta_percentuale: Optional[float] = None
    impresa: Optional[str] = None
    round_number: Optional[int] = None


class AnalisiDistribuzioneItemSchema(BaseModel):
    nome: str
    valore: int
    colore: str


class AnalisiVoceCriticaSchema(BaseModel):
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    descrizione_estesa: Optional[str] = None
    progetto: float
    imprese: dict[str, float]
    delta: float
    criticita: str
    delta_assoluto: float
    media_prezzo_unitario: Optional[float] = None
    media_importo_totale: Optional[float] = None
    min_offerta: Optional[float] = None
    max_offerta: Optional[float] = None
    impresa_min: Optional[str] = None
    impresa_max: Optional[str] = None
    deviazione_standard: Optional[float] = None
    direzione: str


class AnalisiWBS6CriticitaSchema(BaseModel):
    alta: int = 0
    media: int = 0
    bassa: int = 0


class AnalisiWBS6VoceSchema(BaseModel):
    codice: Optional[str] = None
    descrizione: Optional[str] = None
    descrizione_estesa: Optional[str] = None
    unita_misura: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_unitario_progetto: Optional[float] = None
    importo_totale_progetto: Optional[float] = None
    media_prezzo_unitario: Optional[float] = None
    media_importo_totale: Optional[float] = None
    delta_percentuale: Optional[float] = None
    delta_assoluto: Optional[float] = None
    offerte_considerate: int = 0
    importo_minimo: Optional[float] = None
    importo_massimo: Optional[float] = None
    impresa_min: Optional[str] = None
    impresa_max: Optional[str] = None
    deviazione_standard: Optional[float] = None
    criticita: Optional[str] = None


class AnalisiWBS6TrendSchema(BaseModel):
    wbs6_id: str
    wbs6_label: str
    wbs6_code: Optional[str] = None
    wbs6_description: Optional[str] = None
    progetto: float
    media_ritorni: float
    delta_percentuale: float
    delta_assoluto: float
    conteggi_criticita: AnalisiWBS6CriticitaSchema
    offerte_considerate: int
    offerte_totali: int
    voci: list[AnalisiWBS6VoceSchema]


class AnalisiRoundSchema(BaseModel):
    numero: int
    label: str
    imprese: list[str]
    imprese_count: int


class AnalisiImpresaSchema(BaseModel):
    computo_id: int
    nome: str
    impresa: Optional[str] = None
    etichetta: Optional[str] = None
    round_number: Optional[int] = None
    round_label: Optional[str] = None


class AnalisiFiltriSchema(BaseModel):
    round_number: Optional[int] = None
    impresa: Optional[str] = None
    impresa_normalizzata: Optional[str] = None
    offerte_totali: int
    offerte_considerate: int
    imprese_attive: list[str]


class AnalisiThresholdsSchema(BaseModel):
    media_percent: float
    alta_percent: float


class AnalisiCommessaSchema(BaseModel):
    confronto_importi: list[AnalisiConfrontoImportoSchema]
    distribuzione_variazioni: list[AnalisiDistribuzioneItemSchema]
    voci_critiche: list[AnalisiVoceCriticaSchema]
    analisi_per_wbs6: list[AnalisiWBS6TrendSchema]
    rounds: list[AnalisiRoundSchema]
    imprese: list[AnalisiImpresaSchema]
    filtri: AnalisiFiltriSchema
    thresholds: AnalisiThresholdsSchema


# Analisi Avanzate - Trend Evoluzione Round
class TrendEvoluzioneOffertaSchema(BaseModel):
    """Dati di un'offerta in uno specifico round."""
    round: int
    round_label: Optional[str] = None
    importo: float
    delta: Optional[float] = None  # % vs round precedente


class TrendEvoluzioneImpresaSchema(BaseModel):
    """Dati trend di un'impresa attraverso i round."""
    impresa: str
    color: str
    offerte: list[TrendEvoluzioneOffertaSchema]
    delta_complessivo: Optional[float] = None  # % primo vs ultimo round


class TrendEvoluzioneSchema(BaseModel):
    """Schema per il grafico Trend Evoluzione Prezzi tra Round."""
    imprese: list[TrendEvoluzioneImpresaSchema]
    rounds: list[AnalisiRoundSchema]
    filtri: AnalisiFiltriSchema


# Analisi Avanzate - Heatmap Competitività
class HeatmapCategoriaSchema(BaseModel):
    """Definizione categoria WBS6 nella heatmap."""
    categoria: str
    importo_progetto: float


class HeatmapImpresaCategoriaSchema(BaseModel):
    """Offerta di un'impresa per una specifica categoria."""
    categoria: str
    importo_offerta: float
    delta: float  # % vs progetto


class HeatmapImpresaSchema(BaseModel):
    """Dati completi di un'impresa nella heatmap."""
    impresa: str
    categorie: list[HeatmapImpresaCategoriaSchema]


class HeatmapCompetitivitaSchema(BaseModel):
    """Schema per il grafico Heatmap Competitività."""
    categorie: list[HeatmapCategoriaSchema]
    imprese: list[HeatmapImpresaSchema]
    filtri: AnalisiFiltriSchema


# Import Configurations
class ImportConfigCreateSchema(BaseModel):
    nome: str
    impresa: str | None = None
    sheet_name: str | None = None
    code_columns: str | None = None
    description_columns: str | None = None
    price_column: str | None = None
    quantity_column: str | None = None
    note: str | None = None


class ImportConfigSchema(ImportConfigCreateSchema):
    id: int
    commessa_id: int | None
    created_at: datetime
    updated_at: datetime


class ImportBatchSingleFileFailureSchema(BaseModel):
    impresa: str
    error: str
    error_type: Optional[str] = None
    details: Optional[str] = None
    config: Optional[dict[str, Any]] = None


class ImportBatchSingleFileResultSchema(BaseModel):
    success: list[str]
    failed: list[ImportBatchSingleFileFailureSchema]
    total: int
    success_count: int
    failed_count: int
    computi: dict[str, ComputoSchema]

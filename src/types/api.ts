export type ComputoTipo = "progetto" | "ritorno";

export interface ApiComputo {
  id: number;
  nome: string;
  tipo: ComputoTipo;
  impresa?: string | null;
  round_number?: number | null;
  importo_totale?: number | null;
  delta_vs_progetto?: number | null;
  percentuale_delta?: number | null;
  note?: string | null;
  file_nome?: string | null;
  created_at: string;
  updated_at: string;
  matching_report?: Record<string, any> | null;
}

export type CommessaStato = "setup" | "in_corso" | "chiusa";

export interface ApiCommessa {
  id: number;
  nome: string;
  codice: string;
  descrizione?: string | null;
  note?: string | null;
  business_unit?: string | null;
  revisione?: string | null;
  stato: CommessaStato;
  created_at: string;
  updated_at: string;
}

export interface ApiCommessaDetail extends ApiCommessa {
  computi: ApiComputo[];
}

export interface ApiWbsNode {
  level: number;
  code?: string | null;
  description?: string | null;
  importo: number;
  children: ApiWbsNode[];
}

export interface ApiWbsPathEntry {
  level: number;
  code?: string | null;
  description?: string | null;
}

export interface ApiAggregatedVoce {
  codice?: string | null;
  descrizione?: string | null;
  quantita_totale: number;
  importo_totale: number;
  prezzo_unitario?: number | null;
   unita_misura?: string | null;
  wbs_6_code?: string | null;
  wbs_6_description?: string | null;
  wbs_7_code?: string | null;
  wbs_7_description?: string | null;
  wbs_path?: ApiWbsPathEntry[];
}

export interface ApiComputoWbsSummary {
  importo_totale: number;
  tree: ApiWbsNode[];
  voci: ApiAggregatedVoce[];
}

export interface FrontendWbsNode {
  id: string;
  level: number;
  code?: string | null;
  description?: string | null;
  importo: number;
  children: FrontendWbsNode[];
  path: ApiWbsPathEntry[];
}

export interface ApiWbsSpazialeNode {
  id: number;
  commessa_id: number;
  parent_id?: number | null;
  level: number;
  code: string;
  description?: string | null;
  importo_totale?: number | null;
}

export interface ApiWbs6Node {
  id: number;
  commessa_id: number;
  wbs_spaziale_id?: number | null;
  code: string;
  description: string;
  label: string;
}

export interface ApiWbs7Node {
  id: number;
  commessa_id: number;
  wbs6_id: number;
  code?: string | null;
  description?: string | null;
}

export interface ApiCommessaWbs {
  commessa_id: number;
  spaziali: ApiWbsSpazialeNode[];
  wbs6: ApiWbs6Node[];
  wbs7: ApiWbs7Node[];
}

export interface ApiWbsImportStats {
  rows_total: number;
  spaziali_inserted: number;
  spaziali_updated: number;
  wbs6_inserted: number;
  wbs6_updated: number;
  wbs7_inserted: number;
  wbs7_updated: number;
}

export interface ApiWbsVisibilityEntry {
  level: number;
  node_id: number;
  code: string;
  description?: string | null;
  hidden: boolean;
}

export interface ApiSixImportReport {
  commessa_id: number;
  wbs_spaziali: number;
  wbs6: number;
  wbs7: number;
  voci: number;
  importo_totale: number;
  price_items?: number | null;
  preventivo_id?: string | null;
  listino_only?: boolean;
}

export interface ApiSixPreventivoOption {
  internal_id: string;
  code?: string | null;
  description?: string | null;
}

export interface ApiSixPreventiviPreview {
  preventivi: ApiSixPreventivoOption[];
}

export interface ApiSixInspectionPriceList {
  canonical_id: string;
  label: string;
  aliases: string[];
  priority: number;
  products: number;
  rilevazioni: number;
}

export interface ApiSixInspectionGroup {
  grp_id: string;
  code: string;
  description?: string | null;
  level?: number | null;
}

export interface ApiSixInspectionPreventivo {
  internal_id: string;
  code?: string | null;
  description?: string | null;
  author?: string | null;
  version?: string | null;
  date?: string | null;
  price_list_id?: string | null;
  rilevazioni: number;
  items: number;
}

export interface ApiSixInspection {
  preventivi: ApiSixInspectionPreventivo[];
  price_lists: ApiSixInspectionPriceList[];
  wbs_spaziali: ApiSixInspectionGroup[];
  wbs6: ApiSixInspectionGroup[];
  wbs7: ApiSixInspectionGroup[];
  products_total: number;
}

export interface ApiNlpModelOption {
  id: string;
  label: string;
  description: string;
  dimension: number;
  languages: string;
  speed: string;
}

export interface ApiSettings {
  id: number;
  delta_minimo_critico: number;
  delta_massimo_critico: number;
  percentuale_cme_alto: number;
  percentuale_cme_basso: number;
  nlp_model_id: string;
  nlp_batch_size: number;
  nlp_max_length: number;
  nlp_embeddings_model_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiSettingsResponse {
  settings: ApiSettings;
  nlp_models: ApiNlpModelOption[];
  nlp_embeddings_outdated: boolean;
}

export interface PropertySchemaField {
  id: string;
  title?: string | null;
  type?: string | null;
  unit?: string | null;
  enum?: string[] | null;
}

export interface PropertyCategorySchema {
  id: string;
  name?: string | null;
  required: string[];
  properties: PropertySchemaField[];
}

export interface PropertySchemaResponse {
  categories: PropertyCategorySchema[];
}

export interface PropertyExtractionPayload {
  text: string;
  category_id: string;
  wbs6_code?: string | null;
  wbs6_description?: string | null;
  properties?: string[];
  engine?: "llm" | "rules";
}

export interface PropertyExtractionResult {
  category_id: string;
  properties: Record<string, any>;
  missing_required: string[];
}

export interface ApiImportConfigCreate {
  nome: string;
  impresa?: string | null;
  sheet_name?: string | null;
  code_columns?: string | null;
  description_columns?: string | null;
  price_column?: string | null;
  quantity_column?: string | null;
  note?: string | null;
}

export interface ApiImportConfig extends ApiImportConfigCreate {
  id: number;
  commessa_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ApiCommessaPreferencesCreate {
  selected_preventivo_id?: string | null;
  selected_price_list_id?: string | null;
  default_wbs_view?: string | null;
  custom_settings?: Record<string, unknown> | null;
}

export interface ApiCommessaPreferences extends ApiCommessaPreferencesCreate {
  id: number;
  commessa_id: number;
  created_at: string;
  updated_at: string;
}

export interface ApiDashboardActivity {
  computo_id: number;
  computo_nome: string;
  tipo: ComputoTipo;
  commessa_id: number;
  commessa_codice: string;
  commessa_nome: string;
  created_at: string;
}

export interface ApiDashboardStats {
  commesse_attive: number;
  computi_caricati: number;
  ritorni: number;
  report_generati: number;
  attivita_recente: ApiDashboardActivity[];
}

export interface ApiConfrontoVoceOfferta {
  quantita?: number | null;
  prezzo_unitario?: number | null;
  importo_totale?: number | null;
  note?: string | null;
  criticita?: string | null;
}

export interface ApiConfrontoVoce {
  codice?: string | null;
  descrizione?: string | null;
  descrizione_estesa?: string | null;
  unita_misura?: string | null;
  quantita?: number | null;
  prezzo_unitario_progetto?: number | null;
  importo_totale_progetto?: number | null;
  offerte: Record<string, ApiConfrontoVoceOfferta>;
  wbs6_code?: string | null;
  wbs6_description?: string | null;
  wbs7_code?: string | null;
  wbs7_description?: string | null;
}

export interface ApiConfrontoImpresa {
  nome: string;
  computo_id: number;
  impresa?: string | null;
  round_number?: number | null;
  etichetta?: string | null;
  round_label?: string | null;
}

export interface ApiConfrontoRound {
  numero: number;
  label: string;
  imprese: string[];
  imprese_count: number;
}

export interface ApiConfrontoOfferte {
  voci: ApiConfrontoVoce[];
  imprese: ApiConfrontoImpresa[];
  rounds: ApiConfrontoRound[];
}

export interface ApiAnalisiConfrontoImporto {
  nome: string;
  tipo: ComputoTipo;
  importo: number;
  delta_percentuale?: number | null;
  impresa?: string | null;
  round_number?: number | null;
}

export interface ApiAnalisiDistribuzioneItem {
  nome: string;
  valore: number;
  colore: string;
}

export interface ApiAnalisiVoceCritica {
  codice?: string | null;
  descrizione?: string | null;
  descrizione_estesa?: string | null;
  progetto: number;
  imprese: Record<string, number>;
  delta: number;
  criticita: string;
  delta_assoluto: number;
  media_prezzo_unitario?: number | null;
  media_importo_totale?: number | null;
  min_offerta?: number | null;
  max_offerta?: number | null;
  impresa_min?: string | null;
  impresa_max?: string | null;
  deviazione_standard?: number | null;
  direzione: string;
}

export interface ApiAnalisiWBS6Criticita {
  alta: number;
  media: number;
  bassa: number;
}

export interface ApiAnalisiWBS6Voce {
  codice?: string | null;
  descrizione?: string | null;
  descrizione_estesa?: string | null;
  unita_misura?: string | null;
  quantita?: number | null;
  prezzo_unitario_progetto?: number | null;
  importo_totale_progetto?: number | null;
  media_prezzo_unitario?: number | null;
  media_importo_totale?: number | null;
  delta_percentuale?: number | null;
  delta_assoluto?: number | null;
  offerte_considerate: number;
  importo_minimo?: number | null;
  importo_massimo?: number | null;
  impresa_min?: string | null;
  impresa_max?: string | null;
  deviazione_standard?: number | null;
  criticita?: string | null;
  direzione?: string;
}

export interface ApiAnalisiWBS6Trend {
  wbs6_id: string;
  wbs6_label: string;
  wbs6_code?: string | null;
  wbs6_description?: string | null;
  progetto: number;
  media_ritorni: number;
  delta_percentuale: number;
  delta_assoluto: number;
  conteggi_criticita: ApiAnalisiWBS6Criticita;
  offerte_considerate: number;
  offerte_totali: number;
  voci: ApiAnalisiWBS6Voce[];
}

export interface ApiAnalisiRound {
  numero: number;
  label: string;
  imprese: string[];
  imprese_count: number;
}

export interface ApiAnalisiImpresa {
  computo_id: number;
  nome: string;
  impresa?: string | null;
  etichetta?: string | null;
  round_number?: number | null;
  round_label?: string | null;
}

export interface ApiAnalisiFiltri {
  round_number?: number | null;
  impresa?: string | null;
  impresa_normalizzata?: string | null;
  offerte_totali: number;
  offerte_considerate: number;
  imprese_attive: string[];
}

export interface ApiAnalisiThresholds {
  media_percent: number;
  alta_percent: number;
}

export interface ApiAnalisiCommessa {
  confronto_importi: ApiAnalisiConfrontoImporto[];
  distribuzione_variazioni: ApiAnalisiDistribuzioneItem[];
  voci_critiche: ApiAnalisiVoceCritica[];
  analisi_per_wbs6: ApiAnalisiWBS6Trend[];
  rounds: ApiAnalisiRound[];
  imprese: ApiAnalisiImpresa[];
  filtri: ApiAnalisiFiltri;
  thresholds: ApiAnalisiThresholds;
}

// Trend Evoluzione Round
export interface ApiTrendEvoluzioneOfferta {
  round: number;
  round_label?: string | null;
  importo: number;
  delta?: number | null;
}

export interface ApiTrendEvoluzioneImpresa {
  impresa: string;
  color: string;
  offerte: ApiTrendEvoluzioneOfferta[];
  delta_complessivo?: number | null;
}

export interface ApiTrendEvoluzione {
  imprese: ApiTrendEvoluzioneImpresa[];
  rounds: ApiAnalisiRound[];
  filtri: ApiAnalisiFiltri;
}

// Heatmap Competitività
export interface ApiHeatmapCategoria {
  categoria: string;
  importo_progetto: number;
}

export interface ApiHeatmapImpresaCategoria {
  categoria: string;
  importo_offerta: number;
  delta: number;
}

export interface ApiHeatmapImpresa {
  impresa: string;
  categorie: ApiHeatmapImpresaCategoria[];
}

export interface ApiHeatmapCompetitivita {
  categorie: ApiHeatmapCategoria[];
  imprese: ApiHeatmapImpresa[];
  filtri: ApiAnalisiFiltri;
}

export interface ApiPriceListOffer {
  id: number;
  price_list_item_id: number;
  computo_id: number;
  impresa_id?: number | null;
  impresa_label?: string | null;
  round_number?: number | null;
  prezzo_unitario: number;
  quantita?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ApiPriceListItem {
  id: number;
  commessa_id: number;
  commessa_nome: string;
  commessa_codice: string;
  business_unit?: string | null;
  product_id: string;
  item_code: string;
  item_description?: string | null;
  unit_id?: string | null;
  unit_label?: string | null;
  wbs6_code?: string | null;
  wbs6_description?: string | null;
  wbs7_code?: string | null;
  wbs7_description?: string | null;
  price_lists?: Record<string, number> | null;
  extra_metadata?: Record<string, any> | null;
  source_file?: string | null;
  preventivo_id?: string | null;
  project_price?: number | null;
  project_quantity?: number | null;
  offer_prices?: Record<
    string,
    {
      price: number | null;
      quantity?: number | null;
      round_number?: number | null;
      computo_id?: number | null;
    }
  > | null;
  offers?: ApiPriceListOffer[];
  created_at: string;
  updated_at: string;
}

export interface ApiManualPriceUpdateResponse {
  offer: ApiPriceListOffer;
  computo: ApiComputo;
}

export interface ApiPriceListItemSearchResult extends ApiPriceListItem {
  score: number;
  match_reason?: string | null;
}

export interface ApiPriceCatalogCommessaSummary {
  commessa_id: number;
  commessa_nome: string;
  commessa_codice: string;
  business_unit?: string | null;
  items_count: number;
  last_updated?: string | null;
}

export interface ApiPriceCatalogBusinessUnitSummary {
  label: string;
  value?: string | null;
  items_count: number;
  commesse: ApiPriceCatalogCommessaSummary[];
}

export interface ApiPriceCatalogSummary {
  total_items: number;
  total_commesse: number;
  business_units: ApiPriceCatalogBusinessUnitSummary[];
}

export type ApiUserRole = "admin" | "manager" | "user";

export interface ApiUser {
  id: number;
  email: string;
  full_name?: string | null;
  role: ApiUserRole;
  is_active: boolean;
  created_at: string;
}

export interface ApiUserProfile {
  id: number;
  user_id: number;
  company?: string | null;
  language?: string | null;
  settings?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface ApiAuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: ApiUser;
}

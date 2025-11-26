export type { ApiCommessa } from "@/types/api";

import {
  ApiAnalisiCommessa,
  ApiAnalisiWBS6Trend,
  ApiAuthResponse,
  ApiCommessa,
  ApiCommessaDetail,
  ApiCommessaPreferences,
  ApiCommessaPreferencesCreate,
  ApiCommessaWbs,
  ApiComputo,
  ApiComputoWbsSummary,
  ApiConfrontoOfferte,
  ApiDashboardStats,
  ApiHeatmapCompetitivita,
  ApiManualPriceUpdateResponse,
  ApiImportConfig,
  ApiImportConfigCreate,
  ApiBatchSingleFileResult,
  ApiPriceCatalogSummary,
  ApiPriceListItem,
  ApiPriceListItemSearchResult,
  ApiSettings,
  ApiSettingsResponse,
  ApiSixImportReport,
  ApiSixPreventiviPreview,
  ApiTrendEvoluzione,
  ApiUser,
  ApiUserProfile,
  ApiWbsImportStats,
  ApiWbsVisibilityEntry,
  CommessaStato,
  PropertySchemaResponse,
  PropertyExtractionPayload,
  PropertyExtractionResult,
} from "@/types/api";
import { getAccessToken } from "./auth-storage";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const propertySchemasStaticOnly =
  (import.meta.env.VITE_PROPERTY_SCHEMAS_STATIC as string | undefined)?.toLowerCase() === "true" ||
  (import.meta.env.VITE_PROPERTY_SCHEMAS_STATIC as string | undefined) === "1";

let propertySchemasFallbackPreferred = false;
const propertyExtractionStaticOnly =
  (import.meta.env.VITE_PROPERTY_EXTRACTION_STATIC as string | undefined)?.toLowerCase() === "true" ||
  (import.meta.env.VITE_PROPERTY_EXTRACTION_STATIC as string | undefined) === "1";
const propertyExtractionNoFallback =
  (import.meta.env.VITE_PROPERTY_EXTRACTION_NO_FALLBACK as string | undefined)?.toLowerCase() === "true" ||
  (import.meta.env.VITE_PROPERTY_EXTRACTION_NO_FALLBACK as string | undefined) === "1";
let propertyExtractionFallbackPreferred = false;

const apiBaseNoTrailing = API_BASE_URL.replace(/\/+$/, "");
const apiBaseWithoutPrefix = apiBaseNoTrailing.replace(/\/api\/v1$/, "");

const fetchPropertySchemasStatic = async (): Promise<PropertySchemaResponse> => {
  const base = import.meta.env.BASE_URL || "/";
  const fallbackUrl = base.endsWith("/") ? `${base}property-schemas.json` : `${base}/property-schemas.json`;
  const response = await fetch(fallbackUrl, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Impossibile caricare gli schemi proprietà da asset statico (${response.status})`);
  }
  return (await response.json()) as PropertySchemaResponse;
};

const buildExtractionFallback = (payload: PropertyExtractionPayload): PropertyExtractionResult => ({
  category_id: payload.category_id,
  properties: {},
  missing_required: [],
});

const authHeaders = () => {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const tryExtractAtUrl = async (url: string, payload: PropertyExtractionPayload) => {
  const response = await fetch(url, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as PropertyExtractionResult;
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: options?.cache ?? "no-store",
    headers: {
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    const contentType = response.headers.get("content-type") ?? "";

    if (contentType.includes("application/json")) {
      try {
        const payload: unknown = await response.json();
        if (typeof payload === "string") {
          message = payload;
        } else if (payload && typeof payload === "object") {
          const data = payload as Record<string, unknown>;
          if (Array.isArray(data.detail)) {
            message = data.detail
              .map((item) => {
                if (typeof item === "string") return item;
                if (item && typeof item === "object" && "msg" in item) {
                  return String((item as Record<string, unknown>).msg);
                }
                return JSON.stringify(item);
              })
              .join("\n");
          } else if (data.detail) {
            if (
              typeof data.detail === "object" &&
              data.detail !== null &&
              "message" in data.detail
            ) {
              message = String(
                (data.detail as Record<string, unknown>).message ?? "Richiesta non valida",
              );
            } else {
              message = String(data.detail);
            }
          } else if (data.message) {
            message = String(data.message);
          }
        }
      } catch {
        const fallback = await response.text();
        if (fallback) message = fallback;
      }
    } else {
      const text = await response.text();
      if (text) message = text;
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const expectsJson = response.headers.get("content-type")?.includes("application/json");
  if (!expectsJson) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  async listCommesse(): Promise<ApiCommessa[]> {
    return apiFetch<ApiCommessa[]>("/commesse");
  },

  async getCommessa(id: number | string): Promise<ApiCommessaDetail> {
    return apiFetch<ApiCommessaDetail>(`/commesse/${id}`);
  },

  async exportCommessaBundle(
    commessaId: number | string,
  ): Promise<{ blob: Blob; filename: string }> {
    const token = getAccessToken();
    const response = await fetch(`${API_BASE_URL}/commesse/${commessaId}/bundle`, {
      method: "GET",
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      let message = `Request failed with status ${response.status}`;
      const contentType = response.headers.get("content-type") ?? "";

      if (contentType.includes("application/json")) {
        try {
          const payload: unknown = await response.json();
          if (payload && typeof payload === "object") {
            const data = payload as Record<string, unknown>;
            if (Array.isArray(data.detail)) {
              message = data.detail
                .map((item) => {
                  if (typeof item === "string") return item;
                  if (item && typeof item === "object" && "msg" in item) {
                    return String((item as Record<string, unknown>).msg);
                  }
                  return JSON.stringify(item);
                })
                .join("\n");
            } else if (data.detail) {
              if (
                typeof data.detail === "object" &&
                data.detail !== null &&
                "message" in data.detail
              ) {
                message = String(
                  (data.detail as Record<string, unknown>).message ?? "Richiesta non valida",
                );
              } else {
                message = String(data.detail);
              }
            } else if (data.message) {
              message = String(data.message);
            }
          }
        } catch {
          const fallback = await response.text();
          if (fallback) message = fallback;
        }
      } else {
        const text = await response.text();
        if (text) message = text;
      }

      throw new Error(message);
    }

    const contentDisposition = response.headers.get("content-disposition") ?? "";
    const filenameMatch = contentDisposition.match(/filename\*?=([^;]+)/i);
    const filename = filenameMatch
      ? decodeURIComponent(filenameMatch[1].replace(/^"|"$/g, "").replace("UTF-8''", ""))
      : `commessa-${commessaId}.mmcomm`;

    const blob = await response.blob();
    return { blob, filename };
  },

  async createCommessa(payload: {
    nome: string;
    codice: string;
    descrizione?: string | null;
    note?: string | null;
    business_unit?: string | null;
    revisione?: string | null;
    stato?: CommessaStato;
  }): Promise<ApiCommessa> {
    return apiFetch<ApiCommessa>("/commesse", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async importCommessaBundle(
    file: File,
    options?: { overwrite?: boolean },
  ): Promise<ApiCommessa> {
    const formData = new FormData();
    formData.append("file", file);
    const params = new URLSearchParams();
    if (options?.overwrite) {
      params.set("overwrite", "true");
    }
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<ApiCommessa>(`/commesse/import-bundle${suffix}`, {
      method: "POST",
      body: formData,
    });
  },

  async updateCommessa(
    commessaId: number | string,
    payload: {
      nome: string;
      codice: string;
      descrizione?: string | null;
      note?: string | null;
      business_unit?: string | null;
      revisione?: string | null;
      stato?: CommessaStato;
    }
  ): Promise<ApiCommessa> {
    return apiFetch<ApiCommessa>(`/commesse/${commessaId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async getCommessaPreferences(commessaId: number | string): Promise<ApiCommessaPreferences> {
    return apiFetch<ApiCommessaPreferences>(`/commesse/${commessaId}/preferences`);
  },

  async updateCommessaPreferences(
    commessaId: number | string,
    payload: ApiCommessaPreferencesCreate
  ): Promise<ApiCommessaPreferences> {
    return apiFetch<ApiCommessaPreferences>(`/commesse/${commessaId}/preferences`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async getCommessaWbsStructure(
    commessaId: number | string,
  ): Promise<ApiCommessaWbs> {
    return apiFetch<ApiCommessaWbs>(`/commesse/${commessaId}/wbs`);
  },

  async uploadCommessaWbs(
    commessaId: number | string,
    file: File,
    mode: "create" | "update" = "create",
  ): Promise<ApiWbsImportStats> {
    const formData = new FormData();
    formData.append("file", file);
    const method = mode === "create" ? "POST" : "PUT";
    return apiFetch<ApiWbsImportStats>(`/commesse/${commessaId}/wbs/upload`, {
      method,
      body: formData,
    });
  },

  async getWbsVisibility(
    commessaId: number | string,
  ): Promise<ApiWbsVisibilityEntry[]> {
    return apiFetch<ApiWbsVisibilityEntry[]>(
      `/commesse/${commessaId}/wbs/visibility`,
    );
  },

  async updateWbsVisibility(
    commessaId: number | string,
    payload: { level: number; node_id: number; hidden: boolean }[],
  ): Promise<ApiWbsVisibilityEntry[]> {
    return apiFetch<ApiWbsVisibilityEntry[]>(
      `/commesse/${commessaId}/wbs/visibility`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    );
  },


  async deleteCommessa(commessaId: number | string): Promise<void> {
    return apiFetch<void>(`/commesse/${commessaId}`, {
      method: "DELETE",
    });
  },

  async uploadComputoProgetto(
    commessaId: number | string,
    file: File,
  ): Promise<ApiComputo> {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch<ApiComputo>(`/commesse/${commessaId}/computo-progetto`, {
      method: "POST",
      body: formData,
    });
  },

  async previewSixPreventivi(
    commessaId: number | string,
    file: File,
  ): Promise<ApiSixPreventiviPreview> {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch<ApiSixPreventiviPreview>(
      `/commesse/${commessaId}/import-six/preview`,
      {
        method: "POST",
        body: formData,
      },
    );
  },

  async importSixFile(
    commessaId: number | string,
    file: File,
    preventivoId?: string | null,
    options?: {
      enableEmbeddings?: boolean;
      enablePropertyExtraction?: boolean;
    },
  ): Promise<ApiSixImportReport> {
    const formData = new FormData();
    formData.append("file", file);
    if (preventivoId) {
      formData.append("preventivo_id", preventivoId);
    }
    if (options?.enableEmbeddings) {
      formData.append("compute_embeddings", "true");
    }
    if (options?.enablePropertyExtraction) {
      formData.append("extract_properties", "true");
    }
    return apiFetch<ApiSixImportReport>(`/commesse/${commessaId}/import-six`, {
      method: "POST",
      body: formData,
    });
  },

  async uploadRitorno(
    commessaId: number | string,
    params: {
      file: File;
      impresa: string;
      roundMode: "new" | "replace";
      roundNumber?: number;
      sheetName: string;
      codeColumns: string[];
      descriptionColumns: string[];
      priceColumn: string;
      quantityColumn?: string;
      progressColumn?: string;
    },
  ): Promise<ApiComputo> {
    const {
      file,
      impresa,
      roundMode,
      roundNumber,
      sheetName,
      codeColumns,
      descriptionColumns,
      priceColumn,
      quantityColumn,
      progressColumn,
    } = params;
    const formData = new FormData();
    formData.append("file", file);
    formData.append("impresa", impresa);
    formData.append("round_mode", roundMode);
    if (roundNumber !== undefined && roundNumber !== null) {
      formData.append("round_number", String(roundNumber));
    }
    formData.append("sheet_name", sheetName);
    if (codeColumns?.length) {
      formData.append("code_columns", JSON.stringify(codeColumns));
    }
    if (descriptionColumns?.length) {
      formData.append("description_columns", JSON.stringify(descriptionColumns));
    }
    formData.append("price_column", priceColumn);
    if (quantityColumn) {
      formData.append("quantity_column", quantityColumn);
    }
    if (progressColumn) {
      formData.append("progressive_column", progressColumn);
    }
    return apiFetch<ApiComputo>(`/commesse/${commessaId}/ritorni`, {
      method: "POST",
      body: formData,
    });
  },

  async uploadRitorniBatchSingleFile(
    commessaId: number | string,
    params: {
      file: File;
      impreseConfig: {
        nome_impresa: string;
        colonna_prezzo: string;
        colonna_quantita?: string | null;
        round_number?: number | null;
        round_mode?: "auto" | "new" | "replace";
      }[];
      sheetName?: string | null;
      codeColumns?: string[];
      descriptionColumns?: string[];
      progressiveColumn?: string | null;
    },
  ): Promise<ApiBatchSingleFileResult> {
    const formData = new FormData();
    formData.append("file", params.file);
    formData.append("imprese_config", JSON.stringify(params.impreseConfig));
    if (params.sheetName) {
      formData.append("sheet_name", params.sheetName);
    }
    if (params.codeColumns?.length) {
      formData.append("code_columns", JSON.stringify(params.codeColumns));
    }
    if (params.descriptionColumns?.length) {
      formData.append("description_columns", JSON.stringify(params.descriptionColumns));
    }
    if (params.progressiveColumn) {
      formData.append("progressive_column", params.progressiveColumn);
    }
    return apiFetch<ApiBatchSingleFileResult>(
      `/commesse/${commessaId}/ritorni/batch-single-file`,
      {
        method: "POST",
        body: formData,
      },
    );
  },

  async deleteComputo(
    commessaId: number | string,
    computoId: number | string,
  ): Promise<void> {
    return apiFetch<void>(`/commesse/${commessaId}/computo/${computoId}`, {
      method: "DELETE",
    });
  },

  async getComputoWbs(
    computoIdOrCommessaId: number | string,
    computoId?: number | string
  ): Promise<ApiComputoWbsSummary> {
    // If second parameter is provided, use it as computoId (ignoring first param for backward compatibility)
    const actualComputoId = computoId !== undefined ? computoId : computoIdOrCommessaId;
    return apiFetch<ApiComputoWbsSummary>(`/computi/${actualComputoId}/wbs`);
  },

  async getDashboardStats(): Promise<ApiDashboardStats> {
    return apiFetch<ApiDashboardStats>("/dashboard/stats");
  },

  async getCommessaConfronto(commessaId: number | string): Promise<ApiConfrontoOfferte> {
    return apiFetch<ApiConfrontoOfferte>(`/commesse/${commessaId}/confronto`);
  },

  async getCommessaAnalisi(
    commessaId: number | string,
    params?: { round_number?: number | null; impresa?: string | null },
  ): Promise<ApiAnalisiCommessa> {
    const query = new URLSearchParams();
    if (params?.round_number != null) {
      query.set("round_number", String(params.round_number));
    }
    if (params?.impresa) {
      query.set("impresa", params.impresa);
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<ApiAnalisiCommessa>(`/commesse/${commessaId}/analisi${suffix}`);
  },

  async getCommessaAnalisiWbs6(
    commessaId: number | string,
    wbs6Id: string,
    params?: { round_number?: number | null; impresa?: string | null },
  ): Promise<ApiAnalisiWBS6Trend> {
    const query = new URLSearchParams();
    if (params?.round_number != null) {
      query.set("round_number", String(params.round_number));
    }
    if (params?.impresa) {
      query.set("impresa", params.impresa);
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<ApiAnalisiWBS6Trend>(
      `/commesse/${commessaId}/analisi/wbs6/${wbs6Id}${suffix}`,
    );
  },

  async getCommessaTrendRound(
    commessaId: number | string,
    params?: { impresa?: string | null },
  ): Promise<ApiTrendEvoluzione> {
    const query = new URLSearchParams();
    if (params?.impresa) {
      query.set("impresa", params.impresa);
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<ApiTrendEvoluzione>(
      `/commesse/${commessaId}/analisi/trend-round${suffix}`,
    );
  },

  async getCommessaHeatmapCompetitivita(
    commessaId: number | string,
    params?: { round_number?: number | null },
  ): Promise<ApiHeatmapCompetitivita> {
    const query = new URLSearchParams();
    if (params?.round_number != null) {
      query.set("round_number", String(params.round_number));
    }
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return apiFetch<ApiHeatmapCompetitivita>(
      `/commesse/${commessaId}/analisi/heatmap-competitivita${suffix}`,
    );
  },

  async getSettings(): Promise<ApiSettingsResponse> {
    return apiFetch<ApiSettingsResponse>("/settings/");
  },

  async listImportConfigs(options?: {
    commessaId?: number | string | null;
  }): Promise<ApiImportConfig[]> {
    const params = new URLSearchParams();
    if (options?.commessaId !== undefined && options?.commessaId !== null) {
      params.set("commessa_id", String(options.commessaId));
    }
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<ApiImportConfig[]>(`/import-configs${suffix}`);
  },

  async createImportConfig(
    payload: ApiImportConfigCreate,
    options?: { commessaId?: number | string | null },
  ): Promise<ApiImportConfig> {
    const params = new URLSearchParams();
    if (options?.commessaId !== undefined && options?.commessaId !== null) {
      params.set("commessa_id", String(options.commessaId));
    }
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<ApiImportConfig>(`/import-configs${suffix}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async updateImportConfig(
    configId: number | string,
    payload: ApiImportConfigCreate,
  ): Promise<ApiImportConfig> {
    return apiFetch<ApiImportConfig>(`/import-configs/${configId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async deleteImportConfig(configId: number | string): Promise<void> {
    await apiFetch<void>(`/import-configs/${configId}`, {
      method: "DELETE",
    });
  },

  async updateSettings(payload: {
    delta_minimo_critico?: number;
    delta_massimo_critico?: number;
    percentuale_cme_alto?: number;
    percentuale_cme_basso?: number;
    nlp_model_id?: string;
    nlp_batch_size?: number;
    nlp_max_length?: number;
  }): Promise<ApiSettingsResponse> {
    return apiFetch<ApiSettingsResponse>("/settings/", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async regenerateEmbeddings(commessaId?: number): Promise<{
    message: string;
    total: number;
    updated: number;
    skipped: number;
    errors: number;
  }> {
    const params = new URLSearchParams();
    if (commessaId !== undefined) {
      params.set("commessa_id", String(commessaId));
    }
    const url = `/settings/regenerate-embeddings${params.toString() ? `?${params.toString()}` : ""}`;
    return apiFetch(url, {
      method: "POST",
    });
  },

  async regenerateProperties(commessaId?: number): Promise<{
    message: string;
    total: number;
    updated: number;
    skipped: number;
    errors: number;
  }> {
    const params = new URLSearchParams();
    if (commessaId !== undefined) {
      params.set("commessa_id", String(commessaId));
    }
    const url = `/settings/regenerate-properties${params.toString() ? `?${params.toString()}` : ""}`;
    return apiFetch(url, {
      method: "POST",
    });
  },

  async normalizeImprese(commessaId?: number): Promise<{
    message: string;
    total: number;
    updated: number;
    errors: number;
  }> {
    const params = new URLSearchParams();
    if (commessaId !== undefined) {
      params.set("commessa_id", String(commessaId));
    }
    const url = `/settings/normalize-imprese${params.toString() ? `?${params.toString()}` : ""}`;
    return apiFetch(url, {
      method: "POST",
    });
  },

  async getCommessaPriceCatalog(
    commessaId: number | string,
    options?: { usedOnly?: boolean },
  ): Promise<ApiPriceListItem[]> {
    const params = new URLSearchParams();
    if (options?.usedOnly) {
      params.set("used_only", "true");
    }
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<ApiPriceListItem[]>(`/commesse/${commessaId}/price-catalog${suffix}`);
  },

  async getGlobalPriceCatalog(options?: {
    search?: string;
    commessaId?: number | string | null;
    businessUnit?: string | null;
  }): Promise<ApiPriceListItem[]> {
    const params = new URLSearchParams();
    if (options?.search) {
      params.set("search", options.search);
    }
    if (options?.commessaId !== undefined && options?.commessaId !== null) {
      params.set("commessa_id", String(options.commessaId));
    }
    if (options?.businessUnit) {
      params.set("business_unit", options.businessUnit);
    }
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return apiFetch<ApiPriceListItem[]>(`/commesse/price-catalog${suffix}`);
  },

  async semanticPriceCatalogSearch(params: {
    query: string;
    commessaId?: number | string;
    topK?: number;
    minScore?: number;
  }): Promise<ApiPriceListItemSearchResult[]> {
    const searchParams = new URLSearchParams();
    searchParams.set("query", params.query);
    if (params.commessaId !== undefined && params.commessaId !== null) {
      searchParams.set("commessa_id", String(params.commessaId));
    }
    if (params.topK !== undefined) {
      searchParams.set("top_k", String(params.topK));
    }
    if (params.minScore !== undefined) {
      searchParams.set("min_score", String(params.minScore));
    }
    const suffix = searchParams.toString();
    return apiFetch<ApiPriceListItemSearchResult[]>(
      `/commesse/price-catalog/semantic-search?${suffix}`,
    );
  },

  async getPriceCatalogSummary(): Promise<ApiPriceCatalogSummary> {
    return apiFetch<ApiPriceCatalogSummary>(`/commesse/price-catalog/summary`);
  },

  async updateManualOfferPrice(
    commessaId: number | string,
    payload: {
      price_list_item_id: number;
      computo_id: number;
      prezzo_unitario: number;
      quantita?: number | null;
    },
  ): Promise<ApiManualPriceUpdateResponse> {
    return apiFetch<ApiManualPriceUpdateResponse>(
      `/commesse/${commessaId}/offers/manual-price`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  },

  async login(payload: { email: string; password: string }): Promise<ApiAuthResponse> {
    return apiFetch<ApiAuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async register(payload: {
    email: string;
    password: string;
    full_name?: string | null;
  }): Promise<ApiUser> {
    return apiFetch<ApiUser>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async getCurrentUser(): Promise<ApiUser> {
    return apiFetch<ApiUser>("/me");
  },

  async getProfile(): Promise<ApiUserProfile> {
    return apiFetch<ApiUserProfile>("/profile");
  },

  async updateProfile(payload: Partial<ApiUserProfile>): Promise<ApiUserProfile> {
    return apiFetch<ApiUserProfile>("/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  async logout(): Promise<void> {
    await apiFetch<void>("/auth/logout", { method: "POST" });
  },

  // Backward compatibility aliases
  async getConfronto(commessaId: number | string): Promise<ApiConfrontoOfferte> {
    return this.getCommessaConfronto(commessaId);
  },

  async getAnalisi(
    commessaId: number | string,
    params?: { round_number?: number | null; impresa?: string | null },
  ): Promise<ApiAnalisiCommessa> {
    return this.getCommessaAnalisi(commessaId, params);
  },

  async getAnalisiWbs6Detail(
    commessaId: number | string,
    wbs6Code: string,
    params?: { round_number?: number | null; impresa?: string | null },
  ): Promise<ApiAnalisiWBS6Trend> {
    return this.getCommessaAnalisiWbs6(commessaId, wbs6Code, params);
  },

  async getWbsTree(commessaId: number | string): Promise<ApiCommessaWbs> {
    return this.getCommessaWbsStructure(commessaId);
  },

  async getPropertySchemas(): Promise<PropertySchemaResponse> {
    if (propertySchemasStaticOnly || propertySchemasFallbackPreferred) {
      return fetchPropertySchemasStatic();
    }
    try {
      return await apiFetch<PropertySchemaResponse>("/settings/property-schemas");
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const is404 = message.includes("404");
      if (!is404) {
        throw error;
      }
      propertySchemasFallbackPreferred = true;
      return fetchPropertySchemasStatic();
    }
  },

  async extractProperties(payload: PropertyExtractionPayload): Promise<PropertyExtractionResult> {
    const allowFallback = !propertyExtractionNoFallback;

    if (propertyExtractionStaticOnly || (allowFallback && propertyExtractionFallbackPreferred)) {
      return buildExtractionFallback(payload);
    }
    try {
      return await apiFetch<PropertyExtractionResult>("/settings/extract-properties", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const is404 = message.includes("404");
      if (is404 && apiBaseWithoutPrefix !== apiBaseNoTrailing) {
        try {
          const altUrl = `${apiBaseWithoutPrefix}/settings/extract-properties`;
          return await tryExtractAtUrl(altUrl, payload);
        } catch (altError) {
          const altMessage = altError instanceof Error ? altError.message : String(altError);
          if (!altMessage.includes("404")) {
            throw altError;
          }
        }
      }
      if (!is404) {
        throw error;
      }
      if (!allowFallback) {
        throw error;
      }
      propertyExtractionFallbackPreferred = true;
      return buildExtractionFallback(payload);
    }
  },

  // Overload for semanticSearchPriceCatalog to accept simple parameters
  async semanticSearchPriceCatalog(
    queryOrParams: string | { query: string; commessaId?: number | string; topK?: number; minScore?: number },
    threshold?: number
  ): Promise<ApiPriceListItemSearchResult[]> {
    // If first param is string, use simple signature
    if (typeof queryOrParams === 'string') {
      return this.semanticPriceCatalogSearch({
        query: queryOrParams,
        minScore: threshold,
      });
    }
    // Otherwise use object signature
    return this.semanticPriceCatalogSearch(queryOrParams);
  },
};

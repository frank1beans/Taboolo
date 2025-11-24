import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api } from "@/lib/api-client";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ColDef, ColGroupDef } from "ag-grid-community";
import { DataTable, type ColumnAggregation } from "@/components/DataTable";
import { WBSFilterPanel } from "@/components/WBSFilterPanel";
import { TablePage, type TableStat, type ActiveFilter } from "@/components/ui/table-page";
import { ToggleFilter } from "@/components/ui/table-filters";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import {
  PanelRight,
  AlertTriangle,
  Sparkles,
} from "lucide-react";
import {
  formatCurrency,
  getImpresaColor,
  createImpresaCellStyle,
  truncateMiddle,
  type ExcelExportColumn,
} from "@/lib/grid-utils";
import { getItemExtractedProperties } from "@/lib/property-utils";
import type {
  ApiPriceListItem,
  FrontendWbsNode,
  PropertyCategorySchema,
  PropertyExtractionPayload,
  PropertyExtractionResult,
} from "@/types/api";
import { useTheme } from "next-themes";
import { useCommessaContext } from "@/hooks/useCommessaContext";
import { useToast } from "@/hooks/use-toast";
import { usePropertySchemas } from "@/hooks/queries";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const getProjectPriceValue = (item: ApiPriceListItem): number => {
  if (typeof item.project_price === "number") {
    return item.project_price;
  }
  const priceLists = item.price_lists;
  if (!priceLists) {
    return 0;
  }
  for (const key of ["prezzi_base", "base"]) {
    const value = priceLists[key];
    if (typeof value === "number" && !Number.isNaN(value)) {
      return value;
    }
  }
  const firstValue = Object.values(priceLists).find(
    (value): value is number => typeof value === "number" && !Number.isNaN(value),
  );
  return firstValue ?? 0;
};

const WBS_CATEGORY_MAP: Record<string, string> = {
  "11": "controsoffitti",
  "10": "opere_di_pavimentazione",
  "9": "opere_di_rivestimento",
  "12": "opere_da_cartongessista",
  "16": "opere_da_serramentista",
  "18": "opere_da_falegname",
  "25": "apparecchi_sanitari_accessori",
};

type ManualMissingItem = {
  price_list_item_id: number | null;
  item_code?: string | null;
  item_description?: string | null;
  note?: string | null;
};

type ManualPriceContext = {
  computoId: number;
  label: string;
  offerKey: string;
  missingItems: ManualMissingItem[];
  impresaLabel: string | null;
  roundNumber: number | null;
};

type OfferColumnMeta = {
  key: string;
  label: string;
  roundLabel: string;
  computoId: number;
  roundNumber: number | null;
  impresaLabel: string | null;
};

const buildOfferKey = (impresa: string | null, roundNumber: number | null) => {
  const normalizedLabel = (impresa?.trim() ?? "") || "Offerta";
  return roundNumber == null ? normalizedLabel : `${normalizedLabel} (Round ${roundNumber})`;
};

const formatQuantityValue = (value: number) =>
  value.toLocaleString("it-IT", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 3,
  });

const renderQuantityValue = (value: number | null | undefined) =>
  value != null && !Number.isNaN(Number(value))
    ? formatQuantityValue(Number(value))
    : "-";

const parsePriceInput = (input: unknown): number | null => {
  if (input == null) return null;
  if (typeof input === "number") {
    return Number.isFinite(input) ? input : null;
  }

  const raw = String(input).trim();
  if (!raw) return null;

  let sanitized = raw.replace(/\s/g, "").replace(/[€]/g, "");
  sanitized = sanitized.replace(/[^0-9.,-]/g, "");
  if (!sanitized) return null;

  const commaIndex = sanitized.lastIndexOf(",");
  const dotIndex = sanitized.lastIndexOf(".");

  if (commaIndex !== -1 && dotIndex !== -1) {
    if (commaIndex > dotIndex) {
      sanitized = sanitized.replace(/\./g, "");
      sanitized = sanitized.replace(",", ".");
    } else {
      sanitized = sanitized.replace(/,/g, "");
    }
  } else if (commaIndex !== -1) {
    sanitized = sanitized.replace(/\./g, "");
    sanitized = sanitized.replace(",", ".");
  } else {
    sanitized = sanitized.replace(/,/g, "");
  }

  const parsed = Number(sanitized);
  return Number.isFinite(parsed) ? parsed : null;
};

export default function ElencoPrezziNew() {
  const { id: routeCommessaId } = useParams();
  const { commessa, refetchCommessa } = useCommessaContext();
  const commessaId = routeCommessaId ?? (commessa ? String(commessa.id) : "");
  const { theme } = useTheme();
  const isDarkMode = theme === "dark";
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [manualDialogItem, setManualDialogItem] = useState<ManualMissingItem | null>(null);
  const [manualPriceValue, setManualPriceValue] = useState<string>("");
  const [manualDialogContextId, setManualDialogContextId] = useState<number | null>(null);
  const [activeManualContextId, setActiveManualContextId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"all" | "missing">("all");
  const [selectedRows, setSelectedRows] = useState<ApiPriceListItem[]>([]);
  const [labOpen, setLabOpen] = useState(false);
  const [labText, setLabText] = useState("");
  const [labCategory, setLabCategory] = useState<string | null>(null);
  const [labEngine, setLabEngine] = useState<"llm" | "rules">("llm");
  const [lastResult, setLastResult] = useState<PropertyExtractionResult | null>(null);
  const [resultSource, setResultSource] = useState<"precalculated" | "manual" | null>(null);
  const [propertyPrefs, setPropertyPrefs] = useState<Record<string, string[]>>(() => {
    if (typeof window === "undefined") return {};
    try {
      const raw = window.localStorage.getItem("property-lab-prefs");
      return raw ? (JSON.parse(raw) as Record<string, string[]>) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem("property-lab-prefs", JSON.stringify(propertyPrefs));
    } catch {
      // ignora
    }
  }, [propertyPrefs]);

  const { data: priceCatalog, isLoading: catalogLoading } = useQuery({
    queryKey: ["price-catalog", commessaId],
    queryFn: () => api.getCommessaPriceCatalog(commessaId!),
    enabled: !!commessaId,
  });

  const { data: propertySchemas } = usePropertySchemas();

  const isLoading = !commessa || catalogLoading;

  const offerKeyMetadata = useMemo(() => {
    const map = new Map<string, OfferColumnMeta>();
    if (!commessa?.computi) {
      return map;
    }
    commessa.computi
      .filter((computo) => computo.tipo === "ritorno")
      .forEach((computo) => {
        const key = buildOfferKey(computo.impresa ?? null, computo.round_number ?? null);
        const labelBase = (computo.impresa?.trim() ?? "") || "Offerta";
        map.set(key, {
          key,
          label: labelBase,
          roundLabel: computo.round_number != null ? `Round ${computo.round_number}` : "",
          computoId: computo.id,
          roundNumber: computo.round_number ?? null,
          impresaLabel: computo.impresa ?? null,
        });
      });
    return map;
  }, [commessa?.computi]);

  const computoIdToOfferKey = useMemo(() => {
    const map = new Map<number, string>();
    offerKeyMetadata.forEach((meta, key) => {
      map.set(meta.computoId, key);
    });
    return map;
  }, [offerKeyMetadata]);

  const enrichedData = useMemo<ApiPriceListItem[]>(() => {
    if (!priceCatalog) return [];
    return priceCatalog.map((item) => {
      const offerEntries = { ...(item.offer_prices ?? {}) } as NonNullable<
        ApiPriceListItem["offer_prices"]
      >;
      offerKeyMetadata.forEach((meta, key) => {
        if (!offerEntries[key]) {
          offerEntries[key] = {
            price: null,
            quantity: null,
            round_number: meta.roundNumber ?? undefined,
            computo_id: meta.computoId,
          };
        } else {
          if (offerEntries[key].computo_id == null) {
            offerEntries[key].computo_id = meta.computoId;
          }
          if (offerEntries[key].round_number == null && meta.roundNumber != null) {
            offerEntries[key].round_number = meta.roundNumber;
          }
        }
      });
      return {
        ...item,
        offer_prices: offerEntries,
      };
    });
  }, [priceCatalog, offerKeyMetadata]);

  const priceCatalogMap = useMemo(() => {
    const map = new Map<number, ApiPriceListItem>();
    enrichedData.forEach((item) => map.set(item.id, item));
    return map;
  }, [enrichedData]);

  const propertyCategories = propertySchemas?.categories ?? [];
  const selectedRow = selectedRows[0] ?? null;
  const wbsKey =
    selectedRow?.wbs6_code ??
    (selectedRow as any)?.wbs_code ??
    selectedRow?.wbs7_code ??
    "default";
  const precomputedExtraction = useMemo(
    () => getItemExtractedProperties(selectedRow),
    [selectedRow],
  );

  const guessCategoryFromRow = useCallback(
    (row: ApiPriceListItem) => {
      const code = (row.wbs6_code ?? (row as any)?.wbs_code ?? "").toString();
      const prefix = code.split(".")[0];
      if (prefix && WBS_CATEGORY_MAP[prefix]) {
        return WBS_CATEGORY_MAP[prefix];
      }
      return null;
    },
    [],
  );

  const currentCategory = useMemo<PropertyCategorySchema | null>(() => {
    if (!propertyCategories.length) return null;
    if (labCategory) {
      const found = propertyCategories.find((cat) => cat.id === labCategory);
      if (found) return found;
    }
    return propertyCategories[0] ?? null;
  }, [labCategory, propertyCategories]);

  const currentCategoryProperties = currentCategory?.properties ?? [];

  const selectedPropertyIds = useMemo(() => {
    if (!currentCategory) return [];
    const fromPrefs = propertyPrefs[wbsKey];
    if (fromPrefs && fromPrefs.length > 0) {
      return fromPrefs;
    }
    if (currentCategory.required?.length) {
      return currentCategory.required;
    }
    return currentCategory.properties.map((p) => p.id);
  }, [currentCategory, propertyPrefs, wbsKey]);

  useEffect(() => {
    if (!selectedRow || !propertyCategories.length) return;
    const guessed = guessCategoryFromRow(selectedRow);
    const fallbackCategory = guessed || propertyCategories[0]?.id || null;
    setLabCategory((prev) => prev ?? fallbackCategory);
    const defaults =
      currentCategory?.required?.length
        ? currentCategory.required
        : currentCategoryProperties.map((p) => p.id);
    if (defaults.length > 0 && !propertyPrefs[wbsKey]) {
      setPropertyPrefs((prev) => ({ ...prev, [wbsKey]: defaults }));
    }
  }, [
    currentCategory,
    currentCategoryProperties,
    guessCategoryFromRow,
    propertyCategories,
    propertyPrefs,
    selectedRow,
    wbsKey,
  ]);

  useEffect(() => {
    if (!selectedRow) {
      setLastResult(null);
      setResultSource(null);
      return;
    }
    setLabText(selectedRow.item_description ?? (selectedRow as any).description ?? "");
    setLastResult(precomputedExtraction);
    setResultSource(precomputedExtraction ? "precalculated" : null);
  }, [precomputedExtraction, selectedRow]);

  const manualPriceContexts = useMemo<ManualPriceContext[]>(() => {
    if (!commessa?.computi) return [];
    const normalize = (value?: string | null) => (value ? value.trim().toLowerCase() : "");
    const codeIndex = new Map<string, number>();
    const descriptionIndex = new Map<string, { id: number; count: number }>();
    (priceCatalog ?? []).forEach((item) => {
      const codeKey = normalize(item.item_code);
      if (codeKey && !codeIndex.has(codeKey)) {
        codeIndex.set(codeKey, item.id);
      }
      const descKey = normalize(item.item_description);
      if (descKey) {
        const entry = descriptionIndex.get(descKey);
        if (entry) {
          entry.count += 1;
        } else {
          descriptionIndex.set(descKey, { id: item.id, count: 1 });
        }
      }
    });

    const resolveItemId = (entry: any): number | null => {
      if (typeof entry?.price_list_item_id === "number") {
        return entry.price_list_item_id;
      }
      const codeCandidate = normalize(entry?.item_code ?? entry?.itemCode);
      if (codeCandidate && codeIndex.has(codeCandidate)) {
        return codeIndex.get(codeCandidate)!;
      }
      const descCandidate = normalize(entry?.item_description ?? entry?.itemDescription);
      if (descCandidate) {
        const meta = descriptionIndex.get(descCandidate);
        if (meta && meta.count === 1) {
          return meta.id;
        }
      }
      return null;
    };

    const normalizeEntry = (entry: any): ManualMissingItem => {
      const resolvedId = resolveItemId(entry);
      const note = resolvedId
        ? null
        : entry?.item_code
          ? "Voce non trovata nel listino importato. Verifica l'allineamento dell'elenco prezzi."
          : "Descrizione non riconosciuta nel listino. Reimporta l'XML per aggiornare i codici.";
      return {
        price_list_item_id: resolvedId,
        item_code: entry?.item_code ?? entry?.itemCode ?? null,
        item_description: entry?.item_description ?? entry?.itemDescription ?? null,
        note,
      };
    };

    return commessa.computi
      .filter((computo) => computo.tipo === "ritorno")
      .map((computo) => {
        const report = computo.matching_report;
        const missingEntries =
          report?.mode === "lc"
            ? ((report?.missing_price_items as Record<string, unknown>[] | undefined) ?? [])
            : [];
        const normalizedMissing = missingEntries.map((entry) => normalizeEntry(entry));
        const labelBase = (computo.impresa ?? "Impresa").trim() || "Impresa";
        const label =
          computo.round_number != null ? `${labelBase} · Round ${computo.round_number}` : labelBase;
        return {
          computoId: computo.id,
          label,
          offerKey: buildOfferKey(computo.impresa ?? null, computo.round_number ?? null),
          missingItems: normalizedMissing,
          impresaLabel: computo.impresa ?? null,
          roundNumber: computo.round_number ?? null,
        };
      })
      .filter((ctx) => ctx.missingItems.length > 0);
  }, [commessa?.computi, priceCatalog]);

  useEffect(() => {
    if (manualPriceContexts.length === 0) {
      setActiveManualContextId(null);
      return;
    }
    if (
      activeManualContextId === null ||
      !manualPriceContexts.some((ctx) => ctx.computoId === activeManualContextId)
    ) {
      setActiveManualContextId(manualPriceContexts[0].computoId);
    }
  }, [manualPriceContexts, activeManualContextId]);

  const activeManualContext =
    manualPriceContexts.find((ctx) => ctx.computoId === activeManualContextId) ?? null;

  // Set of items with missing prices for the active offer
  const activeMissingSet = useMemo(() => {
    if (!activeManualContext) return new Set<number>();
    const set = new Set<number>();
    activeManualContext.missingItems.forEach((item) => {
      if (typeof item.price_list_item_id === "number") {
        set.add(item.price_list_item_id);
      }
    });
    return set;
  }, [activeManualContext]);

  // Set of ALL items with missing prices across all offers
  const allMissingPricesSet = useMemo(() => {
    const set = new Set<number>();
    manualPriceContexts.forEach((ctx) => {
      ctx.missingItems.forEach((item) => {
        if (typeof item.price_list_item_id === "number") {
          set.add(item.price_list_item_id);
        }
      });
    });
    return set;
  }, [manualPriceContexts]);

  const manualPriceMutation = useMutation({
    mutationFn: (payload: {
      price_list_item_id: number;
      computo_id: number;
      prezzo_unitario: number;
    }) => {
      if (!commessaId) {
        throw new Error("Commessa non valida per l'aggiornamento manuale");
      }
      return api.updateManualOfferPrice(commessaId, payload);
    },
    onSuccess: async (_data, variables) => {
      if (commessaId) {
        queryClient.setQueryData<ApiPriceListItem[] | undefined>(
          ["price-catalog", commessaId],
          (current) => {
            if (!current) {
              return current;
            }
            const offerKey = computoIdToOfferKey.get(variables.computo_id);
            if (!offerKey) {
              return current;
            }
            const offerMeta = offerKeyMetadata.get(offerKey);
            let updated = false;
            const nextCatalog = current.map((item) => {
              if (item.id !== variables.price_list_item_id) {
                return item;
              }
              const existingOffers = { ...(item.offer_prices ?? {}) };
              const currentEntry = existingOffers[offerKey];
              const nextEntry = {
                ...(currentEntry ?? {}),
                price: variables.prezzo_unitario,
                quantity: currentEntry?.quantity ?? null,
                round_number:
                  currentEntry?.round_number ??
                  offerMeta?.roundNumber ??
                  undefined,
                computo_id:
                  currentEntry?.computo_id ??
                  offerMeta?.computoId ??
                  variables.computo_id,
              };

              const isSamePrice =
                currentEntry?.price === nextEntry.price &&
                currentEntry?.computo_id === nextEntry.computo_id;
              if (isSamePrice) {
                return item;
              }

              updated = true;
              return {
                ...item,
                offer_prices: {
                  ...existingOffers,
                  [offerKey]: nextEntry,
                },
              };
            });
            return updated ? nextCatalog : current;
          },
        );
      }

      const currentContextMissingCount = activeManualContext?.missingItems.length || 0;
      const wasLastItemForOffer = currentContextMissingCount === 1;
      const offerLabel = activeManualContext?.label || "Offerta";

      await refetchCommessa();

      if (wasLastItemForOffer) {
        toast({
          title: "Offerta completata",
          description: `Tutti i prezzi per "${offerLabel}" sono stati inseriti correttamente.`,
          variant: "default",
        });
      } else {
        const remainingAfterThis = currentContextMissingCount - 1;
        toast({
          title: "Prezzo salvato",
          description: `Aggiornato correttamente. Rimangono ${remainingAfterThis} ${remainingAfterThis === 1 ? "prezzo" : "prezzi"} da completare per questa offerta.`,
        });
      }

      setManualDialogItem(null);
      setManualDialogContextId(null);
      setManualPriceValue("");
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Impossibile salvare il prezzo. Riprova.";
      toast({
        title: "Aggiornamento non riuscito",
        description: message,
        variant: "destructive",
      });
    },
  });

  const extractionMutation = useMutation({
    mutationFn: (payload: PropertyExtractionPayload) => api.extractProperties(payload),
    onSuccess: (data) => {
      setLastResult(data);
      setResultSource("manual");
      toast({
        title: "Proprietà estratte",
        description: `Categoria ${data.category_id}`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Errore durante l'estrazione",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  const openManualDialog = (item: ManualMissingItem) => {
    if (!activeManualContext || manualPriceMutation.isPending) return;
    if (item.price_list_item_id == null) {
      toast({
        title: "Voce non riconosciuta",
        description:
          item.note ??
          "La voce non è stata trovata nell'elenco prezzi importato. Reimporta il file XML per allineare i codici.",
        variant: "destructive",
      });
      return;
    }
    setManualDialogItem(item);
    setManualDialogContextId(activeManualContext.computoId);
    setManualPriceValue("");
  };

  const closeManualDialog = () => {
    if (manualPriceMutation.isPending) return;
    setManualDialogItem(null);
    setManualDialogContextId(null);
    setManualPriceValue("");
  };

  const handleManualPriceSubmit = () => {
    if (!manualDialogItem || manualDialogContextId == null) {
      toast({
        title: "Selezione non valida",
        description: "Seleziona una voce da aggiornare.",
        variant: "destructive",
      });
      return;
    }
    if (manualDialogItem.price_list_item_id == null) {
      toast({
        title: "Voce non disponibile",
        description:
          manualDialogItem.note ??
          "La voce selezionata non è collegata al listino. Reimporta il listino per aggiornarla.",
        variant: "destructive",
      });
      return;
    }
    const parsed = parsePriceInput(manualPriceValue);
    if (parsed == null || parsed <= 0) {
      toast({
        title: "Prezzo non valido",
        description: "Inserisci un valore numerico maggiore di zero.",
        variant: "destructive",
      });
      return;
    }
    manualPriceMutation.mutate({
      price_list_item_id: manualDialogItem.price_list_item_id,
      computo_id: manualDialogContextId,
      prezzo_unitario: Number(parsed.toFixed(4)),
    });
  };

  const totalManualMissing = manualPriceContexts.reduce(
    (sum, ctx) => sum + ctx.missingItems.length,
    0,
  );
  const manualFilterActive = Boolean(activeManualContext);

  const contextTotals = useMemo(() => {
    if (!activeManualContext) return null;
    const offerKey = activeManualContext.offerKey;
    let projectTotal = 0;
    let importedTotal = 0;
    enrichedData.forEach((item) => {
      const projectQuantity = Number(item.project_quantity ?? 0);
      if (!Number.isNaN(projectQuantity)) {
        projectTotal += projectQuantity;
      }
      const offerQuantity = item.offer_prices?.[offerKey]?.quantity;
      if (typeof offerQuantity === "number" && !Number.isNaN(offerQuantity)) {
        importedTotal += offerQuantity;
      }
    });
    return {
      project: projectTotal,
      imported: importedTotal,
      delta: importedTotal - projectTotal,
    };
  }, [activeManualContext, enrichedData]);

  const missingTotals = useMemo(() => {
    if (!activeManualContext) return null;
    let projectTotal = 0;
    activeManualContext.missingItems.forEach((item) => {
      if (typeof item.price_list_item_id !== "number") {
        return;
      }
      const catalogEntry = priceCatalogMap.get(item.price_list_item_id);
      if (!catalogEntry) {
        return;
      }
      const projectQuantity = Number(catalogEntry.project_quantity ?? 0);
      if (!Number.isNaN(projectQuantity)) {
        projectTotal += projectQuantity;
      }
    });
    return {
      project: projectTotal,
      imported: 0,
      delta: -projectTotal,
    };
  }, [activeManualContext, priceCatalogMap]);

  // Build WBS tree
  const wbsTree = useMemo<FrontendWbsNode[]>(() => {
    if (!priceCatalog) return [];

    const wbs6Map = new Map<string, FrontendWbsNode>();
    const wbs7Map = new Map<string, FrontendWbsNode>();

    priceCatalog.forEach((item) => {
      const wbs6Code = item.wbs6_code || "SENZA_WBS6";
      const wbs7Code = item.wbs7_code;
      const primaryPrice = getProjectPriceValue(item);

      if (!wbs6Map.has(wbs6Code)) {
        const pathEntry = { level: 6, code: wbs6Code, description: item.wbs6_description || "" };
        wbs6Map.set(wbs6Code, {
          id: `wbs6-${wbs6Code}`,
          level: 6,
          code: wbs6Code,
          description: item.wbs6_description || "",
          importo: 0,
          children: [],
          path: [pathEntry],
        });
      }

      const wbs6Node = wbs6Map.get(wbs6Code)!;
      wbs6Node.importo += primaryPrice;

      if (wbs7Code) {
        const wbs7Key = `${wbs6Code}-${wbs7Code}`;
        if (!wbs7Map.has(wbs7Key)) {
          const path = [
            ...wbs6Node.path,
            { level: 7, code: wbs7Code, description: item.wbs7_description || "" },
          ];
          const wbs7Node: FrontendWbsNode = {
            id: `wbs7-${wbs7Key}`,
            level: 7,
            code: wbs7Code,
            description: item.wbs7_description || "",
            importo: 0,
            children: [],
            path,
          };
          wbs7Map.set(wbs7Key, wbs7Node);
          const parent = wbs6Map.get(wbs6Code);
          if (parent) {
            parent.children.push(wbs7Node);
          }
        }
        const wbs7Node = wbs7Map.get(wbs7Key)!;
        wbs7Node.importo += primaryPrice;
      }
    });

    return Array.from(wbs6Map.values()).sort((a, b) =>
      (a.code || "").localeCompare(b.code || "")
    );
  }, [priceCatalog]);

  // Filter data based on selected WBS node
  const filteredData = useMemo(() => {
    let dataset = enrichedData;

    // Filter by WBS node selection
    if (selectedNodeId) {
      const selectedNode = wbsTree.find((n) => n.id === selectedNodeId);
      if (!selectedNode) {
        for (const wbs6 of wbsTree) {
          const wbs7 = wbs6.children.find((c) => c.id === selectedNodeId);
          if (wbs7) {
            dataset = dataset.filter(
              (item) => item.wbs6_code === wbs6.code && item.wbs7_code === wbs7.code,
            );
            break;
          }
        }
      } else {
        dataset = dataset.filter((item) => item.wbs6_code === selectedNode.code);
      }
    }

    // Filter by tab: show only items with missing prices if "missing" tab is active
    if (activeTab === "missing" && allMissingPricesSet.size > 0) {
      dataset = dataset.filter((item) => allMissingPricesSet.has(item.id));
    }

    return dataset;
  }, [enrichedData, selectedNodeId, wbsTree, activeTab, allMissingPricesSet]);


  const imprese = useMemo(() => Array.from(offerKeyMetadata.values()), [offerKeyMetadata]);

  // Build column definitions
  const columnDefs = useMemo<(ColDef<ApiPriceListItem> | ColGroupDef<ApiPriceListItem>)[]>(() => {
    const columns: (ColDef<ApiPriceListItem> | ColGroupDef<ApiPriceListItem>)[] = [
      // Indicator column (no checkbox selection to avoid AG Grid deprecations)
      {
        width: 50,
        pinned: "left",
        cellRenderer: (params: any) => {
          const hasMissingPrice = allMissingPricesSet.has(params.data?.id);
          if (!hasMissingPrice) return null;
          return (
            <div className="flex items-center justify-center h-full" title="Prezzi mancanti">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            </div>
          );
        },
        cellClass: "flex items-center justify-center",
      },
      {
        field: "item_code",
        headerName: "Codice",
        width: 150,
        pinned: "left",
        cellClass: "font-mono text-xs font-semibold",
        headerClass: "font-semibold",
        sortable: true,
        filter: true,
      },
      {
        field: "item_description",
        headerName: "Descrizione",
        width: 420,
        cellClass: "text-sm",
        headerClass: "font-semibold",
        sortable: true,
        filter: true,
        valueFormatter: (params) => truncateMiddle(params.value, 60, 60),
        tooltipValueGetter: (params) => params.value || "",
      },
      {
        field: "unit_label",
        headerName: "U.M.",
        width: 80,
        cellClass: "text-center font-mono text-xs",
        headerClass: "text-center font-semibold",
      },
      {
        field: "wbs6_code",
        headerName: "WBS6",
        width: 100,
        cellClass: "font-mono text-xs",
        sortable: true,
        filter: true,
      },
      {
        field: "wbs7_code",
        headerName: "WBS7",
        width: 110,
        cellClass: "font-mono text-xs",
        sortable: true,
        filter: true,
      },
    ];

    columns.push({
      headerName: "Prezzo progetto",
      headerClass: "font-bold text-base bg-blue-100 dark:bg-blue-900/40 text-blue-900 dark:text-blue-100",
      children: [
        {
          field: "project_price",
          headerName: "Prezzo base",
          width: 160,
          type: "numericColumn",
          cellClass: "font-mono text-sm font-semibold text-blue-700 dark:text-blue-200",
          headerClass: "text-right font-bold",
          valueGetter: (params) => params.data?.project_price ?? getProjectPriceValue(params.data),
          valueFormatter: (params) =>
            params.value != null ? formatCurrency(params.value) : "-",
        },
      ],
    });

    if (imprese.length > 0) {
      const impresaColumns: ColDef<ApiPriceListItem>[] = imprese.map((impresa, idx) => {
        const colorTheme = getImpresaColor(idx);
        return {
          field: `offer_prices.${impresa.key}`,
          headerName: `${impresa.label}\n${impresa.roundLabel}`,
          width: 180,
          type: "numericColumn",
          editable: true,
          valueParser: (params) => parsePriceInput(params.newValue),
          valueSetter: (params) => {
            if (!params.data) return false;
            if (!params.data.offer_prices) {
              params.data.offer_prices = {};
            }
            let entry = params.data.offer_prices[impresa.key];
            if (!entry) {
              entry = {
                price: null,
                quantity: null,
                round_number: impresa.roundNumber ?? undefined,
                computo_id: impresa.computoId,
              };
              params.data.offer_prices[impresa.key] = entry;
            }
            entry.price = parsePriceInput(params.newValue);
            if (entry.computo_id == null && impresa.computoId != null) {
              entry.computo_id = impresa.computoId;
            }
            return true;
          },
          cellClass: "font-mono text-sm font-semibold",
          headerClass: "text-center font-semibold",
          valueGetter: (params) => params.data?.offer_prices?.[impresa.key]?.price,
          valueFormatter: (params) =>
            params.value != null ? formatCurrency(params.value) : "-",
          cellStyle: (params) => {
            const baseStyle = createImpresaCellStyle(colorTheme, isDarkMode);
            const hasMissingPrice = params.value == null && allMissingPricesSet.has(params.data?.id);

            if (hasMissingPrice) {
              return {
                ...baseStyle,
                border: "2px solid #f59e0b",
                backgroundColor: "#fffbeb",
              };
            }

            return baseStyle;
          },
          cellRenderer: (params: any) => {
            const value = params.value;
            const hasMissingPrice = value == null && allMissingPricesSet.has(params.data?.id);

            if (hasMissingPrice) {
              return (
                <div className="flex items-center justify-between h-full px-2">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-600 flex-shrink-0" />
                  <span className="text-amber-700 font-semibold text-xs ml-1">Inserisci</span>
                </div>
              );
            }

            return value != null ? formatCurrency(value) : "-";
          },
        };
      });

      columns.push({
        headerName: "Offerte Ricevute",
        headerClass: "font-semibold bg-amber-50 dark:bg-amber-950",
        children: impresaColumns,
      });
    }

    return columns;
  }, [imprese, isDarkMode, allMissingPricesSet]);

  // Export columns configuration
  const exportColumns = useMemo<ExcelExportColumn[]>(() => {
    const cols: ExcelExportColumn[] = [
      { header: "Codice", field: "item_code" },
      { header: "Descrizione", field: "item_description" },
      { header: "U.M.", field: "unit_label" },
      { header: "WBS6", field: "wbs6_code" },
      { header: "WBS7", field: "wbs7_code" },
      {
        header: "Prezzo base",
        field: "project_price",
        valueFormatter: (row: any) =>
          row?.project_price != null ? formatCurrency(row.project_price) : "-",
      },
      {
        header: "Quantità progetto",
        field: "project_quantity",
        valueFormatter: (row: any) =>
          row?.project_quantity != null
            ? Number(row.project_quantity).toLocaleString("it-IT")
            : "-",
      },
    ];

    imprese.forEach(({ key, label, roundLabel }) => {
      cols.push({
        header: `${label} (${roundLabel})`,
        field: `offer_prices_${key}`,
        valueFormatter: (row: any) => {
          const price = row?.offer_prices?.[key]?.price;
          return price != null ? formatCurrency(price) : "-";
        },
      });
    });

    return cols;
  }, [imprese]);

  // Statistics
  const stats = useMemo(() => {
    const totalItems = filteredData.length;
    const wbs6Count = new Set(filteredData.map((item) => item.wbs6_code)).size;
    const wbs7Count = new Set(
      filteredData.filter((item) => item.wbs7_code).map((item) => item.wbs7_code)
    ).size;

    return { totalItems, wbs6Count, wbs7Count };
  }, [filteredData]);

  const totalProjectPrice = useMemo(() => {
    return filteredData.reduce((sum, item) => {
      if (typeof item.project_price === "number") {
        return sum + item.project_price;
      }
      return sum + getProjectPriceValue(item);
    }, 0);
  }, [filteredData]);

  const offerRoundCount = useMemo(() => {
    const set = new Set<number>();
    enrichedData.forEach((item) => {
      const offers = item.offer_prices;
      if (!offers) return;
      Object.values(offers).forEach((entry) => {
        if (entry?.round_number != null) {
          set.add(entry.round_number);
        }
      });
    });
    return set.size;
  }, [enrichedData]);

  const handleToggleProperty = (propId: string, checked: boolean) => {
    if (!selectedRow) return;
    const requiredSet = new Set(currentCategory?.required ?? []);
    if (requiredSet.has(propId) && !checked) {
      return;
    }
    setPropertyPrefs((prev) => {
      const next = new Set(prev[wbsKey] ?? []);
      if (checked) {
        next.add(propId);
      } else {
        next.delete(propId);
      }
      return { ...prev, [wbsKey]: Array.from(next) };
    });
  };

  const handleOpenLabPanel = () => {
    if (!selectedRow) {
      toast({
        title: "Seleziona una voce",
        description: "Scegli una voce dell'elenco prezzi per avviare l'estrazione.",
      });
      return;
    }
    setLabOpen(true);
  };

  const handleRunExtraction = () => {
    if (!selectedRow || !currentCategory) {
      toast({
        title: "Config incompleta",
        description: "Seleziona una voce e una categoria WBS/schema prima di estrarre.",
        variant: "destructive",
      });
      return;
    }
    const payload: PropertyExtractionPayload = {
      text:
        labText ||
        selectedRow.item_description ||
        (selectedRow as any).description ||
        "",
      category_id: currentCategory.id,
      wbs6_code: selectedRow.wbs6_code ?? (selectedRow as any)?.wbs_code,
      wbs6_description: selectedRow.wbs6_description ?? (selectedRow as any)?.wbs_description,
      properties: selectedPropertyIds,
      engine: labEngine,
    };
    extractionMutation.mutate(payload);
  };

  const renderExtractionResult = () => {
    if (extractionMutation.isPending) {
      return <Skeleton className="h-24 w-full rounded-md" />;
    }
    if (!lastResult) {
      return (
        <p className="text-sm text-muted-foreground">
          Avvia un'estrazione per vedere i risultati LLM / regole.
        </p>
      );
    }
    const entries = Object.entries(lastResult.properties);
    if (entries.length === 0) {
      return <p className="text-sm text-muted-foreground">Nessuna proprietà trovata nel testo.</p>;
    }
    return (
      <div className="space-y-2">
        {entries.map(([propId, value]) => {
          const isMissing = lastResult.missing_required?.includes(propId);
          return (
            <div key={propId} className="rounded-md border border-border/60 p-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="font-semibold">{propId.replace(/_/g, " ")}</span>
                {isMissing && <Badge variant="destructive">Mancante</Badge>}
              </div>
              <div className="text-sm font-medium text-foreground break-words">
                {value === null || value === undefined ? "—" : String(value)}
              </div>
            </div>
          );
        })}
        {lastResult.missing_required?.length ? (
          <Alert>
            <AlertDescription>
              Proprietà obbligatorie non trovate: {lastResult.missing_required.join(", ")}
            </AlertDescription>
          </Alert>
        ) : null}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex-1 space-y-6 bg-muted/30 p-8">
        <Skeleton className="h-10 w-64 rounded-2xl" />
        <div className="grid gap-4 md:grid-cols-4">
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
          <Skeleton className="h-24 rounded-2xl" />
        </div>
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (!commessa) {
    return (
      <div className="flex-1 bg-muted/30 p-8">
        <Alert variant="destructive" className="rounded-2xl border border-border/60">
          <AlertDescription>Commessa non trovata</AlertDescription>
        </Alert>
      </div>
    );
  }

  // Handler for inline price editing
  const handleCellValueChanged = (event: any) => {
    const { data, colDef, newValue } = event;

    // Parse the offer key from the field name (e.g., "offer_prices.Impresa A (Round 1)")
    const field = colDef.field as string;
    if (!field?.startsWith("offer_prices.")) return;

    const offerKey = field.replace("offer_prices.", "");
    const offerData = data?.offer_prices?.[offerKey];
    const offerMeta = offerKeyMetadata.get(offerKey);

    const computoId = offerData?.computo_id ?? offerMeta?.computoId;

    if (!computoId) {
      toast({
        title: "Errore",
        description: "Impossibile identificare l'offerta da modificare",
        variant: "destructive",
      });
      return;
    }

    // Parse the new price value
    const parsedPrice = parsePriceInput(newValue);

    if (parsedPrice == null || Number.isNaN(parsedPrice) || parsedPrice <= 0) {
      toast({
        title: "Valore non valido",
        description: "Inserisci un prezzo valido maggiore di zero",
        variant: "destructive",
      });
      return;
    }

    // Call the mutation to update the price
    manualPriceMutation.mutate({
      price_list_item_id: data.id,
      computo_id: computoId,
      prezzo_unitario: parsedPrice,
    });
  };

  // Build stats for TablePage
  const tableStats: TableStat[] = [
    { label: "voci", value: stats.totalItems },
    { label: "WBS6", value: stats.wbs6Count },
    ...(imprese.length > 0 ? [{ label: "offerte", value: imprese.length }] : []),
    ...(allMissingPricesSet.size > 0
      ? [{ label: "mancanti", value: allMissingPricesSet.size, variant: "warning" as const }]
      : []),
  ];

  // Build active filters
  const activeFiltersArray: ActiveFilter[] = [
    ...(selectedNodeId
      ? [{
          id: "wbs",
          label: "WBS",
          value: selectedNodeId,
          onRemove: () => setSelectedNodeId(null),
        }]
      : []),
  ];

  // Aggregations for footer
  const aggregations: ColumnAggregation[] = [
    {
      field: "project_price",
      type: "sum",
      label: "Totale",
      formatter: (v) => `€${v.toLocaleString("it-IT", { minimumFractionDigits: 2 })}`,
    },
  ];

  return (
    <TablePage
      title="Elenco Prezzi"
      description="Voci computo con prezzi progetto e offerte per round"
      stats={tableStats}
      activeFilters={activeFiltersArray}
      onClearAllFilters={() => setSelectedNodeId(null)}
      filters={
        <ToggleFilter
          options={[
            { value: "all", label: "Tutte" },
            { value: "missing", label: "Mancanti" },
          ]}
          value={activeTab}
          onChange={(v) => setActiveTab(v as "all" | "missing")}
        />
      }
      actions={
        <div className="flex items-center gap-2">
          {wbsTree.length > 0 && (
            <Button
              variant={sidebarOpen ? "secondary" : "outline"}
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="h-8 gap-1.5"
            >
              <PanelRight className="h-4 w-4" />
              WBS
            </Button>
          )}
          <Button
            size="sm"
            variant="default"
            onClick={handleOpenLabPanel}
            className="h-8 gap-1.5"
            disabled={!selectedRow}
          >
            <Sparkles className="h-4 w-4" />
            Lab proprietà
          </Button>
        </div>
      }
      className="h-full min-h-[calc(100vh-96px)]"
    >
      <DataTable<ApiPriceListItem>
        data={filteredData}
        columnDefs={columnDefs}
        height="70vh"
        headerHeight={64}
        enableSearch={true}
        enableExport={true}
        enableColumnToggle={true}
        exportFileName={`elenco-prezzi-${commessa.codice ?? "commessa"}`}
        exportColumns={exportColumns}
        getRowId={(params) => String(params.data.id)}
        onCellValueChanged={handleCellValueChanged}
        aggregations={aggregations}
        showAggregationFooter={true}
        enableRowSelection={true}
        onSelectionChanged={(rows) => setSelectedRows(rows as ApiPriceListItem[])}
        onRowClicked={(row) => setSelectedRows([row])}
      />

      {/* Property Extraction Lab */}
      <Sheet open={labOpen} onOpenChange={setLabOpen}>
        <SheetContent side="right" className="w-[520px] sm:w-[580px] overflow-y-auto">
          <SheetHeader className="pb-4">
            <SheetTitle className="text-base">Laboratorio estrazione proprieta</SheetTitle>
          </SheetHeader>
          <div className="space-y-4 pb-4">
            {selectedRow ? (
              <div className="rounded-lg border border-border/60 bg-muted/30 p-3 space-y-1">
                <div className="text-xs text-muted-foreground">Voce selezionata</div>
                <div className="text-sm font-semibold">{selectedRow.item_code ?? "—"}</div>
                <div className="text-sm text-foreground">{selectedRow.item_description || "Descrizione non disponibile"}</div>
                {selectedRow.wbs6_code && (
                  <div className="text-xs text-muted-foreground">
                    WBS: {selectedRow.wbs6_code} {selectedRow.wbs6_description ? `· ${selectedRow.wbs6_description}` : ""}
                  </div>
                )}
              </div>
            ) : (
              <Alert>
                <AlertDescription>Seleziona una voce della tabella per configurare il laboratorio.</AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 gap-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label>Engine</Label>
                  <Select value={labEngine} onValueChange={(v) => setLabEngine(v as "llm" | "rules")}>
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona engine" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="llm">LLM (Ollama)</SelectItem>
                      <SelectItem value="rules">Regole / parser</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label>Categoria schema</Label>
                  <Select
                    value={currentCategory?.id ?? ""}
                    onValueChange={(value) => setLabCategory(value)}
                    disabled={!propertyCategories.length}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Categoria..." />
                    </SelectTrigger>
                    <SelectContent>
                      {propertyCategories.map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.name ?? cat.id}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-1">
                <Label>Testo da analizzare</Label>
                <Textarea
                  value={labText}
                  onChange={(e) => setLabText(e.target.value)}
                  rows={5}
                  placeholder="Incolla qui la descrizione della voce"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold">Propriet� da estrarre</p>
                    <p className="text-xs text-muted-foreground">Personalizza l'output per questa WBS/categoria.</p>
                  </div>
                  <Badge variant="secondary">
                    {selectedPropertyIds.length} / {currentCategoryProperties.length}
                  </Badge>
                </div>
                <div className="rounded-md border border-border/60 bg-muted/30">
                  <ScrollArea className="h-48">
                    <div className="divide-y divide-border/60">
                      {currentCategoryProperties.length === 0 ? (
                        <div className="p-3 text-sm text-muted-foreground">Caricamento schema...</div>
                      ) : (
                        currentCategoryProperties.map((prop) => {
                          const isChecked = selectedPropertyIds.includes(prop.id);
                          const isRequired = currentCategory?.required?.includes(prop.id);
                          return (
                            <label
                              key={prop.id}
                              className="flex items-start gap-3 p-3 hover:bg-background/60 cursor-pointer"
                              htmlFor={`prop-${prop.id}`}
                            >
                              <Checkbox
                                id={`prop-${prop.id}`}
                                checked={isChecked}
                                disabled={isRequired}
                                onCheckedChange={(v) => handleToggleProperty(prop.id, Boolean(v))}
                              />
                              <div className="space-y-0.5">
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-sm">{prop.title ?? prop.id}</span>
                                  {isRequired && <Badge variant="outline">Obbligatoria</Badge>}
                                  {prop.unit && <Badge variant="secondary">{prop.unit}</Badge>}
                                </div>
                                <div className="text-xs text-muted-foreground">
                                  {prop.type ?? "string"} {prop.enum ? `(enum ${prop.enum.join(", ")})` : ""}
                                </div>
                              </div>
                            </label>
                          );
                        })
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button onClick={handleRunExtraction} disabled={extractionMutation.isPending || !currentCategory || !selectedRow}>
                  {extractionMutation.isPending ? "Estrazione..." : "Estrai proprieta"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setLastResult(null);
                    setResultSource(null);
                  }}
                >
                  Svuota risultato
                </Button>
              </div>

              <div className="rounded-lg border border-border/60 bg-card p-3">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm font-semibold">Risultato</p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {resultSource === "precalculated" && <Badge variant="outline">Calcolato catalogo</Badge>}
                    {resultSource === "manual" && <Badge variant="secondary">Ultima estrazione</Badge>}
                  </div>
                </div>
                {renderExtractionResult()}
              </div>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* WBS Panel as Sheet Overlay */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="right" className="w-[400px] sm:w-[450px] p-0">
          <SheetHeader className="px-4 py-3 border-b">
            <SheetTitle className="text-base">Filtro WBS</SheetTitle>
          </SheetHeader>
          <div className="h-[calc(100%-57px)] overflow-y-auto p-3">
            <WBSFilterPanel
              nodes={wbsTree}
              selectedNodeId={selectedNodeId}
              onNodeSelect={(nodeId) => {
                setSelectedNodeId(nodeId);
              }}
              onClose={() => setSidebarOpen(false)}
              showAmounts={false}
            />
          </div>
        </SheetContent>
      </Sheet>

      <Dialog open={Boolean(manualDialogItem)} onOpenChange={(open) => !open && closeManualDialog()}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Imposta il prezzo offerto</DialogTitle>
            <DialogDescription>
              La voce selezionata verrà aggiornata nel computo{" "}
              <span className="font-semibold">
                {manualPriceContexts.find((ctx) => ctx.computoId === manualDialogContextId)?.label ??
                  activeManualContext?.label ??
                  "selezionato"}
              </span>
              .
            </DialogDescription>
          </DialogHeader>
          {manualDialogItem && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-border/60 bg-muted/30 p-4">
                <p className="text-body font-semibold">
                  {manualDialogItem.item_code ?? "Voce senza codice"}
                </p>
                <p className="text-body-sm text-muted-foreground">
                  {manualDialogItem.item_description ?? "Descrizione non disponibile"}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="manual-price-input">Prezzo unitario offerto</Label>
                <Input
                  id="manual-price-input"
                  type="number"
                  inputMode="decimal"
                  min="0"
                  step="0.01"
                  placeholder="es. 1250.50"
                  value={manualPriceValue}
                  onChange={(event) => setManualPriceValue(event.target.value)}
                  disabled={manualPriceMutation.isPending}
                />
                <p className="text-body-sm text-muted-foreground">
                  Il valore verrà memorizzato con quattro cifre decimali.
                </p>
              </div>
            </div>
          )}
          <DialogFooter className="gap-2 sm:gap-3">
            <Button
              variant="outline"
              onClick={closeManualDialog}
              disabled={manualPriceMutation.isPending}
            >
              Annulla
            </Button>
            <Button onClick={handleManualPriceSubmit} disabled={manualPriceMutation.isPending}>
              {manualPriceMutation.isPending ? "Salvataggio..." : "Salva prezzo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </TablePage>
  );
}

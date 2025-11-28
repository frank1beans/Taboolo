import { useMutation, useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { ColDef } from "ag-grid-community";
import { DataTable } from "@/components/DataTable";
import { WBSFilterPanel } from "@/components/WBSFilterPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { XCircle, Sparkles, Search, X, PanelRight, Filter, Info, Tag } from "lucide-react";
import { formatCurrency, truncateMiddle } from "@/lib/grid-utils";
import { api } from "@/lib/api-client";
import { getItemExtractedProperties } from "@/lib/property-utils";
import { usePropertySchemas } from "@/hooks/queries/usePropertySchemas";
import type {
  ApiPriceListItem,
  ApiPriceListItemSearchResult,
  FrontendWbsNode,
  PropertyCategorySchema,
  PropertyExtractionPayload,
  PropertyExtractionResult,
  PropertySchemaField,
} from "@/types/api";

const DEFAULT_SEMANTIC_THRESHOLD = 0.35;
const WBS_CATEGORY_MAP: Record<string, string> = {
  "11": "controsoffitti",
  "10": "opere_di_pavimentazione",
  "9": "opere_di_rivestimento",
  "12": "opere_da_cartongessista",
  "16": "opere_da_serramentista",
  "18": "opere_da_falegname",
  "25": "apparecchi_sanitari_accessori",
};

type PriceListRow = ApiPriceListItem | ApiPriceListItemSearchResult;

export default function PriceCatalogExplorerNew() {
  const [businessUnitFilter, setBusinessUnitFilter] = useState<string | null>(null);
  const [commessaFilter, setCommessaFilter] = useState<number | null>(null);
  const [semanticQuery, setSemanticQuery] = useState<string>("");
  const [activeSemanticSearch, setActiveSemanticSearch] = useState<string>("");
  const [semanticThreshold, setSemanticThreshold] = useState<number>(DEFAULT_SEMANTIC_THRESHOLD);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [semanticOpen, setSemanticOpen] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedRows, setSelectedRows] = useState<PriceListRow[]>([]);

  const [extractionEngine, setExtractionEngine] = useState<"llm" | "rules">("llm");
  const [labCategoryId, setLabCategoryId] = useState<string | null>(null);
  const [selectedProperties, setSelectedProperties] = useState<string[]>([]);
  const [labText, setLabText] = useState<string>("");
  const [extractionResult, setExtractionResult] = useState<PropertyExtractionResult | null>(null);
  const [extractionSource, setExtractionSource] = useState<"precalculated" | "manual" | null>(null);

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["price-catalog-summary"],
    queryFn: () => api.getPriceCatalogSummary(),
  });

  const { data: catalogItems, isLoading: catalogLoading } = useQuery({
    queryKey: ["price-catalog", businessUnitFilter, commessaFilter],
    queryFn: () =>
      api.getGlobalPriceCatalog({
        businessUnit: businessUnitFilter ?? undefined,
        commessaId: commessaFilter ?? undefined,
      }),
    enabled: !activeSemanticSearch,
  });

  const {
    data: semanticResults,
    isLoading: semanticLoading,
    error: semanticError,
  } = useQuery({
    queryKey: ["price-catalog-semantic", activeSemanticSearch, commessaFilter, semanticThreshold],
    queryFn: () =>
      api.semanticPriceCatalogSearch({
        query: activeSemanticSearch,
        commessaId: commessaFilter ?? undefined,
        topK: 50,
        minScore: semanticThreshold,
      }),
    enabled: !!activeSemanticSearch,
  });

  const { data: propertySchemas } = usePropertySchemas();

  const extractionMutation = useMutation({
    mutationFn: (payload: PropertyExtractionPayload) => api.extractProperties(payload),
    onSuccess: (data) => {
      setExtractionResult(data);
      setExtractionSource("manual");
    },
  });

  const propertyCategories = propertySchemas?.categories ?? [];
  const detailRow = selectedRows[0] ?? null;
  const precomputedExtraction = useMemo(
    () => getItemExtractedProperties(detailRow as ApiPriceListItem | null),
    [detailRow],
  );

  const guessCategoryFromRow = useCallback((row: PriceListRow | null) => {
    if (!row) return null;
    const code = (row.wbs6_code ?? (row as any)?.wbs_code ?? "").toString();
    const prefix = code.split(".")[0];
    return prefix && WBS_CATEGORY_MAP[prefix] ? WBS_CATEGORY_MAP[prefix] : null;
  }, []);

  const currentCategory: PropertyCategorySchema | null = useMemo(() => {
    if (!propertyCategories.length) return null;
    if (labCategoryId) {
      const found = propertyCategories.find((cat) => cat.id === labCategoryId);
      if (found) return found;
    }
    return propertyCategories[0] ?? null;
  }, [labCategoryId, propertyCategories]);

  const currentCategoryProperties: PropertySchemaField[] = currentCategory?.properties ?? [];

  const isSemanticMode = !!activeSemanticSearch;
  const isLoading = summaryLoading || catalogLoading || semanticLoading;
  const displayItems = isSemanticMode ? semanticResults : catalogItems;

  const wbsTree = useMemo<FrontendWbsNode[]>(() => {
    if (!displayItems) return [];
    const wbs6Map = new Map<string, FrontendWbsNode>();
    const wbs7Map = new Map<string, FrontendWbsNode>();
    displayItems.forEach((item) => {
      const wbs6 = item.wbs6_code || "SENZA_WBS6";
      const wbs7 = item.wbs7_code;
      if (!wbs6Map.has(wbs6)) {
        wbs6Map.set(wbs6, {
          id: `wbs6-${wbs6}`,
          level: 6,
          code: wbs6,
          description: item.wbs6_description || "",
          children: [],
          importo: 0,
          path: [{ level: 6, code: wbs6, description: item.wbs6_description || "" }],
        });
      }
      const wbs6Node = wbs6Map.get(wbs6)!;
      if (item.project_price) wbs6Node.importo += item.project_price;
      if (wbs7) {
        const key = `${wbs6}-${wbs7}`;
        if (!wbs7Map.has(key)) {
          const node: FrontendWbsNode = {
            id: `wbs7-${key}`,
            level: 7,
            code: wbs7,
            description: item.wbs7_description || "",
            importo: 0,
            children: [],
            path: [...wbs6Node.path, { level: 7, code: wbs7, description: item.wbs7_description || "" }],
          };
          wbs7Map.set(key, node);
          wbs6Node.children.push(node);
        }
        const wbs7Node = wbs7Map.get(key)!;
        if (item.project_price) wbs7Node.importo += item.project_price;
      }
    });
    return Array.from(wbs6Map.values()).sort((a, b) => (a.code || "").localeCompare(b.code || ""));
  }, [displayItems]);

  const filteredDisplayItems = useMemo(() => {
    if (!displayItems) return [];
    if (!selectedNodeId) return displayItems;
    for (const wbs6 of wbsTree) {
      if (wbs6.id === selectedNodeId || wbs6.code === selectedNodeId) {
        return displayItems.filter((row) => row.wbs6_code === wbs6.code);
      }
      for (const wbs7 of wbs6.children) {
        if (wbs7.id === selectedNodeId || wbs7.code === selectedNodeId) {
          return displayItems.filter((row) => row.wbs6_code === wbs6.code && row.wbs7_code === wbs7.code);
        }
      }
    }
    return displayItems;
  }, [displayItems, selectedNodeId, wbsTree]);

  const businessUnitOptions = useMemo(() => {
    if (!summary) return [];
    return summary.business_units
      .map((bu) => ({ value: bu.value ?? "", label: bu.label }))
      .filter((opt) => opt.value !== "");
  }, [summary]);

  const commessaOptions = useMemo(() => {
    if (!summary) return [];
    return summary.business_units
      .flatMap((bu) =>
        bu.commesse.map((c) => ({
          value: c.commessa_id,
          label: `${c.commessa_nome} (${c.commessa_codice})`,
          businessUnit: bu.value ?? "",
        })),
      )
      .filter((opt) => String(opt.value) !== "");
  }, [summary]);

  const filteredCommessaOptions = useMemo(() => {
    if (!businessUnitFilter) return commessaOptions;
    return commessaOptions.filter((c) => c.businessUnit === businessUnitFilter);
  }, [commessaOptions, businessUnitFilter]);

  const columnDefs = useMemo<ColDef<PriceListRow>[]>(() => {
    const cols: ColDef<PriceListRow>[] = [
      { field: "commessa_codice", headerName: "Commessa", width: 120 },
      { field: "business_unit", headerName: "Business Unit", width: 150 },
      { field: "item_code", headerName: "Codice", width: 140 },
      {
        field: "item_description",
        headerName: "Descrizione",
        width: 380,
        valueFormatter: (params) => truncateMiddle(params.value, 60, 40),
        tooltipValueGetter: (params) => params.value || "",
      },
      { field: "unit_label", headerName: "U.M.", width: 80 },
      { field: "wbs6_code", headerName: "WBS6", width: 100 },
      { field: "wbs7_code", headerName: "WBS7", width: 100 },
      {
        field: "project_price",
        headerName: "Prezzo",
        width: 130,
        type: "numericColumn",
        valueFormatter: (params) => (params.value != null ? formatCurrency(params.value) : "-"),
      },
    ];
    if (isSemanticMode) {
      cols.unshift({
        field: "score" as any,
        headerName: "Rilevanza",
        width: 110,
        cellRenderer: (params: any) => {
          const score = typeof params.value === "number" ? params.value : Number(params.value);
          if (!Number.isFinite(score)) return "-";
          return `${(score * 100).toFixed(1)}%`;
        },
      });
    }
    return cols;
  }, [isSemanticMode, semanticThreshold]);

  const stats = useMemo(() => {
    const totalItems = displayItems?.length ?? 0;
    const wbs6Count = new Set(
      (displayItems ?? []).map((row) => row.wbs6_code).filter((code): code is string => Boolean(code)),
    ).size;
    return { totalItems, wbs6Count };
  }, [displayItems]);

  const handleSemanticSearch = () => {
    if (semanticQuery.trim().length >= 2) {
      setSemanticThreshold(DEFAULT_SEMANTIC_THRESHOLD);
      setActiveSemanticSearch(semanticQuery.trim());
      setSemanticOpen(false);
    }
  };

  const clearSemantic = () => {
    setSemanticQuery("");
    setActiveSemanticSearch("");
    setSemanticThreshold(DEFAULT_SEMANTIC_THRESHOLD);
  };

  const getRowId = useCallback(
    (params: { data: PriceListRow; rowIndex?: number }) => {
      const item = params.data;
      if (item?.id != null) return String(item.id);
      const code = item?.item_code || item?.product_id || "row";
      const suffix = params.rowIndex != null ? `-${params.rowIndex}` : "";
      return `${code}${suffix}`;
    },
    [],
  );

  useEffect(() => {
    if (!detailRow) {
      setExtractionResult(null);
      setExtractionSource(null);
      return;
    }
    setLabText(detailRow.item_description ?? (detailRow as any).description ?? "");
    setExtractionResult(precomputedExtraction);
    setExtractionSource(precomputedExtraction ? "precalculated" : null);
    const guessed = guessCategoryFromRow(detailRow);
    setLabCategoryId((prev) => prev ?? guessed ?? propertyCategories[0]?.id ?? null);
  }, [detailRow, guessCategoryFromRow, precomputedExtraction, propertyCategories]);

  useEffect(() => {
    if (!currentCategory) return;
    const defaults =
      currentCategory.required && currentCategory.required.length > 0
        ? currentCategory.required
        : currentCategory.properties.map((p) => p.id);
    setSelectedProperties(defaults);
  }, [currentCategory]);

  const handleRunExtraction = () => {
    if (!detailRow || !currentCategory) return;
    extractionMutation.mutate({
      text: labText || detailRow.item_description || (detailRow as any).description || "",
      category_id: currentCategory.id,
      wbs6_code: detailRow.wbs6_code ?? (detailRow as any)?.wbs_code,
      wbs6_description: detailRow.wbs6_description ?? (detailRow as any)?.wbs_description,
      properties: selectedProperties,
      engine: extractionEngine,
    });
  };

  const renderExtractionResult = () => {
    if (extractionMutation.isPending) return <Skeleton className="h-20 w-full" />;
    if (!extractionResult) return <p className="text-sm text-muted-foreground">Esegui una estrazione per vedere i valori.</p>;
    const entries = Object.entries(extractionResult.properties ?? {});
    if (!entries.length) return <p className="text-sm text-muted-foreground">Nessuna proprieta disponibile.</p>;
    return (
      <div className="grid grid-cols-1 gap-2">
        {entries.map(([key, raw]) => {
          const display = raw == null ? "—" : String(raw);
          const isMissing = extractionResult.missing_required?.includes(key);
          return (
            <div key={key} className="rounded-md border border-border/60 p-2">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span className="font-semibold">{key.replace(/_/g, " ")}</span>
                {isMissing && <Badge variant="destructive">Mancante</Badge>}
              </div>
              <div className="text-sm font-medium text-foreground break-words">{display}</div>
            </div>
          );
        })}
        {extractionResult.missing_required?.length ? (
          <Alert className="col-span-1">
            <AlertDescription>
              Proprietà obbligatorie non trovate: {extractionResult.missing_required.join(", ")}
            </AlertDescription>
          </Alert>
        ) : null}
      </div>
    );
  };

  if (isLoading && !displayItems) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="p-6">
        <Alert variant="destructive">
          <AlertDescription>Impossibile caricare il catalogo prezzi</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <>
      <div className="flex items-center justify-between gap-3 pb-3">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold">Elenco Prezzi</h1>
          <p className="text-sm text-muted-foreground">
            Include laboratorio AI collegato a Ollama. Totale voci: {stats.totalItems.toLocaleString("it-IT")}.
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline">WBS6: {stats.wbs6Count}</Badge>
            {isSemanticMode && <Badge variant="secondary">AI attiva</Badge>}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setSidebarOpen(true)}>
            <PanelRight className="mr-2 h-4 w-4" />
            WBS
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setFiltersOpen(true)}>
            <Filter className="mr-2 h-4 w-4" />
            Filtri
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setSemanticOpen(true)}>
            <Sparkles className="mr-2 h-4 w-4" />
            Ricerca AI
          </Button>
        </div>
      </div>

      <Card className="mb-3">
        <CardContent className="flex flex-wrap items-center gap-2 py-3">
          <Select
            value={businessUnitFilter ?? "all"}
            onValueChange={(value) => {
              setBusinessUnitFilter(value === "all" ? null : value);
              if (value === "all") setCommessaFilter(null);
            }}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Business Unit" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutte le Business Unit</SelectItem>
              {businessUnitOptions.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={commessaFilter ? String(commessaFilter) : "all"}
            onValueChange={(value) => setCommessaFilter(value === "all" ? null : Number(value))}
          >
            <SelectTrigger className="w-[230px]">
              <SelectValue placeholder="Commessa" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Tutte le Commesse</SelectItem>
              {filteredCommessaOptions.map((opt) => (
                <SelectItem key={opt.value} value={String(opt.value)}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="relative w-[280px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSemanticSearch()}
              placeholder='Ricerca semantica (es. "porta blindata")'
              className="pl-9 pr-9"
            />
            {semanticQuery && (
              <button
                onClick={() => setSemanticQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <Button size="sm" onClick={handleSemanticSearch} disabled={semanticQuery.trim().length < 2}>
            <Sparkles className="mr-2 h-4 w-4" />
            Cerca AI
          </Button>
          {isSemanticMode && (
            <Button variant="ghost" size="sm" onClick={clearSemantic}>
              <XCircle className="mr-1 h-4 w-4" />
              Annulla
            </Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">Catalogo prezzi</CardTitle>
          {isSemanticMode && <p className="text-xs text-muted-foreground">Ricerca AI con soglia {semanticThreshold}</p>}
        </CardHeader>
        <CardContent className="p-2 sm:p-4">
          <DataTable
            data={filteredDisplayItems ?? []}
            columnDefs={columnDefs}
            getRowId={getRowId}
            enableRowSelection
            enableQuickFilter
            onRowClicked={(row) => {
              setSelectedRows([row]);
              setDetailOpen(true);
            }}
            onSelectionChanged={(rows) => setSelectedRows(rows)}
            isLoading={isLoading}
          />
        </CardContent>
      </Card>

      <Sheet open={filtersOpen} onOpenChange={setFiltersOpen}>
        <SheetContent side="right" className="w-[380px]">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Filtri
            </SheetTitle>
          </SheetHeader>
          <div className="mt-4 space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Business Unit</label>
              <Select
                value={businessUnitFilter ?? "all"}
                onValueChange={(value) => {
                  setBusinessUnitFilter(value === "all" ? null : value);
                  if (value === "all") setCommessaFilter(null);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutte" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte le Business Unit</SelectItem>
                  {businessUnitOptions.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Commessa</label>
              <Select
                value={commessaFilter ? String(commessaFilter) : "all"}
                onValueChange={(value) => setCommessaFilter(value === "all" ? null : Number(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tutte" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutte le Commesse</SelectItem>
                  {filteredCommessaOptions.map((opt) => (
                    <SelectItem key={opt.value} value={String(opt.value)}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button variant="outline" onClick={() => setSelectedNodeId(null)}>
              Azzera filtro WBS
            </Button>
          </div>
        </SheetContent>
      </Sheet>

      <Sheet open={semanticOpen} onOpenChange={setSemanticOpen}>
        <SheetContent side="right" className="w-[380px]">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Ricerca semantica
            </SheetTitle>
          </SheetHeader>
          <div className="mt-4 space-y-4">
            {semanticError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {semanticError instanceof Error ? semanticError.message : String(semanticError)}
                </AlertDescription>
              </Alert>
            )}
            <label className="text-sm text-muted-foreground">Soglia minima</label>
            <input
              type="range"
              min={0.1}
              max={0.9}
              step={0.05}
              value={semanticThreshold}
              onChange={(e) => setSemanticThreshold(Number(e.target.value))}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">Riduci la soglia per piu risultati, aumenta per match piu precisi.</p>
            <Button variant="outline" onClick={clearSemantic}>
              Annulla ricerca AI
            </Button>
          </div>
        </SheetContent>
      </Sheet>

      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="right" className="w-[400px] p-0">
          <SheetHeader className="px-4 py-3 border-b">
            <SheetTitle className="text-base">Filtro WBS</SheetTitle>
          </SheetHeader>
          <div className="h-[calc(100%-56px)] overflow-y-auto p-3">
            <WBSFilterPanel
              nodes={wbsTree}
              selectedNodeId={selectedNodeId}
              onNodeSelect={(nodeId) => setSelectedNodeId(nodeId)}
              onClose={() => setSidebarOpen(false)}
              showAmounts={false}
            />
          </div>
        </SheetContent>
      </Sheet>

      <Sheet open={detailOpen} onOpenChange={setDetailOpen}>
        <SheetContent side="right" className="w-full sm:w-[520px] overflow-y-auto">
          <SheetHeader>
            <SheetTitle className="flex items-center gap-2">
              <Info className="h-5 w-5" />
              Dettaglio & AI lab
            </SheetTitle>
          </SheetHeader>
          {!detailRow ? (
            <p className="mt-4 text-sm text-muted-foreground">Seleziona una riga per vedere il dettaglio.</p>
          ) : (
            <Tabs defaultValue="dettaglio" className="mt-4">
              <TabsList className="grid grid-cols-2">
                <TabsTrigger value="dettaglio">Dettaglio</TabsTrigger>
                <TabsTrigger value="ai">Proprieta (AI)</TabsTrigger>
              </TabsList>
              <TabsContent value="dettaglio" className="space-y-3">
                <Card>
                  <CardHeader className="pb-1">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Tag className="h-4 w-4 text-muted-foreground" />
                      {detailRow.item_code}
                      <Badge variant="outline">{detailRow.unit_label}</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <p className="text-sm leading-relaxed">{detailRow.item_description}</p>
                    <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary">WBS6 {detailRow.wbs6_code || "-"}</Badge>
                      <Badge variant="secondary">WBS7 {detailRow.wbs7_code || "-"}</Badge>
                      <Badge variant="secondary">Commessa {detailRow.commessa_codice || "-"}</Badge>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="ai" className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label>Engine</Label>
                    <Select value={extractionEngine} onValueChange={(v: "llm" | "rules") => setExtractionEngine(v)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="llm">LLM (Ollama)</SelectItem>
                        <SelectItem value="rules">Regole / parser</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Categoria schema</Label>
                    <Select
                      value={currentCategory?.id ?? ""}
                      onValueChange={(value) => setLabCategoryId(value)}
                      disabled={!propertyCategories.length}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Categoria" />
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
                    rows={4}
                    placeholder="Incolla o modifica la descrizione della voce"
                  />
                </div>
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <Label>Proprieta</Label>
                    <Badge variant="secondary">
                      {selectedProperties.length}/{currentCategoryProperties.length}
                    </Badge>
                  </div>
                  <div className="rounded-md border border-border/60 bg-muted/40">
                    <ScrollArea className="h-40">
                      <div className="divide-y divide-border/60">
                        {currentCategoryProperties.length === 0 ? (
                          <div className="p-3 text-sm text-muted-foreground">Caricamento schema...</div>
                        ) : (
                          currentCategoryProperties.map((prop) => {
                            const isChecked = selectedProperties.includes(prop.id);
                            const isRequired = currentCategory?.required?.includes(prop.id);
                            return (
                              <label
                                key={prop.id}
                                className="flex items-start gap-3 p-2 hover:bg-background/60 cursor-pointer"
                              >
                                <Checkbox
                                  checked={isChecked}
                                  disabled={isRequired}
                                  onCheckedChange={(v) =>
                                    setSelectedProperties((prev) =>
                                      v ? [...new Set([...prev, prop.id])] : prev.filter((p) => p !== prop.id),
                                    )
                                  }
                                />
                                <div className="space-y-0.5">
                                  <div className="flex items-center gap-2 text-sm font-semibold">
                                    <span>{prop.title ?? prop.id}</span>
                                    {isRequired && <Badge variant="outline">Obbligatoria</Badge>}
                                    {prop.unit && <Badge variant="secondary">{prop.unit}</Badge>}
                                  </div>
                                  <p className="text-xs text-muted-foreground">
                                    {prop.type ?? "string"} {prop.enum ? `(enum ${prop.enum.join(", ")})` : ""}
                                  </p>
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
                  <Button onClick={handleRunExtraction} disabled={extractionMutation.isPending || !currentCategory}>
                    {extractionMutation.isPending ? "Estrazione..." : "Estrai proprieta"}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setExtractionResult(null);
                      setExtractionSource(null);
                    }}
                  >
                    Svuota
                  </Button>
                </div>
                <div className="rounded-lg border border-border/60 bg-card p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-semibold">Risultato</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      {extractionSource === "precalculated" && <Badge variant="outline">Calcolato catalogo</Badge>}
                      {extractionSource === "manual" && <Badge variant="secondary">Ultima estrazione</Badge>}
                    </div>
                  </div>
                  {renderExtractionResult()}
                </div>
              </TabsContent>
            </Tabs>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

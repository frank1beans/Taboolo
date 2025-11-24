import { useCallback, useEffect, useMemo, useRef, useState, ComponentProps } from "react";
import { Upload, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { read, utils } from "xlsx";
import type { WorkBook } from "xlsx";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";
import { ApiImportConfig, ApiImportConfigCreate, ApiSixPreventivoOption } from "@/types/api";
import { UploadArea } from "@/components/UploadArea";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api-client";
import { formatCurrency } from "@/lib/formatters";

type ImportMode = "project" | "return";
type ReturnFormat = "lc" | "mc";
type WizardStep = "kind" | "upload" | "config" | "status";

const WIZARD_STEPS: { id: WizardStep; label: string }[] = [
  { id: "kind", label: "Tipo" },
  { id: "upload", label: "File" },
  { id: "config", label: "Configurazione" },
  { id: "status", label: "Avanzamento" },
];

interface ColumnMeta {
  key: string;
  label: string;
  samples: string[];
  numericScore: number;
  currencyScore: number;
  textScore: number;
  codeScore: number;
}

interface ColumnScoreOptions {
  keywords?: string[];
  excludeKeys?: string[];
  disallowKeywords?: string[];
  preferNumeric?: boolean;
  preferText?: boolean;
  preferCodePattern?: boolean;
  preferCurrency?: boolean;
  penalizeCurrency?: boolean;
}

interface RoundInfo {
  round: number;
  imprese: string[];
}

interface RoundUploadDialogProps {
  commessaId?: number | string | null;
  onUploadProgetto: (params: {
    file: File;
    tipo: "excel" | "six";
    preventivoId?: string;
    enableEmbeddings?: boolean;
    enablePropertyExtraction?: boolean;
  }) => Promise<void>;
  onPreviewPreventivi: (file: File) => Promise<ApiSixPreventivoOption[]>;
  onUploadRitorno: (params: {
    file: File;
    impresa: string;
    roundNumber: number;
    mode: "new" | "replace";
    sheetName: string;
    codeColumns: string[];
    descriptionColumns: string[];
    priceColumn: string;
    quantityColumn?: string;
    progressColumn?: string;
  }) => Promise<void>;
  existingRounds: number[];
  roundDetails: RoundInfo[];
  disabled?: boolean;
  triggerProps?: ComponentProps<typeof Button>;
}

const PRICE_KEYWORDS = ["prezzo", "price", "€", "importo unitario"];
const QUANTITY_KEYWORDS = ["quant", "qta", "qty"];
const CURRENCY_REGEX = /€|eur|euro/i;
const CODE_PATTERN = /^[A-Za-z]{1,3}\d{2,4}(?:[.\-_/]?[A-Za-z0-9]{1,4})*$/;
const EMPTY_SELECT_VALUE = "__none__";

const normalizeColumnKey = (value: string | null | undefined): string | null => {
  if (!value) return null;
  const trimmed = value.trim();
  return trimmed || null;
};
const CONFIG_MANUAL_VALUE = "__manual__";

const splitColumnTokens = (value?: string | null): string[] => {
  if (!value) return [];
  return value
    .split(/[,;\s]+/)
    .map((token) => token.trim())
    .filter(Boolean);
};

const firstColumnToken = (value?: string | null): string => {
  const tokens = splitColumnTokens(value);
  return tokens[0] ?? "";
};

const columnLetter = (index: number): string => {
  let current = index;
  let label = "";
  while (current >= 0) {
    label = String.fromCharCode((current % 26) + 65) + label;
    current = Math.floor(current / 26) - 1;
  }
  return label;
};

const buildColumnMeta = (rows: unknown[][]): ColumnMeta[] => {
  if (!rows.length) return [];
  const HEADER_TOKENS = ["cod", "categoria", "descr", "prezzo", "importo", "unit", "qta", "quant"];
  const looksLikeHeader = (row: unknown[]): boolean => {
    const filled = row
      .map((cell) => (cell == null ? "" : String(cell).trim()))
      .filter((cell) => cell.length > 0);
    if (filled.length < 2) return false;
    const matches = filled.filter((cell) =>
      HEADER_TOKENS.some((token) => cell.toLowerCase().includes(token)),
    ).length;
    return matches >= 2;
  };
  let headerIndex = rows.findIndex(looksLikeHeader);
  if (headerIndex === -1) {
    headerIndex = rows.findIndex(
      (row) => (row ?? []).filter((cell) => cell != null && String(cell).trim().length > 0).length >= 2,
    );
  }
  if (headerIndex === -1) headerIndex = 0;
  const header = rows[headerIndex] ?? [];
  const samples = rows.slice(headerIndex + 1, headerIndex + 6);
  return header
    .map((cell, index) => {
      const label = cell ? String(cell) : columnLetter(index);
      const columnSamples = samples
        .map((row) => (row?.[index] ? String(row[index]) : ""))
        .filter(Boolean);
      const numericScore = columnSamples.filter((value) => !Number.isNaN(Number(value))).length / 5;
      const currencyScore =
        columnSamples.filter((value) => CURRENCY_REGEX.test(value.toString())).length / 5;
      const textScore =
        columnSamples.filter((value) => value.toString().replace(/\d+/g, "").trim().length > 10)
          .length / 5;
      const codeScore =
        columnSamples.filter((value) => CODE_PATTERN.test(value.toString().toUpperCase()))
          .length / 5;
      return {
        key: columnLetter(index),
        label,
        samples: columnSamples,
        numericScore,
        currencyScore,
        textScore,
        codeScore,
      };
    })
    .filter((column) => column.label);
};

const computeColumnScore = (column: ColumnMeta, options: ColumnScoreOptions): number => {
  const haystack = `${column.label} ${column.samples.join(" ")}`.toLowerCase();
  let score = 0;
  options.keywords?.forEach((keyword) => {
    if (haystack.includes(keyword.toLowerCase())) score += 3;
  });
  if (options.disallowKeywords?.some((keyword) => haystack.includes(keyword.toLowerCase()))) {
    return 0;
  }
  if (options.preferCodePattern) score += column.codeScore * 4;
  if (options.preferNumeric) score += column.numericScore * 3;
  if (options.preferText) score += column.textScore * 2;
  if (options.preferCurrency) score += column.currencyScore * 3;
  if (options.penalizeCurrency) score -= column.currencyScore;
  if (column.samples.length) score += 0.5;
  if (options.excludeKeys?.includes(column.key)) return 0;
  return score;
};

const pickColumnKey = (
  columns: ColumnMeta[],
  options: ColumnScoreOptions,
  fallback?: string,
): string => {
  const ranked = columns
    .map((column) => ({ column, score: computeColumnScore(column, options) }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score);
  if (ranked.length > 0) return ranked[0].column.key;
  return fallback ?? "";
};

export function RoundUploadDialog({
  commessaId,
  onUploadProgetto,
  onPreviewPreventivi,
  onUploadRitorno,
  existingRounds,
  roundDetails,
  disabled = false,
  triggerProps,
}: RoundUploadDialogProps) {
  const [open, setOpen] = useState(false);
  const [importMode, setImportMode] = useState<ImportMode>("project");
  const [returnFormat, setReturnFormat] = useState<ReturnFormat>("lc");
  const [wizardStep, setWizardStep] = useState<WizardStep>("kind");
  const [projectFile, setProjectFile] = useState<File | null>(null);
  const [projectFileKind, setProjectFileKind] = useState<"six" | "excel" | null>(null);
  const [projectPreviewing, setProjectPreviewing] = useState(false);
  const [preventivoOptions, setPreventivoOptions] = useState<ApiSixPreventivoOption[]>([]);
  const [selectedPreventivoId, setSelectedPreventivoId] = useState<string>("");
  const [returnFile, setReturnFile] = useState<File | null>(null);
  const [returnWorkbook, setReturnWorkbook] = useState<WorkBook | null>(null);
  const [returnSheetName, setReturnSheetName] = useState("");
  const [returnColumns, setReturnColumns] = useState<ColumnMeta[]>([]);
  const [sheetLoading, setSheetLoading] = useState(false);
  const [roundMode, setRoundMode] = useState<"new" | "existing">("new");
  const [existingAction, setExistingAction] = useState<"add" | "replace">("add");
  const [selectedRound, setSelectedRound] = useState<string>("");
  const [impresaName, setImpresaName] = useState("");
  const [codeColumnKey, setCodeColumnKey] = useState("");
  const [descriptionColumnKey, setDescriptionColumnKey] = useState("");
  const [priceColumnKey, setPriceColumnKey] = useState("");
  const [quantityColumnKey, setQuantityColumnKey] = useState("");
  const [progressiveColumnKey, setProgressiveColumnKey] = useState("");
  const [selectedConfigId, setSelectedConfigId] = useState<string>(CONFIG_MANUAL_VALUE);
  const [pendingSheetName, setPendingSheetName] = useState<string | null>(null);
  const [enableEmbeddings, setEnableEmbeddings] = useState(false);
  const [enablePropertyExtraction, setEnablePropertyExtraction] = useState(false);
  const [configSaveName, setConfigSaveName] = useState("");
  const [configSaveImpresa, setConfigSaveImpresa] = useState("");
  const [configSaveNote, setConfigSaveNote] = useState("");
  const [configSaveScope, setConfigSaveScope] = useState<"commessa" | "global">("commessa");
  const [configSaveIncludeColumns, setConfigSaveIncludeColumns] = useState(true);
  const [uploadState, setUploadState] = useState<"idle" | "uploading" | "success" | "error">(
    "idle",
  );
  const [uploadLog, setUploadLog] = useState<string[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const configsEnabled = open && importMode === "return";
  const {
    data: importConfigs = [],
    isLoading: configsLoading,
    refetch: refetchImportConfigs,
  } = useQuery({
    queryKey: ["import-configs", "wizard", commessaId ?? "global"],
    queryFn: () => api.listImportConfigs(
      commessaId !== undefined && commessaId !== null
        ? { commessaId }
        : undefined,
    ),
    enabled: configsEnabled,
  });
  const selectedConfig = useMemo(() => {
    if (selectedConfigId === CONFIG_MANUAL_VALUE) return null;
    return (
      importConfigs.find((config) => String(config.id) === selectedConfigId) ?? null
    );
  }, [importConfigs, selectedConfigId]);

  const columnMap = useMemo(() => {
    const map = new Map<string, ColumnMeta>();
    returnColumns.forEach((column) => map.set(column.key, column));
    return map;
  }, [returnColumns]);

  const resolveColumnReference = useCallback(
    (key?: string) => {
      if (!key) return undefined;
      const meta = columnMap.get(key);
      if (!meta) return key;
      const label = String(meta.label ?? "").trim();
      if (label && label.toUpperCase() !== meta.key.toUpperCase()) {
        return label;
      }
      return meta.key;
    },
    [columnMap],
  );

  const findColumnKeyForReference = useCallback(
    (reference?: string | null) => {
      if (!reference) return "";
      const normalized = reference.trim();
      if (!normalized) return "";
      const upper = normalized.toUpperCase();
      const byLabel = returnColumns.find(
        (column) => (column.label ?? "").trim().toUpperCase() === upper,
      );
      if (byLabel) return byLabel.key;
      const byKey = returnColumns.find((column) => column.key.toUpperCase() === upper);
      if (byKey) return byKey.key;
      return upper;
    },
    [returnColumns],
  );
  const saveConfigMutation = useMutation({
    mutationFn: async ({
      payload,
      scope,
    }: {
      payload: ApiImportConfigCreate;
      scope: "commessa" | "global";
    }) => {
      if (scope === "commessa" && (commessaId === undefined || commessaId === null)) {
        throw new Error("Commessa non disponibile per il salvataggio.");
      }
      return api.createImportConfig(
        payload,
        scope === "commessa" && commessaId !== undefined && commessaId !== null
          ? { commessaId }
          : undefined,
      );
    },
    onSuccess: (config) => {
      toast.success("Configurazione salvata", {
        description: `Applicata "${config.nome}"`,
      });
      queryClient.invalidateQueries({ queryKey: ["import-configs"] });
      refetchImportConfigs();
      setSelectedConfigId(String(config.id));
      setConfigSaveName("");
      setConfigSaveImpresa("");
      setConfigSaveNote("");
    },
    onError: (error) => {
      toast.error("Impossibile salvare la configurazione", {
        description: error instanceof Error ? error.message : undefined,
      });
    },
  });
  const applyImportConfig = useCallback(
    (config: ApiImportConfig) => {
      if (config.impresa) {
        setImpresaName(config.impresa);
      }
      if (config.sheet_name) {
        if (returnWorkbook?.SheetNames?.includes(config.sheet_name)) {
          setReturnSheetName(config.sheet_name);
          setPendingSheetName(null);
        } else {
          setPendingSheetName(config.sheet_name);
        }
      } else {
        setPendingSheetName(null);
      }
      const codeToken = firstColumnToken(config.code_columns);
      const descriptionToken = firstColumnToken(config.description_columns);
      setCodeColumnKey(codeToken ? findColumnKeyForReference(codeToken) : "");
      setDescriptionColumnKey(
        descriptionToken ? findColumnKeyForReference(descriptionToken) : "",
      );
      setPriceColumnKey(findColumnKeyForReference(config.price_column) || "");
      setQuantityColumnKey(findColumnKeyForReference(config.quantity_column) || "");
    },
    [returnWorkbook, findColumnKeyForReference],
  );
  const handleSaveConfig = useCallback(() => {
    const nome = configSaveName.trim();
    if (!nome) {
      toast.error("Nome configurazione obbligatorio");
      return;
    }
    if (
      configSaveScope === "commessa" &&
      (commessaId === undefined || commessaId === null)
    ) {
      toast.error("Commessa non disponibile", {
        description: "Non è possibile salvare su questa commessa al momento.",
      });
      return;
    }
    const resolveRef = (key?: string) => resolveColumnReference(key) ?? key?.toUpperCase();

    const payload: ApiImportConfigCreate = {
      nome,
      impresa: configSaveImpresa.trim()
        ? configSaveImpresa.trim()
        : impresaName.trim() || undefined,
      sheet_name: returnSheetName || undefined,
      note: configSaveNote.trim() || undefined,
      code_columns:
        configSaveIncludeColumns && codeColumnKey
          ? resolveRef(codeColumnKey) ?? codeColumnKey
          : undefined,
      description_columns:
        configSaveIncludeColumns && descriptionColumnKey
          ? resolveRef(descriptionColumnKey) ?? descriptionColumnKey
          : undefined,
      price_column:
        configSaveIncludeColumns && priceColumnKey
          ? resolveRef(priceColumnKey) ?? priceColumnKey
          : undefined,
      quantity_column:
        configSaveIncludeColumns && quantityColumnKey
          ? resolveRef(quantityColumnKey) ?? quantityColumnKey
          : undefined,
    };
    saveConfigMutation.mutate({ payload, scope: configSaveScope });
  }, [
    codeColumnKey,
    commessaId,
    configSaveImpresa,
    configSaveIncludeColumns,
    configSaveName,
    configSaveNote,
    configSaveScope,
    descriptionColumnKey,
    impresaName,
    priceColumnKey,
    quantityColumnKey,
    returnSheetName,
    saveConfigMutation,
  ]);
  const progressValue = useMemo(() => {
    if (uploadState === "uploading") {
      return Math.min(20 + uploadLog.length * 20, 95);
    }
    if (uploadState === "success") {
      return 100;
    }
    if (uploadState === "error") {
      return uploadLog.length > 0 ? 100 : 0;
    }
    return 0;
  }, [uploadState, uploadLog.length]);

  const nextRoundNumber =
    existingRounds.length > 0 ? Math.max(...existingRounds) + 1 : 1;
  const roundDetailsMap = useMemo(
    () => new Map(roundDetails.map((detail) => [String(detail.round), detail])),
    [roundDetails],
  );
  const selectedRoundInfo = selectedRound ? roundDetailsMap.get(selectedRound) : null;

  const {
    className: triggerClassName,
    disabled: triggerDisabled,
    ...restTriggerProps
  } = triggerProps ?? {};
  const mergedTriggerDisabled = triggerDisabled ?? disabled;

  const resetState = useCallback(() => {
    setWizardStep("kind");
    setImportMode("project");
    setReturnFormat("lc");
    setProjectFile(null);
    setProjectFileKind(null);
    setPreventivoOptions([]);
    setSelectedPreventivoId("");
    setReturnFile(null);
    setReturnWorkbook(null);
    setReturnSheetName("");
    setReturnColumns([]);
    setSheetLoading(false);
    setRoundMode("new");
    setExistingAction("add");
    setSelectedRound("");
    setImpresaName("");
    setCodeColumnKey("");
    setDescriptionColumnKey("");
    setPriceColumnKey("");
    setQuantityColumnKey("");
    setProgressiveColumnKey("");
    setSelectedConfigId(CONFIG_MANUAL_VALUE);
    setPendingSheetName(null);
    setConfigSaveName("");
    setConfigSaveImpresa("");
    setConfigSaveNote("");
    setConfigSaveScope("commessa");
    setConfigSaveIncludeColumns(true);
    setUploadState("idle");
    setUploadLog([]);
    setUploadError(null);
  }, []);

  useEffect(() => {
    if (!open) {
      resetState();
    }
  }, [open, resetState]);

  const handleProjectFileSelected = useCallback(
    async (file: File | null) => {
      if (!file) {
        setProjectFile(null);
        setProjectFileKind(null);
        setPreventivoOptions([]);
        setSelectedPreventivoId("");
        return;
      }
      setProjectFile(file);
      const lower = file.name.toLowerCase();
      const isSix = lower.endsWith(".six") || lower.endsWith(".xml");
      setProjectFileKind(isSix ? "six" : "excel");
      if (isSix) {
        setProjectPreviewing(true);
        try {
          const options = await onPreviewPreventivi(file);
          setPreventivoOptions(options);
          setSelectedPreventivoId(options[0]?.internal_id ?? "");
        } catch (error) {
          toast.error("Impossibile analizzare il file STR Vision", {
            description: error instanceof Error ? error.message : undefined,
          });
          setProjectFile(null);
          setProjectFileKind(null);
        } finally {
          setProjectPreviewing(false);
        }
      }
    },
    [onPreviewPreventivi],
  );

  const parseReturnSheet = useCallback(
    (workbook: WorkBook, sheetName: string) => {
      const sheet = workbook.Sheets[sheetName];
      if (!sheet) {
        setReturnColumns([]);
        return;
      }
      const rows = utils.sheet_to_json(sheet, {
        header: 1,
        blankrows: false,
        defval: null,
      }) as unknown[][];
      setReturnColumns(buildColumnMeta(rows));
    },
    [],
  );

  const handleReturnFileSelected = useCallback(
    async (file: File | null) => {
      if (!file) {
        setReturnFile(null);
        setReturnWorkbook(null);
        setReturnSheetName("");
        setReturnColumns([]);
        return;
      }
      setSheetLoading(true);
      try {
        const buffer = await file.arrayBuffer();
        const workbook = read(buffer, { type: "array" });
        setReturnWorkbook(workbook);
        setReturnSheetName(workbook.SheetNames?.[0] ?? "");
        setReturnFile(file);
        if (workbook.SheetNames?.[0]) {
          parseReturnSheet(workbook, workbook.SheetNames[0]);
        }
      } catch (error) {
        toast.error("Impossibile leggere il file Excel", {
          description: error instanceof Error ? error.message : undefined,
        });
        setReturnWorkbook(null);
        setReturnFile(null);
        setReturnSheetName("");
        setReturnColumns([]);
      } finally {
        setSheetLoading(false);
      }
    },
    [parseReturnSheet],
  );

  useEffect(() => {
    if (returnWorkbook && returnSheetName) {
      parseReturnSheet(returnWorkbook, returnSheetName);
    }
  }, [returnWorkbook, returnSheetName, parseReturnSheet]);

  useEffect(() => {
    if (!returnColumns.length) return;
    setPriceColumnKey((prev) =>
      prev || pickColumnKey(returnColumns, { keywords: PRICE_KEYWORDS, preferCurrency: true }),
    );
    if (returnFormat === "mc") {
      setProgressiveColumnKey((prev) =>
        prev || pickColumnKey(returnColumns, { keywords: ["prog", "progressivo"], preferNumeric: true }),
      );
    } else {
      setCodeColumnKey((prev) =>
        prev || pickColumnKey(returnColumns, { preferCodePattern: true }),
      );
      setDescriptionColumnKey((prev) =>
        prev || pickColumnKey(returnColumns, { preferText: true }),
      );
    }
    setQuantityColumnKey((prev) =>
      prev || pickColumnKey(returnColumns, { keywords: QUANTITY_KEYWORDS, preferNumeric: true }),
    );
  }, [returnColumns, returnFormat]);
  useEffect(() => {
    if (selectedConfig) {
      applyImportConfig(selectedConfig);
    }
  }, [selectedConfig, applyImportConfig]);
  useEffect(() => {
    if (!selectedConfig && selectedConfigId !== CONFIG_MANUAL_VALUE) {
      setSelectedConfigId(CONFIG_MANUAL_VALUE);
    }
  }, [selectedConfig, selectedConfigId]);
  useEffect(() => {
    if (!pendingSheetName || !returnWorkbook) return;
    if (returnWorkbook.SheetNames?.includes(pendingSheetName)) {
      setReturnSheetName(pendingSheetName);
      setPendingSheetName(null);
    }
  }, [pendingSheetName, returnWorkbook]);
  useEffect(() => {
    if (importMode !== "return") {
      setSelectedConfigId(CONFIG_MANUAL_VALUE);
    }
  }, [importMode]);


  const canProceedFromKind = importMode === "project" || Boolean(returnFormat);
  const canProceedFromUpload =
    importMode === "project" ? Boolean(projectFile) : Boolean(returnFile && returnSheetName);

  const sixPreventiviAvailable = projectFileKind === "six" && preventivoOptions.length > 0;
  const requiresPreventivoSelection = sixPreventiviAvailable;

  const canSubmit =
    importMode === "project"
      ? projectFileKind === "six"
        ? Boolean(projectFile) && (!requiresPreventivoSelection || Boolean(selectedPreventivoId))
        : Boolean(projectFile)
      : Boolean(
          impresaName.trim() &&
            (roundMode === "new" || selectedRound) &&
            returnFile &&
            returnSheetName &&
            priceColumnKey &&
            (returnFormat === "mc" ? progressiveColumnKey : codeColumnKey || descriptionColumnKey),
        );

  const handleNext = () => {
    if (wizardStep === "kind" && canProceedFromKind) {
      setWizardStep("upload");
    } else if (wizardStep === "upload" && canProceedFromUpload) {
      setWizardStep("config");
    }
  };

  const handlePrevious = () => {
    if (wizardStep === "upload") {
      setWizardStep("kind");
    } else if (wizardStep === "config") {
      setWizardStep("upload");
    } else if (wizardStep === "status") {
      setWizardStep("config");
    }
  };

  const handleUpload = async () => {
    if (!canSubmit) return;
    setWizardStep("status");
    setUploadState("uploading");
    setUploadLog(["Inizio importazione..."]);
    setUploadError(null);
    try {
      if (importMode === "project" && projectFile) {
        await onUploadProgetto({
          file: projectFile,
          tipo: projectFileKind === "six" ? "six" : "excel",
          preventivoId: selectedPreventivoId || undefined,
          enableEmbeddings,
          enablePropertyExtraction,
        });
      } else if (importMode === "return" && returnFile) {
        const roundNumber =
          roundMode === "new" ? nextRoundNumber : Number(selectedRound || nextRoundNumber);
        const codeColumns = codeColumnKey
          ? [resolveColumnReference(codeColumnKey) ?? codeColumnKey]
          : [];
        const descriptionColumns = descriptionColumnKey
          ? [resolveColumnReference(descriptionColumnKey) ?? descriptionColumnKey]
          : [];
        const priceColumnRef = resolveColumnReference(priceColumnKey) ?? priceColumnKey;
        const quantityColumnRef =
          (resolveColumnReference(quantityColumnKey) ?? quantityColumnKey) || undefined;
        const progressRef =
          returnFormat === "mc"
            ? resolveColumnReference(progressiveColumnKey) ?? progressiveColumnKey
            : undefined;
        await onUploadRitorno({
          file: returnFile,
          impresa: impresaName.trim(),
          roundNumber,
          mode: roundMode === "existing" && existingAction === "replace" ? "replace" : "new",
          sheetName: returnSheetName,
          codeColumns,
          descriptionColumns,
          priceColumn: priceColumnRef,
          quantityColumn: quantityColumnRef,
          progressColumn: progressRef,
        });
      }
      setUploadState("success");
      setUploadLog((log) => [...log, "Importazione completata"]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Errore sconosciuto";
      setUploadState("error");
      setUploadError(message);
      setUploadLog((log) => [...log, `Errore: ${message}`]);
    }
  };

  const renderKindStep = () => (
    <div className="space-y-6 py-4">
      <div className="space-y-3">
        <Label>Tipo di importazione</Label>
        <RadioGroup value={importMode} onValueChange={(value) => setImportMode(value as ImportMode)}>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="project" id="mode-project" />
            <Label htmlFor="mode-project" className="cursor-pointer font-normal">
              Computo di progetto (XML/SIX)
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="return" id="mode-return" />
            <Label htmlFor="mode-return" className="cursor-pointer font-normal">
              Ritorno di gara (Excel)
            </Label>
          </div>
        </RadioGroup>
      </div>
      {importMode === "return" && (
        <div className="space-y-3 rounded-md border px-4 py-3">
          <Label>Formato ritorno</Label>
          <RadioGroup
            value={returnFormat}
            onValueChange={(value) => setReturnFormat(value as ReturnFormat)}
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="lc" id="format-lc" />
              <Label htmlFor="format-lc" className="cursor-pointer font-normal">
                Lista lavorazioni (LC)
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="mc" id="format-mc" />
              <Label htmlFor="format-mc" className="cursor-pointer font-normal">
                Computo metrico per appalto (MC)
              </Label>
            </div>
          </RadioGroup>
        </div>
      )}
    </div>
  );

  const renderUploadStep = () => (
    <div className="space-y-6 py-4">
      <div>
        <Label className="mb-2 block">
          {importMode === "project" ? "File STR Vision" : "File Excel del ritorno"}
        </Label>
        <UploadArea
          onFileSelected={
            importMode === "project" ? handleProjectFileSelected : handleReturnFileSelected
          }
          onFileUpload={() => Promise.resolve()}
          submitLabel="File impostato"
          acceptExtensions={
            importMode === "project" ? [".six", ".xml", ".xlsx", ".xls"] : [".xlsx", ".xls"]
          }
          emptyStateTitle={
            importMode === "project"
              ? "Trascina qui il file STR Vision"
              : "Trascina qui il file Excel dell'offerta"
          }
          emptyStateDescription="oppure clicca per selezionarlo"
          successMessage={null}
        />
        {importMode === "project" && projectFile && (
          <p className="mt-2 text-xs text-muted-foreground">File: {projectFile.name}</p>
        )}
        {importMode === "return" && returnFile && (
          <p className="mt-2 text-xs text-muted-foreground">File: {returnFile.name}</p>
        )}
      </div>
      {importMode === "return" && returnWorkbook && (
        <div className="space-y-2">
          <Label>Foglio da importare</Label>
          <Select value={returnSheetName} onValueChange={setReturnSheetName}>
            <SelectTrigger>
              <SelectValue placeholder="Seleziona il foglio" />
            </SelectTrigger>
            <SelectContent>
              {returnWorkbook.SheetNames?.map((sheet) => (
                <SelectItem key={sheet} value={sheet}>
                  {sheet}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  );

  const renderConfigStep = () => {
    if (importMode === "project") {
      return (
        <div className="space-y-4 py-4">
          {projectFileKind === "six" ? (
            projectPreviewing ? (
              <p className="text-sm text-muted-foreground">Analisi del file STR Vision…</p>
            ) : preventivoOptions.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Nessun preventivo trovato: verrà importato solo il listino prezzi associato.
              </p>
            ) : (
              <>
                <Label>Seleziona il preventivo da importare</Label>
                <Select
                  value={selectedPreventivoId}
                  onValueChange={setSelectedPreventivoId}
                  disabled={projectPreviewing}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Preventivo..." />
                  </SelectTrigger>
                  <SelectContent>
                    {preventivoOptions.map((option) => (
                      <SelectItem key={option.internal_id} value={option.internal_id}>
                        <div className="flex flex-col gap-[2px]">
                          <span className="text-sm font-medium">
                            {option.code ? `${option.code} — ` : ""}
                            {option.description ?? option.internal_id}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {option.date ? `Data: ${option.date}` : "Data: n/d"}
                            {option.price_list_label ? ` · Listino: ${option.price_list_label}` : ""}
                            {option.rilevazioni != null ? ` · Rilevazioni: ${option.rilevazioni}` : ""}
                            {option.items != null ? ` · Prodotti: ${option.items}` : ""}
                          </span>
                          {option.total_importo != null && (
                            <span className="text-xs text-muted-foreground">
                              Importo stimato: {formatCurrency(option.total_importo)}
                            </span>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="grid gap-3 rounded-md border border-border/60 bg-background/40 p-3 text-sm text-foreground">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="font-semibold">Opzioni di elaborazione</p>
                      <p className="text-xs text-muted-foreground">Disabilitate di default per performance.</p>
                    </div>
                  </div>
                  <div className="flex flex-col gap-3">
                    <label className="flex items-center gap-2">
                      <Switch
                        checked={enableEmbeddings}
                        onCheckedChange={setEnableEmbeddings}
                      />
                      <div>
                        <p className="text-sm font-medium">Calcola embedding prezzi</p>
                        <p className="text-xs text-muted-foreground">
                          Genera embedding semantici del listino (CPU/GPU intensivo).
                        </p>
                      </div>
                    </label>
                    <label className="flex items-center gap-2">
                      <Switch
                        checked={enablePropertyExtraction}
                        onCheckedChange={setEnablePropertyExtraction}
                      />
                      <div>
                        <p className="text-sm font-medium">Estrai proprietà da descrizione</p>
                        <p className="text-xs text-muted-foreground">
                          Rallenta l'import: usa solo se ti servono subito gli attributi.
                        </p>
                      </div>
                    </label>
                  </div>
                </div>
              </>
            )
          ) : (
            <p className="text-sm text-muted-foreground">
              Nessuna configurazione richiesta per file Excel di progetto.
            </p>
          )}
        </div>
      );
    }
    return (
      <div className="space-y-4 py-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <Label>Impresa *</Label>
            <Input
              value={impresaName}
              onChange={(event) => setImpresaName(event.target.value)}
              placeholder="Nome dell'impresa"
            />
          </div>
          <div className="space-y-2">
            <Label>Round *</Label>
            <RadioGroup
              value={roundMode}
              onValueChange={(value) => setRoundMode(value as "new" | "existing")}
              className="space-y-2 rounded-md border px-3 py-2"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="new" id="round-new" />
                <Label htmlFor="round-new" className="cursor-pointer font-normal">
                  Nuovo round (Round {nextRoundNumber})
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="existing" id="round-existing" />
                <Label htmlFor="round-existing" className="cursor-pointer font-normal">
                  Round esistente
                </Label>
              </div>
            </RadioGroup>
          </div>
        </div>
        {roundMode === "existing" && (
          <Select value={selectedRound} onValueChange={setSelectedRound}>
            <SelectTrigger>
              <SelectValue placeholder="Seleziona il round" />
            </SelectTrigger>
            <SelectContent>
              {existingRounds.map((round) => (
                <SelectItem key={round} value={String(round)}>
                  Round {round}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        {selectedRoundInfo && (
          <p className="text-xs text-muted-foreground">
            Imprese giù presenti: {selectedRoundInfo.imprese.join(", ") || "Nessuna"}
          </p>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          {returnFormat === "mc" ? (
            <div className="space-y-2">
              <Label>Colonna progressivo *</Label>
              <Select
                value={progressiveColumnKey || EMPTY_SELECT_VALUE}
                onValueChange={(value) =>
                  setProgressiveColumnKey(value === EMPTY_SELECT_VALUE ? "" : value)
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Progressivo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={EMPTY_SELECT_VALUE}>Nessuna</SelectItem>
                  {returnColumns.map((column) => (
                    <SelectItem key={column.key} value={column.key}>
                      {column.label} ({column.key})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <Label>Colonna codice *</Label>
                <Select
                  value={codeColumnKey || EMPTY_SELECT_VALUE}
                  onValueChange={(value) =>
                    setCodeColumnKey(value === EMPTY_SELECT_VALUE ? "" : value)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Codice" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={EMPTY_SELECT_VALUE}>Nessuna</SelectItem>
                    {returnColumns.map((column) => (
                      <SelectItem key={column.key} value={column.key}>
                        {column.label} ({column.key})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Colonna descrizione</Label>
                <Select
                  value={descriptionColumnKey || EMPTY_SELECT_VALUE}
                  onValueChange={(value) =>
                    setDescriptionColumnKey(value === EMPTY_SELECT_VALUE ? "" : value)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Descrizione" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={EMPTY_SELECT_VALUE}>Nessuna</SelectItem>
                    {returnColumns.map((column) => (
                      <SelectItem key={column.key} value={column.key}>
                        {column.label} ({column.key})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </>
          )}
          <div className="space-y-2">
            <Label>Colonna prezzo *</Label>
            <Select
              value={priceColumnKey || EMPTY_SELECT_VALUE}
              onValueChange={(value) =>
                setPriceColumnKey(value === EMPTY_SELECT_VALUE ? "" : value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Prezzo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={EMPTY_SELECT_VALUE}>Nessuna</SelectItem>
                {returnColumns.map((column) => (
                  <SelectItem key={column.key} value={column.key}>
                    {column.label} ({column.key})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Colonna quantità</Label>
            <Select
              value={quantityColumnKey || EMPTY_SELECT_VALUE}
              onValueChange={(value) =>
                setQuantityColumnKey(value === EMPTY_SELECT_VALUE ? "" : value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Quantità" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={EMPTY_SELECT_VALUE}>Nessuna</SelectItem>
                {returnColumns.map((column) => (
                  <SelectItem key={column.key} value={column.key}>
                    {column.label} ({column.key})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {renderConfigManagement()}
      </div>
    );
  };

  const renderConfigManagement = () => {
    return (
      <div className="space-y-3 rounded-lg border border-border/60 bg-muted/20 p-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <Label className="text-sm font-semibold">Configurazioni salvate (opzionali)</Label>
          <Button
            variant="ghost"
            size="sm"
            className="gap-2"
            onClick={() => refetchImportConfigs()}
            disabled={configsLoading}
          >
            <RefreshCw className={cn("h-4 w-4", configsLoading && "animate-spin")} />
            Aggiorna
          </Button>
        </div>
        <Select
          value={selectedConfigId}
          onValueChange={(value) => setSelectedConfigId(value)}
          disabled={configsLoading}
        >
          <SelectTrigger>
            <SelectValue
              placeholder={
                configsLoading
                  ? "Caricamento configurazioni..."
                  : "Seleziona una configurazione salvata"
              }
            />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={CONFIG_MANUAL_VALUE}>
              Nessuna configurazione (compila manualmente)
            </SelectItem>
            {importConfigs.map((config) => (
              <SelectItem key={config.id} value={String(config.id)}>
                {config.nome}
                {config.commessa_id ? "" : " · Globale"}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedConfig && (
          <p className="text-xs text-muted-foreground">
            Foglio: {selectedConfig.sheet_name ?? "—"} · Impresa predefinita:{" "}
            {selectedConfig.impresa ?? "—"}
          </p>
        )}
        <div className="space-y-3 rounded-md border border-dashed border-border/60 p-3">
          <p className="text-sm font-semibold">Salva configurazione attuale</p>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Nome configurazione</Label>
              <Input
                value={configSaveName}
                onChange={(event) => setConfigSaveName(event.target.value)}
                placeholder="Es. Formato EXA"
              />
            </div>
            <div className="space-y-1">
              <Label>Impresa associata (facoltativa)</Label>
              <Input
                value={configSaveImpresa}
                onChange={(event) => setConfigSaveImpresa(event.target.value)}
                placeholder="Lascia vuoto per usare l'impresa selezionata"
              />
            </div>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label>Note</Label>
              <Input
                value={configSaveNote}
                onChange={(event) => setConfigSaveNote(event.target.value)}
                placeholder='Es. Foglio "Ritorno_LC"'
              />
            </div>
            <div className="space-y-1">
              <Label>Ambito</Label>
              <Select
                value={configSaveScope}
                onValueChange={(value) => setConfigSaveScope(value as "commessa" | "global")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="commessa">Solo questa commessa</SelectItem>
                  <SelectItem value="global">Tutte le commesse</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-md border border-border/50 px-3 py-2">
            <Switch
              checked={configSaveIncludeColumns}
              onCheckedChange={(checked) => setConfigSaveIncludeColumns(Boolean(checked))}
            />
            <div className="text-xs">
              <p className="font-semibold">Includi la mappatura delle colonne</p>
              <p className="text-muted-foreground">
                Disattiva per non specificare i campi e sceglierli manualmente.
              </p>
            </div>
          </div>
          <Button
            onClick={handleSaveConfig}
            disabled={saveConfigMutation.isPending || !configSaveName.trim()}
          >
            {saveConfigMutation.isPending ? "Salvataggio..." : "Salva configurazione"}
          </Button>
        </div>
      </div>
    );
  };

  const renderStatusStep = () => {
    const statusLabel =
      uploadState === "uploading"
        ? "Importazione in corso..."
        : uploadState === "success"
        ? "Importazione completata"
        : uploadState === "error"
        ? "Si è verificato un errore"
        : "Pronto a iniziare";
    const showProgress = uploadState !== "idle";
    const roundedProgress = Math.round(progressValue);

    return (
      <div className="space-y-3 py-4">
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">{statusLabel}</p>
          {showProgress && (
            <div className="space-y-1">
              <Progress value={progressValue} className="h-2" />
              <div className="text-right text-xs text-muted-foreground">
                {uploadState === "uploading" ? `${roundedProgress}%` : "100%"}
              </div>
            </div>
          )}
        </div>
        <div className="rounded-md border bg-muted/20 p-3 text-xs">
          {uploadLog.map((entry, idx) => (
            <p key={idx}>{entry}</p>
          ))}
          {uploadError && <p className="text-destructive">{uploadError}</p>}
        </div>
      </div>
    );
  };

  const renderStep = () => {
    if (wizardStep === "kind") return renderKindStep();
    if (wizardStep === "upload") return renderUploadStep();
    if (wizardStep === "config") return renderConfigStep();
    return renderStatusStep();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={mergedTriggerDisabled}
          {...restTriggerProps}
          className={cn("gap-2", triggerClassName)}
        >
          <Upload className="h-4 w-4" />
          Importa computo
        </Button>
      </DialogTrigger>
      <DialogContent className="flex max-h-[90vh] max-w-3xl flex-col overflow-hidden">
        <DialogHeader>
          <DialogTitle>Wizard importazione computi</DialogTitle>
          <DialogDescription>
            Seleziona il tipo di file, carica il documento e configura l’importazione
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-wrap items-center gap-3 py-2 text-sm">
          {WIZARD_STEPS.map((step, index) => {
            const active = wizardStep === step.id;
            const completed =
              WIZARD_STEPS.findIndex((s) => s.id === step.id) <
              WIZARD_STEPS.findIndex((s) => s.id === wizardStep);
            return (
              <div key={step.id} className="flex items-center gap-2">
                <div
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border",
                    active && "border-primary bg-primary text-primary-foreground",
                    completed && !active && "bg-muted text-muted-foreground",
                  )}
                >
                  {index + 1}
                </div>
                <span className={active ? "font-medium" : "text-muted-foreground"}>
                  {step.label}
                </span>
                {index !== WIZARD_STEPS.length - 1 && (
                  <div className="w-12 border-t border-dashed border-muted" />
                )}
              </div>
            );
          })}
        </div>

        <div className="flex-1 overflow-y-auto pr-1">{renderStep()}</div>

        <div className="flex justify-between pt-4">
          <Button variant="ghost" onClick={handlePrevious} disabled={wizardStep === "kind"}>
            Indietro
          </Button>
          {wizardStep === "config" ? (
            <Button onClick={handleUpload} disabled={!canSubmit}>
              Avvia importazione
            </Button>
          ) : wizardStep === "status" ? (
            <Button onClick={() => setOpen(false)} disabled={uploadState === "uploading"}>
              Chiudi
            </Button>
          ) : (
            <Button
              onClick={handleNext}
              disabled={
                wizardStep === "kind"
                  ? !canProceedFromKind
                  : wizardStep === "upload" && !canProceedFromUpload
              }
            >
              Continua
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

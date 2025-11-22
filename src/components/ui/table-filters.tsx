/**
 * TableFilters - Componenti filtro riutilizzabili per tabelle
 * Include RangeFilter, SearchFilter, SelectFilter, DateFilter
 */

import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, X, SlidersHorizontal, Calendar, Filter } from "lucide-react";

// ============= SEARCH FILTER =============

export interface SearchFilterProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  debounceMs?: number;
}

export function SearchFilter({
  value,
  onChange,
  placeholder = "Cerca...",
  className,
  debounceMs = 300,
}: SearchFilterProps) {
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (localValue !== value) {
        onChange(localValue);
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [localValue, value, onChange, debounceMs]);

  return (
    <div className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder={placeholder}
        className="pl-9 pr-9 h-9"
      />
      {localValue && (
        <button
          onClick={() => {
            setLocalValue("");
            onChange("");
          }}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

// ============= RANGE FILTER =============

export interface RangeFilterProps {
  label: string;
  min: number;
  max: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
  step?: number;
  formatValue?: (value: number) => string;
  className?: string;
}

export function RangeFilter({
  label,
  min,
  max,
  value,
  onChange,
  step = 1,
  formatValue = (v) => v.toLocaleString("it-IT"),
  className,
}: RangeFilterProps) {
  const [localValue, setLocalValue] = useState(value);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const handleApply = () => {
    onChange(localValue);
    setIsOpen(false);
  };

  const handleReset = () => {
    const resetValue: [number, number] = [min, max];
    setLocalValue(resetValue);
    onChange(resetValue);
    setIsOpen(false);
  };

  const isFiltered = value[0] !== min || value[1] !== max;

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={isFiltered ? "secondary" : "outline"}
          size="sm"
          className={cn("h-9 gap-1.5", className)}
        >
          <SlidersHorizontal className="h-4 w-4" />
          {label}
          {isFiltered && (
            <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-[10px]">
              {formatValue(value[0])} - {formatValue(value[1])}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">{label}</span>
              <span className="text-muted-foreground">
                {formatValue(localValue[0])} - {formatValue(localValue[1])}
              </span>
            </div>
            <Slider
              value={localValue}
              min={min}
              max={max}
              step={step}
              onValueChange={(v) => setLocalValue(v as [number, number])}
              className="py-2"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{formatValue(min)}</span>
              <span>{formatValue(max)}</span>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="flex-1"
            >
              Reset
            </Button>
            <Button
              size="sm"
              onClick={handleApply}
              className="flex-1"
            >
              Applica
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// ============= SELECT FILTER =============

export interface SelectFilterOption {
  value: string;
  label: string;
  count?: number;
}

export interface SelectFilterProps {
  label: string;
  options: SelectFilterOption[];
  value: string | null;
  onChange: (value: string | null) => void;
  placeholder?: string;
  allLabel?: string;
  className?: string;
}

export function SelectFilter({
  label,
  options,
  value,
  onChange,
  placeholder = "Seleziona...",
  allLabel = "Tutti",
  className,
}: SelectFilterProps) {
  return (
    <Select
      value={value || "all"}
      onValueChange={(v) => onChange(v === "all" ? null : v)}
    >
      <SelectTrigger className={cn("h-9 w-[180px]", className)}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">{allLabel}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
            {option.count !== undefined && (
              <span className="ml-2 text-muted-foreground">({option.count})</span>
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

// ============= MULTI SELECT FILTER =============

export interface MultiSelectFilterProps {
  label: string;
  options: SelectFilterOption[];
  value: string[];
  onChange: (value: string[]) => void;
  className?: string;
}

export function MultiSelectFilter({
  label,
  options,
  value,
  onChange,
  className,
}: MultiSelectFilterProps) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOption = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      onChange([...value, optionValue]);
    }
  };

  const handleSelectAll = () => {
    onChange(options.map((o) => o.value));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant={value.length > 0 ? "secondary" : "outline"}
          size="sm"
          className={cn("h-9 gap-1.5", className)}
        >
          <Filter className="h-4 w-4" />
          {label}
          {value.length > 0 && (
            <Badge variant="secondary" className="ml-1 px-1.5 py-0 text-[10px]">
              {value.length}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56" align="start">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">{label}</span>
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSelectAll}
                className="h-6 px-2 text-xs"
              >
                Tutti
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearAll}
                className="h-6 px-2 text-xs"
              >
                Nessuno
              </Button>
            </div>
          </div>

          <div className="space-y-1 max-h-48 overflow-y-auto">
            {options.map((option) => (
              <label
                key={option.value}
                className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-muted cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={value.includes(option.value)}
                  onChange={() => toggleOption(option.value)}
                  className="rounded border-border"
                />
                <span className="text-sm flex-1">{option.label}</span>
                {option.count !== undefined && (
                  <span className="text-xs text-muted-foreground">
                    {option.count}
                  </span>
                )}
              </label>
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// ============= TOGGLE FILTER =============

export interface ToggleFilterOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

export interface ToggleFilterProps {
  options: ToggleFilterOption[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

export function ToggleFilter({
  options,
  value,
  onChange,
  className,
}: ToggleFilterProps) {
  return (
    <div className={cn("flex gap-1 p-1 bg-muted/50 rounded-lg", className)}>
      {options.map((option) => (
        <Button
          key={option.value}
          variant={value === option.value ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onChange(option.value)}
          className="h-7 gap-1.5"
        >
          {option.icon}
          {option.label}
        </Button>
      ))}
    </div>
  );
}

// ============= QUICK FILTERS =============

export interface QuickFilter {
  id: string;
  label: string;
  filter: () => void;
  isActive?: boolean;
}

export interface QuickFiltersProps {
  filters: QuickFilter[];
  className?: string;
}

export function QuickFilters({ filters, className }: QuickFiltersProps) {
  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      {filters.map((filter) => (
        <Button
          key={filter.id}
          variant={filter.isActive ? "default" : "outline"}
          size="sm"
          onClick={filter.filter}
          className="h-8 rounded-full"
        >
          {filter.label}
        </Button>
      ))}
    </div>
  );
}

// ============= FILTER SUMMARY =============

export interface FilterSummaryProps {
  total: number;
  filtered: number;
  label?: string;
  className?: string;
}

export function FilterSummary({
  total,
  filtered,
  label = "righe",
  className,
}: FilterSummaryProps) {
  const isFiltered = filtered !== total;

  return (
    <span className={cn("text-sm text-muted-foreground", className)}>
      {isFiltered ? (
        <>
          <span className="font-medium text-foreground">
            {filtered.toLocaleString("it-IT")}
          </span>
          {" "}di{" "}
          <span>{total.toLocaleString("it-IT")}</span>
          {" "}{label}
        </>
      ) : (
        <>
          <span className="font-medium text-foreground">
            {total.toLocaleString("it-IT")}
          </span>
          {" "}{label}
        </>
      )}
    </span>
  );
}

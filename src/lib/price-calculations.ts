/**
 * Utility functions for price calculations and statistics
 * Used across ConfrontoOfferte, ElencoPrezziNew, GraficiAnalisi, etc.
 */

// ============= TYPES =============

export interface PriceStats {
  average: number;
  min: number;
  max: number;
  stdDev: number;
  count: number;
  sum: number;
}

export interface DeltaResult {
  value: number;
  percentage: number;
  isPositive: boolean;
  isNegative: boolean;
  isZero: boolean;
}

export interface OfferPrice {
  price: number | null | undefined;
  quantity?: number | null;
  impresa?: string;
  roundNumber?: number;
}

// ============= BASIC CALCULATIONS =============

/**
 * Calculate sum of numeric values, filtering out nulls/NaN
 */
export const sumValues = (values: (number | null | undefined)[]): number => {
  return values.reduce((sum, val) => {
    if (val != null && !Number.isNaN(val)) {
      return sum + val;
    }
    return sum;
  }, 0);
};

/**
 * Filter valid numeric values from array
 */
export const filterValidNumbers = (values: (number | null | undefined)[]): number[] => {
  return values.filter((val): val is number =>
    val != null && !Number.isNaN(val) && Number.isFinite(val)
  );
};

/**
 * Calculate average of numeric values
 */
export const calculateAverage = (values: (number | null | undefined)[]): number => {
  const validValues = filterValidNumbers(values);
  if (validValues.length === 0) return 0;
  return sumValues(validValues) / validValues.length;
};

/**
 * Calculate minimum value
 */
export const calculateMin = (values: (number | null | undefined)[]): number => {
  const validValues = filterValidNumbers(values);
  if (validValues.length === 0) return 0;
  return Math.min(...validValues);
};

/**
 * Calculate maximum value
 */
export const calculateMax = (values: (number | null | undefined)[]): number => {
  const validValues = filterValidNumbers(values);
  if (validValues.length === 0) return 0;
  return Math.max(...validValues);
};

/**
 * Calculate standard deviation
 */
export const calculateStdDev = (values: (number | null | undefined)[]): number => {
  const validValues = filterValidNumbers(values);
  if (validValues.length < 2) return 0;

  const avg = calculateAverage(validValues);
  const squaredDiffs = validValues.map((val) => Math.pow(val - avg, 2));
  const avgSquaredDiff = sumValues(squaredDiffs) / validValues.length;

  return Math.sqrt(avgSquaredDiff);
};

// ============= PRICE STATISTICS =============

/**
 * Calculate comprehensive price statistics
 */
export const calculatePriceStats = (prices: (number | null | undefined)[]): PriceStats => {
  const validPrices = filterValidNumbers(prices);

  if (validPrices.length === 0) {
    return {
      average: 0,
      min: 0,
      max: 0,
      stdDev: 0,
      count: 0,
      sum: 0,
    };
  }

  const sum = sumValues(validPrices);
  const average = sum / validPrices.length;
  const min = Math.min(...validPrices);
  const max = Math.max(...validPrices);
  const stdDev = calculateStdDev(validPrices);

  return {
    average,
    min,
    max,
    stdDev,
    count: validPrices.length,
    sum,
  };
};

/**
 * Calculate stats from array of offer prices
 */
export const calculateOfferStats = (offers: OfferPrice[]): PriceStats => {
  const prices = offers.map((o) => o.price);
  return calculatePriceStats(prices);
};

// ============= DELTA CALCULATIONS =============

/**
 * Calculate delta between two values
 */
export const calculateDelta = (
  current: number | null | undefined,
  reference: number | null | undefined
): DeltaResult => {
  const curr = current ?? 0;
  const ref = reference ?? 0;
  const value = curr - ref;
  const percentage = ref !== 0 ? ((curr - ref) / ref) * 100 : 0;

  return {
    value,
    percentage,
    isPositive: value > 0,
    isNegative: value < 0,
    isZero: value === 0,
  };
};

/**
 * Calculate percentage difference
 */
export const calculatePercentageDelta = (
  value: number | null | undefined,
  reference: number | null | undefined
): number => {
  if (reference == null || reference === 0) return 0;
  if (value == null) return 0;
  return ((value - reference) / reference) * 100;
};

/**
 * Calculate delta from average (how far from mean)
 */
export const calculateDeltaFromAverage = (
  value: number | null | undefined,
  average: number
): DeltaResult => {
  return calculateDelta(value, average);
};

// ============= PRICE COMPARISONS =============

/**
 * Find best (lowest) price from offers
 */
export const findBestPrice = (offers: OfferPrice[]): {
  price: number;
  impresa?: string;
  roundNumber?: number;
} | null => {
  const validOffers = offers.filter(
    (o) => o.price != null && !Number.isNaN(o.price)
  );

  if (validOffers.length === 0) return null;

  const best = validOffers.reduce((min, curr) =>
    (curr.price ?? Infinity) < (min.price ?? Infinity) ? curr : min
  );

  return {
    price: best.price ?? 0,
    impresa: best.impresa,
    roundNumber: best.roundNumber,
  };
};

/**
 * Find worst (highest) price from offers
 */
export const findWorstPrice = (offers: OfferPrice[]): {
  price: number;
  impresa?: string;
  roundNumber?: number;
} | null => {
  const validOffers = offers.filter(
    (o) => o.price != null && !Number.isNaN(o.price)
  );

  if (validOffers.length === 0) return null;

  const worst = validOffers.reduce((max, curr) =>
    (curr.price ?? -Infinity) > (max.price ?? -Infinity) ? curr : max
  );

  return {
    price: worst.price ?? 0,
    impresa: worst.impresa,
    roundNumber: worst.roundNumber,
  };
};

/**
 * Rank offers by price (ascending - lowest first)
 */
export const rankOffersByPrice = (offers: OfferPrice[]): (OfferPrice & { rank: number })[] => {
  const validOffers = offers.filter(
    (o) => o.price != null && !Number.isNaN(o.price)
  );

  return validOffers
    .sort((a, b) => (a.price ?? 0) - (b.price ?? 0))
    .map((offer, index) => ({
      ...offer,
      rank: index + 1,
    }));
};

// ============= TOTALS CALCULATIONS =============

/**
 * Calculate total amount (price * quantity)
 */
export const calculateAmount = (
  price: number | null | undefined,
  quantity: number | null | undefined
): number => {
  if (price == null || quantity == null) return 0;
  return price * quantity;
};

/**
 * Calculate weighted average price
 */
export const calculateWeightedAverage = (
  items: { price: number | null | undefined; weight: number | null | undefined }[]
): number => {
  let totalWeight = 0;
  let weightedSum = 0;

  items.forEach((item) => {
    if (item.price != null && item.weight != null) {
      totalWeight += item.weight;
      weightedSum += item.price * item.weight;
    }
  });

  if (totalWeight === 0) return 0;
  return weightedSum / totalWeight;
};

// ============= FORMATTING HELPERS =============

/**
 * Format price delta for display with sign
 */
export const formatDeltaWithSign = (value: number): string => {
  if (value === 0) return "0%";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
};

/**
 * Get delta color class based on value
 * Positive delta (higher price) = red (bad)
 * Negative delta (lower price) = green (good)
 */
export const getDeltaColorClass = (
  value: number | null | undefined,
  options?: { invertColors?: boolean }
): string => {
  if (value == null || value === 0) return "text-muted-foreground";

  const isGood = options?.invertColors ? value > 0 : value < 0;

  if (isGood) {
    return "text-green-600 dark:text-green-400";
  }
  return "text-red-600 dark:text-red-400";
};

/**
 * Get delta badge variant
 */
export const getDeltaBadgeVariant = (
  value: number | null | undefined
): "default" | "destructive" | "secondary" => {
  if (value == null || Math.abs(value) < 0.01) return "secondary";
  return value > 0 ? "destructive" : "default";
};

// ============= VALIDATION =============

/**
 * Check if price is valid
 */
export const isValidPrice = (value: unknown): value is number => {
  return typeof value === "number" && !Number.isNaN(value) && Number.isFinite(value) && value >= 0;
};

/**
 * Parse price input (supports EUR format, comma/dot separators)
 */
export const parsePriceInput = (input: unknown): number | null => {
  if (input == null) return null;
  if (typeof input === "number") {
    return Number.isFinite(input) ? input : null;
  }

  const raw = String(input).trim();
  if (!raw) return null;

  // Remove currency symbols and whitespace
  let sanitized = raw.replace(/\s/g, "").replace(/[€$]/g, "");
  sanitized = sanitized.replace(/[^0-9.,-]/g, "");
  if (!sanitized) return null;

  // Handle European vs US number format
  const commaIndex = sanitized.lastIndexOf(",");
  const dotIndex = sanitized.lastIndexOf(".");

  if (commaIndex !== -1 && dotIndex !== -1) {
    if (commaIndex > dotIndex) {
      // European: 1.234,56
      sanitized = sanitized.replace(/\./g, "");
      sanitized = sanitized.replace(",", ".");
    } else {
      // US: 1,234.56
      sanitized = sanitized.replace(/,/g, "");
    }
  } else if (commaIndex !== -1) {
    // Only comma: assume decimal separator
    sanitized = sanitized.replace(/\./g, "");
    sanitized = sanitized.replace(",", ".");
  } else {
    // Only dots or no separator
    sanitized = sanitized.replace(/,/g, "");
  }

  const parsed = Number(sanitized);
  return Number.isFinite(parsed) ? parsed : null;
};

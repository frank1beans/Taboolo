export const WBS_LEVELS = [1, 2, 3, 4, 5, 6, 7] as const;

export const WBS_LEVEL_TITLES: Record<(typeof WBS_LEVELS)[number], string> = {
  1: "WBS 1 - Lotto/Edificio",
  2: "WBS 2 - Livelli",
  3: "WBS 3 - Ambiti omogenei",
  4: "WBS 4 - Appalto / Fase",
  5: "WBS 5 - Elementi funzionali",
  6: "WBS 6 - Categorie merceologiche",
  7: "WBS 7 - Raggruppatori EPU",
};

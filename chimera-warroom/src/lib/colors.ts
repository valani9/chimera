export const COLORS = {
  bg:       "#000000",
  surface:  "#0a0a0a",
  surface2: "#111111",
  border:   "rgba(255,255,255,0.07)",
  border2:  "rgba(255,255,255,0.13)",

  text:  "#ffffff",
  text2: "#888888",
  text3: "#333333",

  green: "#22c55e",
  red:   "#ef4444",
  amber: "#f59e0b",

  // Agent colors — kept for debate panel
  bull:       "#22c55e",
  bear:       "#ef4444",
  historian:  "#f59e0b",
  contrarian: "#a855f7",
  quant:      "#06b6d4",
  judge:      "#f5f5f5",
} as const;

export const PHASE_COLORS: Record<string, string> = {
  ORACLE:   "#888888",
  HYDRA:    "#a855f7",
  RIPPLE:   "#22c55e",
  PREDATOR: "#ef4444",
  FUSION:   "#f5f5f5",
  EXECUTE:  "#22c55e",
};

export const AGENT_COLORS: Record<string, string> = {
  Bull:       COLORS.bull,
  Bear:       COLORS.bear,
  Historian:  COLORS.historian,
  Contrarian: COLORS.contrarian,
  Quant:      COLORS.quant,
  Judge:      COLORS.judge,
};

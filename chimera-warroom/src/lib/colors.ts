export const COLORS = {
  bg: "#0a0a0f",
  panelBg: "#111118",
  panelBorder: "#1e1e2e",
  glass: "rgba(17, 17, 24, 0.7)",

  textPrimary: "#e4e4e7",
  textSecondary: "#71717a",
  textDim: "#3f3f46",

  cyan: "#06b6d4",
  purple: "#a855f7",
  green: "#22c55e",
  red: "#ef4444",
  amber: "#f59e0b",
  gold: "#eab308",
  blue: "#3b82f6",

  // Agent colors
  bull: "#22c55e",
  bear: "#ef4444",
  historian: "#f59e0b",
  contrarian: "#a855f7",
  quant: "#06b6d4",
  judge: "#eab308",
} as const;

export const PHASE_COLORS: Record<string, string> = {
  ORACLE: COLORS.cyan,
  HYDRA: COLORS.purple,
  RIPPLE: COLORS.green,
  PREDATOR: COLORS.red,
  FUSION: COLORS.gold,
  EXECUTE: "#ffffff",
};

export const AGENT_COLORS: Record<string, string> = {
  Bull: COLORS.bull,
  Bear: COLORS.bear,
  Historian: COLORS.historian,
  Contrarian: COLORS.contrarian,
  Quant: COLORS.quant,
  Judge: COLORS.judge,
};

import { create } from "zustand";
import type {
  Signal, WaterfallStep, DebateResult, GraphData,
  TradeDecision, PortfolioSummary, Scenario,
} from "./types";

interface ChimeraStore {
  // Mode
  mode: "live" | "replay";
  setMode: (mode: "live" | "replay") => void;

  // Replay state
  replayStartTime: number;
  replaySpeed: number;
  replayPaused: boolean;
  activeScenario: Scenario | null;
  setReplaySpeed: (speed: number) => void;
  toggleReplayPause: () => void;
  startReplay: (scenario: Scenario) => void;

  // Data
  signals: Signal[];
  waterfall: WaterfallStep[];
  debates: DebateResult[];
  graph: GraphData;
  trades: TradeDecision[];
  portfolio: PortfolioSummary;
  rippleActiveNodes: Set<string>;

  // Actions
  addSignal: (signal: Signal) => void;
  addWaterfallStep: (step: WaterfallStep) => void;
  setDebates: (debates: DebateResult[]) => void;
  setGraph: (graph: GraphData) => void;
  addTrade: (trade: TradeDecision) => void;
  setPortfolio: (portfolio: PortfolioSummary) => void;
  triggerRipple: (nodeId: string) => void;

  // Computed replay elapsed
  getElapsedMs: () => number;
}

export const useChimeraStore = create<ChimeraStore>((set, get) => ({
  mode: "replay",
  setMode: (mode) => set({ mode }),

  replayStartTime: 0,
  replaySpeed: 1,
  replayPaused: false,
  activeScenario: null,
  setReplaySpeed: (speed) => set({ replaySpeed: speed }),
  toggleReplayPause: () => set((s) => ({ replayPaused: !s.replayPaused })),
  startReplay: (scenario) =>
    set({
      activeScenario: scenario,
      replayStartTime: Date.now(),
      replayPaused: false,
      signals: [],
      waterfall: [],
      debates: [],
      trades: [],
      rippleActiveNodes: new Set(),
      graph: scenario.graph,
      portfolio: {
        bankroll: 1000,
        total_pnl: 0,
        trade_count: 0,
        win_rate: 0,
        max_drawdown: 0,
        active_positions: 0,
      },
    }),

  signals: [],
  waterfall: [],
  debates: [],
  graph: { nodes: [], edges: [] },
  trades: [],
  portfolio: {
    bankroll: 1000,
    total_pnl: 0,
    trade_count: 0,
    win_rate: 0,
    max_drawdown: 0,
    active_positions: 0,
  },
  rippleActiveNodes: new Set(),

  addSignal: (signal) => set((s) => ({ signals: [...s.signals, signal] })),
  addWaterfallStep: (step) => set((s) => ({ waterfall: [...s.waterfall, step] })),
  setDebates: (debates) => set({ debates }),
  setGraph: (graph) => set({ graph }),
  addTrade: (trade) =>
    set((s) => ({
      trades: [...s.trades, trade],
      portfolio: {
        ...s.portfolio,
        trade_count: s.portfolio.trade_count + 1,
        total_pnl: s.portfolio.total_pnl + trade.edge * trade.bet_amount,
        bankroll: s.portfolio.bankroll + trade.edge * trade.bet_amount,
      },
    })),
  setPortfolio: (portfolio) => set({ portfolio }),
  triggerRipple: (nodeId) =>
    set((s) => {
      const newSet = new Set(s.rippleActiveNodes);
      newSet.add(nodeId);
      return { rippleActiveNodes: newSet };
    }),

  getElapsedMs: () => {
    const s = get();
    if (s.replayPaused) return 0;
    return (Date.now() - s.replayStartTime) * s.replaySpeed;
  },
}));

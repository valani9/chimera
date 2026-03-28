import { create } from "zustand";
import type { Scenario } from "./types";
import type { TerminalLine } from "./terminalLines";

interface ChimeraStore {
  // Replay state
  mode: "live" | "replay";
  replayStartTime: number;
  replaySpeed: number;
  replayPaused: boolean;
  activeScenario: Scenario | null;

  // Terminal output
  lines: TerminalLine[];

  // Actions
  setReplaySpeed: (speed: number) => void;
  toggleReplayPause: () => void;
  startReplay: (scenario: Scenario) => void;
  addLine: (line: TerminalLine) => void;
  clearLines: () => void;
}

export const useChimeraStore = create<ChimeraStore>((set) => ({
  mode: "replay",
  replayStartTime: 0,
  replaySpeed: 1,
  replayPaused: false,
  activeScenario: null,
  lines: [],

  setReplaySpeed: (speed) => set({ replaySpeed: speed }),
  toggleReplayPause: () => set((s) => ({ replayPaused: !s.replayPaused })),

  startReplay: (scenario) =>
    set({
      activeScenario: scenario,
      replayStartTime: Date.now(),
      replayPaused: false,
      lines: [],
    }),

  addLine: (line) => set((s) => ({ lines: [...s.lines, line] })),
  clearLines: () => set({ lines: [] }),
}));

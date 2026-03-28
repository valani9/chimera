"use client";

import { useChimeraStore } from "@/lib/store";
import { ukraineScenario, tariffShockScenario } from "@/lib/scenario";

const SCENARIOS = [
  { key: "ukraine-signal", label: "Ukraine Signal", scenario: ukraineScenario },
  { key: "tariff-shock", label: "Tariff Shock", scenario: tariffShockScenario },
];

export function Header() {
  const { mode, replaySpeed, replayPaused, setReplaySpeed, toggleReplayPause, signals, trades, portfolio, activeScenario, startReplay } =
    useChimeraStore();

  return (
    <div className="warroom-header glass-panel flex items-center justify-between px-4" style={{ borderRadius: 0 }}>
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        <div className="text-xl font-bold tracking-wider">
          <span style={{ color: "#06b6d4" }}>CHI</span>
          <span style={{ color: "#a855f7" }}>ME</span>
          <span style={{ color: "#22c55e" }}>RA</span>
        </div>
        <span className="text-xs text-zinc-500 hidden sm:inline">WAR ROOM</span>
      </div>

      {/* Center: Subsystem status */}
      <div className="flex items-center gap-4 text-xs mono">
        {["ORACLE", "HYDRA", "RIPPLE", "PREDATOR"].map((sys, i) => (
          <div key={sys} className="flex items-center gap-1.5">
            <div
              className="w-2 h-2 rounded-full pulse-dot"
              style={{
                backgroundColor: ["#06b6d4", "#a855f7", "#22c55e", "#ef4444"][i],
              }}
            />
            <span className="text-zinc-400">{sys}</span>
          </div>
        ))}
      </div>

      {/* Right: Mode + stats */}
      <div className="flex items-center gap-4 text-xs">
        {/* Scenario selector */}
        <div className="flex items-center gap-1">
          {SCENARIOS.map(({ key, label, scenario }) => (
            <button
              key={key}
              onClick={() => startReplay(scenario)}
              className={`px-2 py-0.5 rounded text-xs mono transition-colors ${
                activeScenario?.id === key
                  ? "text-amber-400 border border-amber-500/40"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
              style={{ background: activeScenario?.id === key ? "#1e1a00" : "transparent" }}
            >
              {label}
            </button>
          ))}
        </div>

        {mode === "replay" && (
          <div className="flex items-center gap-2">
            <button
              onClick={toggleReplayPause}
              className="px-2 py-0.5 rounded text-zinc-300 hover:text-white"
              style={{ background: "#1e1e2e" }}
            >
              {replayPaused ? "▶" : "⏸"}
            </button>
            {[1, 2, 5].map((s) => (
              <button
                key={s}
                onClick={() => setReplaySpeed(s)}
                className={`px-1.5 py-0.5 rounded mono ${replaySpeed === s ? "text-cyan-400" : "text-zinc-500"}`}
                style={{ background: replaySpeed === s ? "#1e1e3e" : "transparent" }}
              >
                {s}x
              </button>
            ))}
          </div>
        )}

        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full pulse-dot`} style={{ backgroundColor: mode === "live" ? "#22c55e" : "#f59e0b" }} />
          <span className="text-zinc-400">{mode === "live" ? "LIVE" : "REPLAY"}</span>
        </div>

        <span className="text-zinc-500">Signals: <span className="text-zinc-300">{signals.length}</span></span>
        <span className="text-zinc-500">Trades: <span className="text-zinc-300">{trades.length}</span></span>
        <span className={`mono font-semibold ${portfolio.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
          ${portfolio.total_pnl >= 0 ? "+" : ""}{portfolio.total_pnl.toFixed(2)}
        </span>
      </div>
    </div>
  );
}

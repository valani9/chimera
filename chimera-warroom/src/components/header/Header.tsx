"use client";

import { useChimeraStore } from "@/lib/store";
import { ukraineScenario, tariffShockScenario } from "@/lib/scenario";

const SCENARIOS = [
  { key: "ukraine-signal", label: "Ukraine Signal", scenario: ukraineScenario },
  { key: "tariff-shock",   label: "Tariff Shock",   scenario: tariffShockScenario },
];

const SUBSYSTEMS = ["ORACLE", "HYDRA", "RIPPLE", "PREDATOR"];

export function Header() {
  const {
    mode, replaySpeed, replayPaused,
    setReplaySpeed, toggleReplayPause,
    signals, trades, portfolio,
    activeScenario, startReplay,
  } = useChimeraStore();

  const pnl = portfolio.total_pnl;

  return (
    <header
      className="warroom-header"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 20px",
        borderBottom: "1px solid var(--border)",
        height: "56px",
      }}
    >
      {/* Wordmark */}
      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        <span
          style={{
            fontWeight: 600,
            fontSize: 15,
            letterSpacing: "0.12em",
            color: "var(--text)",
          }}
        >
          CHIMERA
        </span>

        {/* Subsystem status */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {SUBSYSTEMS.map((sys) => (
            <div key={sys} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div className="status-dot" />
              <span className="label">{sys}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Center: scenario selector */}
      <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
        {SCENARIOS.map(({ key, label, scenario }) => {
          const active = activeScenario?.id === key;
          return (
            <button
              key={key}
              onClick={() => startReplay(scenario)}
              style={{
                padding: "4px 12px",
                fontSize: 11,
                fontWeight: 500,
                letterSpacing: "0.04em",
                color: active ? "var(--text)" : "var(--text-2)",
                background: "transparent",
                border: "none",
                borderBottom: active ? "1px solid var(--text)" : "1px solid transparent",
                cursor: "pointer",
                transition: "color 0.15s, border-color 0.15s",
              }}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Right: controls + stats */}
      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        {/* Replay controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button
            onClick={toggleReplayPause}
            style={{
              width: 24,
              height: 24,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 11,
              color: "var(--text-2)",
              background: "var(--surface-2)",
              border: "1px solid var(--border)",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            {replayPaused ? "▶" : "⏸"}
          </button>
          {[1, 2, 5].map((s) => (
            <button
              key={s}
              onClick={() => setReplaySpeed(s)}
              style={{
                padding: "2px 6px",
                fontSize: 11,
                fontFamily: "inherit",
                color: replaySpeed === s ? "var(--text)" : "var(--text-3)",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                fontWeight: replaySpeed === s ? 600 : 400,
              }}
            >
              {s}×
            </button>
          ))}
        </div>

        {/* Stats */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
            <span className="label">Signals</span>
            <span className="mono" style={{ fontSize: 12, color: "var(--text)" }}>{signals.length}</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
            <span className="label">Trades</span>
            <span className="mono" style={{ fontSize: 12, color: "var(--text)" }}>{trades.length}</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end" }}>
            <span className="label">P&amp;L</span>
            <span
              className="mono"
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: pnl >= 0 ? "var(--green)" : "var(--red)",
              }}
            >
              {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Mode badge */}
        <div
          style={{
            padding: "3px 8px",
            fontSize: 10,
            fontWeight: 500,
            letterSpacing: "0.08em",
            color: mode === "live" ? "var(--green)" : "var(--text-2)",
            border: `1px solid ${mode === "live" ? "var(--green)" : "var(--border)"}`,
            borderRadius: 3,
          }}
        >
          {mode === "live" ? "LIVE" : "REPLAY"}
        </div>
      </div>
    </header>
  );
}

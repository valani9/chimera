"use client";

import { useEffect, useRef } from "react";
import { useChimeraStore } from "@/lib/store";
import { ukraineScenario, tariffShockScenario } from "@/lib/scenario";
import { scenarioToTerminalLines } from "@/lib/terminalLines";
import type { Scenario } from "@/lib/types";

const SCENARIOS: { key: string; label: string; scenario: Scenario }[] = [
  { key: "ukraine-signal", label: "ukraine-signal", scenario: ukraineScenario },
  { key: "tariff-shock",   label: "tariff-shock",   scenario: tariffShockScenario },
];

export default function TerminalPage() {
  const store = useChimeraStore();
  const bodyRef = useRef<HTMLDivElement>(null);
  const tickRef = useRef<ReturnType<typeof setInterval>>(null);
  const processedRef = useRef<Set<string>>(new Set());
  const linesRef = useRef(scenarioToTerminalLines(ukraineScenario));

  // Start on mount
  useEffect(() => {
    linesRef.current = scenarioToTerminalLines(ukraineScenario);
    store.startReplay(ukraineScenario);
    processedRef.current = new Set();
  }, []);

  // Reset on scenario change
  useEffect(() => {
    if (!store.activeScenario) return;
    linesRef.current = scenarioToTerminalLines(store.activeScenario);
    processedRef.current = new Set();
  }, [store.activeScenario?.id]);

  // Auto-scroll to bottom when lines are added
  useEffect(() => {
    const el = bodyRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [store.lines.length]);

  // Replay tick engine
  useEffect(() => {
    const scenario = store.activeScenario;
    if (!scenario || store.mode !== "replay") return;

    tickRef.current = setInterval(() => {
      if (store.replayPaused) return;
      const elapsed = (Date.now() - store.replayStartTime) * store.replaySpeed;

      linesRef.current.forEach((tl) => {
        if (!processedRef.current.has(tl.id) && elapsed >= tl.offsetMs) {
          processedRef.current.add(tl.id);
          store.addLine(tl);
        }
      });
    }, 50);

    return () => { if (tickRef.current) clearInterval(tickRef.current); };
  }, [store.activeScenario, store.mode, store.replayPaused, store.replaySpeed, store.replayStartTime]);

  const handleScenario = (s: Scenario) => {
    linesRef.current = scenarioToTerminalLines(s);
    store.startReplay(s);
    processedRef.current = new Set();
  };

  const lastLine = store.lines[store.lines.length - 1];
  const showCursor = lastLine?.type === "prompt";

  return (
    <div className="terminal-backdrop">
      <div className="terminal-window">

        {/* Title bar */}
        <div className="terminal-titlebar">
          {/* macOS dots */}
          <div className="titlebar-dots">
            <div className="titlebar-dot" style={{ background: "#ff5f56" }} />
            <div className="titlebar-dot" style={{ background: "#ffbd2e" }} />
            <div className="titlebar-dot" style={{ background: "#27c93f" }} />
          </div>

          {/* Center: title */}
          <div className="titlebar-title">chimera — zsh</div>

          {/* Right: controls */}
          <div className="titlebar-controls">
            {/* Scenario picker */}
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              {SCENARIOS.map(({ key, label, scenario }) => {
                const active = store.activeScenario?.id === key;
                return (
                  <button
                    key={key}
                    onClick={() => handleScenario(scenario)}
                    style={{
                      fontSize: 11,
                      color: active ? "#e5e5e5" : "#444",
                      background: "transparent",
                      border: "none",
                      cursor: "pointer",
                      fontFamily: "inherit",
                      padding: 0,
                      transition: "color 0.15s",
                    }}
                  >
                    {label}
                  </button>
                );
              })}
            </div>

            {/* Divider */}
            <div style={{ width: 1, height: 14, background: "#222" }} />

            {/* Replay controls */}
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button
                onClick={store.toggleReplayPause}
                style={{
                  fontSize: 11,
                  color: "#555",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  padding: 0,
                }}
              >
                {store.replayPaused ? "▶" : "⏸"}
              </button>
              {[1, 2, 5].map((s) => (
                <button
                  key={s}
                  onClick={() => store.setReplaySpeed(s)}
                  style={{
                    fontSize: 11,
                    color: store.replaySpeed === s ? "#e5e5e5" : "#444",
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    padding: 0,
                    fontWeight: store.replaySpeed === s ? 600 : 400,
                  }}
                >
                  {s}×
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Terminal body */}
        <div className="terminal-body" ref={bodyRef}>
          {store.lines.map((tl) => {
            if (tl.type === "blank") {
              return <div key={tl.id} className="tl-blank" />;
            }

            const isLastPrompt = tl.type === "prompt" && tl === lastLine;

            return (
              <div
                key={tl.id}
                className={`tl-${tl.type} line-in`}
                style={tl.color ? { color: tl.color } : undefined}
              >
                {isLastPrompt && showCursor
                  ? <>$ <span className="cursor" /></>
                  : tl.text
                }
              </div>
            );
          })}

          {/* Blinking cursor before first line appears */}
          {store.lines.length === 0 && (
            <div className="tl-prompt">
              $ <span className="cursor" />
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

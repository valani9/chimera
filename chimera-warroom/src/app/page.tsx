"use client";

import { useEffect, useRef } from "react";
import { useChimeraStore } from "@/lib/store";
import { ukraineScenario, tariffShockScenario } from "@/lib/scenario";
import { Header } from "@/components/header/Header";
import { OraclePanel } from "@/components/oracle/OraclePanel";
import { RippleGraph } from "@/components/ripple/RippleGraph";
import { WaterfallPanel } from "@/components/waterfall/WaterfallPanel";
import { HydraPanel } from "@/components/hydra/HydraPanel";
import { PnLPanel } from "@/components/pnl/PnLPanel";
import { FusionPanel } from "@/components/fusion/FusionPanel";

export default function WarRoom() {
  const store = useChimeraStore();
  const tickRef = useRef<ReturnType<typeof setInterval>>(null);
  const processedRef = useRef<Set<string>>(new Set());

  // Start replay on mount
  useEffect(() => {
    store.startReplay(ukraineScenario);
    processedRef.current = new Set();
  }, []);

  // Reset processed events when scenario changes
  useEffect(() => {
    processedRef.current = new Set();
  }, [store.activeScenario?.id]);

  // Replay tick engine
  useEffect(() => {
    const scenario = store.activeScenario;
    if (!scenario || store.mode !== "replay") return;

    tickRef.current = setInterval(() => {
      if (store.replayPaused) return;

      const elapsed = (Date.now() - store.replayStartTime) * store.replaySpeed;

      // Process signals
      scenario.signals.forEach((s) => {
        const key = `signal-${s.id}`;
        if (!processedRef.current.has(key) && elapsed >= s.offsetMs) {
          processedRef.current.add(key);
          store.addSignal(s);
        }
      });

      // Process waterfall steps
      scenario.waterfall.forEach((w, i) => {
        const key = `waterfall-${w.id || i}`;
        if (!processedRef.current.has(key) && elapsed >= w.offsetMs) {
          processedRef.current.add(key);
          store.addWaterfallStep(w);
        }
      });

      // Process debates
      scenario.debates.forEach((d, i) => {
        const key = `debate-${i}`;
        if (!processedRef.current.has(key) && elapsed >= d.offsetMs) {
          processedRef.current.add(key);
          store.setDebates([...store.debates, d]);
        }
      });

      // Process trades
      scenario.trades.forEach((t, i) => {
        const key = `trade-${i}`;
        if (!processedRef.current.has(key) && elapsed >= t.offsetMs) {
          processedRef.current.add(key);
          store.addTrade(t);
        }
      });

      // Process ripple events
      scenario.rippleEvents.forEach((r, i) => {
        const key = `ripple-${i}`;
        if (!processedRef.current.has(key) && elapsed >= r.offsetMs) {
          processedRef.current.add(key);
          store.triggerRipple(r.sourceNodeId);
        }
      });
    }, 100);

    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, [store.activeScenario, store.mode, store.replayPaused, store.replaySpeed, store.replayStartTime]);

  return (
    <div className="warroom-grid">
      {/* Header */}
      <Header />

      {/* Row 1: Main panels */}
      <OraclePanel />
      <RippleGraph />
      <WaterfallPanel />
      <HydraPanel />

      {/* Row 2: Bottom panels */}
      <div className="glass-panel p-3 flex flex-col">
        {/* Mini world map placeholder */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-semibold text-blue-400 mono">GLOBAL VIEW</span>
        </div>
        <div className="flex-1 flex items-center justify-center relative">
          <svg viewBox="0 0 200 100" className="w-full h-full opacity-30">
            {/* Simplified world outline */}
            <ellipse cx="100" cy="50" rx="90" ry="40" fill="none" stroke="#2a2a3e" strokeWidth="0.5" />
            <line x1="10" y1="50" x2="190" y2="50" stroke="#1e1e2e" strokeWidth="0.3" />
            <line x1="100" y1="10" x2="100" y2="90" stroke="#1e1e2e" strokeWidth="0.3" />
          </svg>
          {/* Pulsing markers */}
          {[
            { x: "38%", y: "35%", label: "DC", color: "#3b82f6" },
            { x: "52%", y: "28%", label: "Kyiv", color: "#ef4444" },
            { x: "55%", y: "30%", label: "Moscow", color: "#ef4444" },
            { x: "75%", y: "38%", label: "Beijing", color: "#f59e0b" },
            { x: "48%", y: "35%", label: "Istanbul", color: "#22c55e" },
          ].map((m) => (
            <div key={m.label} className="absolute" style={{ left: m.x, top: m.y }}>
              <div className="relative">
                <div className="w-2 h-2 rounded-full pulse-dot" style={{ backgroundColor: m.color }} />
                <div className="absolute w-2 h-2 rounded-full pulse-ring" style={{ backgroundColor: m.color, top: 0, left: 0 }} />
                <span className="absolute text-[8px] text-zinc-500 whitespace-nowrap" style={{ top: 10, left: -8 }}>{m.label}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <PnLPanel />
      <FusionPanel />
    </div>
  );
}

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

  useEffect(() => {
    store.startReplay(ukraineScenario);
    processedRef.current = new Set();
  }, []);

  useEffect(() => {
    processedRef.current = new Set();
  }, [store.activeScenario?.id]);

  useEffect(() => {
    const scenario = store.activeScenario;
    if (!scenario || store.mode !== "replay") return;

    tickRef.current = setInterval(() => {
      if (store.replayPaused) return;
      const elapsed = (Date.now() - store.replayStartTime) * store.replaySpeed;

      scenario.signals.forEach((s) => {
        const key = `signal-${s.id}`;
        if (!processedRef.current.has(key) && elapsed >= s.offsetMs) {
          processedRef.current.add(key);
          store.addSignal(s);
        }
      });

      scenario.waterfall.forEach((w, i) => {
        const key = `waterfall-${w.id || i}`;
        if (!processedRef.current.has(key) && elapsed >= w.offsetMs) {
          processedRef.current.add(key);
          store.addWaterfallStep(w);
        }
      });

      scenario.debates.forEach((d, i) => {
        const key = `debate-${i}`;
        if (!processedRef.current.has(key) && elapsed >= d.offsetMs) {
          processedRef.current.add(key);
          store.setDebates([...store.debates, d]);
        }
      });

      scenario.trades.forEach((t, i) => {
        const key = `trade-${i}`;
        if (!processedRef.current.has(key) && elapsed >= t.offsetMs) {
          processedRef.current.add(key);
          store.addTrade(t);
        }
      });

      scenario.rippleEvents.forEach((r, i) => {
        const key = `ripple-${i}`;
        if (!processedRef.current.has(key) && elapsed >= r.offsetMs) {
          processedRef.current.add(key);
          store.triggerRipple(r.sourceNodeId);
        }
      });
    }, 100);

    return () => { if (tickRef.current) clearInterval(tickRef.current); };
  }, [store.activeScenario, store.mode, store.replayPaused, store.replaySpeed, store.replayStartTime]);

  return (
    <div className="warroom-grid">
      <Header />
      <OraclePanel />
      <RippleGraph />
      <HydraPanel />
      <WaterfallPanel />
      <FusionPanel />
      <PnLPanel />
    </div>
  );
}

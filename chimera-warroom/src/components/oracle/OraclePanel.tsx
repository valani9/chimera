"use client";

import { useChimeraStore } from "@/lib/store";
import { PHASE_COLORS } from "@/lib/colors";
import { motion, AnimatePresence } from "framer-motion";

const SIGNAL_ICONS: Record<string, string> = {
  news_cluster: "📡",
  wikipedia_spike: "📊",
  cloudflare_anomaly: "🌐",
  gov_change: "🏛️",
  vpin_spike: "⚠️",
  whale_move: "🐋",
  cascade: "🔗",
};

export function OraclePanel() {
  const { signals } = useChimeraStore();

  return (
    <div className="glass-panel p-3 flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#06b6d4" }} />
        <span className="text-xs font-semibold text-cyan-400 mono">ORACLE</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1.5">
        <AnimatePresence>
          {[...signals].reverse().map((signal, i) => (
            <motion.div
              key={signal.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className="p-2 rounded text-xs"
              style={{
                background: "rgba(30, 30, 46, 0.6)",
                borderLeft: `2px solid ${signal.source === "predator" ? "#ef4444" : "#06b6d4"}`,
              }}
            >
              <div className="flex items-center justify-between mb-0.5">
                <span className="mono text-zinc-500 text-[10px]">
                  {new Date(signal.timestamp).toLocaleTimeString()}
                </span>
                <span className="mono text-[10px]" style={{ color: signal.source === "predator" ? "#ef4444" : "#06b6d4" }}>
                  {signal.signal_type.replace(/_/g, " ").toUpperCase()}
                </span>
              </div>
              <div className="text-zinc-300 text-[11px] leading-tight mb-1">
                {SIGNAL_ICONS[signal.signal_type] || "📌"} {signal.title}
              </div>
              {/* Score bar */}
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1 rounded-full" style={{ background: "#1e1e2e" }}>
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${signal.score * 100}%`,
                      background: `linear-gradient(90deg, #06b6d4, ${signal.score > 0.7 ? "#ef4444" : "#22c55e"})`,
                    }}
                  />
                </div>
                <span className="mono text-[10px] text-zinc-400">{signal.score.toFixed(2)}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {signals.length === 0 && (
          <div className="text-zinc-600 text-xs text-center mt-8">
            Scanning data sources...
          </div>
        )}
      </div>
    </div>
  );
}

"use client";

import { useChimeraStore } from "@/lib/store";
import { PHASE_COLORS } from "@/lib/colors";
import { motion, AnimatePresence } from "framer-motion";

export function WaterfallPanel() {
  const { waterfall } = useChimeraStore();

  return (
    <div className="glass-panel p-3 flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-zinc-300 mono">REASONING WATERFALL</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Vertical line */}
        <div className="relative pl-4">
          <div
            className="absolute left-1.5 top-0 bottom-0 w-px"
            style={{ background: "#2a2a3e" }}
          />

          <AnimatePresence>
            {waterfall.map((step, i) => {
              const color = PHASE_COLORS[step.phase] || "#71717a";
              return (
                <motion.div
                  key={step.id || i}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: 0.05 }}
                  className="relative mb-2"
                >
                  {/* Dot on the timeline */}
                  <div
                    className="absolute -left-2.5 top-1 w-2 h-2 rounded-full"
                    style={{ backgroundColor: color, boxShadow: `0 0 8px ${color}40` }}
                  />

                  <div className="ml-2 p-2 rounded" style={{ background: "rgba(30, 30, 46, 0.4)" }}>
                    {/* Phase badge */}
                    <div className="flex items-center justify-between mb-0.5">
                      <span
                        className="mono text-[10px] font-semibold px-1.5 py-0.5 rounded"
                        style={{ color, background: `${color}15` }}
                      >
                        {step.phase}
                      </span>
                      {step.probability !== undefined && step.probability !== null && (
                        <span
                          className="mono text-[11px] font-bold px-1.5 py-0.5 rounded"
                          style={{
                            color: step.probability > 0.5 ? "#22c55e" : "#ef4444",
                            background: `${step.probability > 0.5 ? "#22c55e" : "#ef4444"}15`,
                            boxShadow: `0 0 8px ${step.probability > 0.5 ? "#22c55e" : "#ef4444"}20`,
                          }}
                        >
                          {(step.probability * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>

                    {/* Title */}
                    <div className="text-[11px] text-zinc-200 leading-tight">
                      {step.title}
                    </div>

                    {/* Detail */}
                    {step.detail && (
                      <div className="text-[10px] text-zinc-500 mt-0.5 leading-tight">
                        {step.detail}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>

          {waterfall.length === 0 && (
            <div className="text-zinc-600 text-xs text-center mt-8">
              Waiting for pipeline cycle...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

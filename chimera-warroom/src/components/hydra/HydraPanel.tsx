"use client";

import { useChimeraStore } from "@/lib/store";
import { AGENT_COLORS } from "@/lib/colors";
import { motion, AnimatePresence } from "framer-motion";

const AGENT_ICONS: Record<string, string> = {
  Bull: "↑",
  Bear: "↓",
  Historian: "◷",
  Contrarian: "⇄",
  Quant: "∑",
  Judge: "⚖",
};

export function HydraPanel() {
  const { debates } = useChimeraStore();
  const latestDebate = debates[debates.length - 1];

  return (
    <div className="glass-panel p-3 flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#a855f7" }} />
        <span className="text-xs font-semibold text-purple-400 mono">HYDRA DEBATE</span>
        {latestDebate && (
          <span className="text-[10px] text-zinc-500 ml-auto">
            {latestDebate.market_question.slice(0, 40)}...
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-2">
        <AnimatePresence>
          {latestDebate?.rounds.map((round) =>
            round.votes.map((vote, i) => {
              const color = AGENT_COLORS[vote.agent_name] || "#71717a";
              return (
                <motion.div
                  key={`${round.round_number}-${vote.agent_name}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.1 }}
                  className="flex gap-2"
                >
                  {/* Avatar */}
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5"
                    style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}
                  >
                    {AGENT_ICONS[vote.agent_name] || "?"}
                  </div>

                  {/* Message bubble */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[11px] font-semibold" style={{ color }}>
                        {vote.agent_name}
                      </span>
                      <span className="mono text-[10px] text-zinc-500">R{round.round_number}</span>
                      <span
                        className="mono text-[11px] font-bold ml-auto px-1.5 py-0.5 rounded"
                        style={{ color, background: `${color}15` }}
                      >
                        {(vote.probability * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div
                      className="text-[10px] text-zinc-400 leading-tight p-2 rounded"
                      style={{ background: "rgba(30, 30, 46, 0.5)" }}
                    >
                      {vote.reasoning}
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}

          {/* Judge verdict */}
          {latestDebate && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="mt-2 p-3 rounded glow-gold"
              style={{ background: "rgba(234, 179, 8, 0.08)", border: "1px solid rgba(234, 179, 8, 0.3)" }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-yellow-400">⚖ JUDGE VERDICT</span>
                <span className="mono text-sm font-bold text-yellow-300 ml-auto">
                  {(latestDebate.judge_probability * 100).toFixed(0)}%
                </span>
              </div>
              <div className="text-[10px] text-zinc-300 leading-tight">
                {latestDebate.judge_reasoning}
              </div>
              {latestDebate.dissenting_view && (
                <div className="text-[10px] text-zinc-500 mt-1 italic">
                  Dissent: {latestDebate.dissenting_view}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {!latestDebate && (
          <div className="text-zinc-600 text-xs text-center mt-8">
            Awaiting market for debate...
          </div>
        )}
      </div>
    </div>
  );
}

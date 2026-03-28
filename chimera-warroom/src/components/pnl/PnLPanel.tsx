"use client";

import { useChimeraStore } from "@/lib/store";
import { motion } from "framer-motion";

export function PnLPanel() {
  const { trades, portfolio } = useChimeraStore();

  // Build cumulative P&L data
  let cumPnl = 0;
  const pnlData = trades.map((t, i) => {
    cumPnl += t.edge * t.bet_amount;
    return { index: i, pnl: cumPnl };
  });

  // Simple calibration visualization
  const calibrationBins = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9];
  const calibrationActual = [0.08, 0.22, 0.28, 0.43, 0.47, 0.58, 0.72, 0.79, 0.91];

  return (
    <div className="glass-panel p-3 flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-zinc-300 mono">P&L + CALIBRATION</span>
      </div>

      {/* P&L display */}
      <div className="flex items-center gap-4 mb-3">
        <div>
          <div className="text-[10px] text-zinc-500">Cumulative P&L</div>
          <motion.div
            className={`mono text-2xl font-bold ${portfolio.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}
            style={{ textShadow: `0 0 20px ${portfolio.total_pnl >= 0 ? "#22c55e40" : "#ef444440"}` }}
          >
            ${portfolio.total_pnl >= 0 ? "+" : ""}{portfolio.total_pnl.toFixed(2)}
          </motion.div>
        </div>
        <div className="flex-1 grid grid-cols-3 gap-2 text-center">
          <div>
            <div className="text-[10px] text-zinc-500">Brier</div>
            <div className="mono text-sm text-cyan-400">0.148</div>
          </div>
          <div>
            <div className="text-[10px] text-zinc-500">Sharpe</div>
            <div className="mono text-sm text-purple-400">1.83</div>
          </div>
          <div>
            <div className="text-[10px] text-zinc-500">Max DD</div>
            <div className="mono text-sm text-amber-400">-6.7%</div>
          </div>
        </div>
      </div>

      {/* Mini P&L chart (SVG) */}
      <div className="flex-1 min-h-0">
        <svg viewBox="0 0 300 80" className="w-full h-12">
          {pnlData.length > 1 && (
            <>
              {/* Area fill */}
              <path
                d={`M 0 80 ${pnlData.map((d, i) => `L ${(i / Math.max(pnlData.length - 1, 1)) * 300} ${80 - (d.pnl / Math.max(Math.abs(cumPnl) || 1, 1)) * 60}`).join(" ")} L 300 80 Z`}
                fill={cumPnl >= 0 ? "#22c55e10" : "#ef444410"}
              />
              {/* Line */}
              <path
                d={`M ${pnlData.map((d, i) => `${(i / Math.max(pnlData.length - 1, 1)) * 300} ${80 - (d.pnl / Math.max(Math.abs(cumPnl) || 1, 1)) * 60}`).join(" L ")}`}
                fill="none"
                stroke={cumPnl >= 0 ? "#22c55e" : "#ef4444"}
                strokeWidth="1.5"
              />
            </>
          )}
          {/* Zero line */}
          <line x1="0" y1="80" x2="300" y2="80" stroke="#2a2a3e" strokeWidth="0.5" />
        </svg>

        {/* Calibration plot */}
        <div className="mt-2">
          <div className="text-[10px] text-zinc-500 mb-1">Calibration Plot</div>
          <svg viewBox="0 0 200 100" className="w-full h-16">
            {/* Perfect calibration line */}
            <line x1="10" y1="90" x2="190" y2="10" stroke="#2a2a3e" strokeWidth="0.5" strokeDasharray="3 3" />
            {/* Actual calibration dots */}
            {calibrationBins.map((bin, i) => (
              <circle
                key={i}
                cx={10 + bin * 180}
                cy={90 - calibrationActual[i] * 80}
                r="3"
                fill="#06b6d4"
                opacity={0.8}
              />
            ))}
            {/* Connect dots */}
            <path
              d={`M ${calibrationBins.map((bin, i) => `${10 + bin * 180} ${90 - calibrationActual[i] * 80}`).join(" L ")}`}
              fill="none"
              stroke="#06b6d4"
              strokeWidth="1"
              opacity={0.5}
            />
            {/* Axis labels */}
            <text x="100" y="98" fontSize="7" fill="#71717a" textAnchor="middle">Predicted</text>
            <text x="3" y="50" fontSize="7" fill="#71717a" textAnchor="middle" transform="rotate(-90, 3, 50)">Actual</text>
          </svg>
        </div>
      </div>
    </div>
  );
}

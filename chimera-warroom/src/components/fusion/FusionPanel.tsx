"use client";

import { useChimeraStore } from "@/lib/store";
import { motion } from "framer-motion";

export function FusionPanel() {
  const { trades, portfolio } = useChimeraStore();
  const latestTrade = trades[trades.length - 1];

  return (
    <div className="glass-panel p-3 flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#eab308" }} />
        <span className="text-xs font-semibold text-yellow-400 mono">SIGNAL FUSION + POSITIONS</span>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        {[
          { label: "Bankroll", value: `$${portfolio.bankroll.toFixed(0)}`, color: "#e4e4e7" },
          { label: "Total P&L", value: `$${portfolio.total_pnl >= 0 ? "+" : ""}${portfolio.total_pnl.toFixed(2)}`, color: portfolio.total_pnl >= 0 ? "#22c55e" : "#ef4444" },
          { label: "Trades", value: portfolio.trade_count.toString(), color: "#06b6d4" },
          { label: "Win Rate", value: `${(portfolio.win_rate * 100).toFixed(0)}%`, color: "#a855f7" },
        ].map(({ label, value, color }) => (
          <div key={label} className="text-center p-2 rounded" style={{ background: "rgba(30, 30, 46, 0.5)" }}>
            <div className="text-[10px] text-zinc-500">{label}</div>
            <div className="mono text-sm font-bold" style={{ color }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Fusion gauge (latest trade) */}
      {latestTrade && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mb-3 p-2 rounded"
          style={{ background: "rgba(30, 30, 46, 0.5)", borderLeft: "2px solid #eab308" }}
        >
          <div className="text-[10px] text-zinc-500 mb-1">Latest Fusion Result</div>
          <div className="flex items-center gap-3">
            {/* Probability bar */}
            <div className="flex-1">
              <div className="flex justify-between text-[10px] mb-0.5">
                <span className="text-red-400">NO</span>
                <span className="text-green-400">YES</span>
              </div>
              <div className="h-3 rounded-full relative" style={{ background: "#1e1e2e" }}>
                {/* Market price marker */}
                <div
                  className="absolute top-0 h-full w-0.5 bg-zinc-400 z-10"
                  style={{ left: `${latestTrade.market_price * 100}%` }}
                />
                {/* Our estimate */}
                <motion.div
                  className="absolute top-0 h-full rounded-full"
                  style={{
                    width: `${latestTrade.estimated_probability * 100}%`,
                    background: `linear-gradient(90deg, #ef4444, #eab308, #22c55e)`,
                    opacity: 0.7,
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${latestTrade.estimated_probability * 100}%` }}
                  transition={{ duration: 1 }}
                />
              </div>
              <div className="flex justify-between text-[10px] mt-0.5 mono">
                <span className="text-zinc-500">Market: {(latestTrade.market_price * 100).toFixed(0)}%</span>
                <span className="text-yellow-400">Ours: {(latestTrade.estimated_probability * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Edge + amount */}
            <div className="text-right">
              <div className="mono text-sm font-bold text-green-400">+{(latestTrade.edge * 100).toFixed(1)}%</div>
              <div className="text-[10px] text-zinc-500">edge</div>
              <div className="mono text-xs text-zinc-300">${latestTrade.bet_amount.toFixed(2)}</div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Trade log */}
      <div className="flex-1 overflow-y-auto">
        <div className="text-[10px] text-zinc-500 mb-1 font-semibold">TRADE LOG</div>
        {trades.map((trade, i) => (
          <div
            key={i}
            className="flex items-center gap-2 p-1.5 rounded mb-1 text-[10px]"
            style={{ background: "rgba(30, 30, 46, 0.3)" }}
          >
            <span className={`mono font-bold ${trade.direction === "YES" ? "text-green-400" : "text-red-400"}`}>
              {trade.direction}
            </span>
            <span className="text-zinc-400 truncate flex-1">{trade.market_question.slice(0, 35)}...</span>
            <span className="mono text-zinc-300">${trade.bet_amount.toFixed(0)}</span>
            <span className="mono text-green-400">+{(trade.edge * 100).toFixed(0)}%</span>
          </div>
        ))}
        {trades.length === 0 && (
          <div className="text-zinc-600 text-xs text-center mt-4">No trades yet</div>
        )}
      </div>
    </div>
  );
}

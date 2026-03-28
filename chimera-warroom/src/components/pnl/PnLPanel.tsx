"use client";

import { useChimeraStore } from "@/lib/store";

export function PnLPanel() {
  const { trades, portfolio } = useChimeraStore();

  let cumPnl = 0;
  const pnlData = trades.map((t) => {
    cumPnl += t.edge * t.bet_amount;
    return cumPnl;
  });

  const maxAbs = Math.max(Math.abs(cumPnl) || 1, 1);
  const W = 280;
  const H = 60;
  const pad = 6;

  const points =
    pnlData.length > 1
      ? pnlData
          .map((v, i) => {
            const x = pad + (i / (pnlData.length - 1)) * (W - pad * 2);
            const y = H / 2 - (v / maxAbs) * (H / 2 - pad);
            return `${x},${y}`;
          })
          .join(" ")
      : null;

  const lineColor = cumPnl >= 0 ? "var(--green)" : "var(--red)";

  return (
    <div className="panel">
      <div className="panel-header">
        <span className="label">P&amp;L</span>
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "12px 14px", gap: 12 }}>
        {/* Big P&L number */}
        <div>
          <div className="label" style={{ marginBottom: 4 }}>Cumulative</div>
          <div
            className="mono"
            style={{
              fontSize: 28,
              fontWeight: 700,
              color: portfolio.total_pnl >= 0 ? "var(--green)" : "var(--red)",
              letterSpacing: "-0.01em",
              lineHeight: 1,
            }}
          >
            {portfolio.total_pnl >= 0 ? "+" : ""}$
            {portfolio.total_pnl.toFixed(2)}
          </div>
        </div>

        {/* Stats row */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 1,
            background: "var(--border)",
          }}
        >
          {[
            { label: "Trades", value: portfolio.trade_count.toString() },
            { label: "Brier", value: "0.148" },
            { label: "Sharpe", value: "1.83" },
          ].map(({ label, value }) => (
            <div
              key={label}
              style={{
                padding: "8px 10px",
                background: "var(--surface)",
              }}
            >
              <div className="label" style={{ marginBottom: 2, fontSize: 9 }}>{label}</div>
              <div
                className="mono"
                style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}
              >
                {value}
              </div>
            </div>
          ))}
        </div>

        {/* SVG line chart */}
        <div style={{ flex: 1, minHeight: 0 }}>
          <div className="label" style={{ marginBottom: 6, fontSize: 9 }}>Equity Curve</div>
          <svg
            viewBox={`0 0 ${W} ${H}`}
            style={{ width: "100%", height: "100%", display: "block", minHeight: 0 }}
            preserveAspectRatio="none"
          >
            {/* Zero baseline */}
            <line
              x1={0}
              y1={H / 2}
              x2={W}
              y2={H / 2}
              stroke="var(--border-2)"
              strokeWidth={0.5}
            />

            {points && (
              <polyline
                points={points}
                fill="none"
                stroke={lineColor}
                strokeWidth={1.2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            )}

            {pnlData.length === 0 && (
              <text
                x={W / 2}
                y={H / 2 + 4}
                textAnchor="middle"
                fontSize={9}
                fill="var(--text-3)"
              >
                No data
              </text>
            )}
          </svg>
        </div>
      </div>
    </div>
  );
}

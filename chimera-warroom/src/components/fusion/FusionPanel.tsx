"use client";

import { useChimeraStore } from "@/lib/store";

export function FusionPanel() {
  const { trades, portfolio } = useChimeraStore();
  const latestTrade = trades[trades.length - 1];

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="status-dot" style={{ background: "var(--amber)" }} />
        <span className="label">Signal Fusion</span>
      </div>

      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column" }}>
        {/* Key metrics strip */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            borderBottom: "1px solid var(--border)",
          }}
        >
          {[
            {
              label: "Edge",
              value: latestTrade ? `+${(latestTrade.edge * 100).toFixed(1)}%` : "—",
              color: latestTrade ? "var(--green)" : "var(--text-3)",
            },
            {
              label: "Est. Prob",
              value: latestTrade
                ? `${(latestTrade.estimated_probability * 100).toFixed(0)}%`
                : "—",
              color: "var(--text)",
            },
            {
              label: "Kelly",
              value: latestTrade ? `$${latestTrade.bet_amount.toFixed(0)}` : "—",
              color: "var(--text)",
            },
          ].map(({ label, value, color }) => (
            <div
              key={label}
              style={{
                padding: "10px 14px",
                borderRight: label !== "Kelly" ? "1px solid var(--border)" : undefined,
              }}
            >
              <div className="label" style={{ marginBottom: 3 }}>{label}</div>
              <div className="mono" style={{ fontSize: 15, fontWeight: 600, color }}>
                {value}
              </div>
            </div>
          ))}
        </div>

        {/* Probability bar */}
        {latestTrade && (
          <div style={{ padding: "12px 14px", borderBottom: "1px solid var(--border)" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: 5,
              }}
            >
              <span className="label" style={{ fontSize: 9 }}>Market price</span>
              <span className="label" style={{ fontSize: 9 }}>Our estimate</span>
            </div>

            {/* Bar track */}
            <div
              style={{
                height: 4,
                background: "var(--surface-2)",
                position: "relative",
                borderRadius: 2,
              }}
            >
              {/* Estimate fill */}
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 0,
                  height: "100%",
                  width: `${latestTrade.estimated_probability * 100}%`,
                  background:
                    latestTrade.direction === "YES"
                      ? "var(--green)"
                      : "var(--red)",
                  borderRadius: 2,
                  transition: "width 0.6s ease",
                }}
              />
              {/* Market price tick */}
              <div
                style={{
                  position: "absolute",
                  top: -3,
                  bottom: -3,
                  width: 1,
                  background: "rgba(255,255,255,0.4)",
                  left: `${latestTrade.market_price * 100}%`,
                }}
              />
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginTop: 4,
              }}
            >
              <span className="mono" style={{ fontSize: 10, color: "var(--text-2)" }}>
                {(latestTrade.market_price * 100).toFixed(0)}%
              </span>
              <span
                className="mono"
                style={{
                  fontSize: 10,
                  color:
                    latestTrade.direction === "YES"
                      ? "var(--green)"
                      : "var(--red)",
                }}
              >
                {(latestTrade.estimated_probability * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}

        {/* Trade log */}
        <div style={{ flex: 1, overflowY: "auto" }}>
          <div style={{ padding: "6px 14px 4px", borderBottom: "1px solid var(--border)" }}>
            <span className="label" style={{ fontSize: 9 }}>Executions</span>
          </div>
          {trades.length === 0 ? (
            <div
              style={{
                padding: "24px 14px",
                fontSize: 11,
                color: "var(--text-3)",
                textAlign: "center",
              }}
            >
              No trades yet
            </div>
          ) : (
            trades.map((trade, i) => (
              <div
                key={i}
                className="fade-in"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "7px 14px",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                {/* Direction badge */}
                <span
                  className="mono"
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color:
                      trade.direction === "YES"
                        ? "var(--green)"
                        : "var(--red)",
                    width: 26,
                    flexShrink: 0,
                  }}
                >
                  {trade.direction}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--text-2)",
                    flex: 1,
                    overflow: "hidden",
                    whiteSpace: "nowrap",
                    textOverflow: "ellipsis",
                  }}
                >
                  {trade.market_question.slice(0, 40)}
                </span>
                <span
                  className="mono"
                  style={{ fontSize: 10, color: "var(--text-2)", flexShrink: 0 }}
                >
                  ${trade.bet_amount.toFixed(0)}
                </span>
                <span
                  className="mono"
                  style={{ fontSize: 10, color: "var(--green)", flexShrink: 0 }}
                >
                  +{(trade.edge * 100).toFixed(0)}%
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

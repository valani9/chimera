"use client";

import { useChimeraStore } from "@/lib/store";

const TYPE_COLOR: Record<string, string> = {
  news_cluster:       "#888",
  wikipedia_spike:    "#888",
  cloudflare_anomaly: "#888",
  gov_change:         "#f59e0b",
  vpin_spike:         "#ef4444",
  whale_move:         "#ef4444",
  cascade:            "#ef4444",
};

const TYPE_LABEL: Record<string, string> = {
  news_cluster:       "NEWS",
  wikipedia_spike:    "WIKI",
  cloudflare_anomaly: "NET",
  gov_change:         "GOV",
  vpin_spike:         "VPIN",
  whale_move:         "WHALE",
  cascade:            "CASCADE",
};

export function OraclePanel() {
  const { signals } = useChimeraStore();

  return (
    <div className="panel">
      {/* Header */}
      <div className="panel-header">
        <div className="status-dot" />
        <span className="label">Oracle</span>
        <span
          className="mono"
          style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-2)" }}
        >
          {signals.length}
        </span>
      </div>

      {/* Signal list */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {signals.length === 0 ? (
          <div
            style={{
              padding: "32px 14px",
              fontSize: 11,
              color: "var(--text-3)",
              textAlign: "center",
            }}
          >
            Scanning sources...
          </div>
        ) : (
          [...signals].reverse().map((signal) => {
            const typeColor = TYPE_COLOR[signal.signal_type] ?? "#555";
            const typeLabel = TYPE_LABEL[signal.signal_type] ?? signal.signal_type.toUpperCase();
            return (
              <div
                key={signal.id}
                className="fade-in"
                style={{
                  display: "flex",
                  alignItems: "stretch",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                {/* Left accent bar */}
                <div
                  style={{
                    width: 2,
                    flexShrink: 0,
                    background: typeColor,
                    opacity: 0.7,
                  }}
                />
                {/* Content */}
                <div style={{ flex: 1, padding: "8px 12px", minWidth: 0 }}>
                  {/* Row 1: time + type */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      marginBottom: 3,
                    }}
                  >
                    <span
                      className="mono"
                      style={{ fontSize: 9, color: "var(--text-3)" }}
                    >
                      {new Date(signal.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </span>
                    <span
                      className="mono"
                      style={{
                        fontSize: 9,
                        color: typeColor,
                        letterSpacing: "0.06em",
                      }}
                    >
                      {typeLabel}
                    </span>
                  </div>

                  {/* Row 2: title */}
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--text)",
                      lineHeight: 1.4,
                      overflow: "hidden",
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      marginBottom: 5,
                    }}
                  >
                    {signal.title}
                  </div>

                  {/* Row 3: score bar */}
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div
                      style={{
                        flex: 1,
                        height: 2,
                        background: "var(--surface-2)",
                        borderRadius: 1,
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          height: "100%",
                          width: `${signal.score * 100}%`,
                          background:
                            signal.score >= 0.75
                              ? "var(--red)"
                              : signal.score >= 0.5
                              ? "var(--amber)"
                              : "#555",
                          borderRadius: 1,
                          transition: "width 0.4s ease",
                        }}
                      />
                    </div>
                    <span
                      className="mono"
                      style={{ fontSize: 10, color: "var(--text-2)", flexShrink: 0 }}
                    >
                      {signal.score.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

"use client";

import { useChimeraStore } from "@/lib/store";
import { AGENT_COLORS } from "@/lib/colors";

export function HydraPanel() {
  const { debates } = useChimeraStore();
  const latestDebate = debates[debates.length - 1];

  return (
    <div className="panel">
      {/* Header */}
      <div className="panel-header">
        <div className="status-dot" style={{ background: "#a855f7" }} />
        <span className="label">Hydra Debate</span>
      </div>

      {/* Market question */}
      {latestDebate && (
        <div
          style={{
            padding: "8px 14px",
            borderBottom: "1px solid var(--border)",
            fontSize: 11,
            color: "var(--text-2)",
            lineHeight: 1.4,
            flexShrink: 0,
          }}
        >
          {latestDebate.market_question}
        </div>
      )}

      {/* Agent table */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {!latestDebate ? (
          <div
            style={{
              padding: "32px 14px",
              fontSize: 11,
              color: "var(--text-3)",
              textAlign: "center",
            }}
          >
            Awaiting market...
          </div>
        ) : (
          <>
            {latestDebate.rounds.map((round, ri) => (
              <div key={round.round_number}>
                {/* Round divider */}
                <div
                  style={{
                    padding: "5px 14px",
                    borderBottom: "1px solid var(--border)",
                    borderTop: ri > 0 ? "1px solid var(--border)" : undefined,
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <span
                    className="label"
                    style={{ color: "var(--text-3)", fontSize: 9 }}
                  >
                    Round {round.round_number}
                  </span>
                  {round.challenge_text && (
                    <span
                      style={{
                        fontSize: 10,
                        color: "var(--text-3)",
                        fontStyle: "italic",
                        flex: 1,
                        overflow: "hidden",
                        whiteSpace: "nowrap",
                        textOverflow: "ellipsis",
                      }}
                    >
                      — {round.challenge_text.slice(0, 55)}...
                    </span>
                  )}
                </div>

                {/* Votes */}
                {round.votes.map((vote) => {
                  const color = AGENT_COLORS[vote.agent_name] ?? "var(--text-2)";
                  return (
                    <div
                      key={vote.agent_name}
                      className="fade-in"
                      style={{
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 10,
                        padding: "7px 14px",
                        borderBottom: "1px solid var(--border)",
                      }}
                    >
                      {/* Agent dot + name */}
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                          width: 72,
                          flexShrink: 0,
                        }}
                      >
                        <div
                          style={{
                            width: 5,
                            height: 5,
                            borderRadius: "50%",
                            background: color,
                            flexShrink: 0,
                          }}
                        />
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 500,
                            color,
                          }}
                        >
                          {vote.agent_name}
                        </span>
                      </div>

                      {/* Probability */}
                      <span
                        className="mono"
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color:
                            vote.probability > 0.5
                              ? "var(--green)"
                              : "var(--red)",
                          width: 36,
                          flexShrink: 0,
                          textAlign: "right",
                        }}
                      >
                        {(vote.probability * 100).toFixed(0)}%
                      </span>

                      {/* Reasoning */}
                      <span
                        style={{
                          fontSize: 10,
                          color: "var(--text-2)",
                          lineHeight: 1.4,
                          flex: 1,
                          overflow: "hidden",
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                        }}
                      >
                        {vote.reasoning}
                      </span>
                    </div>
                  );
                })}
              </div>
            ))}

            {/* Judge verdict */}
            <div
              className="fade-in"
              style={{
                margin: "8px 14px",
                padding: "10px 12px",
                borderLeft: "2px solid var(--text)",
                background: "var(--surface-2)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 5,
                }}
              >
                <span className="label" style={{ fontSize: 9 }}>
                  Judge Synthesis
                </span>
                <span
                  className="mono"
                  style={{
                    fontSize: 18,
                    fontWeight: 700,
                    color:
                      latestDebate.judge_probability > 0.5
                        ? "var(--green)"
                        : "var(--red)",
                  }}
                >
                  {(latestDebate.judge_probability * 100).toFixed(0)}%
                </span>
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: "var(--text-2)",
                  lineHeight: 1.45,
                  marginBottom: 5,
                }}
              >
                {latestDebate.judge_reasoning}
              </div>
              {latestDebate.dissenting_view && (
                <div
                  style={{
                    fontSize: 10,
                    color: "var(--text-3)",
                    fontStyle: "italic",
                    lineHeight: 1.4,
                  }}
                >
                  Dissent: {latestDebate.dissenting_view}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

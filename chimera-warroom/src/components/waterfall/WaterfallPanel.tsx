"use client";

import { useChimeraStore } from "@/lib/store";
import { PHASE_COLORS } from "@/lib/colors";

export function WaterfallPanel() {
  const { waterfall } = useChimeraStore();

  return (
    <div
      className="warroom-waterfall"
      style={{
        background: "var(--surface)",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header strip */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "0 16px",
          height: 30,
          borderBottom: "1px solid var(--border)",
          flexShrink: 0,
        }}
      >
        <span className="label">Reasoning Waterfall</span>
        <span className="mono" style={{ fontSize: 10, color: "var(--text-3)", marginLeft: "auto" }}>
          {waterfall.length} steps
        </span>
      </div>

      {/* Horizontal scrolling timeline */}
      <div
        style={{
          flex: 1,
          overflowX: "auto",
          overflowY: "hidden",
          display: "flex",
          alignItems: "stretch",
          position: "relative",
        }}
      >
        {waterfall.length === 0 ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              fontSize: 11,
              color: "var(--text-3)",
            }}
          >
            Pipeline idle...
          </div>
        ) : (
          <div
            style={{
              display: "flex",
              alignItems: "stretch",
              gap: 0,
              padding: "0 16px",
              minWidth: "max-content",
            }}
          >
            {waterfall.map((step, i) => {
              const phaseColor = PHASE_COLORS[step.phase] ?? "var(--text-3)";
              const isLast = i === waterfall.length - 1;

              return (
                <div
                  key={step.id || i}
                  className="fade-in"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 0,
                  }}
                >
                  {/* Step card */}
                  <div
                    style={{
                      width: 160,
                      height: "100%",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      padding: "0 12px",
                      borderRight: isLast ? "none" : "1px solid var(--border)",
                      gap: 4,
                    }}
                  >
                    {/* Phase label */}
                    <div
                      style={{
                        fontSize: 9,
                        fontWeight: 500,
                        letterSpacing: "0.1em",
                        color: phaseColor,
                        textTransform: "uppercase",
                        display: "flex",
                        alignItems: "center",
                        gap: 5,
                      }}
                    >
                      <div
                        style={{
                          width: 4,
                          height: 4,
                          borderRadius: "50%",
                          background: phaseColor,
                          flexShrink: 0,
                        }}
                      />
                      {step.phase}
                    </div>

                    {/* Title */}
                    <div
                      style={{
                        fontSize: 11,
                        color: "var(--text)",
                        lineHeight: 1.35,
                        overflow: "hidden",
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                      }}
                    >
                      {step.title}
                    </div>

                    {/* Probability badge */}
                    {step.probability !== undefined && step.probability !== null && (
                      <div
                        className="mono"
                        style={{
                          fontSize: 11,
                          fontWeight: 600,
                          color:
                            step.probability > 0.5
                              ? "var(--green)"
                              : "var(--red)",
                        }}
                      >
                        {(step.probability * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

import type { Scenario } from "./types";

export type TerminalLineType =
  | "prompt"
  | "section"
  | "output"
  | "data"
  | "ascii"
  | "success"
  | "muted"
  | "blank";

export interface TerminalLine {
  id: string;
  type: TerminalLineType;
  text: string;
  offsetMs: number;
  color?: string;
}

const SEP = "─".repeat(54);

function line(
  id: string,
  type: TerminalLineType,
  text: string,
  offsetMs: number,
  color?: string
): TerminalLine {
  return { id, type, text, offsetMs, color };
}

const UKRAINE_ASCII = [
  "  Ukraine ─────── Ceasefire ─────── Sanctions ─────── Russia",
  "     │                 │",
  "   NATO            Oil Prices ─────── Inflation ─────── Int. Rates",
  "                                                             │",
  "                                                      S&P 500 ─── Bitcoin",
];

const TARIFF_ASCII = [
  "  Trump ─────── Tariffs ─────── China ─────── Yuan",
  "                    │               │",
  "               Trade War       (retaliation)",
  "                    │",
  "             Supply Chain ─── Inflation ─── Fed ─── Int. Rates",
  "                                                         │",
  "                                                   S&P 500 ─── Recession ─── Bitcoin",
];

export function scenarioToTerminalLines(scenario: Scenario): TerminalLine[] {
  const lines: TerminalLine[] = [];
  let uid = 0;
  const id = () => `tl-${uid++}`;

  const isUkraine = scenario.id === "ukraine-signal";
  const asciiArt = isUkraine ? UKRAINE_ASCII : TARIFF_ASCII;

  // ── Prompt ──────────────────────────────────────────────
  lines.push(line(id(), "prompt", `$ chimera run --scenario "${scenario.name}" --replay`, 0));
  lines.push(line(id(), "blank", "", 200));

  // ── ORACLE ──────────────────────────────────────────────
  lines.push(line(id(), "section", `┌─ ORACLE  ${SEP}`, 1000));
  lines.push(line(id(), "muted",   "  scanning  rss · gdelt · wikipedia · cloudflare · gov_diffs", 1600));
  lines.push(line(id(), "blank",   "", 2000));

  // Signals
  const TYPE_PAD: Record<string, string> = {
    news_cluster:       "NEWS  ",
    wikipedia_spike:    "WIKI  ",
    cloudflare_anomaly: "NET   ",
    gov_change:         "GOV   ",
    vpin_spike:         "VPIN  ",
    whale_move:         "WHALE ",
    cascade:            "CASC  ",
  };

  scenario.signals.forEach((sig) => {
    const tag = TYPE_PAD[sig.signal_type] ?? "SIG   ";
    const score = sig.score.toFixed(2);
    const title = sig.title.slice(0, 62);
    const color =
      sig.source === "predator"
        ? "#ef4444"
        : sig.signal_type === "gov_change"
        ? "#f59e0b"
        : undefined;
    lines.push(line(id(), "output", `  → ${tag}  ${score}  ${title}`, sig.offsetMs, color));
    if (sig.detail) {
      lines.push(line(id(), "muted", `             ${sig.detail.slice(0, 68)}`, sig.offsetMs + 100));
    }
  });

  const lastSignalMs = Math.max(...scenario.signals.map((s) => s.offsetMs), 0);
  lines.push(line(id(), "blank", "", lastSignalMs + 300));

  // ── RIPPLE ──────────────────────────────────────────────
  const rippleStart = scenario.rippleEvents[0]?.offsetMs ?? lastSignalMs + 2000;
  lines.push(line(id(), "section", `┌─ RIPPLE  ${SEP}`, rippleStart - 1000));
  lines.push(line(id(), "muted",   "  causal knowledge graph", rippleStart - 800));
  lines.push(line(id(), "blank",   "", rippleStart - 600));

  asciiArt.forEach((artLine, i) => {
    lines.push(line(id(), "ascii", artLine, rippleStart - 400 + i * 40));
  });

  lines.push(line(id(), "blank", "", rippleStart));

  scenario.rippleEvents.forEach((ev, i) => {
    const depth = i + 1;
    const decay = Math.pow(0.6, depth).toFixed(2);
    lines.push(
      line(id(), "muted", `  → ${ev.sourceNodeId.padEnd(14)}  depth:${depth}  decay:×${decay}  activated`, ev.offsetMs)
    );
  });

  const lastRippleMs = Math.max(...scenario.rippleEvents.map((r) => r.offsetMs), rippleStart);
  lines.push(line(id(), "output", `  ${scenario.rippleEvents.length} effects propagated  ·  log-odds adj: +0.04`, lastRippleMs + 400));
  lines.push(line(id(), "blank",  "", lastRippleMs + 600));

  // ── HYDRA ───────────────────────────────────────────────
  const debate = scenario.debates[0];
  if (debate) {
    lines.push(line(id(), "section", `┌─ HYDRA   ${SEP}`, debate.offsetMs));
    lines.push(line(id(), "muted",   `  market   ${debate.market_question}`, debate.offsetMs + 200));
    lines.push(line(id(), "data",    `  price    ${debate.rounds[0]?.votes[0] ? "see below" : "—"}`, debate.offsetMs + 300));
    lines.push(line(id(), "blank",   "", debate.offsetMs + 400));

    const AGENT_COLORS: Record<string, string> = {
      Bull: "#22c55e",
      Bear: "#ef4444",
      Historian: "#f59e0b",
      Contrarian: "#a855f7",
      Quant: "#06b6d4",
      Judge: "#e5e5e5",
    };

    debate.rounds.forEach((round, ri) => {
      const rOffset = debate.offsetMs + 600 + ri * 18000;
      const challengeText = round.challenge_text
        ? `  '${round.challenge_text.slice(0, 72)}'`
        : "";
      lines.push(line(id(), "muted", `  ── round ${round.round_number}  ${SEP.slice(0, 43)}`, rOffset));
      if (challengeText) {
        lines.push(line(id(), "muted", challengeText, rOffset + 200));
      }
      lines.push(line(id(), "blank", "", rOffset + 300));

      round.votes.forEach((vote, vi) => {
        const pct = (vote.probability * 100).toFixed(0).padStart(3);
        const name = vote.agent_name.toLowerCase().padEnd(12);
        const snippet = vote.reasoning.slice(0, 52);
        const color = AGENT_COLORS[vote.agent_name];
        const trend = ri > 0
          ? (vote.probability > (debate.rounds[ri - 1]?.votes[vi]?.probability ?? vote.probability) ? " ↑" :
             vote.probability < (debate.rounds[ri - 1]?.votes[vi]?.probability ?? vote.probability) ? " ↓" : " ●")
          : "";
        lines.push(
          line(id(), "output", `  ${name}  ${pct}%${trend.padEnd(3)}  ${snippet}`, rOffset + 400 + vi * 600, color)
        );
      });
      lines.push(line(id(), "blank", "", rOffset + 400 + round.votes.length * 600));
    });

    // Judge
    const judgeOffset = debate.offsetMs + 600 + debate.rounds.length * 18000;
    lines.push(line(id(), "muted",   `  ── judge synthesis  ${SEP.slice(0, 38)}`, judgeOffset));
    lines.push(line(id(), "success", `  judge       ${(debate.judge_probability * 100).toFixed(0)}%   conf:${debate.judge_confidence.toFixed(2)}`, judgeOffset + 300, "#22c55e"));
    lines.push(line(id(), "muted",   `  "${debate.judge_reasoning.slice(0, 72)}"`, judgeOffset + 500));
    if (debate.dissenting_view) {
      lines.push(line(id(), "muted", `  dissent: ${debate.dissenting_view.slice(0, 68)}`, judgeOffset + 700));
    }
    lines.push(line(id(), "blank",   "", judgeOffset + 900));
  }

  // ── FUSION ──────────────────────────────────────────────
  const trade = scenario.trades[0];
  if (trade) {
    lines.push(line(id(), "section", `┌─ FUSION  ${SEP}`, trade.offsetMs - 20000));
    lines.push(line(id(), "data",    `  raw aggregate   ${((trade.estimated_probability - 0.04) / 1.05).toFixed(3)}`, trade.offsetMs - 19500));
    lines.push(line(id(), "data",    `  ripple adj      +0.040`, trade.offsetMs - 19200));
    lines.push(line(id(), "data",    `  extremize       ${trade.estimated_probability.toFixed(3)}   (d=1.5)`, trade.offsetMs - 18900));
    lines.push(line(id(), "blank",   "", trade.offsetMs - 18600));
    lines.push(line(id(), "data",    `  market price    ${trade.market_price.toFixed(3)}`, trade.offsetMs - 18300));
    lines.push(
      line(id(), "data", `  edge            ${trade.direction === "YES" ? "+" : ""}${(trade.edge * 100).toFixed(1)}%`, trade.offsetMs - 18000,
        trade.edge > 0 ? "#22c55e" : "#ef4444")
    );
    lines.push(line(id(), "data",    `  kelly fraction  ${(trade.kelly_fraction * 100).toFixed(1)}%  →  $${trade.bet_amount.toFixed(2)}`, trade.offsetMs - 17700));
    lines.push(line(id(), "blank",   "", trade.offsetMs - 17400));

    // ── EXECUTE ─────────────────────────────────────────
    lines.push(line(id(), "section", `┌─ EXECUTE ${SEP}`, trade.offsetMs - 1000));
    const dir = trade.direction === "YES" ? "BUY  YES" : "SELL NO ";
    lines.push(
      line(id(), "success",
        `  ${dir}  $${trade.bet_amount.toFixed(2)}  @  ${trade.market_price.toFixed(2)}  ──  FILLED  ✓`,
        trade.offsetMs, "#22c55e")
    );
    lines.push(line(id(), "blank",   "", trade.offsetMs + 300));

    const pnl = trade.edge * trade.bet_amount;
    lines.push(
      line(id(), "muted",
        `  P&L ${pnl >= 0 ? "+" : ""}$${pnl.toFixed(2)}  ·  bankroll $${(1000 + pnl).toFixed(2)}  ·  brier 0.148  ·  sharpe 1.83`,
        trade.offsetMs + 500)
    );
    lines.push(line(id(), "blank",   "", trade.offsetMs + 800));
  }

  // Final prompt
  const finalOffset = trade ? trade.offsetMs + 1200 : lastRippleMs + 3000;
  lines.push(line(id(), "prompt", "$ _", finalOffset));

  return lines.sort((a, b) => a.offsetMs - b.offsetMs);
}

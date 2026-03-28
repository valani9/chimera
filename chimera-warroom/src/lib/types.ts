export interface Signal {
  id: string;
  source: string;
  signal_type: string;
  score: number;
  title: string;
  detail: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface WaterfallStep {
  id: string;
  timestamp: string;
  phase: "ORACLE" | "HYDRA" | "RIPPLE" | "PREDATOR" | "FUSION" | "EXECUTE";
  title: string;
  detail: string;
  probability?: number;
  probability_delta?: number;
  confidence?: number;
}

export interface DebateMessage {
  agent_name: string;
  agent_role: string;
  probability: number;
  confidence: number;
  reasoning: string;
  key_evidence: string[];
  round_number: number;
}

export interface DebateResult {
  market_id: string;
  market_question: string;
  rounds: { round_number: number; votes: DebateMessage[]; challenge_text: string }[];
  judge_probability: number;
  judge_confidence: number;
  judge_reasoning: string;
  dissenting_view: string;
}

export interface GraphNode {
  id: string;
  type: string;
  role?: string;
  active?: boolean;
  rippleTime?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Position {
  market_id: string;
  market_question: string;
  side: string;
  size: number;
  avg_entry_price: number;
  current_price: number;
  unrealized_pnl: number;
}

export interface TradeDecision {
  market_id: string;
  market_question: string;
  direction: string;
  estimated_probability: number;
  market_price: number;
  edge: number;
  kelly_fraction: number;
  bet_amount: number;
  confidence: number;
  rationale: string;
  timestamp: string;
}

export interface PortfolioSummary {
  bankroll: number;
  total_pnl: number;
  trade_count: number;
  win_rate: number;
  max_drawdown: number;
  active_positions: number;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  durationMs: number;
  signals: (Signal & { offsetMs: number })[];
  waterfall: (WaterfallStep & { offsetMs: number })[];
  debates: (DebateResult & { offsetMs: number })[];
  graph: GraphData;
  trades: (TradeDecision & { offsetMs: number })[];
  rippleEvents: { offsetMs: number; sourceNodeId: string }[];
}

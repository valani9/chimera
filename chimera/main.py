"""CHIMERA: Main pipeline orchestrator + FastAPI server.

This is the brain of the system. It:
1. Runs ORACLE scan loops to detect signals
2. Matches signals to Polymarket markets
3. Triggers HYDRA debates on matched markets
4. Runs RIPPLE propagation for second-order effects
5. Fuses all intelligence through the CHIMERA engine
6. Executes trades via PREDATOR-validated orders
7. Serves real-time state to the War Room dashboard via FastAPI
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chimera.config import settings
from chimera.oracle.signals import OracleEngine
from chimera.hydra.debate import DebateOrchestrator
from chimera.ripple.propagation import RippleEngine
from chimera.ripple.market_linker import MarketLinker
from chimera.predator.vpin import VPINCalculator
from chimera.predator.whale import WhaleDetector
from chimera.predator.cascade import CascadeDetector
from chimera.predator.orderbook import analyze_orderbook
from chimera.core.fusion import fuse
from chimera.core.executor import ChimeraExecutor
from chimera.polymarket.markets import PolymarketClient
from chimera.models.events import Signal
from chimera.models.forecasts import MicrostructureAnalysis
from chimera.models.trades import WaterfallStep, TradeDecision


# ── Global State ──

class ChimeraState:
    """Shared application state (in-memory, no DB needed)."""

    def __init__(self):
        self.polymarket = PolymarketClient()
        self.oracle = OracleEngine()
        self.hydra = DebateOrchestrator()
        self.ripple = RippleEngine()
        self.market_linker = MarketLinker()
        self.vpin = VPINCalculator()
        self.whale_detector = WhaleDetector()
        self.cascade_detector = CascadeDetector()
        self.executor = ChimeraExecutor(paper_trading=settings.paper_trading)

        # Dashboard state
        self.signals: list[Signal] = []
        self.waterfall_steps: list[WaterfallStep] = []
        self.trade_decisions: list[TradeDecision] = []
        self.active = False
        self.last_scan: datetime | None = None
        self.scan_count: int = 0


state = ChimeraState()


# ── Pipeline Logic ──

async def run_pipeline_cycle():
    """Run one full CHIMERA pipeline cycle."""
    state.scan_count += 1
    print(f"\n{'='*60}")
    print(f"[CHIMERA] Pipeline cycle #{state.scan_count}")
    print(f"{'='*60}")

    # ── Step 1: ORACLE scan ──
    step = WaterfallStep(
        phase="ORACLE",
        title="Scanning data sources...",
        detail="RSS feeds, GDELT, Wikipedia pageviews, Cloudflare Radar",
    )
    state.waterfall_steps.append(step)

    signals = await state.oracle.scan()
    state.signals.extend(signals)

    if not signals:
        step.detail = "No new signals detected"
        print("[CHIMERA] No signals — sleeping until next cycle")
        return

    step.detail = f"Detected {len(signals)} signals"
    print(f"[CHIMERA] {len(signals)} signals detected")

    # ── Step 2: Fetch markets & match signals ──
    markets = state.polymarket.get_cached_markets()
    if not markets:
        markets = await state.polymarket.fetch_active_markets(
            limit=settings.polymarket.max_markets
        )
        if markets:
            state.market_linker.set_embedder(state.oracle.get_embedder())
            state.market_linker.embed_markets(markets)

    if not markets:
        print("[CHIMERA] No markets available — skipping")
        return

    # Match each signal to relevant markets
    for signal in signals[:3]:  # Process top 3 signals per cycle
        matched = state.market_linker.find_matching_markets(signal, markets)

        if not matched:
            continue

        for market, similarity in matched[:1]:  # Top match per signal
            print(f"\n[CHIMERA] Processing: '{market.question[:60]}...' (sim: {similarity:.2f})")

            state.waterfall_steps.append(WaterfallStep(
                phase="ORACLE",
                title=f"Signal matched: {signal.title[:50]}",
                detail=f"Market: {market.question[:60]}... (similarity: {similarity:.2f})",
                probability=market.yes_price,
            ))

            # ── Step 3: PREDATOR microstructure ──
            ob = await state.polymarket.fetch_orderbook(market.yes_token_id)
            ob_analysis = {}
            micro = MicrostructureAnalysis(market_id=market.id)

            if ob:
                ob_analysis = analyze_orderbook(ob)
                micro.vpin = state.vpin.compute_vpin()
                micro.order_imbalance = ob_analysis.get("imbalance", 0.0)
                micro.spread = ob_analysis.get("spread", 0.0)
                micro.depth_ratio = ob_analysis.get("depth_ratio", 1.0)
                micro.liquidity_score = ob_analysis.get("liquidity_score", 0.0)

                state.waterfall_steps.append(WaterfallStep(
                    phase="PREDATOR",
                    title=f"VPIN: {micro.vpin:.2f} | Imbalance: {micro.order_imbalance:+.2f}",
                    detail=f"Spread: {micro.spread:.3f} | Liquidity: {micro.liquidity_score:.2f}",
                ))

            # ── Step 4: RIPPLE propagation ──
            ripple_effects = await state.ripple.process_signal(signal, markets)

            if ripple_effects:
                chains = [" → ".join(e.relationship_chain[:3]) for e in ripple_effects[:3]]
                state.waterfall_steps.append(WaterfallStep(
                    phase="RIPPLE",
                    title=f"{len(ripple_effects)} second-order effects found",
                    detail=" | ".join(chains),
                ))

            # ── Step 5: HYDRA debate ──
            state.waterfall_steps.append(WaterfallStep(
                phase="HYDRA",
                title="Multi-agent debate starting...",
                detail="Bull, Bear, Historian, Contrarian, Quant → Judge",
            ))

            debate = await state.hydra.run_debate(
                market_question=market.question,
                market_price=market.yes_price,
                market_id=market.id,
                category=market.category,
                signals=[signal],
                best_bid=ob_analysis.get("best_bid", 0.0),
                best_ask=ob_analysis.get("best_ask", 1.0),
                spread=ob_analysis.get("spread", 1.0),
                bid_depth=ob_analysis.get("total_bid_depth", 0.0),
                ask_depth=ob_analysis.get("total_ask_depth", 0.0),
            )

            # Log debate results
            r1_summary = " | ".join(
                f"{v.agent_name}: {v.probability:.0%}"
                for v in debate.rounds[0].votes
            ) if debate.rounds else ""

            state.waterfall_steps.append(WaterfallStep(
                phase="HYDRA",
                title=f"Debate complete → Judge: {debate.judge_probability:.1%}",
                detail=f"R1: {r1_summary}",
                probability=debate.judge_probability,
                confidence=debate.judge_confidence,
            ))

            # ── Step 6: FUSION ──
            decision = fuse(
                debate=debate,
                microstructure=micro,
                ripple_effects=ripple_effects,
                market_price=market.yes_price,
                market_id=market.id,
                market_question=market.question,
            )

            state.waterfall_steps.append(WaterfallStep(
                phase="FUSION",
                title=f"Edge: {decision.edge:.1%} → {decision.direction}",
                detail=decision.rationale,
                probability=decision.estimated_probability,
                confidence=decision.confidence,
            ))

            # ── Step 7: EXECUTE ──
            if decision.direction != "HOLD":
                execution = await state.executor.execute(decision)
                state.waterfall_steps.append(WaterfallStep(
                    phase="EXECUTE",
                    title=f"{decision.direction} ${decision.bet_amount:.2f} @ {market.yes_price:.3f}",
                    detail=f"Status: {execution.status} | {execution.error or 'OK'}",
                ))
                state.trade_decisions.append(decision)
            else:
                state.waterfall_steps.append(WaterfallStep(
                    phase="EXECUTE",
                    title="HOLD — edge insufficient",
                    detail=decision.rationale,
                ))

    state.last_scan = datetime.utcnow()


async def run_pipeline_loop():
    """Main pipeline loop — runs scans at configured intervals."""
    state.active = True
    while state.active:
        try:
            await run_pipeline_cycle()
        except Exception as e:
            print(f"[CHIMERA] Pipeline error: {e}")
        await asyncio.sleep(settings.oracle.rss_poll_interval_seconds)


# ── FastAPI App ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the pipeline loop on app startup."""
    task = asyncio.create_task(run_pipeline_loop())
    yield
    state.active = False
    task.cancel()
    await state.polymarket.close()


app = FastAPI(
    title="CHIMERA War Room API",
    description="Autonomous News-Driven Polymarket Trading Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API Endpoints for Dashboard ──

@app.get("/api/status")
async def get_status():
    return {
        "active": state.active,
        "scan_count": state.scan_count,
        "last_scan": state.last_scan.isoformat() if state.last_scan else None,
        "signals_detected": len(state.signals),
        "trades_executed": len(state.trade_decisions),
        "portfolio": state.executor.get_portfolio_summary(),
    }


@app.get("/api/signals")
async def get_signals(limit: int = 50):
    return [s.model_dump() for s in state.signals[-limit:]]


@app.get("/api/waterfall")
async def get_waterfall(limit: int = 50):
    return [w.model_dump() for w in state.waterfall_steps[-limit:]]


@app.get("/api/debates")
async def get_debates(limit: int = 10):
    debates = state.hydra.get_debate_log()[-limit:]
    return [d.model_dump() for d in debates]


@app.get("/api/graph")
async def get_graph():
    return state.ripple.get_graph_data()


@app.get("/api/trades")
async def get_trades(limit: int = 50):
    return [t.model_dump() for t in state.trade_decisions[-limit:]]


@app.get("/api/markets")
async def get_markets(limit: int = 50):
    markets = state.polymarket.get_cached_markets()[:limit]
    return [m.model_dump() for m in markets]


@app.get("/api/portfolio")
async def get_portfolio():
    return state.executor.get_portfolio_summary()


@app.post("/api/scan")
async def trigger_scan():
    """Manually trigger a pipeline scan cycle."""
    await run_pipeline_cycle()
    return {"status": "scan_complete", "scan_count": state.scan_count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.server.host, port=settings.server.port)

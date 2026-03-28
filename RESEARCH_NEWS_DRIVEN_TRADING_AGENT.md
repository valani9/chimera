# Autonomous News-Driven Polymarket Trading Agent: Deep Research Report

---

## 1. REAL-TIME NEWS APIs AND DATA SOURCES

### 1.1 NewsAPI.org
- **Coverage**: 50,000+ sources globally
- **Free tier**: 100 requests/day, development use ONLY (cannot be used in production/staging)
- **Paid**: Starts at $449/month -- massive jump from free
- **Latency**: Low-latency queries, suitable for tickers and alerts
- **Limitation**: Free tier articles are delayed, not truly real-time
- **Verdict**: Good for prototyping, too expensive and restricted for production free-tier use

### 1.2 GDELT (Global Database of Events, Language, and Tone)
- **Update frequency**: Every 15 minutes ("15-minute heartbeat")
- **Coverage**: Translates 98.4% of non-English content across 65 languages in real-time
- **Processing**: Within 15 minutes of a news report breaking anywhere in the world, GDELT has translated it, processed it, and identified all events, counts, quotes, people, organizations, locations, themes, emotions, imagery, video, and embedded social media
- **Trend detection**: Rolling 60-minute window for anomaly detection, compared against previous 3 days
- **Cost**: FREE -- open data, accessible via BigQuery (Google Cloud free tier gives 1TB/month of queries)
- **APIs**: DOC 2.0 API, GKG API, Event API, TV API
- **Best for**: Event detection, trend analysis, geopolitical monitoring
- **Limitation**: 15-minute granularity means it is not sub-second real-time

### 1.3 Event Registry / NewsAPI.ai
- **Coverage**: Excels in both archival and real-time news data
- **Best for**: Data mining, market intelligence, risk management, media monitoring
- **Free tier**: Limited (check current plans at newsapi.ai/plans)
- **Strength**: Strong event clustering and entity extraction built-in

### 1.4 Newsdata.io
- **Free tier**: Available and tested as working in 2026
- **Best for**: Simple news aggregation with category filtering
- **Documentation**: Well-maintained with tested free API endpoints

### 1.5 Twitter/X API
- **Official API pricing (2025-2026)**:
  - Basic: $200/month (very limited)
  - Pro: $5,000/month
  - Enterprise: up to $42,000/month
- **Filtered Stream**: Real-time streaming with keyword/account filtering via API v2
- **Breaking news detection**: Monitor specific high-signal accounts (journalists, officials, agencies)
- **Third-party alternatives**:
  - **TwitterAPI.io**: $0.15 per 1,000 tweets, pay-as-you-go, real-time streaming available
  - **SociaVault**: Multi-platform API with credit-based pricing
  - **Nitter instances**: Free but unreliable/getting shut down
- **Verdict**: Official API is prohibitively expensive. Use third-party providers or focused account monitoring

### 1.6 Reddit API
- **Free tier**: Available for non-commercial use, rate-limited
- **Key subreddits for early signals**: r/worldnews, r/politics, r/geopolitics, r/news, r/cryptocurrency
- **Tools**:
  - **ApeWisdom API**: Aggregates Reddit mentions (stocks/crypto focused)
  - **PRAW (Python Reddit API Wrapper)**: Standard library for Reddit access
  - Reddit-AI-Trends: Automated scanning with DeepSeek R1 analysis
- **Academic validation**: Research shows Reddit sentiment can be a leading indicator, especially for retail-driven events
- **ICE-Reddit collaboration** (2025): Institutional-grade Reddit data products for capital markets

### 1.7 Telegram Channel Monitoring
- **Best library**: Telethon (Python) -- most mature, well-documented
- **Alternative**: Pyrogram (Python) -- additional features
- **Capabilities**:
  - Real-time continuous scraping with state persistence
  - Media downloading and data export
  - SQLite per-channel storage (message ID, timestamp, sender, text, media)
  - CSV export for analysis
- **Key channels to monitor**: Breaking news channels, geopolitical analysts, crypto signal groups, journalist channels
- **Implementation**: Use Telegram API credentials (api_id, api_hash), not bot API (which cannot read channel history)
- **Open-source tool**: github.com/unnohwn/telegram-scraper -- production-ready with continuous scraping

### 1.8 RSS Aggregation at Scale
- **feedparser**: Gold standard Python library, but slow at scale (8s for 50k entries)
- **FastFeedParser** (by Kagi): 25x faster than feedparser, familiar API, powers Kagi Small Web processing thousands of feeds
  - GitHub: github.com/kagisearch/fastfeedparser
  - PyPI: `pip install fastfeedparser`
- **Scaling strategy**: Use `concurrent.futures` or `asyncio` with thread pools for parallel feed fetching
- **Recommended sources**: AP, Reuters, BBC, Al Jazeera, major wire services RSS feeds
- **Update frequency**: Most major news RSS feeds update within 1-5 minutes of publication

### 1.9 Recommended Data Source Stack (Cost-Optimized)
```
Priority 1 (FREE):     GDELT API (15-min event detection) + RSS via FastFeedParser
Priority 2 (FREE):     Reddit API via PRAW + Telegram via Telethon
Priority 3 (CHEAP):    TwitterAPI.io ($0.15/1k tweets) for breaking news accounts
Priority 4 (FREEMIUM): Newsdata.io free tier for supplementary coverage
Avoid:                 Official X API ($5k+/mo), NewsAPI.org paid ($449/mo)
```

---

## 2. LLMs FOR PROBABILITY ESTIMATION

### 2.1 Current State of the Art (ForecastBench, March 2026)

**Key benchmark**: ForecastBench -- 1,000 auto-generated forecasting questions, continuously updated

**Performance hierarchy** (Brier scores, lower = better):
| Forecaster | Brier Score |
|---|---|
| Superforecasters | 0.081 |
| GPT-4.5 (best LLM) | 0.101 |
| Human crowd median | ~0.110 (dropped to #22 on leaderboard) |
| Claude 3.7 | Outperformed GPT-4 on practical accuracy |
| Random chance | 0.250 |

**Trajectory**: LLM performance improves ~0.016 Brier points/year. Projected LLM-superforecaster parity: late 2026 (95% CI: Dec 2025 - Jan 2028).

### 2.2 Log Probability Method (arxiv 2501.04880)

First approach to exploit logprobs for forecasting:

**Pipeline**:
1. Reformulate and categorize the forecasting query
2. Search for global and local trends relevant to the event
3. Collect sources through semantic search over news providers
4. Extract significant events from headline data
5. Verify the event is non-exclusive
6. Calculate probability using ALL token logprobs (not just top-1 completion)

**Calibration**: Uses Support Vector Regression (SVR) to learn a transformation function between raw LLM logprob outputs and calibrated probabilities.

**Results**: Brier score of 0.186 -- 19% improvement over vanilla GPT-4o (0.236), competitive with prediction markets (0.100-0.200 range).

**Implementation insight**: Instead of asking "What is the probability of X?" and taking the text answer, extract the logprobs for all possible probability tokens (0-100) and compute a weighted average using exp(logprob) as weights.

### 2.3 LLM Ensemble Method ("Wisdom of the Silicon Crowd")

Published in Science Advances (2024), landmark study:

**Methodology**:
- Aggregate forecasts from 12 different LLMs
- Use **median** as aggregation mechanism (not mean)
- Tested on 31 binary questions vs 925 human forecasters over 3 months

**Key findings**:
- LLM ensemble is statistically indistinguishable from human crowd accuracy
- Median aggregation counteracts acquiescence bias in individual models
- Diversity of training data/architectures creates genuine "wisdom of crowds"

**Practical implementation**:
```python
# Pseudocode for ensemble forecasting
models = [gpt4, claude, gemini, llama, mistral, ...]
forecasts = [model.forecast(question, context) for model in models]
final_probability = np.median(forecasts)  # Simple median outperforms mean
```

### 2.4 Mantic AI: RL Fine-Tuning for Forecasting

Mantic (founded by ex-DeepMind researcher) -- ranked 4th out of 539 humans in Metaculus Cup:

**Architecture**:
1. **Research Phase**: Deep research agents collect contextual information (military movements, political statements, economic conditions, etc.)
2. **Prediction Phase**: LLM uses specialized tools to construct a **mixture model** -- parameterizing different scenarios with components, parameters, and weights to create a CDF

**RL Fine-Tuning Details**:
- Algorithm: Policy gradient with GRPO-style advantage normalization
- Reward: Brier score (bounded [0,1], more stable than log score)
- Dataset: ~10,000 binary questions from Aug 2024 - Dec 2025
- Infrastructure: Tinker platform, batch size 64, group size 8
- Result: gpt-oss-120b improved from 38.6 to 45.8 baseline points/question (matching frontier models)
- Key insight: Pre-generated research prompts + mixture model tools yielded 7-point improvement vs 3 points for model-only training

**Backtesting advantage**: AI can be backtested instantly by restricting knowledge to past information and replaying world events, collapsing evaluation latency from months to milliseconds.

### 2.5 Chain-of-Thought Prompting for Forecasting

Surprising finding from rigorous testing (arxiv 2506.01578):

- **Prompt engineering has minimal to nonexistent effect** on LLM forecasting performance across frontier, reasoning, and efficient models
- Several approaches (CoT, frequency-based reasoning) showed improved accuracy vs control, but **no prompt remained statistically significant after multiple comparison adjustment**
- A Superforecaster-authored Conditional Odds-Ratio Prompt actually **reduced** accuracy

**What DOES work**:
- Providing the model with rich, relevant context (news, data, base rates)
- Using retrieval-augmented generation to supply current information
- Ensemble aggregation across models
- RL fine-tuning on forecasting tasks

### 2.6 Calibration Techniques

**Verbalized probability calibration** (arxiv 2410.06707): Adjusting LLM explanations to better reflect internal confidence narrows both calibration and discrimination gaps.

**LogU framework** (arxiv 2502.00290): Logits-induced Token Uncertainty -- estimates token-specific uncertainty in real-time without multiple sampling rounds.

**Bayesian approaches** (Google Research, March 2026): Teaching LLMs to reason like Bayesians by training them to mimic optimal Bayesian model predictions. Key challenge: transformers systematically violate the martingale property (a cornerstone of Bayesian updating).

### 2.7 Human-LLM Augmentation

- LLM assistants improve human forecasting accuracy by 24-28% vs control
- LLM assistants with superforecasting prompts enhance accuracy by 23-43%
- Suggests hybrid human-AI systems currently outperform either alone

---

## 3. SUPERFORECASTING TECHNIQUES FOR AI

### 3.1 Tetlock's Core Principles (Encodable)

Philip Tetlock's research (IARPA-sponsored Good Judgment Project) identified these key traits of superforecasters:

1. **Granular probability thinking**: Use specific percentages, not vague terms ("70% likely" not "probably")
2. **Base rate reasoning**: Always start with the base rate (historical frequency)
3. **Frequent small updates**: Update beliefs incrementally as new evidence arrives (not big swings)
4. **Foxes not hedgehogs**: Draw from many information sources, not one grand theory
5. **Self-criticism**: Actively seek disconfirming evidence
6. **Distinguish signal from noise**: Not all new information warrants an update
7. **Decomposition**: Break complex questions into sub-questions (Fermi estimation)

### 3.2 Implementable Algorithms

**Reference Class Forecasting (Outside View)**:
```
1. Identify the relevant reference class (similar past events)
2. Obtain the base rate from that reference class
3. Adjust from base rate based on specific case factors (inside view)
4. Weight outside view heavily (60-80%) especially early on
```

Example: "Will Country X invade Country Y in 2026?"
- Reference class: All militarized interstate disputes since 1945
- Base rate: ~3% escalate to full invasion
- Inside view adjustments: troop movements (+5%), diplomatic breakdown (+3%), economic incentives (-2%)
- Final estimate: ~9%

**Bayesian Updating Formula**:
```
Posterior Odds = Likelihood Ratio * Prior Odds

Where:
- Prior odds = P(event) / (1 - P(event))
- Likelihood ratio = P(evidence | event) / P(evidence | no event)
- Convert back: P(event) = posterior_odds / (1 + posterior_odds)
```

**Inside vs Outside View Integration**:
```python
def integrate_views(base_rate, inside_view_estimate, evidence_strength):
    """
    evidence_strength: 0.0 (no unique info) to 1.0 (highly diagnostic)
    """
    # Weight outside view more when evidence is weak
    outside_weight = 1.0 - (evidence_strength * 0.6)
    inside_weight = 1.0 - outside_weight
    return (base_rate * outside_weight) + (inside_view_estimate * inside_weight)
```

### 3.3 AI Superforecasting Agent Architecture

Based on research findings, an optimal AI agent should:

1. **Multi-agent team structure**: Separate roles (researcher, base-rate analyst, devil's advocate, synthesizer)
2. **Outside-View Analyst agent**: Identifies reference classes and retrieves base rates from historical data
3. **Inside-View Analyst agent**: Processes current evidence specific to this question
4. **Devil's Advocate agent**: Generates arguments for opposite conclusion
5. **Synthesizer agent**: Integrates all views with appropriate weighting

Validated by research: Creating AI "teams" with roles like Outside-View Analyst focusing on reference classes and base rates provides historical context that improves accuracy.

### 3.4 Practical Calibration Training

Use historical prediction market data to calibrate:
1. Collect resolved questions from Metaculus, Polymarket, Good Judgment Open
2. For each question, recreate the information state at various time points
3. Have your system make predictions
4. Measure Brier score and calibration curve
5. Apply post-hoc calibration (isotonic regression or Platt scaling)

---

## 4. REAL-TIME EVENT DETECTION AND CLASSIFICATION

### 4.1 Breaking News Detection Pipeline

**Chronicle system architecture** (github.com/dukeblue1994-glitch/chronicle):

```
News Sources --> Content Extraction --> Deduplication --> Embedding --> Clustering --> Summarization
     |                |                    |                |              |              |
  RSS/APIs    Readability+BS4     MinHash LSH        Sentence-     HDBSCAN      TF-IDF
              + lxml parsing      (85% threshold)    Transformers  (density-    weighted
                                  128 permutations   all-MiniLM-   based with   sentence
                                  4-gram shingling   L6-v2         auto-        extraction
                                                     384-dim       outlier
                                                     vectors       detection)
```

### 4.2 Deduplication (Critical for Noise Reduction)

**MinHash LSH approach**:
- 128 hash permutations for signature generation
- 4-gram shingling for text tokenization
- Jaccard similarity threshold: 0.85
- Achieves O(n) processing time (sub-linear for near-duplicate detection)
- Prevents duplicate stories from inflating cluster importance

### 4.3 Semantic Embedding for News

**Primary**: Sentence-Transformers (`all-MiniLM-L6-v2`)
- 384-dimensional semantic vectors
- Normalized L2 vectors for efficient similarity computation
- ~100ms per document on CPU

**Fallback**: TF-IDF with 4096 features and bigram analysis (no GPU required)

### 4.4 Clustering for Event Detection

**Primary: HDBSCAN**
- Density-based clustering with automatic outlier detection
- Probabilistic membership scores (soft clustering)
- Minimum cluster size: 3 documents
- Handles irregular cluster shapes
- No need to specify number of clusters in advance

**Fallback: Agglomerative Clustering**
- Cosine distance threshold: 0.6
- Deterministic, reproducible results

### 4.5 Breaking News vs Noise Classification

Key signals for "breaking" classification:
1. **Velocity**: Rate of new articles appearing in a cluster (articles/minute)
2. **Source diversity**: Number of independent sources reporting (>3 sources = likely real)
3. **Novelty score**: Semantic distance from any existing cluster (high = genuinely new)
4. **Entity prominence**: Named entities involved (head of state > local official)
5. **Temporal clustering**: Multiple articles within <15 minutes = breaking

**LLM-enhanced approach** (arxiv 2406.10552):
- Use LLMs for pre-event detection tasks (keyword extraction, text embedding)
- Post-event detection tasks (event summarization, topic labeling)
- Significantly improves clustering quality over pure statistical approaches

### 4.6 Event Extraction from Unstructured Text

Modern pipeline (transformer-based):
1. **Trigger identification**: Detect event trigger words ("attacked", "signed", "announced")
2. **Event type classification**: Map to ontology (conflict, diplomacy, economic, election, etc.)
3. **Argument extraction**: Who, What, When, Where, How
4. **Temporal reasoning**: Extract and normalize dates/times, determine event timeline ordering

**LLM advantage**: LLMs can perform all four steps in a single pass with appropriate prompting, avoiding the error propagation of sequential pipelines.

### 4.7 Practical Implementation Pattern

```python
# Simplified real-time event detection loop
async def event_detection_loop():
    while True:
        # 1. Ingest from multiple sources
        articles = await gather(
            fetch_gdelt_updates(),        # Every 15 min
            fetch_rss_feeds(),            # Every 1-2 min
            fetch_telegram_messages(),    # Real-time
            fetch_twitter_mentions(),     # Near real-time
        )

        # 2. Deduplicate
        unique_articles = minhash_dedup(articles, threshold=0.85)

        # 3. Embed
        embeddings = sentence_transformer.encode(unique_articles)

        # 4. Cluster with existing events
        clusters = hdbscan_cluster(embeddings, min_cluster_size=3)

        # 5. Detect NEW clusters (breaking news)
        new_clusters = identify_novel_clusters(clusters, existing_events)

        # 6. For each new cluster, classify and assess relevance
        for cluster in new_clusters:
            event_type = llm_classify(cluster)
            relevance = match_to_polymarket_questions(event_type)
            if relevance > threshold:
                trigger_trading_pipeline(cluster, relevance)

        await asyncio.sleep(60)  # Check every minute
```

---

## 5. OPEN-SOURCE PROJECTS: LLMs + PREDICTION MARKETS

### 5.1 Polymarket/agents (Official)
- **GitHub**: github.com/Polymarket/agents
- **License**: MIT
- **Stack**: Python 3.9+, LangChain, ChromaDB, OpenAI, Pydantic, Docker
- **Architecture**: CLI-driven with modular APIs (Gamma, CLOB, Chroma), RAG pipeline
- **Key SDKs**: py-clob-client (trading), python-order-utils (order signing)
- **How it works**: Fetches markets via Gamma API -> enriches with news via ChromaDB RAG -> processes through LLM -> executes trades via CLOB API

### 5.2 OpenClaw + PolyClaw
- **What**: Autonomous AI agent framework accepting natural-language instructions
- **LLM brain**: Claude 3.7 Sonnet or GPT-4.5
- **Unique feature**: LLM-powered hedge discovery via contrapositive logic
- **Plugin architecture**: Modular "skills" for different capabilities

### 5.3 Polystrat (by Polymarket)
- **What**: Autonomous AI trading agent for Polymarket
- **Interface**: Plain-English goal setting
- **Capabilities**: Watches markets, rebalances positions, executes trades 24/7
- **Released**: February 2026

### 5.4 PredictOS
- **GitHub**: github.com/PredictionXBT/PredictOS
- **What**: Open-source all-in-one framework for prediction markets

### 5.5 Kalshi News Bot Pattern
- **Approach**: Claude AI analyzes breaking news -> identifies mispriced events -> places trades
- **Relevant pattern**: Same architecture works for Polymarket

### 5.6 TypeScript Polymarket Bot
- **7 automated strategies**: Arbitrage, convergence, market making, momentum, AI forecast
- **Includes**: Whale tracker and real-time dashboard

### 5.7 Key Tools Ecosystem

**Curated list**: github.com/aarora4/Awesome-Prediction-Market-Tools (150+ tools)

Notable for agent development:
- **Polymarket py-clob-client**: Official Python SDK for CLOB trading
- **polymarket-apis (PyPI)**: Unified package with Pydantic validation covering CLOB, Gamma, Data, Web3, Websockets, GraphQL
- **Dome API**: Unified API for real-time and historical prediction market data
- **Metaforecast.org**: Meta search engine aggregating probability estimates across platforms
- **Adjacent News (adj.news)**: Forward-looking news with prediction market-driven APIs
- **Polyseer**: Open-source multi-agent analytics with Bayesian probability aggregation

### 5.8 Polymarket API Architecture

```
Gamma API (gamma-api.polymarket.com)     --> Market discovery, metadata, prices
CLOB API (clob.polymarket.com)           --> Order book, trading, order execution
Data API                                  --> Positions, trade history, user data

Key SDK methods:
  client.get_markets()                    --> List all markets
  client.get_order_book(token_id)         --> Get order book for a market
  client.get_midpoint(token_id)           --> Get current mid price
  client.create_order(order_args)         --> Place an order
  client.cancel_order(order_id)           --> Cancel an order
```

---

## 6. RECOMMENDED ARCHITECTURE FOR YOUR AGENT

Based on all research findings, here is the optimal architecture:

```
                    DATA LAYER
    ┌──────────────────────────────────────────┐
    │  GDELT (15-min)  │  RSS/FastFeedParser   │
    │  Telegram/Telethon│  TwitterAPI.io        │
    │  Reddit/PRAW      │  Newsdata.io          │
    └──────────────────┬───────────────────────┘
                       │
                 EVENT DETECTION
    ┌──────────────────┴───────────────────────┐
    │  MinHash LSH Dedup (85% threshold)       │
    │  Sentence-Transformer Embeddings         │
    │  HDBSCAN Clustering                      │
    │  Novelty Detection (new cluster = break) │
    │  LLM Event Classification                │
    └──────────────────┬───────────────────────┘
                       │
              MARKET MATCHING
    ┌──────────────────┴───────────────────────┐
    │  Polymarket Gamma API (active markets)   │
    │  Semantic similarity: event <-> question │
    │  Filter to relevant, liquid markets      │
    └──────────────────┬───────────────────────┘
                       │
            PROBABILITY ESTIMATION
    ┌──────────────────┴───────────────────────┐
    │  Multi-Agent Superforecaster System:     │
    │    1. Base Rate Agent (reference class)   │
    │    2. Evidence Agent (current news)       │
    │    3. Devil's Advocate Agent              │
    │    4. Synthesizer (Bayesian integration)  │
    │                                          │
    │  LLM Ensemble (median of 3+ models)      │
    │  Logprob extraction + SVR calibration    │
    │  Post-hoc calibration (Platt scaling)    │
    └──────────────────┬───────────────────────┘
                       │
              TRADING DECISION
    ┌──────────────────┴───────────────────────┐
    │  Compare: our_probability vs market_price │
    │  Edge threshold: |delta| > 5%            │
    │  Kelly criterion for position sizing     │
    │  Risk management (max position, max loss)│
    └──────────────────┬───────────────────────┘
                       │
               EXECUTION
    ┌──────────────────┴───────────────────────┐
    │  Polymarket py-clob-client               │
    │  Limit orders at favorable prices        │
    │  Position monitoring + auto-exit         │
    └──────────────────────────────────────────┘
```

### Key Implementation Priorities

1. **Start with GDELT + RSS** -- free, reliable, good coverage
2. **Use LLM ensemble (3+ models, median aggregation)** -- proven to match human crowds
3. **Implement reference class forecasting** -- the single most impactful technique
4. **Logprob-based probability extraction** -- 19% improvement over naive prompting
5. **HDBSCAN clustering for event detection** -- handles noise well, auto-detects outliers
6. **MinHash LSH dedup** -- critical for preventing duplicate signal amplification
7. **Bayesian updating loop** -- continuously revise estimates as new evidence arrives

---

## SOURCES

### News APIs & Data Sources
- [Best News API 2025: 8 Providers Compared](https://newsapi.ai/blog/best-news-api-comparison-2025/)
- [10 News APIs for Developers in 2025](https://finlight.me/blog/news-apis-for-developers-in-2025)
- [Free News APIs That Work in 2026](https://newsdata.io/blog/best-free-news-api/)
- [NewsAPI.org Pricing](https://newsapi.org/pricing)
- [GDELT 2.0: Our Global World in Realtime](https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/)
- [GDELT DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [Breaking News Detection with GCP Timeseries Insights](https://blog.gdeltproject.org/identifying-breaking-online-news-stories-across-the-world-in-realtime-with-the-gcp-timeseries-insights-api-natural-language-api/)

### Twitter/X & Social Media
- [Twitter API Alternatives 2026](https://twitterapi.io/articles/twitter-api-alternatives-tools-for-developers-2026)
- [Affordable Real-Time X API](https://twitterapi.io/twitter-stream)
- [Top Twitter/X Data API Providers 2026](https://www.netrows.com/blog/top-twitter-x-data-api-providers-2026)
- [X Developer Platform Docs](https://docs.x.com/overview)
- [Reddit Sentiment Analysis Strategy with Alpaca](https://alpaca.markets/learn/reddit-sentiment-analysis-trading-strategy)

### Telegram & RSS
- [Telegram Scraper (GitHub)](https://github.com/unnohwn/telegram-scraper)
- [Scraping Telegram Using APIs](https://substack.thewebscraping.club/p/scraping-telegram-channels)
- [FastFeedParser (GitHub/Kagi)](https://github.com/kagisearch/fastfeedparser)

### LLM Forecasting & Calibration
- [Leveraging Log Probabilities for Forecasting (arxiv 2501.04880)](https://arxiv.org/html/2501.04880v1)
- [Wisdom of the Silicon Crowd (Science Advances)](https://www.science.org/doi/10.1126/sciadv.adp1528)
- [ForecastBench](https://www.forecastbench.org/)
- [How Well Can LLMs Predict the Future? (Forecasting Research Institute)](https://forecastingresearch.substack.com/p/ai-llm-forecasting-model-forecastbench-benchmark)
- [Training LLMs to Predict World Events (Mantic)](https://thinkingmachines.ai/news/training-llms-to-predict-world-events/)
- [Prompt Engineering LLMs' Forecasting Capabilities (arxiv 2506.01578)](https://arxiv.org/pdf/2506.01578)
- [AI-Augmented Predictions: LLM Assistants Improve Accuracy](https://dl.acm.org/doi/full/10.1145/3707649)
- [Can Language Models Use Forecasting Strategies?](https://arxiv.org/html/2406.04446v1)
- [Teaching LLMs to Reason Like Bayesians (Google Research)](https://research.google/blog/teaching-llms-to-reason-like-bayesians/)
- [Calibrating Verbalized Probabilities (arxiv 2410.06707)](https://arxiv.org/html/2410.06707v1)
- [Estimating LLM Uncertainty with Evidence (arxiv 2502.00290)](https://arxiv.org/html/2502.00290)

### Superforecasting
- [Superforecasting by Philip Tetlock (Summary)](https://jamesstuber.com/super-forecasting/)
- [Tetlock on Superforecasting (EconTalk)](https://www.econtalk.org/philip-tetlock-on-superforecasting/)
- [Can AI Agents Mimic a Superforecasting Team?](https://www.underthesurface.blog/p/can-ai-agents-mimic-a-superforecasting)
- [Reference Class Forecasting](https://assetmechanics.org/insights/reference-class-forecasting/)

### Event Detection & NLP
- [Chronicle: Event Detection System (GitHub)](https://github.com/dukeblue1994-glitch/chronicle)
- [LLM Enhanced Clustering for News Event Detection (arxiv 2406.10552)](https://arxiv.org/abs/2406.10552)
- [Event Extraction in LLMs: Holistic Survey (arxiv 2512.19537)](https://arxiv.org/html/2512.19537v1)
- [Event Detection from Social Media Stream (arxiv 2306.16495)](https://arxiv.org/pdf/2306.16495)

### Prediction Market Tools & Agents
- [Polymarket/agents (GitHub)](https://github.com/Polymarket/agents)
- [Polymarket Developer Quickstart](https://docs.polymarket.com/quickstart/overview)
- [py-clob-client (GitHub)](https://github.com/Polymarket/py-clob-client)
- [Awesome Prediction Market Tools (GitHub)](https://github.com/aarora4/Awesome-Prediction-Market-Tools)
- [Awesome Polymarket Tools (GitHub)](https://github.com/harish-garg/Awesome-Polymarket-Tools)
- [Best Open-Source Prediction Market Bots 2026](https://agentbets.ai/guides/best-open-source-prediction-market-bots/)
- [Polymarket API Architecture (Medium)](https://medium.com/@gwrx2005/the-polymarket-api-architecture-endpoints-and-use-cases-f1d88fa6c1bf)
- [Polystrat AI Agent Launch](https://seczine.com/technology/2026/02/polymarket-launches-polystrat-ai-agent-for-autonom/)
- [OpenClaw Polymarket Bot Guide](https://skywork.ai/skypage/en/openclaw-polymarket-ai-trading/2036741591760736256)
- [Mantic AI](https://mntc.ai/)

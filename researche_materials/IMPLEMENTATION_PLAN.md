# Implementation Plan: Hybrid Quant+LLM Crypto Trading System

**Status:** v1.0, 2026-05-05. Companion to `LLM_LIMITATIONS_AND_RESEARCH_GAPS.md` and `THESIS_FINDINGS.md`.

---

## 0. Core architectural shift: LLM as modulator, not decider

Everything below is organized around a single structural change that the 2024-2026 literature converges on: **the LLM stack should modulate a quant signal, not compete with it.**

The current system treats LLM agents as an alternative signal source that runs in parallel with the V2 quant baseline (LGB term-structure consensus + SMA30). The mixed strategy (BTC=quant, ETH=LLM hybrid, Sharpe 2.94) was discovered empirically — it works, but it is ad hoc. The implementation plan below formalizes this into a principled hybrid architecture with three layers:

```
┌─────────────────────────────────────────────────────────┐
│                    LAYER 3: EXECUTION                   │
│  Portfolio Manager receives sized positions + regime    │
│  label + LLM narrative. Applies risk limits, executes.  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│                 LAYER 2: LLM MODULATOR                  │
│  Regime-conditional overlay on quant signal:             │
│  • Sentiment modifier (anonymized, fact/subj split)     │
│  • Narrative interpreter (event-driven adjustment)      │
│  • Confidence calibration (Self-MoA + isotonic)         │
│  • Verbal memory (FinCon CVRF weekly reflection)        │
│                                                         │
│  Output: multiplier ∈ [0.0, 1.5] on quant position     │
│          + narrative explanation for audit trail         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│              LAYER 1: QUANT SIGNAL ENGINE                │
│  LGB term-structure consensus (h=7, h=14 ensemble)      │
│  + deterministic signals (kimchi, funding, USDT flow)   │
│  + token unlock calendar                                │
│  + regime detector (HMM-3 + BOCPD)                      │
│                                                         │
│  Output: direction + magnitude + regime label            │
└─────────────────────────────────────────────────────────┘
```

### Why this matters for the thesis

The current defensible claim is "per-coin LLM augmentation." The hybrid architecture upgrades this to "regime-conditional LLM modulation of quant signals" — a stronger, more generalizable contribution that aligns with FINSABER (arXiv 2505.07078), FS-ReasoningAgent (arXiv 2410.12464), and the Springer 2026 unified agentic framework. It also directly explains the BTC failure: in a macro-driven bear regime, the LLM modulator weight should be low (0.2-0.3), so even poor BTC LLM signals get damped rather than amplified.

### Regime-conditional LLM weighting table

| Regime (HMM state) | LLM weight on position | Rationale |
|---|---|---|
| Bull-trending (H>0.55, ADX>25) | 0.2–0.3 | LLM is too conservative in trends (FINSABER); quant trend signal dominates |
| Sideways / transitional (HMM max_prob < 0.6) | 0.6–0.8 | Narrative-driven; LLM sentiment is additive (Singhi 2025, FS-ReasoningAgent) |
| Bear (drawdown > 10%, vol expanding) | 0.4 | Factual LLM helps risk control; quant overrides direction |

### Per-coin routing logic

| Asset | Primary signal | LLM role | Rationale |
|---|---|---|---|
| BTC | Quant (LGB consensus) | Regime confirmer + risk dampener only | BTC is macro-driven; LLM has persistent bearish bias (§2.1); narrative content is high-volume low-signal |
| ETH | Quant base + LLM modulator at full regime weight | Sentiment overlay + narrative interpreter | ETH price is narrative-driven (upgrades, DeFi, L2s); LLM adds genuine alpha (§2.2) |
| Altcoins (BNB, SOL, etc.) | Quant with LLM event-gating | Token unlock veto + event interpreter | Thinner news coverage; LLM primarily gates for supply events and structural risks |

---

## 1. Implementation roadmap

Items are grouped into three tiers: **Tier A** (core hybrid architecture, do first), **Tier B** (signal + calibration improvements), **Tier C** (advanced / long-term). Within tiers, items are ordered by expected impact per unit effort.

### Tier A — Core hybrid architecture (weeks 1-3)

These items collectively implement the Layer 1 → Layer 2 → Layer 3 stack above. They are the thesis contribution.

| # | Change | What to build | Difficulty | Cost | Expected Δ Sharpe |
|---|---|---|---|---|---|
| A1 | **Regime detector (HMM-3 + BOCPD ensemble)** | Train 3-state HMM on (returns, realized_vol, ADX, funding_rate). Add BOCPD changepoint detector. Majority-vote for regime label. Add Hurst exponent filter (H>0.55 = trending, H<0.45 = mean-reverting). Output: `{regime, confidence, hurst}` consumed by every downstream component. | Medium | $0 | +0.3–0.5 |
| A2 | **LLM modulator interface** | Replace the current "LLM generates a standalone trade decision" flow with a modulator API: LLM receives (quant_signal, regime_label, regime_confidence, news_summary, on_chain_summary) and outputs `{multiplier: float[0.0-1.5], narrative: str, confidence: float}`. The multiplier scales the quant position. Multiplier bounds are regime-conditional per the weighting table above. | Medium | $0 | +0.2–0.4 |
| A3 | **Per-coin routing** | Configuration-driven router that assigns each coin to a signal path: `quant_only`, `quant_plus_llm_modulator`, or `quant_plus_llm_event_gate`. BTC defaults to `quant_only` with LLM as regime confirmer. ETH defaults to `quant_plus_llm_modulator`. Altcoins default to `quant_plus_llm_event_gate`. Overrideable per regime. | Low | $0 | +0.1–0.2 |
| A4 | **Asset-name anonymization** | Replace literal coin names ("Bitcoin", "Ethereum") with "Asset X", "Asset Y" in analyst and debate prompts. Re-attach identity only at portfolio manager stage. One-day change addressing Glasserman & Lin (arXiv 2309.17322) training-corpus bias — the single most direct fix for BTC's persistent bearish LLM signals. | Low | $0 | +0.2–0.4 (BTC) |
| A5 | **Fact vs subjectivity split (FS-ReasoningAgent)** | Split the analyst layer into Factual agent (on-chain stats, price, derivatives) and Subjective agent (news tone, social sentiment). Add a Reflection agent that re-weights them by detected regime. Bull regime → upweight factual; sideways → upweight subjective. Directly explains BTC vs ETH asymmetry. | Medium | $0 | +0.2–0.4 |

**Tier A milestone:** At this point the system has a formal hybrid architecture with regime-conditional LLM weighting, per-coin routing, debiased prompts, and a fact/subjectivity split. This is the core thesis contribution and should be evaluated as a unit before proceeding.

**Evaluation checkpoint:** Re-run the 88-bar window with the Tier A stack. Compare against V2 quant baseline (Sharpe 3.31), current mixed strategy (2.94), and pure LLM hybrid (1.46). The target is Sharpe ≥ 3.0 with lower MaxDD than pure quant, demonstrating the LLM modulator adds risk management value even if raw return is similar.

---

### Tier B — Signal enrichment + calibration (weeks 3-5)

These items improve the quality of inputs to the hybrid stack and the calibration of its outputs.

| # | Change | What to build | Difficulty | Cost | Expected Δ Sharpe |
|---|---|---|---|---|---|
| B1 | **FinCon CVRF weekly reflection agent** | Weekly cron: read past 7 days of decisions, returns, and post-mortems. Distill into 3-5 sentence "investment beliefs." Persist to a beliefs store injected into next-decision context. Singhi (arXiv 2510.08068) reports +31% return on BTC from this alone. | Medium | tokens only | +0.2–0.4 |
| B2 | **Token unlock event module** | Ingest vesting schedules from Tokenomist/CryptoRank free tier. For any coin where `next_unlock_pct > 1%` AND recipient is VC/team/insider, inject a bearish prior into Layer 2 modulator during T-30 to T+14 window. ~90% of unlocks produce negative returns (Tokenomist 2023). Mechanical, rarely arbitraged. | Low | $0 | +0.2–0.4 |
| B3 | **Deterministic signal pack** | Add to Layer 1: kimchi premium zero-crossings (+1.7% avg 7d return, 67% win), funding rate Z-score (cross-sectional), USDT exchange netflow (Chi/Chu/Hao arXiv 2411.06327), NDF whale concentration (only on-chain factor surviving Harvey-Liu). Feed as structured features alongside LGB output. | Low | $29/mo (CryptoQuant Advanced) | +0.2–0.3 |
| B4 | **Pydantic structured outputs + PIT enforcement** | Adopt TradingAgents v0.2.4 Pydantic schemas for all agent outputs. Add 5-tier rating scale (strong buy → strong sell). Enforce `as_of_date < decision_date - 1 trading day` on every retrieval call. Non-negotiable per Look-Ahead-Bench (arXiv 2601.13770). | Low | $0 | +0.1–0.2 |
| B5 | **Verbalized P(up) + Self-MoA + isotonic calibration** | Have analysts output P(up) as a number. Run N=5 samples at T=0.4-0.6 via Self-MoA (arXiv 2502.00674 — single-model sampling beats multi-model mixing by +6.6%). Use std-dev as system uncertainty. Apply isotonic regression calibration on held-out period. Convert to position weight = f(verbalized_p, ensemble_disagreement, regime). | Low-Med | tokens | +0.1–0.3 |
| B6 | **Sentiment data expansion** | Add LunarCrush Individual ($24/mo), PulseReddit dataset (free, arXiv 2506.03861), CryptoBERT local (free). Apply market-derived labeling (arXiv 2502.14897) for BTC sentiment few-shots: label news by realized forward return sign → +11% BTC accuracy. | Low | $24/mo | +0.1–0.3 |
| B7 | **Asymmetric debate restructuring** | Cap bull/bear debates at 2 rounds (Du et al. ICML 2024). Add Skeptic-Quant third agent that compares LLM signal vs quant baseline. Give Bear agent stronger historical-analog context. Use third-person aggregator prompting (SYCON-Bench arXiv 2505.23840: 63.8% sycophancy reduction). Strip persona labels before aggregation (Choi et al. arXiv 2510.07517). | Low | $0 | +0.1–0.2 |
| B8 | **Hybrid RAG (BM25 + BGE-M3 + reranker)** | Replace current retrieval with BM25 + BGE-M3 dense hybrid, BGE-Reranker-v2-large cross-encoder (Akarsu et al. arXiv 2604.01733: Recall@5 = 0.816). Add historical analog retrieval: vectorize regime-feature tuples, retrieve top-K past 30-day windows with realized outcomes. Directly attacks FINSABER's bull-conservative/bear-aggressive pathology. | Medium | $0 (Qdrant/pgvector) | +0.1–0.2 |

**Tier B milestone:** The hybrid system now has calibrated confidence, richer inputs, episodic memory, and debiased debate. Total data cost: ~$53/mo.

---

### Tier C — Advanced / long-term (post-thesis or if time permits)

| # | Change | Difficulty | Cost | Expected Δ Sharpe |
|---|---|---|---|---|
| C1 | LoRA fine-tune open model (Llama/Qwen) on regime-labeled crypto corpus for sentiment subagent | High | ~$262 one-time | +0.3–0.6 |
| C2 | SFT+RL on small open reasoning model along Trading-R1 lines (arXiv 2509.11420) | Very high | compute | +0.3–0.6 |
| C3 | Cross-model validation (Claude Haiku 4.5, DeepSeek V4-Flash) for model-robustness claim | Low | ~$15/run | robustness |
| C4 | Bull-regime OOS window (2025-Q4) to test regime robustness | Low | ~$5 | robustness |
| C5 | Walk-forward parameter selection for hybrid sizing (aw, cap, dw) | Low | $0 | robustness |
| C6 | Forward paper validation on Binance testnet (30 days) | Low | ~$30/mo API | robustness |

---

## 2. What changes from the current codebase

### Current flow (app.py / LangGraph)
```
News/OnChain/Price data
  → Market Analyst → On-Chain Analyst → Sentiment Analyst → Prediction Analyst
    → Bull/Bear Debate (1 round)
      → Trader
        → Risk Debate
          → Portfolio Manager → {BUY/SELL/HOLD, confidence}
```

### Target flow (hybrid architecture)
```
Price/Indicator data
  → LAYER 1: LGB ensemble (h=7, h=14) → direction + magnitude
  → LAYER 1: Regime detector (HMM-3 + BOCPD + Hurst) → regime label + confidence
  → LAYER 1: Deterministic signals (kimchi, funding, USDT, NDF, unlocks)
  │
  ├─ Per-coin router checks asset config
  │   ├─ quant_only path (default BTC): Layer 1 output → PM directly
  │   ├─ quant_plus_llm_modulator path (default ETH):
  │   │     News/OnChain/Sentiment → Factual Agent + Subjective Agent
  │   │       → Regime-weighted merge
  │   │         → Asymmetric Debate (2 rounds, Bull + Bear + Skeptic-Quant)
  │   │           → Modulator: outputs multiplier ∈ [0.0, 1.5] on quant position
  │   │             → Self-MoA N=5 → calibrated confidence
  │   │               → PM receives: (quant_signal × multiplier, regime, narrative)
  │   └─ quant_plus_llm_event_gate path (default altcoins):
  │         Unlock calendar + event scan → LLM veto/confirm only
  │           → PM receives: (quant_signal, gate_flag, event_narrative)
  │
  → LAYER 3: Portfolio Manager
      → Inputs: sized positions per coin + regime label + narratives
      → Risk limits, correlation check, execution
  │
  → Weekly: CVRF Reflect agent reads decision log → updates beliefs store
```

### Key interface contracts

**Layer 1 → Layer 2 (quant → LLM modulator):**
```python
@dataclass
class QuantSignal:
    coin: str
    direction: Literal["long", "short", "flat"]
    magnitude: float          # LGB expected return, normalized
    regime: Literal["bull", "sideways", "bear"]
    regime_confidence: float  # HMM max posterior probability
    hurst: float              # trending vs mean-reverting
    deterministic_signals: dict  # kimchi, funding_z, usdt_netflow, ndf, unlock_flag
```

**Layer 2 → Layer 3 (LLM modulator → PM):**
```python
@dataclass
class ModulatedPosition:
    coin: str
    quant_direction: str
    quant_magnitude: float
    llm_multiplier: float     # [0.0, 1.5], regime-bounded
    llm_confidence: float     # calibrated, from Self-MoA
    llm_uncertainty: float    # std-dev across N=5 samples
    narrative: str            # 2-3 sentence audit trail
    regime: str
    route: Literal["quant_only", "quant_plus_llm_modulator", "quant_plus_llm_event_gate"]
```

---

## 3. Validation requirements before defense

These are ordered by priority, matching §4 of `LLM_LIMITATIONS_AND_RESEARCH_GAPS.md` but now scoped to the hybrid architecture:

| # | Validation | Time | Why critical |
|---|---|---|---|
| V1 | Pre-cutoff placebo run (gpt-4o-mini, Oct 2023 cutoff) on hybrid stack | 0.5 day | Standard LLM-finance control. If ETH alpha persists with old model, claim is methodologically sound. |
| V2 | Block-bootstrap Sharpe CI on hybrid vs quant vs pure-LLM | 0.5 day | Promotes headline result from descriptive to inferential. |
| V3 | BTC LLM signal post-mortem: cluster wrong-direction calls by cause | 1-2 days | Documents the failure mode that motivates per-coin routing. |
| V4 | Ablation: hybrid with anonymization ON vs OFF | 0.5 day | Isolates the debiasing effect. |
| V5 | Ablation: hybrid with regime-conditional weighting vs fixed weighting | 0.5 day | Isolates the regime contribution. |
| V6 | Cross-model validation (Claude Haiku 4.5) on ETH modulator leg | 1-2 days | Model-robustness claim. |
| V7 | Bull-regime OOS window (2025-Q4) | 1 day | Regime-robustness claim. |

Minimum bar for defense: V1 + V2 + V3 + V4 + V5 (≈4 days of work).

---

## 4. Data stack summary

| Source | Cost | What it provides | Layer |
|---|---|---|---|
| CoinMetrics Community | Free | Active addresses, NVT, hash rate, supply metrics | Layer 1 |
| DefiLlama | Free | TVL, protocol revenue, fee data | Layer 1 |
| Coinglass | Free | Funding rates, open interest, liquidations | Layer 1 |
| Tokenomist / CryptoRank | Free tier | Vesting schedules, unlock calendar | Layer 1 |
| Dune free | Free | PIT on-chain queries with block_time filters | Layer 1 |
| CryptoPanic | Free | News aggregation with community bull/bear votes | Layer 2 |
| PulseReddit dataset | Free | Hourly Reddit-aligned market data (arXiv 2506.03861) | Layer 2 |
| CryptoBERT (local) | Free | Deterministic sentiment baseline | Layer 2 |
| Alpaca News (existing) | Existing | PIT news firehose | Layer 2 |
| GDELT + F&G (existing) | Existing | PIT macro sentiment | Layer 2 |
| CryptoQuant Advanced | $29/mo | Kimchi premium, Coinbase premium, exchange netflows, SOPR | Layer 1+2 |
| LunarCrush Individual | $24/mo | Galaxy Score, AltRank, social sentiment (2000+ coins) | Layer 2 |
| **Total incremental** | **$53/mo** | | |

---

## 5. Key academic references

| Short cite | arXiv / DOI | Finding relevant to this plan |
|---|---|---|
| FINSABER | 2505.07078 | LLM agents "too timid in uptrends, too reckless in downturns" — validates hybrid approach |
| FS-ReasoningAgent | 2410.12464 | Fact vs subjectivity split; regime-conditional re-weighting explains BTC vs ETH |
| FinCon | 2407.06567 | CVRF weekly reflection → +31% return on BTC (Singhi replication) |
| Glasserman & Lin | 2309.17322 | Asset-name anonymization improves LLM trading P&L |
| Choi et al. | 2510.07517 | Identity-anonymized debate reduces aggregator bias |
| Self-MoA | 2502.00674 | Single-model N-sampling > multi-model mixing (+6.6%) |
| Trading-R1 | 2509.11420 | TauricResearch's own post-debate evolution: SFT+RL |
| Tian et al. | 2305.14975 | "Just Ask for Calibration" reduces ECE ~50% |
| Chi/Chu/Hao | 2411.06327 | USDT exchange netflow predicts BTC/ETH returns |
| Sakkas & Urquhart | J. Int'l Fin Mkts 94 | NDF (whale concentration) only on-chain factor surviving Harvey-Liu |
| Singhi | 2510.08068 | Adaptive multi-agent BTC system with reflection agent |
| Look-Ahead-Bench | 2601.13770 | PIT date filtering is non-negotiable for LLM finance |
| Akarsu et al. | 2604.01733 | BM25+dense hybrid wins RAG benchmarks on financial docs |
| Springer 2026 | unified agentic framework | +0.373 Sharpe net of costs with LLM + regime + tail-risk |
| arXiv 2502.14897 | market-derived labeling | +11% BTC accuracy from return-sign-labeled few-shots |
| Tokenomist 2023 | industry study | ~90% of token unlocks produce negative returns |

---

## 6. Thesis framing of the contribution

With the hybrid architecture in place, the defensible thesis claim becomes:

> We empirically demonstrate that multi-agent LLM systems function optimally as **regime-conditional modulators** of quantitative trading signals, not as standalone signal generators. On a bear-to-sideways evaluation window, the hybrid architecture achieves [Sharpe TBD] with lower maximum drawdown than pure-quant, while the per-coin routing policy (BTC=quant-only, ETH=quant+LLM-modulator) captures [X]% of quant risk-adjusted return with interpretable, narrative-aware decision audit trails.
>
> This finding reproduces FINSABER's (2025) diagnosis on cryptocurrency — a previously untested asset class — and confirms FS-ReasoningAgent's regime-conditional ablation pattern via the BTC vs ETH asymmetry. The contribution is architectural: a three-layer hybrid stack (quant engine → LLM modulator → portfolio manager) with formal regime detection, asset-name anonymization, and fact/subjectivity decomposition that addresses documented LLM trading pathologies.

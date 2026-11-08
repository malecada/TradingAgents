# Charter 1 — Multi-agent v2 development run (`llm-v2-charter1`) — DRAFT, NOT FROZEN

**Status:** draft written 2026-11-08 while the corpora are being ingested. It is frozen (hashes, budget,
exact windows) only after the two-week pilot has measured cost and validity (plan §10, week 3–4). No
dev-window result may be looked at before the freeze commit.
**Parent plan:** `docs/superpowers/specs/2026-11-08-multiagent-v2-analysis-and-plan.md`.
**Prior cycle:** Charter 0 (`llm-v2-charter0-2026-11-09`) FAIL → dossier carries summaries and numeric cards,
no typed-event store.

## 1. Question
Does the dossier-fed, anonymized, order-debiased multi-agent system (DeepSeek V4-Pro in every judgment role)
produce weekly cross-sectional forecasts with detectable skill, and does it add forecast skill over the
quant-only cross-sectional model fed identical cards?

## 2. Target and universe
- Universe: weekly top-50 Binance USDT perpetuals by trailing 30-day dollar volume from the card panel
  (PIT: cards computed from trailing data; universe membership chosen on the Friday itself).
- Decision time: Saturday 00:00 UTC after each Friday card; text admissible iff `as_of_ts <= decision time`.
- Target: y = 1[asset's return Friday close → next Friday close exceeds the universe median return].
  Forecast: `p_outperform` ∈ [0,1] per asset-week.
- Dev window: Fridays 2022-01-07 → 2024-12-27 (156 weeks, 7,800 asset-weeks). Sealed-A 2025-01 → 2026-04,
  Sealed-B 2026-05 → 2026-12-11: untouched by this charter.

## 3. Frozen inputs (hashes recorded at freeze)
- Dossier builder version and anonymizer dictionary; dossier files (one hash per file, manifest hashed).
- Agent config sha (`tradingagents/agents_v2/graph.py::config_sha`): prompts and schemas.
- Model pins: `deepseek/deepseek-v4-pro` on Baidu fp8, reasoning effort medium, temperature 0; Flash for typing.
- Text sources admitted: Wayback captures of CoinDesk, Cointelegraph, The Block (as_of = first capture);
  Arctic Shift Reddit posts for r/CryptoCurrency, r/Bitcoin, r/ethereum (as_of = created; scores are
  retrieval-time and used for nothing). Alpaca/Benzinga store if synced before freeze.
- Forward returns from the 799-symbol daily kline store.

## 4. Pre-run validity probes (pilot, two dev weeks, STOP on fail)
| Probe | Floor |
|---|---|
| Schema-valid answers | ≥ 0.99 of calls |
| Order-swap consistency: Spearman between judge p in bull-first vs bear-first across debated assets | ≥ 0.75 |
| Repeat agreement: Spearman of p across two identical runs on 50 assets | ≥ 0.85 |
| Re-identification: asset accuracy on 300 anonymized dossiers | ≤ 2× chance (≈ 4% for ~50 candidates) |
| Re-identification: month within ±6 months | ≤ 25% |
| Dossier noise share (price recaps + promotional + unrelated among retrieved) | reported; ≤ 0.6 of retrieved |
| Measured cost per asset-week | recorded; budget set at 1.3× projection |

## 5. Gates (dev window, forecast quality before any portfolio claim)
| Gate | Floor |
|---|---|
| Residualized weekly rank IC (controls: vol_ewma20, ret_4w, size_rank), Newey-West lag 4 | t ≥ 2.0 |
| Brier skill vs base rate 0.5 | > 0 |
| Calibration slope (quintiles) | within [0.7, 1.3] |
| Incremental: system IC ≥ quant-only ridge IC on common weeks | required |
| Sub-periods (2022, 2023, 2024) | same sign of mean IC in ≥ 2 of 3 |

Portfolio gates (only if all forecast gates pass): rule-twin and PM books, taker costs 5 bp per side plus
funding, net SR ≥ 0.8, dual-family placebo (shuffled dates, shuffled assets) p ≤ 0.05, DSR at the declared
trial count (1 configuration; ablations are descriptive).

## 6. Ablations (10% stratified subsample, descriptive, no gate)
Leave-one-analyst-out (3); no debate; named vs anonymized dossiers; text-free (numeric only); Flash in all roles;
Claude Opus 5.5 in judgment roles (optional, ≤ $120); V3.2 chronological control on 2025-12 → 2026-12.

## 7. Stop rules, budget, attribution
- One configuration; prompts, schemas, builder version and model pins frozen at registration; any change after
  the first dev call is a new charter.
- Spend cap: set at freeze from the pilot (plan estimate ≈ $530 for the dev run at pro-judgment prices).
- Family: `llm-multiagent-v2` (new mechanism: dossier-fed debate on anonymized cross-section), attempt budget 6,
  prior attempts 0. The legacy multi-agent cells (THESIS §23, §48) are a different mechanism (tool-fetching
  agents on named daily BTC/ETH) and are cited as history.
- Disclosures: Wayback capture survivorship; Reddit deletions; cards end 2026-06-26; model cutoff unknown
  (release-date bound 2026-04-24); dev window is pre-release so memorization is controlled only by
  anonymization and measured by the probes in §4 and the Sealed-B comparison.

# liq_fade_r1 — Independent Replication of the Intraday Liquidation-Cascade Fade

**Date**: 2026-07-29
**Branch**: `feature/xs-momentum`
**Experiment ID**: `liq_fade_r1`
**Status**: pre-registration draft — not yet committed to `gates.json`

## 1. Motivation

`liq_fade_i1` (THESIS §49) closed its dev gate at 2/3. Net SR +1.305 cleared the
1.0 floor and the dual-family placebo returned p = 0.002 in both families — the
minimum attainable at 500 draws, and the first time any lead in the post-rebuild
program (§45-§49) cleared a placebo test at all. Kill-tests confirmed the
mechanism detects timing rather than bookkeeping: a planted +50bp edge at real
event timing stayed significant, while a mistimed control collapsed to p = 0.59.

The single failure was DSR = 0.479 against a 0.9 bar. Decomposition (§49 F5)
showed DSR = 0.881 when computed on this experiment's own six trials; the
shortfall is therefore the ledger-cumulative multiplicity burden, not intrinsic
weakness of the effect. Relaxing that bar post-hoc for the one config that
happened to look good is precisely the bias the deflated Sharpe ratio exists to
prevent, so the dev verdict stands and the holdout remains sealed.

The house-consistent path forward is a fresh, independently pre-registered
replication carrying its own trial budget. This document specifies it.

Two prerequisites carried over from the §49 whole-branch review are treated as
mandatory rather than optional, and are folded into the probe set and the code
changes below:

1. The vol-drift confound was never excluded. §49 F9 reported an event-day
   volatility percentile of 0.966, which is close to tautological given the
   trigger is defined from the same return and volume series. The discriminating
   control — long-only on high `z_vol` *without* the `z_ret` crash condition —
   was never run, and the long/short inversion cannot substitute for it, since
   inversion flips the sign of any drift whatsoever.
2. `pct_change` in the engine relies on the pandas-2 default fill behaviour.
   The pandas-3 default change would silently alter gap-bar attribution.

## 2. A note on the DSR denominator

The house standard computes DSR against the ledger-cumulative trial count, now
120 rows. That denominator grows monotonically and never decreases, so under a
literal reading no future experiment can ever pass the DSR gate irrespective of
merit. The denominator is also dominated by trials that are not alpha searches
at all: 37 of the 120 belong to `factor_floor`, a baseline-calibration sweep,
and a further 20 to the `axis_*` design-sensitivity runs.

The resolution adopted here is the standard confirmatory/exploratory split.
Multiplicity correction attaches to a *search*: a grid, a sweep, a set of
candidate hypotheses screened against the same data. A single frozen hypothesis,
pre-registered in full before any of the replication data is touched and
evaluated on events disjoint from those used in discovery, constitutes a
separate confirmatory inference and carries n_trials = 1.

This is a deliberate amendment to the house standard, not an oversight, and is
declared here before the run rather than after it. To keep the choice fully
transparent, DSR is additionally computed and reported at two more
denominators — family scope and cumulative scope — as pre-registered
sensitivities. The gate binds on n = 1; the other two appear in the thesis so a
reader can see the entire picture and judge the amendment on its merits.

## 3. Hypothesis

Frozen from §49. One statement, no grid, no search:

> On Binance UM perpetuals ranked 51-150 by point-in-time monthly dollar volume
> over 2021-01-01 → 2025-03-31, the long-side fade of 1h proxy liquidation
> cascades — trigger `z_ret ≤ −3.5` AND `z_vol ≥ 3.5`, z-windows 2160/1440 bars,
> holding horizon H = 48 hours, 1/10 of capital per event, aggregate cap 1.0,
> risk-free 4.5%/yr on full capital, 20bps round-trip cost — earns a net Sharpe
> ratio of at least 1.0.

Every parameter is inherited unchanged from the §49 best config. Exactly two
things differ from the dev run, both declared in advance:

- **Universe**: ranks 51-150 instead of the top 50.
- **Costs**: 20bps instead of 10bps (§5).

## 4. Universe

The 1h store `data/xsect/klines_1h/` currently holds 217 symbols — the union of
the monthly top-50 selections over the 51-month dev window. The replication band
(monthly ranks 51-150, same window, same selector `monthly_top_n`) has a union
of 304 symbols and averages 83 symbols per month; early months carry fewer than
100 because fewer perpetuals were listed. 188 of the 304 are already present in
the store, leaving 116 to fetch at roughly 215MB. Free disk is 74GB.

The full 304-symbol band is used. 188 of those symbols also appear in the dev
top-50 union, but the universe is point-in-time monthly: dev traded symbol S
only in the months S ranked top-50, and the replication trades S only in the
months S ranked 51-150. The two runs therefore share no event — the samples are
disjoint by (symbol, month), not merely by symbol. Symbol identities are partly
shared, so idiosyncratic character is not perfectly independent; this is
recorded as a scope limitation rather than papered over.

As a pre-registered descriptive breakdown — a partition of the same run, not an
additional config and not an additional trial — results are also reported for
the 116-symbol never-top-50 subset, which carries no shared symbol identity with
the dev run at all.

The selection is frozen to `data/xsect/liq_fade_r1_universe.json` and committed
before any replication result is computed.

The holdout window 2025-04-01 → 2026-07-31 remains sealed and is not touched by
this experiment under any outcome.

## 5. Cost assumption

20bps round-trip, against 10bps in dev. Band names are smaller and wider-spread
than the dev top-50, and carrying the top-50 cost model onto them would invite
the obvious objection. §49 F6 established the effect is not cost-fragile
(SR 1.305 / 1.229 / 1.153 at 10 / 20 / 30bps), so the stricter assumption is
affordable. 10bps and 30bps are reported as sensitivities.

## 6. Probes

All four are blocking and run to completion before any gate is evaluated. P3
runs first, because it is the one that can invalidate the hypothesis outright.

**P3 — vol-drift control.** Long-only entries on `z_vol ≥ 3.5` with the
`z_ret ≤ −3.5` crash condition removed, holding the sizing, horizon, universe
and cost model identical to the primary. This isolates whether the returns come
from crash timing or from generic long exposure on high-volatility days.

- PASS iff control net SR **< 0.5** AND (primary net SR − control net SR) **≥ 0.75**.
- FAIL ⇒ verdict `NEGATIVE-confounded`. Gates G1-G3 are not evaluated, the
  result is written up as such, and the lead closes.

The separation term is only diagnostic of a confound when the primary itself is
strong. If the primary net SR falls below the G1 floor of 1.0, the verdict is
plain `NEGATIVE` on G1 and the P3 label is not applied, since a weak primary
cannot be said to be explained away by volatility drift. `NEGATIVE-confounded`
is therefore reserved for the case where the primary clears 1.0 and the control
tracks it.

**P0 — stamp alignment.** Timestamp-alignment correlation between the 1h bar
index and the event index, as in §49 (which returned 0.9999).

**P1 — proxy concordance.** Agreement between proxy-detected cascades and
benchmark cascade dates, restricted to band symbols. §49 achieved 5/5 on top-50
names; the band is thinner, so the criterion is ≥ 4/5.

**P2 — event-study floor.** Mean gross return per event must clear the +25bp
floor established in §47/§49.

## 7. Gates

Three gates, all required. Evaluated on the primary config only.

| Gate | Criterion |
|------|-----------|
| G1 | net SR ≥ 1.0 at 20bps |
| G2 | dual-family placebo p ≤ 0.05 in **both** families, 500 draws |
| G3 | DSR ≥ 0.9 at n_trials = 1 |

Reported alongside, explicitly **non-gate-bearing** and pre-declared so that no
post-hoc promotion is possible: the two remaining §49 dev survivors
(thr 2.5 / H 24 and thr 3.5 / H 24); costs at 10bps and 30bps; DSR at n = 13
(liquidation-family scope: `liq_mr_t1` 6 + `liq_fade_i1` 6 + this 1) and at
n = 121 (ledger-cumulative); and the never-top-50 subset breakdown. None of
these can rescue a G1-G3 failure.

## 8. Code changes

The backtest engine `tradingagents/xsect/liq_fade.py` is frozen and is not
edited at all. It contains no `pct_change` call — returns inside the engine come
from `np.log(close).diff()`, which is unaffected by the pandas-3 change.

The `pct_change` exposure is entirely in the runner and forensics layers, and
those calls take an explicit `fill_method=None`:

- `scripts/liq_fade_dev.py` lines 185, 188, 285, 523
- `scripts/liq_fade_forensics.py` line 66
- every `pct_change` in the new `scripts/liq_fade_repl.py`

`pyproject.toml` declares `pandas>=2.3.0` with no upper bound, so a future
`uv sync` can pull pandas 3 and silently change gap-bar attribution in exactly
these five places. The explicit argument is the fix; no version ceiling is
added, since the argument is valid in both major versions.

New runner `scripts/liq_fade_repl.py` imports the engine unchanged and differs
from `liq_fade_dev.py` only in universe file, cost constant, config set, and the
P3 control path.

The existing 26 `liq_fade` tests must stay green, which is what demonstrates the
engine was not modified in substance. New tests cover the P3 control path and
the frozen-config hash.

## 9. Outcomes

- **3/3 PASS** — the first GO of the post-rebuild program. The sealed holdout
  then becomes a justified one-shot confirmation, pre-registered separately as
  its own experiment.
- **P3 FAIL** — the §49 signal was generic high-volatility long drift. A clean,
  well-powered negative that closes the lead and retrospectively explains the
  §49 result.
- **G1 or G2 FAIL** — the effect is specific to the top-50 cross-section.
  Reported as a scope limitation on §49 rather than a refutation of it.
- **G3 FAIL alone** — reported with the full denominator sensitivity table; at
  n = 1 this would require a genuinely small effect size, which would be
  informative in itself.

Every outcome is written up as THESIS §50 and the trial is logged to
`data/rebuild/trial_ledger.jsonl` regardless of result.

## 10. Order of operations

Registration strictly precedes data.

1. Commit this spec.
2. Add the `liq_fade_r1` entry to `data/rebuild/gates.json` and commit.
3. Build and commit the frozen `liq_fade_r1_universe.json`.
4. Fetch the 116 missing band symbols.
5. Run P3, then P0-P2.
6. Run the primary and evaluate G1-G3.
7. Forensics, ledger entry, THESIS §50.

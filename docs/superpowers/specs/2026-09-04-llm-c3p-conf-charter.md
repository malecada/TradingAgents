# llm_c3p_conf — LLM pairwise ranking, confirmatory (registered 2026-09-04, run deferred)

Status: **REGISTERED, NOT RUN.** Gates key `llm_c3p_conf` in
`data/llm_pair_xs/gates.json`. Source: `master_thesis/LEADS_SCOPE_2026-09-02.md`
Lead 9; parent `llm_c3p_pair_xs` (§65: P2 residual IC +0.0079, NW-t 1.01,
LLM ≥ GBDT twin but insignificant). Decision under the user's afk autonomy
grant (2026-09-04): the recommended option — register now, run at ≥ 90 sealed
weeks (≈ 2027-01) with the F-window cards appended, not at 65 weeks now
(power: 65 weeks need IC ≈ 0.03, ≈ 4× the dev point estimate).

## Frozen pipeline (verbatim from the parent)

gpt-5.4-mini, temperature 0, k = 10 permutation-pairing rounds per week, every
pair in both orders in disjoint prompts, 20 duels per prompt, Bradley–Terry
via MM (200 iterations, α = 0.5 virtual-opponent prior), log-strength score,
weekly OLS residualization on {vol_ewma20, ret_4w, size_rank}; anonymized
cards from `data/llm_pair_xs/cards.parquet` (top-200 by 30-day median dollar
volume, monthly PIT). Cutoff hygiene: gpt-5.4-mini cutoff Aug-2025 — primary =
all sealed weeks on anonymized cards (P1 showed no memorization); sensitivity
= post-cutoff weeks; both reported.

## Gates (one run, cap $40)

Residual IC > 0 AND NW-t ≥ 2.0 (lag 4) on the primary; LLM residual IC ≥ the
GBDT twin on common weeks (twin refit on dev only). Holdout = the sealed weeks
2025-04-04 → ≥ 2026-12-25 (**H1** for this family); any F-window weeks used
here are thereby spent for this family.

## Trigger

Run when `cards.parquet` covers ≥ 90 Fridays after 2025-04-04 (extend the
card store first; the extension is a data fetch, not a design change).
Scripts: `scripts/llm_pair_xs_p2_run.py --window sealed`,
`scripts/llm_pair_xs_p2_score.py`. THESIS §84.

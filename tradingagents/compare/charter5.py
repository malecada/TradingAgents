"""Evaluation of the direct-comparison configuration (Charter 5).

The comparison score of an asset and week is the Bradley-Terry strength from the decided comparisons of its
text dossier with the dossiers of other assets of the same week; an asset without a dossier takes the neutral
score. The gate is the mean weekly coefficient of the within-week rank of that score in an OLS of the
within-week return rank on the existing quant forecast, the three controls of the earlier charters and three
attention controls. No model is fitted; the only estimated quantities are the weekly regression coefficients.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.agents_v2.evaluate import CONTROLS, newey_west_t
from tradingagents.compare.duel import NO_BASIS
from tradingagents.reader import features

GATE_T = 2.0                 # Newey-West t (lag 4) of the mean weekly coefficient of the comparison score, >=
GATE_YEARS = (2023, 2024)    # calendar years (of the Friday) in which the mean weekly coefficient must be positive
TEST_START = pd.Timestamp("2023-01-06", tz="UTC")
STORE_START = pd.Timestamp("2022-01-01", tz="UTC")
MIN_WEEK_ROWS = 15           # complete rows a week needs (as in the encompassing regression of Charters 1b and 2)
MIN_WEEK_DOSSIERS = 10       # assets with a dossier among them
MIN_GATE_WEEKS = 78          # weeks the statistic needs; with fewer the verdict is FAIL
SCORE, QUANT, RET = "cmp_score", "p_quant", "fwd_ret"
ATTENTION = ["attn_7d", "n_lines", "has_dossier"]
GATE_CONTROLS = [QUANT, *CONTROLS, *ATTENTION]
SPREAD_MIN = 9               # dossier assets a week needs for the tercile spread
BOOTSTRAP_DRAWS, BOOTSTRAP_SEED = 500, 20261115
PANEL_COLUMNS = ["date", "symbol", "base", *CONTROLS, *ATTENTION, QUANT, SCORE, "cmp_net", "tone_code", "n_duels", "n_decided",
                 "identified", RET, "delisted"]


def _f(x):
    return None if x is None or not np.isfinite(x) else float(x)


def test_universe(top: pd.DataFrame) -> pd.DataFrame:
    """Universe rows of the test weeks (Fridays from ``TEST_START``)."""
    return top[top["date"] >= TEST_START].reset_index(drop=True)


def attention_7d(items: pd.DataFrame, top: pd.DataFrame) -> pd.DataFrame:
    """(date, base, attn_7d): log(1 + distinct linked documents of the last seven days observable at the
    decision), counted over ``items`` (the rows of the present store and of the whole linked archive)."""
    rows = items[["doc_id", "base", "event_ts", "as_of_ts"]]
    return features.attention(rows, sorted(top["date"].unique()), top["base"].unique(), STORE_START)[["date", "base", "attn_7d"]]


def code_tone(lines: pd.DataFrame) -> pd.DataFrame:
    """(friday, base, tone_code): direction sign times materiality summed by code over the dossier lines."""
    value = lines["direction"].map(features.DIRECTION_SIGN).astype(float) * lines["materiality"].astype(float)
    return lines.assign(tone_code=value).groupby(["friday", "base"], as_index=False)["tone_code"].sum()


def net_wins(results: pd.DataFrame) -> pd.DataFrame:
    """(friday, base, cmp_net): wins minus losses over the comparisons of the asset."""
    rows = []
    for r in results.itertuples(index=False):
        won = None if r.winner in (None, "", NO_BASIS) or pd.isna(r.winner) else r.winner
        for base in (r.a, r.b):
            rows.append((r.friday, base, 0.0 if won is None else (1.0 if won == base else -1.0)))
    out = pd.DataFrame(rows, columns=["friday", "base", "value"])
    return out.groupby(["friday", "base"], as_index=False)["value"].mean().rename(columns={"value": "cmp_net"})


def assemble_panel(top: pd.DataFrame, attention: pd.DataFrame, dossiers: pd.DataFrame, lines: pd.DataFrame, scores: pd.DataFrame,
                   results: pd.DataFrame, quant: pd.DataFrame, fwd: pd.DataFrame, flags: pd.DataFrame | None) -> pd.DataFrame:
    """Test-universe rows joined one-to-one with the attention count, the dossier facts, the comparison score,
    the existing quant forecast, the forward return and the identification flag. An asset without a dossier has
    ``has_dossier`` 0, no lines and the neutral score 0."""
    panel = test_universe(top)[["date", "symbol", "base", *CONTROLS]].copy()
    if panel.duplicated(["date", "symbol"]).any() or panel.duplicated(["date", "base"]).any():
        raise ValueError("universe rows are not unique")
    panel = panel.merge(attention, on=["date", "base"], how="left", validate="1:1")
    if panel["attn_7d"].isna().any():
        raise ValueError("universe rows without an attention count")
    by_base = [dossiers[["friday", "base", "n_lines"]], scores[["friday", "base", SCORE, "n_duels", "n_decided"]],
               net_wins(results), code_tone(lines)]
    if flags is not None:
        by_base.append(flags[["friday", "base", "identified"]])
    for frame in by_base:
        frame = frame.rename(columns={"friday": "date"})
        if len(frame.merge(panel[["date", "base"]], on=["date", "base"], how="left", indicator=True).query("_merge != 'both'")):
            raise ValueError("dossier rows outside the test universe")
        panel = panel.merge(frame, on=["date", "base"], how="left", validate="1:1")
    if flags is None:
        panel["identified"] = None
    panel["has_dossier"] = panel["n_lines"].notna().astype(float)
    if (panel["has_dossier"].astype(bool) != panel[SCORE].notna()).any():
        raise ValueError("dossiers and comparison scores cover different assets")
    for col in ("n_lines", SCORE, "cmp_net", "tone_code", "n_duels", "n_decided"):
        panel[col] = panel[col].fillna(0.0).astype(float)
    q = quant[["date", "symbol", "pred_rank_pct"]].rename(columns={"pred_rank_pct": QUANT})
    panel = panel.merge(q, on=["date", "symbol"], how="left", validate="1:1")
    panel = panel.merge(fwd[["date", "symbol", RET, "delisted"]], on=["date", "symbol"], how="left", validate="1:1")
    panel[RET] = pd.to_numeric(panel[RET], errors="coerce")
    return panel.sort_values(["date", "symbol"]).reset_index(drop=True)[PANEL_COLUMNS]


# ---------------------------------------------------------------- statistics
def _residual(z: np.ndarray, v: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(z, v, rcond=None)
    return v - z @ beta


def residual_pairs(panel: pd.DataFrame, x_col: str = SCORE, controls=GATE_CONTROLS, ret_col: str = RET,
                   min_rows: int = MIN_WEEK_ROWS, min_dossiers: int = MIN_WEEK_DOSSIERS) -> pd.DataFrame:
    """Rows of the weeks that enter the statistic with the residual of the return rank (``ry``) and of the rank
    of ``x_col`` (``rx``) on an intercept and the ranks of ``controls``. Ranks are percentile ranks within the
    week over the complete rows; a missing control rank takes 0.5, a row without the quant forecast is left out.
    A week needs ``min_rows`` complete rows, ``min_dossiers`` of them with a dossier."""
    need = [x_col, ret_col] + ([QUANT] if QUANT in controls else [])
    parts = []
    for _, day in panel.groupby("date"):
        day = day.dropna(subset=need)
        if len(day) < min_rows or day["has_dossier"].sum() < min_dossiers:
            continue
        z = np.column_stack([np.ones(len(day))] + [day[c].astype(float).rank(pct=True).fillna(0.5).to_numpy() for c in controls])
        ry = _residual(z, day[ret_col].rank(pct=True).to_numpy())
        rx = _residual(z, day[x_col].rank(pct=True).to_numpy())
        parts.append(day.assign(ry=ry, rx=rx))
    return pd.concat(parts, ignore_index=True) if parts else panel.iloc[:0].assign(ry=[], rx=[])


def partial_series(panel: pd.DataFrame, x_col: str = SCORE, controls=GATE_CONTROLS, **kwargs) -> pd.Series:
    """Weekly coefficient of the rank of ``x_col`` in the OLS of the return rank on an intercept, that rank and
    the ranks of ``controls`` (computed from the two residuals, which gives the same number). A week in which
    the rank of ``x_col`` does not vary beyond the controls has no coefficient."""
    pairs = residual_pairs(panel, x_col, controls, **kwargs)
    out = {}
    for d, day in pairs.groupby("date"):
        ss = float(day["rx"] @ day["rx"])
        if ss > 1e-9:
            out[d] = float(day["rx"] @ day["ry"]) / ss
    return pd.Series(out, dtype=float).sort_index()


def summarize(series: pd.Series) -> dict:
    years = pd.DatetimeIndex(series.index).year if len(series) else np.array([], dtype=int)
    by_year = {str(y): {"weeks": int((years == y).sum()), "mean": _f(series[years == y].mean()) if (years == y).any() else None}
               for y in GATE_YEARS}
    return {"weeks": int(len(series)), "mean": _f(series.mean()) if len(series) else None,
            "nw_t": _f(newey_west_t(series)) if len(series) >= 3 else None,
            "share_positive": _f((series > 0).mean()) if len(series) else None, "by_year": by_year}


def gate_statistics(panel: pd.DataFrame) -> tuple[dict, pd.Series]:
    """The registered statistic and its weekly coefficients."""
    weekly = partial_series(panel)
    return summarize(weekly), weekly


def gates(stat: dict) -> dict:
    enough = stat["weeks"] >= MIN_GATE_WEEKS
    g1 = bool(enough and stat["nw_t"] is not None and stat["nw_t"] >= GATE_T and stat["mean"] > 0)
    g2 = bool(enough and all(v["mean"] is not None and v["mean"] > 0 for v in stat["by_year"].values()))
    return {"G1_coefficient_t": {"pass": g1, "threshold": GATE_T, "t": stat["nw_t"], "mean": stat["mean"], "weeks": stat["weeks"],
                                 "weeks_needed": MIN_GATE_WEEKS},
            "G2_both_years_positive": {"pass": g2, "by_year": stat["by_year"]}}


# ---------------------------------------------------------------- descriptive panels
def spread(panel: pd.DataFrame, col: str = SCORE) -> dict:
    """Mean simple return of the top third minus the bottom third of the dossier assets by ``col``, per week."""
    out = {}
    for d, day in panel[panel["has_dossier"] > 0].dropna(subset=[RET]).groupby("date"):
        if len(day) < SPREAD_MIN:
            continue
        day = day.sort_values([col, "symbol"])
        k = len(day) // 3
        out[d] = float(day[RET].iloc[-k:].mean() - day[RET].iloc[:k].mean())
    s = pd.Series(out, dtype=float).sort_index()
    return {"weeks": int(len(s)), "mean": _f(s.mean()) if len(s) else None, "nw_t": _f(newey_west_t(s)) if len(s) >= 3 else None,
            "share_positive": _f((s > 0).mean()) if len(s) else None}


def _corr(frame: pd.DataFrame) -> float:
    if len(frame) < 3 or frame["rx"].std() == 0 or frame["ry"].std() == 0:
        return float("nan")
    return float(np.corrcoef(frame["rx"], frame["ry"])[0, 1])


def identified_split(panel: pd.DataFrame, n_boot: int = BOOTSTRAP_DRAWS, seed: int = BOOTSTRAP_SEED) -> dict:
    """Pooled correlation of the two gate residuals among the dossier rows whose asset the comparison model
    named from the dossier and among those it did not, with a week bootstrap of the difference."""
    pairs = residual_pairs(panel)
    rows = pairs[(pairs["has_dossier"] > 0) & pairs["identified"].notna()]
    if rows.empty:
        return {"rows": 0}
    flag = rows["identified"].astype(bool)
    out = {"rows": int(len(rows)), "identified_rows": int(flag.sum()), "identified": _f(_corr(rows[flag])),
           "not_identified": _f(_corr(rows[~flag]))}
    weeks = {d: g for d, g in rows.groupby("date")}
    keys, rng, draws = list(weeks), np.random.default_rng(seed), []
    for _ in range(n_boot):
        sample = pd.concat([weeks[keys[i]] for i in rng.integers(0, len(keys), len(keys))], ignore_index=True)
        f = sample["identified"].astype(bool)
        draws.append(_corr(sample[f]) - _corr(sample[~f]))
    draws = np.array(draws, dtype=float)
    draws = draws[np.isfinite(draws)]
    if len(draws):
        out["difference"] = _f(out["identified"] - out["not_identified"]) if None not in (out["identified"], out["not_identified"]) else None
        out["difference_ci90"] = [_f(np.quantile(draws, 0.05)), _f(np.quantile(draws, 0.95))]
    return out


def coverage(panel: pd.DataFrame) -> dict:
    per_week = panel.groupby("date")["has_dossier"].sum()
    have = panel[panel["has_dossier"] > 0]
    return {"rows": int(len(panel)), "weeks": int(panel["date"].nunique()), "dossier_rows": int(len(have)),
            "dossier_share": _f(len(have) / len(panel)), "dossiers_per_week": {"min": _f(per_week.min()), "median": _f(per_week.median()),
                                                                                "max": _f(per_week.max())},
            "lines_per_dossier": _f(have["n_lines"].mean()), "decided_per_dossier": _f(have["n_decided"].mean()),
            "dossiers_without_decided_comparison": int((have["n_decided"] == 0).sum()),
            "rows_without_return": int(panel[RET].isna().sum()), "rows_without_quant": int(panel[QUANT].isna().sum())}


MOST_COVERED = ("BTC", "ETH")


def within_asset(panel: pd.DataFrame) -> pd.DataFrame:
    """Adds ``cmp_within``: the score less the asset's mean score over its dossier weeks (zero without a
    dossier). A coefficient that lives only between assets is a standing preference, not a weekly reading."""
    have = panel["has_dossier"] > 0
    mean = panel[have].groupby("base")[SCORE].mean()
    return panel.assign(cmp_within=np.where(have, panel[SCORE] - panel["base"].map(mean), 0.0))


DESCRIPTIVE = {
    "score_without_attention_controls": (SCORE, [QUANT, *CONTROLS]),
    "score_without_quant": (SCORE, [*CONTROLS, *ATTENTION]),
    "net_wins": ("cmp_net", GATE_CONTROLS),
    "code_tone": ("tone_code", GATE_CONTROLS),
    "score_beyond_code_tone": (SCORE, [*GATE_CONTROLS, "tone_code"]),
    "code_tone_beyond_score": ("tone_code", [*GATE_CONTROLS, SCORE]),
    "attention": ("attn_7d", [QUANT, *CONTROLS, "n_lines", "has_dossier", SCORE]),
    "quant": (QUANT, [*CONTROLS, *ATTENTION, SCORE]),
}


def evaluate(panel: pd.DataFrame, n_boot: int = BOOTSTRAP_DRAWS) -> tuple[dict, dict]:
    """(evaluation, errors). The gate statistic is computed unguarded; a failure in a descriptive panel is
    recorded and does not change the verdict."""
    stat, weekly = gate_statistics(panel)
    out = {"gate": {"statistic": stat, "controls": list(GATE_CONTROLS),
                    "weekly": {"dates": [str(pd.Timestamp(d).date()) for d in weekly.index], "coefficient": [float(v) for v in weekly]}},
           "gates": gates(stat), "descriptive": {}}
    errors = {}
    jobs = {name: (lambda c=col, k=ctrl: summarize(partial_series(panel, c, k))) for name, (col, ctrl) in DESCRIPTIVE.items()}
    jobs["score_outside_most_covered"] = lambda: summarize(partial_series(panel[~panel["base"].isin(MOST_COVERED)]))
    jobs["score_within_asset"] = lambda: summarize(partial_series(within_asset(panel), "cmp_within"))
    jobs["spread_score"] = lambda: spread(panel, SCORE)
    jobs["spread_code_tone"] = lambda: spread(panel, "tone_code")
    jobs["identified_split"] = lambda: identified_split(panel, n_boot)
    jobs["coverage"] = lambda: coverage(panel)
    for name, job in jobs.items():
        try:
            out["descriptive"][name] = job()
        except Exception as exc:                                    # noqa: BLE001
            errors[name] = f"{type(exc).__name__}: {exc}"
    return out, errors


def build_verdict(evaluation: dict, errors: dict, comparison: dict) -> dict:
    g = evaluation["gates"]
    passed = all(v["pass"] for v in g.values())
    return {"verdict": "PASS" if passed else "FAIL", "gates": g, "test_weeks": evaluation["gate"]["statistic"]["weeks"],
            "descriptive_errors": errors, "comparison": comparison,
            "note": ("A PASS licenses a single registered run on a sealed window and nothing else: the comparison model was "
                     "trained on text written after this window. A FAIL closes the family.")}


def finalize(top: pd.DataFrame, attention: pd.DataFrame, dossiers: pd.DataFrame, lines: pd.DataFrame, scores: pd.DataFrame,
             results: pd.DataFrame, quant: pd.DataFrame, fwd: pd.DataFrame, flags: pd.DataFrame | None, comparison: dict,
             n_boot: int = BOOTSTRAP_DRAWS) -> dict:
    """The registered outputs from the decision-time tables and the forward returns."""
    panel = assemble_panel(top, attention, dossiers, lines, scores, results, quant, fwd, flags)
    evaluation, errors = evaluate(panel, n_boot)
    rows = panel.drop(columns=[RET, "delisted"]).assign(date=panel["date"].dt.strftime("%Y-%m-%d"))
    rows = rows.astype(object).where(rows.notna(), None)
    return {"scores.json": {"columns": list(rows.columns), "rows": rows.to_numpy().tolist()},
            "evaluation.json": evaluation, "comparison.json": comparison,
            "verdict.json": build_verdict(evaluation, errors, comparison)}

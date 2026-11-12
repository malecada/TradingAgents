"""Evaluation tail of the reader configuration (Charter 2): panel, fitted forecasts, gates, books.

No model call and no cache. The reader records are an input and everything here is arithmetic on registered
inputs. ``finalize`` joins the universe rows with the text features, the forward returns, the existing quant
forecast and the identification flags, fits the forecasters, applies the two registered gates by code and
returns the output files in JSON-safe form. Every statistic outside the two gates is descriptive and guarded:
an error there is recorded in the verdict and cannot void it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.agents_v2.charter1b import (BOOTSTRAP_DRAWS, BOOTSTRAP_SEED, PLACEBO_DRAWS, _errors, _finite, _guard,
                                               _utc, json_safe)
from tradingagents.agents_v2.evaluate import CONTROLS, newey_west_t, residualize, subset_gaps, weekly_ic
from tradingagents.agents_v2.graph import rule_weights
from tradingagents.agents_v2.portfolio_eval import COST_PER_SIDE, book_components, summarize_book
from tradingagents.dossier.universe import weekly_top
from tradingagents.reader import consensus, features, model
from tradingagents.reader.reading import flag_items, reading_sets, work_list

# registered thresholds (Charter 2 §5)
GATE_TEXT_T = 2.0           # Newey-West t of the mean weekly s_text coefficient next to the quant forecast, >=
GATE_YEARS = (2023, 2024)   # calendar years (of the Friday) in which the mean weekly coefficient must be positive

PANEL_START, PANEL_END = "2022-01-07", "2024-12-27"
STORE_START = pd.Timestamp("2022-01-01", tz="UTC")
UNIVERSE_N = 50
MIN_WEEK_ROWS = 15          # rows a week needs in the encompassing regression (as in evaluate.encompassing)
DEFAULT_VOL = 0.8

TEXT = list(features.TEXT_FEATURES)
QUANT = list(model.QUANT_FEATURES)
FULL = QUANT + TEXT
GATE_SCORE = "s_text"
RIDGE_SCORES = {"s_text": TEXT, "s_full": FULL, "s_quant": QUANT, "s_block_a": list(features.BLOCK_A),
                "s_block_b": list(features.BLOCK_B), "s_text_class": [*features.BLOCK_A, *features.BLOCK_B_CLASS]}
GBM_SCORES = {"g_text": TEXT, "g_full": FULL, "g_quant": QUANT}
CROSS_FIT_SCORES = {"cf_text": TEXT, "cf_full": FULL, "cf_quant": QUANT}
SCORES = [*RIDGE_SCORES, *GBM_SCORES, *CROSS_FIT_SCORES]
PAIRED = [("s_full", "s_quant"), ("g_full", "g_quant"), ("cf_full", "cf_quant"), ("s_full", "p_quant"), ("g_full", "s_full")]
ENCOMPASSING = [("s_full", "p_quant"), ("s_block_a", "p_quant"), ("s_block_b", "p_quant"), ("s_text_class", "p_quant"),
                ("g_text", "p_quant"), ("g_full", "p_quant"), ("cf_text", "p_quant"), ("s_text", "s_quant"), ("g_text", "g_quant")]
BOOK_SCORES = ("s_full", "s_quant", "p_quant", "g_full", "s_text")
TEXT_COLUMNS = [*TEXT, *[c for c in features.BLOCK_B_CLASS if c not in TEXT], *features.COUNTS]
PANEL_COLUMNS = ["date", "symbol", "base", *dict.fromkeys([*QUANT, *CONTROLS]), *TEXT_COLUMNS, "fwd_ret", "delisted", "p_quant",
                 "identified"]
OUTPUT_COLUMNS = ["date", "symbol", "base", *CONTROLS, *TEXT_COLUMNS, "fwd_ret", "delisted", "p_quant", "identified", *SCORES]


# ---------------------------------------------------------------- universe and reading
def universe(cards: pd.DataFrame) -> pd.DataFrame:
    """Card rows of the weekly top-``UNIVERSE_N`` over the panel window."""
    cards = cards.assign(date=pd.to_datetime(cards["date"], utc=True))
    return weekly_top(cards, UNIVERSE_N, PANEL_START, PANEL_END)


def reading(items: pd.DataFrame, docs: pd.DataFrame, top: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(reading sets of every universe week, work list of (doc_id, base) that yield a record)."""
    sets = reading_sets(flag_items(items, docs), top)
    return sets, work_list(sets)


def text_features(items: pd.DataFrame, sets: pd.DataFrame, records: pd.DataFrame, top: pd.DataFrame) -> pd.DataFrame:
    """Asset-week text features of the universe from the record table. The records must cover the work list
    exactly: one row per (doc_id, base), none missing and none beyond it."""
    work = work_list(sets)
    have = records[["doc_id", "base"]]
    if have.duplicated().any():
        raise ValueError("record table: duplicate (doc_id, base)")
    if set(map(tuple, have.to_numpy())) != set(map(tuple, work[["doc_id", "base"]].to_numpy())):
        raise ValueError("record table and work list differ")
    return features.asset_week_features(items, sets, records, top, STORE_START)


# ---------------------------------------------------------------- panel
def _keyed(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = frame[["date", "symbol", *cols]].copy()
    out["date"] = _utc(out["date"].to_numpy()).to_numpy()
    return out


def assemble_panel(top: pd.DataFrame, feats: pd.DataFrame, fwd: pd.DataFrame, quant: pd.DataFrame,
                   flags: pd.DataFrame | None) -> pd.DataFrame:
    """Universe rows joined with the text features, the forward returns, the existing quant forecast and the
    identification flags. Every join is one-to-one on (date, symbol); every universe row needs its text row."""
    key = ["date", "symbol"]
    panel = _keyed(top, ["base", *dict.fromkeys([*QUANT, *CONTROLS])])
    if panel.duplicated(key).any():
        raise ValueError("universe rows are not unique on (date, symbol)")
    panel = panel.merge(_keyed(feats, TEXT_COLUMNS), on=key, how="left", validate="1:1", indicator=True)
    if (panel.pop("_merge") != "both").any():
        raise ValueError("universe rows without text features")
    filled = [c for c in TEXT_COLUMNS if c != "attn_abn"]            # attn_abn alone may be missing (short own history)
    if panel[filled].isna().any().any():
        raise ValueError("text features with missing values")
    panel = panel.merge(_keyed(fwd, ["fwd_ret", "delisted"]), on=key, how="left", validate="1:1")
    panel["fwd_ret"] = pd.to_numeric(panel["fwd_ret"], errors="coerce")
    panel = panel.merge(_keyed(quant, ["pred_rank_pct"]).rename(columns={"pred_rank_pct": "p_quant"}),
                        on=key, how="left", validate="1:1")
    if flags is not None:
        fl = flags.assign(date=_utc(flags["friday"].to_numpy()).to_numpy())[["date", "symbol", "identified"]]
        panel = panel.merge(fl, on=key, how="left", validate="1:1")
    else:
        panel["identified"] = None
    return panel.sort_values(key).reset_index(drop=True)[PANEL_COLUMNS]


# ---------------------------------------------------------------- fitted scores
def fit_scores(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict, dict]:
    """(panel with one column per fitted score, fit information per walk-forward score, errors). The gate score
    is fitted unguarded; a failure of any other fit leaves its column missing and is recorded."""
    out, paths, errors = panel.copy(), {}, {}
    out[GATE_SCORE], paths[GATE_SCORE] = model.walk_forward(panel, RIDGE_SCORES[GATE_SCORE])
    jobs = [(n, lambda c=c: model.walk_forward(panel, c)) for n, c in RIDGE_SCORES.items() if n != GATE_SCORE]
    jobs += [(n, lambda c=c: model.walk_forward(panel, c, fit=model.fit_gbm)) for n, c in GBM_SCORES.items()]
    jobs += [(n, lambda c=c: (model.cross_fit(panel, c), None)) for n, c in CROSS_FIT_SCORES.items()]
    for name, job in jobs:
        try:
            out[name], info = job()
            if info is not None:
                paths[name] = info
        except Exception as exc:                                    # noqa: BLE001
            out[name], errors[name] = np.nan, {"error": f"{type(exc).__name__}: {exc}"}
    return out, paths, errors


# ---------------------------------------------------------------- statistics
def encompassing_series(panel: pd.DataFrame, prob_col: str, quant_col: str = "p_quant",
                        ret_col: str = "fwd_ret") -> tuple[dict, pd.DataFrame]:
    """The encompassing regression of Charter 1b (``evaluate.encompassing``) with its weekly coefficients:
    per week an OLS of the residualised return rank on the residualised ranks of ``quant_col`` and ``prob_col``.
    Returns (summary with the keys of ``evaluate.encompassing``, weekly frame beta_quant / beta_llm)."""
    rows = []
    for d, day in panel.groupby("date"):
        day = day.dropna(subset=[prob_col, quant_col, ret_col])
        if len(day) < MIN_WEEK_ROWS:
            continue
        rr = residualize(day, ret_col).to_numpy()
        rq = residualize(day, quant_col).to_numpy()
        rp = residualize(day, prob_col).to_numpy()
        beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(day)), rq, rp]), rr, rcond=None)
        rows.append((d, beta[1], beta[2]))
    weekly = pd.DataFrame(rows, columns=["date", "beta_quant", "beta_llm"]).set_index("date").sort_index()
    if len(weekly) < 3:
        return {"weeks": int(len(weekly)), "beta_quant": None, "t_quant": None, "beta_llm": None, "t_llm": None}, weekly
    return {"weeks": int(len(weekly)), "beta_quant": float(weekly["beta_quant"].mean()), "t_quant": newey_west_t(weekly["beta_quant"]),
            "beta_llm": float(weekly["beta_llm"].mean()), "t_llm": newey_west_t(weekly["beta_llm"])}, weekly


def _years(index) -> np.ndarray:
    return np.asarray(pd.DatetimeIndex(index).year) if len(index) else np.array([], dtype=int)


def gate_statistics(test: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """The two registered statistics on the test weeks and the weekly coefficients they are built from."""
    summary, weekly = encompassing_series(test, GATE_SCORE, "p_quant")
    years = _years(weekly.index)
    by_year = {}
    for y in GATE_YEARS:
        vals = weekly["beta_llm"].to_numpy()[years == y]
        by_year[str(y)] = {"weeks": int(len(vals)), "mean": float(vals.mean()) if len(vals) else None}
    return {"encompassing_text_vs_quant": summary, "text_coefficient_by_year": by_year}, weekly


def ic_summary(panel: pd.DataFrame, col: str) -> dict:
    ic = weekly_ic(panel, col).dropna()
    if not len(ic):
        return {"weeks": 0, "mean": None, "nw_t": None, "hit_rate": None, "by_year": {}}
    by_year = {str(int(y)): float(v.mean()) for y, v in ic.groupby(_years(ic.index))}
    return {"weeks": int(len(ic)), "mean": float(ic.mean()), "nw_t": newey_west_t(ic), "hit_rate": float((ic > 0).mean()),
            "by_year": by_year}


def paired_ic(panel: pd.DataFrame, a: str, b: str) -> dict:
    """Weekly IC of ``a`` minus weekly IC of ``b`` on the weeks where both exist."""
    diff = (weekly_ic(panel, a) - weekly_ic(panel, b)).dropna()
    if not len(diff):
        return {"weeks": 0, "mean": None, "nw_t": None, "share_positive": None}
    return {"weeks": int(len(diff)), "mean": float(diff.mean()), "nw_t": newey_west_t(diff), "share_positive": float((diff > 0).mean())}


def coefficient_summary(paths: dict) -> dict:
    """Ridge coefficients per test week: the whole path of the gate score, mean / sd / share positive for every
    ridge score; mean gain share per feature for the boosted trees."""
    out = {}
    for name, frame in paths.items():
        if name in GBM_SCORES:
            share = frame.div(frame.sum(axis=1).replace(0.0, np.nan), axis=0)
            out[name] = {"weeks": int(len(frame)), "mean_gain_share": {c: float(share[c].mean()) for c in frame.columns}}
        else:
            out[name] = {"weeks": int(len(frame)),
                         "features": {c: {"mean": float(frame[c].mean()), "sd": float(frame[c].std()),
                                          "share_positive": float((frame[c] > 0).mean())} for c in frame.columns}}
    gate = paths[GATE_SCORE]
    out["path_" + GATE_SCORE] = {"dates": list(gate.index), **{c: gate[c].to_numpy() for c in gate.columns}}
    return out


def feature_coverage(panel: pd.DataFrame) -> dict:
    per_week = panel.groupby("date")
    out = {"rows": int(len(panel)), "weeks": int(panel["date"].nunique()), "features": {}}
    for c in TEXT_COLUMNS:
        out["features"][c] = {"missing": float(panel[c].isna().mean()), "nonzero": float((panel[c].fillna(0.0) != 0).mean()),
                              "mean_assets_nonzero_per_week": float(per_week[c].apply(lambda s: (s.fillna(0.0) != 0).sum()).mean()),
                              "mean": float(panel[c].mean()), "sd": float(panel[c].std())}
    return out


def identified_subsets(test: pd.DataFrame, n_boot: int) -> dict:
    """The identified-subset estimator of Charter 1b on the within-week ranks of the text score and of the full
    score, against the existing quant forecast (difference in differences of the text score)."""
    ranked = test.copy()
    for src, dst in (("s_text", "r_text"), ("s_full", "r_full")):
        grp = ranked.groupby("date")[src]
        ranked[dst] = (grp.rank() - 0.5) / grp.transform("count")
    flagged = ranked["identified"].notna()
    return {"flagged_rows": int(flagged.sum()), "identified_rows": int((ranked.loc[flagged, "identified"] == True).sum()),  # noqa: E712
            "estimate": subset_gaps(ranked, cols=("r_text", "r_full", "p_quant"), contrast=("r_text", "p_quant"),
                                    n_boot=n_boot, seed=BOOTSTRAP_SEED)}


def evaluate_forecasts(panel: pd.DataFrame, paths: dict, fit_errors: dict, n_boot: int = BOOTSTRAP_DRAWS) -> dict:
    """evaluation.json: the gate statistics on the test weeks and the descriptive panels of Charter 2 §5."""
    test = panel[panel[GATE_SCORE].notna()]
    gates, weekly = gate_statistics(test)
    days = sorted(test["date"].unique())
    walk = [*RIDGE_SCORES, *GBM_SCORES, "p_quant"]
    return {"gates": gates,
            "gate_weekly_coefficients": [{"date": d, **row} for d, row in weekly.to_dict("index").items()],
            "weeks": {"panel": int(panel["date"].nunique()), "test": len(days), "first_test": days[0] if days else None,
                      "last_test": days[-1] if days else None},
            "fit_errors": fit_errors,
            "ic_test_weeks": {c: _guard(ic_summary, test, c) for c in walk},
            "ic_cross_fit_all_weeks": {c: _guard(ic_summary, panel, c) for c in [*CROSS_FIT_SCORES, "p_quant"]},
            "paired_ic": {f"{a}_minus_{b}": _guard(paired_ic, panel if a.startswith("cf_") else test, a, b) for a, b in PAIRED},
            "encompassing": {f"{a}_vs_{b}": _guard(lambda a=a, b=b: encompassing_series(panel if a.startswith("cf_") else test, a, b)[0])
                             for a, b in ENCOMPASSING},
            "coefficients": _guard(coefficient_summary, paths),
            "feature_coverage": {"all_weeks": _guard(feature_coverage, panel), "test_weeks": _guard(feature_coverage, test)},
            "identified_subsets": _guard(identified_subsets, test, n_boot),
            "panel": {"rows": int(len(panel)), "test_rows": int(len(test)), "missing_fwd_ret": int(panel["fwd_ret"].isna().sum()),
                      "missing_fwd_ret_test": int(test["fwd_ret"].isna().sum()),
                      "missing_p_quant_test": int(test["p_quant"].isna().sum()),
                      "delisted_rows": int(panel["delisted"].fillna(False).astype(bool).sum())}}


# ---------------------------------------------------------------- books
def book_weights(test: pd.DataFrame, col: str) -> dict:
    """friday -> {symbol: weight}: the rule book of Charter 1b on the within-week ranks of one score."""
    out = {}
    for d, day in test.dropna(subset=[col]).groupby("date"):
        p = (day[col].rank() - 0.5) / len(day)
        vol = day["vol_ewma20"].where(day["vol_ewma20"] > 0)
        fallback = float(vol.median()) if vol.notna().any() else DEFAULT_VOL
        out[pd.Timestamp(d)] = rule_weights([{"symbol": s, "p_outperform_7d": float(pi), "vol_ann": float(v) if pd.notna(v) else fallback,
                                              "abstain": False} for s, pi, v in zip(day["symbol"], p, vol)])
    return out


def evaluate_books(test: pd.DataFrame, fwd: pd.DataFrame, funding: pd.DataFrame, n_placebo: int = PLACEBO_DRAWS) -> tuple[dict, dict]:
    """portfolio.json (summary per book, funded, all descriptive) and books.json (weekly decomposition, weights)."""
    def _one(col: str) -> tuple[dict, dict]:
        w = book_weights(test, col)
        comp = book_components(w, fwd, funding=funding)
        return (summarize_book(w, fwd, funding=funding, n_placebo=n_placebo),
                {"weekly": [{"date": d, **row} for d, row in comp.to_dict("index").items()], "weights": {d: w[d] for d in sorted(w)}})

    portfolio, detail = {}, {}
    for col in BOOK_SCORES:
        res = _guard(_one, col)
        portfolio[col], detail[col] = res if isinstance(res, tuple) else (res, res)
    have = set(zip(_utc(funding["date"].to_numpy()), funding["symbol"])) if len(funding) else set()
    keys = list(zip(test["date"], test["symbol"]))
    portfolio["funding_coverage"] = float(sum(k in have for k in keys) / len(keys)) if keys else None
    portfolio["cost_per_side"] = COST_PER_SIDE
    return portfolio, detail


# ---------------------------------------------------------------- verdict
def build_verdict(evaluation: dict, portfolio: dict, detail: dict, reader: dict) -> dict:
    """The registered gates applied by code. A statistic that cannot be computed fails its gate."""
    g = evaluation["gates"]
    enc, years = g["encompassing_text_vs_quant"], g["text_coefficient_by_year"]
    t, beta = enc["t_llm"], enc["beta_llm"]
    means = {str(y): years.get(str(y), {}).get("mean") for y in GATE_YEARS}
    gates = {
        "text_encompassing": {"value": {"nw_t": t, "mean_coefficient": beta, "weeks": enc["weeks"]},
                              "rule": f"Newey-West t >= {GATE_TEXT_T} and mean coefficient > 0",
                              "pass": bool(_finite(t) and _finite(beta) and t >= GATE_TEXT_T and beta > 0)},
        "text_coefficient_sign_by_year": {"value": means, "weeks": {y: years.get(y, {}).get("weeks") for y in means},
                                          "rule": "mean weekly coefficient > 0 in " + " and in ".join(means),
                                          "pass": bool(all(_finite(v) and v > 0 for v in means.values()))},
    }
    failed = [k for k, v in gates.items() if not v["pass"]]
    errors = (_errors({k: v for k, v in evaluation.items() if k != "gates"}, "evaluation") + _errors(portfolio, "portfolio")
              + _errors(detail, "books") + _errors(reader, "reader"))
    return {"charter": "llm-v2 Charter 2 (reader configuration)", "test_weeks": evaluation["weeks"]["test"], "gates": gates,
            "failed_gates": failed, "descriptive_errors": errors, "verdict": "FAIL" if failed else "PASS"}


def finalize(top: pd.DataFrame, feats: pd.DataFrame, records: pd.DataFrame, fwd: pd.DataFrame, funding: pd.DataFrame,
             quant: pd.DataFrame, flags: pd.DataFrame | None, extraction: dict | None = None,
             n_placebo: int = PLACEBO_DRAWS, n_boot: int = BOOTSTRAP_DRAWS) -> dict:
    """Everything after the feature build: panel, fitted scores, gates, descriptive panels, books and the verdict,
    already in JSON-safe form (file name -> object)."""
    panel = assemble_panel(top, feats, fwd, quant, flags)
    panel, paths, fit_errors = fit_scores(panel)
    evaluation = evaluate_forecasts(panel, paths, fit_errors, n_boot=n_boot)
    portfolio, detail = evaluate_books(panel[panel[GATE_SCORE].notna()], fwd, funding, n_placebo=n_placebo)
    reader = {"quality": _guard(lambda: consensus.quality(consensus.record_rows(records))), "extraction": extraction}
    verdict = build_verdict(evaluation, portfolio, detail, reader)
    shown = panel[OUTPUT_COLUMNS]
    rows = shown.astype(object).where(shown.notna(), None).to_numpy().tolist()          # one list per row, column order below
    return {"forecasts.json": json_safe({"columns": OUTPUT_COLUMNS, "rows": rows}), "evaluation.json": json_safe(evaluation),
            "portfolio.json": json_safe(portfolio), "books.json": json_safe(detail), "reader.json": json_safe(reader),
            "verdict.json": json_safe(verdict)}

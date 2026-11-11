"""Charter 1b: replacement registration of the Charter 1 dev run after its evaluation tail was found defective
(system review 2026-11-11). The agents, prompts, dossiers and the three registered gate families are unchanged.
This module holds what the replacement adds:

* a cache-only loader for the weeks completed by the first attempt (no call, no retry; the stored book must
  equal the book recomputed from the cached forecasts);
* panel construction with the provider and text-availability columns used by the declared sensitivities;
* the corrected evaluation tail (identified-subset estimator, funded Sharpe, aligned funding window, book
  decomposition) and a verdict object written by code;
* ``json_safe``, so a non-finite statistic can no longer abort the publication of the outputs.
"""
from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from tradingagents.agents_v2.evaluate import (CONTROLS, encompassing, evaluate_panel, newey_west_t, recalibrated_brier,
                                               subperiod_sign_gate, subset_gaps, weekly_ic)
from tradingagents.agents_v2.graph import rule_weights
from tradingagents.agents_v2.portfolio_eval import COST_PER_SIDE, book_components, summarize_book

# registered thresholds (Charter 1 §5, unchanged)
GATE_IC_T = 2.0             # Newey-West t of the weekly residual rank IC of p_hybrid, >=
GATE_BRIER_SKILL = 0.0      # Brier skill of p_hybrid after walk-forward recalibration, >
GATE_ENCOMPASSING_T = 2.0   # Newey-West t of the mean p_judge coefficient in the encompassing regression, >=
GATE_NET_SHARPE = 0.8       # rule-twin book, net of taker costs and realized funding, >=
GATE_PLACEBO_P = 0.05       # both placebo families, <=
GATE_SUBPERIOD_YEARS = 2    # years whose mean IC must share a sign (of the years present)

MAX_FAILED_NEW_WEEK = 5     # a newly run week with more failed assets is excluded and ends the run
PLACEBO_DRAWS = 500
BOOTSTRAP_DRAWS = 2000
BOOTSTRAP_SEED = 20261111
BOOK_KEYS = {"rule_twin": "rule_weights", "rule_twin_llm_only": "rule_weights_llm_only",
             "rule_twin_judge_nd": "rule_weights_judge_nd", "rule_twin_confidence": "rule_weights_confidence"}
PRIMARY_PROVIDER = "Baidu"


class CacheError(RuntimeError):
    """A frozen week does not match the registered cache."""


# ---------------------------------------------------------------- serialization
def json_safe(value):
    """Plain JSON types only: string keys, numpy scalars unwrapped, timestamps as ISO strings and every
    non-finite float as null (the run helper encodes with allow_nan=False)."""
    if value is None or value is pd.NaT or value is pd.NA:
        return None
    if isinstance(value, dict):
        return {(k if isinstance(k, str) else str(json_safe(k))): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return [json_safe(v) for v in value.tolist()]
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, str):
        return value
    raise TypeError(f"not JSON-serializable: {type(value).__name__}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------- registered inputs
def load_dossiers(root: Path, manifest: dict) -> dict[str, dict]:
    """week -> symbol -> dossier, every file verified against the registered manifest."""
    by_day: dict[str, dict] = {}
    for path, digest in manifest["files"].items():
        p = Path(root) / path
        if sha256_file(p) != digest:
            raise CacheError(f"dossier changed since freeze: {path}")
        by_day.setdefault(p.parent.name, {})[p.stem] = json.loads(p.read_text())
    return by_day


def verify_store(root: Path, digest: dict[str, str], label: str) -> Path:
    """Every file of a parquet store must match its registered digest and the store must hold no other parquet
    file. Returns the store directory."""
    parents = {str(Path(path).parent) for path in digest}
    if len(parents) != 1:
        raise CacheError(f"{label}: digest spans {len(parents)} directories")
    directory = Path(root) / parents.pop()
    present = {p.name for p in directory.glob("*.parquet")}
    if present != {Path(path).name for path in digest}:
        raise CacheError(f"{label}: store holds files that differ from the registered set")
    for path, expected in digest.items():
        if sha256_file(Path(root) / path) != expected:
            raise CacheError(f"{label}: changed since freeze: {path}")
    return directory


def verify_cache(runs_dir: Path, cache: dict, by_day: dict[str, dict], config: str) -> set[str]:
    """The call cache must be exactly the registered one: frozen weeks are the newest contiguous block of the
    manifested weeks, every frozen and every other pinned file matches its digest, and no manifested week holds
    an unpinned cached file. Returns the frozen weeks."""
    if cache["config_sha"] != config:
        raise CacheError("cache manifest belongs to another agent config")
    frozen = sorted(cache["complete_weeks"], reverse=True)
    if frozen != sorted(by_day, reverse=True)[:len(frozen)]:
        raise CacheError("frozen weeks are not the newest contiguous block of the manifested weeks")
    registered = {**cache["files"], **cache["pinned_other"]}
    for rel, digest in registered.items():
        path = Path(runs_dir) / rel
        if not path.exists() or sha256_file(path) != digest:
            raise CacheError(f"cached file differs from the registered cache: {rel}")
    for day in by_day:
        day_dir = Path(runs_dir) / day
        if day_dir.is_dir():
            for f in day_dir.glob("*.json"):
                if f"{day}/{f.name}" not in registered:
                    raise CacheError(f"unregistered cached file: {day}/{f.name}")
    return set(frozen)


# ---------------------------------------------------------------- frozen weeks
def week_books(results: dict[str, dict], dossiers: dict[str, dict]) -> dict[str, dict]:
    """The four deterministic books of one week from per-asset results, as built by runner.run_week."""
    vols = [dossiers[s]["numeric"].get("vol_ewma20_ann_pct") for s in dossiers]
    vols = [v for v in vols if v]
    median_vol = (sorted(vols)[len(vols) // 2] if vols else 80.0) / 100.0
    candidates = [{"symbol": s, "p_outperform_7d": r["p_outperform"], "confidence": r["confidence"], "abstain": r["abstain"],
                   "vol_ann": (dossiers[s]["numeric"].get("vol_ewma20_ann_pct") or median_vol * 100) / 100.0}
                  for s, r in results.items() if not r.get("failed")]
    return {"rule_weights": rule_weights(candidates),
            "rule_weights_confidence": rule_weights(candidates, use_confidence=True),
            "rule_weights_judge_nd": rule_weights([{**c, "p_outperform_7d": results[c["symbol"]]["p_judge_nd"]} for c in candidates]),
            "rule_weights_llm_only": rule_weights([{**c, "p_outperform_7d": results[c["symbol"]]["p_judge"]} for c in candidates])}


def load_cached_week(day: str, dossiers: dict[str, dict], runs_dir: Path, config: str, tolerance: float = 1e-9) -> dict:
    """Read one completed week from the per-asset cache without any call. Every universe member must have a file
    carrying the registered agent config and the dossier hash; an asset recorded as failed stays failed and a
    failed debate keeps its no-debate forecast. The stored book must equal the book recomputed from the cached
    forecasts. Returns the structure of runner.run_week."""
    day_dir = Path(runs_dir) / day
    results: dict[str, dict] = {}
    for sym, d in dossiers.items():
        path = day_dir / f"{sym}.json"
        if not path.exists():
            raise CacheError(f"{day} {sym}: no cached result")
        r = json.loads(path.read_text())
        if r.get("config_sha") != config or r.get("dossier_sha") != d["sha256"]:
            raise CacheError(f"{day} {sym}: cached result belongs to another config or dossier")
        if not r.get("failed") and "nd" not in r.get("stages", {}):
            raise CacheError(f"{day} {sym}: cached result is incomplete")
        results[sym] = r
    stored = json.loads((day_dir / "_portfolio.json").read_text())
    if stored.get("config_sha") != config:
        raise CacheError(f"{day}: stored book belongs to another config")
    books = week_books(results, dossiers)
    for name, book in books.items():
        if set(book) != set(stored[name]) or any(abs(book[s] - stored[name][s]) > tolerance for s in book):
            raise CacheError(f"{day}: stored book {name} differs from the book recomputed from cached forecasts")
    return {"results": results, "portfolio": {"config_sha": config, **books, "weights": books["rule_weights"]}}


# ---------------------------------------------------------------- panel
def _mean_rate(cites: dict, key: str):
    vals = [v[key] for v in cites.values() if v.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


def asset_rows(day: str, results: dict[str, dict], dossiers: dict[str, dict]) -> list[dict]:
    """One panel row per universe member of the week (columns of the first attempt plus debate_failed, n_items,
    n_calls and the share of calls served by the primary provider)."""
    rows = []
    for s, r in results.items():
        cites = {}
        for stage in ("nd", "debate"):
            for role, rep in (r.get("stages", {}).get(stage, {}).get("citations") or {}).items():
                cites[role] = rep
        providers = [m.get("provider") for m in r.get("meta", [])]
        rows.append({"date": day, "symbol": s, "p_outperform": r.get("p_outperform"), "p_judge": r.get("p_judge"),
                     "p_hybrid": r.get("p_hybrid"), "p_judge_nd": r.get("p_judge_nd"), "p_hybrid_nd": r.get("p_hybrid_nd"),
                     "p_judge_debate": r.get("p_judge_debate"), "p_analyst_mean": r.get("p_analyst_mean"),
                     "weight_on_quant": r.get("weight_on_quant"), "quant_rank_pct": r.get("quant_rank_pct"),
                     "confidence": r.get("confidence"), "abstain": bool(r.get("abstain")),
                     "debated": bool(r.get("debated", False)), "debate_selected": bool(r.get("debate_selected", False)),
                     "failed": bool(r.get("failed")), "debate_failed": bool(r.get("debate_failed")),
                     "cite_exist_mean": _mean_rate(cites, "cite_exist_rate"),
                     "number_grounded_mean": _mean_rate(cites, "number_grounded_rate"),
                     "n_items": len(dossiers[s].get("items") or []), "n_calls": len(providers),
                     "primary_provider_share": (sum(p == PRIMARY_PROVIDER for p in providers) / len(providers)) if providers else None})
    return rows


def _utc(values) -> pd.Series:
    return pd.to_datetime(pd.Series(values), utc=True).dt.as_unit("ns")


def assemble_panel(rows: list[dict], fwd: pd.DataFrame, cards: pd.DataFrame, quant: pd.DataFrame,
                   flags: pd.DataFrame | None) -> pd.DataFrame:
    """Forecast rows joined with forward returns, the control columns, the quant twin and the identification
    flags. Every join is many-to-one on (date, symbol)."""
    panel = pd.DataFrame(rows)
    panel["date"] = _utc(panel["date"]).to_numpy()
    for col in ("p_outperform", "p_judge", "p_hybrid", "p_judge_nd", "p_hybrid_nd", "p_judge_debate", "p_analyst_mean",
                "weight_on_quant", "quant_rank_pct", "confidence", "cite_exist_mean", "number_grounded_mean",
                "primary_provider_share"):
        panel[col] = pd.to_numeric(panel[col], errors="coerce")

    def _keyed(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        out = frame[["date", "symbol", *cols]].copy()
        out["date"] = _utc(out["date"].to_numpy()).to_numpy()
        return out

    panel = panel.merge(_keyed(fwd, ["fwd_ret", "delisted"]), on=["date", "symbol"], how="left", validate="m:1")
    panel["fwd_ret"] = pd.to_numeric(panel["fwd_ret"], errors="coerce")
    panel = panel.merge(_keyed(cards, [*CONTROLS, "size_rank"]), on=["date", "symbol"], how="left", validate="m:1")
    panel = panel.merge(_keyed(quant, ["pred_rank_pct"]).rename(columns={"pred_rank_pct": "p_quant"}),
                        on=["date", "symbol"], how="left", validate="m:1")
    if flags is not None:
        fl = flags.assign(date=_utc(flags["friday"].to_numpy()).to_numpy())[["date", "symbol", "identified"]]
        panel = panel.merge(fl, on=["date", "symbol"], how="left", validate="m:1")
    else:
        panel["identified"] = None
    return panel.reset_index(drop=True)


# ---------------------------------------------------------------- evaluation tail
def gate_statistics(panel: pd.DataFrame) -> dict:
    """The four registered forecast-gate statistics on one panel."""
    ic = weekly_ic(panel, "p_hybrid")
    return {"hybrid_ic": {"weeks": int(len(ic)), "mean": float(ic.mean()) if len(ic) else None, "nw_t": newey_west_t(ic),
                          "hit_rate": float((ic > 0).mean()) if len(ic) else None},
            "hybrid_brier_recalibrated": recalibrated_brier(panel, "p_hybrid"),
            "encompassing_llm_vs_quant": encompassing(panel, "p_judge", "p_quant"),
            "subperiods": subperiod_sign_gate(ic, GATE_SUBPERIOD_YEARS)}


def _debate_contrast(panel: pd.DataFrame) -> dict:
    """Paired within-asset-week debate effect on the judge probability (descriptive)."""
    paired = panel.dropna(subset=["p_judge_debate", "p_judge_nd"])
    if len(paired) < 30:
        return {}
    scored = paired.dropna(subset=["fwd_ret"])

    def _wk_ic(col):
        return pd.Series({d: g[col].rank(pct=True).corr(g["fwd_ret"].rank(pct=True), method="spearman")
                          for d, g in scored.groupby("date") if len(g) >= 8}, dtype=float)

    diff = (_wk_ic("p_judge_debate") - _wk_ic("p_judge_nd")).dropna()
    return {"n_pairs": int(len(paired)), "weeks": int(len(diff)), "delta_ic_mean": float(diff.mean()) if len(diff) else None,
            "delta_ic_nw_t": newey_west_t(diff) if len(diff) >= 3 else None,
            "mean_abs_shift": float((paired["p_judge_debate"] - paired["p_judge_nd"]).abs().mean()),
            "sd_debate": float(paired["p_judge_debate"].std()), "sd_nd": float(paired["p_judge_nd"].std())}


def _mean(series: pd.Series):
    return float(series.mean()) if series.notna().any() else None


def _guard(fn, *args, **kwargs):
    """Descriptive statistics must not be able to void the registered gates: an exception is recorded in place
    of the value (and listed in the verdict) instead of aborting the run."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:                                    # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def _errors(value, path: str = "") -> list[str]:
    if isinstance(value, dict):
        if isinstance(value.get("error"), str):
            return [path]
        return [e for k, v in value.items() for e in _errors(v, f"{path}/{k}" if path else str(k))]
    return []


def evaluate_forecasts(panel: pd.DataFrame, weeks: dict, n_boot: int = BOOTSTRAP_DRAWS) -> dict:
    """evaluation.json: gate statistics, the descriptive panels of the first attempt, the declared sensitivities
    and the identified-subset estimator."""
    ok = panel[~panel["failed"]]
    same = bool(np.allclose(ok["p_outperform"].to_numpy(dtype=float), ok["p_hybrid"].to_numpy(dtype=float), equal_nan=True)) if len(ok) else True
    flagged = panel["identified"].notna()
    text_only = panel.assign(identified=panel["identified"].where(panel["n_items"] >= 1))
    all_primary = panel[panel["primary_provider_share"] == 1.0]
    return {"gates": gate_statistics(panel),
            "system": _guard(evaluate_panel, panel, "p_hybrid"),                # deployed hybrid (debate where available)
            "llm_only": _guard(evaluate_panel, panel.dropna(subset=["p_judge"]), "p_judge"),
            "hybrid_uniform": _guard(evaluate_panel, panel.dropna(subset=["p_hybrid_nd"]), "p_hybrid_nd"),
            "llm_only_uniform": _guard(evaluate_panel, panel.dropna(subset=["p_judge_nd"]), "p_judge_nd"),
            "analyst_mean": _guard(evaluate_panel, panel.dropna(subset=["p_analyst_mean"]), "p_analyst_mean"),
            "quant_twin": _guard(evaluate_panel, panel.dropna(subset=["p_quant"]), "p_quant"),
            "encompassing_hybrid_vs_quant": _guard(encompassing, panel, "p_hybrid", "p_quant"),
            "debate_paired_contrast": _guard(_debate_contrast, panel),
            "weight_on_quant": {"mean": _mean(panel["weight_on_quant"]),
                                "sd": float(panel["weight_on_quant"].std()) if panel["weight_on_quant"].notna().sum() > 1 else None},
            "citations": {"cite_exist_mean": _mean(panel["cite_exist_mean"]), "number_grounded_mean": _mean(panel["number_grounded_mean"])},
            "by_year": {str(y): _guard(evaluate_panel, g, "p_hybrid") for y, g in panel.groupby(panel["date"].dt.year)},
            "sensitivity": {"abstentions_excluded": {"rows": int((~panel["abstain"]).sum()),
                                                     **_guard(gate_statistics, panel[~panel["abstain"]])},
                            "primary_provider_rows": {"rows": int(len(all_primary)), **_guard(gate_statistics, all_primary)}},
            "identified_subsets": {"flagged_rows": int(flagged.sum()),
                                   "identified_rows": int((panel.loc[flagged, "identified"] == True).sum()),  # noqa: E712
                                   "all_flagged": _guard(subset_gaps, panel, n_boot=n_boot, seed=BOOTSTRAP_SEED),
                                   "text_rows_only": _guard(subset_gaps, text_only, n_boot=n_boot, seed=BOOTSTRAP_SEED)},
            "panel": {"rows": int(len(panel)), "failed": int(panel["failed"].sum()), "abstain": int(panel["abstain"].sum()),
                      "debated": int(panel["debated"].sum()), "debate_failed": int(panel["debate_failed"].sum()),
                      "missing_fwd_ret": int(panel["fwd_ret"].isna().sum()),
                      "delisted_rows": int(panel["delisted"].fillna(False).astype(bool).sum()),
                      "primary_provider_rows": int(len(all_primary)), "deployed_equals_hybrid": same},
            "weeks": weeks}


def evaluate_books(books: dict[str, dict], panel: pd.DataFrame, fwd: pd.DataFrame, funding: pd.DataFrame,
                   n_placebo: int = PLACEBO_DRAWS) -> tuple[dict, dict]:
    """portfolio.json (summary per book variant, funded) and books.json (weekly decomposition and weights)."""
    portfolio = {name: (summarize_book(w, fwd, funding=funding, n_placebo=n_placebo) if name == "rule_twin"
                        else _guard(summarize_book, w, fwd, funding=funding, n_placebo=n_placebo)) for name, w in books.items()}
    portfolio["rule_twin_no_funding"] = _guard(summarize_book, books["rule_twin"], fwd, n_placebo=n_placebo)
    have = set(zip(_utc(funding["date"].to_numpy()), funding["symbol"])) if len(funding) else set()
    keys = list(zip(panel["date"], panel["symbol"]))
    portfolio["funding_coverage"] = float(sum(k in have for k in keys) / len(keys)) if keys else None
    portfolio["cost_per_side"] = COST_PER_SIDE
    def _detail(w: dict) -> dict:
        comp = book_components(w, fwd, funding=funding)
        return {"weekly": [{"date": d, **row} for d, row in comp.to_dict("index").items()],
                "weights": {d: w[d] for d in sorted(w)}}

    return portfolio, {name: _guard(_detail, w) for name, w in books.items()}


def _finite(x) -> bool:
    return x is not None and isinstance(x, (int, float, np.integer, np.floating)) and math.isfinite(float(x))


def build_verdict(evaluation: dict, portfolio: dict) -> dict:
    """Registered gates applied by code. A statistic that cannot be computed fails its gate. Portfolio gates
    are evaluated only when every forecast gate passes (Charter 1 §5); otherwise their values are descriptive."""
    g = evaluation["gates"]
    ic_t, skill = g["hybrid_ic"]["nw_t"], g["hybrid_brier_recalibrated"]["skill"]
    t_llm, sub = g["encompassing_llm_vs_quant"]["t_llm"], g["subperiods"]
    forecast = {
        "hybrid_ic_nw_t": {"value": ic_t, "rule": f">= {GATE_IC_T}", "pass": bool(_finite(ic_t) and ic_t >= GATE_IC_T)},
        "hybrid_brier_skill_recalibrated": {"value": skill, "rule": f"> {GATE_BRIER_SKILL}",
                                            "test_weeks": g["hybrid_brier_recalibrated"].get("weeks"),
                                            "pass": bool(_finite(skill) and skill > GATE_BRIER_SKILL)},
        "encompassing_llm_nw_t": {"value": t_llm, "rule": f">= {GATE_ENCOMPASSING_T}",
                                  "pass": bool(_finite(t_llm) and t_llm >= GATE_ENCOMPASSING_T)},
        "subperiod_sign": {"value": sub["mean_ic_by_year"], "rule": "mean IC of the same sign in >= min(2, years present) years",
                           "years_present": sub["years_present"], "binding": sub["binding"], "pass": bool(sub["pass"])},
    }
    forecast_pass = all(v["pass"] for v in forecast.values())
    book = portfolio["rule_twin"]
    sr, p_date, p_asset = book["sharpe"], book["p_date_shuffle"], book["p_asset_shuffle"]
    port = {
        "net_sharpe": {"value": sr, "rule": f">= {GATE_NET_SHARPE}", "pass": bool(_finite(sr) and sr >= GATE_NET_SHARPE)},
        "placebo_date_shuffle_p": {"value": p_date, "rule": f"<= {GATE_PLACEBO_P}", "pass": bool(_finite(p_date) and p_date <= GATE_PLACEBO_P)},
        "placebo_asset_shuffle_p": {"value": p_asset, "rule": f"<= {GATE_PLACEBO_P}", "pass": bool(_finite(p_asset) and p_asset <= GATE_PLACEBO_P)},
    }
    portfolio_pass = all(v["pass"] for v in port.values())
    failed = [k for k, v in forecast.items() if not v["pass"]]
    if forecast_pass:
        failed += [k for k, v in port.items() if not v["pass"]]
    return {"charter": "llm-v2 Charter 1b", "weeks": evaluation["weeks"].get("n_completed"),
            "forecast_gates": forecast, "forecast_gates_pass": forecast_pass,
            "portfolio_gates_evaluated": forecast_pass,
            "portfolio_gates": port if forecast_pass else {k: {**v, "pass": None, "descriptive": True} for k, v in port.items()},
            "portfolio_gates_pass": portfolio_pass if forecast_pass else None,
            "deflated_sharpe_trial_count_1": {"value": book["psr_vs_zero"], "rule": "reported, no registered threshold"},
            "failed_gates": failed,
            "descriptive_errors": _errors({k: v for k, v in evaluation.items() if k != "gates"}) + _errors(portfolio),
            "verdict": "PASS" if forecast_pass and portfolio_pass else "FAIL"}


def finalize(rows: list[dict], books: dict[str, dict], fwd: pd.DataFrame, funding: pd.DataFrame, cards: pd.DataFrame,
             quant: pd.DataFrame, flags: pd.DataFrame | None, weeks: dict, n_placebo: int = PLACEBO_DRAWS,
             n_boot: int = BOOTSTRAP_DRAWS) -> dict:
    """Everything after the agent run: panel, forecast evaluation, book evaluation and the verdict, already in
    JSON-safe form (file name -> object, without cost.json)."""
    panel = assemble_panel(rows, fwd, cards, quant, flags)
    evaluation = evaluate_forecasts(panel, weeks, n_boot=n_boot)
    portfolio, detail = evaluate_books(books, panel, fwd, funding, n_placebo=n_placebo)
    verdict = build_verdict(evaluation, portfolio)
    records = panel.astype(object).where(panel.notna(), None).to_dict("records")
    return {"forecasts.json": json_safe({"rows": records}), "evaluation.json": json_safe(evaluation),
            "portfolio.json": json_safe(portfolio), "books.json": json_safe(detail), "verdict.json": json_safe(verdict)}

"""Registered NLST4 cache-only correction; all economics are retrospective.

No legacy main, fetcher, source writer, new pool or fitted model is invoked.
The command requires --execute and the common committed-source preflight.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack, contextmanager
import json
from pathlib import Path
import sys
from unittest.mock import patch
import urllib.request
import warnings

import numpy as np
import pandas as pd
import scipy.stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import predlab_nlst2_features as f2  # noqa: E402
import predlab_nlst3_features as f3  # noqa: E402
import predlab_nlst_dex_fetch as fetch  # noqa: E402
import predlab_nlst_dex_p0 as dex  # noqa: E402
from predlab_nlst3_p0 import block_bootstrap_ic  # noqa: E402
from predlab_nlst_lib import nw_tstat  # noqa: E402
from tradingagents.predlab import rpc_pool  # noqa: E402

DAY = 86400
CELL = "original_new_pool_cohort_causal_v2"
CONTROLS = ["deployer_supply_share", "deployer_age", "depth_growth"]


class CacheUnavailable(ValueError):
    """A historical observation cannot be reconstructed from authorized caches."""


def _network_forbidden(*args, **kwargs):
    raise RuntimeError("network forbidden: NLST4 correction uses existing caches only")


@contextmanager
def cache_only_headers(headers):
    """Fence imported aliases as well as RPC pool and HTTP transport paths."""
    def cached_header(block):
        if int(block) not in headers:
            raise CacheUnavailable(f"missing_header:{block}")
        return headers[int(block)]

    with ExitStack() as stack:
        for obj, names in [(fetch, ["rpc", "get_logs", "block_ts", "block_at_ts"]),
                           (f2, ["rpc", "get_logs", "eth_call", "fetch_pool_features"]),
                           (f3, ["get_logs", "fetch_ownership"]),
                           (rpc_pool, ["rpc", "rpc_batch", "get_pool"]),
                           (rpc_pool.Pool, ["rpc", "self_check"]),
                           (rpc_pool.Endpoint, ["_post"]),
                           (urllib.request, ["urlopen"])]:
            for name in names:
                stack.enter_context(patch.object(obj, name, _network_forbidden))
        stack.enter_context(patch.object(dex, "header", cached_header))
        stack.enter_context(patch.object(fetch, "header", cached_header))
        yield


def _json(ctx, path, reason):
    if not path.is_file():
        raise CacheUnavailable(f"{reason}:{path.name}")
    try:
        return json.loads(ctx.track(path).read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CacheUnavailable(f"invalid_cache:{path.name}") from exc


def _jsonl(ctx, path):
    if not path.is_file():
        raise CacheUnavailable(f"missing_required_cache:{path}")
    return [json.loads(line) for line in ctx.track(path).read_text().splitlines() if line]


def _anchors(rows):
    by_block = {}
    for row in rows:
        block, stamp = int(row["block"]), float(row["ts"])
        if block in by_block and by_block[block] != stamp:
            raise CacheUnavailable(f"conflicting_anchor:{block}")
        by_block[block] = stamp
    b = np.asarray(sorted(by_block), dtype=np.float64)
    t = np.asarray([by_block[x] for x in b], dtype=np.float64)
    if len(b) < 2 or not np.isfinite(t).all() or not (np.diff(t) > 0).all():
        raise CacheUnavailable("invalid_anchor_clock")

    def ts_of(block):
        if block < b[0] or block > b[-1]:
            raise CacheUnavailable(f"outside_anchor_clock:{block}")
        return float(np.interp(block, b, t))

    def block_at(stamp):
        if stamp < t[0] or stamp > t[-1]:
            raise CacheUnavailable(f"outside_anchor_clock:{stamp}")
        return int(np.interp(stamp, t, b))

    return ts_of, block_at


def _selection(pool, ts_of):
    """Original Sync selection needs blocks, independently of header coverage."""
    syncs = [r for r in pool["logs"] if r["kind"] == "sync"]
    created = ts_of(pool["meta"]["block"])
    entry = next((s for s in syncs if ts_of(s["block"]) >= created + DAY), None)
    if entry is None:
        raise CacheUnavailable("original_entered_pool_no_entry")
    entry_selection_ts = ts_of(entry["block"])
    exit7 = next((s for s in syncs if ts_of(s["block"]) >= entry_selection_ts + 7 * DAY), syncs[-1])
    return {"creation_block": pool["meta"]["block"], "create_ts_interp": created,
            "entry_block": entry["block"], "exit7_block": exit7["block"]}


def _timing(pool, ts_of):
    """Exactly the original helper's Sync selection, with exact exit availability."""
    selection = _selection(pool, ts_of)
    eh, xh = dex.header(selection["entry_block"]), dex.header(selection["exit7_block"])
    return {**selection, "entry_ts": eh["ts"], "exit7_ts": xh["ts"],
            "complete_ts": max(eh["ts"] + 7 * DAY, xh["ts"]),
            "decision_ts": eh["ts"], "available_ts": eh["ts"]}


def score_cohort(frame):
    """Retain missing rows and distinguish raw from causally standardized coverage."""
    out = frame.copy()
    cols = list(f3.SIGNS)
    out[cols] = out[cols].astype(float).replace([np.inf, -np.inf], np.nan)
    out["n_raw_features"] = out[cols].notna().sum(axis=1)
    valid = np.isfinite(out[["decision_ts", "available_ts"]].to_numpy(float)).all(axis=1)
    z = pd.DataFrame(np.nan, index=out.index, columns=cols)
    if valid.any():
        z.loc[valid] = f2.per_quarter_z(out.loc[valid], cols)
    out["n_standardized_features"] = z.notna().sum(axis=1)
    out["legit3_score"] = (z * pd.Series(f3.SIGNS, dtype=float)).mean(axis=1)
    out.loc[out.n_standardized_features < f3.MIN_FEATS, "legit3_score"] = np.nan
    for col in cols:
        out[f"z_{col}"] = z[col]
    return out


def _history_features(frame, records):
    """Every frozen creation remains in history, including unknown observations.

    Reuse the frozen feature formulas for known records, then qualify any
    output whose required history is not identifiable. Future/uncompleted
    outcomes do not taint decisions before their earliest possible availability.
    """
    def outcome_known(record):
        return bool(np.isfinite([record["ret7"], record["complete_ts"]]).all())

    entries = [{**r, "buyers": r["buyers"] if r["buyers"] is not None else {},
                "complete_ts": r["complete_ts"] if outcome_known(r) else np.inf} for r in records]
    for computed in [f3.smart_money(entries), f3.serial_deployer(entries)]:
        frame.loc[computed.index, computed.columns] = computed
    for row in records:
        pair, stamp, dep = row["pair"], row["create_ts"], row["deployer"]
        prior = [p for p in records if p["create_ts"] < stamp]
        possible = [p for p in prior if (p["complete_ts"] if np.isfinite(p["complete_ts"])
                                         else p["completion_lower_bound"]) < stamp]
        reasons = []
        if row["buyers"] is None:
            frame.loc[pair, ["smart_money_volshare", "smart_money_breadth"]] = np.nan
        unknown_wallet = [p for p in possible if p["buyers"] is None or
                          (p["buyers"] and not outcome_known(p))]
        if unknown_wallet:
            frame.loc[pair, ["smart_money_volshare", "smart_money_breadth", "n_qualified_wallets"]] = np.nan
            reasons.append(f"wallet_history_unavailable:{len(unknown_wallet)}")
        if dep:
            unknown_identity = [p for p in prior if not p["deployer"]]
            if unknown_identity:
                frame.loc[pair, "serial_deployer_count"] = np.nan
                reasons.append(f"deployer_count_history_unavailable:{len(unknown_identity)}")
            unknown_return = [p for p in possible if not p["deployer"] or
                              (p["deployer"] == dep and not outcome_known(p))]
            if unknown_return:
                frame.loc[pair, "serial_deployer_perf"] = np.nan
                reasons.append(f"deployer_return_history_unavailable:{len(unknown_return)}")
        else:
            reasons.append("deployer_identity_unavailable")
        frame.loc[pair, "missing_reasons"] = " | ".join(
            [x for x in [frame.loc[pair, "missing_reasons"], *reasons] if x])
    return frame


def build_cohort(ctx, source, *, expected_total=3981, expected_new=2776):
    """Read only frozen IDs and their cached windows; never enumerate new pool files."""
    source = Path(source)
    nl = source / "predlab/nlst"
    raw = nl / "dex_raw"
    frozen = pd.read_parquet(ctx.track(nl / "nlst4_features.parquet"), columns=["quarter", "new_set"])
    reference = pd.read_parquet(ctx.track(nl / "nlst4_events.parquet"), columns=["entry_ts"])
    if (len(frozen) != expected_total or not frozen.index.is_unique or
            frozen.new_set.isna().any() or frozen.new_set.dtype != bool or
            int(frozen.new_set.sum()) != expected_new or
            not reference.index.is_unique or set(reference.index) != set(frozen.index)):
        raise ValueError("frozen cohort identity/count mismatch; no substitute sample permitted")
    screened = {r["pair"]: r for r in _jsonl(ctx, raw / "screened.jsonl") if r["verdict"] == "KEEP"}
    prior = {r["pair"] for r in _jsonl(ctx, raw / "screened_nlst3_snapshot.jsonl") if r["verdict"] == "KEEP"}
    for pair, row in frozen.iterrows():
        if (pair not in screened or str(screened[pair]["quarter"]) != str(row.quarter) or
                bool(row.new_set) != (pair not in prior)):
            raise ValueError(f"frozen cohort screening membership mismatch:{pair}")
    ts_of, block_at = _anchors(_jsonl(ctx, raw / "anchors.jsonl"))
    headers = {}
    for h in _jsonl(ctx, raw / "headers.jsonl"):
        block = int(h["block"])
        if block in headers and headers[block] != h:
            raise CacheUnavailable(f"conflicting_header:{block}")
        if not np.isfinite([h["ts"], h["basefee"]]).all() or h["basefee"] < 0:
            raise CacheUnavailable(f"invalid_header:{block}")
        headers[block] = h
    fx = ctx.read_market(source / "predlab/klines_5m/ETHUSDT.parquet",
                         end_exclusive=ctx.family_gate["settlement_fx_end_exclusive"])["close"]
    fx.attrs.update(bar_interval="5min", timestamp_label="open")
    rows, history = [], []
    with cache_only_headers(headers):
        for number, (pair, frozen_row) in enumerate(frozen.iterrows(), 1):
            row = {"pair": pair, "quarter": str(frozen_row.quarter), "new_set": bool(frozen_row.new_set),
                   **{c: np.nan for c in f3.SIGNS}, "n_qualified_wallets": np.nan,
                   "decision_ts": np.nan, "available_ts": np.nan, "entry_ts": np.nan,
                   "entry_block": np.nan, "raw_b24": np.nan, "ret7": np.nan,
                   "ret7_s5000": np.nan, "list_date": pd.NaT}
            row["creation_block"] = screened[pair]["block"]
            row["create_ts_interp"] = ts_of(row["creation_block"])
            if not (pd.Timestamp("2021-01-01", tz="UTC").timestamp() <= row["create_ts_interp"] <
                    pd.Timestamp("2025-04-01", tz="UTC").timestamp()):
                raise ValueError(f"frozen cohort creation outside development:{pair}")
            reasons = []
            pool = raw2 = None
            pool_valid = False
            buyers = deployer = None
            try:
                pool = _json(ctx, raw / "pools" / f"{pair}.json", "missing_pool")
                meta, logs = pool["meta"], pool["logs"]
                if meta["pair"] != pair or str(meta["quarter"]) != row["quarter"]:
                    raise CacheUnavailable("pool_identity_mismatch")
                if meta["block"] != row["creation_block"]:
                    raise ValueError(f"frozen cohort creation block mismatch:{pair}")
                row.update(_selection(pool, ts_of))
                pool_valid = True
                row.update(_timing(pool, ts_of))
                if row["entry_ts"] != reference.loc[pair, "entry_ts"]:
                    row.update({c: np.nan for c in ["decision_ts", "available_ts", "complete_ts"]})
                    raise CacheUnavailable("original_entry_clock_mismatch")
                row["list_date"] = pd.Timestamp(row["entry_ts"], unit="s", tz="UTC")
                try:
                    row.update(dex.pool_event(pool, ts_of, fx))
                except CacheUnavailable as exc:
                    reasons.append(str(exc))
                except ValueError as exc:
                    if "5m" not in str(exc):
                        raise
                    reasons.append("missing_completed_fx:" + str(exc))
            except CacheUnavailable as exc:
                reasons.append(str(exc))
            except (KeyError, TypeError, OverflowError) as exc:
                reasons.append(f"invalid_pool_schema:{type(exc).__name__}")
                pool_valid = False
            # Creation/deployer identity can be known even if an event header
            # or h24 buyer window is missing. Never omit that prior creation.
            try:
                raw2 = _json(ctx, nl / "nlst2_raw" / f"{pair}.json", "missing_raw2")
                if raw2["pair"] != pair:
                    raise CacheUnavailable("raw2_identity_mismatch")
                deployer = raw2.get("deployer") or None
                row["raw_b24"] = raw2["b24"]
                if not pool_valid or not np.isfinite(row["entry_block"]):
                    raise CacheUnavailable("feature_window_entry_unverified")
                if raw2["b24"] >= row["entry_block"]:
                    raise CacheUnavailable("feature_window_not_strictly_prior")
                if pool_valid:
                    controls = f2.build_row(meta, logs, raw2, ts_of)
                    row.update({c: controls[c] for c in CONTROLS})
                    row.update(f3.flow_features(logs, meta["weth_is_0"], meta.get("first_weth_reserve"),
                                                block_at(row["create_ts_interp"] + DAY / 2), raw2["b24"]))
                    buyers = f3.pool_buyers(raw2["swaps_topics"], meta["weth_is_0"])
                    try:
                        ownership = _json(ctx, nl / "nlst3_raw" / f"{pair}.json", "missing_ownership")
                        if (ownership.get("retrieval_status") != "ok" or
                                ownership.get("block_end") != raw2["b24"] or
                                not isinstance(ownership.get("renounced"), bool)):
                            reasons.append("ownership_unverified")
                        else:
                            row["ownership_renounced"] = float(ownership["renounced"])
                    except CacheUnavailable as exc:
                        reasons.append(str(exc))
            except CacheUnavailable as exc:
                reasons.append(str(exc))
            except (KeyError, TypeError, OverflowError) as exc:
                reasons.append(f"invalid_raw2_schema:{type(exc).__name__}")
                row.update({c: np.nan for c in f3.SIGNS})
                buyers = None
            history.append({"pair": pair, "create_ts": row["create_ts_interp"],
                            "complete_ts": row.get("complete_ts", np.nan), "ret7": row["ret7"],
                            "completion_lower_bound": float(reference.loc[pair, "entry_ts"]) + 7 * DAY,
                            "deployer": deployer, "buyers": buyers})
            row["deployer_identity_known"] = bool(deployer)
            row["buyer_window_known"] = buyers is not None
            row["missing_reasons"] = " | ".join(reasons)
            rows.append(row)
            if number % 250 == 0:
                print(f"NLST4 cached pools: {number}/{len(frozen)}", flush=True)
    frame = pd.DataFrame(rows).set_index("pair")
    frame = _history_features(frame, history)
    frame = score_cohort(frame)
    frame["unavailable_features"] = frame[list(f3.SIGNS)].isna().apply(
        lambda row: ",".join(row.index[row]), axis=1)
    frame["score_available"] = np.isfinite(frame.legit3_score)
    return frame


def evaluate_cohort(frame):
    """Frozen T1/T2 on available new rows, with full requested denominators."""
    requested = frame.loc[frame.new_set]
    valid = np.isfinite(requested[["legit3_score", "ret7"]].to_numpy(float)).all(axis=1)
    new = requested.loc[valid].copy()
    new["quarter"] = new.quarter.astype(str)
    ic = ic_p = p5 = conditional_p5 = np.nan
    boot = np.full(1000, np.nan)
    if len(new) >= 3 and new.legit3_score.nunique() > 1 and new.ret7.nunique() > 1:
        ic, ic_p = st.spearmanr(new.legit3_score, new.ret7)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", st.ConstantInputWarning)
            boot = block_bootstrap_ic(new, "legit3_score", n_draws=1000, seed=7)
        if np.isfinite(boot).any():
            conditional_p5 = float(np.nanpercentile(boot, 5))
        if len(boot) == 1000 and np.isfinite(boot).all():
            p5 = float(np.percentile(boot, 5))
    q80 = float(new.legit3_score.quantile(.8)) if len(new) else np.nan
    top = new.loc[new.legit3_score >= q80].sort_values("list_date")
    mean = float(top.ret7.mean())
    _, t, p_two = nw_tstat(top.ret7.to_numpy(), lag=5)
    p_one = p_two / 2 if t > 0 else 1 - p_two / 2
    ex_top = top.ret7.drop(top.ret7.abs().idxmax()) if len(top) else top.ret7
    total_abs = float(top.ret7.abs().sum())
    top1 = float(top.ret7.abs().max() / total_abs) if total_abs > 0 else np.nan
    stress_available = np.isfinite(top.ret7_s5000).sum()
    stress_mean = float(top.ret7_s5000.mean()) if stress_available == len(top) else np.nan
    t1 = bool(ic > 0 and p5 > 0)
    t2 = bool(mean > 0 and p_one < .05 and ex_top.mean() > 0 and top1 <= .25 and
              np.sign(stress_mean) == np.sign(mean))
    t1_available = bool(np.isfinite([ic, p5]).all())
    t2_available = bool(np.isfinite([mean, p_one, ex_top.mean(), top1, stress_mean]).all())
    verdict = ("PASS" if t1 and t2 else "FAIL") if t1_available and t2_available else "UNAVAILABLE"
    reasons = Counter(r.split(":", 1)[0] for value in requested.missing_reasons for r in value.split(" | ") if r)
    return {"n_cohort_requested": len(frame), "n_prior_requested": int((~frame.new_set).sum()),
            "n_new_requested": len(requested), "n_new_scoreable": len(new),
            "n_new_unavailable": len(requested) - len(new),
            "n_new_event_available": int(np.isfinite(requested.ret7).sum()),
            "n_quarters": int(new.quarter.nunique()), "new_missing_reason_counts": dict(reasons),
            "per_quarter_requested": requested.quarter.value_counts().to_dict(),
            "per_quarter_scoreable": new.quarter.value_counts().to_dict(),
            "new_feature_available": {c: int(np.isfinite(requested[c]).sum()) for c in f3.SIGNS if c in requested},
            "T1": {"ic": float(ic), "ic_p_diagnostic": float(ic_p), "boot_p5": p5,
                   "boot_p5_conditional_finite_diagnostic": conditional_p5,
                   "bootstrap_ic_draws": boot.tolist(),
                   "bootstrap_draws": 1000, "bootstrap_finite_draws": int(np.isfinite(boot).sum()),
                   "available": t1_available, "pass": t1},
            "T2": {"q80_full_new_sample": q80, "n_top": len(top), "mean_ret7": mean,
                   "nw_t": t, "p_one_sided": p_one, "nw_lag": 5,
                   "mean_ex_top": float(ex_top.mean()), "median_ret7": float(top.ret7.median()),
                   "top1_share": top1, "mean_ret7_s5000": stress_mean,
                   "n_stress_available": int(stress_available), "available": t2_available, "pass": t2},
            "diagnostic_thresholds_pass": t1 and t2 if verdict != "UNAVAILABLE" else None,
            "diagnostic_verdict": verdict, "promotion_eligible": False,
            "causal_entry_rule_tested": False,
            "interpretation": "retrospective_ranking_and_cohort_diagnostic",
            "qualifications": ["Original new-set outcomes were already examined; no virgin holdout claim.",
                               "Global score q80 uses the full evaluated new cohort; no online entry policy.",
                               "Creation timestamps are interpolated; original pair/quarter/block membership is frozen.",
                               "Unavailable features and causal warmup reduce score coverage; full cohort is retained.",
                               "Original gas/constant-product assumptions exclude MEV and are not realized live fills."]}


def run(ctx, source):
    config = {"original_gate": "predlab_nlst4", "features": dict(f3.SIGNS), "min_features": 6,
              "smart_wallet_min_priors": 3, "smart_wallet_quantile": .8,
              "normalization": "same_quarter_strict_prior_decision_and_availability_min2",
              "completion": "max(entry_header_ts+7days,selected_exit7_header_ts)",
              "history_missingness": "retain_every_creation;unknown_required_history_unavailable_after_earliest_possible_completion",
              "creation_membership": "original_pairs_quarters_blocks;interpolated_timestamps",
              "feature_window": "raw2.b24 < exact_entry_block", "ownership": "verified_retrieval_status_only",
              "fx": "exact_last_completed_open_labeled_ETH_5min_close",
              "settlement_fx_end_exclusive": ctx.family_gate["settlement_fx_end_exclusive"],
              "notionals_usd": [1000, 5000], "lp_fee_each_side": .003,
              "gas_units_each_swap": 150000, "tip_gwei": 2,
              "bootstrap_draws": 1000, "bootstrap_seed": 7, "nw_lag": 5,
              "q80": "full_new_cohort_retrospective_only", "promotion_eligible": False}
    try:
        frame = build_cohort(ctx, source)
        metrics = evaluate_cohort(frame)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        # A family-wide input failure still occupies its registered cell. No
        # synthetic IDs or zero outcomes are manufactured when the cohort
        # itself cannot be recovered. finish still enforces source provenance;
        # its integrity/preflight exceptions must never be swallowed here.
        metrics = {"diagnostic_verdict": "UNAVAILABLE", "promotion_eligible": False,
                   "causal_entry_rule_tested": False, "n_cohort_requested": 3981,
                   "n_prior_requested": 1205, "n_new_requested": 2776,
                   "n_cohort_reconstructed": 0,
                   "blocked_reason": f"{type(exc).__name__}: {exc}",
                   "required_action": "Recover and verify the registered immutable cache/provenance; do not fetch replacement history or infer missing outcomes."}
        return ctx.finish({"status": "blocked", "metrics": metrics,
                           "prior_artifacts_overwritten": False},
                          [{"id": CELL, "config": config, "metrics": metrics}])
    ctx.write_frame("cohort_causal_v2.parquet", frame)
    return ctx.finish({"status": "completed_with_coverage_qualifications", "metrics": metrics,
                       "network_used": False, "prior_artifacts_overwritten": False},
                      [{"id": CELL, "config": config, "metrics": metrics}])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="run the committed registered correction once")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute required; empirical execution follows the tested-source commit")
    from audit_reeval_common import RunContext
    ctx = RunContext("nlst4")
    sources = [Path(p) for p in ctx.gate["source_roots"] if Path(p).parent.name == "TradingAgents-predlab"]
    if len(sources) != 1:
        raise ValueError("registered original predlab source root is ambiguous")
    print(run(ctx, sources[0]))


if __name__ == "__main__":
    main()

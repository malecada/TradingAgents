"""Original-input allocation forensics only. Default invocation is a dry run.

No portfolio, return panel, performance probe, forecast or network call is used.
The original cascade signal internally uses log differences as registered.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from scripts.audit_reeval_common import plain, sha256
from scripts.audit_reevaluate_accounting_2026_09_09 import membership_mask
from tradingagents.predlab import registry
from tradingagents.xsect import liq_fade

KEY = "audit_lifecycle_exposure_2026_09_10"
ORIGINAL = "audit_reevaluation_2026_09_09"
ORIGINAL_COMMIT = "49fb9e47c4d9e40b9c3f1b7de475041ec63aac76"
ORIGINAL_RESULT_SHA256 = "30a8629fa9214ac031d8a642f719bccdff60c6f1a0b473b365e699dd79f6837a"
DEV = ("2021-01-01", "2025-03-31")
END = pd.Timestamp("2025-04-01", tz="UTC")
HOUR = pd.Timedelta(hours=1)


def utc(value):
    value = pd.Timestamp(value)
    return value.tz_localize("UTC") if value.tz is None else value.tz_convert("UTC")


def validate_clock(index):
    if (not isinstance(index, pd.DatetimeIndex) or index.tz is None or
            not len(index) or not index.is_unique or not index.is_monotonic_increasing or
            not index.equals(pd.date_range(index[0], index[-1], freq="h")) or
            not (index == index.floor("h")).all()):
        raise ValueError("allocation requires a complete aligned hourly clock")


def audit_event(allocation, event):
    """Inspect requested weights, without inferring NAV, quantity or an exit fill."""
    validate_clock(allocation.index)
    clock = allocation.index.tz_convert("UTC")
    closure = utc(event["closure_utc"])
    boundary = closure.floor("h")
    result = {"symbol": event["symbol"], "closure_utc": closure.isoformat(),
              "readiness_certified": False, "order_quantity_changes_measured": False}
    if boundary not in clock or boundary - HOUR not in clock:
        return {**result, "status": "unavailable_event_clock"}
    values = allocation.to_numpy(dtype=float)
    previous = np.r_[np.nan, values[:-1]]
    i = clock.get_loc(boundary)
    incoming, requested = previous[i], values[i]
    exact_boundary = boundary == closure
    # Allocation at row t is decided no earlier than t and values through t+1h.
    # Equality belongs to the post-event regime; no invented t-1ms execution.
    straddle = (clock < closure) & (clock + HOUR > closure)
    after = clock >= closure
    allocated = np.isfinite(values) & (values != 0.)
    incoming_unresolved = bool(exact_boundary and np.isfinite(incoming) and incoming != 0.)
    unknown = bool(not np.isfinite([incoming, requested]).all() or
                   (~np.isfinite(values[straddle | after])).any())
    result.update(boundary={"bar_open_utc": boundary.isoformat(),
                  "decision_available_utc": boundary.isoformat(),
                  "valuation_available_utc": (boundary + HOUR).isoformat(),
                  "event_at_exact_boundary": exact_boundary,
                  "incoming_previous_allocation": float(incoming) if np.isfinite(incoming) else None,
                  "requested_allocation": float(requested) if np.isfinite(requested) else None},
                  unreconciled_incoming_at_closure=incoming_unresolved,
                  straddling_allocated_bars=int((allocated & straddle).sum()),
                  post_closure_allocated_bars=int((allocated & after).sum()),
                  post_closure_last_requested_utc=(clock[allocated & after][-1].isoformat()
                                                  if (allocated & after).any() else None))
    restriction = event.get("new_position_restriction_utc", event.get("new_position_cutoff_utc"))
    restricted = np.zeros(len(clock), dtype=bool)
    restriction_result = {"restriction_utc": restriction, "order_quantity_increases": None}
    if restriction is not None:
        cutoff = utc(restriction)
        if cutoff > closure:
            raise ValueError("new-position restriction cannot follow closure")
        restricted = clock >= cutoff
        known = np.isfinite(values) & np.isfinite(previous)
        new = restricted & known & (values != 0.) & (previous == 0.)
        increase = restricted & known & (values != 0.) & (previous != 0.) & (np.abs(values) > np.abs(previous))
        unchanged = restricted & known & (values != 0.) & (values == previous)
        restriction_result.update(new_target_requests=int(new.sum()),
            increased_nonzero_target_requests=int(increase.sum()),
            new_target_requests_before_closure=int((new & (clock < closure)).sum()),
            increased_nonzero_target_requests_before_closure=int((increase & (clock < closure)).sum()),
            nonzero_unchanged_target_bars=int(unchanged.sum()),
            unavailable_target_transition_bars=int((restricted & ~known).sum()))
        unknown |= bool((restricted & ~known).any())
    else:
        new = increase = np.zeros(len(clock), dtype=bool)
        restriction_result["status"] = "no_separate_restriction_established"
    result["restriction"] = restriction_result
    conflict = bool(incoming_unresolved or (allocated & (straddle | after)).any() or new.any() or increase.any())
    result["observed_conflict"] = conflict
    result["allocation_uncertainty"] = unknown
    result["status"] = ("observed_lifecycle_conflict" if conflict else
                        "unavailable_allocation" if unknown else "no_observed_conflict_qualified")
    # Preserve exact requested rows around the event, plus every later nonzero
    # request. Rows are not rewritten to zero after settlement.
    detail = (((clock >= boundary - HOUR) & (clock <= boundary + HOUR)) |
              (allocated & after) | (restricted & (allocated | (np.isfinite(previous) & (previous != 0.)))))
    result["allocation_rows"] = [
        {"bar_open_utc": t.isoformat(),
         "previous_requested_allocation": float(old) if np.isfinite(old) else None,
         "requested_allocation": float(w) if np.isfinite(w) else None}
        for t, old, w in zip(clock[detail], previous[detail], values[detail])]
    return result


def build_original_allocations(close, volume, monthly, cells, dev_clock):
    """Reuse just the frozen membership, cascade and event-weight functions."""
    validate_clock(close.index)
    if not close.index.equals(volume.index) or list(close.columns) != list(volume.columns):
        raise ValueError("unaligned original feature panels")
    if not close.columns.is_unique or list(close.columns) != sorted(close.columns):
        raise ValueError("original allocation tie order must be sorted unique symbols")
    mask = membership_mask(monthly, close.columns, close.index)
    close = close.where(close > 0.)
    coverage = {"rectangular_panel_observations": int(close.size),
                "missing_close_observations": int((~np.isfinite(close.to_numpy())).sum()),
                "missing_volume_observations": int((~np.isfinite(volume.to_numpy())).sum()),
                "qualification": "Rectangular counts include prelisting and terminal periods; missing source inputs are retained exactly as in the original signal construction."}
    triggers = {thr: (liq_fade.cascade_triggers(close, volume, thr, window=2160, min_periods=1440) & mask).loc[dev_clock]
                for thr in sorted({c["thr"] for c in cells})}
    weights = {}
    for cell in cells:
        trig = triggers[cell["thr"]]
        names = trig.columns[trig.to_numpy().any(axis=0)].tolist()
        # Same subset, column order, cap, timer reset and development initialization
        # as the original wrapper. No prepare_liq_fade or performance probe call.
        weights[cell["id"]] = liq_fade.event_weights_hourly(trig[names], cell["H"], w_per=.1, cap=1.)
    return weights, coverage


def verify_original_sources(rows, source_root, expected_count=217):
    if len(rows) != expected_count:
        raise ValueError("original hourly manifest count differs")
    if len({r["symbol"] for r in rows}) != len(rows) or len({r["path"] for r in rows}) != len(rows):
        raise ValueError("duplicate original manifest symbol or path")
    root = Path(source_root).resolve()
    hashes = {}
    for row in rows:
        path = Path(row["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"input outside original source root: {path}")
        if sha256(path) != row["sha256"]:
            raise ValueError(f"original input hash mismatch: {path}")
        hashes[str(path)] = row["sha256"]
    return hashes


def read_original_market(path, start, end):
    start, end = utc(start), utc(end)
    if end > END or start < utc("2020-06-01") or start >= end:
        raise ValueError("original market read outside development/warmup bounds")
    schema = pq.ParquetFile(path).schema_arrow
    meta = json.loads(schema.metadata.get(b"pandas", b"{}"))
    indexes = [x for x in meta.get("index_columns", []) if isinstance(x, str)]
    field = "ts" if "ts" in schema.names else (indexes[0] if indexes else None)
    if field is None:
        raise ValueError("original market input has no timestamp column")
    frame = pd.read_parquet(path, columns=[field, "close", "quote_volume"],
                            filters=[(field, ">=", start), (field, "<", end)])
    if field in frame.columns:
        frame = frame.set_index(field)
    frame.index = pd.DatetimeIndex(frame.index)
    if frame.index.tz is None or not frame.index.is_unique or not frame.index.is_monotonic_increasing:
        raise ValueError("original market clock is naive, duplicate or unsorted")
    frame.index = frame.index.tz_convert("UTC")
    if len(frame) and ((frame.index < start) | (frame.index >= end) | (frame.index != frame.index.floor("h"))).any():
        raise ValueError("original market timestamp outside aligned development clock")
    return frame[["close", "quote_volume"]]


def checked_file(path, expected, hashes):
    path = Path(path).resolve()
    if sha256(path) != expected:
        raise ValueError(f"pinned input hash mismatch: {path}")
    hashes[str(path)] = expected
    return path


def validate_registration(gate, original):
    family = gate["families"]["liq_fade"]
    prior = original["families"]["liq_fade"]
    if (gate["type"] != "exposure_only_forensic_audit" or gate["strategy_evaluation_permitted"] or
            not gate["signal_weight_reconstruction_permitted"] or not gate["original_inputs_only"] or
            gate["original_cycle"] != ORIGINAL or gate["allow_holdout"] or
            gate["development_window"] != list(DEV) or family["cells"] != prior["cells"] or
            len(family["cells"]) != 6 or len(gate["events"]) != 5 or
            len({e["symbol"] for e in gate["events"]}) != 5 or
            family["warmup_start"] != prior["warmup_start"] or
            family["hourly_end"] != prior["hourly_end"] or
            [family[k] for k in ("weight_per_event", "gross_cap", "feature_window", "feature_min_periods")] != [.1, 1., 2160, 1440]):
        raise ValueError("exposure registration differs from frozen original construction")
    for event in gate["events"]:
        if not utc(DEV[0]) <= utc(event["closure_utc"]) < END:
            raise ValueError("lifecycle event outside development")


def write_forensic_artifact(out, result):
    """Exclusive six-row nonfinancial ledger; never call the trial registry."""
    out = Path(out)
    final, ledger = out / "result.json", out / "forensic-ledger.jsonl"
    if final.exists() or ledger.exists():
        raise FileExistsError("forensic artifact already exists")
    cells = result["cells"]
    if len(cells) != 6 or len({c["id"] for c in cells}) != 6:
        raise ValueError("forensic artifact must retain six unique cells")
    for cell in cells:
        events = cell["metrics"]["events"]
        if (len(events) != 5 or len({e["symbol"] for e in events}) != 5 or
                cell["metrics"].get("financial_candidate_evaluated") is not False):
            raise ValueError("forensic cell must retain five events without a financial candidate")
    rows = [{"experiment": KEY, "cell": c["id"], "type": "nonfinancial_exposure_forensic",
             "config": c["config"], "metrics": c["metrics"]} for c in cells]
    ledger_bytes = ("\n".join(json.dumps(plain(r), allow_nan=False, sort_keys=True) for r in rows) + "\n").encode()
    outputs = {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file()}
    outputs[ledger.name] = hashlib.sha256(ledger_bytes).hexdigest()
    result = {**result, "output_sha256": outputs,
              "forensic_ledger": "forensic-ledger.jsonl", "central_trial_ledger_written": False}
    # All six rows and the complete result must serialize before either file is
    # opened. A low-level interrupted write still requires manual provenance review.
    encoded = json.dumps(plain(result), indent=2, allow_nan=False) + "\n"
    with ledger.open("xb") as handle:
        handle.write(ledger_bytes)
    with final.open("x") as handle:
        handle.write(encoded)
    return final


def execute():
    gate = registry.get_experiment(KEY)
    original = registry.get_experiment(ORIGINAL)
    validate_registration(gate, original)
    provenance = registry.preflight(KEY, DEV)
    central_ledger = registry.ledger_path().resolve()
    central_before = sha256(central_ledger) if central_ledger.exists() else None
    hashes = {}
    # Refuse any change to the reused construction, even in a later clean commit.
    for name in ("tradingagents/xsect/liq_fade.py", "scripts/audit_reevaluate_accounting_2026_09_09.py"):
        old = subprocess.check_output(["git", "show", f"{ORIGINAL_COMMIT}:{name}"], cwd=ROOT)
        checked_file(ROOT / name, hashlib.sha256(old).hexdigest(), hashes)
    original_result = ROOT / "data/predlab" / ORIGINAL / "liq_fade/result.json"
    checked_file(original_result, ORIGINAL_RESULT_SHA256, hashes)
    inventory_path = checked_file(ROOT / gate["inventory"]["path"], gate["inventory"]["sha256"], hashes)
    inventory = json.loads(inventory_path.read_text())
    source = Path(gate["source_roots"][0]).resolve() / "xsect"
    hashes.update(verify_original_sources(inventory["hourly"]["files"], source / "klines_1h"))
    for path, digest in inventory["scope_files"].items():
        if not Path(path).resolve().is_relative_to(source):
            raise ValueError("inventory scope file outside original root")
        checked_file(path, digest, hashes)
    universe_path = checked_file(source / "liq_fade_universe.json", gate["universe_sha256"], hashes)
    names_path = source / "liq_fade_symbols.txt"
    if str(names_path) not in hashes:
        raise ValueError("original symbol list not pinned by inventory")
    names = names_path.read_text().split()
    if len(names) != len(set(names)) or not names:
        raise ValueError("original symbol list empty or duplicated")
    files = {r["symbol"]: Path(r["path"]) for r in inventory["hourly"]["files"]}
    if not set(names).issubset(files):
        raise ValueError("original symbol is missing from inventory")
    monthly = json.loads(universe_path.read_text())
    event_receipts = {}
    for event in gate["events"]:
        code = event["official_article_code"]
        candidates = [ROOT / "data/recovery/2026-09-10/prx-identities" / f"{code}.json",
                      ROOT / "data/recovery/2026-09-10/settlements" / f"cms-{code}.json"]
        path = next((p for p in candidates if p.exists()), None)
        if path is None:
            raise ValueError(f"official event receipt absent: {code}")
        checked_file(path, sha256(path), hashes)
        response = json.loads(path.read_text())
        if response["data"]["code"] != code or response["success"] is not True:
            raise ValueError("invalid official event receipt")
        event_receipts[event["symbol"]] = {"path": str(path), "sha256": hashes[str(path.resolve())]}
    out = ROOT / gate["outputs"]
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    with (out / "started.json").open("x") as handle:
        json.dump({"experiment": KEY, "started_utc": started, **provenance}, handle, indent=2)
    family = gate["families"]["liq_fade"]
    cells = []
    coverage = {}
    try:
        clock = pd.date_range(utc(family["warmup_start"]), utc(family["hourly_end"]), freq="h")
        dev_clock = pd.date_range(utc(DEV[0]), utc(family["hourly_end"]), freq="h")
        frames = {}
        for i, name in enumerate(sorted(names), 1):
            frames[name] = read_original_market(files[name], family["warmup_start"], END)
            if i % 50 == 0:
                print(f"Loaded original signal inputs: {i}/{len(names)} symbols", flush=True)
        close = pd.DataFrame({s: f.close.reindex(clock) for s, f in frames.items()}, index=clock)
        volume = pd.DataFrame({s: f.quote_volume.reindex(clock) for s, f in frames.items()}, index=clock)
        weights, coverage = build_original_allocations(close, volume, monthly, family["cells"], dev_clock)
        for config in family["cells"]:
            events = []
            for event in gate["events"]:
                symbol = event["symbol"]
                w = weights[config["id"]].get(symbol, pd.Series(0., index=dev_clock, name=symbol))
                row = audit_event(w, event)
                boundary = utc(event["closure_utc"]).floor("h")
                lookback = close.loc[boundary - (2160 + config["H"] + 1) * HOUR:boundary - HOUR, symbol]
                qlookback = volume.loc[lookback.index, symbol]
                row["original_local_input_coverage"] = {
                    "lookback_start": str(lookback.index[0]) if len(lookback) else None,
                    "lookback_end": str(lookback.index[-1]) if len(lookback) else None,
                    "missing_or_invalid_close": int((~np.isfinite(lookback) | (lookback <= 0)).sum()),
                    "missing_volume": int((~np.isfinite(qlookback)).sum()),
                    "qualification": "Local lookback does not certify full slot-competition history or executable quantities; original missing-signal behavior is reproduced."}
                events.append(row)
            cells.append({"id": config["id"], "config": config,
                "metrics": {"status": "exposure_forensics_complete", "financial_candidate_evaluated": False,
                    "n_registered_events": len(gate["events"]), "events": events,
                    "n_events_with_observed_conflict": sum(e.get("observed_conflict", False) for e in events),
                    "readiness_certified": False}})
            print(f"Inspected original allocation cell {len(cells)}/{len(family['cells'])}", flush=True)
    except Exception as exc:
        cells = [{"id": c["id"], "config": c, "metrics": {
            "status": "unavailable_reconstruction", "financial_candidate_evaluated": False,
            "reason": f"{type(exc).__name__}: {exc}", "readiness_certified": False,
            "events": [{"symbol": e["symbol"], "closure_utc": e["closure_utc"],
                        "status": "unavailable_reconstruction"} for e in gate["events"]]}}
                 for c in family["cells"]]
    for path, expected in hashes.items():
        if sha256(Path(path)) != expected:
            raise RuntimeError(f"input changed during reconstruction: {path}")
    if registry.preflight(KEY, DEV) != provenance:
        raise RuntimeError("source, gate or policy changed during reconstruction")
    central_after = sha256(central_ledger) if central_ledger.exists() else None
    if central_after != central_before:
        raise RuntimeError("central trial ledger changed during exposure-only reconstruction")
    result = plain({"experiment": KEY, "type": "exposure_only_forensic_audit", **provenance,
        "started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
        "original_cycle": ORIGINAL, "original_source_commit": ORIGINAL_COMMIT,
        "original_result_sha256": ORIGINAL_RESULT_SHA256, "registered_gate": gate,
        "n_registered_cells": 6, "n_registered_events_per_cell": 5, "cells": cells,
        "input_sha256": hashes, "inputs_unchanged_after_run": True,
        "event_receipts": event_receipts, "original_input_coverage": coverage,
        "original_inventory_internal_missing_hours": inventory["hourly"]["total_internal_missing_periods"],
        "no_pnl_or_performance_statistics": True, "financial_candidates_evaluated": 0,
        "central_trial_ledger_sha256": central_before, "central_trial_ledger_unchanged": True,
        "holdout_read": False, "readiness_certified": False,
        "runtime": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
        "limitations": ["Requested allocations are not account fills or actual quantities.",
            "Original gaps and post-termination bars are preserved only to reconstruct historical assumptions.",
            "An absent flag does not certify full input coverage or lifecycle/settlement execution readiness.",
            "Only five registered events are audited; earlier same-ticker incarnations and all other lifecycle events remain outside this audit."]})
    write_forensic_artifact(out, result)
    print(f"Exposure-only artifact: {out / 'result.json'}", flush=True)
    return out / "result.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="consume the committed one-shot exposure audit")
    args = parser.parse_args(argv)
    if not args.execute:
        print(f"Dry run: {KEY}; use --execute only after gate and source are committed. No inputs or output state consumed.")
        return 0
    execute()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

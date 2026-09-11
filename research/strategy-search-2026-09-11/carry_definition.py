"""Frozen saved-series definition diagnostic; never a cash-PnL reconstruction."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import io
import json
import math
from pathlib import Path
import re
import statistics

from tradingagents.research import ResearchRun

REGISTRATION = "research/strategy-search-2026-09-11/gates.json"
EXPERIMENT = "carry-definition-20260911"
WINDOWS = {"dev": ("2021-11-08", "2025-03-31"),
           "holdout": ("2025-04-01", "2026-07-01")}
SERIES = ("btc", "eth", "sleeve")
SR_TOLERANCE = 1e-9


def _day(value: str) -> datetime:
    """Date-only saved observations denote UTC days, never local time."""
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}(?:T00:00:00(?:Z|\+00:00))?", value
    ):
        raise ValueError("dates must be ISO UTC midnight days")
    return datetime.fromisoformat(value[:10]).replace(tzinfo=timezone.utc)


def _finite(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be finite numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite numeric")
    return result


def _stats(values):
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    sr = mean / sd * math.sqrt(252) if sd > 0 else None
    if sr is not None and not math.isfinite(sr):
        sr = None
    invalid = sum(value <= -1 for value in values)
    log_sum = math.fsum(math.log1p(value) for value in values) if not invalid else None
    try:
        index = math.exp(log_sum) if log_sum is not None else None
    except OverflowError:
        index = None
    total = math.fsum(values)
    return {
        "n": len(values), "sum": total, "mean": mean,
        "sample_std_ddof1": sd if len(values) > 1 else None,
        "sr_sqrt252": sr,
        "sr_unavailable_reason": None if sr is not None else "zero/undefined dispersion or nonfinite ratio",
        "compounded_index_starting_at_one": index,
        "index_unavailable_reason": ("simple-index day <= -1" if invalid else
                                     "index overflow" if index is None else None),
        "convention_diagnostic": {
            "label": "invalid log-return arithmetic booking diagnostic; not cash PnL",
            "all_days": len(values), "valid_simple_index_days": len(values) - invalid,
            "invalid_simple_index_days": invalid,
            "log1p_sum": log_sum,
            "log_sum_minus_additive_sum": None if log_sum is None else log_sum - total,
            "status": "unavailable" if invalid else "complete",
        },
    }


def _sign(value):
    return "positive" if value > 0 else "negative" if value < 0 else "zero"


def diagnose(csv_bytes: bytes, costs: dict, *, start: str, end: str) -> dict:
    """Compare one complete registered saved window under two definitions.

    Input units are legacy daily PnL per target notional, not demonstrated
    investable simple returns. Compounding/log1p are convention indices only.
    No capital denominator or trading eligibility is inferred.
    """
    first, stop = _day(start), _day(end)
    if stop <= first:
        raise ValueError("registered window must be nonempty")
    if costs.get("window") != [start, end]:
        raise ValueError("costs window differs from registered window")
    if costs.get("annualization") != "sqrt(252)":
        raise ValueError("saved annualization differs from registered sqrt(252)")
    params = costs["cost_parameters"]
    if _finite(params["target_notional_per_leg"], "target notional") != 1.0:
        raise ValueError("legacy diagnostic requires unit target notional")
    rf = _finite(params["rf_daily"], "rf_daily")
    margin = _finite(params["margin_fraction_of_perp_notional"], "margin fraction")
    if rf < 0 or not 0 <= margin <= 1:
        raise ValueError("invalid opportunity cost parameters")
    drag = rf * margin
    saved_sr = _finite(costs["stressed_blended_sr"], "saved SR")
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8")))
    if reader.fieldnames != ["date", *SERIES]:
        raise ValueError("CSV schema must be date,btc,eth,sleeve")
    observations = {name: [] for name in SERIES}
    expected = first
    for row in reader:
        if set(row) != {"date", *SERIES} or any(value is None for value in row.values()):
            raise ValueError("malformed CSV row")
        if _day(row["date"]) != expected or expected >= stop:
            raise ValueError("dates must be unique ordered complete registered daily window")
        values = {name: _finite(row[name], name) for name in SERIES}
        if not math.isclose(values["sleeve"], 0.5 * values["btc"] + 0.5 * values["eth"],
                            rel_tol=1e-12, abs_tol=1e-14):
            raise ValueError("sleeve differs from fixed 50/50 blend")
        for name, value in values.items():
            observations[name].append(value)
        expected += timedelta(days=1)
    if expected != stop:
        raise ValueError("dates must cover complete registered daily window")
    results = {}
    for name, values in observations.items():
        stressed = _stats(values)
        addback = _stats([_finite(value + drag, "addback") for value in values])
        before, after = _sign(stressed["sum"]), _sign(addback["sum"])
        results[name] = {"stressed": stressed, "opportunity_cost_addback": addback,
                         "additive_sum_sign": {"stressed": before, "addback": after,
                                               "changed": before != after}}
    actual_sr = results["sleeve"]["stressed"]["sr_sqrt252"]
    delta = None if actual_sr is None else actual_sr - saved_sr
    if delta is not None and abs(delta) > SR_TOLERANCE:
        raise ValueError(f"saved blended SR disagreement exceeds {SR_TOLERANCE}: {delta}")
    unavailable = {"status": "unavailable", "reason":
                   "Legacy notional accounting lacks signed cash/base wallets, capital/reserves and market benchmark reconstruction."}
    return {
        "window": [start, end], "series_denominator": list(SERIES),
        "interpretation": "Exploratory saved-series definition diagnostic only; no significance, selection or adoption claim.",
        "units": "legacy PnL per unit target notional; compounded index is not cash wealth",
        "inherited_defects": ["Historical missing price differences were zero-filled.",
                              "Funding expected-event completeness remains unverified.",
                              "Short-equity drift proxy is not an explicit quantity book."],
        "daily_opportunity_cost_addback": drag, "series": results,
        "saved_blended_sr_check": {"saved": saved_sr, "recomputed": actual_sr,
                                   "difference": delta, "absolute_tolerance": SR_TOLERANCE,
                                   "agrees": None if delta is None else abs(delta) <= SR_TOLERANCE},
        "cashflow_profit": dict(unavailable), "full_capital_returns": dict(unavailable),
        "market_beta": dict(unavailable),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Full committed execution HEAD")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    with ResearchRun.start(root=root, registration=REGISTRATION,
                           experiment=EXPERIMENT, source=args.source) as run:
        outputs, cells = {}, []
        for name, (start, end) in WINDOWS.items():
            # Read/hash failures are lifecycle failures, not semantic unavailability.
            raw_series = run.read_input(f"{name}_series")
            raw_costs = run.read_input(f"{name}_costs")
            try:
                result = diagnose(raw_series, json.loads(raw_costs), start=start, end=end)
                if result["saved_blended_sr_check"]["agrees"] is not True:
                    raise ValueError("saved blended SR agreement is undefined")
            except (ValueError, KeyError, TypeError, OverflowError) as exc:
                outputs[name] = {"status": "unavailable", "reason": str(exc),
                                 "series_denominator": list(SERIES)}
                cells.extend({"id": f"{name}-{symbol}", "status": "unavailable",
                              "reason": str(exc)} for symbol in SERIES)
            else:
                outputs[name] = result
                cells.extend({"id": f"{name}-{symbol}", "status": "complete",
                              "scope": "definition diagnostic only"} for symbol in SERIES)
        run.write_json("diagnostic.json", outputs)
        run.finish(cells)


if __name__ == "__main__":
    main()

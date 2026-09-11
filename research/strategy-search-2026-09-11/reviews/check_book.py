"""Reconstruct retained financial results only; no runner/book/statistics import.

No network, new strategy evaluation, parameter search or experiment writes.
Writes the independent review JSON from the already completed frozen cases.
"""
import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D, ROUND_FLOOR, localcontext
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from scipy.stats import norm, t

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "research_runs/carry-book-20260911"
SOURCE = "7d704ca97606eea4ab953c29d7587e7e8af517f1"
CASES = [(a, c, s) for a in ("BTC", "ETH") for c in (1000, 10000) for s in ("base", "stress")]
ERRORS = []


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def snapshot(path):
    return subprocess.check_output(["git", "show", f"{SOURCE}:{path}"], cwd=ROOT)


def close(label, actual, expected, tolerance=1e-8):
    assert actual is not None and math.isfinite(actual), label
    difference = abs(float(actual) - float(expected))
    assert math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=tolerance), (label, actual, str(expected), difference)
    ERRORS.append(difference)


def fields(label, actual, expected):
    for name, value in expected.items():
        close(label + "/" + name, actual[name], value)


def reconstruct(asset, capital, scenario, payloads, got, zero=False):
    spot, perp, mark = [payloads[asset.lower() + "-" + kind] for kind in ("spot", "perp", "mark")]
    events = payloads[asset.lower() + "-funding"]
    C = D(capital)
    multiplier = D(1 if scenario == "base" else 2)
    sf, ff, slip = D(".001") * multiplier, D(".0005") * multiplier, D(".0002") * multiplier
    raw_s0, raw_f0 = D(spot[0][1]), D(perp[0][1])
    s0, f0 = raw_s0 * (1 + slip), raw_f0 * (1 - slip)
    lot = D(".001") if asset == "BTC" else D(".01")
    q = (C * D(".4") / ((s0 * (1 + sf) + f0 * ff) * lot)).to_integral_value(rounding=ROUND_FLOOR) * lot
    reserve = C / 2
    spot_fee0, future_fee0 = q * s0 * sf, q * f0 * ff
    idle = C - reserve - q * s0 - spot_fee0 - future_fee0
    assert q > 0 and idle >= C / 10
    initial = {"quantity": q, "spot_quantity": q, "perp_quantity": -q, "assumed_common_lot": lot,
               "spot_entry_price": s0, "perp_entry_price": f0, "spot_purchase_principal": q*s0,
               "spot_entry_fee": spot_fee0, "perp_entry_fee": future_fee0, "futures_reserve": reserve, "idle_cash": idle}
    fields("initial", got["initial"], initial)
    fields("costs", got["costs"], {"spot_fee": sf, "perp_fee": ff, "slippage": slip})
    assert got["status"] == "conditional" and got["days"] == 91
    assert got["asset"] == asset and got["capital"] == capital and got["cost_scenario"] == scenario
    start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    start_ms = int(start.timestamp() * 1000)
    expected_stamps = [start_ms + i * 28800000 for i in range(273)]
    assert len(events) == 273
    day_events = [[] for _ in range(91)]
    excluded = []
    for event, expected in zip(events, expected_stamps):
        stamp = event["fundingTime"]
        assert type(stamp) is int and abs(stamp - expected) <= 5000
        assert event["symbol"] == asset + "USDT" and D(event["markPrice"]) > 0
        if expected == start_ms:
            excluded.append(stamp)
        else:
            rate = D(0) if zero else D(event["fundingRate"])
            day_events[(stamp - start_ms) // 86400000].append(q * D(event["markPrice"]) * rate)
    assert got["excluded_first_funding_timestamps"] == excluded and len(excluded) == 1
    assert sum(map(len, day_events)) == 272
    assert len(got["daily_trace"]) == 91
    wealth, buffers, cumulative, expected_rows = [], [], D(0), []
    for day, row in enumerate(got["daily_trace"]):
        assert row["date"] == (start + timedelta(days=day)).date().isoformat()
        prior = cumulative
        daily = sum(day_events[day], D(0))
        negative = sum((v for v in day_events[day] if v < 0), D(0))
        cumulative += daily
        S, F, M, H = D(spot[day][4]), D(perp[day][4]), D(mark[day][4]), D(mark[day][2])
        wallet = reserve + cumulative
        mtm = q * (f0 - M)
        nav = idle + wallet + mtm + q*S
        wallet_floor = reserve + prior + negative
        equity_floor = wallet_floor + q * (f0 - H)
        maintenance = D(".01") * q * H
        buffer = equity_floor - maintenance
        expected = {"spot_close": S, "perp_close": F, "mark_close": M, "mark_high": H,
                    "funding_cash": daily, "negative_funding_cash": negative, "cumulative_funding_cash": cumulative,
                    "futures_wallet": wallet, "short_mtm": mtm, "spot_value": q*S, "idle_cash": idle,
                    "pre_exit_nav": nav, "nav": nav, "margin_wallet_lower_bound": wallet_floor,
                    "margin_equity_lower_bound": equity_floor, "assumed_maintenance_requirement": maintenance,
                    "margin_buffer_lower_bound": buffer, "spot_quantity": q, "perp_quantity": -q,
                    "net_base_quantity": D(0), "net_market_notional": q*(S-M), "gross_market_notional": q*(S+M)}
        assert row["funding_event_count"] == len(day_events[day])
        expected_rows.append(expected)
        wealth.append(nav)
        buffers.append(buffer)
    se, fe = D(spot[-1][4]) * (1-slip), D(perp[-1][4]) * (1+slip)
    fee_s1, fee_f1 = q*se*sf, q*fe*ff
    final_futures = reserve + cumulative + q*(f0-fe) - fee_f1
    final_idle = idle + q*se - fee_s1
    cash = final_idle + final_futures
    profit = cash - C
    all_fees = spot_fee0 + future_fee0 + fee_s1 + fee_f1
    final = {"spot_exit_price": se, "perp_exit_price": fe, "spot_sale_proceeds": q*se,
             "spot_exit_fee": fee_s1, "perp_realized_price_pnl": q*(f0-fe), "perp_exit_fee": fee_f1,
             "cumulative_funding_cash": cumulative, "futures_cash_after_close": final_futures,
             "idle_cash": idle, "final_cash": cash, "cash_profit": profit, "terminal_spot_quantity": D(0),
             "terminal_perp_quantity": D(0), "spot_price_pnl": q*(se-s0), "all_fees": all_fees,
             "cash_profit_from_signed_components": q*(se-s0) + q*(f0-fe) + cumulative - all_fees,
             "cash_reconciliation_difference": D(0)}
    fields("terminal", got["final_ledger"], final)
    last = expected_rows[-1]
    fields("pre_exit_components", got["daily_trace"][-1]["pre_exit_components"], {
        name: last[name] for name in ("futures_wallet", "short_mtm", "spot_value", "idle_cash", "spot_quantity",
                                    "perp_quantity", "net_base_quantity", "net_market_notional", "gross_market_notional", "nav")})
    last.update(nav=cash, futures_wallet=final_futures, short_mtm=D(0), spot_value=D(0), idle_cash=final_idle,
                spot_quantity=D(0), perp_quantity=D(0), net_base_quantity=D(0), net_market_notional=D(0), gross_market_notional=D(0))
    wealth[-1] = cash
    simple, peak, maximum_drawdown, previous = [], C, D(0), C
    for row, expected, nav in zip(got["daily_trace"], expected_rows, wealth):
        fields("daily", row, expected)
        assert nav > 0 and previous > 0
        ret = nav / previous - 1
        close("daily simple return", row["full_capital_daily_return"], ret, 1e-12)
        simple.append(ret)
        previous = nav
        peak = max(peak, nav)
        maximum_drawdown = max(maximum_drawdown, (peak-nav)/peak)
    metrics = {"cash_profit": profit, "full_capital_return": profit/C,
               "annualized_simple_return_365": profit/C*D(365)/91, "max_drawdown": maximum_drawdown,
               "minimum_margin_buffer_lower_bound": min(buffers), "funding_cash": cumulative, "applied_funding_events": 272}
    fields("metrics", got["metrics"], metrics)
    assert got["metrics"]["margin_buffer_breach"] == any(v < 0 for v in buffers)
    convention = got["convention_diagnostic"]
    assert convention["status"] == "complete" and convention["all_days"] == convention["valid_simple_index_days"] == 91
    logs = (cash/C).ln()
    arithmetic = sum(simple)
    fields("convention", convention, {"log1p_sum": logs, "arithmetic_daily_simple_return_sum": arithmetic,
           "terminal_simple_return": profit/C, "log_sum_minus_arithmetic_daily_sum": logs-arithmetic,
           "arithmetic_daily_sum_minus_terminal_simple_return": arithmetic-profit/C,
           "log_sum_minus_actual_simple_total_return": logs-profit/C})
    stress_values = {}
    for name, factor in (("half", D(".5")), ("double", D(2))):
        sx, fx = raw_s0*factor*(1-slip), raw_f0*factor*(1+slip)
        fw = reserve + q*(f0-fx) - q*fx*ff
        total = idle + fw + q*sx - q*sx*sf
        high = max(D(mark[0][1]), D(mark[0][1])*factor)
        mb = reserve + q*(f0-high) - D(".01")*q*high
        values = {"spot_exit_price": sx, "perp_exit_price": fx, "spot_sale_proceeds": q*sx,
                  "spot_exit_fee": q*sx*sf, "perp_realized_price_pnl": q*(f0-fx), "perp_exit_fee": q*fx*ff,
                  "cumulative_funding_cash": 0, "futures_cash_after_close": fw, "idle_cash": idle,
                  "final_cash": total, "cash_profit": total-C, "terminal_spot_quantity": 0,
                  "terminal_perp_quantity": 0, "margin_buffer_lower_bound": mb, "quantity": q, "price_multiple": factor}
        fields("price stress", got["quantity_price_stresses"][name], values)
        stress_values[name] = values
    raw_basis = q*((D(spot[-1][4])-raw_s0) - (D(perp[-1][4])-raw_f0))
    slippage_cash = q*slip*(raw_s0+raw_f0+D(spot[-1][4])+D(perp[-1][4]))
    close("independent basis/fee/funding decomposition", float(profit), raw_basis + cumulative - slippage_cash - all_fees)
    return {"nav": np.asarray([float(v) for v in wealth]), "returns": np.asarray([float(v) for v in simple]),
            "metrics": metrics, "stresses": stress_values,
            "forensic": {"quantity": float(q), "cash_profit_usdt": float(profit), "funding_cash_usdt": float(cumulative),
                         "raw_entry_exit_basis_price_pnl_usdt": float(raw_basis), "slippage_cash_usdt": float(slippage_cash),
                         "commission_cash_usdt": float(all_fees), "full_capital_return": float(profit/C)}}


def main():
    claim_raw = (RUN / "claim.json").read_bytes()
    receipt_raw = (RUN / "complete.json").read_bytes()
    claim, receipt = json.loads(claim_raw), json.loads(receipt_raw)
    assert claim["source"] == claim["design_source"] == receipt["source"] == SOURCE
    assert sha(claim_raw) == receipt["claim_sha256"]
    registration_raw = snapshot(claim["registration"])
    assert sha(registration_raw) == claim["registration_sha256"] == receipt["registration_sha256"]
    registration = json.loads(registration_raw)
    gate = registration["experiments"]["carry-book-20260911"]
    assert gate == claim["experiment"] and gate["parent"] == "carry-inputs-20260911"
    assert gate["stage"] == "development" and gate["reuse"] == "exploratory" and gate["selection"] is None
    members = dict(gate["source_files"])
    members[gate["charter"]["path"]] = gate["charter"]["sha256"]
    members.update({"tradingagents/research/"+k: v for k, v in gate["runtime_hashes"].items()})
    for path, digest in members.items():
        assert sha(snapshot(path)) == digest
    inputs = {}
    for name, spec in gate["inputs"].items():
        raw = (ROOT / spec["path"]).read_bytes()
        assert sha(raw) == sha(snapshot(spec["path"])) == spec["sha256"]
        inputs[name] = json.loads(raw)
    output_dir = RUN / "outputs"
    assert set(p.name for p in output_dir.iterdir()) == set(gate["outputs"]) == {"books.json", "summary.json"}
    for name, digest in receipt["output_sha256"].items():
        assert sha((output_dir/name).read_bytes()) == digest
    books = json.loads((output_dir/"books.json").read_bytes())
    summary = json.loads((output_dir/"summary.json").read_bytes())
    ids = [f"{a.lower()}-{c}-{s}" for a,c,s in CASES]
    all_ids = [name+suffix for name in ids for suffix in ("", "-zero-funding")]
    assert gate["cells"] == [r["id"] for r in receipt["cells"]] == all_ids
    assert len(set(all_ids)) == receipt["cell_count"] == 16 and receipt["unavailable_count"] == 0
    assert all(c["status"] == "complete" for c in receipt["cells"])
    assert set(books["primary_books"]) == set(books["zero_funding_counterfactual_books"]) == set(ids)
    assert [r["id"] for r in summary["cases"]] == ids
    assert summary["primary_count"] == summary["counterfactual_count"] == 8 and summary["validated_strategies"] == 0
    payloads = {}
    for response in inputs["capture"]["requests"]:
        raw = base64.b64decode(response["body_base64"], validate=True)
        assert len(raw) == response["body_bytes"] and sha(raw) == response["body_sha256"]
        payloads[response["id"]] = json.loads(raw)
    primary, zero, forensic = {}, {}, {}
    with localcontext() as context:
        context.prec = 50
        for identifier, (asset, capital, scenario) in zip(ids, CASES):
            primary[identifier] = reconstruct(asset, capital, scenario, payloads, books["primary_books"][identifier])
            zero[identifier] = reconstruct(asset, capital, scenario, payloads, books["zero_funding_counterfactual_books"][identifier], zero=True)
            close("funding-off identity", primary[identifier]["forensic"]["cash_profit_usdt"]-zero[identifier]["forensic"]["cash_profit_usdt"], primary[identifier]["metrics"]["funding_cash"])
            forensic[identifier] = primary[identifier]["forensic"]
            forensic[identifier]["zero_funding_cash_profit_usdt"] = zero[identifier]["forensic"]["cash_profit_usdt"]
    changes = np.asarray([np.diff(np.r_[c, primary[name]["nav"]])/c for name, (_,c,_) in zip(ids,CASES)])
    rng = np.random.default_rng(20260911)
    starts = rng.integers(0, 91, size=(2000,13))
    # Build each resample explicitly, independently of the runner's tensor indexing.
    boot = np.empty((8,2000))
    for draw in range(2000):
        sample = np.concatenate([np.arange(start,start+7)%91 for start in starts[draw]])
        boot[:,draw] = np.sum(changes[:,sample],axis=1)/91*365
    benchmarks = []
    for asset in ("btc","eth"):
        rows = payloads[asset+"-spot"]
        closes = np.asarray([float(r[4]) for r in rows])
        previous = np.r_[float(rows[0][1]),closes[:-1]]
        benchmarks.append(closes/previous-1)
    X = np.column_stack((np.ones(91),*benchmarks))
    assert np.linalg.matrix_rank(X) == 3
    bread = np.linalg.inv(X.T@X)
    for i,(name,case,item) in enumerate(zip(ids,CASES,summary["cases"])):
        low,high = np.quantile(boot[i], [.003125,.996875])
        se = np.std(boot[i],ddof=1)
        uncertainty = {"annualized_point": changes[i].sum()/91*365, "annualized_lower": low,
                       "annualized_upper": high, "bootstrap_standard_error": se,
                       "approximate_80pct_mde_annualized": (norm.ppf(.996875)+norm.ppf(.8))*se}
        fields("bootstrap",item["uncertainty"],uncertainty)
        for key,value in {"seed":20260911,"draws":2000,"block_days":7,"observations":91,"approximate_blocks":13}.items():
            assert item["uncertainty"][key] == value
        y = primary[name]["returns"]
        coefficients = np.linalg.solve(X.T@X,X.T@y)
        residual = y-X@coefficients
        scores = X*residual[:,None]
        meat = scores.T@scores
        for lag in range(1,8):
            cross = scores[lag:].T@scores[:-lag]
            meat += (1-lag/8)*(cross+cross.T)
        covariance = bread@meat@bread
        widths = t.ppf(.9875,88)*np.sqrt(np.diag(covariance))
        intervals = np.column_stack((coefficients-widths,coefficients+widths))
        exposure = item["market_exposure"]
        assert exposure["status"] == "complete" and exposure["observations"] == 91 and exposure["hac_lags"] == 7
        fields("OLS coefficients",exposure,{"intercept":coefficients[0],"btc_beta":coefficients[1],"eth_beta":coefficients[2]})
        for j,asset in enumerate(("btc","eth"),start=1):
            for actual,expected in zip(exposure[asset+"_interval"],intervals[j]):
                close("independent HAC interval",actual,expected,1e-10)
        metrics = primary[name]["metrics"]
        fields("summarymetrics",item["metrics"],metrics)
        close("zero counterfactual summary",item["zero_funding_cash_profit"],zero[name]["metrics"]["cash_profit"])
        fields("cashbenchmarks",item["cash_benchmarks"],{str(rate):case[1]*rate*91/365 for rate in (0,.03,.05)})
        beta_ok = all(abs(coefficients[j])<=.1 and intervals[j,0]>=-.2 and intervals[j,1]<=.2 for j in (1,2))
        double = primary[name]["stresses"]["double"]
        screens = {"annualized_cash_at_least_3pct":metrics["annualized_simple_return_365"]>=D(".03"),
                   "exploratory_simultaneous_cash_lower_positive":low>0,"beta_point_and_interval_screen":beta_ok,
                   "max_drawdown_at_most_10pct":metrics["max_drawdown"]<=D(".1"),
                   "conditional_daily_margin_buffer_nonnegative":metrics["minimum_margin_buffer_lower_bound"]>=0,
                   "base_delta_at_most_1pct_nav":True,
                   "doubling_stress_wallet_and_buffer_nonnegative":double["futures_cash_after_close"]>=0 and double["margin_buffer_lower_bound"]>=0,
                   "cash_components_reconcile":True}
        assert item["necessary_conditional_screens"] == screens
        assert item["all_necessary_conditional_screens_pass"] == all(screens.values())
        assert item["adoption_or_execution_validated"] is False
        forensic[name].update(annualized_point=float(uncertainty["annualized_point"]),
                              annualized_lower=float(low),annualized_upper=float(high),
                              approximate_80pct_mde_annualized=float(uncertainty["approximate_80pct_mde_annualized"]),
                              failed_screens=[k for k,v in screens.items() if not v],
                              max_drawdown=float(metrics["max_drawdown"]),btc_beta=float(coefficients[1]),eth_beta=float(coefficients[2]))
    report = {"status":"pass_independent_reconstruction","source":SOURCE,"reviewer":"independent_review",
              "checker_sha256":sha(Path(__file__).read_bytes()),"claim_sha256":sha(claim_raw),"receipt_sha256":sha(receipt_raw),
              "output_sha256":receipt["output_sha256"],"primary_books":8,"counterfactual_books":8,"complete_cells":16,"unavailable_cells":0,
              "daily_nav_snapshots_verified":1456,"numeric_comparisons":len(ERRORS),"maximum_absolute_numeric_difference":max(ERRORS),
              "method":"Independent 50-digit Decimal signed cash/quantity and wallet reconstruction from raw captured bodies. Explicit paired resampling; OLS normal equations and Bartlett HAC sandwich reconstructed without statsmodels or any book/runner/statistics import. No new economic configuration, financial experiment or network.",
              "cases":forensic,"material_implementation_findings":[],
              "interpretation":"All eight frozen conditional cash books lost money after modeled fees/slippage and entry/exit basis effects. Only cash relevance and positive exploratory lower-bound screens fail; other conditional screens pass. Insufficient evidence for useful positive returns, not family-wide rejection.",
              "not_tested":["Actual executable prices or account fees/fee assets/lots", "Historical calendar/maintenance/product applicability", "Continuous margin or liquidation path", "Prospective return confidence or nominal bootstrap coverage", "Genuine fresh confirmation or historical search multiplicity", "External backup or pre-result push timing", "Runtime concurrency/crash faults"],
              "next_action":"Preserve original holdout NO-GO and close this fixed book/quarter question under its failed cash screens. Three new carry investigations consumed; switch to separately registered dated-archive admission, without new carry parameter search. Future reopening needs documented information value and new evidence."}
    with Path(__file__).with_name("book-review.json").open("w") as handle:
        json.dump(report,handle,indent=2,allow_nan=False);handle.write("\n")
    print(json.dumps({k:report[k] for k in ("status","complete_cells","daily_nav_snapshots_verified","numeric_comparisons","maximum_absolute_numeric_difference")}))


if __name__ == "__main__":
    main()

"""Charter 1b replacement run: cache-only frozen weeks, input verification, corrected evaluation tail, verdict
by code and the lifecycle run end to end. Synthetic fixtures only; no market data, no network."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tradingagents.agents_v2 import charter1b as c1b  # noqa: E402
from tradingagents.agents_v2.graph import config_sha  # noqa: E402
from tradingagents.agents_v2.runner import run_week  # noqa: E402
from tradingagents.dossier.or_client import ORError, SpendCapError  # noqa: E402
from test_agents_v2 import DOSSIER, StubClient  # noqa: E402

WEEKS = ["2024-03-01", "2024-03-08", "2024-03-15", "2024-03-22", "2024-03-29"]      # Fridays, oldest first
FROZEN = WEEKS[2:]
N = 12
SYMS = [f"S{i:02d}USDT" for i in range(N)]


class CountingClient(StubClient):
    """Stub with the spend counters the run script reads; optional hard cap and failure mode."""
    def __init__(self, *args, cap_calls=None, fail=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls, self.spent_usd, self.cap_calls, self.fail = 0, 0.0, cap_calls, fail

    def call(self, *args, **kwargs):
        if self.cap_calls is not None and self.calls >= self.cap_calls:
            raise SpendCapError("spend cap reached")
        if self.fail:
            raise ORError("provider unavailable")
        self.calls += 1
        self.spent_usd += 0.001
        return super().call(*args, **kwargs)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _dossier(i: int, day: str) -> dict:
    alias = "Asset_" + "AB"[i % 2]
    return {"alias": alias, "sha256": f"sha-{day}-{i}", "text": DOSSIER.replace("Asset_A", alias),
            "numeric": {"vol_ewma20_ann_pct": 50.0 + i}, "quant_forecast": {"pred_rank_pct": i / N},
            "items": [{"id": "t1"}] if i % 3 else []}


def _repo(root: Path, interrupted: bool = True) -> dict:
    """Synthetic checkout: dossiers, kline and funding stores, panel inputs, a call cache with the three newest
    weeks completed and (optionally) a partly cached fourth week, and a committed registration."""
    from llm_v2c1b_manifest import build_cache_manifest
    from tradingagents.research import runtime_hashes
    rng = np.random.default_rng(7)
    _git(root, "init", "-q")
    files, by_day = {}, {}
    for day in WEEKS:
        for i, sym in enumerate(SYMS):
            path = root / "dossiers" / day / f"{sym}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            d = _dossier(i, day)
            path.write_text(json.dumps(d))
            files[f"dossiers/{day}/{sym}.json"] = _sha(path)
            by_day.setdefault(day, {})[sym] = d
    (root / "manifest.json").write_text(json.dumps({"builder_version": "test", "files": files}))
    (root / "agent_config.json").write_text(json.dumps({"config_sha": config_sha()}))
    days = pd.date_range("2024-02-20", "2024-04-20", freq="D", tz="UTC")
    stamps = pd.date_range("2024-02-20", "2024-04-20", freq="8h", tz="UTC")
    for store in ("klines", "funding"):
        (root / store).mkdir()
    for sym in SYMS:
        pd.DataFrame({"close": 100 * np.exp(np.cumsum(rng.normal(0, 0.03, len(days))))}, index=days).to_parquet(root / "klines" / f"{sym}.parquet")
        pd.DataFrame({"fundingTime": stamps, "fundingRate": 1e-4}).to_parquet(root / "funding" / f"{sym}.parquet")
    for store in ("klines", "funding"):
        digest = {f"{store}/{p.name}": _sha(p) for p in sorted((root / store).glob("*.parquet"))}
        (root / f"{store}_digest.json").write_text(json.dumps(digest))
    keys = [(pd.Timestamp(day, tz="UTC"), sym) for day in WEEKS for sym in SYMS]
    frame = pd.DataFrame(keys, columns=["date", "symbol"])
    frame.assign(vol_ewma20=rng.uniform(0.3, 1.5, len(frame)), ret_4w=rng.normal(0, 0.2, len(frame)),
                 dvol_30d=rng.uniform(1, 100, len(frame)), size_rank=rng.integers(1, 200, len(frame))).to_parquet(root / "cards.parquet")
    frame.assign(pred_rank_pct=rng.uniform(0, 1, len(frame))).to_parquet(root / "quant.parquet")
    flags = frame.iloc[::2].rename(columns={"date": "friday"})
    flags.assign(identified=rng.uniform(size=len(flags)) > 0.5).to_parquet(root / "flags.parquet")
    client = CountingClient(0.7, 0.6, p_nd=0.45)
    for day in FROZEN:
        run_week(pd.Timestamp(day, tz="UTC"), by_day[day], client, runs_dir=root / "runs")
    if interrupted:                                             # a week with cached assets and no stored book
        run_week(pd.Timestamp(WEEKS[1], tz="UTC"), by_day[WEEKS[1]], client, runs_dir=root / "runs")
        (root / "runs" / WEEKS[1] / "_portfolio.json").unlink()
        for sym in SYMS[:4]:
            (root / "runs" / WEEKS[1] / f"{sym}.json").unlink()
    cache = build_cache_manifest(root, "runs", by_day, config_sha(), tally=1.0, unsaved_allowance=0.35, overshoot_allowance=0.15)
    (root / "cache_manifest.json").write_text(json.dumps(cache))
    (root / "charter.md").write_text("synthetic charter\n")
    (root / "engine.py").write_text("# synthetic\n")
    inputs = {"dossier_manifest": "manifest.json", "agent_config": "agent_config.json", "cache_manifest": "cache_manifest.json",
              "cards": "cards.parquet", "quant_forecasts": "quant.parquet", "reid_flags": "flags.parquet",
              "klines_digest": "klines_digest.json", "funding_digest": "funding_digest.json"}
    from llm_v2c1b_run import CELLS, OUTPUTS
    spec = {"schema_version": 1, "program_id": "synthetic-c1b",
            "families": {"fam": {"mechanism_id": "synthetic-mechanism", "attempt_budget": 3, "prior_attempts": 0,
                                 "history_reference": "synthetic"}},
            "datasets": {"sample": {"identity": "synthetic-sample", "history_reference": "synthetic", "exposures": []}},
            "experiments": {"c1b": {
                "family": "fam", "parent": None, "question": "synthetic", "charter": {"path": "charter.md", "sha256": _sha(root / "charter.md")},
                "stage": "development", "reuse": "exploratory", "selection": None,
                "source_files": {"engine.py": _sha(root / "engine.py")}, "runtime_hashes": runtime_hashes(),
                "windows": [{"dataset": "sample", "start": "2024-01-01T00:00:00Z", "end": "2024-05-01T00:00:00Z", "availability": "existing"}],
                "inputs": {n: {"path": p, "sha256": _sha(root / p), "dataset": "sample"} for n, p in inputs.items()},
                "cells": list(CELLS), "outputs": list(OUTPUTS)}}}
    (root / "registration.json").write_text(json.dumps(spec))
    _git(root, "add", "registration.json", "charter.md", "engine.py")
    _git(root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "synthetic registration")
    return {"by_day": by_day, "cache": cache, "frozen_calls": client.calls}


def _main(root, *extra, client=None):
    from llm_v2c1b_run import main
    return main(["--registration", "registration.json", "--experiment", "c1b", *extra], root=root, client=client)


def _output(root, name):
    return json.loads((root / "research_runs" / "c1b" / "outputs" / name).read_text())


# ---------------------------------------------------------------- serialization
def test_json_safe_plain_types_and_nulls():
    ts = pd.Timestamp("2024-03-01", tz="UTC")
    value = {"a": np.float64("nan"), "b": [np.int64(3), np.bool_(True), float("inf")], ts: {"x": pd.NaT, "y": np.array([1.5, np.nan])},
             "s": {"q"}, 5: None}
    out = c1b.json_safe(value)
    assert out == {"a": None, "b": [3, True, None], ts.isoformat(): {"x": None, "y": [1.5, None]}, "s": ["q"], "5": None}
    json.dumps(out, sort_keys=True, allow_nan=False)
    with pytest.raises(TypeError):
        c1b.json_safe({"a": object()})


# ---------------------------------------------------------------- cache and stores
def test_cached_week_equals_runner_output_and_detects_tampering(tmp_path):
    day, d = WEEKS[-1], {sym: _dossier(i, WEEKS[-1]) for i, sym in enumerate(SYMS)}
    live = run_week(pd.Timestamp(day, tz="UTC"), d, CountingClient(0.7, 0.6, p_nd=0.45), n_debate=3, runs_dir=tmp_path)
    cached = c1b.load_cached_week(day, d, tmp_path, config_sha())
    assert cached["portfolio"]["rule_weights"] == live["portfolio"]["rule_weights"]
    assert cached["results"] == json.loads(json.dumps(live["results"], default=str))
    rows = c1b.asset_rows(day, cached["results"], d)
    assert len(rows) == N and sum(r["debated"] for r in rows) == 3 and {r["n_items"] for r in rows} == {0, 1}
    assert all(r["primary_provider_share"] == 0.0 for r in rows)             # stub provider is not the primary one
    target = tmp_path / day / f"{SYMS[0]}.json"
    original = target.read_text()
    r = json.loads(original)
    r["p_outperform"] = r["p_hybrid"] = 0.99                                  # forecast edited after the book was stored
    target.write_text(json.dumps(r))
    with pytest.raises(c1b.CacheError, match="differs from the book recomputed"):
        c1b.load_cached_week(day, d, tmp_path, config_sha())
    target.write_text(original)
    with pytest.raises(c1b.CacheError, match="another config"):
        c1b.load_cached_week(day, d, tmp_path, "0" * 64)
    with pytest.raises(c1b.CacheError, match="another config or dossier"):
        c1b.load_cached_week(day, {**d, SYMS[1]: {**d[SYMS[1]], "sha256": "other"}}, tmp_path, config_sha())
    target.unlink()
    with pytest.raises(c1b.CacheError, match="no cached result"):
        c1b.load_cached_week(day, d, tmp_path, config_sha())


def test_verify_store_requires_exact_registered_set(tmp_path):
    (tmp_path / "store").mkdir()
    for name in ("A", "B"):
        pd.DataFrame({"x": [1.0]}).to_parquet(tmp_path / "store" / f"{name}.parquet")
    digest = {f"store/{name}.parquet": _sha(tmp_path / "store" / f"{name}.parquet") for name in ("A", "B")}
    assert c1b.verify_store(tmp_path, digest, "store") == tmp_path / "store"
    pd.DataFrame({"x": [2.0]}).to_parquet(tmp_path / "store" / "C.parquet")
    with pytest.raises(c1b.CacheError, match="registered set"):
        c1b.verify_store(tmp_path, digest, "store")
    (tmp_path / "store" / "C.parquet").unlink()
    pd.DataFrame({"x": [3.0]}).to_parquet(tmp_path / "store" / "A.parquet")
    with pytest.raises(c1b.CacheError, match="changed since freeze"):
        c1b.verify_store(tmp_path, digest, "store")


def test_verify_cache_pins_every_cached_file(tmp_path):
    ctx = _repo(tmp_path)
    cache, by_day = ctx["cache"], ctx["by_day"]
    assert cache["complete_weeks"] == FROZEN and cache["interrupted_week"] == WEEKS[1]
    assert len(cache["files"]) == 3 * (N + 1) and len(cache["pinned_other"]) == N - 4
    assert c1b.verify_cache(tmp_path / "runs", cache, by_day, config_sha()) == set(FROZEN)
    stray = tmp_path / "runs" / WEEKS[0] / f"{SYMS[0]}.json"
    stray.parent.mkdir()
    stray.write_text("{}")
    with pytest.raises(c1b.CacheError, match="unregistered cached file"):
        c1b.verify_cache(tmp_path / "runs", cache, by_day, config_sha())
    stray.unlink()
    with pytest.raises(c1b.CacheError, match="newest contiguous block"):
        c1b.verify_cache(tmp_path / "runs", {**cache, "complete_weeks": [WEEKS[2], WEEKS[4]]}, by_day, config_sha())
    pinned = tmp_path / "runs" / WEEKS[1] / f"{SYMS[5]}.json"
    pinned.write_text(pinned.read_text() + " ")
    with pytest.raises(c1b.CacheError, match="differs from the registered cache"):
        c1b.verify_cache(tmp_path / "runs", cache, by_day, config_sha())


# ---------------------------------------------------------------- evaluation tail and verdict
def _synthetic_run(signal: float, weeks: int = 60, n: int = 30, seed: int = 0):
    """Forecast rows, books, returns, funding and panel inputs with a latent signal of the given strength."""
    rng = np.random.default_rng(seed)
    dates = [pd.Timestamp("2023-06-02", tz="UTC") + pd.Timedelta(weeks=w) for w in range(weeks)]
    syms = [f"S{i}" for i in range(n)]
    rows, fwd, fund, cards, quant, flags, book = [], [], [], [], [], [], {}
    for d in dates:
        latent = rng.normal(size=n)
        p_judge = np.clip(0.5 + 0.1 * latent + 0.02 * rng.normal(size=n), 0.02, 0.98)
        p_quant = rng.uniform(0, 1, n)
        ret = 0.04 * signal * latent + 0.05 * rng.normal(size=n)
        w = (p_judge - p_judge.mean())
        w = w / np.abs(w).sum()
        book[d] = dict(zip(syms, w.tolist()))
        for i, s in enumerate(syms):
            rows.append({"date": d.strftime("%Y-%m-%d"), "symbol": s, "p_outperform": p_judge[i], "p_judge": p_judge[i], "p_hybrid": p_judge[i],
                         "p_judge_nd": p_judge[i], "p_hybrid_nd": p_judge[i], "p_judge_debate": None, "p_analyst_mean": p_judge[i],
                         "weight_on_quant": 0.2, "quant_rank_pct": p_quant[i], "confidence": 0.5, "abstain": False, "debated": False,
                         "debate_selected": False, "failed": False, "debate_failed": False, "cite_exist_mean": 1.0,
                         "number_grounded_mean": 0.9, "n_items": i % 3, "n_calls": 5, "primary_provider_share": 1.0 if i % 4 else 0.5})
            fwd.append((d, s, ret[i], False))
            fund.append((d, s, 0.0002, 21))
            cards.append((d, s, rng.uniform(0.3, 1.5), rng.normal(0, 0.2), rng.uniform(1, 100), int(rng.integers(1, 200))))
            quant.append((d, s, p_quant[i]))
            if i % 2 == 0:
                flags.append((d, s, bool(i % 4 == 0)))
    books = {name: book for name in c1b.BOOK_KEYS}
    return (rows, books, pd.DataFrame(fwd, columns=["date", "symbol", "fwd_ret", "delisted"]),
            pd.DataFrame(fund, columns=["date", "symbol", "funding_week", "n_settlements"]),
            pd.DataFrame(cards, columns=["date", "symbol", "vol_ewma20", "ret_4w", "dvol_30d", "size_rank"]),
            pd.DataFrame(quant, columns=["date", "symbol", "pred_rank_pct"]),
            pd.DataFrame(flags, columns=["friday", "symbol", "identified"]),
            {"completed": [d.strftime("%Y-%m-%d") for d in dates], "n_completed": weeks, "truncated_at": None})


def test_finalize_passes_planted_signal_and_fails_noise():
    out = c1b.finalize(*_synthetic_run(1.0), n_placebo=100, n_boot=200)
    for name, value in out.items():
        json.dumps(value, sort_keys=True, allow_nan=False)                       # the run helper's encoder accepts every output
    v = out["verdict.json"]
    assert v["verdict"] == "PASS" and v["forecast_gates_pass"] and v["portfolio_gates_evaluated"] and v["portfolio_gates_pass"]
    assert v["failed_gates"] == [] and v["descriptive_errors"] == [] and v["weeks"] == 60
    assert v["forecast_gates"]["subperiod_sign"]["years_present"] == 2 and v["forecast_gates"]["subperiod_sign"]["binding"]
    ev, pf = out["evaluation.json"], out["portfolio.json"]
    assert ev["panel"]["rows"] == 1800 and ev["panel"]["deployed_equals_hybrid"] and ev["identified_subsets"]["flagged_rows"] == 900
    assert ev["identified_subsets"]["all_flagged"]["columns"]["p_judge"]["n_identified"] == 480
    assert ev["identified_subsets"]["text_rows_only"]["columns"]["p_judge"]["n_identified"] < 480      # rows without text dropped
    assert ev["sensitivity"]["primary_provider_rows"]["rows"] == 1320 and ev["sensitivity"]["abstentions_excluded"]["rows"] == 1800
    assert pf["rule_twin"]["funded"] and pf["funding_coverage"] == 1.0 and not pf["rule_twin_no_funding"]["funded"]
    assert pf["rule_twin"]["sharpe"] == pytest.approx(pf["rule_twin_no_funding"]["sharpe"], abs=0.5)   # dollar-neutral book
    assert len(out["books.json"]["rule_twin"]["weekly"]) == 60 and len(out["forecasts.json"]["rows"]) == 1800
    null = c1b.finalize(*_synthetic_run(0.0, seed=1), n_placebo=100, n_boot=200)["verdict.json"]
    assert null["verdict"] == "FAIL" and not null["portfolio_gates_evaluated"] and null["portfolio_gates_pass"] is None
    assert all(g["pass"] is None and g["descriptive"] for g in null["portfolio_gates"].values())
    assert "hybrid_ic_nw_t" in null["failed_gates"] and not any(k.startswith("placebo") for k in null["failed_gates"])


def test_verdict_rules_on_boundaries_and_missing_statistics():
    def evaluation(ic_t=2.0, skill=0.01, t_llm=2.0, sub=True):
        return {"gates": {"hybrid_ic": {"nw_t": ic_t}, "hybrid_brier_recalibrated": {"skill": skill, "weeks": 9},
                          "encompassing_llm_vs_quant": {"t_llm": t_llm},
                          "subperiods": {"mean_ic_by_year": {"2023": 0.01, "2024": 0.02}, "years_present": 2, "binding": True, "pass": sub}},
                "weeks": {"n_completed": 61}, "extra": {"broken": {"rows": 3, "error": "ValueError: x"}}}

    def portfolio(sr=0.8, p_date=0.05, p_asset=0.05):
        return {"rule_twin": {"sharpe": sr, "p_date_shuffle": p_date, "p_asset_shuffle": p_asset, "psr_vs_zero": 0.9}}

    v = c1b.build_verdict(evaluation(), portfolio())
    assert v["verdict"] == "PASS" and v["descriptive_errors"] == ["extra/broken"]            # thresholds are inclusive where registered so
    assert c1b.build_verdict(evaluation(skill=0.0), portfolio())["failed_gates"] == ["hybrid_brier_skill_recalibrated"]   # strict >
    assert c1b.build_verdict(evaluation(ic_t=1.999), portfolio())["verdict"] == "FAIL"
    assert c1b.build_verdict(evaluation(t_llm=None), portfolio())["failed_gates"] == ["encompassing_llm_nw_t"]
    assert c1b.build_verdict(evaluation(ic_t=float("nan")), portfolio())["failed_gates"] == ["hybrid_ic_nw_t"]
    assert c1b.build_verdict(evaluation(sub=False), portfolio())["failed_gates"] == ["subperiod_sign"]
    v = c1b.build_verdict(evaluation(), portfolio(sr=0.79))
    assert v["verdict"] == "FAIL" and v["forecast_gates_pass"] and v["failed_gates"] == ["net_sharpe"]
    v = c1b.build_verdict(evaluation(), portfolio(p_asset=0.051))
    assert v["failed_gates"] == ["placebo_asset_shuffle_p"] and v["deflated_sharpe_trial_count_1"]["value"] == 0.9
    assert c1b.build_verdict(evaluation(), portfolio(sr=None))["failed_gates"] == ["net_sharpe"]


# ---------------------------------------------------------------- lifecycle run
def test_lifecycle_run_reuses_frozen_weeks_and_runs_older_weeks(tmp_path):
    from tradingagents.research.verify import verify_run
    ctx = _repo(tmp_path)
    client = CountingClient(0.7, 0.6, p_nd=0.45)
    assert _main(tmp_path, "--cost-cap", "8.5", client=client) == 0
    directory = tmp_path / "research_runs" / "c1b"
    assert (directory / "complete.json").is_file() and not (directory / "failed.json").exists()
    assert verify_run(directory)["status"] == "complete"
    assert sorted(p.name for p in (directory / "outputs").iterdir()) == sorted(
        ["forecasts.json", "evaluation.json", "portfolio.json", "books.json", "cost.json", "verdict.json"])
    cost, verdict, ev = _output(tmp_path, "cost.json"), _output(tmp_path, "verdict.json"), _output(tmp_path, "evaluation.json")
    assert cost["weeks_completed"] == 5 and cost["weeks_frozen"] == 3 and sorted(cost["new_weeks"]) == WEEKS[:2]
    assert cost["calls"] == client.calls and cost["truncated_at"] is None
    assert 0 < cost["new_weeks"][WEEKS[1]]["calls"] < cost["new_weeks"][WEEKS[0]]["calls"]      # interrupted week resumed from cache
    assert cost["new_weeks"][WEEKS[0]]["calls"] == ctx["frozen_calls"] // 4                    # a full week costs what a frozen one did
    assert cost["cumulative_recorded_spend_usd"] == pytest.approx(cost["attempt1"]["recorded_spend_usd"] + client.spent_usd)
    assert ev["weeks"]["n_completed"] == 5 and ev["weeks"]["n_frozen"] == 3 and ev["weeks"]["n_new"] == 2
    assert len(_output(tmp_path, "forecasts.json")["rows"]) == 5 * N
    assert verdict["verdict"] == "FAIL" and "hybrid_brier_skill_recalibrated" in verdict["failed_gates"]   # too few weeks to recalibrate
    assert _output(tmp_path, "portfolio.json")["rule_twin"]["weeks"] == 5
    with pytest.raises(c1b.CacheError, match="unregistered cached file"):          # the cache has grown past the registered state
        _main(tmp_path, "--cost-cap", "8.5", client=client)


def test_lifecycle_run_without_new_weeks_makes_no_call(tmp_path):
    _repo(tmp_path)
    assert _main(tmp_path, "--cost-cap", "0", "--no-new-weeks") == 0
    cost, ev = _output(tmp_path, "cost.json"), _output(tmp_path, "evaluation.json")
    assert cost["calls"] == 0 and cost["spent_usd"] == 0.0 and cost["weeks_completed"] == 3 and cost["new_weeks"] == {}
    assert cost["truncated_at"]["week"] == WEEKS[1] and ev["weeks"]["completed"] == FROZEN
    assert (tmp_path / "research_runs" / "c1b" / "complete.json").is_file()
    with pytest.raises(ValueError, match="repeat run prohibited"):
        _main(tmp_path, "--cost-cap", "0", "--no-new-weeks")


def test_spend_cap_inside_a_week_excludes_it_and_still_publishes(tmp_path):
    _repo(tmp_path)
    client = CountingClient(0.7, 0.6, p_nd=0.45, cap_calls=30)                   # reached inside the first older week
    assert _main(tmp_path, "--cost-cap", "8.5", client=client) == 0
    cost = _output(tmp_path, "cost.json")
    assert cost["weeks_completed"] == 3 and cost["new_weeks"] == {} and cost["truncated_at"]["week"] == WEEKS[1]
    assert "spend cap" in cost["truncated_at"]["reason"] and (tmp_path / "research_runs" / "c1b" / "complete.json").is_file()


def test_week_with_too_many_failed_assets_is_excluded(tmp_path):
    _repo(tmp_path, interrupted=False)
    assert _main(tmp_path, "--cost-cap", "8.5", client=CountingClient(fail=True)) == 0
    cost = _output(tmp_path, "cost.json")
    assert cost["weeks_completed"] == 3 and cost["truncated_at"]["week"] == WEEKS[1] and "failed assets" in cost["truncated_at"]["reason"]


def test_defects_found_before_the_claim_do_not_consume_the_attempt(tmp_path):
    ctx = _repo(tmp_path)
    with pytest.raises(SystemExit, match="exceeds the registered remainder"):
        _main(tmp_path, "--cost-cap", str(ctx["cache"]["attempt1"]["process_cap_usd"] + 0.01), client=CountingClient())
    target = tmp_path / "runs" / FROZEN[0] / f"{SYMS[0]}.json"
    target.write_text(target.read_text() + "\n")
    with pytest.raises(c1b.CacheError):
        _main(tmp_path, "--cost-cap", "8.5", client=CountingClient())
    assert not (tmp_path / "research_runs").exists()

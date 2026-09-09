"""Synthetic-only caller regressions for the frozen NLST4 correction."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/audit_reevaluate_nlst4_2026_09_09.py"
DAY = 86400
BASE = int(pd.Timestamp("2021-01-01", tz="UTC").timestamp())


def module():
    assert SCRIPT.exists(), "registered NLST4 cache-only wrapper is missing"
    spec = importlib.util.spec_from_file_location("audit_nlst4", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Context:
    family_gate = {"settlement_fx_end_exclusive": "2025-04-15T09:20:00Z"}

    def __init__(self, root):
        self.hashes = {}
        self.output_dir = root / "output"
        self.frames = {}

    def track(self, path):
        path = Path(path)
        self.hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def read_market(self, path, start=None, end_exclusive=None):
        assert end_exclusive == self.family_gate["settlement_fx_end_exclusive"]
        return pd.read_parquet(self.track(path))

    def write_frame(self, name, frame):
        self.frames[name] = frame.copy()
        return self.output_dir / name

    def finish(self, payload, cells):
        for path, digest in self.hashes.items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
        self.finished = (payload, cells)
        return self.output_dir / "result.json"


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def fixture(tmp_path):
    source = tmp_path / "data"
    nl = source / "predlab/nlst"
    raw = nl / "dex_raw"
    raw.mkdir(parents=True)
    pairs = [f"0x{i:040x}" for i in range(1, 5)]
    buyer = "0x" + "b" * 40
    headers, entries = [], []
    for i, pair in enumerate(pairs):
        create = [0, DAY, 2 * DAY, 12 * DAY][i]
        entry = create + DAY + 10
        exit_block = [20 * DAY + 10, 21 * DAY + 10, 22 * DAY + 10, 20 * DAY + 10][i]
        meta = {"pair": pair, "block": create, "quarter": "2021Q1",
                "weth_is_0": True, "first_weth_reserve": 10,
                "token0": "weth", "token1": "token"}
        sync = lambda b: {"kind": "sync", "block": b, "r0": 10 * 10**18, "r1": 10000}
        swap = lambda b: {"kind": "swap", "block": b, "a0in": 10**18,
                          "a1in": 0, "a0out": 0, "a1out": 500}
        logs = [sync(create), swap(create + DAY // 4), swap(create + 3 * DAY // 4),
                sync(entry), sync(exit_block)]
        write_json(raw / "pools" / f"{pair}.json", {"meta": meta, "logs": logs})
        write_json(nl / "nlst2_raw" / f"{pair}.json", {
            "pair": pair, "b24": create + DAY, "deployer": buyer, "nonce": i + 1,
            "supply": 10000, "bal_dep": 100 * (i + 1), "bal_pair": 1000,
            "transfers": [{"block": create, "from": "0x" + "0" * 40,
                           "to": buyer, "value": 1000}],
            "swaps_topics": [{"topics": ["swap", "sender", "0x" + "0" * 24 + buyer[2:]],
                              "data": "0x" + "".join(f"{x:064x}" for x in [10**18, 0, 0, 500])}],
        })
        write_json(nl / "nlst3_raw" / f"{pair}.json", {"renounced": False})
        headers.extend({"block": b, "ts": BASE + b, "basefee": 0} for b in [entry, exit_block])
        entries.append(BASE + entry)
    # Same header may be selected by several pools; identical duplicate is harmless.
    (raw / "headers.jsonl").write_text("".join(json.dumps(x) + "\n" for x in headers))
    (raw / "anchors.jsonl").write_text("".join(json.dumps({"block": b, "ts": BASE + b}) + "\n"
                                                       for b in [0, 40 * DAY]))
    screened = [{"pair": p, "quarter": "2021Q1", "verdict": "KEEP", "block": b}
                for p, b in zip(pairs, [0, DAY, 2 * DAY, 12 * DAY])]
    for name, rows in [("screened.jsonl", screened), ("screened_nlst3_snapshot.jsonl", screened[:3])]:
        (raw / name).write_text("".join(json.dumps(x) + "\n" for x in rows))
    index = pd.Index(pairs, name="pair")
    pd.DataFrame({"quarter": "2021Q1", "new_set": [False] * 3 + [True]}, index=index).to_parquet(nl / "nlst4_features.parquet")
    pd.DataFrame({"entry_ts": entries}, index=index).to_parquet(nl / "nlst4_events.parquet")
    fx = pd.DataFrame({"close": 2000.0}, index=pd.date_range("2021-01-01", periods=32 * 288, freq="5min", tz="UTC", name="ts"))
    path = source / "predlab/klines_5m/ETHUSDT.parquet"
    path.parent.mkdir(parents=True)
    fx.to_parquet(path)
    return source, pairs, Context(tmp_path)


def build(mod, ctx, source):
    return mod.build_cohort(ctx, source, expected_total=4, expected_new=1)


def test_original_denominators_legacy_missingness_and_actual_completion(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    frame = build(mod, ctx, source)
    assert frame.index.tolist() == pairs
    assert len(frame) == 4 and frame.new_set.sum() == 1
    assert frame.ownership_renounced.isna().all()
    assert frame.missing_reasons.str.contains("ownership_unverified").all()
    assert frame.loc[pairs[0], "complete_ts"] == BASE + 20 * DAY + 10
    assert frame.loc[pairs[3], "n_qualified_wallets"] == 0
    assert np.isnan(frame.loc[pairs[3], "smart_money_volshare"])
    assert np.isnan(frame.loc[pairs[3], "serial_deployer_perf"])
    assert frame.loc[pairs[3], "serial_deployer_count"] == 3
    assert all((frame.raw_b24 < frame.entry_block))
    assert all(frame.decision_ts == frame.entry_ts)
    assert np.isfinite(frame.ret7).all()
    # Missing ownership must never count as a known zero.
    assert (frame.n_raw_features <= 9).all()


def test_missing_pool_raw_header_or_completed_quote_retains_every_row(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    nl = source / "predlab/nlst"
    (nl / "dex_raw/pools" / f"{pairs[0]}.json").unlink()
    (nl / "nlst2_raw" / f"{pairs[1]}.json").unlink()
    hp = nl / "dex_raw/headers.jsonl"
    hp.write_text("\n".join(l for l in hp.read_text().splitlines() if json.loads(l)["block"] != 3 * DAY + 10))
    fp = source / "predlab/klines_5m/ETHUSDT.parquet"
    fx = pd.read_parquet(fp)
    fx = fx.drop(pd.Timestamp(BASE + 13 * DAY, unit="s", tz="UTC") - pd.Timedelta(minutes=5))
    fx.to_parquet(fp)
    frame = build(mod, ctx, source)
    assert len(frame) == 4 and frame.new_set.sum() == 1
    for pair, reason in zip(pairs, ["missing_pool", "missing_raw2", "missing_header", "missing_completed_fx"]):
        assert reason in frame.loc[pair, "missing_reasons"]
    assert np.isfinite(frame.loc[pairs[1], "ret7"])
    assert np.isnan(frame.loc[pairs[3], "ret7"])


def test_same_entry_block_feature_window_is_unavailable(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    p = source / "predlab/nlst/nlst2_raw" / f"{pairs[3]}.json"
    raw = json.loads(p.read_text())
    raw["b24"] += 10
    write_json(p, raw)
    frame = build(mod, ctx, source)
    assert "feature_window_not_strictly_prior" in frame.loc[pairs[3], "missing_reasons"]
    dependent = [c for c in mod.f3.SIGNS if not c.startswith("serial_deployer")]
    assert frame.loc[pairs[3], dependent].isna().all()
    assert np.isfinite(frame.loc[pairs[3], "ret7"])


def test_exact_completed_fx_cashflow_and_no_current_candle_lookahead(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    before = build(mod, ctx, source)
    token = mod.dex.v2_buy(1000 / 2000, 10, 10000)
    expected = (mod.dex.v2_sell(token, 10, 10000) * 2000 - 2 * 150000 * 2e9 / 1e18 * 2000) / 1000 - 1
    assert before.loc[pairs[0], "ret7"] == pytest.approx(expected)
    fp = source / "predlab/klines_5m/ETHUSDT.parquet"
    fx = pd.read_parquet(fp)
    for stamp in [BASE + DAY + 10, BASE + 20 * DAY + 10]:
        fx.loc[pd.Timestamp(stamp, unit="s", tz="UTC").floor("5min"), "close"] = 999999
    fx.to_parquet(fp)
    after = build(mod, Context(tmp_path), source)
    assert after.loc[pairs[0], "ret7"] == before.loc[pairs[0], "ret7"]


def test_score_uses_only_strict_prior_observations_and_counts_nans():
    mod = module()
    frame = pd.DataFrame({c: [1., 3., 5., 8., 1000.] for c in mod.f3.SIGNS},
                         index=list("abcde"))
    frame["quarter"] = "2021Q1"
    frame["decision_ts"] = frame["available_ts"] = [1., 2., 3., 3., 4.]
    frame.loc["c", "ownership_renounced"] = np.nan
    scored = mod.score_cohort(frame)
    assert scored.loc["c", "n_standardized_features"] == 9
    assert np.isnan(scored.loc["a", "legit3_score"])
    changed = frame.copy()
    changed.loc[["d", "e"], list(mod.f3.SIGNS)] = 1e9
    assert mod.score_cohort(changed).loc["c", "legit3_score"] == scored.loc["c", "legit3_score"]


def test_even_passing_retrospective_diagnostics_never_promote_and_keep_denominators():
    mod = module()
    n = 101
    frame = pd.DataFrame({"new_set": True, "quarter": [f"2021Q{i % 4 + 1}" for i in range(n)],
                          "legit3_score": np.arange(n, dtype=float), "ret7": np.linspace(.1, .2, n),
                          "ret7_s5000": np.linspace(.05, .15, n),
                          "list_date": pd.date_range("2021-01-01", periods=n, tz="UTC"),
                          "missing_reasons": ""})
    frame.loc[0, "legit3_score"] = np.nan
    result = mod.evaluate_cohort(frame)
    assert result["n_new_requested"] == 101 and result["n_new_scoreable"] == 100
    assert result["T1"]["pass"] and result["T2"]["pass"]
    assert result["promotion_eligible"] is False
    assert result["causal_entry_rule_tested"] is False
    assert result["interpretation"] == "retrospective_ranking_and_cohort_diagnostic"
    frame.loc[100, "ret7_s5000"] = np.nan
    result = mod.evaluate_cohort(frame)
    assert result["T2"]["pass"] is False
    assert result["T2"]["n_stress_available"] < result["T2"]["n_top"]


def test_network_fence_blocks_bound_fetch_aliases_and_missing_headers():
    mod = module()
    with mod.cache_only_headers({}):
        for call in [lambda: mod.fetch.rpc("x", []), lambda: mod.f2.rpc("x", []),
                     lambda: mod.f3.get_logs("x", [], 0, 1)]:
            with pytest.raises(RuntimeError, match="network forbidden"):
                call()
        with pytest.raises(mod.CacheUnavailable, match="missing_header"):
            mod.dex.header(123)


def test_wrong_frozen_cohort_size_refused_before_market_read(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    with pytest.raises(ValueError, match="frozen cohort"):
        mod.build_cohort(ctx, source)
    assert not any("ETHUSDT" in p for p in ctx.hashes)


def test_missing_pool_metadata_is_an_unavailable_row_not_a_cohort_abort(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    path = source / "predlab/nlst/dex_raw/pools" / f"{pairs[0]}.json"
    pool = json.loads(path.read_text())
    del pool["meta"]["block"]
    write_json(path, pool)
    frame = build(mod, ctx, source)
    assert len(frame) == 4
    assert "invalid_pool_schema" in frame.loc[pairs[0], "missing_reasons"]
    assert np.isnan(frame.loc[pairs[0], "legit3_score"])


def test_dead_pool_fallback_never_makes_outcome_available_before_nominal_horizon(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    path = source / "predlab/nlst/dex_raw/pools" / f"{pairs[0]}.json"
    pool = json.loads(path.read_text())
    pool["logs"] = pool["logs"][:-1]  # last Sync is now the entry
    write_json(path, pool)
    frame = build(mod, ctx, source)
    assert frame.loc[pairs[0], "exit7_ts"] == frame.loc[pairs[0], "entry_ts"]
    assert frame.loc[pairs[0], "complete_ts"] == frame.loc[pairs[0], "entry_ts"] + 7 * DAY
    assert frame.loc[pairs[0], "rug7"]


def test_caller_archives_complete_synthetic_cohort_and_qualifies_the_only_cell(tmp_path, monkeypatch):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    real_build = mod.build_cohort
    monkeypatch.setattr(mod, "build_cohort", lambda c, s: real_build(c, s, expected_total=4, expected_new=1))
    result = mod.run(ctx, source)
    assert result == ctx.output_dir / "result.json"
    assert list(ctx.frames) == ["cohort_causal_v2.parquet"]
    assert ctx.frames["cohort_causal_v2.parquet"].index.tolist() == pairs
    payload, cells = ctx.finished
    assert len(cells) == 1 and cells[0]["id"] == mod.CELL
    assert cells[0]["metrics"]["n_new_requested"] == 1
    assert not cells[0]["metrics"]["promotion_eligible"]
    assert not cells[0]["config"]["promotion_eligible"]
    assert payload["network_used"] is False
    assert cells[0]["metrics"]["diagnostic_verdict"] == "UNAVAILABLE"
    # 2 frozen tables + 4 metadata caches + 3 per-pool caches + 1 FX file.
    assert len(ctx.hashes) == 2 + 4 + 3 * 4 + 1
    for path, digest in ctx.hashes.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest


def test_cli_requires_explicit_execution_before_common_preflight(monkeypatch):
    mod = module()
    monkeypatch.setattr(sys, "argv", [str(SCRIPT)])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 2


def test_missing_global_cohort_still_records_the_registered_blocked_cell(tmp_path):
    mod = module()
    source = tmp_path / "absent_data"
    ctx = Context(tmp_path)
    mod.run(ctx, source)
    payload, cells = ctx.finished
    assert payload["status"] == "blocked"
    assert len(cells) == 1 and cells[0]["id"] == mod.CELL
    metrics = cells[0]["metrics"]
    assert metrics["diagnostic_verdict"] == "UNAVAILABLE"
    assert metrics["n_cohort_requested"] == 3981
    assert metrics["n_new_requested"] == 2776
    assert metrics["n_prior_requested"] == 1205
    assert metrics["n_cohort_reconstructed"] == 0
    assert "nlst4_features.parquet" in metrics["blocked_reason"]
    assert not ctx.frames  # no fictitious IDs/rows


def test_one_unavailable_bootstrap_draw_keeps_full_denominator_and_prevents_t1_pass(monkeypatch):
    mod = module()
    frame = pd.DataFrame({"new_set": True, "quarter": "2021Q1", "legit3_score": [1., 2., 3.],
                          "ret7": [.1, .2, .3], "ret7_s5000": [.05, .1, .15],
                          "list_date": pd.date_range("2021-01-01", periods=3, tz="UTC"),
                          "missing_reasons": ""})
    draws = np.ones(1000)
    draws[321] = np.nan
    monkeypatch.setattr(mod, "block_bootstrap_ic", lambda *a, **kw: draws.copy())
    result = mod.evaluate_cohort(frame)
    assert result["T1"]["available"] is False
    assert result["T1"]["pass"] is False
    assert result["T1"]["bootstrap_draws"] == 1000
    assert result["T1"]["bootstrap_finite_draws"] == 999
    assert len(result["T1"]["bootstrap_ic_draws"]) == 1000
    assert np.isnan(result["T1"]["bootstrap_ic_draws"][321])
    assert np.isnan(result["T1"]["boot_p5"])
    assert result["T1"]["boot_p5_conditional_finite_diagnostic"] == 1.0


def mature_priors(source, pairs):
    raw = source / "predlab/nlst/dex_raw"
    hp = raw / "headers.jsonl"
    for pair in pairs[:3]:
        path = raw / "pools" / f"{pair}.json"
        pool = json.loads(path.read_text())
        block = pool["meta"]["block"] + 8 * DAY + 10
        pool["logs"][-1]["block"] = block
        write_json(path, pool)
        with hp.open("a") as handle:
            handle.write(json.dumps({"block": block, "ts": BASE + block, "basefee": 0}) + "\n")


def test_invalid_prior_window_preserves_known_deployer_count_and_qualifies_wallet_history(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    mature_priors(source, pairs)
    path = source / "predlab/nlst/nlst2_raw" / f"{pairs[0]}.json"
    raw2 = json.loads(path.read_text())
    raw2["b24"] += 10
    write_json(path, raw2)
    frame = build(mod, ctx, source)
    assert frame.loc[pairs[3], "serial_deployer_count"] == 3
    assert np.isfinite(frame.loc[pairs[3], "serial_deployer_perf"])
    assert np.isnan(frame.loc[pairs[3], "smart_money_volshare"])
    assert np.isnan(frame.loc[pairs[3], "n_qualified_wallets"])
    assert "wallet_history_unavailable" in frame.loc[pairs[3], "missing_reasons"]


def test_missing_prior_raw2_propagates_unknown_identity_and_wallet_history(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    mature_priors(source, pairs)
    (source / "predlab/nlst/nlst2_raw" / f"{pairs[0]}.json").unlink()
    frame = build(mod, ctx, source)
    assert np.isnan(frame.loc[pairs[3], "serial_deployer_count"])
    assert np.isnan(frame.loc[pairs[3], "serial_deployer_perf"])
    assert np.isnan(frame.loc[pairs[3], "smart_money_volshare"])
    assert "deployer_count_history_unavailable" in frame.loc[pairs[3], "missing_reasons"]
    assert "deployer_return_history_unavailable" in frame.loc[pairs[3], "missing_reasons"]
    assert frame.loc[pairs[0], "creation_block"] == 0


def test_missing_prior_entry_header_preserves_identity_but_not_known_return_history(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    mature_priors(source, pairs)
    hp = source / "predlab/nlst/dex_raw/headers.jsonl"
    hp.write_text("\n".join(l for l in hp.read_text().splitlines() if json.loads(l)["block"] != DAY + 10))
    frame = build(mod, ctx, source)
    assert frame.loc[pairs[3], "serial_deployer_count"] == 3
    assert np.isnan(frame.loc[pairs[3], "serial_deployer_perf"])
    assert np.isnan(frame.loc[pairs[3], "smart_money_volshare"])
    assert "deployer_return_history_unavailable" in frame.loc[pairs[3], "missing_reasons"]


def test_pool_creation_block_must_match_immutable_screening_record(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    path = source / "predlab/nlst/dex_raw/pools" / f"{pairs[0]}.json"
    pool = json.loads(path.read_text())
    pool["meta"]["block"] += 1
    write_json(path, pool)
    with pytest.raises(ValueError, match="frozen cohort creation block mismatch"):
        build(mod, ctx, source)


def test_missing_outcome_does_not_taint_wallets_before_earliest_possible_completion(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    hp = source / "predlab/nlst/dex_raw/headers.jsonl"
    hp.write_text("\n".join(l for l in hp.read_text().splitlines() if json.loads(l)["block"] != DAY + 10))
    frame = build(mod, ctx, source)
    for pair, expected_count in zip(pairs[1:3], [1, 2]):
        assert frame.loc[pair, "n_qualified_wallets"] == 0
        assert frame.loc[pair, "serial_deployer_count"] == expected_count
        assert "wallet_history_unavailable" not in frame.loc[pair, "missing_reasons"]
        assert "deployer_return_history_unavailable" not in frame.loc[pair, "missing_reasons"]


def test_entry_reference_mismatch_cannot_donate_to_later_normalization(tmp_path):
    mod = module()
    source, pairs, ctx = fixture(tmp_path)
    path = source / "predlab/nlst/nlst4_events.parquet"
    reference = pd.read_parquet(path)
    reference.loc[pairs[0], "entry_ts"] += 60
    reference.to_parquet(path)
    frame = build(mod, ctx, source)
    assert "original_entry_clock_mismatch" in frame.loc[pairs[0], "missing_reasons"]
    assert frame.loc[pairs[0], ["decision_ts", "available_ts", "complete_ts"]].isna().all()
    # Only one valid predecessor remains for pool 3, below min2 normalization.
    assert frame.loc[pairs[2], "n_standardized_features"] == 0
    # Independent creation/deployer information is still retained.
    assert frame.loc[pairs[0], "creation_block"] == 0
    assert frame.loc[pairs[3], "serial_deployer_count"] == 3

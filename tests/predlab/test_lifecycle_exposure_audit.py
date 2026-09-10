"""Synthetic lifecycle clocks only; no original market observations are read."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/audit_lifecycle_exposure_2026_09_10.py"


def module():
    assert SCRIPT.exists(), "exposure-only lifecycle audit is not implemented"
    spec = importlib.util.spec_from_file_location("lifecycle_audit", SCRIPT)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def allocation(values, start="2022-05-12 13:00"):
    return pd.Series(values, index=pd.date_range(start, periods=len(values), freq="h", tz="UTC"), name="OLDUSDT")


def event(closure="2022-05-12T15:30:00Z", restriction=None):
    return {"symbol": "OLDUSDT", "closure_utc": closure,
            "new_position_cutoff_utc": restriction}


def test_intrabar_closure_uses_available_bar_interval_not_open_label():
    out = module().audit_event(allocation([0, .1, .1, .1, 0]), event())
    assert out["boundary"]["bar_open_utc"] == "2022-05-12T15:00:00+00:00"
    assert out["boundary"]["incoming_previous_allocation"] == .1
    assert out["boundary"]["requested_allocation"] == .1
    assert out["straddling_allocated_bars"] == 1
    assert out["post_closure_allocated_bars"] == 1
    assert out["status"] == "observed_lifecycle_conflict"


def test_flatten_at_exact_closure_cannot_hide_incoming_position():
    out = module().audit_event(allocation([0, .1, 0, 0]), event("2022-05-12T15:00:00Z"))
    assert out["boundary"]["incoming_previous_allocation"] == .1
    assert out["boundary"]["requested_allocation"] == 0
    assert out["unreconciled_incoming_at_closure"] is True
    assert out["status"] == "observed_lifecycle_conflict"


def test_observed_preclosure_flatten_is_distinct_from_boundary_flatten():
    out = module().audit_event(allocation([.1, 0, 0, 0]), event())
    assert out["unreconciled_incoming_at_closure"] is False
    assert out["status"] == "no_observed_conflict_qualified"
    assert out["readiness_certified"] is False


def test_new_postclosure_request_is_reported_even_if_boundary_flat():
    out = module().audit_event(allocation([0, 0, 0, .1, .1]), event())
    assert out["post_closure_allocated_bars"] == 2
    assert out["status"] == "observed_lifecycle_conflict"


def test_restriction_distinguishes_target_increase_from_unknown_quantity_drift():
    out = module().audit_event(allocation([0, .1, .1, 0, 0]),
                              event("2022-05-12T16:30:00Z", "2022-05-12T14:00:00Z"))
    assert out["restriction"]["new_target_requests"] == 1
    assert out["restriction"]["increased_nonzero_target_requests"] == 0
    assert out["restriction"]["nonzero_unchanged_target_bars"] == 1
    assert out["restriction"]["order_quantity_increases"] is None


def test_restriction_report_includes_forbidden_new_request_after_closure():
    out = module().audit_event(allocation([0, 0, 0, .1]),
                              event("2022-05-12T15:00:00Z", "2022-05-12T14:30:00Z"))
    assert out["restriction"]["new_target_requests"] == 1
    assert out["restriction"]["new_target_requests_before_closure"] == 0


def test_nonfinite_allocation_never_becomes_no_exposure():
    out = module().audit_event(allocation([0, np.nan, np.nan, 0]), event())
    assert out["status"] == "unavailable_allocation"
    assert out["boundary"]["incoming_previous_allocation"] is None
    assert out["boundary"]["requested_allocation"] is None


def test_gap_in_allocation_clock_is_rejected_instead_of_compressed():
    w = allocation([0, .1, .1, 0]).drop(pd.Timestamp("2022-05-12T14:00:00Z"))
    with pytest.raises(ValueError, match="hourly clock"):
        module().audit_event(w, event())


def test_event_outside_clock_is_unavailable_not_clear():
    out = module().audit_event(allocation([0, 0]), event())
    assert out["status"] == "unavailable_event_clock"


def test_frozen_event_construction_holds_next_bar_and_preserves_missing_inputs():
    mod = module()
    clock = pd.date_range("2021-01-01", periods=2200, freq="h", tz="UTC")
    close = pd.DataFrame({"OLDUSDT": 10.0}, index=clock)
    volume = pd.DataFrame({"OLDUSDT": 100.0}, index=clock)
    close.iloc[2170:, 0] = 5.0
    volume.iloc[2170, 0] = 100000.
    close.iloc[2180, 0] = np.nan
    weights, coverage = mod.build_original_allocations(close, volume,
        {"2021-01-01": ["OLDUSDT"]}, [{"id": "one", "thr": 2.5, "H": 6}], clock)
    w = weights["one"].OLDUSDT
    assert w.iloc[2170] == 0
    assert w.iloc[2171:2177].tolist() == [.1] * 6
    assert w.iloc[2177] == 0
    assert coverage["missing_close_observations"] == 1
    assert pd.isna(close.iloc[2180, 0])


def test_source_manifest_rejects_changed_or_replacement_input(tmp_path):
    mod = module()
    source = tmp_path / "original"
    source.mkdir()
    p = source / "ONE.parquet"
    p.write_bytes(b"original")
    rows = [{"path": str(p), "sha256": hashlib.sha256(b"original").hexdigest(), "symbol": "ONE"}]
    assert mod.verify_original_sources(rows, source, expected_count=1) == {str(p): rows[0]["sha256"]}
    p.write_bytes(b"replacement")
    with pytest.raises(ValueError, match="hash mismatch"):
        mod.verify_original_sources(rows, source, expected_count=1)
    with pytest.raises(ValueError, match="source root"):
        mod.verify_original_sources(rows, tmp_path / "different", expected_count=1)


def test_duplicate_or_missing_manifest_symbol_is_rejected(tmp_path):
    mod = module()
    with pytest.raises(ValueError, match="count"):
        mod.verify_original_sources([], tmp_path, expected_count=1)
    with pytest.raises(ValueError, match="duplicate"):
        mod.verify_original_sources([{"path": "a", "symbol": "ONE"}] * 2, tmp_path, expected_count=2)


def test_default_and_help_do_not_open_registration_or_consume_state(monkeypatch, capsys):
    mod = module()
    def forbidden(*args, **kwargs):
        pytest.fail("dry run consumed execution state")
    monkeypatch.setattr(mod, "execute", forbidden)
    assert mod.main([]) == 0
    assert "--execute" in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        mod.main(["--help"])
    assert exc.value.code == 0


def test_filtered_market_read_excludes_holdout_and_unused_price_columns(tmp_path):
    mod = module()
    clock = pd.date_range("2025-03-31 23:00", periods=2, freq="h", tz="UTC", name="ts")
    p = tmp_path / "ONE.parquet"
    pd.DataFrame({"close": [10., 999.], "quote_volume": [1., 999.], "open": [1., 2.]}, index=clock).to_parquet(p)
    f = mod.read_original_market(p, "2020-06-01", "2025-04-01")
    assert f.index.tolist() == [pd.Timestamp("2025-03-31T23:00:00Z")]
    assert list(f.columns) == ["close", "quote_volume"]
    with pytest.raises(ValueError, match="development"):
        mod.read_original_market(p, "2020-06-01", "2025-04-02")


def registration_fixture():
    cells = [{"id": f"thr{t}_H{h}", "thr": t, "H": h} for t in (2.5, 3.5) for h in (6, 24, 48)]
    family = {"cells": cells, "warmup_start": "2020-06-01", "hourly_end": "2025-03-31T23:00:00Z",
              "weight_per_event": .1, "gross_cap": 1., "feature_window": 2160, "feature_min_periods": 1440}
    gate = {"type": "exposure_only_forensic_audit", "strategy_evaluation_permitted": False,
            "signal_weight_reconstruction_permitted": True, "original_inputs_only": True,
            "original_cycle": "audit_reevaluation_2026_09_09", "allow_holdout": False,
            "development_window": ["2021-01-01", "2025-03-31"], "families": {"liq_fade": family},
            "events": [{"symbol": f"OLD{i}", "closure_utc": "2022-05-12T15:30:00Z"} for i in range(5)]}
    original = {"families": {"liq_fade": json.loads(json.dumps(family))}}
    return gate, original


@pytest.mark.parametrize("change", ["new_grid", "holdout", "performance", "recovered_input", "new_weight", "duplicate_event"])
def test_registration_refuses_unregistered_scope_change(change):
    mod = module()
    gate, original = registration_fixture()
    mod.validate_registration(gate, original)
    if change == "new_grid": gate["families"]["liq_fade"]["cells"][0]["H"] = 7
    elif change == "holdout": gate["allow_holdout"] = True
    elif change == "performance": gate["strategy_evaluation_permitted"] = True
    elif change == "recovered_input": gate["original_inputs_only"] = False
    elif change == "new_weight": gate["families"]["liq_fade"]["weight_per_event"] = .2
    elif change == "duplicate_event": gate["events"][1] = gate["events"][0].copy()
    with pytest.raises(ValueError, match="registration"):
        mod.validate_registration(gate, original)


def test_uncommitted_source_refused_before_any_market_read_or_output(tmp_path, monkeypatch):
    mod = module()
    gate, original = registration_fixture()
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    monkeypatch.setattr(mod.registry, "get_experiment", lambda key: gate if key == mod.KEY else original)
    def dirty(*args):
        raise RuntimeError("uncommitted source")
    monkeypatch.setattr(mod.registry, "preflight", dirty)
    with pytest.raises(RuntimeError, match="uncommitted"):
        mod.execute()
    assert not list(tmp_path.iterdir())


def forensic_payload():
    gate, _ = registration_fixture()
    return {"experiment": "audit_lifecycle_exposure_2026_09_10", "cells": [
        {"id": c["id"], "config": c, "metrics": {"financial_candidate_evaluated": False,
           "events": [{"symbol": e["symbol"], "status": "synthetic"} for e in gate["events"]]}}
        for c in gate["families"]["liq_fade"]["cells"]]}


def test_dedicated_six_row_ledger_preserves_central_trials_and_refuses_repeat(tmp_path, monkeypatch):
    mod = module()
    central = tmp_path / "trial_ledger.jsonl"
    central.write_text('{"existing_financial_trial": true}\n')
    before = central.read_bytes()
    out = tmp_path / "audit"
    out.mkdir()
    def forbidden(*args, **kwargs):
        pytest.fail("forensic record entered the financial trial registry")
    monkeypatch.setattr(mod.registry, "log_trial", forbidden)
    mod.write_forensic_artifact(out, forensic_payload())
    rows = [json.loads(line) for line in (out / "forensic-ledger.jsonl").read_text().splitlines()]
    assert len(rows) == 6 and len({r["cell"] for r in rows}) == 6
    assert central.read_bytes() == before
    result = json.loads((out / "result.json").read_text())
    assert result["output_sha256"]["forensic-ledger.jsonl"] == hashlib.sha256((out / "forensic-ledger.jsonl").read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        mod.write_forensic_artifact(out, forensic_payload())


@pytest.mark.parametrize("failure", ["serialization", "missing_cell", "missing_event", "duplicate_cell", "financial_candidate"])
def test_invalid_forensic_payload_never_writes_partial_ledger(tmp_path, failure):
    mod = module()
    payload = forensic_payload()
    if failure == "serialization": payload["unsupported"] = object()
    elif failure == "missing_cell": payload["cells"].pop()
    elif failure == "missing_event": payload["cells"][0]["metrics"]["events"].pop()
    elif failure == "duplicate_cell": payload["cells"][1] = payload["cells"][0]
    elif failure == "financial_candidate": payload["cells"][0]["metrics"]["financial_candidate_evaluated"] = True
    with pytest.raises((TypeError, ValueError)):
        mod.write_forensic_artifact(tmp_path, payload)
    assert not list(tmp_path.iterdir())

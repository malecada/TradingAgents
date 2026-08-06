"""PredlabSource: filesystem layout, reference files, degradation."""
from __future__ import annotations

import json
from pathlib import Path

from tradingagents.monitor.predlab import PredlabSource, resolve_predlab_source


def _mk_data(tmp_path: Path, champion_rows=None, vt10_rows=None,
             gates=None, backtest=None) -> Path:
    s1 = tmp_path / "predlab" / "s1_paper"
    s1.mkdir(parents=True)
    if champion_rows is not None:
        (s1 / "journal_champion.jsonl").write_text(
            "\n".join(json.dumps(r) for r in champion_rows) + "\n")
    if vt10_rows is not None:
        (s1 / "journal.jsonl").write_text(
            "\n".join(json.dumps(r) for r in vt10_rows) + "\n")
    if gates is not None:
        (tmp_path / "predlab" / "gates.json").write_text(json.dumps(gates))
    if backtest is not None:
        (tmp_path / "predlab" / "champion_backtest.json").write_text(
            json.dumps(backtest))
    return tmp_path


def _row(asof, ret):
    return {"asof": asof, "written_utc": f"{asof}T00:20:00+00:00",
            "n_universe": 500, "membership_hash": "abc",
            "weights": {"BTCUSDT": 0.025, "AKEUSDT": -0.025},
            "realized_book_ret": ret, "est_turnover": 0.1,
            "est_cost": 0.00005, "vt15_b100_scale": None,
            "vt10_scale": None, "breadth": 200}


GATES = {"predlab_opt": {"final_champion": {
    "dev_metrics": {"ovl_sr_full": 1.892, "ovl_maxdd": 0.176,
                    "raw_sr_full": 1.928,
                    "dsr_selection_pool": 0.913}}}}
BACKTEST = {"systems": {
    "new": {"yearly_ovl": {"2025": {"sr": 2.0, "ret": 0.24,
                                    "maxdd": 0.058, "n_days": 365}}},
    "old": {"yearly_ovl": {"2025": {"sr": 2.0, "ret": 0.24,
                                    "maxdd": 0.058, "n_days": 365}}}}}


def test_full_payload(tmp_path):
    root = _mk_data(tmp_path,
                    champion_rows=[_row("2026-08-03", None),
                                   _row("2026-08-04", 0.01)],
                    vt10_rows=[_row("2026-08-04", 0.02)],
                    gates=GATES, backtest=BACKTEST)
    p = PredlabSource(str(root)).payload()
    assert p["performance"]["books"]["champion"]["cards"]["n_days"] == 2
    assert p["performance"]["books"]["vt10"]["cards"]["n_days"] == 1
    assert p["performance"]["reference"]["ovl_sr_full"] == 1.892
    assert "2025" in p["performance"]["backtest_yearly"]["champion"]
    assert p["books"]["champion"]["asof"] == "2026-08-04"
    assert p["gate"]["threshold_sr"] == 0.946
    assert p["health"]["books"]["champion"]["rows"] == 2
    assert "predlab-journal-backup" in p["health"]["heartbeat_note"]


def test_missing_everything_degrades_to_nulls(tmp_path):
    p = PredlabSource(str(tmp_path)).payload()
    assert p["performance"]["books"] == {"champion": None, "vt10": None}
    assert p["performance"]["reference"] is None
    assert p["performance"]["backtest_yearly"] is None
    assert p["books"] == {"champion": None, "vt10": None}
    assert p["health"]["books"] == {"champion": None, "vt10": None}
    assert p["gate"]["threshold_sr"] == 0.946  # fallback


def test_payload_is_ttl_cached(tmp_path):
    root = _mk_data(tmp_path, champion_rows=[_row("2026-08-04", 0.01)])
    src = PredlabSource(str(root))
    first = src.payload()
    # rewrite journal; cached payload must not change within TTL
    (root / "predlab" / "s1_paper" / "journal_champion.jsonl").write_text(
        json.dumps(_row("2026-08-05", 0.5)) + "\n")
    assert src.payload() == first


def test_resolve_from_env(tmp_path, monkeypatch):
    monkeypatch.delenv("PREDLAB_DATA_DIR", raising=False)
    assert resolve_predlab_source() is None
    monkeypatch.setenv("PREDLAB_DATA_DIR", str(tmp_path))
    src = resolve_predlab_source()
    assert src is not None and src.data_dir == str(tmp_path)

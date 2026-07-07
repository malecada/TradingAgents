"""Tests for scripts/exp_flip_rate.py — the signal flip-rate stability
metric used to compare a baseline LGB walk-forward run against a
training-window-staggered ensemble run (Experiment E2)."""
from __future__ import annotations

import json
import sys

import pandas as pd
import pytest


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def test_flip_rate_for_pair_exact_known_rate():
    from scripts.exp_flip_rate import flip_rate_for_pair

    # direction = sign(prediction - ref_price); ref_price is 100.0 throughout.
    df_a = pd.DataFrame([
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 105.0, "ref_price": 100.0},  # up
        {"date": "2024-01-01", "coin_id": "ETH", "prediction": 95.0, "ref_price": 100.0},   # down
        {"date": "2024-01-02", "coin_id": "BTC", "prediction": 102.0, "ref_price": 100.0},  # up
        {"date": "2024-01-02", "coin_id": "ETH", "prediction": 98.0, "ref_price": 100.0},   # down
    ])
    df_b = pd.DataFrame([
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 95.0, "ref_price": 100.0},   # down -> FLIP
        {"date": "2024-01-01", "coin_id": "ETH", "prediction": 90.0, "ref_price": 100.0},   # down -> same
        {"date": "2024-01-02", "coin_id": "BTC", "prediction": 103.0, "ref_price": 100.0},  # up -> same
        {"date": "2024-01-02", "coin_id": "ETH", "prediction": 105.0, "ref_price": 100.0},  # up -> FLIP
    ])

    n_common, n_flips, flip_rate = flip_rate_for_pair(df_a, df_b)
    assert n_common == 4
    assert n_flips == 2
    assert flip_rate == pytest.approx(0.5)


def test_flip_rate_for_pair_only_common_rows_counted():
    from scripts.exp_flip_rate import flip_rate_for_pair

    df_a = pd.DataFrame([
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 105.0, "ref_price": 100.0},
        {"date": "2024-01-03", "coin_id": "BTC", "prediction": 105.0, "ref_price": 100.0},  # not in b
    ])
    df_b = pd.DataFrame([
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 95.0, "ref_price": 100.0},   # FLIP
        {"date": "2024-01-02", "coin_id": "BTC", "prediction": 105.0, "ref_price": 100.0},  # not in a
    ])

    n_common, n_flips, flip_rate = flip_rate_for_pair(df_a, df_b)
    assert n_common == 1
    assert n_flips == 1
    assert flip_rate == pytest.approx(1.0)


def test_flip_rate_for_pair_no_common_rows():
    from scripts.exp_flip_rate import flip_rate_for_pair

    df_a = pd.DataFrame([{"date": "2024-01-01", "coin_id": "BTC", "prediction": 105.0, "ref_price": 100.0}])
    df_b = pd.DataFrame([{"date": "2024-02-01", "coin_id": "BTC", "prediction": 95.0, "ref_price": 100.0}])

    n_common, n_flips, flip_rate = flip_rate_for_pair(df_a, df_b)
    assert n_common == 0
    assert n_flips == 0
    assert flip_rate == 0.0


def test_compute_flip_rates_per_horizon_and_overall(tmp_path):
    from scripts.exp_flip_rate import compute_flip_rates

    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()

    # h7: 4 common rows, 2 flips -> 0.5
    _write_csv(dir_a / "preds_lgb_h7.csv", [
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 105.0, "ref_price": 100.0, "actual": 106.0},
        {"date": "2024-01-01", "coin_id": "ETH", "prediction": 95.0, "ref_price": 100.0, "actual": 94.0},
        {"date": "2024-01-02", "coin_id": "BTC", "prediction": 102.0, "ref_price": 100.0, "actual": 103.0},
        {"date": "2024-01-02", "coin_id": "ETH", "prediction": 98.0, "ref_price": 100.0, "actual": 97.0},
    ])
    _write_csv(dir_b / "preds_lgb_h7.csv", [
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 95.0, "ref_price": 100.0, "actual": 96.0},   # FLIP
        {"date": "2024-01-01", "coin_id": "ETH", "prediction": 90.0, "ref_price": 100.0, "actual": 89.0},
        {"date": "2024-01-02", "coin_id": "BTC", "prediction": 103.0, "ref_price": 100.0, "actual": 104.0},
        {"date": "2024-01-02", "coin_id": "ETH", "prediction": 105.0, "ref_price": 100.0, "actual": 106.0},  # FLIP
    ])

    # h14: 2 common rows, 0 flips -> 0.0
    _write_csv(dir_a / "preds_lgb_h14.csv", [
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 110.0, "ref_price": 100.0, "actual": 111.0},
        {"date": "2024-01-02", "coin_id": "BTC", "prediction": 90.0, "ref_price": 100.0, "actual": 89.0},
    ])
    _write_csv(dir_b / "preds_lgb_h14.csv", [
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 115.0, "ref_price": 100.0, "actual": 116.0},
        {"date": "2024-01-02", "coin_id": "BTC", "prediction": 92.0, "ref_price": 100.0, "actual": 91.0},
    ])

    result = compute_flip_rates(dir_a, dir_b)

    assert result["horizons"][7] == {"n_common": 4, "n_flips": 2, "flip_rate": pytest.approx(0.5)}
    assert result["horizons"][14] == {"n_common": 2, "n_flips": 0, "flip_rate": pytest.approx(0.0)}

    # overall pools rows across horizons: (2 + 0) flips / (4 + 2) common
    assert result["overall"]["n_common"] == 6
    assert result["overall"]["n_flips"] == 2
    assert result["overall"]["flip_rate"] == pytest.approx(2 / 6)


def test_discover_common_horizons_intersects_dirs(tmp_path):
    from scripts.exp_flip_rate import discover_common_horizons

    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    for f in ("preds_lgb_h7.csv", "preds_lgb_h14.csv", "preds_lgb_h21.csv"):
        (dir_a / f).write_text("date,coin_id,prediction,ref_price\n")
    for f in ("preds_lgb_h7.csv", "preds_lgb_h14.csv"):
        (dir_b / f).write_text("date,coin_id,prediction,ref_price\n")

    assert discover_common_horizons(dir_a, dir_b) == [7, 14]


def test_main_writes_json_and_prints_table(tmp_path, monkeypatch, capsys):
    from scripts import exp_flip_rate

    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    _write_csv(dir_a / "preds_lgb_h7.csv", [
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 105.0, "ref_price": 100.0, "actual": 106.0},
    ])
    _write_csv(dir_b / "preds_lgb_h7.csv", [
        {"date": "2024-01-01", "coin_id": "BTC", "prediction": 95.0, "ref_price": 100.0, "actual": 96.0},
    ])

    out_path = tmp_path / "flip.json"
    argv = [
        "exp_flip_rate.py",
        "--dir-a", str(dir_a),
        "--dir-b", str(dir_b),
        "--out", str(out_path),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    exp_flip_rate.main()

    captured = capsys.readouterr()
    assert "flip-rate" in captured.out.lower()

    payload = json.loads(out_path.read_text())
    assert payload["overall"]["flip_rate"] == pytest.approx(1.0)
    assert payload["horizons"]["7"]["n_common"] == 1

"""Tests for scripts/parity_refetch_and_replay.py — the V5 drift check.

The script is not an importable package module, so it is loaded by path.
"""
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PARITY_PATH = _REPO_ROOT / "scripts" / "parity_refetch_and_replay.py"


def _load_parity():
    spec = importlib.util.spec_from_file_location("parity_mod", _PARITY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parity_routes_cover_four_v5_coins():
    parity = _load_parity()
    assert set(parity._PARITY_ROUTES) == {
        "bitcoin", "ethereum", "binancecoin", "solana"
    }
    # 193f routes use PIT on-chain features; 78f routes do not.
    assert parity._PARITY_ROUTES["ethereum"]["pit"] is True
    assert parity._PARITY_ROUTES["solana"]["pit"] is True
    assert parity._PARITY_ROUTES["bitcoin"]["pit"] is False
    assert parity._PARITY_ROUTES["binancecoin"]["pit"] is False


def test_regenerate_predictions_builds_routing_to_sandbox(tmp_path):
    """regenerate_predictions runs evaluate_models_multi per route and
    returns a {coin: sandbox pred dir} routing dict."""
    parity = _load_parity()
    calls = []

    def fake_run_script(name, args, env_extra):
        calls.append((name, args, env_extra))

    with patch.object(parity, "_run_script", side_effect=fake_run_script):
        routing = parity.regenerate_predictions(
            tmp_path, end_date="2026-05-20", lookback_days=1500,
        )

    assert set(routing) == {"bitcoin", "ethereum", "binancecoin", "solana"}
    for coin, pred_dir in routing.items():
        # Each route's output dir lives under the sandbox preds tree.
        assert str(tmp_path / "preds") in pred_dir
    # Four evaluate_models_multi invocations, all redirected to the sandbox.
    assert len(calls) == 4
    for name, args, env_extra in calls:
        assert name == "evaluate_models_multi.py"
        assert env_extra["TRADINGAGENTS_DATA_ROOT"] == str(tmp_path)
        assert "--trade-date" in args and "2026-05-20" in args
        assert "lgb" in args
    # The two PIT routes pass --onchain-pit; the two 78f routes do not.
    pit_flags = [("--onchain-pit" in args) for _, args, _ in calls]
    assert sum(pit_flags) == 2


def test_run_replay_writes_routing_json_and_uses_sys_executable(tmp_path):
    parity = _load_parity()
    (tmp_path / "replay").mkdir(parents=True, exist_ok=True)
    routing = {"bitcoin": str(tmp_path / "preds" / "bitcoin")}
    captured = {}

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return None

    with patch.object(parity.subprocess, "run", side_effect=fake_run):
        out = parity.run_replay(
            tmp_path, "2026-05-13", "2026-05-20", kelly=0.25, routing=routing,
        )

    routing_json = tmp_path / "parity_routing.json"
    assert routing_json.exists()
    assert json.loads(routing_json.read_text()) == routing
    cmd = captured["cmd"]
    assert cmd[0] == sys.executable
    assert "baseline_v5_mix.py" in cmd[1]
    assert "--routing-json" in cmd
    assert "--start" in cmd and "2026-05-13" in cmd
    assert out == tmp_path / "replay"

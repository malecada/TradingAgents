"""Unit tests for llm_c3p_pair_xs core (no API calls)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tradingagents.xsect.pair_xs import (
    K_ROUNDS,
    bt_scores,
    build_prompt,
    chunk_instances,
    make_instances,
    parse_verdicts,
    sample_pairs,
    swap_consistency,
    week_seed,
    week_tags,
)

SYMS = [f"S{i:03d}" for i in range(37)]  # odd count on purpose


def test_sample_pairs_deterministic_and_degree():
    p1 = sample_pairs(SYMS, seed=123)
    p2 = sample_pairs(SYMS, seed=123)
    assert p1 == p2
    assert sample_pairs(SYMS, seed=124) != p1
    # odd n: 18 pairs/round
    assert len(p1) == K_ROUNDS * (len(SYMS) // 2)
    deg = {}
    for a, b in p1:
        assert a != b
        deg[a] = deg.get(a, 0) + 1
        deg[b] = deg.get(b, 0) + 1
    # each symbol skips at most a few rounds; nobody absent
    assert set(deg) == set(SYMS)
    assert max(deg.values()) <= K_ROUNDS


def test_make_instances_both_orders_disjoint_prompts():
    pairs = sample_pairs(SYMS, seed=5)
    inst = make_instances(pairs, seed=5)
    assert len(inst) == 2 * len(pairs)
    # each pair id appears exactly twice, once per order
    by_pid = {}
    for pid, a, b in inst:
        by_pid.setdefault(pid, []).append((a, b))
    for pid, orders in by_pid.items():
        assert len(orders) == 2
        assert orders[0] == (orders[1][1], orders[1][0])
    # sequential chunking: first half is order-1, second half order-2 —
    # both orders of one pair never share a chunk of size <= half
    chunks = chunk_instances(inst, 20)
    for ch in chunks:
        pids = [pid for pid, _, _ in ch]
        firsts = {}
        for pid, a, _ in ch:
            if pid in firsts:
                pytest.fail("both orders of a pair in one prompt")
            firsts[pid] = a


def test_parse_verdicts_and_resolution():
    pairs = [("A", "B"), ("C", "D")]
    inst = [(0, "A", "B"), (1, "D", "C")]
    tags = {"A": "ASSET_001", "B": "ASSET_002", "C": "ASSET_003", "D": "ASSET_004"}
    ok = parse_verdicts(inst, ["ASSET_002", "ASSET_003"], tags)
    assert ok == [(0, "B"), (1, "C")]
    # wrong length -> all unresolved
    assert parse_verdicts(inst, ["ASSET_002"], tags) == [None, None]
    # winner not in duel -> that instance unresolved
    bad = parse_verdicts(inst, ["ASSET_003", "ASSET_003"], tags)
    assert bad == [None, (1, "C")]


def test_bt_scores_recover_transitive_order():
    syms = ["A", "B", "C", "D"]
    wins = []
    strength = {"A": 3, "B": 2, "C": 1, "D": 0}
    rng = np.random.default_rng(7)
    for _ in range(200):
        i, j = rng.choice(4, size=2, replace=False)
        a, b = syms[i], syms[j]
        pa = 1 / (1 + np.exp(-(strength[a] - strength[b])))
        wins.append((a, b) if rng.random() < pa else (b, a))
    s = bt_scores(syms, wins)
    assert list(s.sort_values(ascending=False).index) == ["A", "B", "C", "D"]
    # normalized: mean log-strength ~ 0
    assert abs(s.mean()) < 0.2


def test_bt_scores_empty_and_unbeaten_regularized():
    s = bt_scores(["A", "B"], [])
    assert float(s["A"]) == pytest.approx(float(s["B"]))
    # all wins for A: prior keeps strengths finite
    s2 = bt_scores(["A", "B"], [("A", "B")] * 50)
    assert np.isfinite(s2).all() and s2["A"] > s2["B"]


def test_swap_consistency_metrics():
    # pair 0 consistent (B wins both orders), pair 1 flips with position
    resolved = [
        (0, "B", "A"), (0, "B", "B"),
        (1, "C", "C"), (1, "D", "D"),
    ]
    cons, rate1 = swap_consistency(resolved)
    assert cons == pytest.approx(0.5)
    assert rate1 == pytest.approx(0.75)  # winners equal first slot in 3/4


def test_week_tags_and_prompt_round_trip():
    seed = week_seed(pd.Timestamp("2024-03-01", tz="UTC"), "base")
    tags = week_tags(SYMS, seed)
    assert len(set(tags.values())) == len(SYMS)
    assert all(t.startswith("ASSET_") for t in tags.values())
    assert week_tags(SYMS, seed) == tags  # deterministic
    named = week_tags(SYMS, seed, named=True)
    assert named["S001"] == "S001"

    wk = pd.DataFrame({"symbol": SYMS,
                       "ret_4w": np.linspace(-0.5, 0.5, len(SYMS)),
                       "category": ["defi"] * len(SYMS)})
    inst = make_instances(sample_pairs(SYMS, seed), seed)[:3]
    prompt = build_prompt(inst, wk, tags)
    assert "Duel 3:" in prompt and "Duel 4:" not in prompt
    for _, a, b in inst:
        assert tags[a] in prompt and tags[b] in prompt

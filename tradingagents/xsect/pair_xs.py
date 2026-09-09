"""llm_c3p_pair_xs — pairwise-duel core (charter §3, frozen).

Pure functions only (no API calls here): seeded pair sampling, duel-instance
construction with both presentation orders, prompt assembly, Bradley-Terry
aggregation, and the P0 swap/agreement metrics.

Spec: docs/superpowers/specs/2026-08-17-llm-c3p-pair-xs-charter.md
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

K_ROUNDS = 10
DUELS_PER_PROMPT = 20
BT_ALPHA = 0.5
BT_ITERS = 200
SEED_SALT = "20260817"

FIELDS = ["ret_4w", "ret_12w", "dist_26w_high", "vol_ewma20", "volvol_20",
          "dvol_rank", "mcap_cm", "funding_3d", "funding_30d",
          "d_adract_30d", "d_txcnt_30d", "unlock_next30_pct",
          "unlock_prev30_pct", "age_weeks", "category"]

PROMPT = """You are judging duels between crypto perpetual-futures assets.
Each duel shows two assets; each asset is a card of point-in-time numeric
facts (null = not available). Fields: ret_4w/ret_12w = 4/12-week log
returns; dist_26w_high = log distance from 26-week high; vol_ewma20 =
annualized vol; volvol_20 = vol of vol; dvol_rank = dollar-volume
percentile; mcap_cm = market cap USD; funding_3d/30d = mean daily funding
(positive = longs pay); d_adract_30d/d_txcnt_30d = 30d change in active
addresses / tx count; unlock_next30_pct / unlock_prev30_pct = scheduled
token unlocks next/past 30d as fraction of supply; age_weeks = weeks since
listing; category = protocol category.

For EACH duel decide which of its two assets has the higher expected 5-day
forward return. Use only the given numbers; consider interactions (e.g.
crowded funding + imminent unlocks + weak activity). Return ONLY JSON:
{{"winners": ["<tag>", "<tag>", ...]}} — exactly one winner tag per duel,
in duel order.

{duels}"""


def week_seed(date: pd.Timestamp, variant: str) -> int:
    h = hashlib.sha256(f"{date.date()}|{variant}|{SEED_SALT}".encode()).hexdigest()
    return int(h[:8], 16)


def round3(x):
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return None
    return float(f"{x:.3g}") if isinstance(x, (int, float, np.floating)) else x


def card_text(row, tag: str) -> str:
    kv = []
    for f in FIELDS:
        v = row.get(f)
        v = round3(v) if not isinstance(v, str) else v
        kv.append(f"{f}={v if v is not None else 'null'}")
    return f"{tag}: " + ", ".join(kv)


def sample_pairs(syms: list[str], seed: int, k: int = K_ROUNDS) -> list[tuple[str, str]]:
    """k rounds of seeded permutation-pairing; multigraph, multiplicity kept."""
    rng = np.random.default_rng(seed)
    pairs = []
    for _ in range(k):
        perm = rng.permutation(len(syms))
        for i in range(0, len(syms) - 1, 2):
            pairs.append((syms[perm[i]], syms[perm[i + 1]]))
    return pairs


def make_instances(pairs: list[tuple[str, str]], seed: int) -> list[tuple[int, str, str]]:
    """Both orders of every pair as (pair_id, first, second) instances,
    each half independently seeded-shuffled."""
    rng = np.random.default_rng(seed + 1)
    o1 = [(i, a, b) for i, (a, b) in enumerate(pairs)]
    o2 = [(i, b, a) for i, (a, b) in enumerate(pairs)]
    return ([o1[j] for j in rng.permutation(len(o1))]
            + [o2[j] for j in rng.permutation(len(o2))])


def chunk_instances(instances: list, n: int = DUELS_PER_PROMPT) -> list[list]:
    """Chunk order-1 and order-2 halves separately so the two orders of a
    pair can never share a prompt (charter §3)."""
    half = len(instances) // 2
    out = []
    for part in (instances[:half], instances[half:]):
        out += [part[i:i + n] for i in range(0, len(part), n)]
    return out


def build_prompt(chunk, wk_cards: pd.DataFrame, tags: dict[str, str]) -> str:
    rows = wk_cards.set_index("symbol")
    blocks = []
    for d, (_, a, b) in enumerate(chunk):
        blocks.append(f"Duel {d + 1}:\n{card_text(rows.loc[a], tags[a])}\n"
                      f"{card_text(rows.loc[b], tags[b])}")
    return PROMPT.format(duels="\n\n".join(blocks))


def week_tags(syms: list[str], seed: int, named: bool = False) -> dict[str, str]:
    if named:
        return {s: s for s in syms}
    rng = np.random.default_rng(seed + 2)
    shuffled = rng.permutation(len(syms))
    return {s: f"ASSET_{i:03d}" for s, i in zip(syms, shuffled)}


def parse_verdicts(chunk, winners: list[str], tags: dict[str, str]) -> list[tuple[int, str] | None]:
    """Per instance: (pair_id, winning symbol) or None if unresolved."""
    inv = {v: k for k, v in tags.items()}
    out = []
    if not isinstance(winners, list) or len(winners) != len(chunk):
        return [None] * len(chunk)
    for (pid, a, b), w in zip(chunk, winners):
        s = inv.get(w)
        out.append((pid, s) if s in (a, b) else None)
    return out


def bt_scores(syms: list[str], wins: list[tuple[str, str]],
              alpha: float = BT_ALPHA, iters: int = BT_ITERS) -> pd.Series:
    """log Bradley-Terry strength via MM with virtual-opponent prior.

    wins: list of (winner, loser). Each asset gets alpha pseudo-wins and
    alpha pseudo-losses vs a fixed unit-strength virtual opponent.
    """
    idx = {s: i for i, s in enumerate(syms)}
    n = len(syms)
    w = np.zeros(n)
    games = np.zeros((n, n))
    for a, b in wins:
        w[idx[a]] += 1.0
        games[idx[a], idx[b]] += 1.0
        games[idx[b], idx[a]] += 1.0
    p = np.ones(n)
    for _ in range(iters):
        denom = (games / (p[:, None] + p[None, :])).sum(axis=1) \
            + 2.0 * alpha / (p + 1.0)
        p_new = (w + alpha) / denom
        p_new /= np.exp(np.mean(np.log(p_new)))
        if np.max(np.abs(p_new - p)) < 1e-10:
            p = p_new
            break
        p = p_new
    return pd.Series(np.log(p), index=syms)


def swap_consistency(resolved: list[tuple[int, str, int]]) -> tuple[float, float]:
    """From base-run resolved instances (pair_id, winner_sym, order in {1,2}):
    (consistency rate over pairs with both orders resolved, slot-1 pick rate).

    Slot-1 rate needs the instance's first-slot symbol, so `resolved` rows
    are (pair_id, winner_sym, first_slot_sym) with order implied by caller;
    see p0 script. Here: consistency over pair_ids seen exactly twice.
    """
    by_pair: dict[int, list[str]] = {}
    slot1 = 0
    for pid, winner, first in resolved:
        by_pair.setdefault(pid, []).append(winner)
        slot1 += int(winner == first)
    both = [v for v in by_pair.values() if len(v) == 2]
    cons = float(np.mean([v[0] == v[1] for v in both])) if both else np.nan
    rate1 = slot1 / len(resolved) if resolved else np.nan
    return cons, rate1

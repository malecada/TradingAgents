"""llm_c3p_pair_xs P0 — order-swap kill-probe + stability (charter §5).

8 seeded dev weeks (seed 20260817). Base run contains BOTH orders of every
pair, so the order-swap probe (P0b, the C3 killer) is computed from the
base run itself. Subsets: 3 weeks cache-bypassed identical rerun (P0a),
3 disjoint weeks re-shuffled/re-chunked prompts (P0c). P0d = cost
checkpoint (infra, not a result gate).

Gates (frozen in data/llm_pair_xs/gates.json):
  P0b pooled swap-consistency >= 0.60 AND per-week >= 0.55 in >= 6/8
      AND slot-1 pick rate in [0.35, 0.65]
  P0a instance agreement >= 0.90 AND weekly BT-score Spearman >= 0.90
  P0c instance agreement >= 0.80 AND weekly BT-score Spearman >= 0.80
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.xsect.pair_xs import (  # noqa: E402
    DUELS_PER_PROMPT, K_ROUNDS, bt_scores, build_prompt, chunk_instances,
    make_instances, parse_verdicts, sample_pairs, swap_consistency,
    week_seed, week_tags)

OUT = Path("data/llm_pair_xs")
CACHE = OUT / "duel_call_cache.json"
RESULT = OUT / "p0_swap_stability.json"
LEDGER = OUT / "trial_ledger.jsonl"
MODEL = "gpt-5.4-mini"
DEV_END = pd.Timestamp("2025-03-31", tz="UTC")
N_WEEKS = 8
SEED = 20260817
WORKERS = 8
# cost-checkpoint assumption only (no authoritative mini price in repo);
# verify against billing dashboard before P2
PRICE_IN, PRICE_OUT = 0.30, 1.20  # USD per 1M tokens
SPEND_CAP = 150.0

usage = {"prompt_tokens": 0, "completion_tokens": 0, "fresh_calls": 0,
         "fresh_instances": 0}


def call_chunk(client, chunk, wk_cards, tags, cache, prefix):
    prompt = build_prompt(chunk, wk_cards, tags)
    key = prefix + "|" + hashlib.sha256(prompt.encode()).hexdigest()[:16]
    if key in cache:
        winners = cache[key]
    else:
        r = client.chat.completions.create(
            model=MODEL, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}])
        try:
            winners = json.loads(r.choices[0].message.content).get("winners", [])
        except (json.JSONDecodeError, TypeError):
            winners = []
        cache[key] = winners
        usage["prompt_tokens"] += r.usage.prompt_tokens
        usage["completion_tokens"] += r.usage.completion_tokens
        usage["fresh_calls"] += 1
        usage["fresh_instances"] += len(chunk)
    return chunk, parse_verdicts(chunk, winners, tags)


def run_week(client, wk_cards, date, cache, prefix, inst_seed_variant="base"):
    """One full week (both orders). Returns (bt, resolved, resolution_rate).

    resolved rows: (pair_id, winner_sym, first_slot_sym).
    inst_seed_variant only re-shuffles/re-chunks the SAME instances (P0c).
    """
    seed = week_seed(date, "base")  # pairs + tags identical across variants
    syms = sorted(wk_cards["symbol"].tolist())
    pairs = sample_pairs(syms, seed, K_ROUNDS)
    inst_seed = seed if inst_seed_variant == "base" else week_seed(date, inst_seed_variant)
    instances = make_instances(pairs, inst_seed)
    tags = week_tags(syms, seed)
    chunks = chunk_instances(instances, DUELS_PER_PROMPT)
    resolved, n_inst = [], 0
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(call_chunk, client, ch, wk_cards, tags, cache, prefix)
                for ch in chunks]
        for f in futs:
            chunk, verdicts = f.result()
            n_inst += len(chunk)
            for (pid, a, _b), v in zip(chunk, verdicts):
                if v is not None:
                    resolved.append((pid, v[1], a))
    wins = []
    by_pid = {}
    for pid, w, _first in resolved:
        by_pid.setdefault(pid, []).append(w)
    for pid, ws in by_pid.items():
        a, b = pairs[pid]
        for w in ws:
            wins.append((w, b if w == a else a))
    bt = bt_scores(syms, wins)
    return bt, resolved, len(resolved) / max(1, n_inst)


def agreement(res_a, res_b):
    """Instance-verdict agreement over instances resolved in both runs,
    keyed by (pair_id, first_slot_sym)."""
    da = {(pid, first): w for pid, w, first in res_a}
    db = {(pid, first): w for pid, w, first in res_b}
    common = set(da) & set(db)
    if not common:
        return float("nan")
    return float(np.mean([da[k] == db[k] for k in common]))


def main() -> int:
    if RESULT.exists():
        print(f"{RESULT} exists — refusing to overwrite (stop rule)")
        return 1
    from dotenv import load_dotenv
    load_dotenv(".env")
    from openai import OpenAI
    client = OpenAI()

    cards = pd.read_parquet(Path("data/llm_rank_xs") / "cards.parquet")
    cards["date"] = pd.to_datetime(cards["date"], utc=True)
    cards = cards[cards["date"] <= DEV_END]
    rng = np.random.default_rng(SEED)
    dates = sorted(cards["date"].unique())
    weeks = sorted(pd.Timestamp(w) for w in
                   rng.choice(dates, size=N_WEEKS, replace=False))
    sub = rng.permutation(N_WEEKS)
    rerun_weeks = {weeks[i] for i in sub[:3]}   # P0a
    shuf_weeks = {weeks[i] for i in sub[3:6]}   # P0c (disjoint)

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    per_week = []
    for d in weeks:
        wk = cards[cards["date"] == d]
        base_bt, base_res, rr = run_week(client, wk, d, cache, "anon")
        cons, slot1 = swap_consistency(base_res)
        row = {"week": str(d.date()), "n": int(wk["symbol"].nunique()),
               "resolution": rr, "swap_consistency": cons,
               "slot1_rate": slot1}
        if d in rerun_weeks:
            rr_bt, rr_res, _ = run_week(client, wk, d, cache, "anon-rr")
            row["rerun_agreement"] = agreement(base_res, rr_res)
            row["rerun_rho"] = float(spearmanr(base_bt, rr_bt).statistic)
        if d in shuf_weeks:
            sh_bt, sh_res, _ = run_week(client, wk, d, cache, "anon",
                                        inst_seed_variant="shufchunk")
            row["shuffle_agreement"] = agreement(base_res, sh_res)
            row["shuffle_rho"] = float(spearmanr(base_bt, sh_bt).statistic)
        CACHE.write_text(json.dumps(cache))
        per_week.append(row)
        print(row, flush=True)

    # ── P0b (evaluated first: the C3 killer) ──
    all_res_n = sum(1 for w in per_week)  # weeks
    pooled_pairs = [w["swap_consistency"] for w in per_week]
    # pooled = instance-weighted via per-week n? use simple mean of weeks +
    # per-week floor per gates wording ("pooled" = mean over the 8 weeks)
    pooled_cons = float(np.mean(pooled_pairs))
    weeks_ge = sum(1 for c in pooled_pairs if c >= 0.55)
    slot1_all = float(np.mean([w["slot1_rate"] for w in per_week]))
    p0b_pass = pooled_cons >= 0.60 and weeks_ge >= 6 and 0.35 <= slot1_all <= 0.65
    # ── P0a ──
    rr_agr = [w["rerun_agreement"] for w in per_week if "rerun_agreement" in w]
    rr_rho = [w["rerun_rho"] for w in per_week if "rerun_rho" in w]
    p0a_pass = min(rr_agr) >= 0.90 and min(rr_rho) >= 0.90
    # ── P0c ──
    sh_agr = [w["shuffle_agreement"] for w in per_week if "shuffle_agreement" in w]
    sh_rho = [w["shuffle_rho"] for w in per_week if "shuffle_rho" in w]
    p0c_pass = min(sh_agr) >= 0.80 and min(sh_rho) >= 0.80
    verdict = "PASS" if (p0b_pass and p0a_pass and p0c_pass) else "STOP"

    # ── P0d cost checkpoint (infra) ──
    tok_per_inst = ((usage["prompt_tokens"] + usage["completion_tokens"])
                    / max(1, usage["fresh_instances"]))
    inst_per_week = cards.groupby("date")["symbol"].nunique().map(
        lambda n: 2 * (n // 2) * K_ROUNDS)
    p0_cost = (usage["prompt_tokens"] * PRICE_IN
               + usage["completion_tokens"] * PRICE_OUT) / 1e6
    proj_inst = (inst_per_week.sum()            # P2 full dev
                 + 2 * inst_per_week.sample(26, random_state=SEED).sum())  # P1 approx
    proj_cost = p0_cost + proj_inst * tok_per_inst * (
        (usage["prompt_tokens"] * PRICE_IN + usage["completion_tokens"] * PRICE_OUT)
        / max(1, usage["prompt_tokens"] + usage["completion_tokens"])) / 1e6

    res = {"experiment": "llm_c3p_pair_xs", "probe": "P0_swap_stability",
           "weeks": per_week,
           "P0b": {"pooled_swap_consistency": pooled_cons,
                   "weeks_ge_055": weeks_ge, "slot1_rate": slot1_all,
                   "criteria": {"pooled_min": 0.60, "weekly_min": 0.55,
                                "weeks_needed": 6, "slot1_band": [0.35, 0.65]},
                   "pass": p0b_pass},
           "P0a": {"min_agreement": min(rr_agr), "min_rho": min(rr_rho),
                   "criteria": {"agreement_min": 0.90, "rho_min": 0.90},
                   "pass": p0a_pass},
           "P0c": {"min_agreement": min(sh_agr), "min_rho": min(sh_rho),
                   "criteria": {"agreement_min": 0.80, "rho_min": 0.80},
                   "pass": p0c_pass},
           "P0d_cost": {"fresh_calls": usage["fresh_calls"],
                        "fresh_instances": usage["fresh_instances"],
                        "prompt_tokens": usage["prompt_tokens"],
                        "completion_tokens": usage["completion_tokens"],
                        "p0_cost_usd_assumed": round(p0_cost, 2),
                        "projected_total_usd_assumed": round(proj_cost, 2),
                        "price_assumption_per_1M": [PRICE_IN, PRICE_OUT],
                        "cap_usd": SPEND_CAP,
                        "over_cap": proj_cost > SPEND_CAP},
           "verdict": verdict, "n_weeks": all_res_n}
    RESULT.write_text(json.dumps(res, indent=1))

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    row = {"ts_utc": datetime.now(timezone.utc).isoformat(),
           "experiment": "llm_c3p_pair_xs", "cell": "P0_swap_stability",
           "model": MODEL,
           "config": {"weeks": N_WEEKS, "k_rounds": K_ROUNDS,
                      "duels_per_prompt": DUELS_PER_PROMPT, "seed": SEED},
           "config_hash": "p0-swap-stability",
           "git_commit": commit + ("-dirty" if dirty else ""),
           "window": ["2021-01-01", "2025-03-31"],
           "metrics": {"pooled_swap_consistency": pooled_cons,
                       "slot1_rate": slot1_all,
                       "min_rerun_agreement": min(rr_agr),
                       "min_shuffle_agreement": min(sh_agr),
                       "verdict": verdict}}
    with LEDGER.open("a") as f:
        f.write(json.dumps(row) + "\n")
    print(f"P0 verdict: {verdict} | swap {pooled_cons:.3f} slot1 {slot1_all:.3f} "
          f"| rerun agr {min(rr_agr):.3f} rho {min(rr_rho):.3f} "
          f"| shuffle agr {min(sh_agr):.3f} rho {min(sh_rho):.3f} "
          f"| P0 ${p0_cost:.2f}, projected ${proj_cost:.0f} (assumed pricing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

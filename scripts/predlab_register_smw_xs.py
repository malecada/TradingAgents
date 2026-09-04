"""Freeze the smw_xs registration (predlab_smw_xs). Refuses if the key exists
or if any feature / result artefact already exists (pre-result guard).
Embeds the outcome-free dry-enumeration figures and the feasibility probe."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.predlab import registry  # noqa: E402

SMW = PROJECT_ROOT / "data" / "predlab" / "smw"


def enumeration_facts() -> dict:
    tm = json.loads((SMW / "token_map.json").read_text())
    uni = json.loads((SMW / "universe.json").read_text())
    breadth = pd.Series({m: len(v) for m, v in uni.items()}).sort_index()
    dev = breadth[breadth.index < "2025-04-01"]
    probe = json.loads((SMW / "probe_feasibility.json").read_text())
    pools = json.loads((SMW / "pools.json").read_text())["by_symbol"]
    return {"mapping_how_counts": tm["how_counts"], "n_mapped": sum(1 for v in tm["map"].values() if v.get("address")),
            "n_pools": sum(len(v) for v in pools.values()),
            "breadth_dev_median": float(dev.median()), "breadth_dev_min": int(dev.min()),
            "breadth_dev_max": int(dev.max()), "breadth_first_months": {k: int(v) for k, v in dev.head(6).items()},
            "breadth_floor_40": "PASS" if dev.median() >= 40 else "ABORT",
            "feasibility_probe": {k: probe[k] for k in ("month", "n_pools", "logs", "wall", "projected_logs",
                                                         "projected_store_gb", "projected_hours", "verdict")}}


def entry(facts: dict) -> dict:
    return {
        "registered_utc": "2026-09-04",
        "charter": "docs/superpowers/specs/2026-09-04-smw-xs-charter.md",
        "purpose": "smart-money wallet features (PIT, DEX swap logs) on perp-listed mainnet ERC-20s carry cross-sectional next-24h / 7d rank information (T7 battery); transfer test of the nlst3 T1 channel to a liquid shortable universe",
        "parents": "predlab_nlst3 (75, T1 PASS IC +0.136 on day-old pools, T2 FAIL), predlab_p2_t7 (55, universe + IC battery)",
        "decisions_afk_grant": {"data": "DEX Swap logs only (Uniswap v2 + v3, quotes WETH/USDC/USDT, v3 fees 100/500/3000/10000); ERC-20 Transfer logs excluded",
                                "breadth_floor": 40, "sequencing": "run now, concurrently with nlst4; nlst4 wallet ledger NOT an input",
                                "wallet_identity": "swap recipient; contracts excluded via eth_getCode on wallets with >=5 net-buy days plus top-2000 by gross",
                                "mapping": "Binance-spot rule first, CoinGecko symbol fallback for dead tokens; see charter"},
        "universe": {"base": "monthly PIT top-200 perps (predlab_t7.monthly_universe)", "mapped_erc20": True,
                     "depth_rule": "sum over enumerated pools of 2 x quote balance x price at month-start block >= $250k, stablecoin perps excluded; pools fetched if >= $10k",
                     "rescope_pre_registration": "scoping cut $1M gave dev median breadth 30 (min 15, 47/51 months < 40) = abort condition; lowered to $250k (median 48, min 25) on 2026-09-04 before any swap log was read; $1M subset kept as forensic slice 6",
                     "dev_window": ["2021-01-01", "2025-03-31"], "eval_start_rule": "first day with >= 100 qualified wallets (disclosed, not chosen)",
                     "min_breadth_per_day": 20, **facts},
        "track_record": "episode = (wallet, token, day) with net_buy_usd > 0 in universe; ret7 = close[d+7]/close[d]-1; record = expanding mean over episodes completed strictly before t; qualified >= 5; smart = record >= 80th pct of qualified (daily)",
        "features_frozen": {"f1": "+ smart net-buy share (sum net_buy over smart buyers / total gross over all recipients)",
                            "f2": "+ smart buyer breadth (count)", "f3": "- smart net-sell share",
                            "f4": "+ log(distinct non-contract buyers d / mean over d-7..d-1)",
                            "composite": "equal-weight mean of pre-signed daily cross-sectional z, >= 3 of 4"},
        "alignment": "features from UTC day d swaps -> shifted one row -> scored against T7 target row d+1 (ret_24h = log close diff; ret_7d = 7-day rolling sum shifted -6); NW lag 5 / 10",
        "protocol": "T7 battery verbatim: daily Spearman IC (xsec.daily_ic, min breadth 20), NW-t, sub-periods 2021-2022 / 2023-2024 / 2025Q1; BH-FDR q=0.10 over 10 tests (4 features x 2 horizons + composite x 2); every row to the ledger",
        "T1_gate": {"rule": "composite mean IC >= +0.02 AND NW-t >= 3 AND BH-adjusted p < 0.05 AND positive mean IC in >= 2 of 3 sub-periods, at 24h or 7d",
                    "fail": "family CLOSED for the perp universe; no re-signing / new features / re-weighting / universe re-cut"},
        "P1": "on T1 PASS only; two pre-declared constructions both run (long-only top quintile vs EW smw basket; quintile L/S); 5 bp + funding; net SR >= 1.0, dual placebo 500 draws p <= 0.05, dSR vs basket > 0 for (a), 2x cost stress, convention swap; DSR at n=2 + cumulative; then STOP-AND-DECIDE",
        "holdout": "H2 2025-04-01..2026-07-01, price panel observed by prior programs, on-chain features virgin; H2 universe enumeration only after a user decision; one-shot",
        "forensics_declared": ["momentum-control partial IC (trailing 7d/30d)", "timing canary (contemporaneous and +1 extra lag)",
                               "contract share of gross volume", "coverage per month", "power (IC SE)",
                               "depth slice: >= $1M names vs $250k-$1M band"],
        "mechanics": "scripts/predlab_smw_{map,pools,depth,fetch,features,p0}.py; tests/predlab/test_smw.py; data/predlab/smw/; transport tradingagents/predlab/rpc_pool.py; ledger predlab_smw_xs; THESIS section 82",
        "stop_rule": "no change to features, signs, thresholds, universe rule or alignment after any feature is joined to a return; p0 script refuses to run twice",
    }


def main() -> None:
    gates = registry.load_gates()
    if "predlab_smw_xs" in gates:
        raise SystemExit("predlab_smw_xs already registered")
    for f in ("features.parquet", "p0_result.json"):
        if (SMW / f).exists():
            raise SystemExit(f"pre-result guard: {f} exists")
    facts = enumeration_facts()
    if facts["breadth_floor_40"] != "PASS" or facts["feasibility_probe"]["verdict"] != "GO":
        raise SystemExit(f"registration blocked: {facts}")
    gates["predlab_smw_xs"] = entry(facts)
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print("gates.json['predlab_smw_xs'] written")
    print(json.dumps(facts, indent=1))


if __name__ == "__main__":
    main()

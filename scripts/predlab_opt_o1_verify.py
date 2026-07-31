"""O-02b — adoption verification for the stage-O1 top candidate (ewma_20).

Runs the remaining predlab_opt adoption-rule gates + forensic kill-tests:
  1. dual-family placebos (200 time-shift + 200 xsect-shuffle) on the FULL
     window net SR
  2. DSR at n_trials = 16 prior strategy trials (13 pp + 3 pp2) + 11 O1
  3. lag-direction canary: unshifted (future-peeking) signal must beat the
     shifted one materially (harness can detect timing)
  4. cost-off sanity: gross SR >= net SR
  5. coverage audit: traded days + names/day with honest denominators

Writes data/predlab/opt_o1_verify.json. Idempotent: refuses to overwrite.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from tradingagents.predlab import opt, pp  # noqa: E402

DATA_ROOT = Path(os.environ.get("TRADINGAGENTS_DATA_ROOT", PROJECT_ROOT / "data"))
OUT = DATA_ROOT / "predlab" / "opt_o1_verify.json"
FULL = ("2021-01-01", "2026-07-01")
CANDIDATE = "ewma_20"
N_DRAWS = 200


def main() -> None:
    if OUT.exists():
        print(f"verify results exist ({OUT}) — refusing to overwrite")
        sys.exit(1)
    from predlab_opt_o1 import inputs

    close, park, ret, uni, fund = inputs()
    cfg = opt.OptConfig()
    sig = opt.build_signal(park, close, CANDIDATE)

    def sr_of(s: pd.DataFrame) -> float:
        return opt.run_ls(s, ret, uni, fund, cfg, *FULL)["sr_net"]

    r = opt.run_ls(sig, ret, uni, fund, cfg, *FULL)
    real = r["sr_net"]
    res = {"candidate": CANDIDATE, "real_sr_full": real}

    # 3. lag-direction canary (cheap, run first)
    sig_peek = park.ewm(span=20).mean()  # NO shift -> uses day-t range info
    peek = sr_of(sig_peek)
    res["canary_unshifted_sr"] = peek
    res["canary_ok"] = bool(peek > real + 0.25)
    print(f"canary: unshifted {peek:+.3f} vs real {real:+.3f} ok={res['canary_ok']}",
          flush=True)

    # 4. cost-off sanity
    res["sr_gross"] = r["sr_gross"]
    res["cost_sanity_ok"] = bool(r["sr_gross"] >= r["sr_net"])

    # 5. coverage audit
    df = r["rets"]
    idx = ret.index
    expected = int(((idx >= pd.Timestamp(FULL[0], tz="UTC"))
                    & (idx <= pd.Timestamp(FULL[1], tz="UTC"))).sum())
    names_per_day = (~sig.where(uni).isna()).sum(axis=1)
    npd = names_per_day[(names_per_day.index >= FULL[0]) & (names_per_day.index <= FULL[1])]
    res["coverage"] = {"traded_days": int(len(df)), "calendar_days": expected,
                      "names_per_day_min": int(npd.min()),
                      "names_per_day_median": float(npd.median())}
    print(f"coverage: {len(df)}/{expected} days, names/day min {npd.min()} "
          f"median {npd.median():.0f}", flush=True)

    # 1. placebos
    rng = np.random.default_rng(7)
    n = len(sig)
    fam_a = []
    for i in range(N_DRAWS):
        k = int(rng.integers(30, n - 30))
        fam_a.append(sr_of(pd.DataFrame(np.roll(sig.to_numpy(), k, axis=0),
                                        index=sig.index, columns=sig.columns)))
        if (i + 1) % 25 == 0:
            print(f"fam_a {i+1}/{N_DRAWS}", flush=True)
    fam_b = []
    for d in range(N_DRAWS):
        rngb = np.random.default_rng(1000 + d)
        vals = sig.to_numpy().copy()
        for i in range(vals.shape[0]):
            row = vals[i]
            ok = ~np.isnan(row)
            row[ok] = rngb.permutation(row[ok])
        fam_b.append(sr_of(pd.DataFrame(vals, index=sig.index, columns=sig.columns)))
        if (d + 1) % 25 == 0:
            print(f"fam_b {d+1}/{N_DRAWS}", flush=True)
    res["p_shift"] = pp.placebo_pvalue(real, fam_a)
    res["p_xshuffle"] = pp.placebo_pvalue(real, fam_b)
    res["placebo_null_max"] = {"shift": float(np.max(fam_a)),
                               "xshuffle": float(np.max(fam_b))}
    print(f"placebos: p_shift {res['p_shift']:.4f} p_xshuffle {res['p_xshuffle']:.4f}",
          flush=True)

    # 2. DSR at cumulative trials
    o1 = json.loads((DATA_ROOT / "predlab" / "opt_o1_results.json").read_text())
    ppd = json.loads((DATA_ROOT / "predlab" / "pp_dev_results.json").read_text())
    pp2 = json.loads((DATA_ROOT / "predlab" / "pp2_dev_results.json").read_text())
    trials = [v["sr_net"] for v in ppd["S1"].values()]
    trials += [v["sr_net"] for v in ppd["S2"].values()]
    trials += [v["sr_net"] for v in ppd["S3"].values()]
    trials += [pp2[k]["sr_net"] for k in ("vt10", "vt15", "vt20")]
    trials += [v["sr_net_full"] for v in o1["configs"].values()]
    res["n_trials"] = len(trials)
    res["dsr"] = pp.dsr(real, trials, r["n_days"], df["net"].to_numpy())
    print(f"DSR {res['dsr']:.3f} at n_trials={len(trials)}", flush=True)

    res["adopt"] = bool(res["canary_ok"] and res["cost_sanity_ok"]
                        and res["p_shift"] < 0.05 and res["p_xshuffle"] < 0.05
                        and res["dsr"] > 0.5)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"ADOPT={res['adopt']} written {OUT}", flush=True)


if __name__ == "__main__":
    main()

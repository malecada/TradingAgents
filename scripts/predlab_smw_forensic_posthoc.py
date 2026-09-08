"""smw_xs POST-HOC mechanism forensic (after the T1 verdict; disclosed, not a gate).

Question: is the negative IC of the smart-money features (f1/f2, NW-t ≈ −2.2)
smart-wallet information or plain DEX-activity reversal? Compares the T7 IC
of raw activity measures (all-wallet buyer breadth, gross DEX USD volume,
DEX/CEX volume ratio, the known CEX volume-change factor) with the registered
features, and the two partial ICs (f2 | n_buyers, n_buyers | f2). Nothing
here is a claim; every number is dev-window, post-verdict, exploratory.
Output: data/predlab/smw/forensic_posthoc.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_smw_p0 import residualize, score, universe_mask  # noqa: E402

SMW = ROOT / "data" / "predlab" / "smw"
PANELS = ROOT / "data" / "predlab" / "t7_panels"


def main() -> None:
    assert (SMW / "p0_result.json").exists(), "post-hoc forensic runs only after the verdict"
    F = pd.read_parquet(SMW / "features.parquet")
    universe = json.loads((SMW / "universe.json").read_text())
    close = pd.read_parquet(PANELS / "close.parquet")
    close = close[(close.index >= "2020-12-01") & (close.index <= "2025-03-31")]
    syms = sorted(set(F["sym"]) & set(close.columns))
    close = close[syms]
    uni = universe_mask(universe, close.index, syms)
    ret = np.log(close).diff()
    qv = pd.read_parquet(PANELS / "qv.parquet").reindex(index=close.index, columns=syms)
    start = pd.Timestamp(json.loads((SMW / "p0_result.json").read_text())["eval_window"][0], tz="UTC")

    def P(col):
        return F.pivot(index="date", columns="sym", values=col).reindex(index=close.index, columns=syms).shift(1)

    cands = {"n_buyers_all": np.log1p(P("n_buyers")), "gross_usd": np.log1p(P("gross_total")),
             "f2_smart_buyers": P("f2"), "f1_smart_share": P("f1"),
             "dex_gross_over_cex_qv": np.log((P("gross_total") + 1) / (qv.shift(1) + 1)),
             "cex_volchg_5": np.log(qv.shift(1)) - np.log(qv.shift(2).rolling(5).mean())}
    y24 = ret[ret.index >= start].where(uni)
    y7 = ret.rolling(7).sum().shift(-6)[ret.index >= start].where(uni)
    out = {"note": "post-hoc, dev-window, exploratory; not a claim", "eval_start": str(start.date()), "ics": {}}
    for k, s in cands.items():
        s = s[s.index >= start].where(uni)
        out["ics"][k] = {"ret_24h": score(s, y24, 5), "ret_7d": score(s, y7, 10)}
        a, b = out["ics"][k]["ret_24h"], out["ics"][k]["ret_7d"]
        print(f"{k:24s} 24h ic={a['mean_ic']:+.4f} t={a['nw_t']:+.2f} | 7d ic={b['mean_ic']:+.4f} t={b['nw_t']:+.2f}", flush=True)
    f2 = cands["f2_smart_buyers"][cands["f2_smart_buyers"].index >= start].where(uni)
    nb = cands["n_buyers_all"][cands["n_buyers_all"].index >= start].where(uni)
    out["partial"] = {"f2_given_n_buyers_24h": score(residualize(f2, [nb]), y24, 5),
                      "n_buyers_given_f2_24h": score(residualize(nb, [f2]), y24, 5)}
    for k, v in out["partial"].items():
        print(f"{k:24s} ic={v['mean_ic']:+.4f} t={v['nw_t']:+.2f}", flush=True)
    (SMW / "forensic_posthoc.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()

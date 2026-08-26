"""nlst P0 — perp cells: nlst_bin, nlst_byb, nlst_x (on-disk stores only).

Charter: docs/superpowers/specs/2026-08-26-newlist-charter.md (frozen).
Computes per-event funding-adjusted cum returns and the P0 stat blocks for
the 8 perp-side tests (bin 5/10/20d, byb 5/10/20d, x 5/10d). Verdicts are
NOT assigned here — BH-FDR q<0.10 runs across all 11 tests (incl. dex) in
predlab_nlst_p0_verdict.py once the dex cell is computed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_nlst_lib import (  # noqa: E402
    DEV, HORIZONS_PERP, HORIZONS_X, OUT_DIR,
    daily_funding, event_cum_returns, ledger_append, listing_events,
    p0_stats, write_result,
)

BIN_K = ROOT / "data" / "xsect" / "klines"
BIN_F = ROOT / "data" / "xsect" / "funding"
BYB_K = ROOT / "data" / "predlab" / "bybit" / "klines"
BYB_F = ROOT / "data" / "predlab" / "bybit" / "funding"


def excluded_syms(venue: str) -> set[str]:
    """Store-artifact events (first bar >7d after exchange launch metadata) —
    pre-result amendment in gates.json['predlab_nlst']['data_quality_result']."""
    import json

    nd = ROOT / "data" / "predlab" / "nlst"
    files = {"bin": ["binance_onboard_diff.json"],
             "byb": ["bybit_launchtime_diff.json",
                     "bybit_launchtime_diff_closed.json"]}[venue]
    out = set()
    for f in files:
        d = json.loads((nd / f).read_text())
        out |= {s for s, v in d.items() if abs(v) > 7}
    return out


def event_table(kdir: Path, fdir: Path, horizons, venue: str) -> pd.DataFrame:
    ev = listing_events(kdir, max_h=max(horizons))
    ev = ev.drop(index=excluded_syms(venue) & set(ev.index))
    rows = {}
    for sym, r in ev.iterrows():
        close = pd.read_parquet(kdir / f"{sym}.parquet", columns=["close"])["close"]
        rows[sym] = {"list_date": r["list_date"],
                     **event_cum_returns(close, daily_funding(fdir, sym),
                                         horizons=horizons)}
    return pd.DataFrame.from_dict(rows, orient="index").sort_values("list_date")


def x_event_table() -> pd.DataFrame:
    """Cross-venue: Binance listing (dev) of symbol on Bybit >=30d earlier.
    Entry close of Binance-listing day 0 on Bybit bars; horizons on Bybit."""
    evB = listing_events(BIN_K, max_h=max(HORIZONS_X))
    evB = evB.drop(index=excluded_syms("bin") & set(evB.index))
    rows = {}
    for sym, r in evB.iterrows():
        pk = BYB_K / f"{sym}.parquet"
        if not pk.exists():
            continue
        close = pd.read_parquet(pk, columns=["close"])["close"]
        lday = r["list_date"].floor("D")
        pre = close[close.index < lday]
        if len(pre) < 30:
            continue
        # entry bar = Bybit bar of the Binance listing day (close is post-news)
        sub = close[close.index >= lday]
        if len(sub) == 0 or sub.index[0] != lday:
            continue
        anchored = pd.concat([pre.iloc[-1:], sub])  # bar0=prev day, bar1=day0
        rows[sym] = {"list_date": r["list_date"],
                     **event_cum_returns(anchored, daily_funding(BYB_F, sym),
                                         horizons=HORIZONS_X, entry_bar=1)}
    return pd.DataFrame.from_dict(rows, orient="index").sort_values("list_date")


def run_cell(cell: str, tab: pd.DataFrame, horizons) -> dict:
    stats = {}
    for h in horizons:
        st = p0_stats(tab, f"ret{h}")
        px = p0_stats(tab, f"px{h}")
        st["price_only_mean"] = px["mean"]
        st["funding_mean"] = float(tab[f"fund{h}"].mean())
        stats[f"{cell}_{h}d"] = st
        ledger_append(f"predlab_nlst_{cell}", cell=f"{h}d", model="event_study",
                      config={"horizon": h, "entry": "close_bar1",
                              "funding_adj": True, "window": list(DEV)},
                      metrics={k: v for k, v in st.items()
                               if not isinstance(v, dict)})
    per_year = {h: tab.groupby(tab["list_date"].dt.year)[f"ret{h}"]
                .agg(["count", "mean", "median"]).round(4).to_dict("index")
                for h in horizons}
    return {"stats": stats, "per_year_descriptive": per_year}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tabs = {
        "bin": event_table(BIN_K, BIN_F, HORIZONS_PERP, "bin"),
        "byb": event_table(BYB_K, BYB_F, HORIZONS_PERP, "byb"),
        "x": x_event_table(),
    }
    for cell, tab in tabs.items():
        tab.to_parquet(OUT_DIR / f"{cell}_events.parquet")
        horizons = HORIZONS_X if cell == "x" else HORIZONS_PERP
        payload = run_cell(cell, tab, horizons)
        payload["n_events"] = int(len(tab))
        p = write_result(f"{cell}_p0", payload)
        print(f"{cell}: n={len(tab)} -> {p}")
        for name, st in payload["stats"].items():
            print(f"  {name}: n={st['n']} mean={st['mean']:+.4f} "
                  f"t={st['nw_t']:+.2f} p={st['nw_p']:.4f} "
                  f"med={st['median']:+.4f} sign_p={st['sign_p']:.4f} "
                  f"top_share={st['concentration']['top_share']:.2f}")


if __name__ == "__main__":
    main()

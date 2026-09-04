"""DefiLlama fees/revenue snapshot for the value_rev cycle (charter 2026-09-04).

  python scripts/fetch_defillama_fees.py --snapshot 2026-09-04

Vintage-stamped: raw per-protocol responses are kept under
data/xsect/fees_raw/{snapshot}/ (sha256 manifest), the per-symbol daily panel
under data/xsect/fees/{snapshot}/{SYMBOL}.parquet (fees_usd, revenue_usd,
n_protocols). A second snapshot >= 14 days later feeds the P0 restatement probe;
snapshots are never overwritten.

Mapping: /protocols gives slug -> symbol; a protocol maps to the perp base
{SYMBOL}USDT (or 1000{SYMBOL}USDT) present in the 799-symbol daily store.
Several protocols may share a symbol (aave-v2/v3 -> AAVE): fees are summed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
KL = ROOT / "data/xsect/klines"
RAW = ROOT / "data/xsect/fees_raw"
OUT = ROOT / "data/xsect/fees"
OVERVIEW = "https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"
PROTOCOLS = "https://api.llama.fi/protocols"
SUMMARY = "https://api.llama.fi/summary/fees/{slug}?dataType={dt}"
SLEEP = 0.25
EXCLUDE_SYMBOLS = {"USDT", "USDC", "DAI", "BUSD", "TUSD", "USDD", "FRAX", "WBTC", "WETH", "STETH", "WSTETH", "RETH", "CBETH", "-", ""}


def _get(url: str, retries: int = 4) -> requests.Response | None:
    for i in range(retries):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r
            if r.status_code == 404:
                return r
        except requests.RequestException:
            pass
        time.sleep(2.0 * (i + 1))
    return None


def perp_symbols() -> set[str]:
    return {p.stem for p in KL.glob("*.parquet")}


def map_symbol(sym: str, perps: set[str]) -> str | None:
    s = sym.upper()
    for cand in (f"{s}USDT", f"1000{s}USDT"):
        if cand in perps:
            return cand
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", required=True, help="YYYY-MM-DD vintage label")
    args = ap.parse_args()
    raw_dir, out_dir = RAW / args.snapshot, OUT / args.snapshot
    if out_dir.exists():
        raise SystemExit(f"{out_dir} exists -- snapshots are never overwritten")
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"snapshot": args.snapshot, "fetched_utc": pd.Timestamp.utcnow().isoformat(), "files": {}, "mapping": {}}

    def save(name: str, content: bytes) -> None:
        (raw_dir / name).write_bytes(content)
        manifest["files"][name] = {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}

    ov = _get(OVERVIEW)
    save("overview_fees.json", ov.content)
    pr = _get(PROTOCOLS)
    save("protocols.json", pr.content)
    fee_protocols = json.loads(ov.content)["protocols"]
    plist = {p["slug"]: p for p in json.loads(pr.content)}
    perps = perp_symbols()
    by_symbol: dict[str, list[str]] = {}
    for f in fee_protocols:
        meta = plist.get(f["slug"])
        if not meta:
            continue
        sym = (meta.get("symbol") or "").upper()
        if sym in EXCLUDE_SYMBOLS:
            continue
        perp = map_symbol(sym, perps)
        if perp is None:
            continue
        by_symbol.setdefault(perp, []).append(f["slug"])
    manifest["mapping"] = by_symbol
    print(f"{len(fee_protocols)} fee protocols; {sum(len(v) for v in by_symbol.values())} mapped to {len(by_symbol)} perp symbols", flush=True)

    t0 = time.time()
    for i, (perp, slugs) in enumerate(sorted(by_symbol.items())):
        frames = []
        for slug in slugs:
            cols = {}
            for dt in ("dailyFees", "dailyRevenue"):
                r = _get(SUMMARY.format(slug=slug, dt=dt))
                time.sleep(SLEEP)
                if r is None or r.status_code != 200:
                    continue
                save(f"{slug}__{dt}.json", r.content)
                chart = json.loads(r.content).get("totalDataChart") or []
                if chart:
                    s = pd.Series({pd.Timestamp(int(ts), unit="s", tz="UTC"): float(v) for ts, v in chart})
                    cols["fees_usd" if dt == "dailyFees" else "revenue_usd"] = s
            if cols:
                df = pd.DataFrame(cols)
                df["slug"] = slug
                frames.append(df)
        if not frames:
            continue
        allp = pd.concat(frames)
        panel = allp.groupby(allp.index).agg(fees_usd=("fees_usd", "sum"), revenue_usd=("revenue_usd", "sum"),
                                              n_protocols=("slug", "nunique")).sort_index()
        panel.index.name = "ts"
        panel.to_parquet(out_dir / f"{perp}.parquet")
        print(f"[{i+1}/{len(by_symbol)}] {perp}: {len(slugs)} protocols, {len(panel)} days "
              f"({panel.index.min().date()} -> {panel.index.max().date()}) t={time.time()-t0:.0f}s", flush=True)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"done -> {out_dir}")


if __name__ == "__main__":
    main()

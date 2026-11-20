"""Event-time study: is the direction read by the agents still tradable minutes after a news item appears?

The six attempts of family ``llm-multiagent-v2`` decided once a day or once a week, about ten hours or more
after the news. This module asks the question at the time of the news. An event is one fact record of the
reader agents (Charter 2 instructions, records of Charters 2 and 5) with a direction, placed at the
publication time of its document. The outcome is the return of the asset's perpetual contract minus the
return of the market contract over a window that starts a fixed number of minutes after the event.

Three parts. ``event_table`` and ``mark_leads`` use text stores and records only. ``event_returns`` is the
single join with minute bars. ``evaluate`` computes the registered gate and the descriptive tables by code.
Returns are simple returns of bar open prices; no model is called.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

SIGN = {"favourable": 1, "unfavourable": -1}
MARKET = "BTC"
TEST_START, TEST_END = pd.Timestamp("2023-01-01", tz="UTC"), pd.Timestamp("2025-01-01", tz="UTC")
ENTRY_LAGS = (0, 1, 5, 15, 60)          # minutes between the event clock and the entry
HORIZONS = (15, 60, 240, 1440)          # minutes held after the entry
PRE_WINDOWS = (1440, 240, 60, 15)       # minutes before the event clock
GATE_LAG, GATE_HORIZON = 5, 240         # the registered cell
HOLD = pd.Timedelta(minutes=GATE_LAG + GATE_HORIZON)
FRESH_GAP = pd.Timedelta(hours=24)
MAX_GAP = pd.Timedelta(minutes=5)       # a price is the open of the first bar at or after a time, at most this late
COST_BP = 10.0                          # one contract in and out at 5 bp per side
T_MIN = 2.0
YEARS = (2023, 2024)
LIVE_LAG = pd.Timedelta(hours=1, seconds=1)   # archive rows observable one hour after publication were ingested live
PUB_SLACK = pd.Timedelta(minutes=5)     # a publication time may exceed the first page capture by at most this
# Not news about one asset: opinions and price forecasts, market-wide items (the outcome is market-relative), rest class
SOFT_CLASSES = ("opinion_or_forecast", "market_wide_or_macro", "other")
EVENT_COLUMNS = ["doc_id", "base", "source", "outlet", "t0", "clock", "sign", "direction", "materiality",
                 "event_class", "status"]
_URL = re.compile(r"^[a-z]+://(www\.)?")


def url_key(url) -> str:
    """Scheme, ``www.``, query, fragment and trailing slash removed; lower case."""
    text = "" if url is None or (isinstance(url, float) and np.isnan(url)) else str(url).strip().lower()
    return _URL.sub("", text).split("?", 1)[0].split("#", 1)[0].rstrip("/")


def publication_times(pages: pd.DataFrame, feed: pd.DataFrame) -> pd.Series:
    """Publication time to the second for page-archive documents, by URL from the news feed.

    ``pages``: doc_id, url, event_ts (publication date), as_of_ts (first capture). ``feed``: url, event_ts
    (publication time, UTC). A time is accepted when the URL matches exactly one feed row, the time is not
    later than the first capture (plus ``PUB_SLACK``) and lies within one day of the stored publication date.
    """
    feed = feed.assign(key=feed["url"].map(url_key))
    feed = feed[(feed["key"] != "") & ~feed["key"].duplicated(keep=False)]
    pages = pages.assign(key=pages["url"].map(url_key)).merge(feed[["key", "event_ts"]].rename(columns={"event_ts": "pub_ts"}),
                                                              on="key", how="inner")
    ok = (pages["pub_ts"] <= pages["as_of_ts"] + PUB_SLACK) & ((pages["pub_ts"] - pages["event_ts"]).abs() <= pd.Timedelta(days=2))
    return pages[ok].drop_duplicates("doc_id").set_index("doc_id")["pub_ts"]


def _records(items: pd.DataFrame, records: pd.DataFrame, source: str) -> pd.DataFrame:
    keys = items[items["source"] == source][["doc_id", "base", "source", "outlet", "event_ts", "as_of_ts"]]
    keys = keys.drop_duplicates(["doc_id", "base"])
    out = records[["doc_id", "base", "direction", "materiality", "event_class", "status"]].merge(
        keys, on=["doc_id", "base"], how="inner", validate="1:1")
    for col in ("event_ts", "as_of_ts"):
        out[col] = pd.to_datetime(out[col], utc=True)
    return out


def event_table(page_items: pd.DataFrame, page_records: pd.DataFrame, feed_items: pd.DataFrame,
                feed_records: pd.DataFrame, pub: pd.Series) -> pd.DataFrame:
    """One row per news record with its event clock. No price is read.

    clock ``publication``: the publication time to the second (feed rows ingested live; page-archive rows
    with a time from ``publication_times``). clock ``capture``: page-archive rows without one, placed at the
    first capture. clock ``late``: feed rows ingested after the fact, placed at their observable time.
    """
    pages = _records(page_items, page_records, "wayback")
    pages["pub_ts"] = pages["doc_id"].map(pub)
    pages["clock"] = np.where(pages["pub_ts"].notna(), "publication", "capture")
    pages["t0"] = pages["pub_ts"].fillna(pages["as_of_ts"])
    feed = _records(feed_items, feed_records, "ccnews")
    live = (feed["as_of_ts"] - feed["event_ts"]) <= LIVE_LAG
    feed["clock"] = np.where(live, "publication", "late")
    feed["t0"] = feed["event_ts"].where(live, feed["as_of_ts"])
    out = pd.concat([pages, feed], ignore_index=True)
    out["sign"] = out["direction"].map(SIGN).fillna(0).astype(int)
    out["t0"] = pd.to_datetime(out["t0"], utc=True).dt.floor("s")
    return out.sort_values(["t0", "doc_id", "base"]).reset_index(drop=True)[EVENT_COLUMNS]


def mark_leads(events: pd.DataFrame) -> pd.DataFrame:
    """Adds ``fresh``, ``lead``, ``n_following`` and ``n_opposed``. No price is read.

    ``fresh``: no news record of any clock or direction on the asset in the ``FRESH_GAP`` before the event.
    ``lead``: a signed publication-clock event of a class outside ``SOFT_CLASSES`` with no earlier lead of the
    same asset inside ``HOLD``; the positions of the lead events of one asset therefore never overlap. ``n_following`` and ``n_opposed``
    count the further such events of the asset inside the lead's ``HOLD`` and those of them with the other sign.
    """
    out = events.sort_values(["base", "t0", "doc_id"]).reset_index(drop=True)
    prev = out.groupby("base")["t0"].shift(1)
    same = out["t0"] == prev
    gap = out["t0"] - prev
    out["fresh"] = prev.isna() | (gap >= FRESH_GAP)
    # rows that share the time of the row before them inherit its flag, so a batch at one time is judged as one
    out["fresh"] = out["fresh"].astype(float).where(~same).groupby(out["base"]).ffill().fillna(1.0).astype(bool)
    lead = np.zeros(len(out), dtype=bool)
    following = np.zeros(len(out), dtype=int)
    opposed = np.zeros(len(out), dtype=int)
    eligible = ((out["sign"] != 0) & (out["clock"] == "publication") & ~out["event_class"].isin(SOFT_CLASSES)).to_numpy()
    t0, sign = out["t0"].to_numpy(), out["sign"].to_numpy()
    for idx in out.groupby("base", sort=False).indices.values():
        head = None
        for i in idx:
            if not eligible[i]:
                continue
            if head is None or t0[i] >= t0[head] + HOLD.to_timedelta64():
                head, lead[i] = i, True
            else:
                following[head] += 1
                opposed[head] += int(sign[i] != sign[head])
    out["lead"], out["n_following"], out["n_opposed"] = lead, following, opposed
    return out.sort_values(["t0", "doc_id", "base"]).reset_index(drop=True)


def symbol_file(klines_dir: Path, base: str) -> Path | None:
    for name in (f"{base}USDT", f"1000{base}USDT"):
        path = Path(klines_dir) / f"{name}.parquet"
        if path.exists():
            return path
    return None


class Bars:
    """Open prices of minute bars; ``price(base, times)`` is the open of the first bar at or after each time."""

    def __init__(self, klines_dir: Path):
        self.dir = Path(klines_dir)
        self._cache: dict[str, tuple[np.ndarray, np.ndarray] | None] = {}

    def has(self, base: str) -> bool:
        return symbol_file(self.dir, base) is not None

    def _load(self, base: str):
        if base not in self._cache:
            path = symbol_file(self.dir, base)
            if path is None:
                self._cache[base] = None
            else:
                frame = pd.read_parquet(path, columns=["open"])
                ts = pd.DatetimeIndex(frame.index).tz_convert("UTC").asi8
                order = np.argsort(ts, kind="stable")
                self._cache[base] = (ts[order], frame["open"].to_numpy(dtype=float)[order])
        return self._cache[base]

    def price(self, base: str, times: pd.DatetimeIndex) -> np.ndarray:
        loaded = self._load(base)
        if loaded is None:
            return np.full(len(times), np.nan)
        ts, px = loaded
        want = pd.DatetimeIndex(times).tz_convert("UTC").as_unit("ns").asi8
        pos = np.searchsorted(ts, want, side="left")
        ok = pos < len(ts)
        out = np.full(len(want), np.nan)
        hit = np.where(ok, pos, 0)
        late = ts[hit] - want
        ok &= late <= MAX_GAP.value
        out[ok] = px[hit[ok]]
        return out

    def drop(self, base: str) -> None:
        self._cache.pop(base, None)


def return_columns() -> list[str]:
    cols = [f"pre_{k}" for k in PRE_WINDOWS] + [f"imm_{d}" for d in ENTRY_LAGS if d]
    return cols + [f"post_{d}_{h}" for d in ENTRY_LAGS for h in HORIZONS]


def _window_returns(bars: Bars, base: str, t0: pd.DatetimeIndex) -> dict[str, np.ndarray]:
    minute = pd.Timedelta(minutes=1)
    p0 = bars.price(base, t0)
    out = {f"pre_{k}": p0 / bars.price(base, t0 - k * minute) - 1.0 for k in PRE_WINDOWS}
    for d in ENTRY_LAGS:
        entry = p0 if d == 0 else bars.price(base, t0 + d * minute)
        if d:
            out[f"imm_{d}"] = entry / p0 - 1.0
        for h in HORIZONS:
            out[f"post_{d}_{h}"] = bars.price(base, t0 + (d + h) * minute) / entry - 1.0
    return out


def event_returns(events: pd.DataFrame, klines_dir: Path) -> pd.DataFrame:
    """THE OUTCOME JOIN. Simple returns around every event, own contract (``r_``) and minus the market (``ar_``).

    ``pre_k``: from k minutes before the event clock to the clock. ``imm_d``: from the clock to d minutes
    after it. ``post_d_h``: from d minutes after the clock to h minutes later. Missing where a bar is missing.
    """
    bars = Bars(klines_dir)
    out = events.reset_index(drop=True).copy()
    t0 = pd.DatetimeIndex(out["t0"])
    cols = return_columns()
    market = _window_returns(bars, MARKET, t0)
    raw = {c: np.full(len(out), np.nan) for c in cols}
    for base, idx in out.groupby("base", sort=True).indices.items():
        if not bars.has(base):
            continue
        got = _window_returns(bars, base, t0[idx])
        for c in cols:
            raw[c][idx] = got[c]
        if base != MARKET:
            bars.drop(base)
    for c in cols:
        out[f"r_{c}"] = raw[c]
        out[f"ar_{c}"] = raw[c] - market[c]
    return out


def clustered(x: np.ndarray, day: np.ndarray) -> dict:
    """Mean of ``x`` with a standard error clustered by ``day`` (sandwich with the small-sample factor)."""
    x, day = np.asarray(x, dtype=float), np.asarray(day)
    keep = np.isfinite(x)
    x, day = x[keep], day[keep]
    n, days = len(x), len(np.unique(day))
    if n < 2 or days < 2:
        return {"n": int(n), "days": int(days), "mean": float(x.mean()) if n else None, "se": None, "t": None}
    mean = x.mean()
    sums = pd.Series(x - mean).groupby(day).sum().to_numpy()
    se = float(np.sqrt((sums ** 2).sum() * days / (days - 1)) / n)
    return {"n": int(n), "days": int(days), "mean": float(mean), "se": se, "t": float(mean / se) if se > 0 else None}


def slope(ret: np.ndarray, sign: np.ndarray, day: np.ndarray, group: np.ndarray) -> dict:
    """Slope of the return on the sign (+1 favourable, -1 unfavourable) with one intercept per ``group``
    (the calendar year), standard error clustered by ``day``.

    The slope is half the difference between the mean return after favourable and after unfavourable events.
    A drift common to all events of a year (most events are favourable, so a plain signed mean would earn
    the average drift of the assets against the market) goes into the intercept and not into the slope.
    """
    ret, sign, day, group = (np.asarray(v) for v in (ret, sign, day, group))
    keep = np.isfinite(ret.astype(float))
    ret, sign, day, group = ret[keep].astype(float), sign[keep].astype(float), day[keep], group[keep]
    n, days = len(ret), len(np.unique(day))
    empty = {"n": int(n), "days": int(days), "mean": None, "se": None, "t": None}
    if n < 3 or days < 2:
        return empty
    frame = pd.DataFrame({"r": ret, "s": sign, "g": group})
    r = (frame["r"] - frame.groupby("g")["r"].transform("mean")).to_numpy()
    s = (frame["s"] - frame.groupby("g")["s"].transform("mean")).to_numpy()
    sxx = float((s ** 2).sum())
    if sxx <= 0:
        return empty
    b = float((s * r).sum() / sxx)
    scores = pd.Series(s * (r - b * s)).groupby(day).sum().to_numpy()
    se = float(np.sqrt((scores ** 2).sum() * days / (days - 1)) / sxx)
    return {"n": int(n), "days": int(days), "mean": b, "se": se, "t": float(b / se) if se > 0 else None}


def gate_set(panel: pd.DataFrame) -> pd.DataFrame:
    """Lead events of the test window on assets other than the market contract."""
    keep = panel["lead"] & (panel["base"] != MARKET) & (panel["t0"] >= TEST_START) & (panel["t0"] < TEST_END)
    return panel[keep]


def _bp(stat: dict) -> dict:
    return {**stat, "mean_bp": None if stat["mean"] is None else 1e4 * stat["mean"],
            "se_bp": None if stat["se"] is None else 1e4 * stat["se"]}


def _slope(panel: pd.DataFrame, column: str) -> dict:
    return _bp(slope(panel[column].to_numpy(dtype=float), panel["sign"].to_numpy(), panel["t0"].dt.floor("D").to_numpy(),
                     panel["t0"].dt.year.to_numpy()))


def _mean(panel: pd.DataFrame, column: str) -> dict:
    return _bp(clustered(panel[column].to_numpy(dtype=float), panel["t0"].dt.floor("D").to_numpy()))


GATE_COLUMN = f"ar_post_{GATE_LAG}_{GATE_HORIZON}"


def gate(panel: pd.DataFrame) -> dict:
    """G1: clustered t of the slope of the registered cell at least ``T_MIN`` and a positive slope.
    G2: positive slope in every year of ``YEARS``. The size reading compares the slope with the cost."""
    g = gate_set(panel)
    total = _slope(g, GATE_COLUMN)
    by_year = {str(y): _slope(g[g["t0"].dt.year == y], GATE_COLUMN) for y in YEARS}
    g1 = total["t"] is not None and total["t"] >= T_MIN and total["mean"] > 0
    g2 = all(v["mean"] is not None and v["mean"] > 0 for v in by_year.values())
    size = None if total["mean"] is None else ("above cost" if total["mean_bp"] >= COST_BP else "below cost")
    return {"cell": GATE_COLUMN, "total": total, "by_year": by_year, "g1": bool(g1), "g2": bool(g2),
            "verdict": "PASS" if g1 and g2 else "FAIL", "size_reading": size, "cost_bp": COST_BP, "t_min": T_MIN}


def permutation(panel: pd.DataFrame, n: int = 1000, seed: int = 20261120) -> dict:
    """Gate t with the signs of the gate events shuffled within the day."""
    g = gate_set(panel)
    g = g[np.isfinite(g[GATE_COLUMN])]
    day, year = g["t0"].dt.floor("D").to_numpy(), g["t0"].dt.year.to_numpy()
    ret, sign = g[GATE_COLUMN].to_numpy(dtype=float), g["sign"].to_numpy()
    observed = slope(ret, sign, day, year)["t"]
    rng = np.random.default_rng(seed)
    codes = pd.factorize(day)[0]
    by_day = np.argsort(codes, kind="stable")
    draws = []
    for _ in range(n):
        shuffled = np.empty_like(sign)
        shuffled[by_day] = sign[np.lexsort((rng.random(len(sign)), codes))]     # a random order inside each day
        t = slope(ret, shuffled, day, year)["t"]
        if t is not None:
            draws.append(t)
    draws = np.array(draws)
    return {"n": len(draws), "observed_t": observed, "sd": float(draws.std()) if len(draws) else None,
            "q975": float(np.quantile(draws, 0.975)) if len(draws) else None,
            "share_at_or_above": float((draws >= observed).mean()) if len(draws) and observed is not None else None}


def path_table(panel: pd.DataFrame) -> dict:
    """Slope of the market-relative return on the sign before, right after and after the event, and the share
    of the whole move from one day before to one day after that is done before the registered entry."""
    out = {c: _slope(panel, f"ar_{c}") for c in return_columns()}
    pre, first, later = (out["pre_1440"]["mean_bp"], out[f"imm_{GATE_LAG}"]["mean_bp"], out[f"post_{GATE_LAG}_1440"]["mean_bp"])
    share = None
    if None not in (pre, first, later) and pre + first + later > 0:
        share = (pre + first) / (pre + first + later)
    return {"cells": out, "share_done_before_entry": share}


def evaluate(panel: pd.DataFrame, n_placebo: int = 1000) -> dict[str, dict]:
    """Registered outputs. ``panel`` is ``event_returns(mark_leads(event_table(...)))``."""
    g = gate_set(panel)
    verdict = gate(panel)
    in_window = (panel["t0"] >= TEST_START) & (panel["t0"] < TEST_END) & (panel["base"] != MARKET)
    rows = panel[in_window & (panel["sign"] != 0)]
    published = rows[rows["clock"] == "publication"]
    splits = {
        "fresh": g[g["fresh"]], "not_fresh": g[~g["fresh"]],
        "materiality_2_3": g[g["materiality"] >= 2], "materiality_1": g[g["materiality"] == 1],
        "status_occurred": g[g["status"] == "occurred"], "unopposed": g[g["n_opposed"] == 0],
        "page_archive_outlets": g[g["source"] == "wayback"], "feed_outlets": g[g["source"] == "ccnews"],
        "without_eth": g[g["base"] != "ETH"],
        "opinion_or_forecast_all": published[published["event_class"] == "opinion_or_forecast"],
        "all_signed_publication_clock": published, "capture_clock": rows[rows["clock"] == "capture"],
    }
    market = panel[(panel["base"] == MARKET) & (panel["sign"] != 0) & (panel["clock"] == "publication")
                   & (panel["t0"] >= TEST_START) & (panel["t0"] < TEST_END) & ~panel["event_class"].isin(SOFT_CLASSES)]
    cells = (f"pre_{PRE_WINDOWS[0]}", f"imm_{GATE_LAG}", f"post_{GATE_LAG}_{GATE_HORIZON}")
    signed_gate = (g["sign"] * g[GATE_COLUMN]).to_numpy(dtype=float)
    descriptive = {
        "gate_events_path": path_table(g),
        "splits": {name: _slope(part, GATE_COLUMN) for name, part in splits.items()},
        "event_class": {str(k): _slope(part, GATE_COLUMN) for k, part in g.groupby("event_class") if len(part) >= 30},
        "mean_return_by_sign": {"favourable": {c: _mean(g[g["sign"] > 0], f"ar_{c}") for c in cells},
                                "unfavourable": {c: _mean(g[g["sign"] < 0], f"ar_{c}") for c in cells}},
        "market_contract_raw": {c: _slope(market, f"r_{c}") for c in cells},
        "absolute_move_bp": {c: (1e4 * float(np.nanmean(np.abs(g[f"ar_{c}"]))) if np.isfinite(g[f"ar_{c}"]).any() else None)
                             for c in (f"pre_{GATE_HORIZON}", f"post_{GATE_LAG}_{GATE_HORIZON}")},
        "signed_mean_no_intercept": _bp(clustered(signed_gate, g["t0"].dt.floor("D").to_numpy())),
        "signed_mean_winsorised_1pct": _bp(clustered(_winsor(signed_gate), g["t0"].dt.floor("D").to_numpy())),
        "permutation": permutation(panel, n=n_placebo),
    }
    counts = {"news_records": len(panel), "signed_in_window": len(rows),
              "by_clock": {str(k): int(v) for k, v in rows["clock"].value_counts().items()},
              "lead_events": len(g), "lead_with_return": int(np.isfinite(g[GATE_COLUMN]).sum()),
              "lead_assets": int(g["base"].nunique()), "lead_days": int(g["t0"].dt.floor("D").nunique())}
    return {"verdict.json": {**verdict, "counts": counts},
            "evaluation.json": {"gate": verdict, "descriptive": descriptive, "counts": counts}}


def _winsor(x: np.ndarray, q: float = 0.01) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if not np.isfinite(x).any():
        return x
    lo, hi = np.nanquantile(x, [q, 1 - q])
    return np.clip(x, lo, hi)


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def store_digest(root: Path, directory: str) -> dict[str, str]:
    """Relative path -> sha256 of every parquet file of a bar store."""
    return {f"{directory}/{p.name}": sha256_file(p) for p in sorted((Path(root) / directory).glob("*.parquet"))}


def verify_store(root: Path, digest: dict[str, str]) -> Path:
    """Every file of the bar store matches its registered digest and the store holds no other parquet file."""
    parents = {str(Path(path).parent) for path in digest}
    if len(parents) != 1:
        raise ValueError(f"bar store digest spans {len(parents)} directories")
    directory = Path(root) / parents.pop()
    if {p.name for p in directory.glob("*.parquet")} != {Path(path).name for path in digest}:
        raise ValueError("bar store holds files that differ from the registered set")
    for path, expected in digest.items():
        if sha256_file(Path(root) / path) != expected:
            raise ValueError(f"bar store changed since the freeze: {path}")
    return directory


def json_safe(value):
    """Plain Python values; a float that is not finite becomes None."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return value

"""Bitemporal text store: one Parquet file per (source, month), rows keyed by URL/post id.

Columns: event_ts (publication time, UTC), as_of_ts (time the text became observable:
crawl/capture time or API retrieval time, UTC), source, outlet, url, title, body, lang,
author, extra (JSON string). A row is admissible for a decision at time T only when
as_of_ts <= T; event_ts orders it within the dossier.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path

import pandas as pd

DEFAULT_ROOT = Path("data/dossier/text")
COLUMNS = ["doc_id", "event_ts", "as_of_ts", "source", "outlet", "url", "title", "body",
           "lang", "author", "extra"]


def doc_id(source: str, key: str) -> str:
    return hashlib.sha256(f"{source}|{key}".encode("utf-8")).hexdigest()[:24]


def _month_path(root: Path, source: str, ts: pd.Timestamp) -> Path:
    return Path(root) / source / f"{ts.year}" / f"{ts.month:02d}.parquet"


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"store rows missing columns: {sorted(missing)}")
    out = df[COLUMNS].copy()
    for col in ("event_ts", "as_of_ts"):
        out[col] = pd.to_datetime(out[col], utc=True, format="ISO8601")
    if (out["as_of_ts"] < out["event_ts"] - pd.Timedelta(days=2)).any():
        raise ValueError("as_of_ts earlier than event_ts by more than the 2-day tolerance")
    return out


def upsert(df: pd.DataFrame, root: Path = DEFAULT_ROOT) -> int:
    """Merge rows into month files by event_ts; on duplicate doc_id keep the EARLIEST as_of_ts.

    Keeping the earliest capture is the conservative point-in-time choice: the text was
    observable from then on, and later re-captures must not move it later.
    """
    if df.empty:
        return 0
    rows = normalize(df)
    written = 0
    for (year, month), part in rows.groupby([rows["event_ts"].dt.year, rows["event_ts"].dt.month]):
        for source, chunk in part.groupby("source"):
            target = _month_path(root, source, pd.Timestamp(year=int(year), month=int(month), day=1, tz="UTC"))
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                existing = pd.read_parquet(target)
                chunk = pd.concat([existing, chunk], ignore_index=True)
            chunk = chunk.sort_values("as_of_ts").drop_duplicates(subset=["doc_id"], keep="first")
            chunk.to_parquet(target, index=False)
            written += len(chunk)
    return written


def query(ts_start: datetime, ts_end: datetime, as_of: datetime, sources=None,
          root: Path = DEFAULT_ROOT) -> pd.DataFrame:
    """Rows with event_ts in [ts_start, ts_end] and as_of_ts <= as_of."""
    ts_start, ts_end, as_of = (pd.Timestamp(t, tz="UTC") if pd.Timestamp(t).tzinfo is None
                               else pd.Timestamp(t) for t in (ts_start, ts_end, as_of))
    frames = []
    for src_dir in sorted(Path(root).glob("*")):
        if not src_dir.is_dir() or (sources and src_dir.name not in sources):
            continue
        for path in sorted(src_dir.glob("*/*.parquet")):
            year, month = int(path.parent.name), int(path.stem)
            first = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
            last = first + pd.offsets.MonthEnd(1) + pd.Timedelta(days=1)
            if last < ts_start or first > ts_end:
                continue
            frames.append(pd.read_parquet(path))
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.concat(frames, ignore_index=True)
    mask = (df["event_ts"] >= ts_start) & (df["event_ts"] <= ts_end) & (df["as_of_ts"] <= as_of)
    return df[mask].sort_values("event_ts").reset_index(drop=True)


def extra_json(**kwargs) -> str:
    return json.dumps(kwargs, sort_keys=True, ensure_ascii=False, default=str)

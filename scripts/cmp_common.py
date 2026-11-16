"""Shared pieces of the Charter 5 drivers: weeks, the frozen-charter check, the client, the joined tables."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tradingagents.compare import charter5, scope  # noqa: E402
from tradingagents.dossier.or_client import PINS, StructuredClient  # noqa: E402
from tradingagents.dossier.universe import load_cards  # noqa: E402
from tradingagents.reader import charter2  # noqa: E402

CHARTER = "docs/superpowers/specs/2026-11-15-llm-v2-charter5-direct-comparison-charter.md"
DRAFT_MARK = "DRAFT, NOT FROZEN"
PIN = "flash"                                    # model and quantisation of the typing and the reader
PROVIDER_ORDER = ("DeepInfra", "Baidu")          # as in the reader stage of Charter 2
MODEL = PINS[PIN][0]
PRESENT = {"items": "data/reader/items.parquet", "docs": "data/reader/docs.parquet", "records": "data/reader/records.parquet"}
ARCHIVE = {"items": "data/compare/items.parquet", "docs": "data/compare/docs.parquet", "records": "data/compare/records.parquet"}


def add_week_args(ap) -> None:
    ap.add_argument("--pilot", action="store_true", help="the seeded pilot weeks only (allowed before the freeze)")
    ap.add_argument("--weeks", default="", help="comma-separated Fridays, counted as a pilot (default: every test week)")


def universe_weeks(args) -> tuple[pd.DataFrame, list, bool]:
    """(universe, weeks of this run, whether the run is a pilot)."""
    top = charter2.universe(load_cards())
    fridays = sorted(charter5.test_universe(top)["date"].unique())
    if args.pilot:
        return top, scope.pilot_weeks(fridays), True
    if args.weeks:
        chosen = {pd.Timestamp(d, tz="UTC") for d in args.weeks.split(",")}
        if not chosen <= set(fridays):
            raise SystemExit("a requested week is not a test week")
        return top, sorted(chosen), True
    return top, fridays, False


def require_frozen(root: Path = ROOT) -> None:
    """A run on every test week needs the frozen charter; before the freeze only pilot weeks may run."""
    charter = root / CHARTER
    if not charter.exists() or DRAFT_MARK in charter.read_text():
        raise SystemExit("the charter is a draft: only pilot weeks may run before the freeze")


def make_client(remaining_usd: float, workers: int, max_tokens: int) -> StructuredClient:
    import requests
    from scripts.llm_v2c0_client import load_api_key
    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=workers + 4))
    return StructuredClient(api_key=load_api_key(), model=MODEL, provider=list(PROVIDER_ORDER), quantization=PINS[PIN][2],
                            cost_cap_usd=remaining_usd, reasoning_enabled=False, max_tokens=max_tokens, session=session)


def join_frames(present: dict, archive: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Items, docs and records of both stores, the archive rows under the columns of the present tables."""
    if set(present["docs"]["doc_id"]) & set(archive["docs"]["doc_id"]):
        raise SystemExit("a document id is in both stores")
    out = []
    for kind in ("items", "docs", "records"):
        cols = list(present[kind].columns)
        out.append(pd.concat([present[kind], archive[kind][cols]], ignore_index=True))
    return out[0], out[1], out[2]


def joined_tables(root: Path = ROOT, records: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Items, docs and records of the present material and the archive together. ``records`` replaces the path
    of the archive records (the pilot writes its own file)."""
    present = {k: pd.read_parquet(root / p) for k, p in PRESENT.items()}
    paths = dict(ARCHIVE, records=records or ARCHIVE["records"])
    return join_frames(present, {k: pd.read_parquet(root / p) for k, p in paths.items()})

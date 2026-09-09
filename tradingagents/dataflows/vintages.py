"""Immutable retrieval-vintage helpers; legacy assumed lags are not strict PIT."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pandas as pd

AVAILABILITY_COLUMNS = ['availability_basis', 'retrieved_at', 'source_updated_at']
KNOWN_AVAILABILITY = {'retrieved_snapshot', 'observed', 'published_version'}


def with_availability(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in AVAILABILITY_COLUMNS:
        if c not in df:
            df[c] = 'legacy_unverified' if c == 'availability_basis' else pd.NaT
    for c in ['event_ts', 'as_of_ts', 'retrieved_at', 'source_updated_at']:
        df[c] = pd.to_datetime(df[c], utc=True)
    if df[['event_ts', 'as_of_ts']].isna().any().any() or (df.as_of_ts < df.event_ts).any():
        raise ValueError('vintage requires valid event_ts <= as_of_ts')
    known = df.availability_basis.isin(KNOWN_AVAILABILITY)
    if (df.loc[known, "source_updated_at"] > df.loc[known, "as_of_ts"]).any():
        raise ValueError("version availability cannot precede the source update")
    retrieved = df.availability_basis.eq('retrieved_snapshot')
    if (df.loc[retrieved, 'retrieved_at'].isna().any() or
            (df.loc[retrieved, 'as_of_ts'] < df.loc[retrieved, 'retrieved_at']).any()):
        raise ValueError('retrieved vintage cannot be available before retrieval')
    return df


def merge_vintages(existing: pd.DataFrame, incoming: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    combined = pd.concat([with_availability(existing), with_availability(incoming)], ignore_index=True)
    unique = combined.drop_duplicates()
    if unique.duplicated(keys, keep=False).any():
        raise ValueError('conflicting same-key vintage: retain the original and supply the actual '
                         'new retrieval timestamp; a historical version cannot be reconstructed')
    return unique.reset_index(drop=True)


def write_preserving_vintage(frame: pd.DataFrame, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        current = pd.read_parquet(target)
        if current.equals(frame):
            return
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        archive = target.parent / '_vintages' / target.stem / f'{digest}.parquet'
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            shutil.copyfile(target, archive)
    tmp = target.with_suffix('.parquet.tmp')
    frame.to_parquet(tmp, index=False)
    tmp.replace(target)


def require_known_availability(frame: pd.DataFrame, strict_pit: bool) -> pd.DataFrame:
    if strict_pit and not frame.empty and (
        'availability_basis' not in frame or
        not frame['availability_basis'].isin(KNOWN_AVAILABILITY).all()
    ):
        raise ValueError('strict PIT availability unavailable for legacy/assumed-lag rows; '
                         'supply preserved historical vintages or use strict_pit=False only '
                         'for explicitly qualified diagnostics')
    return frame


def parquet_view(con, name: str, glob: str) -> None:
    """Expose mixed legacy/new shards without inventing an availability basis."""
    escaped = glob.replace("'", "''")
    con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{escaped}', union_by_name=true)")
    columns = {r[0] for r in con.execute(f'DESCRIBE {name}').fetchall()}
    if 'availability_basis' not in columns:
        con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT *, NULL::VARCHAR AS availability_basis "
                    f"FROM read_parquet('{escaped}', union_by_name=true)")

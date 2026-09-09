"""Immutable, registered development-only lead correction I/O.

Wrappers own numerical logic. This module owns the run fence, source hashes,
safe market reads, complete cell denominator and append-only evidence writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from tradingagents.predlab import registry

ROOT = Path(__file__).resolve().parents[1]
KEY = "audit_reevaluation_2026_09_09"
DEV = ("2021-01-01", "2025-03-31")
CUTOFF = pd.Timestamp("2025-04-01", tz="UTC")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def plain(value):
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [plain(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (Path, pd.Timestamp, datetime)):
        return str(value)
    return value


class RunContext:
    def __init__(self, family: str, *, root: Path | None = None):
        self.root = Path(root) if root is not None else ROOT
        self.family = family
        self.gate = registry.get_experiment(KEY)
        self.family_gate = self.gate["families"][family]
        self.provenance = registry.preflight(KEY, DEV)
        self.output_dir = self.root / "data/predlab" / KEY / family
        # Refuse both completed output and an unfinished prior invocation.
        self.output_dir.mkdir(parents=True, exist_ok=False)
        self.hashes: dict[str, str] = {}
        self.started = datetime.now(timezone.utc).isoformat()
        self.runtime = {
            "python": platform.python_version(),
            "packages": {name: importlib.metadata.version(name)
                         for name in ("numpy", "pandas", "scipy", "statsmodels", "pyarrow")},
            "threads": {name: os.environ.get(name) for name in
                        ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
        }
        (self.output_dir / "started.json").write_text(json.dumps({
            "experiment": KEY, "family": family, "started_utc": self.started,
            **self.provenance, "runtime": self.runtime,
        }, indent=2) + "\n")

    def track(self, path: str | Path) -> Path:
        path = Path(path).resolve()
        roots = [Path(r).resolve() for r in self.gate.get("source_roots", [])]
        if roots and not any(path.is_relative_to(r) for r in roots):
            raise ValueError(f"input is outside registered source roots: {path}")
        digest = sha256(path)
        old = self.hashes.get(str(path))
        if old is not None and old != digest:
            raise RuntimeError(f"input changed during run: {path}")
        self.hashes[str(path)] = digest
        return path

    def read_market(self, path: str | Path, start=None,
                    end_exclusive="2025-04-01") -> pd.DataFrame:
        path = Path(path)
        end = pd.Timestamp(end_exclusive)
        end = end.tz_localize("UTC") if end.tz is None else end.tz_convert("UTC")
        bound = CUTOFF
        if self.family == "nlst4" and path.name == "ETHUSDT.parquet":
            bound = pd.Timestamp(self.family_gate["settlement_fx_end_exclusive"])
        if end > bound:
            raise ValueError(f"market read exceeds registered bound {bound}")
        path = self.track(path)
        schema = pq.ParquetFile(path).schema_arrow
        metadata = json.loads(schema.metadata.get(b"pandas", b"{}"))
        indexes = metadata.get("index_columns", [])
        explicit = [x for x in indexes if isinstance(x, str)]
        field = "ts" if "ts" in schema.names else (explicit[0] if explicit else None)
        if field is None:
            raise ValueError(f"market frame lacks explicit timestamp index: {path}")
        filters = [(field, "<", end)]
        if start is not None:
            lo = pd.Timestamp(start)
            lo = lo.tz_localize("UTC") if lo.tz is None else lo.tz_convert("UTC")
            filters.append((field, ">=", lo))
        frame = pd.read_parquet(path, filters=filters)
        if field in frame.columns:
            frame = frame.set_index(field)
        frame.index = pd.DatetimeIndex(frame.index)
        if frame.index.tz is None:
            raise ValueError(f"naive market timestamp: {path}")
        frame.index = frame.index.tz_convert("UTC")
        if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
            raise ValueError(f"nonunique or unsorted market clock: {path}")
        if len(frame) and frame.index.max() >= end:
            raise ValueError(f"market row outside registered bound: {path}")
        return frame

    def write_frame(self, filename: str, frame: pd.DataFrame | pd.Series) -> Path:
        if Path(filename).name != filename or not filename.endswith(".parquet"):
            raise ValueError("archive requires a local Parquet filename")
        target = self.output_dir / filename
        if target.exists():
            raise FileExistsError(target)
        archive = frame.to_frame() if isinstance(frame, pd.Series) else frame.copy()
        archive.attrs = {}  # live BookInputs can contain unencodable DataFrames
        archive.to_parquet(target)
        return target

    def finish(self, payload: dict, cells: list[dict]) -> Path:
        expected = [r["id"] for r in self.family_gate["cells"]]
        actual = [r["id"] for r in cells]
        if len(actual) != len(set(actual)) or set(actual) != set(expected):
            raise ValueError(f"registered cells incomplete, extra or duplicated: {actual}")
        for row in cells:
            if not isinstance(row.get("config"), dict) or not isinstance(row.get("metrics"), dict):
                raise ValueError("cells require config and metrics objects")
        final = self.output_dir / "result.json"
        if final.exists():
            raise FileExistsError(final)
        for source, expected_hash in self.hashes.items():
            if sha256(Path(source)) != expected_hash:
                raise RuntimeError(f"input changed during run: {source}")
        end_provenance = registry.preflight(KEY, DEV)
        if end_provenance != self.provenance:
            raise RuntimeError("executed source/gate/policy changed during run")
        outputs = {p.name: sha256(p) for p in sorted(self.output_dir.iterdir()) if p.is_file()}
        result = plain({**payload, "experiment": KEY, "family": self.family,
                        "window": DEV, "cells": cells, "registered_gate": self.family_gate,
                        "started_utc": self.started,
                        "completed_utc": datetime.now(timezone.utc).isoformat(),
                        "runtime": self.runtime,
                        **self.provenance, "forecast_models_refit": False,
                        "holdout_evaluated": False, "input_sha256": self.hashes,
                        "input_unchanged_after_run": True, "output_sha256": outputs})
        serialized = json.dumps(result, indent=2, allow_nan=False) + "\n"
        # An append lock coordinates independently finishing family wrappers.
        lock = self.output_dir.parent / ".ledger.lock"
        with lock.open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            for cell in result["cells"]:
                registry.log_trial(experiment=KEY, cell=f"{self.family}:{cell['id']}",
                                   model="fixed_lead_correction", config=cell["config"],
                                   window=DEV, metrics=cell["metrics"])
            with final.open("x") as handle_out:
                handle_out.write(serialized)
        return final

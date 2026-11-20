"""Event-time study, lifecycle runner (one registered experiment). No model call.

The reader records of Charters 2 and 5, the item tables, the publication times and the digest of the minute
bar store are registered inputs. The runner rebuilds the event table (text stores only), rehearses the whole
evaluation on synthetic returns before the claim, then joins the minute bars once and writes the verdict by code.
Usage: evt_run.py --registration research/llm-event-time-<date>/gates.json --experiment <id> [--preflight-only]
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.eventtime import study

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ("verdict.json", "evaluation.json")
CELLS = ("event-table", "slope-gate", "descriptive-tables")
FRAMES = ("page_items", "page_records", "feed_items", "feed_records", "pub_times")
REHEARSAL_SEED, REHEARSAL_PLACEBO = 20261120, 20


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def build_events(read) -> pd.DataFrame:
    frames = {name: pd.read_parquet(io.BytesIO(read(name))) for name in FRAMES}
    pub = frames["pub_times"].set_index("doc_id")["pub_ts"]
    events = study.event_table(frames["page_items"], frames["page_records"], frames["feed_items"], frames["feed_records"], pub)
    return study.mark_leads(events)


def synthetic_returns(events: pd.DataFrame, seed: int = REHEARSAL_SEED) -> pd.DataFrame:
    """Return columns of the registered shape made of seeded noise, 2 % missing. No bar is read."""
    rng = np.random.default_rng(seed)
    out = events.reset_index(drop=True).copy()
    for c in study.return_columns():
        r = 0.02 * rng.normal(size=len(out))
        r[rng.uniform(size=len(out)) < 0.02] = np.nan
        out[f"r_{c}"], out[f"ar_{c}"] = r, r - 0.01 * rng.normal(size=len(out))
    return out


def rehearse(events: pd.DataFrame) -> None:
    out = study.json_safe(study.evaluate(synthetic_returns(events), n_placebo=REHEARSAL_PLACEBO))
    json.dumps(out, allow_nan=False)
    if set(out) != set(OUTPUTS):
        raise SystemExit("rehearsal: output names differ from the registered outputs")
    verdict = out["verdict.json"]
    if verdict["verdict"] not in ("PASS", "FAIL") or verdict["counts"]["lead_with_return"] < 1:
        raise SystemExit("rehearsal: no verdict")


def prepare(read, root: Path, rehearsal: bool) -> tuple[pd.DataFrame, Path]:
    """Verify the registered inputs and build the event table. Called before the claim and again inside the run."""
    events = build_events(read)
    klines_dir = study.verify_store(root, json.loads(read("klines_digest")))
    if study.symbol_file(klines_dir, study.MARKET) is None:
        raise SystemExit("minute bar store: no file for the market contract")
    if rehearsal:
        rehearse(events)
    return events, klines_dir


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registration", required=True)
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--preflight-only", action="store_true", help="checks and rehearsal only: no claim, no outcome")
    args = ap.parse_args(argv)
    root = Path(root) if root else ROOT
    from tradingagents.research import ResearchRun
    registered = json.loads((root / args.registration).read_text())["experiments"][args.experiment]["inputs"]
    prepare(lambda name: (root / registered[name]["path"]).read_bytes(), root, rehearsal=True)       # no claim yet
    if args.preflight_only:
        print("pre-flight passed: inputs verified, event table rebuilt, rehearsal on synthetic returns complete")
        return 0
    with ResearchRun.start(root=root, registration=args.registration, experiment=args.experiment, source=_head(root)) as run:
        events, klines_dir = prepare(run.read_input, root, rehearsal=False)
        panel = study.event_returns(events, klines_dir)                                              # the single outcome join
        outputs = study.json_safe(study.evaluate(panel))
        for name in OUTPUTS:
            run.write_json(name, outputs[name])
        run.finish([{"id": c, "status": "complete"} for c in CELLS])
        print(json.dumps(outputs["verdict.json"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

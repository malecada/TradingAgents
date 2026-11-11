"""Freeze the additional inputs of Charter 1b (replacement registration of the Charter 1 dev run):

* cache_manifest.json: the weeks completed by the first attempt (newest contiguous block with a stored book),
  the sha256 of every cached file of those weeks, the sha256 of every other cached file inside the manifested
  window (the interrupted week and the pre-registration preview weeks) and the spend record of the first attempt;
* funding_digest.json: sha256 of every file of the realized-funding store.

The dossier manifest, kline digest, agent config and identification flags of Charter 1 are reused unchanged.
Written to data/agents_v2/charter1b/ and committed before registration.
Usage: llm_v2c1b_manifest.py --runs-dir data/agents_v2/runs/charter1-preview --attempt1-tally 127.49 \
           --unsaved-allowance 0.35 --overshoot-allowance 0.15
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.agents_v2.charter1b import CacheError, load_cached_week  # noqa: E402
from tradingagents.agents_v2.graph import config_sha  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("data/agents_v2/charter1")
TARGET = Path("data/agents_v2/charter1b")
FUNDING = Path("data/dossier/funding")
ATTEMPT1 = "llm-v2c1-dev-run-20261111"
CUMULATIVE_CAP_USD = 140.0


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_cache_manifest(root: Path, runs_rel: str, by_day: dict[str, dict], cfg: str, tally: float,
                         unsaved_allowance: float, overshoot_allowance: float) -> dict:
    """Cache manifest of the weeks under ``root / runs_rel``. A week with a stored book inside the newest
    contiguous block must be admissible by the cache-only loader and is frozen; every other cached file of a
    manifested week is pinned by hash."""
    runs = Path(root) / runs_rel
    complete, files, pinned, interrupted = [], {}, {}, None
    block_open = True
    for day in sorted(by_day, reverse=True):
        day_dir = runs / day
        if block_open and (day_dir / "_portfolio.json").exists():
            try:
                load_cached_week(day, by_day[day], runs, cfg)
            except CacheError as exc:
                raise SystemExit(f"cached week {day} is not admissible: {exc}")
            complete.append(day)
            for sym in by_day[day]:
                files[f"{day}/{sym}.json"] = sha(day_dir / f"{sym}.json")
            files[f"{day}/_portfolio.json"] = sha(day_dir / "_portfolio.json")
            continue
        if block_open:
            block_open = False
            interrupted = day if day_dir.is_dir() and any(day_dir.glob("*.json")) else None
        if day_dir.is_dir():
            for f in sorted(day_dir.glob("*.json")):
                pinned[f"{day}/{f.name}"] = sha(f)
    if not complete:
        raise SystemExit("no completed week in the cache")
    partial_cost, partial_calls = 0.0, 0
    if interrupted:
        for f in sorted((runs / interrupted).glob("*.json")):
            if f.name.startswith("_"):
                continue
            meta = json.loads(f.read_text()).get("meta", [])
            partial_cost += sum(float(m.get("cost") or 0.0) for m in meta)
            partial_calls += len(meta)
    recorded = tally + partial_cost
    process_cap = CUMULATIVE_CAP_USD - recorded - unsaved_allowance - overshoot_allowance
    return {"runs_dir": runs_rel, "config_sha": cfg, "complete_weeks": sorted(complete), "n_complete_weeks": len(complete),
            "files": files, "pinned_other": pinned, "interrupted_week": interrupted,
            "attempt1": {"experiment": ATTEMPT1, "client_tally_usd": tally,
                         "interrupted_week_cached_usd": round(partial_cost, 6), "interrupted_week_cached_calls": partial_calls,
                         "recorded_spend_usd": round(recorded, 6), "unsaved_allowance_usd": unsaved_allowance,
                         "overshoot_allowance_usd": overshoot_allowance, "cumulative_cap_usd": CUMULATIVE_CAP_USD,
                         "process_cap_usd": round(process_cap, 2)}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True, help="per-asset call cache of the first attempt, relative to the checkout")
    ap.add_argument("--attempt1-tally", type=float, required=True,
                    help="client spend of the first attempt at its last completed week (run log)")
    ap.add_argument("--unsaved-allowance", type=float, default=0.35,
                    help="allowance for calls of the interrupted week that were paid but not saved")
    ap.add_argument("--overshoot-allowance", type=float, default=0.15,
                    help="allowance for calls in flight when the cap is reached")
    args = ap.parse_args()
    manifest = json.loads((ROOT / SOURCE / "dossier_manifest.json").read_text())
    cfg = config_sha()
    if json.loads((ROOT / SOURCE / "agent_config.json").read_text())["config_sha"] != cfg:
        raise SystemExit("agent config differs from the Charter 1 freeze")
    by_day: dict[str, dict] = {}
    for path in manifest["files"]:
        p = Path(path)
        by_day.setdefault(p.parent.name, {})[p.stem] = json.loads((ROOT / p).read_text())
    out = build_cache_manifest(ROOT, str(Path(args.runs_dir)), by_day, cfg, args.attempt1_tally, args.unsaved_allowance,
                               args.overshoot_allowance)
    (ROOT / TARGET).mkdir(parents=True, exist_ok=True)
    (ROOT / TARGET / "cache_manifest.json").write_text(json.dumps(out, indent=0, sort_keys=True) + "\n")
    funding = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / FUNDING).glob("*.parquet"))}
    (ROOT / TARGET / "funding_digest.json").write_text(json.dumps(funding, indent=0, sort_keys=True) + "\n")
    print(json.dumps({"complete_weeks": out["n_complete_weeks"], "newest": max(out["complete_weeks"]),
                      "oldest": min(out["complete_weeks"]), "frozen_files": len(out["files"]),
                      "pinned_other": len(out["pinned_other"]), "interrupted_week": out["interrupted_week"],
                      "attempt1": out["attempt1"], "funding_files": len(funding)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

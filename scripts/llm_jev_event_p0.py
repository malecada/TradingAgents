"""Runners for the registered Jev P0 probe (charter §7.3).

  label   E1: Jev labels + blind review sheet data (no metrics)
  render  write the markdown sheet from E1 outputs for the human reviewer
  score   E2: apply the filled sheet, compute gates and diagnostics
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_event_xs_truth import check_reproduction, load_rounds  # noqa: E402
from llm_jev_client import PROVIDER_NAME, JevClient, JevError, load_api_key  # noqa: E402
from llm_jev_labels import THRESHOLD, label_rounds  # noqa: E402
from llm_jev_questions import questions_sha256  # noqa: E402
from llm_jev_review import apply_review, build_review, parse_filled, render_markdown  # noqa: E402
from llm_jev_score import diagnostics, evaluate  # noqa: E402
from llm_jev_smoke import preflight  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROGRAM_DIR = "research/llm-jev-event-2026-09-29"
E1 = "llm-jev-p0-label-20260929"
E2 = "llm-jev-p0-score-20260929"
PINNED_MODEL: str | None = None  # set from the smoke-test response before registration
COST_CAP_USD = 5.0
E1_OUTPUTS = ("jev_labels.json", "jev_labels_anon.json", "review_sheet.json",
              "review_key.json", "run_meta.json")
E1_CELLS = ("label-v1", "label-v2", "anon-v1", "anon-v2", "review-sheet")
E2_OUTPUTS = ("p0_verdict.json", "p0_diagnostics.json")
E2_CELLS = ("gates", "diagnostics")
SHEET_PATH = f"{PROGRAM_DIR}/review/jev-review-sheet.md"


def _head(root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def run_label(root: Path, registration: str, source: str) -> dict:
    if PINNED_MODEL is None:
        raise SystemExit("PINNED_MODEL is unset; finish the smoke test and registration first")
    key = load_api_key(root / ".env")
    try:
        preflight(JevClient(api_key=key, model=PINNED_MODEL, expected_model=PINNED_MODEL,
                            cost_cap_usd=0.05))
    except JevError as exc:
        raise SystemExit(f"preflight failed before any run claim: {exc}") from None
    client = JevClient(api_key=key, model=PINNED_MODEL, expected_model=PINNED_MODEL,
                       cost_cap_usd=COST_CAP_USD)
    from tradingagents.research import ResearchRun
    with ResearchRun.start(root=root, registration=registration, experiment=E1,
                           source=source) as run:
        rounds = load_rounds(run.read_input)
        check_reproduction(rounds)
        named, anon = label_rounds(rounds, client)
        rows, key = build_review(rounds, named)
        latencies = [r["_latency_s"] for label in [*named.values(), *anon.values()]
                     for r in label["raw"]]
        meta = {"model": PINNED_MODEL, "provider": PROVIDER_NAME, "calls": client.calls,
                "spent_usd": client.spent_usd, "questions_sha256": questions_sha256(),
                "threshold": THRESHOLD, "latency_median_s": statistics.median(latencies),
                "review_rows": len(rows)}
        run.write_json("jev_labels.json", named)
        run.write_json("jev_labels_anon.json", anon)
        run.write_json("review_sheet.json", {"rows": rows})
        run.write_json("review_key.json", key)
        run.write_json("run_meta.json", meta)
        return run.finish([{"id": cell, "status": "complete"} for cell in E1_CELLS])


def run_render(root: Path) -> Path:
    sheet = json.loads((root / "research_runs" / E1 / "outputs" / "review_sheet.json").read_text())
    target = root / SHEET_PATH
    if target.exists():
        raise SystemExit(f"{target} exists; refusing to overwrite a review sheet")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_markdown(sheet["rows"]))
    return target


def run_score(root: Path, registration: str, source: str) -> dict:
    from tradingagents.research import ResearchRun
    with ResearchRun.start(root=root, registration=registration, experiment=E2,
                           source=source) as run:
        rounds = load_rounds(run.read_input)
        check_reproduction(rounds)
        named = json.loads(run.read_input("jev_labels"))
        anon = json.loads(run.read_input("jev_labels_anon"))
        rows = json.loads(run.read_input("review_sheet"))["rows"]
        key = json.loads(run.read_input("review_key"))
        meta = json.loads(run.read_input("run_meta"))
        filled = parse_filled(run.read_input("review_filled").decode("utf-8"), rows)
        truth, same, stats = apply_review(rounds, named, rows, key, filled)
        jev_events = {int(k): v["events"] for k, v in named.items()}
        verdict = {**evaluate(truth, jev_events, same, named, anon), "review": stats,
                   "model": meta["model"], "questions_sha256": meta["questions_sha256"]}
        run.write_json("p0_verdict.json", verdict)
        run.write_json("p0_diagnostics.json", diagnostics(rounds, truth, named, meta))
        run.finish([{"id": cell, "status": "complete"} for cell in E2_CELLS])
        return verdict


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("label", "render", "score"))
    parser.add_argument("--registration")
    parser.add_argument("--source")
    args = parser.parse_args(argv)
    if args.command == "render":
        print(run_render(ROOT))
        return 0
    default = "gates.json" if args.command == "label" else "gates_e2.json"
    registration = args.registration or f"{PROGRAM_DIR}/{default}"
    source = args.source or _head(ROOT)
    runner = run_label if args.command == "label" else run_score
    print(json.dumps(runner(ROOT, registration, source), indent=1)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())

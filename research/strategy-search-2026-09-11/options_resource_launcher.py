"""Exclusive options collector launch under reviewed 256 MiB/120-second guard."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


def launch(command, report_path):
    # Reserve before launching: an existing report cannot cause a second run.
    with Path(report_path).open("x") as report:
        original_affinity = None
        try:
            from resource_guard_v2 import run_guard
            original_affinity = os.sched_getaffinity(0)
            os.sched_setaffinity(0, [min(original_affinity)])
            result = run_guard(command, rss_limit_bytes=256 * 1024**2, wall_seconds=120)
        except Exception as exc:
            result = {"child_exit_code": None, "limit_reason": "launcher/guard failure: " + type(exc).__name__ + ": " + str(exc),
                      "rss_limit_bytes": 256 * 1024**2, "wall_limit_seconds": 120, "retry": False}
        finally:
            if original_affinity is not None:
                os.sched_setaffinity(0, original_affinity)
        result["options_cpu_contract"] = "Child sets affinity to one CPU before capture; no nested/detached processes authorized."
        json.dump(result, report, sort_keys=True, indent=2, allow_nan=False)
        report.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    command = [sys.executable, "-B", str(Path(__file__).with_name("options_metadata.py")), "--source", args.source]
    result = launch(command, args.report)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["child_exit_code"] == 0 and result["limit_reason"] is None else 1)


if __name__ == "__main__":
    main()

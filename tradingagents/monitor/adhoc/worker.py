# tradingagents/monitor/adhoc/worker.py
"""Subprocess entry: ``python -m tradingagents.monitor.adhoc.worker --run <id>``.

Loads a run row, drives the matching service generator, and writes progress +
outputs incrementally. Never raises out of execute(): a failure is recorded as
status=error on the run (and even the error-recording is best-effort so a
secondary DB failure cannot strand the run in `running`).
"""
from __future__ import annotations

import argparse
import time
import traceback

from tradingagents.monitor.adhoc import service, store


def execute(run_id: str) -> None:
    conn = store.connect()
    try:
        _run(conn, run_id)
    except Exception as exc:  # noqa: BLE001 — terminal error is the contract
        try:
            store.set_status(
                conn, run_id, "error", finished_ts=time.time(),
                error_msg=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        except Exception:  # noqa: BLE001 — never raise out of the worker
            pass
    finally:
        conn.close()


def _run(conn, run_id: str) -> None:
    run = store.get_run(conn, run_id)
    if run is None:
        return
    store.set_status(conn, run_id, "running", started_ts=time.time(),
                     stage="starting", progress=0.0)
    store.heartbeat(conn, run_id, stage="starting", progress=0.0)

    if run["strategy"] == "hybrid":
        gen = service.run_hybrid(coin=run["coin"], date=run["date"],
                                 analysts=run["analysts"], model=run["model"],
                                 run_id=run_id)
    else:
        gen = service.run_quant(coin=run["coin"], date=run["date"], run_id=run_id)

    ordinal = 0
    for key, label, kind, content in gen:
        if kind == "progress":
            store.heartbeat(conn, run_id, stage=label, progress=run["progress"] or 0.1)
            continue
        store.add_output(conn, run_id, key=key, label=label, kind=kind,
                         content=content, ordinal=ordinal)
        ordinal += 1
        store.heartbeat(conn, run_id, stage=label, progress=0.5)

    store.set_status(conn, run_id, "done", finished_ts=time.time(),
                     stage="done", progress=1.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    execute(args.run)


if __name__ == "__main__":
    main()

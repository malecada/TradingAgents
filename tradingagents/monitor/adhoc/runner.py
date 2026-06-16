# tradingagents/monitor/adhoc/runner.py
"""Spawn the ad-hoc worker subprocess and enforce a single-job lock.

One run at a time protects the shared Binance IP and LLM budget. The stale
reaper marks a wedged run as `error` so the lock can never block permanently:
a `running` run with no heartbeat for STALE_SECONDS, or a `queued` run created
over STALE_SECONDS ago whose worker never started.
"""
from __future__ import annotations

import subprocess
import sys
import time

STALE_SECONDS = 600  # 10 min (spec §12)


def _is_stale(active: dict) -> bool:
    now = time.time()
    if active["status"] == "running":
        # Fall back to started_ts/created_ts when no heartbeat was ever written
        # (worker crashed right after flipping to running) so it still reaps.
        hb = (active.get("heartbeat_ts") or active.get("started_ts")
              or active.get("created_ts"))
        return hb is not None and (now - hb) > STALE_SECONDS
    if active["status"] == "queued":
        created = active.get("created_ts")
        return created is not None and (now - created) > STALE_SECONDS
    return False


def can_start(conn) -> tuple[bool, str | None]:
    from tradingagents.monitor.adhoc import store
    active = store.active_run(conn)
    if active is not None and _is_stale(active):
        store.set_status(conn, active["run_id"], "error", finished_ts=time.time(),
                         error_msg="stale: worker died without finishing")
        active = None
    if active is not None:
        return False, active["run_id"]
    return True, None


def launch(run_id: str) -> None:
    subprocess.Popen(
        [sys.executable, "-m", "tradingagents.monitor.adhoc.worker", "--run", run_id])

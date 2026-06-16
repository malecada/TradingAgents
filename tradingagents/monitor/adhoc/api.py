# tradingagents/monitor/adhoc/api.py
"""Ad-hoc prediction routes, registered onto the monitor's FastAPI app.

The only writing routes in the monitor; they write solely to the isolated
adhoc_runs.db (never the trade journal, never the exchange).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tradingagents.monitor.adhoc import runner, store

_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_ANALYSTS = ["market", "onchain", "prediction"]
_EST_COST = {"quant": 0.0, "hybrid": 0.002}


class AdhocRunBody(BaseModel):
    coin: str
    date: str
    strategy: str = "quant"
    analysts: Optional[List[str]] = None
    model: Optional[str] = None


def _coin_universe() -> list[str]:
    from tradingagents.execution.live import config as live_config
    return list(live_config.load_config().coin_universe)


def register_adhoc_routes(app: FastAPI) -> None:

    @app.get("/api/adhoc/meta")
    def adhoc_meta():
        conn = store.connect()
        try:
            return {
                "coins": _coin_universe(),
                "default_analysts": _DEFAULT_ANALYSTS,
                "default_model": _DEFAULT_MODEL,
                "job_running": store.active_run(conn) is not None,
            }
        finally:
            conn.close()

    @app.post("/api/adhoc/run")
    def adhoc_run(body: AdhocRunBody):
        if body.coin not in _coin_universe():
            raise HTTPException(status_code=400, detail=f"unknown coin: {body.coin}")
        if body.strategy not in ("quant", "hybrid"):
            raise HTTPException(status_code=400, detail="strategy must be quant|hybrid")
        try:
            import pandas as pd
            pd.Timestamp(body.date)
        except Exception:
            raise HTTPException(status_code=400, detail=f"bad date: {body.date}")
        conn = store.connect()
        try:
            ok, blocker = runner.can_start(conn)
            if not ok:
                raise HTTPException(status_code=409,
                                    detail=f"a run is already active: {blocker}")
            run_id = store.create_run(
                conn, coin=body.coin, date=body.date, strategy=body.strategy,
                analysts=body.analysts or _DEFAULT_ANALYSTS,
                model=body.model or _DEFAULT_MODEL,
                est_cost=_EST_COST.get(body.strategy, 0.0))
        finally:
            conn.close()
        runner.launch(run_id)
        return {"run_id": run_id}

    @app.get("/api/adhoc/status/{run_id}")
    def adhoc_status(run_id: str):
        conn = store.connect()
        try:
            run = store.get_run(conn, run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="unknown run")
            outs = store.get_outputs(conn, run_id)
            return {
                "status": run["status"], "stage": run["stage"],
                "progress": run["progress"], "est_cost": run["est_cost"],
                "error_msg": run["error_msg"],
                "outputs": [{"key": o["key"], "label": o["label"],
                             "kind": o["kind"], "ordinal": o["ordinal"]} for o in outs],
            }
        finally:
            conn.close()

    @app.get("/api/adhoc/result/{run_id}")
    def adhoc_result(run_id: str):
        conn = store.connect()
        try:
            run = store.get_run(conn, run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="unknown run")
            return {"run": run, "outputs": store.get_outputs(conn, run_id)}
        finally:
            conn.close()

    @app.get("/api/adhoc/runs")
    def adhoc_runs():
        conn = store.connect()
        try:
            return {"runs": store.list_runs(conn, limit=50)}
        finally:
            conn.close()

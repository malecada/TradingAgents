"""Entrypoint: ``python -m tradingagents.monitor``.

Reads DATA_DIR / LOG_DIR / TA_MONITOR_PASSWORD / TA_MONITOR_START_CAPITAL
from the environment (same env contract as the live runner). Binds
127.0.0.1 only — a reverse proxy terminates TLS in production.
"""
from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from tradingagents.monitor.app import create_app


def main() -> None:
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    log_dir = os.environ.get("LOG_DIR", "logs")
    start_capital = float(os.environ.get("TA_MONITOR_START_CAPITAL", "10000"))
    host = os.environ.get("TA_MONITOR_HOST", "127.0.0.1")
    port = int(os.environ.get("TA_MONITOR_PORT", "8800"))

    app = create_app(
        journal_path=str(data_dir / "trade_journal.db"),
        log_dir=log_dir,
        start_capital=start_capital,
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

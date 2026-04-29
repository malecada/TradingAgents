"""Telegram bot — daily summary + immediate alerts.

Outbound only; failures are logged, never raised (Telegram outage must not
abort a trading cycle).
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _post_telegram(*, token: str, chat_id: str, text: str):
    return requests.post(
        _TELEGRAM_API.format(token=token),
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )


def send_daily_summary(*, bot_token, chat_id, cycle_id,
                        portfolio_before, portfolio_after, trades,
                        agreement_rate) -> None:
    pnl = portfolio_after - portfolio_before
    pnl_pct = pnl / portfolio_before if portfolio_before else 0
    lines = [
        f"*Cycle {cycle_id}*",
        f"Portfolio: {portfolio_before:.2f} → {portfolio_after:.2f} ({pnl_pct:+.2%})",
        f"Trades: {len(trades)}",
        f"Shadow agreement: {agreement_rate:.1%}",
    ]
    for t in trades:
        lines.append(f"  {t['coin']} {t['side']} {t['qty']:.6f} @ {t['price']:.2f}")
    text = "\n".join(lines)
    try:
        _post_telegram(token=bot_token, chat_id=chat_id, text=text)
    except Exception as e:
        logger.error("Telegram delivery failed (non-fatal): %s", e)


def send_alert(*, bot_token, chat_id, severity: str, message: str) -> None:
    text = f"🚨 *{severity}*\n{message}"
    try:
        _post_telegram(token=bot_token, chat_id=chat_id, text=text)
    except Exception as e:
        logger.error("Telegram alert failed (non-fatal): %s", e)

from unittest.mock import patch, MagicMock


def test_send_daily_summary_calls_telegram_api():
    from tradingagents.execution.live import notify

    with patch.object(notify, "_post_telegram") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        notify.send_daily_summary(
            bot_token="t", chat_id="123",
            cycle_id="2026-05-12",
            portfolio_before=10000.0, portfolio_after=10120.0,
            trades=[{"coin": "BTC", "side": "BUY", "qty": 0.1, "price": 60000}],
            agreement_rate=1.0,
        )
        mock_post.assert_called_once()
        text = mock_post.call_args.kwargs["text"]
        assert "2026-05-12" in text
        assert "BTC" in text


def test_send_alert_includes_severity():
    from tradingagents.execution.live import notify

    with patch.object(notify, "_post_telegram") as mock_post:
        notify.send_alert(
            bot_token="t", chat_id="123",
            severity="UNPROTECTED",
            message="BTC stop-loss failed",
        )
        text = mock_post.call_args.kwargs["text"]
        assert "UNPROTECTED" in text
        assert "BTC stop-loss" in text


def test_telegram_failure_does_not_crash():
    from tradingagents.execution.live import notify

    with patch.object(notify, "_post_telegram", side_effect=Exception("network")):
        notify.send_daily_summary(
            bot_token="t", chat_id="123",
            cycle_id="2026-05-12",
            portfolio_before=10000.0, portfolio_after=10100.0,
            trades=[], agreement_rate=1.0,
        )

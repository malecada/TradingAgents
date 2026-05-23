from tradingagents.sentiment.anonymize import (
    anonymize_text,
    build_substitution_table,
)


def test_anonymizes_btc_case_insensitive():
    out = anonymize_text("Bitcoin hits ATH; BTC up. bitcoin etf.", coin="BTC")
    assert "Asset-A" in out
    assert "Bitcoin" not in out
    assert "BTC" not in out
    assert "bitcoin" not in out


def test_anonymizes_eth():
    out = anonymize_text("Ethereum upgrade ships; ETH rises.", coin="ETH")
    assert "Asset-B" in out
    assert "Ethereum" not in out
    assert "ETH" not in out


def test_anonymizes_exchanges():
    out = anonymize_text("Binance and Coinbase pause withdrawals.", coin="BTC")
    assert "Binance" not in out
    assert "Coinbase" not in out
    assert "Exchange-" in out


def test_does_not_corrupt_unrelated_words():
    out = anonymize_text("Bitcoiners are happy", coin="BTC")
    # Whole-word match: 'Bitcoiners' should NOT be replaced.
    assert "Bitcoiners" in out


def test_table_is_reversible_for_inspection():
    table = build_substitution_table("BTC")
    assert any(orig.lower() == "bitcoin" for orig in table)

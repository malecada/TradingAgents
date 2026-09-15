"""Literal independent invented cash examples; no source snapshots/returns."""
import importlib.util
from pathlib import Path
from decimal import Decimal as D
import pytest

P = Path(__file__).resolve().parents[2] / 'research/broader-allocation-2026-09-15/spot_book.py'
s = importlib.util.spec_from_file_location('tested_spot_book', P)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)


def test_literal_round_trip_quote_fees_and_total_capital():
    b = m.SpotBook({('cex', 'USDC'): '10000'})
    b.trade('buy', 'cex', 'BTC', 'USDC', 'buy', '2', '100', fee_asset='USDC', fee='0.2')
    assert b.balances == {('cex', 'USDC'): D('9799.8'), ('cex', 'BTC'): D('2')}
    b.trade('sell', 'cex', 'BTC', 'USDC', 'sell', '2', '110', fee_asset='USDC', fee='0.22')
    nav = b.liquidation_nav({('cex', 'USDC'): '1'}, exit_cost_usd='5', pending_marks={})
    assert nav == D('10014.58')
    assert m.cash_profit(nav, '10000') == {'net_cash_profit_usd': D('14.58'), 'simple_net_return': D('0.001458')}


def test_base_fee_and_third_asset_fee_are_not_free():
    b = m.SpotBook({('cex', 'USDC'): '1000', ('cex', 'FEE'): '1'})
    b.trade('buy', 'cex', 'BTC', 'USDC', 'buy', '2', '100', fee_asset='BTC', fee='0.002')
    assert b.balances[('cex', 'BTC')] == D('1.998')
    b.trade('sell', 'cex', 'BTC', 'USDC', 'sell', '1', '100', fee_asset='FEE', fee='0.1')
    assert b.balances[('cex', 'FEE')] == D('0.9')
    nav = b.liquidation_nav({('cex', 'USDC'): '1', ('cex', 'BTC'): '100', ('cex', 'FEE'): '10'}, exit_cost_usd='0', pending_marks={})
    assert nav == D('1008.8')  # initial all-asset wealth 1010; total loss 1.2


def test_no_borrow_and_failed_event_is_atomic():
    b = m.SpotBook({('cex', 'USDC'): '100'})
    with pytest.raises(ValueError):
        b.trade('a', 'cex', 'BTC', 'USDC', 'buy', '1', '100', fee_asset='USDC', fee='0.1')
    assert b.balances == {('cex', 'USDC'): D('100')} and not b.events
    with pytest.raises(ValueError):
        b.trade('a', 'cex', 'BTC', 'USDC', 'buy', '0.5', '100', fee_asset='GAS', fee='0.1')
    assert not b.events


def test_pending_transfer_is_not_spendable_or_double_counted():
    b = m.SpotBook({('cex', 'USDC'): '10000'})
    b.begin_transfer('t', 'cex', 'wallet:base', 'USDC', '1000', fee_asset='USDC', fee='2')
    assert b.balances[('cex', 'USDC')] == D('8998')
    with pytest.raises(m.MissingValuation):
        b.liquidation_nav({('cex', 'USDC'): '1'}, exit_cost_usd='0', pending_marks={})
    assert b.liquidation_nav({('cex', 'USDC'): '1'}, exit_cost_usd='0', pending_marks={'t': '0.98'}) == D('9978')
    with pytest.raises(ValueError):
        b.trade('early', 'wallet:base', 'BTC', 'USDC', 'buy', '1', '100', fee_asset='USDC', fee='0')
    b.settle_transfer('settle', 't')
    assert b.liquidation_nav({('cex', 'USDC'): '1', ('wallet:base', 'USDC'): '1'}, exit_cost_usd='0', pending_marks={}) == D('9998')
    with pytest.raises(ValueError): b.settle_transfer('twice', 't')
    with pytest.raises(ValueError): b.charge('settle', 'cex', 'USDC', '1')


def test_depeg_missing_value_and_documented_total_loss():
    b = m.SpotBook({('cex', 'USDC'): '7500', ('wallet', 'chain:token'): '25'})
    with pytest.raises(m.MissingValuation):
        b.liquidation_nav({('cex', 'USDC'): '0.8'}, exit_cost_usd='0', pending_marks={})
    assert b.liquidation_nav({('cex', 'USDC'): '0.8', ('wallet', 'chain:token'): '0'}, exit_cost_usd='10', pending_marks={}) == D('5990')
    b.write_off('loss', 'wallet', 'chain:token', '25', evidence='invented irrevocable loss')
    assert b.events[-1]['deltas'][('wallet', 'chain:token')] == D('-25')
    assert b.liquidation_nav({('cex', 'USDC'): '0.8'}, exit_cost_usd='0', pending_marks={}) == D('6000')


def test_rounding_dust_and_committed_phased_entry():
    b = m.SpotBook({('cex', 'USDC'): '10000'})
    for i in range(4):
        # Each 625 budget includes 1 fixed fee; 624/100 floored to 0.1 lot.
        q = m.floor_quantity(D('624') / D('100'), '0.1')
        b.trade(str(i), 'cex', 'BTC', 'USDC', 'buy', q, '100', fee_asset='USDC', fee='1')
    assert b.balances == {('cex', 'USDC'): D('7516'), ('cex', 'BTC'): D('24.8')}
    assert b.liquidation_nav({('cex', 'USDC'): '1', ('cex', 'BTC'): '100'}, exit_cost_usd='0', pending_marks={}) == D('9996')


@pytest.mark.parametrize('bad', ['NaN', 'Infinity', True, 0.1])
def test_nonexact_or_nonfinite_inputs_rejected(bad):
    with pytest.raises(ValueError): m.SpotBook({('x', 'USD'): bad})


def test_zero_balance_does_not_need_price_but_exit_cost_does():
    b = m.SpotBook({('x', 'USD'): '1', ('x', 'DEAD'): '0'})
    with pytest.raises(m.MissingValuation): b.liquidation_nav({('x', 'USD'): '1'}, exit_cost_usd=None, pending_marks={})
    assert b.liquidation_nav({('x', 'USD'): '1'}, exit_cost_usd='2', pending_marks={}) == D('-1')

"""Hand-calculated V2 traces only; no market inputs or strategy experiments."""
import json

import numpy as np
import pandas as pd
import pytest

from scripts.baseline_strategy_v2 import run_coin_backtest


def run(prices, positions, **overrides):
    kwargs = dict(dates=pd.date_range('2024-01-01', periods=len(prices), tz='UTC'),
                  prices=np.array(prices, dtype=float), positions=np.array(positions, dtype=float),
                  initial_capital=100., fee_rate=.01, slippage=0., spread=0.,
                  price_impact=.02, funding_rate=.003, stop_loss=1., max_portfolio_dd=1.)
    kwargs.update(overrides)
    return run_coin_backtest(**kwargs)


@pytest.mark.parametrize('direction,prices,nav,carry,notional', [
    (1., [100., 110.], 106.7, -.3, 110.),
    (-1., [100., 90.], 107.3, .3, -90.),
])
def test_trace_reconciles_opening_fees_signed_funding_and_impact(direction, prices, nav, carry, notional):
    trace = []
    equity, _ = run(prices, [0., direction], trace=trace)
    assert equity == pytest.approx([100., nav])
    assert len(trace) == 1
    row = trace[0]
    assert row['date'] == '2024-01-02T00:00:00+00:00'
    assert row['nav_before'] == 100. and row['nav_after'] == pytest.approx(nav)
    assert row['target_position'] == direction and row['exposure'] == direction
    assert row['gross_dollars'] == pytest.approx(10.)
    assert row['funding_dollars'] == pytest.approx(carry)
    assert row['fee_dollars'] == pytest.approx(1.)
    assert row['impact_dollars'] == pytest.approx(2.)
    assert row['turnover_dollars'] == pytest.approx(100.)
    assert row['closing_notional'] == pytest.approx(notional)
    assert row['exit_notional'] == 0. and not row['exit_executed']
    assert row['nav_after'] == pytest.approx(row['nav_before'] + row['gross_dollars'] +
        row['funding_dollars'] - row['fee_dollars'] - row['impact_dollars'])
    json.dumps(trace, allow_nan=False)


def test_intrabar_stop_trace_includes_marked_exit_cost_and_full_assumed_funding():
    trace = []
    equity, _ = run([100., 90.], [0., 1.], trace=trace,
                   highs=np.array([100., 101.]), lows=np.array([100., 85.]), price_stop_pct=.03)
    # Entry: 100 - 3 price loss - .3 funding - 1 fee - 2 impact = 93.7.
    # The exit sells the marked 97 notional, charging .97 plus quadratic impact.
    exit_impact = .02 * 97.**2 / 93.7
    final = 93.7 - .97 - exit_impact
    assert equity == pytest.approx([100., final])
    row = trace[0]
    assert row['mark_return'] == pytest.approx(-.03)
    assert row['mark_price'] == 97. and row['entry_price'] == 100.
    assert row['price_stop_hit'] and row['exit_executed']
    assert row['stop_outside_envelope'] is False
    assert row['exit_notional'] == pytest.approx(97.) and row['closing_notional'] == 0.
    assert row['fee_dollars'] == pytest.approx(1.97)
    assert row['impact_dollars'] == pytest.approx(2. + exit_impact)
    assert row['turnover_dollars'] == pytest.approx(197.)
    assert row['funding_dollars'] == pytest.approx(-.3)
    assert not row['halted_before'] and not row['halted_after']


def test_gap_stop_flags_assumed_fill_outside_observed_envelope_without_changing_fill():
    args = dict(highs=np.array([100., 85.]), lows=np.array([100., 75.]), price_stop_pct=.03)
    plain = run([100., 80.], [0., 1.], **args)
    trace = []
    traced = run([100., 80.], [0., 1.], trace=trace, **args)
    assert traced == plain
    assert trace[0]['mark_price'] == 97.
    assert trace[0]['mark_return'] == pytest.approx(-.03)
    assert trace[0]['price_stop_hit'] is True
    assert trace[0]['stop_outside_envelope'] is True


def test_permanent_halt_trace_preserves_zero_tail_and_exact_halt_bar():
    trace = []
    equity, metrics = run([100., 80., 120.], [0., 1., 1.], trace=trace,
                          price_impact=0., funding_rate=0., max_portfolio_dd=.15)
    # First daily loss -20, entry fee 1, forced closing fee .8; then remain flat.
    assert equity == pytest.approx([100., 78.2, 78.2])
    assert metrics['halted'] is True
    assert len(trace) == 2
    first, tail = trace
    assert first['portfolio_stop_hit'] and first['exit_executed']
    assert not first['halted_before'] and first['halted_after']
    assert tail['halted_before'] and tail['halted_after']
    assert tail['target_position'] == tail['exposure'] == tail['closing_notional'] == 0.
    assert tail['fee_dollars'] == tail['impact_dollars'] == tail['turnover_dollars'] == 0.
    assert tail['nav_before'] == tail['nav_after'] == pytest.approx(78.2)


def test_trace_retained_contracts_and_default_results_are_identical():
    args = dict(fee_rate=0., price_impact=0., funding_rate=0.)
    plain = run([100., 110., 121.], [0., 1., np.nan], **args)
    trace = []
    traced = run([100., 110., 121.], [0., 1., np.nan], trace=trace, **args)
    assert traced == plain
    assert traced[0] == pytest.approx([100., 110., 121.])
    assert trace[-1]['target_position'] is None
    assert trace[-1]['exposure'] == pytest.approx(1.)
    assert trace[-1]['turnover_dollars'] == 0.
    assert trace[-1]['closing_notional'] == pytest.approx(121.)


def test_flat_unavailable_mark_is_null_in_trace_and_initial_nav_is_not_a_return():
    trace = []
    equity, _ = run([100., np.nan], [0., 0.], trace=trace,
                    fee_rate=0., price_impact=0., funding_rate=0.)
    assert equity == [100., 100.]
    assert len(trace) == 1 and trace[0]['mark_return'] is None
    assert trace[0]['gross_dollars'] == trace[0]['exposure'] == 0.
    json.dumps(trace, allow_nan=False)

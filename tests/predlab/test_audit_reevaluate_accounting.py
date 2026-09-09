"""Synthetic-only contracts for the registered accounting reevaluation wrapper."""
import json
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from scripts import audit_reevaluate_accounting_2026_09_09 as subject


def gate():
    return json.loads(Path('data/predlab/gates.json').read_text())['audit_reevaluation_2026_09_09']


def test_frozen_cell_and_dsr_denominators():
    g = gate()
    assert [len(g['families'][f]['cells']) for f in subject.FAMILIES] == [12, 6, 6]
    assert [g['families'][f]['original_dsr_n'] for f in subject.FAMILIES] == [74, 87, 100]
    assert g['current_dsr']['n_trials'] == 150
    assert sum(len(g['families'][f]['cells']) for f in subject.FAMILIES) == 24


def test_wrapper_weekly_book_keeps_contracts_and_charges_only_rebalance():
    ix = pd.date_range('2021-01-04', periods=3, tz='UTC')
    returns = pd.DataFrame({'a': [0., .1, .1], 'b': 0.}, index=ix)
    net = subject.weekly_book({ix[0]: ['a', 'b']}, ix[:1], returns, cost_bps=0)
    assert net.index.equals(ix[1:])
    assert (1+net).prod() == pytest.approx(1.105)
    fee = subject.weekly_book({ix[0]: ['a', 'b']}, ix[:1], returns, cost_bps=10)
    assert (1+fee).prod() == pytest.approx(1.104)


def test_wrapper_cannot_turn_missing_held_bar_into_zero():
    ix = pd.date_range('2021-01-04', periods=3, tz='UTC')
    ret = pd.DataFrame({'a': [0., .1, np.nan]}, index=ix)
    with pytest.raises(ValueError, match='missing_held_return'):
        subject.weekly_book({ix[0]: ['a']}, ix[:1], ret, 0)


def test_liq_wrapper_compounds_hourly_and_keeps_zero_clock():
    ix = pd.date_range('2021-01-01', periods=48, freq='h', tz='UTC')
    r = pd.DataFrame({'a': [0.5, -0.1] + [0.]*46}, index=ix)
    w = pd.DataFrame({'a': [.1]*48}, index=ix)
    net = subject.hourly_book(w, r, 0., 0.)
    assert net.tolist() == pytest.approx([.0395, 0.])


def test_missing_funding_rejects_daily_carry():
    ix = pd.date_range('2021-01-01', periods=3, tz='UTC')
    w = pd.DataFrame({'a': .5, 'b': -.5}, index=ix)
    r = pd.DataFrame(0., index=ix, columns=w.columns)
    funding = r.copy(); funding.loc[ix[1], 'a'] = np.nan
    with pytest.raises(ValueError, match='missing_held_funding'):
        subject.carry_book(w, r, funding, 0., 0.)


def test_all_forensics_run_even_when_primary_gate_fails():
    f = gate()['families']['momentum']
    ix = pd.date_range('2021-01-01', periods=100, tz='UTC')
    calls = []
    def replay(config, cost, convention):
        calls.append((cost, convention))
        return pd.Series(np.tile([-.02, .001], 50), index=ix)
    p = subject.Prepared(replay=replay, expected_clock=ix,
                         placebo=lambda config, run: {'status': 'computed' if run else 'not_run_primary_gate_failed'})
    result, streams = subject.evaluate_cell(f['cells'][0], f, 150, p)
    assert calls == [(10., 'simple'), (0., 'simple'), (20., 'simple'), (10., 'log')]
    assert len(streams) == 4
    assert result['original_gate_pass'] is False
    assert result['remaining_gates']['status'] == 'not_run_primary_gate_failed'
    assert result['corrected']['original_dsr_n'] == 74
    assert result['corrected']['current_dsr_n'] == 150


def test_current_dsr_cannot_hide_original_gate_survivor(monkeypatch):
    f = gate()['families']['carry']
    ix = pd.date_range('2021-01-01', periods=100, tz='UTC')
    ret = pd.Series(np.tile([.001, .002], 50), index=ix)
    monkeypatch.setattr(subject, 'dsr', lambda values, n: .95 if n == 87 else .2)
    placebo = Mock(return_value={'status': 'computed', 'placebo_p': .01})
    p = subject.Prepared(replay=lambda *args: ret, expected_clock=ix, placebo=placebo)
    result, _ = subject.evaluate_cell(f['cells'][0], f, 150, p)
    placebo.assert_called_once_with(f['cells'][0], True)
    assert result['original_gate_pass'] is True
    assert result['current_dsr_policy_pass'] is False


def test_unknown_clock_does_not_become_success():
    f = gate()['families']['carry']
    ix = pd.date_range('2021-01-01', periods=100, tz='UTC')
    p = subject.Prepared(replay=lambda *args: pd.Series(.01, index=ix[:-1]),
                         expected_clock=ix, placebo=lambda *a: {})
    result, _ = subject.evaluate_cell(f['cells'][0], f, 150, p)
    assert result['status'] == 'blocked'
    assert 'clock' in result['reason']
    assert result['original_gate_pass'] is None


def test_missing_family_source_preserves_all_registered_cells(monkeypatch):
    g = gate()
    ctx = Mock(gate=g, family_gate=g['families']['momentum'])
    monkeypatch.setattr(subject, 'original_results', lambda *a: {})
    monkeypatch.setitem(subject.PREPARERS, 'momentum', Mock(side_effect=FileNotFoundError('missing fixture')))
    subject.run_family(ctx, 'momentum')
    payload, cells = ctx.finish.call_args.args
    assert len(cells) == 12
    assert {c['id'] for c in cells} == {c['id'] for c in g['families']['momentum']['cells']}
    assert all(c['metrics']['status'] == 'blocked' for c in cells)
    assert payload['status'] == 'blocked'


def test_skipped_liq_draws_leave_identical_rng_state():
    ix = pd.date_range('2021-01-01', periods=100, freq='h', tz='UTC')
    trig = pd.DataFrame({'a': np.arange(100) % 17 == 0, 'b': False, 'c': np.arange(100) % 23 == 0}, index=ix)
    mask = pd.DataFrame(True, index=ix, columns=trig.columns)
    direct = np.random.default_rng(48)
    skipped = np.random.default_rng(48)
    for family in ('shift', 'random'):
        for _ in range(7):
            subject.draw_liq_placebo(trig, mask, direct, family, materialize=True)
            assert subject.draw_liq_placebo(trig, mask, skipped, family, materialize=False) is None
    assert direct.bit_generator.state == skipped.bit_generator.state
    pd.testing.assert_frame_equal(subject.draw_liq_placebo(trig, mask, direct, 'shift', True),
                                  subject.draw_liq_placebo(trig, mask, skipped, 'shift', True))


def test_p2_keeps_original_sum_and_compounding_separate():
    ix = pd.date_range('2021-01-01', periods=4, freq='h', tz='UTC')
    r = pd.DataFrame({'a': [0., .5, -.1, 0.]}, index=ix)
    trig = pd.DataFrame({'a': [True, False, False, True]}, index=ix)
    out = subject.forward_probe(r, trig, 2)
    assert out['mean_original_sum'] == pytest.approx(.4)
    assert out['mean_compounded_return'] == pytest.approx(.35)
    assert out['n_events'] == 2 and out['n_endpoint_censored'] == 1
    assert out['n_missing_internal_window'] == 0


def test_p2_missing_interior_is_unavailable_not_dropped():
    ix = pd.date_range('2021-01-01', periods=4, freq='h', tz='UTC')
    r = pd.DataFrame({'a': [0., np.nan, .1, 0.]}, index=ix)
    trig = pd.DataFrame({'a': [True, False, False, False]}, index=ix)
    out = subject.forward_probe(r, trig, 2)
    assert out['n_missing_internal_window'] == 1
    assert out['status'] == 'unavailable'


def test_dsr_degenerate_is_unavailable():
    assert subject.dsr(np.zeros(100), 74) is None


def test_daily_loader_filters_every_manifest_file_before_consumption(tmp_path):
    source = tmp_path/'source'
    (source/'xsect').mkdir(parents=True)
    manifest = source/'xsect/klines_manifest.json'
    manifest.write_text(json.dumps({'BTCUSDT': {}, 'AUSDT': {}, 'FUTUREUSDT': {}}))
    ix = pd.date_range(*subject.DEV, tz='UTC')
    frame = pd.DataFrame({'close': 100., 'quote_volume': 1e7}, index=ix)
    def reader(path, **kwargs):
        assert kwargs == {'start': None, 'end_exclusive': '2025-04-01'}
        return frame.iloc[:0] if path.stem == 'FUTUREUSDT' else frame
    ctx = Mock(gate={'source_roots': [str(source)]}, track=lambda p: p,
               read_market=Mock(side_effect=reader))
    loaded = subject.load_daily(ctx)
    assert sorted(loaded) == ['AUSDT', 'BTCUSDT']
    assert ctx.read_market.call_count == 3


def test_original_count_mismatch_does_not_silently_rebase(tmp_path):
    source = tmp_path/'source'
    target = source/'rebuild/carry_xs/dev_results.json'
    target.parent.mkdir(parents=True)
    f = gate()['families']['carry']
    target.write_text(json.dumps({'results': [{'config': c, 'metrics': {'n_trials_at_eval': 1}}
                                             for c in f['cells']]}))
    ctx = Mock(gate={'source_roots': [str(source)]}, family_gate=f, track=lambda p: p)
    with pytest.raises(ValueError, match='original DSR denominator differs'):
        subject.original_results(ctx, 'carry')


def test_p1_missing_benchmark_hour_is_unavailable_not_negative():
    ix = pd.date_range('2021-01-01T00:00:00Z', '2021-04-05T23:00:00Z', freq='h', tz='UTC')
    close = pd.DataFrame(100., index=ix, columns=subject.MAJORS)
    volume = close*1e5
    observed = subject.p1_probe(close, volume, benchmark_dates=('2021-04-05',), required=1)
    assert observed['pass'] is False
    close.loc[pd.Timestamp('2021-04-05T02:00:00Z'), 'BTCUSDT'] = np.nan
    missing = subject.p1_probe(close, volume, benchmark_dates=('2021-04-05',), required=1)
    assert missing['pass'] is None
    assert missing['n_unavailable_benchmark_hours'] > 0


def test_daily_return_builder_accepts_market_utc_index_and_registered_date_endpoint():
    ix = pd.date_range('2021-01-01', periods=3, tz='UTC')
    frame = pd.DataFrame({'close': [100., 110., 121.]}, index=ix)
    returns = subject._daily_returns({'a': frame}, ['a'])
    assert returns.index[-1] == pd.Timestamp('2025-03-31', tz='UTC')
    assert np.expm1(returns.a.iloc[1]) == pytest.approx(.1)
    assert returns.a.iloc[3:].isna().all()


def test_registered_clocks_include_last_hour_without_mixed_timezone_failure():
    ix = subject.utc_clock('2021-01-01', '2025-03-31T23:00:00Z', 'h')
    assert len(ix) == 1551*24
    assert ix[-1] == pd.Timestamp('2025-03-31T23:00:00Z')


def test_p1_known_hits_cannot_be_undone_by_other_missing_coin(monkeypatch):
    ix = subject.utc_clock('2021-01-01', '2021-04-09T23:00:00Z', 'h')
    close = pd.DataFrame(100., index=ix, columns=subject.MAJORS)
    volume = close*1e5
    dates = tuple(f'2021-04-{i:02}' for i in range(5, 10))
    triggers = pd.DataFrame(False, index=ix, columns=subject.MAJORS)
    for day in dates[:4]:
        triggers.loc[pd.Timestamp(day, tz='UTC'), 'BTCUSDT'] = True
        close.loc[pd.Timestamp(day, tz='UTC'), 'ETHUSDT'] = np.nan
    monkeypatch.setattr(subject.liq_fade, 'cascade_triggers', lambda *a: triggers)
    result = subject.p1_probe(close, volume, dates)
    assert result['pass'] is True
    assert result['n_known_hit_days'] == 4
    assert result['n_unavailable_benchmark_hours'] > 0


def test_p2_known_passing_cell_survives_another_unavailable_cell():
    cells = {'a': {'status': 'computed', 'gate_value': .003},
             'b': {'status': 'unavailable', 'gate_value': .2}}
    assert subject.p2_gate(cells)['pass'] is True
    cells['a']['gate_value'] = .001
    assert subject.p2_gate(cells)['pass'] is None
    cells['b'] = {'status': 'computed', 'gate_value': .001}
    assert subject.p2_gate(cells)['pass'] is False


@pytest.mark.parametrize('primary_pass', [True, False])
def test_unavailable_required_benchmark_preserves_actual_cell(monkeypatch, primary_pass):
    f = gate()['families']['momentum']
    ix = pd.date_range('2021-01-01', periods=100, tz='UTC')
    ret = pd.Series(np.tile([.001, .002] if primary_pass else [-.02, .001], 50), index=ix)
    monkeypatch.setattr(subject, 'dsr', lambda *a: .99)
    placebo = Mock(return_value={'status': 'computed', 'placebo_p': .01})
    p = subject.Prepared(replay=lambda *a: ret, expected_clock=ix, placebo=placebo,
                         benchmark=None, benchmark_required=True)
    out, streams = subject.evaluate_cell(f['cells'][0], f, 150, p)
    assert len(streams) == 4
    assert 'corrected' in out
    if primary_pass:
        assert out['original_gate_pass'] is None
        assert out['remaining_gates']['status'] == 'blocked'
        assert 'benchmark' in out['remaining_gates']['reason']
    else:
        assert out['original_gate_pass'] is False
        assert out['remaining_gates']['status'] == 'not_run_primary_gate_failed'


def test_momentum_benchmark_failure_does_not_abort_cell_preparation(monkeypatch):
    names = ['BTCUSDT']+[f'S{i}' for i in range(19)]
    ix = subject.utc_clock('2020-12-01', subject.DEV[1])
    market = {name: pd.DataFrame({'close': 100., 'quote_volume': 1e7}, index=ix) for name in names}
    monkeypatch.setattr(subject, 'load_daily', lambda ctx: market)
    monkeypatch.setattr(subject.universe, 'eligibility', lambda *a, **k: names)
    monkeypatch.setattr(subject.portfolio, 'momentum_scores', lambda *a: {name: i for i, name in enumerate(names)})
    monkeypatch.setattr(subject, 'weekly_book', Mock(side_effect=ValueError('missing_held_return benchmark_only')))
    g = gate()
    ctx = Mock(gate=g, family_gate=g['families']['momentum'])
    prepared = subject.prepare_momentum(ctx)
    assert prepared.benchmark is None and prepared.benchmark_required
    assert prepared.metadata['benchmark']['status'] == 'unavailable'
    assert 'missing_held_return' in prepared.metadata['benchmark']['reason']

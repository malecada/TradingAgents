"""Synthetic journal admission and accounting-display regressions."""
import copy
import json
from datetime import date, timedelta

import pytest

from tradingagents.monitor.predlab import PredlabSource, derive_account, derive_book, derive_nav


def v2_rows():
    rows = []
    for i, (base, overlay, br, nr) in enumerate([
        (1., 1., None, None), (1.1, 1.03, .1, .03), (.99, .9888, -.1, -.04)
    ]):
        day = date(2026, 9, 1) + timedelta(days=i)
        rows.append(dict(asof=day.isoformat(), written_utc=f'{day}T00:20:00+00:00',
            journal_version=2, accounting_version='pretrade-nav-v1',
            weights={'A': 1.}, n_universe=1, breadth=1,
            realized_book_ret=None if i == 0 else .9,
            realized_mark_ret=None, realized_base_net_ret=br, realized_net_ret=nr,
            base_state={'nav': base, 'notionals': {}}, overlay_state={'nav': overlay, 'notionals': {}},
            base_measurement=None if i == 0 else {'net': br, 'gross': br + .001, 'carry': 0., 'cost': .001, 'turnover': 1.},
            overlay_measurement=None if i == 0 else {'net': nr, 'gross': nr + .001, 'carry': 0., 'cost': .001, 'turnover': 1.},
            measurement_status='incomplete' if i == 0 else 'complete',
            measurement_reason='initial measurement; scale warmup' if i == 0 else '',
            executed_scale=2., measurement_scale=None if i == 0 else 2.,
            vt15_b100_scale=2., mark_coverage='complete'))
    return rows


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))


def paper_path(root, name='journal_champion_v2.jsonl'):
    return root / 'predlab' / 's1_paper' / name


def test_v2_net_streams_use_saved_states_without_gross_or_second_scaling():
    rows = v2_rows()
    base = derive_book(rows, 'vt15_b100_scale')
    overlay = derive_nav(rows, 'vt15_b100_scale')
    assert [p['value'] for p in base['equity']] == pytest.approx([100., 110., 99.])
    assert [p['value'] for p in overlay['series']] == pytest.approx([100., 103., 98.88])
    assert base['cards']['cum_return'] == pytest.approx(-.01)
    assert overlay['cards']['nav_cum_return'] == pytest.approx(-.0112)
    assert base['measurement_status'] == overlay['measurement_status'] == 'corrected_v2'


@pytest.mark.parametrize('problem', ['gap', 'null', 'state_mismatch', 'later_baseline'])
def test_unknown_interval_is_never_dropped_or_reconnected(problem):
    rows = v2_rows()
    if problem == 'gap':
        rows.pop(1)
    elif problem == 'null':
        rows[1]['realized_base_net_ret'] = None
        rows[1]['realized_net_ret'] = None
    elif problem == 'state_mismatch':
        rows[1]['base_state']['nav'] = 2.
        rows[1]['overlay_state']['nav'] = 2.
    else:
        rows[1] = {**rows[0], 'asof': rows[1]['asof']}
    for block, series, card in [(derive_book(rows, 'vt15_b100_scale'), 'equity', 'cum_return'),
                                (derive_nav(rows, 'vt15_b100_scale'), 'series', 'nav_cum_return')]:
        assert [p['ts'] for p in block[series]] == ['2026-09-01', '2026-09-02', '2026-09-03']
        assert [p['value'] for p in block[series]][1:] == [None, None]
        assert block['cards'][card] is None
        assert block['measurement_status'] in {'incomplete', 'invalid'}


@pytest.mark.parametrize('problem', ['duplicate', 'mixed_version', 'nan', 'inf', 'bad_state', 'bad_weights'])
def test_invalid_v2_cannot_claim_complete_measurement(tmp_path, problem):
    rows = v2_rows()
    if problem == 'duplicate': rows.insert(2, copy.deepcopy(rows[1]))
    elif problem == 'mixed_version': rows[1].pop('journal_version')
    elif problem == 'nan': rows[1]['realized_base_net_ret'] = float('nan')
    elif problem == 'inf': rows[1]['base_state']['notionals']['A'] = float('inf')
    elif problem == 'bad_state': rows[1]['base_state'] = []
    else: rows[1]['weights'] = ['A']
    write_rows(paper_path(tmp_path), rows)
    payload = PredlabSource(str(tmp_path)).payload()
    assert payload['performance']['measurement']['books']['champion']['status'] in {'invalid', 'incomplete'}
    assert payload['performance']['books']['champion']['cards']['cum_return'] is None
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize('v2_content', ['', '{bad json\n', '{"asof":"bad"}\n'])
def test_existing_empty_or_corrupt_v2_never_falls_back_to_legacy(tmp_path, v2_content):
    write_rows(paper_path(tmp_path, 'journal_champion.jsonl'), [{'asof': '2026-09-01', 'weights': {}, 'realized_book_ret': .9}])
    path = paper_path(tmp_path)
    path.write_text(v2_content)
    payload = PredlabSource(str(tmp_path)).payload()
    descriptor = payload['performance']['measurement']['books']['champion']
    assert descriptor['journal'] == 'journal_champion_v2.jsonl'
    assert descriptor['status'] in {'incomplete', 'invalid'}
    assert payload['books']['champion'] is None
    assert payload['performance']['books']['champion'] is None
    assert payload['health']['books']['champion']['legacy_rows'] == 1


def test_malformed_line_invalidates_whole_complete_claim_even_with_valid_rows(tmp_path):
    write_rows(paper_path(tmp_path), v2_rows())
    with paper_path(tmp_path).open('a') as fh: fh.write('{bad json\n')
    payload = PredlabSource(str(tmp_path)).payload()
    assert payload['performance']['measurement']['books']['champion']['status'] == 'invalid'
    assert payload['performance']['books']['champion']['cards']['cum_return'] is None
    assert payload['health']['books']['champion']['malformed'] == 1


def test_legacy_only_has_composition_and_health_but_no_net_performance(tmp_path):
    write_rows(paper_path(tmp_path, 'journal_champion.jsonl'), [
        {'asof': '2026-09-01', 'weights': {'A': 1.}, 'realized_book_ret': None},
        {'asof': '2026-09-02', 'weights': {'A': 1.}, 'realized_book_ret': .9}])
    payload = PredlabSource(str(tmp_path)).payload()
    assert payload['books']['champion']['longs'] == [{'symbol': 'A', 'weight': 1.}]
    assert payload['health']['books']['champion']['rows'] == 2
    assert payload['performance']['books']['champion'] is None
    assert payload['performance']['nav']['champion'] is None
    assert payload['performance']['measurement']['books']['champion']['status'] == 'legacy_only'


def test_overlay_warmup_is_known_state_but_not_zero_performance():
    rows = v2_rows()
    for row in rows:
        row.update(executed_scale=None, measurement_scale=None, realized_net_ret=None,
                   overlay_measurement=None, overlay_state={'nav': 1., 'notionals': {}},
                   measurement_status='incomplete', measurement_reason='scale warmup')
    rows[-1]['executed_scale'] = 2.
    base, overlay = derive_book(rows, 'vt15_b100_scale'), derive_nav(rows, 'vt15_b100_scale')
    assert base['measurement_status'] == 'corrected_v2'
    assert base['cards']['cum_return'] == pytest.approx(-.01)
    assert overlay['measurement_status'] == 'warmup'
    assert overlay['cards']['nav_cum_return'] is None
    assert len(overlay['series']) == 3
    assert overlay['cards']['active_days'] == 0


def test_current_quote_incomplete_cannot_be_served_as_fully_complete():
    rows = v2_rows()
    rows[-1].update(measurement_status='incomplete', mark_coverage='incomplete', measurement_reason='current quotes incomplete')
    block = derive_book(rows, 'vt15_b100_scale')
    assert block['measurement_status'] == 'incomplete'
    assert block['cards']['cum_return'] is None


def test_suspended_gate_and_removed_reference_do_not_serve_invalidated_scores(tmp_path):
    write_rows(paper_path(tmp_path), v2_rows())
    (tmp_path / 'predlab' / 'gates.json').write_text(json.dumps({'predlab_opt': {'final_champion': {'dev_metrics': {'ovl_sr_full': 1.892}}}}))
    (tmp_path / 'predlab' / 'champion_backtest.json').write_text(json.dumps({'systems': {'new': {'yearly_ovl': {'2025': {'sr': 9.}}}}}))
    payload = PredlabSource(str(tmp_path)).payload()
    assert payload['performance']['reference'] is None
    assert payload['performance']['backtest_yearly'] is None
    assert payload['gate']['status'] == 'suspended_after_audit'
    assert payload['gate']['threshold_sr'] is None
    assert payload['gate']['running']['sr'] is None


def account_row(day, status='reconciled', **over):
    row = dict(asof=day, executed_utc=f'{day}T00:20:00+00:00', journal_version=2,
        equity_before=1000., status=status, dry_run=False, orders_placed=2,
        orders_filled=2, target_qty={'A': 1.}, actual_positions={'A': 1.}, residual_qty={})
    row.update(over)
    return row


def test_account_intent_then_reconciled_update_is_one_verified_cycle():
    rows = [account_row('2026-09-01', 'intent', orders_placed=0), account_row('2026-09-01'),
            account_row('2026-09-02', equity_before=1050.)]
    block = derive_account(rows, False)
    assert block['measurement_status'] == 'reconciled'
    assert block['cards']['n_cycles'] == 2
    assert block['cards']['orders_total'] == 4
    assert [p['value'] for p in block['series']] == [100., 105.]


@pytest.mark.parametrize('problem', ['intent', 'incomplete', 'dry_run', 'residual', 'missing_positions', 'date_only', 'gap'])
def test_account_unknown_execution_is_not_inferred_from_journal_date(problem):
    rows = [account_row('2026-09-01'), account_row('2026-09-02')]
    if problem in {'intent', 'incomplete'}: rows[1]['status'] = problem
    elif problem == 'dry_run': rows[1]['dry_run'] = True
    elif problem == 'residual': rows[1]['residual_qty'] = {'A': .1}
    elif problem == 'missing_positions': rows[1].pop('actual_positions')
    elif problem == 'date_only': rows[1].pop('status')
    else: rows[1]['asof'] = '2026-09-03'
    block = derive_account(rows, False)
    assert block['measurement_status'] in {'pending', 'incomplete', 'invalid'}
    assert block['cards']['cum_return'] is None
    assert block['series'][-1]['value'] is None


def test_live_v2_file_is_selected_even_when_empty(tmp_path):
    root = tmp_path / 'predlab' / 's1_live'
    write_rows(root / 'journal_live.jsonl', [{'asof': '2026-09-01', 'equity_before': 9999.}])
    (root / 'journal_live_v2.jsonl').write_text('')
    payload = PredlabSource(str(tmp_path)).payload()
    block = payload['performance']['account']['live']
    assert block['measurement_status'] == 'incomplete'
    assert block['cards']['equity'] is None

@pytest.mark.parametrize('bad_version', [None, 'log-return-v1', 'pretrade-nav-v2'])
def test_paper_accounting_convention_is_required_and_fixed(tmp_path, bad_version):
    rows = v2_rows()
    rows[1]['accounting_version'] = bad_version
    write_rows(paper_path(tmp_path), rows)
    payload = PredlabSource(str(tmp_path)).payload()
    assert payload['performance']['measurement']['books']['champion']['status'] == 'invalid'
    assert payload['performance']['books']['champion']['cards']['cum_return'] is None
    assert payload['performance']['measurement']['status'] == 'invalid'


def test_known_overlay_warmup_is_flat_and_counts_base_returns():
    rows = v2_rows()
    for row in rows:
        row.update(executed_scale=None, measurement_scale=None, realized_net_ret=None,
                   overlay_measurement=None, overlay_state={'nav': 1., 'notionals': {}},
                   measurement_status='incomplete', measurement_reason='scale warmup')
    block = derive_nav(rows, 'vt15_b100_scale')
    assert [p['value'] for p in block['series']] == [100., 100., 100.]
    assert block['cards']['warmup'] == {'n': 2, 'required': 20}
    assert block['cards']['nav_cum_return'] is None


@pytest.mark.parametrize('key', ['realized_base_net_ret', 'base_measurement'])
def test_absent_baseline_field_is_not_an_initial_null_measurement(key):
    rows = v2_rows()
    rows[0].pop(key)
    block = derive_book(rows, 'vt15_b100_scale')
    assert block['measurement_status'] == 'incomplete'
    assert block['cards']['cum_return'] is None


@pytest.mark.parametrize('value', ['not-a-timestamp', '2026-09-02T00:20:00', [], {}])
def test_account_requires_real_timezone_aware_observation_timestamp(value):
    rows = [account_row('2026-09-01'), account_row('2026-09-02', executed_utc=value)]
    block = derive_account(rows, False)
    assert block['measurement_status'] in {'invalid', 'incomplete'}
    assert block['cards']['cum_return'] is None


def test_invalid_composition_and_health_metadata_never_crash_payload(tmp_path):
    rows = v2_rows()
    rows[-2]['weights'] = 123
    rows[-1].update(written_utc={}, membership_hash=[])
    write_rows(paper_path(tmp_path), rows)
    payload = PredlabSource(str(tmp_path)).payload()
    assert payload['health']['books']['champion']['written_utc'] is None
    assert payload['books']['champion']['membership_hash'] is None
    assert payload['performance']['measurement']['books']['champion']['status'] == 'invalid'


def test_future_written_timestamp_cannot_claim_fresh():
    from datetime import datetime, timezone
    from tradingagents.monitor.predlab import book_health
    row = v2_rows()[0]
    row['written_utc'] = '2026-09-02T00:20:00+00:00'
    assert book_health([row], 0, datetime(2026, 9, 1, tzinfo=timezone.utc))['stale'] is True

@pytest.mark.parametrize('problem', ['missing_weights', 'bad_status', 'bad_reason'])
def test_malformed_required_paper_metadata_fails_closed(tmp_path, problem):
    rows = v2_rows()
    if problem == 'missing_weights': rows[1].pop('weights')
    elif problem == 'bad_status': rows[1]['measurement_status'] = []
    else: rows[1]['measurement_reason'] = {'unexpected': 'object'}
    write_rows(paper_path(tmp_path), rows)
    payload = PredlabSource(str(tmp_path)).payload()
    assert payload['performance']['measurement']['books']['champion']['status'] == 'invalid'
    assert payload['performance']['books']['champion']['cards']['cum_return'] is None


def test_legacy_schema_inside_v2_account_file_is_invalid(tmp_path):
    path = tmp_path / 'predlab' / 's1_live' / 'journal_live_v2.jsonl'
    write_rows(path, [{'asof': '2026-09-01', 'equity_before': 1000.}])
    block = PredlabSource(str(tmp_path)).payload()['performance']['account']['live']
    assert block['reconciliation_status'] == 'invalid'
    assert block['cards']['equity'] is None


@pytest.mark.parametrize('scaled', [False, True])
def test_actual_paper_writer_schema_is_admitted_without_network(tmp_path, monkeypatch, scaled):
    import numpy as np
    import pandas as pd
    from scripts import predlab_s1_paper as paper
    days = pd.date_range('2026-06-20', '2026-09-02', tz='UTC')
    names = [f'S{i:03}' for i in range(205)]
    close = pd.DataFrame(100., index=days, columns=names)
    panels = {'close': close, 'qv': close.copy(), 'funding': close * 0.,
              'park': pd.DataFrame(np.tile(np.arange(1., 206.), (len(days), 1)), index=days, columns=names)}
    if scaled:
        monkeypatch.setattr(paper, 'vt_scale', lambda *a, **k: .5)
    path = paper_path(tmp_path)
    path.parent.mkdir(parents=True)
    for day in ['2026-08-31', '2026-09-01', '2026-09-02']:
        outcome = paper.journal_one(path, {k: v.loc[:day] for k, v in panels.items()},
                                   'ewma_20', 'vt15_b100_scale', .15, marks={s: 100. for s in names})
        assert not outcome.startswith('WAIT')
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert rows[0]['realized_base_net_ret'] is None and rows[0]['base_measurement'] is None
    block = PredlabSource(str(tmp_path)).payload()['performance']
    assert block['books']['champion']['measurement_status'] == 'corrected_v2'
    assert block['books']['champion']['cards']['cum_return'] == pytest.approx(rows[-1]['base_state']['nav'] - 1.)
    assert block['books']['champion']['equity'][1]['value'] == pytest.approx(99.9)
    assert block['nav']['champion']['measurement_status'] == ('corrected_v2' if scaled else 'warmup')
    if scaled:
        assert block['nav']['champion']['series'][1]['value'] == pytest.approx(99.95)
    else:
        assert block['nav']['champion']['cards']['nav_cum_return'] is None
        assert block['nav']['champion']['cards']['warmup'] == {'n': 2, 'required': 20}

@pytest.mark.parametrize('prefix', ['base', 'overlay'])
def test_nonflat_initial_state_cannot_disappear_without_settlement(prefix):
    rows = v2_rows()
    if prefix == 'overlay':
        for row in rows:
            row.update(executed_scale=None, measurement_scale=None, realized_net_ret=None,
                       overlay_measurement=None, overlay_state={'nav': 1., 'notionals': {}},
                       measurement_status='incomplete', measurement_reason='scale warmup')
    rows[0][prefix + '_state']['notionals'] = {'A': .5}
    block = derive_book(rows, 'vt15_b100_scale') if prefix == 'base' else derive_nav(rows, 'vt15_b100_scale')
    points = block['equity'] if prefix == 'base' else block['series']
    assert [point['ts'] for point in points] == [row['asof'] for row in rows]
    assert [point['value'] for point in points] == [None, None, None]
    assert block['measurement_status'] == 'incomplete'
    assert 'initial' in block['measurement_reason']
    key = 'cum_return' if prefix == 'base' else 'nav_cum_return'
    assert block['cards'][key] is None


@pytest.mark.parametrize('prefix', ['base', 'overlay'])
def test_zero_notional_entries_are_a_flat_initial_state(prefix):
    rows = v2_rows()
    rows[0][prefix + '_state']['notionals'] = {'A': 0., 'B': -0.}
    block = derive_book(rows, 'vt15_b100_scale') if prefix == 'base' else derive_nav(rows, 'vt15_b100_scale')
    assert block['measurement_status'] == 'corrected_v2'

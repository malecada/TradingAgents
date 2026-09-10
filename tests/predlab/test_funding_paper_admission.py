"""Two-book snapshot preflight, using synthetic panels and local temp journals."""
import json

import pandas as pd
import pytest

from scripts import predlab_s1_paper as paper
from tests.predlab.test_paper_repair import panel
from .test_funding_snapshot import snapshot


def prepare_inputs(tmp_path, *, initial=False):
    panels = panel()
    marks = {symbol: 100. for symbol in panels['close'].columns}
    journals = (tmp_path / 'journal_v2.jsonl', tmp_path / 'journal_champion_v2.jsonl')
    if not initial:
        for j, signal, key in zip(journals, ['park_5', 'ewma_20'], ['vt10_scale', 'vt15_b100_scale']):
            paper.journal_one(j, {k: v.loc[:'2026-09-01'] for k, v in panels.items()}, signal, key, .15, marks=marks)
    path = tmp_path / 'capture'
    snapshot(path, names=tuple(panels['close'].columns))
    return panels, marks, journals, path


def run_pair(panels, marks, journals, path):
    return paper.journal_pair(panels, marks=marks, journals=journals, funding_snapshot=path,
                              trade_day=pd.Timestamp('2026-09-03', tz='UTC'),
                              measurement_time=pd.Timestamp('2026-09-03T00:20Z'))


def test_delayed_snapshot_waits_without_poisoning_and_same_day_retry_succeeds(tmp_path):
    panels, marks, journals, path = prepare_inputs(tmp_path)
    before = [j.read_bytes() for j in journals]
    outcome = run_pair(panels, marks, journals, path / 'not-yet-published')
    assert outcome[0].startswith('WAIT:')
    assert [j.read_bytes() for j in journals] == before
    outcome = run_pair(panels, marks, journals, path)
    assert all(not message.startswith('WAIT:') for message in outcome)
    for journal in journals:
        rows = [json.loads(line) for line in journal.read_text().splitlines()]
        assert len(rows) == 2 and rows[-1]['base_state'] is not None
        assert rows[-1]['funding_coverage']['snapshot']['sha256']


@pytest.mark.parametrize('problem', ['missing_quote', 'broken_state', 'gap', 'legacy', 'held_price'])
def test_either_book_failure_blocks_both_appends(tmp_path, problem):
    panels, marks, journals, path = prepare_inputs(tmp_path)
    rows = [json.loads(j.read_text()) for j in journals]
    if problem == 'missing_quote': marks.clear()
    elif problem == 'broken_state': rows[1]['base_state'] = None
    elif problem == 'gap': rows[1]['asof'] = '2026-08-31'
    elif problem == 'legacy': rows[1].pop('journal_version')
    else:
        held = next(iter(rows[1]['weights']))
        panels['close'].loc['2026-09-02', held] = float('nan')
    for j, row in zip(journals, rows): j.write_text(json.dumps(row) + '\n')
    before = [j.read_bytes() for j in journals]
    assert run_pair(panels, marks, journals, path)[0].startswith('WAIT:')
    assert [j.read_bytes() for j in journals] == before


def test_flat_initialization_and_overlay_warmup_remain_legitimate(tmp_path):
    panels, marks, journals, path = prepare_inputs(tmp_path, initial=True)
    outcome = run_pair(panels, marks, journals, path)
    assert len(outcome) == 2 and all(not x.startswith('WAIT:') for x in outcome)
    for j in journals:
        row = json.loads(j.read_text())
        assert row['base_state'] == {'nav': 1., 'notionals': {}}
        assert row['base_measurement'] is None and row['executed_scale'] is None


def test_configured_snapshot_does_not_call_legacy_loader(tmp_path, monkeypatch):
    monkeypatch.setattr(paper, 'load_observed_funding', lambda *a, **k: pytest.fail('legacy fallback'))
    with pytest.raises(ValueError):
        paper._attach_funding(panel(), funding_snapshot=tmp_path / 'missing',
                              measurement_time='2026-09-03T00:20Z')

@pytest.mark.parametrize('problem', ['missing_scale', 'nonfinite_scale', 'missing_baseline_field',
                                    'measurement_status', 'nonfinite_diagnostic'])
def test_existing_malformed_measurement_cannot_be_advanced(tmp_path, problem):
    panels, marks, journals, path = prepare_inputs(tmp_path)
    row = json.loads(journals[1].read_text())
    if problem == 'missing_scale': row.pop('executed_scale')
    elif problem == 'nonfinite_scale': row['executed_scale'] = float('nan')
    elif problem == 'missing_baseline_field': row.pop('base_measurement')
    elif problem == 'measurement_status': row['measurement_status'] = 'invalid'
    else: row['realized_book_ret'] = float('nan')
    journals[1].write_text(json.dumps(row) + '\n')
    before = [j.read_bytes() for j in journals]
    assert run_pair(panels, marks, journals, path)[0].startswith('WAIT:')
    assert [j.read_bytes() for j in journals] == before


def test_pair_requires_an_explicit_snapshot_without_legacy_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(paper, 'load_observed_funding', lambda *a, **k: pytest.fail('legacy fallback'))
    outcome = paper.journal_pair(panel(), marks={}, funding_snapshot=None,
                                 journals=(tmp_path/'a', tmp_path/'b'))
    assert outcome[0].startswith('WAIT:')


def test_quote_required_for_prior_held_symbol_removed_from_new_targets(tmp_path):
    panels, marks, journals, path = prepare_inputs(tmp_path)
    prior = json.loads(journals[1].read_text())
    removed = next(iter(prior['weights']))
    panels['park'].loc['2026-09-02', removed] = float('nan')
    marks.pop(removed)
    before = [j.read_bytes() for j in journals]
    assert run_pair(panels, marks, journals, path)[0].startswith('WAIT:')
    assert [j.read_bytes() for j in journals] == before


def test_persisted_snapshot_coverage_contains_only_the_settlement_day(tmp_path):
    panels, marks, journals, path = prepare_inputs(tmp_path)
    assert all(not value.startswith('WAIT:') for value in run_pair(panels, marks, journals, path))
    row = json.loads(journals[0].read_text().splitlines()[-1]); coverage = row['funding_coverage']
    assert coverage['snapshot']['sha256'] and coverage['snapshot']['source']['collector_sha256']
    assert len(coverage['capture_statuses']) == len(coverage['requested_symbols']) == 205
    assert coverage['settlement_day'] == '2026-09-02'
    for info in coverage['symbols'].values():
        assert info['requested_days'] == 1
        assert set(info['days']) <= {'2026-09-02T00:00:00+00:00'}


@pytest.mark.parametrize('prior_only', [False, True])
def test_boolean_quote_is_not_a_price_during_opted_in_preflight(tmp_path, prior_only):
    panels, marks, journals, path = prepare_inputs(tmp_path)
    symbol = next(iter(json.loads(journals[1].read_text())['weights']))
    if prior_only: panels['park'].loc['2026-09-02', symbol] = float('nan')
    marks[symbol] = True
    before = [j.read_bytes() for j in journals]
    assert run_pair(panels, marks, journals, path)[0].startswith('WAIT:')
    assert [j.read_bytes() for j in journals] == before

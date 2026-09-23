"""Invented archives and graph summaries only; no empirical price reads."""
import calendar
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import pandas as pd
import pytest

PATH = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/comparison/input_adapter.py'


def adapter():
    assert PATH.exists(), 'matched input adapter is not implemented'
    spec = importlib.util.spec_from_file_location('matched_inputs', PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def archive(month, invalid_day=None):
    unit = 1_000_000 if month >= '2025-01' else 1_000
    start = pd.Timestamp(month + '-01', tz='UTC')
    rows = []
    for day in range(calendar.monthrange(start.year, start.month)[1]):
        opening = int((start + pd.Timedelta(days=day)).timestamp()) * unit
        price = 'bad' if day == invalid_day else '100'
        rows.append(f'{opening},{price},120,90,110,7,{opening+86400*unit-1},770,9,2,220,0')
    target = io.BytesIO()
    name = f'ETHUSDT-1d-{month}'
    with zipfile.ZipFile(target, 'w') as z:
        z.writestr(name+'.csv', '\n'.join(rows)+'\n')
    raw = target.getvalue()
    return raw, (hashlib.sha256(raw).hexdigest()+'  '+name+'.zip\n').encode()


def graph():
    row = dict(day='2022-01-02', source_admitted=True, graph_admitted=True,
               source_status='complete', graph_status='complete', available_at=None,
               historical_availability_verified=False, events=3, nodes=3,
               directed_pairs=3, stars=1, dyads=2, triangles=3,
               overlap_nodes=4, nonzero_nodes=3,
               local40=dict(local40_sums=[1]+[0]*23+[4]+[0]*7+[9]+[0]*7,
                            unique_occurrences=6, overlap_node_count=4, nonzero_nodes=3))
    return dict(global_uniqueness_admitted=True, historical_availability_verified=False, days=[row])


def test_spot_quote_volume_and_assumed_clock():
    result = adapter().spot_month('2024-02', *archive('2024-02'))
    assert len(result) == 29
    assert result.iloc[0]['quote_volume'] == 770
    assert result.iloc[0]['open'] == 100 and result.iloc[0]['close'] == 110
    assert result.iloc[0]['available_at'] == pd.Timestamp('2024-02-02T00:05:00Z')


def test_microseconds_and_unopened_out_of_window_prices():
    result = adapter().spot_month('2025-01', *archive('2025-01', invalid_day=1))
    assert result.day.tolist() == [pd.Timestamp('2025-01-01T00:00:00Z')]


def test_spot_checksum_and_invalid_selected_price_fail():
    raw, checksum = archive('2024-02')
    with pytest.raises(ValueError):
        adapter().spot_month('2024-02', raw+b'corrupt', checksum)
    with pytest.raises(ValueError):
        adapter().spot_month('2024-02', *archive('2024-02', invalid_day=2))


def test_graph_assumed_clock_does_not_relabel_provenance_or_input():
    original = graph()
    before = copy.deepcopy(original)
    frame, exclusions = adapter().graph_rows(original)
    assert original == before and exclusions == []
    assert frame.iloc[0]['available_at'] == pd.Timestamp('2022-01-04T00:00:00Z')
    assert frame.attrs['historical_availability_verified'] is False
    assert frame.attrs['availability_basis'] == 'protocol_assumption'
    assert frame.iloc[0]['dyads'] == 2 and frame.iloc[0]['triangles'] == 3


@pytest.mark.parametrize('mutation', ['role', 'denominator', 'duplicate', 'boolean', 'admission'])
def test_graph_inconsistent_counts_or_identity_fail(mutation):
    value = graph()
    row = value['days'][0]
    if mutation == 'role':
        row['local40']['local40_sums'][24] = 3
    elif mutation == 'denominator':
        row['nonzero_nodes'] = 5
    elif mutation == 'duplicate':
        value['days'].append(copy.deepcopy(row))
    elif mutation == 'boolean':
        row['events'] = True
    else:
        value['global_uniqueness_admitted'] = False
    with pytest.raises(ValueError):
        adapter().graph_rows(value)


def test_graph_boundary_exclusion_and_later_clock_preserved():
    value = graph()
    value['days'][0]['available_at'] = '2022-01-05T12:00:00Z'
    value['days'].insert(0, dict(day='2022-01-01', source_admitted=True,
                               graph_admitted=False, reason='missing preceding boundary'))
    frame, excluded = adapter().graph_rows(value)
    assert frame.iloc[0]['available_at'] == pd.Timestamp('2022-01-05T12:00:00Z')
    assert excluded == [dict(day='2022-01-01', reason='missing preceding boundary')]


def test_full_market_cohort_requires_every_month():
    with pytest.raises(ValueError):
        adapter().market_rows({'2024-02': archive('2024-02')})
    inputs = {m: archive(m) for m in adapter().MONTHS}
    result = adapter().market_rows(inputs)
    assert len(result) == 1128
    assert result.day.min() == pd.Timestamp('2021-12-01T00:00:00Z')
    assert result.day.max() == pd.Timestamp('2025-01-01T00:00:00Z')


def test_failure_only_review_cannot_admit_graph():
    with pytest.raises(ValueError):
        adapter().require_graph_review(b'{}', b'{}', {'passed': True, 'passing_full_panel': False}, {}, source='a'*40)


@pytest.mark.parametrize('late', [False, True])
def test_missing_first_graph_day_and_late_clock_propagate_to_features(late):
    m = adapter()
    value = graph()
    row = value['days'][0]
    value['days'] = [dict(day='2022-01-01', source_admitted=True, graph_admitted=False,
                          reason='missing preceding boundary')]
    for day in pd.date_range('2022-01-02', '2022-01-12'):
        value['days'].append(dict(copy.deepcopy(row), day=day.strftime('%Y-%m-%d')))
    if late:
        value['days'][3]['available_at'] = '2022-01-15T12:00:00Z'
    frame, _ = m.graph_rows(value)
    market = pd.concat([m.spot_month(month, *archive(month)) for month in ('2021-12', '2022-01')])
    spec = importlib.util.spec_from_file_location('matched_input_features', PATH.with_name('features.py'))
    features = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(features)
    panel, _ = features.build_panel(market, frame, start='2022-01-09', end='2022-01-12')
    assert pd.isna(panel.loc[0, 'events_relative_7'])
    assert panel.loc[1:, features.FEATURE_SETS['M2']].notna().all().all()
    assert panel.loc[1, 'events_relative_7'] == 0
    clock = panel.loc[1, 'events_relative_7__available_at']
    assert (clock > panel.loc[1, 'decision_at']) == late


def test_review_requires_matching_terminal_panel_and_clean_guard():
    m = adapter()
    raw = json.dumps(graph()).encode()
    digest = hashlib.sha256(raw).hexdigest()
    terminal = dict(status='complete', source='a'*40, experiment_id=m.GRAPH_EXPERIMENT,
                    output_sha256={'panel.json': digest})
    terminal_raw = json.dumps(terminal).encode()
    review = dict(passed=True, passing_full_panel=True, source='a'*40,
                  terminal_sha256=hashlib.sha256(terminal_raw).hexdigest(),
                  output_sha256={'panel.json': digest})
    guard = dict(phase='complete', child_exit_code=0, limit_reason=None, cleanup_verified=True,
                 command=['python', '-B', '/fixed/check_final.py', '--root', '/fixed',
                          '--source', 'a'*40, '--report', '/fixed/independent-report.json'],
                 memory_events={'oom': 0, 'oom_kill': 0, 'oom_group_kill': 0})
    m.require_graph_review(raw, terminal_raw, review, guard, source='a'*40)
    for broken in [dict(guard, child_exit_code=1), dict(guard, memory_events={}), dict(guard, command=['other'])]:
        with pytest.raises(ValueError):
            m.require_graph_review(raw, terminal_raw, review, broken, source='a'*40)
    with pytest.raises(ValueError):
        m.require_graph_review(raw+b' ', terminal_raw, review, guard, source='a'*40)
    with pytest.raises(ValueError):
        m.require_graph_review(raw, terminal_raw+b' ', review, guard, source='a'*40)
    with pytest.raises(ValueError):
        m.require_graph_review(raw, terminal_raw, review, guard, source='b'*40)

"""Synthetic daily panel phases; no real capture bodies or outcomes are read."""
import argparse
import io
import json
from pathlib import Path

import pytest

import importlib.util
ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('fullpanel_day_test', ROOT/'research/onchain-graph-2026-09-16/fullpanel/day.py')
day = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(day)
fixture = day.load('fullpanel_day_fixture', ROOT/'tests/research/test_onchain_graph_prototype.py')


def reference(root, path, value):
    raw = json.dumps(value).encode()
    (root/path).write_bytes(raw)
    return dict(path=path, sha256=day.storage.sha(raw))


def setup(tmp_path, monkeypatch, edge=False):
    projection, raw, footer, blocks = fixture.parquet_fixture()
    sink = io.BytesIO()
    fixture.pq.write_table(fixture.pa.table(dict(number=[101], hash=['0x'+'9'*64], parent_hash=[fixture.H],
        timestamp=fixture.pa.array([fixture.END], type=fixture.pa.timestamp('ns')), transaction_count=[1])), sink)
    calls = []
    def material(root, plan, date, boundary=False):
        calls.append((date, boundary))
        if boundary:
            assert date == '2024-01-02'
            return None, None, sink.getvalue(), None
        assert date == '2024-01-01'
        return projection, footer, blocks, lambda i: raw[projection['ranges'][i]['start']:projection['ranges'][i]['end']+1]
    monkeypatch.setattr(day, 'material', material)
    dates = ['2024-01-01'] if edge else ['2023-12-31', '2024-01-01', '2024-01-02']
    plan = dict(dates=dates, expected_rows={'2024-01-01': 7}, reuse={})
    prefix_dir = tmp_path/'previous-prefix'
    prefix_dir.mkdir()
    prefix = [[fixture.START//10**9-1, 1, fixture.A, fixture.B], [fixture.START//10**9-1, 2, fixture.B, fixture.A]]
    previous_source = dict(date='2023-12-31', status='complete', integrity={'last_block': [99, fixture.P, '0x'+'0'*64, fixture.START-10**9, 2]},
                           prefix=day.old.shards(tmp_path, prefix_dir, 'prefix', prefix))
    report = dict(date='2023-12-31', passed=True)
    report_ref = reference(tmp_path, 'previous-audit.json', report)
    previous = dict(date='2023-12-31', source=previous_source, independent=report, audit=report_ref)
    previous_ref = reference(tmp_path, 'previous.json', previous)
    reference(tmp_path, 'plan.json', plan)
    args = argparse.Namespace(root=str(tmp_path), plan='plan.json', date='2024-01-01',
        phase='research/onchain-graph-2026-09-16/fullpanel/artifacts/scratch/2024-01-01/phase.json',
        previous=None if edge else previous_ref['path'], previous_sha256=None if edge else previous_ref['sha256'])
    return args, plan, calls, previous, material


def test_fresh_source_count_and_boundaries(tmp_path, monkeypatch):
    args, _, calls, _, _ = setup(tmp_path, monkeypatch)
    result = day.execute(args)
    assert result['source']['status'] == result['count']['status'] == 'complete', result
    assert result['source']['expected_rows'] == 7
    assert result['count']['features']['cross_midnight_unique_occurrences'] > 0
    assert result['previous']['audit']['path'] == 'previous-audit.json'
    assert calls == [('2024-01-01', False), ('2024-01-02', True)]
    assert not result['source_reused'] and not result['count_reused']
    assert sum(m['hashes'] for m in result['source']['transaction_hashes']) == 7
    with pytest.raises(FileExistsError):
        day.execute(args)


def test_registered_edge_source_retained_count_unavailable(tmp_path, monkeypatch):
    args, _, calls, _, _ = setup(tmp_path, monkeypatch, edge=True)
    result = day.execute(args)
    assert result['source']['status'] == 'complete'
    assert result['count']['status'] == 'unavailable'
    assert 'panel edge' in result['count']['reason']
    assert result['previous'] is result['following'] is None
    assert calls == [('2024-01-01', False)]


@pytest.mark.parametrize('bad', ['hash', 'date', 'report', 'prefix', 'expected_rows'])
def test_bad_previous_or_population_retained_unavailable(tmp_path, monkeypatch, bad):
    args, plan, _, previous, _ = setup(tmp_path, monkeypatch)
    if bad == 'hash':
        args.previous_sha256 = '0'*64
    elif bad == 'expected_rows':
        plan['expected_rows'][args.date] = 8
        reference(tmp_path, 'plan.json', plan)
    elif bad == 'prefix':
        path = tmp_path/previous['source']['prefix'][0]['path']
        path.write_bytes(path.read_bytes()+b'corrupt')
    else:
        if bad == 'date':
            previous['date'] = '2023-12-30'
        else:
            previous['independent']['passed'] = False
        args.previous_sha256 = reference(tmp_path, 'previous.json', previous)['sha256']
    result = day.execute(args)
    assert result['count']['status'] == 'unavailable' and result['error_type'] == 'ValueError'
    assert result['source']['status'] == ('unavailable' if bad == 'expected_rows' else 'complete')


def test_reuses_sealed_sources_and_counts_without_decode(tmp_path, monkeypatch):
    args, plan, calls, previous, material = setup(tmp_path, monkeypatch)
    own = tmp_path/'original'
    own.mkdir()
    hashes = []
    projection, footer, blocks, reader = material(tmp_path, plan, args.date)
    events, integrity, activity = day.numeric.decode(projection, footer, blocks, reader, fixture.START//10**9,
                                                   fixture.END//10**9, hash_sink=hashes.extend)
    events = [list(event) for event in events]
    source = dict(date=args.date, mode='source', status='complete', integrity=integrity, activity=activity,
                  events=day.old.shards(tmp_path, own, 'events', events), prefix=[],
                  transaction_hashes=[day._hash_blob(tmp_path, own, b''.join(hashes), 0)])
    source_ref = reference(tmp_path, 'original-source.json', source)
    previous_ref = reference(tmp_path, 'original-previous.json', previous['source'])
    local, features, checks, timings = day.numeric.count_day(day.read_rows(tmp_path, previous['source']['prefix']),
                                                           events, fixture.START//10**9, fixture.END//10**9)
    retained_count = dict(date=args.date, mode='count', status='complete', source_result_sha256=source_ref['sha256'],
        previous_result_sha256=previous_ref['sha256'], counts=day.old.shards(tmp_path, own, 'local40', sorted(local.items())),
        features=features, checks=checks, timings=timings)
    plan['reuse'] = {args.date: dict(source=source_ref, count=reference(tmp_path, 'original-count.json', retained_count)),
                     '2023-12-31': dict(source=previous_ref)}
    reference(tmp_path, 'plan.json', plan)
    def forbidden(*a, **kw):
        raise AssertionError('reuse must not decode or recount')
    monkeypatch.setattr(day.numeric, 'decode', forbidden)
    monkeypatch.setattr(day.numeric, 'count_day', forbidden)
    calls.clear()
    result = day.execute(args)
    assert result['source']['status'] == result['count']['status'] == 'complete', result
    assert result['source_reused'] and result['count_reused']
    assert result['count']['features'] == features
    assert calls == [('2024-01-02', True)]
    for item in result['source']['events']+result['source']['transaction_hashes']+result['count']['counts']:
        assert item['path'].startswith('research/onchain-graph-2026-09-16/fullpanel/artifacts/scratch/')


def test_network_guard_and_path_confinement(tmp_path):
    with pytest.raises(RuntimeError, match='network'):
        day.deny_network('socket.connect', ())
    with pytest.raises(ValueError):
        day.within(tmp_path, '../escape')

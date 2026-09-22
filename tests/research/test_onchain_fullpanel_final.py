"""Invented full32 identities and compact lifecycle fixtures only."""
from collections import Counter
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('fullpanel_final_test', ROOT / 'research/onchain-graph-2026-09-16/fullpanel/check_final.py')
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def identity(bucket, number):
    return bytes([bucket]) + number.to_bytes(31, 'big')


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(c.json_bytes(value))


def population(tmp_path, days):
    """Independent Python/Counter writer deliberately reverses each day segment."""
    hashes, copies = tmp_path / 'hashes', tmp_path / 'copies'
    hashes.mkdir(); copies.mkdir()
    buckets = [b''] * 256
    expected, digests = {}, {}
    for i, values in enumerate(days):
        expected[i] = len(values)
        digests[i] = c.sha(b''.join(sorted(values)))
        segments = []
        for b in range(256):
            raw = b''.join(reversed([v for v in values if v[0] == b]))
            segments.append(dict(bucket=f'{b:02x}', offset=len(buckets[b]), rows=len(raw)//32,
                                 bytes=len(raw), sha256=c.sha(raw)))
            buckets[b] += raw
        receipt = dict(schema_version=1, status='complete', day_index=i, rows=len(values),
                       bytes=len(values)*32, stream_sha256=digests[i],
                       total_bucket_bytes=sum(map(len, buckets)), buckets=segments)
        intent = dict(schema_version=1, day_index=i, status='intent', max_total_bytes=c.MAX_HASH_BYTES)
        for suffix, value in [('.json', receipt), ('.intent.json', intent)]:
            publish(hashes / f'day-{i:04d}{suffix}', value)
            publish(copies / f'day-{i:04d}{suffix}', value)
    summaries = []
    for b, raw in enumerate(buckets):
        if raw:
            (hashes / f'{b:02x}.bin').write_bytes(raw)
        values = [raw[i:i+32] for i in range(0, len(raw), 32)]
        counts = Counter(values)
        summaries.append(dict(bucket=f'{b:02x}', bytes=len(raw), rows=len(values), unique=len(counts),
                              duplicate_excess=len(values)-len(counts), sha256=c.sha(raw)))
    rows, unique = sum(expected.values()), sum(s['unique'] for s in summaries)
    production = dict(status='complete', buckets=summaries, rows=rows, unique=unique,
                      duplicate_excess=rows-unique, input_bytes=rows*32, days=len(days),
                      expected_day_rows={str(i):n for i,n in expected.items()}, admitted=rows==unique,
                      scratch_preserved=True)
    return hashes, copies, expected, digests, production


def test_independent_bucket_sort_conservation_and_duplicates(tmp_path):
    values = [identity(i % 256, i % 77) for i in range(1000)]
    days = [values, [values[0], values[21], identity(255, 9999)]]
    args = population(tmp_path, days)
    before = {str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    result = c.verify_buckets(*args)
    oracle = Counter(v for day in days for v in day)
    assert result['unique'] == len(oracle)
    assert result['duplicate_excess'] == sum(oracle.values()) - len(oracle)
    assert result['independent_sorted_day_streams_checked'] == 2
    assert before == {str(p):p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def test_comparison_block_boundary(tmp_path):
    args = population(tmp_path, [[identity(2, 9)] * 40000])
    result = c.verify_buckets(*args)
    assert result['duplicate_excess'] == 39999


def test_empty_population_and_empty_segments(tmp_path):
    result = c.verify_buckets(*population(tmp_path, [[], []]))
    assert result['rows'] == result['unique'] == 0


@pytest.mark.parametrize('kind', ['truncated', 'extra', 'symlink', 'copied_receipt', 'offset',
                                  'segment_sha', 'production_unique', 'production_sha', 'day_digest'])
def test_evidence_mutation_rejected(tmp_path, kind):
    args = population(tmp_path, [[identity(0, 1), identity(0, 2)], [identity(1, 3)]])
    hashes, copies, expected, digests, production = args
    if kind == 'truncated':
        (hashes/'00.bin').write_bytes(b'bad')
    elif kind == 'extra':
        (hashes/'extra').write_bytes(b'')
    elif kind == 'symlink':
        (hashes/'00.bin').rename(hashes/'original')
        (hashes/'00.bin').symlink_to(hashes/'original')
    elif kind == 'copied_receipt':
        (copies/'day-0000.json').write_bytes(b'{}')
    elif kind in ('offset', 'segment_sha'):
        receipt = c.load(hashes/'day-0000.json')
        receipt['buckets'][0]['offset' if kind == 'offset' else 'sha256'] = 32 if kind == 'offset' else '0'*64
        for directory in (hashes, copies):
            publish(directory/'day-0000.json', receipt)
    elif kind == 'production_unique':
        production['unique'] -= 1
    elif kind == 'production_sha':
        production['buckets'][0]['sha256'] = '0'*64
    else:
        digests[0] = '0'*64
    with pytest.raises(AssertionError):
        c.verify_buckets(*args)


def test_forged_writer_population_cannot_replace_independent_day_digest(tmp_path):
    args = population(tmp_path, [[identity(0, 1), identity(0, 2)]])
    hashes, copies, expected, digests, production = args
    # Rebind all writer-controlled raw/segment/global hashes, leave the independent
    # source digest unchanged: ordinary receipt matching alone would pass.
    forged = identity(0, 3) + identity(0, 2)
    (hashes/'00.bin').write_bytes(forged)
    receipt = c.load(hashes/'day-0000.json')
    receipt['buckets'][0]['sha256'] = c.sha(forged)
    for directory in (hashes, copies):
        publish(directory/'day-0000.json', receipt)
    production['buckets'][0]['sha256'] = c.sha(forged)
    with pytest.raises(AssertionError):
        c.verify_buckets(*args)


def test_bucket_limit_checked_before_allocation(tmp_path, monkeypatch):
    args = population(tmp_path, [[identity(0, 1)]])
    monkeypatch.setattr(c, 'MAX_BUCKET', 31)
    monkeypatch.setattr(c.np, 'fromfile', lambda *a, **k: pytest.fail('allocated oversized bucket'))
    with pytest.raises(AssertionError):
        c.verify_buckets(*args)


def compact_fixture(tmp_path):
    day = '2022-01-01'
    value = dict(date=day, source=dict(status='complete', reason=None,
                 activity=dict(events=2,nodes=3,directed_pairs=2),integrity=dict(rows=4)),
                 count=dict(status='unavailable', reason='edge'), independent=dict(passed=True,count_verified=False))
    cells = [dict(id='source-'+day,status='complete'),dict(id='graph-'+day,status='unavailable',reason='edge'),
             dict(id='global-uniqueness',status='complete')]
    plan = dict(dates=[day], expected_graph_unavailable={day:'edge'}, hash_root='/declared/scratch')
    terminal = dict(cells=cells)
    publish(tmp_path/'outputs/panel.json', dict(days=[c.expected_panel_row(day,value,True)],global_uniqueness_admitted=True,
                                             historical_availability_verified=False,prices_or_models_opened=False))
    publish(tmp_path/'outputs/summary.json',dict(cells=cells,dates=1,source_days=1,graph_days=0,
                unavailable_graph_days=[day],expected_boundary_only=True,requests=0,raw_capture_modified=False,
                hash_scratch_retained=plan['hash_root'],stopped=None))
    return plan, terminal, [value]


def test_panel_unavailable_source_still_denominator(tmp_path):
    plan, terminal, values = compact_fixture(tmp_path)
    summary = c.verify_panel_outputs(tmp_path, plan, terminal, values, True)
    assert summary['source_days'] == 1 and summary['graph_days'] == 0


@pytest.mark.parametrize('kind', ['leakage', 'graph_flag', 'source_rows', 'cell_missing', 'summary_count'])
def test_compact_panel_mutations_fail(tmp_path, kind):
    plan, terminal, values = compact_fixture(tmp_path)
    panel = c.load(tmp_path/'outputs/panel.json')
    if kind == 'leakage':
        panel['days'][0]['available_at'] = '2022-01-02'
    elif kind == 'graph_flag':
        panel['days'][0]['graph_admitted'] = True
    elif kind == 'source_rows':
        panel['days'][0]['transactions'] -= 1
    elif kind == 'cell_missing':
        terminal['cells'].pop(0)
    else:
        summary = c.load(tmp_path/'outputs/summary.json'); summary['graph_days'] = 1
        publish(tmp_path/'outputs/summary.json', summary)
    publish(tmp_path/'outputs/panel.json',panel)
    with pytest.raises(AssertionError):
        c.verify_panel_outputs(tmp_path, plan, terminal, values, True)


def test_stopped_complete_lifecycle_is_preservation_only(tmp_path):
    plan, terminal, values = compact_fixture(tmp_path/'run')
    day = plan['dates'][0]
    values[0]['source'] = dict(status='unavailable',reason='stopped')
    values[0]['count']['reason'] = 'stopped'
    terminal['cells'] = [dict(id='source-'+day,status='unavailable',reason='stopped'),
                        dict(id='graph-'+day,status='unavailable',reason='stopped'),
                        dict(id='global-uniqueness',status='unavailable',reason='stopped')]
    run = tmp_path/'run'
    publish(run/'outputs'/('day-'+day+'.json'),values[0])
    publish(run/'outputs/hash-audit.json',dict(status='unavailable',admitted=False))
    publish(run/'outputs/panel.json',dict(days=[c.expected_panel_row(day,values[0],False)],
                  global_uniqueness_admitted=False,historical_availability_verified=False,prices_or_models_opened=False))
    summary = c.load(run/'outputs/summary.json')
    summary.update(cells=terminal['cells'],source_days=0,expected_boundary_only=False,stopped='stopped')
    publish(run/'outputs/summary.json',summary)
    result = c.verify_complete(tmp_path,run,plan,terminal)
    assert result['failed_run_evidence_only'] and not result['passing_full_panel']
    assert not result['numerical_panel_validation_performed']


def daily_fixture(tmp_path):
    import argparse
    import shutil
    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, ROOT/path)
        value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
        return value
    f = module('final_review_synthetic_rows', 'tests/research/test_onchain_fullpanel_check_day.py')
    producer = module('final_review_synthetic_producer', 'research/onchain-graph-2026-09-16/fullpanel/day.py')
    original_capture = f.capture
    def capture(*args, **kwargs):
        args = list(args)
        if args[2] == '2024-01-03':
            args[6] += 86300  # retain a nonempty final-hour prefix
        return original_capture(*args, **kwargs)
    f.capture = capture
    plan, original = f.fixture(tmp_path)
    day, base = original['date'], Path(c.BASE)
    scratch = tmp_path/base/'artifacts/scratch'/day
    shutil.rmtree(scratch)
    plan['reuse'] = {}
    publish(tmp_path/base/'plan.json',plan)
    prior = original['previous']
    prior_audit = c.load(tmp_path/prior['audit']['path'])
    previous = dict(date=prior['date'],source=dict(prior,status='complete'),audit=prior['audit'],independent=prior_audit)
    run = tmp_path/'research_runs'/c.EXPERIMENT
    prior_path = run/'outputs'/('day-'+prior['date']+'.json')
    publish(prior_path,previous)
    phase_rel = base/'artifacts/scratch'/day/'phase.json'
    args = argparse.Namespace(root=str(tmp_path),plan=str(base/'plan.json'),date=day,phase=str(phase_rel),
                 previous=str(prior_path.relative_to(tmp_path)),previous_sha256=c.file_sha(prior_path))
    producer.execute(args)
    phase = c.load(tmp_path/phase_rel)
    assert phase['source']['status'] == phase['count']['status'] == 'complete'
    audit = f.c.check(tmp_path,plan,phase)
    audit.update(phase_sha256=c.file_sha(tmp_path/phase_rel),plan_sha256=c.file_sha(tmp_path/base/'plan.json'),
                 reviewer_script_sha256=c.file_sha(c.HERE/'check_day.py'))
    audit_path = tmp_path/base/'artifacts/checks'/(day+'.json')
    publish(audit_path,audit)
    manifest = c.inventory(scratch,tmp_path)
    value = dict(phase,independent=audit,audit=dict(path=str(audit_path.relative_to(tmp_path)),sha256=c.file_sha(audit_path)),
                 hash_append={},scratch_manifest=manifest,scratch_retention='declared recomputable')
    output = run/'outputs'/('day-'+day+'.json');publish(output,value)
    shutil.rmtree(scratch)
    publish(tmp_path/base/'artifacts/cleanup'/(day+'.json'),dict(date=day,released=True,daily_output_sha256=c.file_sha(output),
                    files=len(manifest),bytes=sum(r['bytes'] for r in manifest)))
    return run,plan,day,value,previous


def test_retained_daily_source_audit_phase_and_cleanup_roundtrip(tmp_path):
    args = daily_fixture(tmp_path)
    retained = set()
    audit = c.verify_daily(tmp_path,*args,retained)
    assert audit['passed'] and audit['count_verified']
    assert any('/prefixes/' in str(p) for p in retained)


@pytest.mark.parametrize('kind', ['phase_numeric', 'reviewer_binding', 'previous_output', 'prefix', 'cleanup', 'extra_array'])
def test_daily_evidence_mutations_fail(tmp_path,kind):
    run,plan,day,value,previous = daily_fixture(tmp_path)
    base = tmp_path/c.BASE
    if kind == 'phase_numeric':
        value['source']['activity']['events'] += 1
    elif kind == 'reviewer_binding':
        audit_path = tmp_path/value['audit']['path']
        value['independent']['reviewer_script_sha256'] = '0'*64
        publish(audit_path,value['independent'])
        value['audit']['sha256'] = c.file_sha(audit_path)
    elif kind == 'previous_output':
        path = run/'outputs'/('day-'+previous['date']+'.json')
        path.write_bytes(path.read_bytes()+b' ')
    elif kind == 'prefix':
        path = tmp_path/value['source']['prefix'][0]['path']
        path.write_bytes(b'corrupt')
    elif kind == 'cleanup':
        path = base/'artifacts/cleanup'/(day+'.json')
        record = c.load(path);record['bytes'] += 1;publish(path,record)
    else:
        (base/'artifacts/scratch'/day).mkdir()
    with pytest.raises(AssertionError):
        c.verify_daily(tmp_path,run,plan,day,value,previous,set())

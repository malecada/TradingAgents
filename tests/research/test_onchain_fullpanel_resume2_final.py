"""Independent invented union namespaces; no empirical data or producer imports."""
from collections import Counter
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('resume2_final_synthetic', ROOT / 'research/onchain-graph-2026-09-16/fullpanel_resume2/check_final.py')
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def identity(bucket, number):
    return bytes([bucket]) + number.to_bytes(31, 'big')


def publish(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(c.json_bytes(value))


def population(tmp_path, days, seed_count=1):
    roots = [tmp_path / 'old', tmp_path / 'new']
    copies = tmp_path / 'copies'
    for path in [*roots, copies]:
        path.mkdir()
    expected = {i: len(v) for i, v in enumerate(days)}
    digests = {i: c.sha(b''.join(sorted(v))) for i, v in enumerate(days)}
    all_buckets = []
    for root_index, root in enumerate(roots):
        buckets = [b''] * 256
        indices = range(seed_count) if root_index == 0 else range(seed_count, len(days))
        for day in indices:
            segments = []
            for bucket in range(256):
                raw = b''.join(reversed([v for v in days[day] if v[0] == bucket]))
                segments.append(dict(bucket=f'{bucket:02x}', offset=len(buckets[bucket]),
                                     rows=len(raw)//32, bytes=len(raw), sha256=c.sha(raw)))
                buckets[bucket] += raw
            receipt = dict(schema_version=1, status='complete', day_index=day,
                           rows=expected[day], bytes=32*expected[day], stream_sha256=digests[day],
                           total_bucket_bytes=sum(map(len, buckets)), buckets=segments)
            cap = c.MAX_HASH_BYTES - (32*sum(expected[i] for i in range(seed_count)) if root_index else 0)
            intent = dict(schema_version=1, day_index=day, status='intent', max_total_bytes=cap)
            for suffix, value in [('.json', receipt), ('.intent.json', intent)]:
                for directory in (root, copies):
                    publish(directory / f'day-{day:04d}{suffix}', value)
        for bucket, raw in enumerate(buckets):
            if raw:
                (root / f'{bucket:02x}.bin').write_bytes(raw)
        all_buckets.append(buckets)
    summaries = []
    for bucket in range(256):
        raw = b''.join(local[bucket] for local in all_buckets)
        values = [raw[i:i+32] for i in range(0, len(raw), 32)]
        unique = len(Counter(values))
        summaries.append(dict(bucket=f'{bucket:02x}', bytes=len(raw), rows=len(values), unique=unique,
                              duplicate_excess=len(values)-unique, sha256=c.sha(raw)))
    rows = sum(expected.values())
    excess = sum(s['duplicate_excess'] for s in summaries)
    production = dict(status='complete', admitted=excess == 0, rows=rows, unique=rows-excess,
                      duplicate_excess=excess, buckets=summaries, input_bytes=rows*32,
                      days=len(days), expected_day_rows={str(i):n for i,n in expected.items()},
                      expected_day_stream_sha256={str(i):d for i,d in digests.items()},
                      roots=[str(p) for p in roots], scratch_preserved=True)
    return roots, copies, expected, digests, production


def verify(args, seed_count=1):
    return c.verify_buckets(*args, seed_count=seed_count)


def saved(directory):
    return {str(p):p.read_bytes() for p in directory.rglob('*') if p.is_file()}


def test_cross_root_duplicates_and_all_buckets_counter(tmp_path):
    values = [identity(i % 256, i % 333) for i in range(3000)]
    days = [values, [values[1], values[2999], identity(255, 9000)], [identity(0, 999)]]
    args = population(tmp_path, days)
    before = saved(tmp_path)
    result = verify(args)
    oracle = Counter(v for d in days for v in d)
    assert result['unique'] == len(oracle)
    assert result['duplicate_excess'] == sum(oracle.values()) - len(oracle)
    assert result['independent_sorted_day_streams_checked'] == 3
    assert before == saved(tmp_path)


def test_empty_days_and_block_boundary(tmp_path):
    values = [identity(4, 1)] * 34000
    result = verify(population(tmp_path, [values[:17000], [], values[17000:]], seed_count=2), seed_count=2)
    assert result['rows'] == 34000 and result['duplicate_excess'] == 33999


def test_empty_union(tmp_path):
    result = verify(population(tmp_path, [[], []]))
    assert result['rows'] == result['unique'] == 0


@pytest.mark.parametrize('kind', ['extra', 'truncated', 'copy', 'offset', 'empty_offset', 'wrong_root_day',
                                  'segment_digest', 'stream_digest', 'production_count', 'production_roots',
                                  'missing_day', 'same_root', 'symlink', 'intent_cap', 'root_symlink'])
def test_tampered_union_fails(tmp_path, kind):
    args = population(tmp_path, [[identity(0, 1)], [identity(0, 2)]])
    roots, copies, expected, digests, production = args
    if kind == 'extra':
        (roots[1] / 'append.lock').mkdir()
    elif kind == 'truncated':
        (roots[1] / '00.bin').write_bytes(b'bad')
    elif kind == 'copy':
        (copies / 'day-0001.json').write_bytes(b'{}')
    elif kind in ('offset', 'empty_offset', 'segment_digest'):
        value = c.load(roots[1] / 'day-0001.json')
        bucket = 3 if kind == 'empty_offset' else 0
        value['buckets'][bucket]['sha256' if kind == 'segment_digest' else 'offset'] = '0'*64 if kind == 'segment_digest' else 32
        for root in (roots[1], copies):
            publish(root / 'day-0001.json', value)
    elif kind == 'wrong_root_day':
        for suffix in ('.json', '.intent.json'):
            (roots[1] / ('day-0001'+suffix)).rename(roots[0] / ('day-0001'+suffix))
    elif kind == 'stream_digest':
        digests[1] = '0'*64
    elif kind == 'production_count':
        production['unique'] -= 1
    elif kind == 'production_roots':
        production['roots'].reverse()
    elif kind == 'missing_day':
        expected.pop(1)
    elif kind == 'same_root':
        roots[1] = roots[0]
    elif kind == 'symlink':
        target = roots[1] / '00.bin'; target.rename(tmp_path/'saved.bin'); target.symlink_to(tmp_path/'saved.bin')
    elif kind == 'intent_cap':
        value = c.load(roots[1]/'day-0001.intent.json'); value['max_total_bytes'] -= 1
        for root in (roots[1], copies):
            publish(root/'day-0001.intent.json', value)
    else:
        link = tmp_path / 'link'; link.symlink_to(roots[1], target_is_directory=True); roots[1] = link
    with pytest.raises((AssertionError, FileNotFoundError)):
        verify(args)


def test_forged_writer_hashes_still_fail_independent_day_digest(tmp_path):
    args = population(tmp_path, [[identity(0, 1)], [identity(0, 2)]])
    roots, copies, _, _, production = args
    forged = identity(0, 3)
    (roots[1]/'00.bin').write_bytes(forged)
    receipt = c.load(roots[1]/'day-0001.json'); receipt['buckets'][0]['sha256'] = c.sha(forged)
    for root in (roots[1], copies):
        publish(root/'day-0001.json', receipt)
    production['buckets'][0]['sha256'] = c.sha(identity(0,1)+forged)
    with pytest.raises(AssertionError):
        verify(args)


def test_combined_cap_checked_before_allocation(tmp_path, monkeypatch):
    args = population(tmp_path, [[identity(0, 1)], [identity(0, 2)]])
    monkeypatch.setattr(c, 'MAX_BUCKET', 63)
    monkeypatch.setattr(c.np, 'empty', lambda *a, **k: pytest.fail('allocated oversized combined bucket'))
    with pytest.raises(AssertionError):
        verify(args)


def resource_fixture(root):
    return dict(cwd=str(root), command=[c.PINNED_PYTHON,'-B',str(root/c.BASE/'run.py'),'--source','a'*40],
                memory_max_bytes=6*2**30, memory_high_bytes=6*2**30, memory_swap_max_bytes=2**29,
                reserve_bytes=3*2**30, start_reserve_bytes=9*2**30, elapsed_time_kill=False,
                retry=False, cpus=[0,1], phase='complete', limit_reason=None, child_exit_code=0,
                cleanup_verified=True, kernel_controls={'memory.max':str(6*2**30),
                'memory.high':str(6*2**30),'memory.swap.max':str(2**29)},
                peak_sampled_memory_current_bytes=2**30, unit_properties={'Result':'success'},
                cleanup_unit_properties={'ActiveState':'inactive'}, memory_events={'oom':0,'oom_kill':0},
                initial_memory_events={'oom':0,'oom_kill':0}, memory_current_bytes=2**20,
                terminal_memory_snapshot={'memory_events':{'oom':0,'oom_kill':0}, 'memory_current_bytes':2**20})


def test_guard_clean_and_missing_or_empty_unknown(tmp_path):
    path = tmp_path/c.BASE/'resources/compute/final.json'
    assert c.compute_resource(tmp_path, 'a'*40)['clean'] is False
    path.parent.mkdir(parents=True);path.touch()
    assert c.compute_resource(tmp_path, 'a'*40)['clean'] is False
    publish(path,resource_fixture(tmp_path))
    assert c.compute_resource(tmp_path, 'a'*40)['clean'] is True


@pytest.mark.parametrize('kind', ['failed','oom','unknown_oom','child_exit','unknown_initial','unknown_terminal','terminal_oom'])
def test_guard_failure_never_numeric_success(tmp_path, kind):
    value = resource_fixture(tmp_path)
    if kind == 'failed':
        value['phase']='failed';value['limit_reason']='host reserve breached'
    elif kind == 'oom':
        value['memory_events']['oom_kill']=1
    elif kind == 'unknown_oom':
        value.pop('memory_events')
    elif kind == 'child_exit':
        value['child_exit_code']=137
    elif kind == 'unknown_initial':
        value.pop('initial_memory_events')
    elif kind == 'unknown_terminal':
        value.pop('terminal_memory_snapshot')
    else:
        value['terminal_memory_snapshot']['memory_events']['oom_kill']=1
    publish(tmp_path/c.BASE/'resources/compute/final.json', value)
    assert c.compute_resource(tmp_path, 'a'*40)['clean'] is False


@pytest.mark.parametrize('kind', ['command','limit','controls','cleanup','cpu','peak'])
def test_guard_evidence_forgery_rejected(tmp_path, kind):
    value = resource_fixture(tmp_path)
    if kind == 'command':value['command'].insert(1,'-c')
    elif kind == 'limit':value['memory_max_bytes']=8*2**30
    elif kind == 'controls':value['kernel_controls']['memory.max']='max'
    elif kind == 'cleanup':value['cleanup_verified']=False
    elif kind == 'cpu':value['cpus']=[0,1,2]
    else:value['peak_sampled_memory_current_bytes']=7*2**30
    publish(tmp_path/c.BASE/'resources/compute/final.json', value)
    with pytest.raises(AssertionError):c.compute_resource(tmp_path,'a'*40)


@pytest.mark.parametrize('kind', ['exact','seed_changed','new_output_changed','partial_extra','missing_member'])
def test_seed_exact_path_and_bytes(tmp_path, kind):
    archive=tmp_path/'archive';run=tmp_path/'run';day='2022-07-25'
    output=f'research_runs/{c.PREDECESSOR}/outputs/day-{day}.json'
    member=c.ORIGINAL_BASE+'/artifacts/checks/'+day+'.json'
    refs={}
    for rel in (output,member):
        source=archive/rel;publish(source,{'preserved':'bytes'})
        target=run/'outputs'/Path(rel).name if rel==output else tmp_path/rel
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        refs[rel]={'bytes':source.stat().st_size,'sha256':c.file_sha(source)}
    resume={'archive_root':'archive','seed_dates':[day],'seed_files':refs}
    original=SimpleNamespace(inside=lambda root,relative:root/relative)
    if kind=='seed_changed':(archive/output).write_bytes(b'changed')
    elif kind=='new_output_changed':(run/'outputs'/Path(output).name).write_bytes(b'changed')
    elif kind=='partial_extra':refs[c.ORIGINAL_BASE+'/artifacts/prefixes/2022-07-26/prefix-0000.jsonl.zst']={'bytes':0,'sha256':c.sha(b'')}
    elif kind=='missing_member':refs.pop(member)
    if kind=='exact':
        c.verify_seed(tmp_path,run,resume,original,{tmp_path/member})
    else:
        with pytest.raises(AssertionError):c.verify_seed(tmp_path,run,resume,original,{tmp_path/member})

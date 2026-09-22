"""Independent continuation closure; no production union imports or raw recount.

Compact days use the byte-bound original verifier and phase correction. Union
identity verification independently reconstructs every sorted daily stream and
counts cross-root duplicates in one bounded combined-bucket allocation.
"""
from datetime import date, datetime, timedelta, timezone
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = 'research/onchain-graph-2026-09-16/fullpanel_resume'
ORIGINAL_BASE = 'research/onchain-graph-2026-09-16/fullpanel'
EXPERIMENT = 'eth-full-history-feature-panel-resume-20260922'
PREDECESSOR = 'eth-full-history-feature-panel-20260922'
MAX_BUCKET = 256 * 2**20
MAX_DAY_ROWS = 2_000_000
MAX_HASH_BYTES = 40 * 2**30
CHUNK_BYTES = 32 * 2**20
PINNED_PYTHON = '/home/malecada/master_thesis/TradingAgents-audit-fixes/.venv/bin/python'


def load(path):
    return json.loads(Path(path).read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def safe_directory(path):
    path = Path(path)
    assert path.is_absolute() and path.is_dir()
    assert not any(p.is_symlink() for p in (path, *path.parents))
    return path


def inside(root, relative):
    relative = Path(relative)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = root / relative
    for parent in (path, *path.parents):
        assert not parent.is_symlink()
        if parent == root:
            break
    return path


def no_network(event, args):
    if event.startswith(('socket.', 'http.client.', 'urllib.')):
        raise RuntimeError('independent continuation check prohibits network access')


def fingerprint(root):
    """Bind namespace metadata without a second bucket payload read."""
    result = {}
    for path in root.iterdir():
        assert path.is_file() and not path.is_symlink()
        s = path.stat()
        result[path.name] = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns,
                             s.st_ctime_ns, file_sha(path) if path.suffix == '.json' else None)
    return result


def verify_buckets(hashroots, copies, expected_rows, day_digests, production, *, seed_count):
    """Independently check a chronological two-root union and its full population."""
    roots = [safe_directory(p) for p in hashroots]
    copies = safe_directory(copies)
    assert len(roots) == 2 and roots[0].resolve() != roots[1].resolve()
    assert set(expected_rows) == set(day_digests) == set(range(len(expected_rows)))
    assert type(seed_count) is int and 0 < seed_count < len(expected_rows)
    assert all(type(n) is int and 0 <= n <= MAX_DAY_ROWS for n in expected_rows.values())
    assert all(isinstance(d, str) and re.fullmatch('[0-9a-f]{64}', d) for d in day_digests.values())
    assert sum(expected_rows.values()) * 32 <= MAX_HASH_BYTES
    groups = [list(range(seed_count)), list(range(seed_count, len(expected_rows)))]
    names = {f'day-{i:04d}{s}' for i in expected_rows for s in ('.json', '.intent.json')}
    assert set(p.name for p in copies.iterdir()) == names
    before = [fingerprint(p) for p in roots]
    before_copies = fingerprint(copies)
    sizes, segments = [], [[] for _ in range(256)]
    for root_index, (root, days) in enumerate(zip(roots, groups, strict=True)):
        positions = [0] * 256
        local_names = set()
        for i in days:
            for suffix in ('.json', '.intent.json'):
                name = f'day-{i:04d}{suffix}'
                local_names.add(name)
                assert (root / name).read_bytes() == (copies / name).read_bytes()
            receipt = load(root / f'day-{i:04d}.json')
            intent = load(root / f'day-{i:04d}.intent.json')
            intent_cap = MAX_HASH_BYTES - (32 * sum(expected_rows[d] for d in groups[0]) if root_index else 0)
            assert intent == dict(schema_version=1, day_index=i, status='intent', max_total_bytes=intent_cap)
            assert receipt['schema_version'] == 1 and receipt['day_index'] == i and receipt['status'] == 'complete'
            assert receipt['rows'] == expected_rows[i] and receipt['bytes'] == 32 * expected_rows[i]
            assert receipt['stream_sha256'] == day_digests[i] and len(receipt['buckets']) == 256
            total = 0
            for bucket, item in enumerate(receipt['buckets']):
                assert item['bucket'] == f'{bucket:02x}' and item['offset'] == positions[bucket]
                assert type(item['rows']) is int and 0 <= item['rows'] <= expected_rows[i]
                assert item['bytes'] == 32 * item['rows']
                assert isinstance(item['sha256'], str) and re.fullmatch('[0-9a-f]{64}', item['sha256'])
                segments[bucket].append((root_index, i, positions[bucket], item['bytes'], item['sha256']))
                positions[bucket] += item['bytes']
                total += item['rows']
            assert total == expected_rows[i] and receipt['total_bucket_bytes'] == sum(positions)
        bucket_names = {f'{b:02x}.bin' for b, size in enumerate(positions) if size}
        assert set(before[root_index]) == local_names | bucket_names
        for b, size in enumerate(positions):
            if size:
                assert (root / f'{b:02x}.bin').stat().st_size == size
        sizes.append(positions)
    combined_sizes = [sum(local[b] for local in sizes) for b in range(256)]
    # Enforce the combined cap before any bucket allocation or payload read.
    assert all(size % 32 == 0 and size <= MAX_BUCKET for size in combined_sizes)
    daily = {i: hashlib.sha256() for i in expected_rows}
    summaries = []
    for b, size in enumerate(combined_sizes):
        identities = np.empty(size // 32, dtype='V32')
        payload = memoryview(identities).cast('B')
        start = 0
        for root_index, root in enumerate(roots):
            nbytes = sizes[root_index][b]
            if nbytes:
                with (root / f'{b:02x}.bin').open('rb', buffering=0) as stream:
                    for pos in range(start, start + nbytes, CHUNK_BYTES):
                        block = payload[pos:min(start+nbytes, pos+CHUNK_BYTES)]
                        assert stream.readinto(block) == len(block)
                        del block
                    assert stream.read(1) == b''
            start += nbytes
        raw_digest = sha(payload)
        assert bool(np.all(identities.view(np.uint8)[::32] == b))
        for root_index, i, offset, length, digest in segments[b]:
            origin = offset + (sizes[0][b] if root_index else 0)
            view = identities[origin // 32:(origin + length) // 32]
            assert sha(memoryview(view).cast('B')) == digest
            ordered = view.copy()
            ordered.sort(kind='quicksort')
            daily[i].update(memoryview(ordered).cast('B'))
            del ordered, view
        del payload
        identities.sort(kind='quicksort')
        duplicates = 0
        for offset in range(1, len(identities), 32768):
            end = min(len(identities), offset + 32768)
            duplicates += int(np.count_nonzero(identities[offset:end] == identities[offset-1:end-1]))
        rows = size // 32
        summaries.append(dict(bucket=f'{b:02x}', bytes=size, rows=rows, unique=rows-duplicates,
                              duplicate_excess=duplicates, sha256=raw_digest))
        del identities
    assert [fingerprint(p) for p in roots] == before and fingerprint(copies) == before_copies
    assert all(daily[i].hexdigest() == day_digests[i] for i in expected_rows)
    rows = sum(expected_rows.values())
    duplicates = sum(item['duplicate_excess'] for item in summaries)
    assert production['status'] == 'complete' and production['buckets'] == summaries
    assert production['rows'] == rows and production['unique'] == rows-duplicates
    assert production['duplicate_excess'] == duplicates and production['input_bytes'] == 32*rows
    assert production['days'] == len(expected_rows)
    assert production['expected_day_rows'] == {str(i): n for i, n in expected_rows.items()}
    assert production['expected_day_stream_sha256'] == {str(i): d for i, d in day_digests.items()}
    assert production['roots'] == [str(p) for p in roots]
    assert production['admitted'] is (duplicates == 0) and production['scratch_preserved'] is True
    return dict(rows=rows, unique=rows-duplicates, duplicate_excess=duplicates, input_bytes=32*rows,
                roots=[str(p) for p in roots], buckets=summaries,
                independent_sorted_day_streams_checked=len(daily),
                algorithm='independent-two-root-full32-quicksort-and-daily-sorted-stream-reconstruction')


def original_checker(root):
    path = root / ORIGINAL_BASE / 'check_final_phase_v2.py'
    spec = importlib.util.spec_from_file_location('resume_frozen_phase_correction', path)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    return wrapper.load_original(root)


def verify_plans(root, resume, original):
    ref = resume['numerical_plan']
    assert ref['path'] == ORIGINAL_BASE + '/plan.json'
    assert ref['sha256'] == '19f3716454216afc172aec2939a9908ba3b57921e99249951e1860b995d1d691'
    path = original.inside(root, ref['path'])
    assert file_sha(path) == ref['sha256']
    plan = load(path)
    dates = [str(date(2022, 1, 1) + timedelta(days=i)) for i in range(1096)]
    assert resume['dates'] == plan['dates'] == dates
    assert resume['seed_count'] == 206 and resume['prior_run_id'] == PREDECESSOR
    assert resume['seed_dates'] == dates[:206] and resume['remaining_dates'] == dates[206:]
    assert resume['limits'] == plan['limits']
    assert set(plan['expected_rows']) == set(dates)
    assert sum(plan['expected_rows'].values()) == plan['expected_total_rows'] == 1221389903
    assert plan['expected_hash_bytes'] == 39084476896
    assert set(plan['expected_graph_unavailable']) == {'2022-01-01', '2024-12-31'}
    assert plan['network_allowed'] is False
    assert len(resume['hash_roots']) == 2
    assert [r['day_indices'] for r in resume['hash_roots']] == [list(range(206)), list(range(206,1096))]
    roots = [item['path'] for item in resume['hash_roots']]
    for value in roots:
        p = Path(value)
        assert p.is_absolute() and not any(q.is_symlink() for q in (p, *p.parents))
    assert roots[0] == plan['hash_root'] and roots[0] != roots[1]
    return plan


def verify_seed(root, run, resume, original, expected_members):
    """Bind the reused dates to registered archived bytes, including path set."""
    archive = original.inside(root, resume['archive_root'])
    prefix = f'research_runs/{PREDECESSOR}/outputs/'
    outputs = {prefix + 'day-' + day + '.json' for day in resume['seed_dates']}
    expected = outputs | {str(p.relative_to(root)) for p in expected_members}
    assert set(resume['seed_files']) == expected
    for relative, ref in resume['seed_files'].items():
        source = original.inside(archive, relative)
        target = run / 'outputs' / Path(relative).name if relative in outputs else original.inside(root, relative)
        assert type(ref['bytes']) is int and ref['bytes'] >= 0
        assert source.stat().st_size == target.stat().st_size == ref['bytes']
        assert file_sha(source) == file_sha(target) == ref['sha256']


def verify_complete(root, run, plan, resume, terminal, original):
    values = [load(run / 'outputs' / ('day-' + day + '.json')) for day in plan['dates']]
    production = load(run / 'outputs/hash-audit.json')
    admitted = production.get('admitted') is True
    roots = [item['path'] for item in resume['hash_roots']]
    # Only the summary's physical-retention pointer changes. Every numerical
    # day below receives the original plan, its dates and original plan SHA.
    summary = original.verify_panel_outputs(run, dict(plan, hash_root=roots), terminal, values, admitted)
    if summary['stopped'] is not None or production['status'] != 'complete':
        assert not admitted
        return dict(passing_full_panel=False, failed_run_evidence_only=True,
                    numerical_panel_validation_performed=False,
                    observed_partial_artifacts=original.inventory(root / ORIGINAL_BASE / 'artifacts', root))
    retained, seed_members = set(), set()
    previous, expected_rows, digests = None, {}, {}
    copies = root / ORIGINAL_BASE / 'artifacts/hash-receipts'
    for i, (day, value) in enumerate(zip(plan['dates'], values, strict=True)):
        audit = original.verify_daily(root, run, plan, day, value, previous, retained)
        assert audit['source_reused'] is value['source_reused']
        assert audit['count_reused'] is value['count_reused']
        assert value['source_reused'] is ('source' in plan.get('reuse', {}).get(day, {}))
        assert value['count_reused'] is ('count' in plan.get('reuse', {}).get(day, {}))
        if day in plan['expected_graph_unavailable']:
            assert value['count']['status'] == 'unavailable'
            assert value['count']['reason'] == 'registered panel edge lacks preceding or following boundary'
            assert audit['count_unavailable_reason'] == value['count']['reason']
            assert audit['boundary_status'] == 'unavailable: missing previous or following evidence'
        else:
            assert value['count']['status'] == 'complete'
        if i + 1 < len(values):
            assert value['following']['date'] == plan['dates'][i+1]
            for key in ('first_block', 'last_block'):
                assert value['following']['integrity'][key] == values[i+1]['source']['integrity'][key]
        else:
            assert value['following'] is None
        expected_rows[i], digests[i] = audit['source_rows'], audit['source_hash_digest']
        assert value['hash_append'] == load(copies / f'day-{i:04d}.json')
        previous = value
        if i + 1 == resume['seed_count']:
            seed_members = set(retained)
    seed_members.update(copies / f'day-{i:04d}{s}' for i in range(resume['seed_count']) for s in ('.json', '.intent.json'))
    verify_seed(root, run, resume, original, seed_members)
    owner = load(root / BASE / 'hash-owner.json')
    assert owner['experiment'] == EXPERIMENT and owner['hash_roots'] == roots
    assert owner['writable_hash_root'] == roots[1]
    hashes = verify_buckets(roots, copies, expected_rows, digests, production, seed_count=resume['seed_count'])
    assert hashes['rows'] == plan['expected_total_rows'] and hashes['input_bytes'] == plan['expected_hash_bytes']
    retained.update(copies.iterdir())
    observed = original.inventory(root / ORIGINAL_BASE / 'artifacts', root)
    assert {root / row['path'] for row in observed} == retained
    success = admitted and summary['source_days'] == 1096 and summary['graph_days'] == 1094
    assert summary['expected_boundary_only'] is success
    return dict(passing_full_panel=success, failed_run_evidence_only=False,
                numerical_panel_validation_performed=True, source_days=len(values),
                graph_days=sum(v['count']['status'] == 'complete' for v in values),
                reused_source_days=resume['seed_count'], newly_computed_source_days=len(values)-resume['seed_count'],
                registered_unavailable_graph_days=list(plan['expected_graph_unavailable']),
                global_hash_verification=hashes,
                retained_artifacts=dict(files=len(observed), bytes=sum(r['bytes'] for r in observed), manifest=observed),
                deleted_arrays='Original compact phase/array manifest identities checked; no deleted-array reconstruction.')


def compute_resource(root, source):
    """Unknown or failed guard state can preserve failure evidence only."""
    path = root / BASE / 'resources/compute/final.json'
    if not path.is_file() or path.stat().st_size == 0:
        return dict(clean=False, reason='compute guard final receipt missing or empty',
                    bytes=path.stat().st_size if path.exists() else None)
    value = load(path)
    assert value['cwd'] == str(root)
    command = value['command']
    assert command == [PINNED_PYTHON, '-B', str(root / BASE / 'run.py'), '--source', source]
    assert value['memory_max_bytes'] == 6 * 2**30
    assert value['memory_high_bytes'] == 4 * 2**30 and value['memory_swap_max_bytes'] == 2**29
    assert value['reserve_bytes'] == 3 * 2**30 and value['start_reserve_bytes'] >= 9 * 2**30
    assert value['elapsed_time_kill'] is False and value['retry'] is False
    assert 0 < len(value['cpus']) <= 2 and len(set(value['cpus'])) == len(value['cpus'])
    initial = value.get('initial_memory_events', {})
    terminal = value.get('terminal_memory_snapshot') or {}
    events = value.get('memory_events', {})
    event_maps = [initial, terminal.get('memory_events', {}), events]
    oom_known_clear = all(isinstance(m, dict) and all(type(m.get(k)) is int and m[k] == 0
                         for k in ('oom', 'oom_kill')) and m.get('oom_group_kill', 0) == 0 for m in event_maps)
    terminal_bytes = terminal.get('memory_current_bytes')
    terminal_known = type(terminal_bytes) is int and 0 <= terminal_bytes <= 6*2**30
    clean = (value['phase'] == 'complete' and value['limit_reason'] is None
             and value['child_exit_code'] == 0 and oom_known_clear and terminal_known)
    if clean:
        assert terminal['memory_events'] == events
        assert value['memory_current_bytes'] == terminal_bytes <= value['peak_sampled_memory_current_bytes']
        assert value['cleanup_verified'] is True
        assert value['kernel_controls'] == {'memory.max':str(6*2**30), 'memory.high':str(4*2**30), 'memory.swap.max':str(2**29)}
        assert value['peak_sampled_memory_current_bytes'] <= 6*2**30
        assert value['unit_properties']['Result'] == 'success'
        assert value['cleanup_unit_properties']['ActiveState'] in ('inactive', 'failed')
    return dict(clean=clean, path=str(path.relative_to(root)), sha256=file_sha(path), receipt=value)


def main():
    from tradingagents.research.verify import verify_claim, verify_run
    parser = argparse.ArgumentParser()
    for key in ('root', 'source', 'report'):
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    here, run = root / BASE, root / 'research_runs' / EXPERIMENT
    report = Path(args.report)
    assert report.is_absolute() and report.parent.resolve() == here.resolve()
    assert not report.exists() and not report.is_symlink()
    assert len(os.sched_getaffinity(0)) <= 2
    sys.addaudithook(no_network)
    terminals = [p for p in (run / 'complete.json', run / 'failed.json') if p.exists()]
    assert len(terminals) == 1
    claim, structural = verify_claim(run), verify_run(run)
    terminal_digest = file_sha(terminals[0])
    terminal = load(terminals[0])
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert head == args.source == claim['source']
    assert claim['experiment_id'] == EXPERIMENT and claim['registration'] == BASE + '/gates.json'
    assert file_sha(here / 'gates.json') == claim['registration_sha256']
    assert claim['family']['prior_attempts'] == 14 and claim['family']['attempt_budget'] == 15
    exp = claim['experiment']
    assert exp['parent'] is None and exp['continuation_of'] == PREDECESSOR
    dates = [str(date(2022,1,1) + timedelta(days=i)) for i in range(1096)]
    assert exp['cells'] == [kind+'-'+d for d in dates for kind in ('source','graph')] + ['global-uniqueness']
    assert exp['outputs'] == ['day-'+d+'.json' for d in dates] + ['hash-audit.json','panel.json','summary.json']
    required_sources = {ORIGINAL_BASE+'/'+p for p in ('check_final.py','check_final_phase_v2.py','check_day.py','day.py')}
    required_sources.update(BASE+'/'+p for p in ('check_final.py','run.py','hash_union.py','launch.py','memory_guard.py'))
    assert required_sources <= set(exp['source_files'])
    for path, digest in exp['source_files'].items():
        assert file_sha(inside(root, path)) == digest
    for path, digest in exp['runtime_hashes'].items():
        assert file_sha(inside(root / 'tradingagents/research', path)) == digest
    for ref in claim['inputs'].values():
        assert file_sha(inside(root, ref['path'])) == ref['sha256']
    for path, digest in load(here / 'history.json')['metadata_hashes'].items():
        assert file_sha(inside(root, path)) == digest
    for key in ('charter','selection'):
        if exp.get(key):
            assert file_sha(inside(root, exp[key]['path'])) == exp[key]['sha256']
    assert exp['source_files'][BASE+'/check_final.py'] == file_sha(Path(__file__))
    original = original_checker(root)
    daily = original.day_module()
    resume = load(here / 'plan.json')
    plan = verify_plans(root, resume, original)
    resource = compute_resource(root, head)
    if structural['status'] == 'complete' and resource['clean']:
        assert structural['cell_count'] == 2193 and structural['output_count'] == 1099
        result = verify_complete(root, run, plan, resume, terminal, original)
    else:
        result = dict(passing_full_panel=False, failed_run_evidence_only=True,
                      numerical_panel_validation_performed=False,
                      observed_partial_artifacts=original.inventory(root / ORIGINAL_BASE / 'artifacts', root))
    assert file_sha(terminals[0]) == terminal_digest
    result.update(passed=True, source=head, structural_verification=structural,
                  reviewed_at=datetime.now(timezone.utc).isoformat(),
                  claim_sha256=file_sha(run / 'claim.json'), terminal_sha256=terminal_digest,
                  gate_sha256=claim['registration_sha256'], reviewer_script_sha256=file_sha(Path(__file__)),
                  execution_resource=resource, new_network_requests=0,
                  output_sha256={p.name:file_sha(p) for p in sorted((run/'outputs').iterdir()) if p.is_file()},
                  financial_admission=False, historical_availability_verified=False,
                  full_day_star_triangle_recounted=False,
                  qualification='Exact two-root full32 union and original compact daily evidence checks. No raw recount, exhaustive full-day star/triangle recount, canonical-chain or historical-publication proof, price, model or financial validation.')
    daily.publish_report(report, result)
    print(json.dumps(dict(passed=True, passing_full_panel=result['passing_full_panel'], lifecycle_status=structural['status'])))


if __name__ == '__main__':
    main()

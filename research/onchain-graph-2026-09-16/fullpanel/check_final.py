"""Independent closed-panel evidence and exact full32 bucket reconciliation.

No production hash-audit imports, source re-decoding, disk sorting or deletion.
"""
import argparse
from datetime import date, timedelta, datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = 'research/onchain-graph-2026-09-16/fullpanel'
EXPERIMENT = 'eth-full-history-feature-panel-20260922'
MAX_BUCKET = 256 * 2**20
MAX_DAY_ROWS = 2_000_000
MAX_HASH_BYTES = 40 * 2**30
EXTRA_DAILY_KEYS = {'independent', 'audit', 'hash_append', 'scratch_manifest', 'scratch_retention'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def inside(root, relative):
    relative = Path(relative)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = root / relative
    path.resolve().relative_to(root.resolve())
    for part in [path, *path.parents]:
        assert not part.is_symlink()
        if part == root:
            break
    return path


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def day_module():
    spec = importlib.util.spec_from_file_location('fullpanel_final_daily_review', HERE / 'check_day.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_buckets(hashroot, copies, expected_rows, day_digests, production):
    """Reconstruct sorted daily populations and count duplicates via quicksort."""
    assert hashroot.is_dir() and not hashroot.is_symlink()
    assert set(expected_rows) == set(day_digests) == set(range(len(expected_rows)))
    assert all(type(n) is int and 0 <= n <= MAX_DAY_ROWS for n in expected_rows.values())
    assert set(p.name for p in copies.iterdir()) == {f'day-{i:04d}{s}' for i in expected_rows for s in ('.json', '.intent.json')}
    positions = [0] * 256
    segments = [[] for _ in range(256)]
    receipt_names = set()
    for i in sorted(expected_rows):
        for suffix in ('.json', '.intent.json'):
            name = f'day-{i:04d}{suffix}'
            receipt_names.add(name)
            a, b = inside(hashroot, name), inside(copies, name)
            assert a.is_file() and b.is_file() and a.read_bytes() == b.read_bytes()
        receipt = load(hashroot / f'day-{i:04d}.json')
        intent = load(hashroot / f'day-{i:04d}.intent.json')
        assert intent == dict(schema_version=1, day_index=i, status='intent', max_total_bytes=MAX_HASH_BYTES)
        assert receipt['schema_version'] == 1 and receipt['day_index'] == i and receipt['status'] == 'complete'
        assert receipt['rows'] == expected_rows[i] and receipt['bytes'] == 32 * expected_rows[i]
        assert receipt['stream_sha256'] == day_digests[i]
        assert len(receipt['buckets']) == 256
        total = 0
        for b, segment in enumerate(receipt['buckets']):
            assert segment['bucket'] == f'{b:02x}' and segment['offset'] == positions[b]
            assert type(segment['rows']) is int and 0 <= segment['rows'] <= expected_rows[i]
            assert segment['bytes'] == 32 * segment['rows']
            segments[b].append((i, positions[b], segment['bytes'], segment['sha256']))
            positions[b] += segment['bytes']
            total += segment['rows']
        assert total == expected_rows[i] and receipt['total_bucket_bytes'] == sum(positions)
    bucket_names = {f'{b:02x}.bin' for b, size in enumerate(positions) if size}
    assert {p.name for p in hashroot.iterdir()} == receipt_names | bucket_names
    assert all(p.is_file() and not p.is_symlink() for p in hashroot.iterdir())
    daily = {i: hashlib.sha256() for i in expected_rows}
    summaries = []
    for b, size in enumerate(positions):
        assert size % 32 == 0 and size <= MAX_BUCKET
        path = hashroot / f'{b:02x}.bin'
        if size:
            assert path.stat().st_size == size
            identities = np.fromfile(path, dtype='V32', count=size // 32)
            assert identities.nbytes == size
            raw_sha = sha(memoryview(identities).cast('B'))
            assert bool(np.all(identities.view(np.uint8)[::32] == b))
        else:
            identities = np.empty(0, dtype='V32')
            raw_sha = sha(b'')
        for i, offset, nbytes, expected_digest in segments[b]:
            view = identities[offset // 32:(offset + nbytes) // 32]
            assert sha(memoryview(view).cast('B')) == expected_digest
            # The source checker binds the lexicographically sorted complete
            # daily hash stream. Reconstruct that stream independently of the
            # producer's unstable leading-byte partition order.
            ordered = view.copy()
            ordered.sort(kind='quicksort')
            daily[i].update(memoryview(ordered).cast('B'))
            del ordered, view
        identities.sort(kind='quicksort')
        duplicates = 0
        for start in range(1, len(identities), 32768):
            stop = min(len(identities), start + 32768)
            duplicates += int(np.count_nonzero(identities[start:stop] == identities[start-1:stop-1]))
        rows = size // 32
        summaries.append(dict(bucket=f'{b:02x}', bytes=size, rows=rows, unique=rows-duplicates,
                              duplicate_excess=duplicates, sha256=raw_sha))
        del identities
    assert all(daily[i].hexdigest() == day_digests[i] for i in expected_rows)
    rows = sum(expected_rows.values())
    assert rows * 32 <= MAX_HASH_BYTES
    duplicates = sum(s['duplicate_excess'] for s in summaries)
    assert production['status'] == 'complete' and production['buckets'] == summaries
    assert production['rows'] == rows and production['unique'] == rows - duplicates
    assert production['duplicate_excess'] == duplicates and production['input_bytes'] == rows * 32
    assert production['days'] == len(expected_rows)
    assert production['expected_day_rows'] == {str(i): n for i, n in expected_rows.items()}
    assert production['admitted'] is (duplicates == 0) and production['scratch_preserved'] is True
    return dict(rows=rows, unique=rows-duplicates, duplicate_excess=duplicates, input_bytes=rows*32,
                buckets=summaries, independent_sorted_day_streams_checked=len(daily),
                algorithm='independent-full32-quicksort-and-daily-sorted-stream-reconstruction')


def expected_panel_row(day, value, admitted):
    source, count = value['source'], value['count']
    audit = value.get('independent') or {}
    source_ok = admitted and source['status'] == 'complete' and audit.get('passed') is True
    graph_ok = source_ok and count['status'] == 'complete' and audit.get('count_verified') is True
    row = dict(day=day, source_admitted=source_ok, graph_admitted=graph_ok,
               available_at=None, historical_availability_verified=False,
               source_status=source['status'], graph_status=count['status'],
               reason=count.get('reason') or source.get('reason'))
    if source['status'] == 'complete':
        row.update({k: source['activity'][k] for k in ('events', 'nodes', 'directed_pairs')})
        row['transactions'] = source['integrity']['rows']
    if count['status'] == 'complete':
        summary = count['features']
        roles = summary['local40_sums']
        row.update(stars=sum(roles[:24]), dyads=sum(roles[24:32]) // 2,
                   triangles=sum(roles[32:]) // 3, overlap_nodes=summary['overlap_node_count'],
                   nonzero_nodes=summary['nonzero_nodes'], local40=summary)
    return row


def verify_daily(root, run, plan, day, value, previous, retained):
    """Bind compact summaries to the checked phase and intentionally deleted arrays."""
    module = day_module()
    p2, _ = module.reviewers()
    artifacts = root / BASE / 'artifacts'
    assert value['date'] == day and value['source']['status'] == 'complete'
    audit_ref = value['audit']
    audit_path = inside(root, audit_ref['path'])
    assert audit_path == artifacts / 'checks' / (day + '.json')
    retained.add(audit_path)
    assert file_sha(audit_path) == audit_ref['sha256']
    audit = load(audit_path)
    assert audit == value['independent'] and audit['passed'] is True and audit['date'] == day
    phase = {k: v for k, v in value.items() if k not in EXTRA_DAILY_KEYS}
    phase_digest = sha(json_bytes(phase))
    assert audit['phase_sha256'] == phase_digest
    assert audit['plan_sha256'] == value['plan_sha256'] == file_sha(root / BASE / 'plan.json')
    assert audit['reviewer_script_sha256'] == file_sha(HERE / 'check_day.py')
    source = value['source']
    assert audit['source_rows'] == source['integrity']['rows'] == source['expected_rows'] == plan['expected_rows'][day]
    assert audit['event_digest'] == source['integrity']['ordered_events_sha256']
    assert audit['events'] == source['activity']['events']
    prefix_digest, prefix_count = module.shard_digest(root, source['prefix'], p2,
                                                   beneath=artifacts / 'prefixes' / day)
    assert prefix_digest == audit['prefix_digest'] and prefix_count == audit['prefix_events']
    for meta in source['prefix']:
        retained.add(inside(root, meta['path']))
    if previous is None:
        assert value['previous'] is None and value['previous_output_sha256'] is None
    else:
        assert value['previous']['date'] == previous['date']
        assert value['previous']['prefix'] == previous['source']['prefix']
        assert value['previous']['integrity'] == previous['source']['integrity']
        assert value['previous']['audit'] == previous['audit']
        assert value['previous_output_sha256'] == file_sha(run / 'outputs' / ('day-' + previous['date'] + '.json'))
    counted = value['count']['status'] == 'complete'
    assert audit['count_verified'] is counted
    if counted:
        assert audit['boundary_status'] == 'passed' and audit['count_check']['full_completion_and_cross_midnight_dyads_recounted'] is True
        assert audit['count_check']['full_day_star_triangle_recounted'] is False
        assert audit['count_check']['unique_occurrences'] == value['count']['features']['unique_occurrences']
        assert audit['count_check']['cross_midnight_unique_occurrences'] == value['count']['features']['cross_midnight_unique_occurrences']
    else:
        assert value['count'].get('reason') and audit['count_check'] is None and audit['local_digest'] is None
    scratch = artifacts / 'scratch' / day
    assert not scratch.exists()
    records = value['scratch_manifest']
    members = {row['path']: row for row in records}
    assert len(members) == len(records)
    for path, row in members.items():
        inside(root, path).relative_to(scratch)
        assert type(row['bytes']) is int and row['bytes'] >= 0
    phase_name = str((scratch / 'phase.json').relative_to(root))
    assert members[phase_name]['sha256'] == phase_digest and members[phase_name]['bytes'] == len(json_bytes(phase))
    expected_scratch = {phase_name}
    for group in (source['events'], source['transaction_hashes'], value['count'].get('counts', [])):
        for meta in group:
            expected_scratch.add(meta['path'])
            assert members[meta['path']]['sha256'] == meta['stored_sha256']
            assert members[meta['path']]['bytes'] == meta['stored_bytes']
    assert set(members) == expected_scratch
    cleanup_path = artifacts / 'cleanup' / (day + '.json')
    retained.add(cleanup_path)
    cleanup = load(cleanup_path)
    assert cleanup['date'] == day and cleanup['released'] is True
    assert cleanup['daily_output_sha256'] == file_sha(run / 'outputs' / ('day-' + day + '.json'))
    assert cleanup['files'] == len(records) and cleanup['bytes'] == sum(m['bytes'] for m in records)
    return audit


def inventory(directory, root):
    records = []
    if directory.exists():
        for path in sorted(directory.rglob('*')):
            assert not path.is_symlink()
            if path.is_file():
                records.append(dict(path=str(path.relative_to(root)), bytes=path.stat().st_size,
                                    sha256=file_sha(path)))
            else:
                assert path.is_dir()
    return records


def verify_panel_outputs(run, plan, terminal, values, admitted):
    """Independently derive all admission flags and lifecycle cell statuses."""
    dates = plan['dates']
    cells = []
    for day, value in zip(dates, values, strict=True):
        assert value['date'] == day
        for kind, key in [('source', 'source'), ('graph', 'count')]:
            status = value[key]['status']
            assert status in ('complete', 'unavailable')
            cell = dict(id=kind+'-'+day, status=status)
            if status == 'unavailable':
                assert value[key].get('reason')
                cell['reason'] = value[key]['reason']
            cells.append(cell)
    actual_cells = terminal['cells']
    assert actual_cells[:-1] == cells
    assert actual_cells[-1]['id'] == 'global-uniqueness'
    assert actual_cells[-1]['status'] == ('complete' if admitted else 'unavailable')
    if not admitted:
        assert actual_cells[-1].get('reason')
    rows = [expected_panel_row(d, v, admitted) for d, v in zip(dates, values, strict=True)]
    panel = load(run / 'outputs/panel.json')
    assert panel == dict(days=rows, global_uniqueness_admitted=admitted,
                         historical_availability_verified=False, prices_or_models_opened=False)
    summary = load(run / 'outputs/summary.json')
    assert summary['cells'] == actual_cells and summary['dates'] == len(dates)
    assert summary['source_days'] == sum(r['source_admitted'] for r in rows)
    assert summary['graph_days'] == sum(r['graph_admitted'] for r in rows)
    unavailable = [r['day'] for r in rows if not r['graph_admitted']]
    assert summary['unavailable_graph_days'] == unavailable
    assert summary['expected_boundary_only'] is (admitted and set(unavailable) == set(plan['expected_graph_unavailable']))
    assert summary['requests'] == 0 and summary['raw_capture_modified'] is False
    assert summary['hash_scratch_retained'] == plan['hash_root']
    return summary


def verify_complete(root, run, plan, terminal):
    dates = plan['dates']
    values = [load(run / 'outputs' / ('day-' + d + '.json')) for d in dates]
    production = load(run / 'outputs/hash-audit.json')
    admitted = production.get('admitted') is True
    summary = verify_panel_outputs(run, plan, terminal, values, admitted)
    # A structurally complete lifecycle can contain an interrupted panel. Preserve
    # its files without converting its unavailable cells into numerical success.
    if summary['stopped'] is not None or production['status'] != 'complete':
        assert not admitted
        return dict(passing_full_panel=False, failed_run_evidence_only=True,
                    numerical_panel_validation_performed=False,
                    observed_partial_artifacts=inventory(root / BASE / 'artifacts', root))
    retained, previous, expected_rows, digests = set(), None, {}, {}
    for i, (day, value) in enumerate(zip(dates, values, strict=True)):
        audit = verify_daily(root, run, plan, day, value, previous, retained)
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
        if i + 1 < len(dates):
            assert value['following']['date'] == dates[i+1]
            for key in ('first_block', 'last_block'):
                assert value['following']['integrity'][key] == values[i+1]['source']['integrity'][key]
        else:
            assert value['following'] is None
        expected_rows[i], digests[i] = audit['source_rows'], audit['source_hash_digest']
        assert value['hash_append'] == load(root / BASE / 'artifacts/hash-receipts' / f'day-{i:04d}.json')
        previous = value
    hashroot = Path(plan['hash_root'])
    assert hashroot.is_absolute()
    for p in [hashroot, *hashroot.parents]:
        assert not p.is_symlink()
    owner = load(root / BASE / 'hash-owner.json')
    assert owner['experiment'] == EXPERIMENT and owner['hash_root'] == str(hashroot)
    copies = root / BASE / 'artifacts/hash-receipts'
    hashes = verify_buckets(hashroot, copies, expected_rows, digests, production)
    assert hashes['rows'] == plan['expected_total_rows'] == 1221389903
    assert hashes['input_bytes'] == plan['expected_hash_bytes'] == 39084476896
    retained.update(copies.iterdir())
    observed = inventory(root / BASE / 'artifacts', root)
    assert {root / r['path'] for r in observed} == retained
    success = admitted and summary['source_days'] == 1096 and summary['graph_days'] == 1094
    assert summary['expected_boundary_only'] is success
    return dict(passing_full_panel=success, failed_run_evidence_only=False,
                numerical_panel_validation_performed=True, source_days=len(values),
                graph_days=sum(v['count']['status'] == 'complete' for v in values),
                registered_unavailable_graph_days=list(plan['expected_graph_unavailable']),
                global_hash_verification=hashes,
                retained_artifacts=dict(files=len(observed), bytes=sum(r['bytes'] for r in observed),
                                        manifest=observed),
                deleted_arrays='Recomputable event/hash/local arrays deliberately absent; immutable phase digests, scratch manifests, audits and retained prefixes checked.')


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
    if report.exists() or report.is_symlink():
        raise FileExistsError('final independent report already exists')
    assert len(os.sched_getaffinity(0)) <= 2
    module = day_module()
    import sys
    sys.addaudithook(module.no_network)
    terminals = [p for p in (run / 'complete.json', run / 'failed.json') if p.exists()]
    assert len(terminals) == 1, 'A unique terminal receipt is required before review.'
    claim, structural = verify_claim(run), verify_run(run)
    terminal_digest = file_sha(terminals[0])
    terminal = load(terminals[0])
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert head == args.source == claim['source']
    assert claim['registration'] == BASE + '/gates.json'
    assert file_sha(here / 'gates.json') == claim['registration_sha256']
    assert claim['family']['prior_attempts'] == 13 and claim['family']['attempt_budget'] == 14
    exp = claim['experiment']
    assert exp['parent'] is None and exp['continuation_of'] == 'eth-seven-day-offline-pilot-20260922'
    dates = [str(date(2022, 1, 1) + timedelta(days=i)) for i in range(1096)]
    assert exp['cells'] == [kind+'-'+d for d in dates for kind in ('source', 'graph')] + ['global-uniqueness']
    assert exp['outputs'] == ['day-'+d+'.json' for d in dates] + ['hash-audit.json', 'panel.json', 'summary.json']
    for path, digest in exp['source_files'].items():
        assert file_sha(inside(root, path)) == digest
    for path, digest in exp['runtime_hashes'].items():
        assert file_sha(inside(root / 'tradingagents/research', path)) == digest
    for ref in claim['inputs'].values():
        assert file_sha(inside(root, ref['path'])) == ref['sha256']
    for path, digest in load(here / 'history.json')['metadata_hashes'].items():
        assert file_sha(inside(root, path)) == digest
    for key in ('charter', 'selection'):
        if exp.get(key):
            assert file_sha(inside(root, exp[key]['path'])) == exp[key]['sha256']
    assert exp['source_files'][BASE+'/check_final.py'] == file_sha(Path(__file__))
    plan = load(here / 'plan.json')
    assert plan['dates'] == dates and set(plan['expected_rows']) == set(dates)
    assert sum(plan['expected_rows'].values()) == plan['expected_total_rows'] == 1221389903
    assert plan['expected_hash_bytes'] == 39084476896
    assert set(plan['expected_graph_unavailable']) == {'2022-01-01', '2024-12-31'}
    assert plan['network_allowed'] is False
    resource = load(here / 'resource.json')
    assert resource['source'] == head and resource['rss_limit_bytes'] == 8 * 2**30
    assert resource['elapsed_time_kill'] is False
    if structural['status'] == 'complete':
        assert structural['cell_count'] == 2193 and structural['output_count'] == 1099
        assert resource['child_exit_code'] == 0 and resource['limit_reason'] is None
        assert resource['peak_sampled_tree_rss_bytes'] <= resource['rss_limit_bytes']
        result = verify_complete(root, run, plan, terminal)
    else:
        result = dict(passing_full_panel=False, failed_run_evidence_only=True,
                      numerical_panel_validation_performed=False,
                      observed_partial_artifacts=inventory(here / 'artifacts', root))
    assert file_sha(terminals[0]) == terminal_digest
    result.update(passed=True, source=head, structural_verification=structural,
                  reviewed_at=datetime.now(timezone.utc).isoformat(),
                  claim_sha256=file_sha(run / 'claim.json'), terminal_sha256=terminal_digest,
                  gate_sha256=claim['registration_sha256'], reviewer_script_sha256=file_sha(Path(__file__)),
                  execution_resource=resource, new_network_requests=0,
                  output_sha256={p.name:file_sha(p) for p in sorted((run / 'outputs').iterdir())},
                  financial_admission=False, historical_availability_verified=False,
                  full_day_star_triangle_recounted=False,
                  qualification='Exact full32 global identities and retained daily raw-reconstruction/dyad/bounded-oracle evidence. No exhaustive full-day star/triangle recount, canonical-chain proof, historical publication proof, price, model or financial validation.')
    module.publish_report(report, result)
    print(json.dumps(dict(passed=True, passing_full_panel=result['passing_full_panel'],
                          lifecycle_status=structural['status'])))


if __name__ == '__main__':
    main()

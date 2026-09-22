"""Independent offline continuation review; no production numerical imports.

Real retained bytes are opened only by the post-terminal CLI. Imported prior
reviewer functions reconstruct rows and use separate dyad/oracle algorithms.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import urllib.parse

import zstandard as zstd

HERE = Path(__file__).resolve().parent
PREFIX = 'research/onchain-graph-2026-09-16/pilot2'
DAYS = [f'2024-01-{i:02d}' for i in range(2, 9)]


def load(path):
    return json.loads(path.read_bytes())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inside(root, relative):
    relative = Path(relative)
    assert not relative.is_absolute() and '..' not in relative.parts
    path = root / relative
    assert all(not p.is_symlink() for p in [path, *path.parents] if p != root.parent)
    path.resolve().relative_to(root.resolve())
    return path


def decompress(path, meta):
    n, stored_n = meta['raw_bytes'], meta['stored_bytes']
    assert type(n) is int and 0 <= n <= 64 * 1024**2
    assert type(stored_n) is int and 0 <= stored_n <= 65 * 1024**2
    assert meta['codec'] == 'zstd' and meta['level'] == 3
    assert path.stat().st_size == stored_n
    stored = path.read_bytes()
    assert sha(stored) == meta['stored_sha256']
    assert zstd.frame_content_size(stored) == n
    assert zstd.get_frame_parameters(stored).has_checksum
    raw = zstd.ZstdDecompressor().decompress(stored, max_output_size=max(1, n), allow_extra_data=False)
    assert len(raw) == n and sha(raw) == meta['raw_sha256']
    assert meta['base64_theoretical_bytes'] == 4 * ((n + 2) // 3)
    return raw


def plain_blob(root, meta, parent=None):
    relative = meta['path']
    path = inside(parent if '/' not in relative and parent else root, relative)
    path.resolve().relative_to((root / PREFIX / 'artifacts').resolve())
    return decompress(path, meta)


def prior_checker():
    path = HERE.parent / 'pilot/check_independent.py'
    spec = importlib.util.spec_from_file_location('offline_pilot_prior_review', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.plain_blob = plain_blob
    return module


def check_tree(root, manifest, strict=True):
    """Exact new-tree membership and independent raw/stored roundtrip binding."""
    base = root / PREFIX / 'artifacts'
    paths = sorted(p for p in base.rglob('*') if p.is_file())
    assert not any(p.is_symlink() for p in base.rglob('*'))
    records = {r['path']: r for r in manifest['files']}
    assert len(records) == len(manifest['files'])
    assert set(records) == {str(p.relative_to(root)) for p in paths}
    assert manifest['bytes'] == sum(r['bytes'] for r in records.values())
    bound = set()
    def visit(value, parent):
        if isinstance(value, dict):
            if {'path', 'raw_bytes', 'stored_bytes', 'raw_sha256', 'stored_sha256', 'codec', 'level'} <= value.keys():
                plain_blob(root, value, parent)
                path = parent / value['path'] if '/' not in value['path'] else root / value['path']
                bound.add(path.resolve())
            for child in value.values():
                visit(child, parent)
        elif isinstance(value, list):
            for child in value:
                visit(child, parent)
    for path in paths:
        record = records[str(path.relative_to(root))]
        assert path.stat().st_size == record['bytes'] and file_sha(path) == record['sha256']
        if path.suffix == '.json':
            visit(load(path), path.parent)
    blobs = {p.resolve() for p in paths if p.suffix == '.zst'}
    assert bound <= blobs
    if strict:
        assert bound == blobs
    return {'files': len(paths), 'bytes': manifest['bytes'], 'roundtripped_blobs': len(bound),
            'unbound_blobs': sorted(str(p.relative_to(root)) for p in blobs - bound)}


def verify_boundaries(before, current, following):
    for left, right in ((before, current), (current, following)):
        a, b = left['last_block'], right['first_block']
        assert b[0] == a[0] + 1 and b[2].lower() == a[1].lower() and b[3] > a[3]


def verify_counts(root, result, prefix, events, start, end):
    """Recount full-day dyads and fixed small subsets independently."""
    assert all(start - 3600 <= e[0] < start for e in prefix)
    assert all(start <= e[0] < end for e in events)
    reviewer = prior_checker()
    return reviewer.verify_counts(root, result, prefix, events, start, end, reviewer.reviewer_math())


def verified_input(root, plan, name):
    info = plan['inputs'][name]
    path = inside(root, info['path'])
    assert file_sha(path) == info['sha256']
    return load(path)


def capture_reader(root, plan, day):
    """Check every selected retained member, while leaving old derived extras alone."""
    spec = plan['captures'][day]
    directory = Path(spec['directory'])
    if not directory.is_absolute():
        directory = inside(root, spec['directory'])
    assert directory.is_dir() and not directory.is_symlink()
    manifest_path = inside(root, spec['manifest']['path'])
    assert file_sha(manifest_path) == spec['manifest']['sha256']
    manifest = load(manifest_path)
    assert manifest.get('status', manifest.get('result', {}).get('status')) == 'complete'
    assert manifest.get('date', manifest.get('result', {}).get('date')) == day
    members = {r['path']: r for r in manifest['files']}
    assert len(members) == len(manifest['files'])
    for relative, record in members.items():
        path = inside(directory, relative)
        assert path.is_file() and path.stat().st_size == record['bytes']
        assert file_sha(path) == record['sha256'], relative
    paths = sorted(n for n in members if n.startswith('request-') and n.endswith('.json') and not n.endswith('-intent.json'))
    assert paths == [f'request-{i:04d}.json' for i in range(1, len(paths) + 1)]
    assert {n for n in members if n.startswith('request-') and n.endswith('-intent.json')} == {n[:-5]+'-intent.json' for n in paths}
    records = []
    bound = set()
    for i, name in enumerate(paths, 1):
        record = load(inside(directory, name))
        intent = load(inside(directory, name[:-5] + '-intent.json'))
        assert record['request_number'] == i and intent['method'] == 'GET'
        for key in ('url', 'request_headers', 'requested_at', 'request_number'):
            assert record[key] == intent[key]
        meta = record['blob']
        assert Path(meta['path']).name == meta['path'] and meta['path'] in members
        assert meta['path'] not in bound
        bound.add(meta['path'])
        assert members[meta['path']]['sha256'] == meta['stored_sha256']
        assert members[meta['path']]['bytes'] == meta['stored_bytes']
        records.append(record)
    assert bound == {n for n in members if n.endswith('.zst')}
    def read(index):
        record = records[index]
        raw = decompress(inside(directory, record['blob']['path']), record['blob'])
        assert len(raw) == record['bytes'] and sha(raw) == record['sha256']
        return raw
    return directory, members, records, read


def source_material(root, plan, day, reviewer):
    """Read the frozen projection, never a derived event file as source evidence."""
    inventory = verified_input(root, plan, plan['inventory_input'])
    obj = reviewer.object_for(inventory, 'transactions', day)
    blocks_obj = reviewer.object_for(inventory, 'blocks', day)
    url = lambda value: plan['base_url'] + urllib.parse.quote(value['key'], safe='/=')
    if day == '2024-01-01':
        context = plan['context']
        projection = verified_input(root, plan, context['plan_input'])
        blocks_record = verified_input(root, plan, context['blocks_input'])
        footer_record = verified_input(root, plan, context['footer_input'])
        blocks, footer = reviewer.old_body(blocks_record), reviewer.old_body(footer_record)
        assert len(context['range_inputs']) == len(projection['ranges']) == 117
        def read(i):
            record = verified_input(root, plan, context['range_inputs'][i])
            raw = reviewer.old_body(record)
            span = projection['ranges'][i]
            reviewer.check_response(record, raw, obj, url(obj), span['start'], span['end'])
            return raw
    else:
        directory, members, records, body = capture_reader(root, plan, day)
        assert 'projection.json' in members
        projection = load(directory / 'projection.json')
        assert len(records) == 3 + len(projection['ranges'])
        blocks_record, footer_record = records[0], records[2]
        blocks, tail, footer = body(0), body(1), body(2)
        reviewer.check_response(records[1], tail, obj, url(obj), obj['size'] - 8, obj['size'] - 1)
        assert footer[-8:] == tail
        def read(i):
            raw = body(i + 3)
            span = projection['ranges'][i]
            reviewer.check_response(records[i + 3], raw, obj, url(obj), span['start'], span['end'])
            return raw
    reviewer.check_response(blocks_record, blocks, blocks_obj, url(blocks_obj))
    reviewer.check_response(footer_record, footer, obj, url(obj), obj['size'] - len(footer), obj['size'] - 1)
    assert projection['object'] == obj
    assert footer[-4:] == b'PAR1' and len(footer) == int.from_bytes(footer[-8:-4], 'little') + 8
    assert len(footer) <= plan['limits']['max_footer_bytes'] + 8
    assert len(blocks) <= plan['limits']['max_block_bytes']
    assert 0 < projection['rows'] <= 2_000_000 and 0 < len(projection['groups']) <= 32
    assert len(projection['ranges']) == 9 * len(projection['groups'])
    assert obj['size'] <= plan['limits']['max_logical_bytes']
    assert sum(r['bytes'] for r in projection['ranges']) <= plan['limits']['max_projection_bytes']
    for raw, types in ((b'PAR1' + footer, plan['required_types']), (blocks, plan['block_required_types'])):
        schema = reviewer.pq.read_metadata(reviewer.io.BytesIO(raw)).schema.to_arrow_schema()
        assert all(str(schema.field(key).type) == value for key, value in types.items())
    return projection, footer, blocks, read


def verify_success(root, run, terminal, plan):
    assert plan['dates'] == DAYS and plan['network_allowed'] is False
    assert plan['limits']['max_requests'] == plan['limits']['max_total_bytes'] == 0
    reviewer = prior_checker()
    output = lambda name: load(run / 'outputs' / name)
    base = root / PREFIX / 'artifacts/results'
    phases = [output('context.json'), *[output(f'source-{day}.json') for day in DAYS]]
    closing = output('boundary.json')
    for phase in [*phases, closing]:
        assert phase['status'] in ('complete', 'unavailable')
        assert phase['requests'] == phase['raw_bytes'] == 0 and phase['denied'] is False
        assert phase['plan_sha256'] == file_sha(root / PREFIX / 'plan.json')
    if closing['status'] == 'complete':
        _, _, records, body = capture_reader(root, plan, '2024-01-09')
        assert len(records) == 1
        inventory = verified_input(root, plan, plan['inventory_input'])
        obj = reviewer.object_for(inventory, 'blocks', '2024-01-09')
        raw = body(0)
        reviewer.check_response(records[0], raw, obj, plan['base_url'] + urllib.parse.quote(obj['key'], safe='/='))
        start = int(datetime(2024, 1, 9, tzinfo=timezone.utc).timestamp())
        rows = reviewer.block_rows(raw, start, start + 86400)
        assert closing['integrity']['first_block'] == list(rows[0])
        assert closing['integrity']['last_block'] == list(rows[-1])
        assert closing['integrity']['blocks'] == len(rows) and not closing['integrity']['transactions_checked']
    all_days = ['2024-01-01', *DAYS]
    hashes_seen, duplicates, decoded, counts = set(), [], {}, {}
    previous_prefix = None
    total_rows = 0
    for day, phase in zip(all_days, phases, strict=True):
        assert phase['date'] == day
        if phase['status'] != 'complete':
            previous_prefix = None
            continue
        start = int(datetime.fromisoformat(day + 'T00:00:00+00:00').timestamp())
        projection, footer, blocks, read = source_material(root, plan, day, reviewer)
        events, integrity, activity, hashes = reviewer.decode_day(projection, footer, blocks, read, start, start + 86400)
        for key, value in integrity.items():
            assert phase['integrity'][key] == value, (day, key)
        assert phase['activity'] == activity
        assert reviewer.shard_rows(root, phase['events']) == [list(e) for e in events]
        prefix = [e for e in events if e[0] >= start + 86400 - 3600]
        assert reviewer.shard_rows(root, phase['prefix']) == [list(e) for e in prefix]
        hash_bytes = b''.join(plain_blob(root, item) for item in phase['transaction_hashes'])
        assert hash_bytes == b''.join(sorted(hashes)) and len(hash_bytes) == integrity['rows'] * 32
        assert sum(item['hashes'] for item in phase['transaction_hashes']) == integrity['rows']
        if not hashes_seen.isdisjoint(hashes):
            duplicates.append(day)
        hashes_seen.update(hashes)
        total_rows += len(hashes)
        decoded[day] = {'integrity': integrity, 'activity': activity}
        if day in DAYS:
            result = output(f'features-{day}.json')
            if result['status'] == 'complete':
                assert previous_prefix is not None
                prior_day = all_days[all_days.index(day) - 1]
                prior_mode = 'context' if prior_day == '2024-01-01' else 'source'
                assert result['source_result_sha256'] == file_sha(base / f'source-{day}.json')
                assert result['previous_result_sha256'] == file_sha(base / f'{prior_mode}-{prior_day}.json')
                counts[day] = verify_counts(root, result, previous_prefix, events, start, start + 86400)
        previous_prefix = prefix
        del events, hashes, hash_bytes
    uniqueness = output('cross-day-integrity.json')
    assert uniqueness['rows'] == total_rows and uniqueness['unique_hashes'] == len(hashes_seen)
    assert uniqueness['covered_days'] == list(decoded) and uniqueness['duplicate_days'] == duplicates
    assert uniqueness['unavailable_days'] == [day for day in all_days if day not in decoded]
    assert uniqueness['all_eight_sources_checked'] == (len(decoded) == 8)
    assert uniqueness['status'] == ('unavailable' if duplicates or len(decoded) != 8 else 'complete')
    if duplicates or len(decoded) != 8:
        assert not counts
    for day in counts:
        index = all_days.index(day)
        before, current = decoded[all_days[index - 1]]['integrity'], decoded[day]['integrity']
        following = closing['integrity'] if day == DAYS[-1] else decoded[all_days[index + 1]]['integrity']
        verify_boundaries(before, current, following)
    summary = output('summary.json')
    assert summary['requests'] == summary['raw_bytes'] == 0 and summary['network_allowed'] is False
    assert summary['complete_motif_days'] == len(counts)
    assert {r['id']: r['status'] for r in summary['cells']} == {r['id']: r['status'] for r in terminal['cells']}
    actual_cells = {'context': phases[0]['status'], 'boundary': closing['status'],
                    'uniqueness': uniqueness['status']}
    actual_cells.update({'source-' + day: phase['status'] for day, phase in zip(DAYS, phases[1:], strict=True)})
    actual_cells.update({'motifs-' + day: output(f'features-{day}.json')['status'] for day in DAYS})
    assert actual_cells == {r['id']: r['status'] for r in terminal['cells']}
    compact = output('features.json')
    assert compact['historical_publication_verified'] is False and compact['prices_or_targets_opened'] is False
    assert compact['days'] == [{k: v for k, v in output(f'features-{day}.json').items() if k not in ('counts', 'artifacts', 'checks')} for day in DAYS]
    return {'decoded_days': decoded, 'counted_days': counts, 'complete_motif_days': len(counts),
            'unique_transactions_across_available_days': len(hashes_seen), 'full_day_star_triangle_recounted': False}


def main():
    from tradingagents.research.verify import verify_claim, verify_run
    parser = argparse.ArgumentParser()
    for name in ('root', 'source'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--output', '--report', dest='output', required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    here = root / PREFIX
    run = root / 'research_runs/eth-seven-day-offline-pilot-20260922'
    assert len(os.sched_getaffinity(0)) <= 2
    terminals = [p for p in (run / 'complete.json', run / 'failed.json') if p.exists()]
    assert len(terminals) == 1, 'Do not open empirical inputs before a unique terminal receipt.'
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    claim, structural, terminal = verify_claim(run), verify_run(run), load(terminals[0])
    assert source == claim['source'] == args.source
    assert claim['family']['prior_attempts'] == 12 and claim['family']['attempt_budget'] == 13
    exp = claim['experiment']
    expected_cells = ['context', 'boundary', *['source-' + d for d in DAYS], 'uniqueness', *['motifs-' + d for d in DAYS]]
    expected_outputs = ['context.json', 'boundary.json', *['source-' + d + '.json' for d in DAYS], 'cross-day-integrity.json', *['features-' + d + '.json' for d in DAYS], 'manifest.json', 'features.json', 'summary.json']
    assert exp['cells'] == expected_cells and exp['outputs'] == expected_outputs
    for path, digest in exp['source_files'].items():
        assert file_sha(inside(root, path)) == digest
    for path, digest in exp['runtime_hashes'].items():
        assert file_sha(inside(root / 'tradingagents/research', path)) == digest
    for info in claim['inputs'].values():
        assert file_sha(inside(root, info['path'])) == info['sha256']
    history = load(here / 'history.json')
    for path, digest in history['metadata_hashes'].items():
        assert file_sha(inside(root, path)) == digest
    resource = load(here / 'resource.json')
    assert resource['source'] == source and resource['rss_limit_bytes'] == 8 * 1024**3
    assert resource['elapsed_time_kill'] is False
    plan = load(here / 'plan.json')
    if structural['status'] == 'complete':
        assert structural['cell_count'] == 17 and structural['output_count'] == 20
        assert resource['child_exit_code'] == 0 and resource['limit_reason'] is None
        assert resource['peak_sampled_tree_rss_bytes'] <= resource['rss_limit_bytes']
        tree = check_tree(root, load(run / 'outputs/manifest.json'))
        result = verify_success(root, run, terminal, plan)
    else:
        files = [dict(path=str(p.relative_to(root)), bytes=p.stat().st_size, sha256=file_sha(p))
                 for p in sorted((here / 'artifacts').rglob('*')) if p.is_file()]
        manifest = dict(files=files, bytes=sum(r['bytes'] for r in files))
        tree = check_tree(root, manifest, strict=False)
        result = dict(failed_run_evidence_only=True, numerical_reconstruction_performed=False,
                      observed_partial_artifacts=manifest)
    result.update(passed=True, source=source, reviewed_at=datetime.now(timezone.utc).isoformat(),
                  structural_verification=structural, artifact_verification=tree,
                  execution_resource=resource, claim_sha256=file_sha(run / 'claim.json'),
                  terminal_sha256=file_sha(terminals[0]), gate_sha256=file_sha(here / 'gates.json'),
                  reviewer_script_sha256=file_sha(Path(__file__)), new_network_requests=0,
                  output_sha256={p.name: file_sha(p) for p in sorted((run / 'outputs').iterdir()) if p.is_file()},
                  numerical_pilot_success=structural['status'] == 'complete' and result.get('complete_motif_days') == 7,
                  financial_admission=False, historical_availability_verified=False,
                  qualification='Independent raw-byte/source/dyad/export reconciliation. No full-day star/triangle recount, canonical-chain validation, historical publication proof, forecasts or financial evaluation.')
    with Path(args.output).open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps(dict(passed=True, status=structural['status'], artifact_files=tree['files'],
                         complete_motif_days=result.get('complete_motif_days'), numerical_pilot_success=result['numerical_pilot_success'])))


if __name__ == '__main__':
    main()

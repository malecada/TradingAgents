"""Independent one-day raw reconstruction and pre-cleanup compact-panel review."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import urllib.parse

HERE = Path(__file__).resolve().parent
PREFIX = 'research/onchain-graph-2026-09-16/fullpanel'
QUALIFICATION = ('Static count-weighted top-level address graph; no entity labels, '
                 'monetary weights, temporal motifs or economic interpretation.')


def no_network(event, args):
    if event.startswith(('socket.', 'http.client.', 'urllib.')):
        raise RuntimeError('independent panel check prohibits network access')


def reviewers():
    path = HERE.parent / 'pilot2/check_independent.py'
    spec = importlib.util.spec_from_file_location('fullpanel_prior_independent', path)
    p2 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p2)
    p2.PREFIX = PREFIX
    physical_reader = p2.capture_reader
    def logical_reader(root, plan, day):
        directory, members, records, read = physical_reader(root, plan, day)
        reused = plan['captures'][day].get('reused_blocks')
        if reused is None:
            return directory, members, records, read
        block_plan = dict(plan, captures={day: reused})
        _, _, block_records, block_read = physical_reader(root, block_plan, day)
        assert len(block_records) == 1
        def logical_read(index):
            return block_read(0) if index == 0 else read(index - 1)
        return directory, members, [block_records[0], *records], logical_read
    p2.capture_reader = logical_reader
    return p2, p2.prior_checker()


def canonical_rows(rows):
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        digest.update((json.dumps(row, separators=(',', ':')) + '\n').encode())
        count += 1
    return digest.hexdigest(), count


def shard_digest(root, metadata, p2, expected=None, beneath=None):
    digest = hashlib.sha256()
    count = 0
    seen = set()
    expected_iter = iter(expected) if expected is not None else None
    sentinel = object()
    for meta in metadata:
        path = p2.inside(root, meta['path'])
        if beneath is not None:
            path.relative_to(beneath)
        assert path not in seen
        seen.add(path)
        raw = p2.plain_blob(root, meta)
        rows = [json.loads(line) for line in raw.splitlines()]
        assert type(meta['rows']) is int and meta['rows'] == len(rows) <= 10000
        assert raw == b''.join((json.dumps(row, separators=(',', ':')) + '\n').encode() for row in rows)
        for row in rows:
            if expected_iter is not None:
                wanted = next(expected_iter, sentinel)
                assert wanted is not sentinel and row == list(wanted)
        digest.update(raw)
        count += len(rows)
    if expected_iter is not None:
        assert next(expected_iter, sentinel) is sentinel
    return digest.hexdigest(), count


def hash_digest(root, metadata, hashes, p2, beneath):
    expected = sorted(hashes)
    offset = 0
    digest = hashlib.sha256()
    seen = set()
    for meta in metadata:
        path = p2.inside(root, meta['path'])
        path.relative_to(beneath)
        assert path not in seen
        seen.add(path)
        raw = p2.plain_blob(root, meta)
        n = meta['hashes']
        assert type(n) is int and 0 < n <= 1_000_000 and len(raw) == 32 * n
        assert raw == b''.join(expected[offset:offset + n])
        offset += n
        digest.update(raw)
    assert offset == len(expected)
    return digest.hexdigest()


def block_integrity(root, plan, day, p2, reviewer):
    inventory = p2.verified_input(root, plan, plan['inventory_input'])
    obj = reviewer.object_for(inventory, 'blocks', day)
    if day == '2024-01-01':
        receipt = p2.verified_input(root, plan, plan['context']['blocks_input'])
        raw = reviewer.old_body(receipt)
    else:
        _, _, records, read = p2.capture_reader(root, plan, day)
        receipt, raw = records[0], read(0)
    reviewer.check_response(receipt, raw, obj, plan['base_url'] + urllib.parse.quote(obj['key'], safe='/='))
    schema = reviewer.pq.read_metadata(reviewer.io.BytesIO(raw)).schema.to_arrow_schema()
    assert all(str(schema.field(k).type) == v for k, v in plan['block_required_types'].items())
    start = int(datetime.fromisoformat(day + 'T00:00:00+00:00').timestamp())
    rows = reviewer.block_rows(raw, start, start + 86400)
    return {'first_block': list(rows[0]), 'last_block': list(rows[-1]), 'blocks': len(rows)}


def previous_prefix(root, previous, start, p2, reviewer):
    day = datetime.fromtimestamp(start - 86400, timezone.utc).date().isoformat()
    assert previous['date'] == day
    audit_ref = previous['audit']
    audit_path = p2.inside(root, audit_ref['path'])
    assert p2.file_sha(audit_path) == audit_ref['sha256']
    audit = p2.load(audit_path)
    assert audit['passed'] is True and audit['date'] == day
    prefix = reviewer.shard_rows(root, previous['prefix'])
    assert all(len(e) == 4 and start - 3600 <= e[0] < start for e in prefix)
    assert all(a[0] <= b[0] and a[1] < b[1] for a, b in zip(prefix, prefix[1:]))
    digest, count = shard_digest(root, previous['prefix'], p2,
                                beneath=root / PREFIX / 'artifacts/prefixes' / day)
    assert digest == audit['prefix_digest'] and count == audit['prefix_events']
    return [tuple(event) for event in prefix]


def check(root, plan, phase):
    p2, reviewer = reviewers()
    day = phase['date']
    assert day in plan['dates'] and phase['source']['date'] == day
    assert plan['network_allowed'] is False
    current = phase['source']
    assert current['status'] == 'complete'
    assert type(phase['source_reused']) is bool and type(phase['count_reused']) is bool
    date = datetime.fromisoformat(day + 'T00:00:00+00:00')
    start, end = int(date.timestamp()), int(date.timestamp()) + 86400
    material = p2.source_material(root, plan, day, reviewer)
    events, integrity, activity, hashes = reviewer.decode_day(*material, start, end)
    assert integrity['rows'] == current['expected_rows'] == plan['expected_rows'][day]
    for key, value in integrity.items():
        assert current['integrity'][key] == value, (day, key)
    assert current['activity'] == dict(activity, qualification=QUALIFICATION)
    scratch = root / PREFIX / 'artifacts/scratch' / day
    event_digest, event_count = shard_digest(root, current['events'], p2, expected=events, beneath=scratch)
    assert event_digest == integrity['ordered_events_sha256'] and event_count == len(events)
    prefix = [event for event in events if event[0] >= end - 3600]
    prefix_digest, prefix_count = shard_digest(root, current['prefix'], p2, expected=prefix,
                                             beneath=root / PREFIX / 'artifacts/prefixes' / day)
    source_hash_digest = hash_digest(root, current['transaction_hashes'], hashes, p2, scratch)
    del hashes
    previous, following = phase['previous'], phase['following']
    count = phase['count']
    assert count['status'] in ('complete', 'unavailable')
    boundary_status = 'unavailable: missing previous or following evidence'
    prior_prefix = None
    if previous is not None:
        prior_prefix = previous_prefix(root, previous, start, p2, reviewer)
        before = block_integrity(root, plan, previous['date'], p2, reviewer)
        for key in ('first_block', 'last_block'):
            assert previous['integrity'][key] == before[key]
    if following is not None:
        assert following['date'] == (date + timedelta(days=1)).date().isoformat()
        after = block_integrity(root, plan, following['date'], p2, reviewer)
        for key in ('first_block', 'last_block'):
            assert following['integrity'][key] == after[key]
    if previous is not None and following is not None:
        try:
            p2.verify_boundaries(before, integrity, after)
        except AssertionError:
            boundary_status = 'unavailable: block height, parent hash or timestamp discontinuity'
        else:
            boundary_status = 'passed'
    count_check = None
    local_digest = None
    if count['status'] == 'complete':
        assert boundary_status == 'passed' and prior_prefix is not None
        local_digest, _ = shard_digest(root, count['counts'], p2, beneath=scratch)
        count_check = reviewer.verify_counts(root, count, prior_prefix, events, start, end, reviewer.reviewer_math())
    else:
        assert count.get('reason')
    return {'passed': True, 'date': day, 'source_rows': integrity['rows'],
            'source_hash_digest': source_hash_digest, 'event_digest': event_digest,
            'events': event_count, 'prefix_digest': prefix_digest, 'prefix_events': prefix_count,
            'local_digest': local_digest, 'count_verified': count_check is not None,
            'boundary_status': boundary_status, 'count_check': count_check,
            'count_unavailable_reason': count.get('reason') if count_check is None else None,
            'source_reused': phase['source_reused'], 'count_reused': phase['count_reused'],
            'qualification': 'Independent full raw-day reconstruction, exported identities/events/prefix and full completion-day dyads; bounded full-role subsets only. No exhaustive full-day stars/triangles, canonical-chain, publication-time, price or financial validation.'}


def publish_report(path, result):
    with path.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'plan', 'phase', 'report'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    sys.addaudithook(no_network)
    root = Path(args.root).resolve()
    p2, _ = reviewers()
    report = Path(args.report)
    assert report.is_absolute()
    report.resolve().relative_to(root / PREFIX / 'artifacts')
    if report.exists() or report.is_symlink():
        raise FileExistsError('independent daily report already exists')
    plan_path, phase_path = p2.inside(root, args.plan), p2.inside(root, args.phase)
    plan_raw, phase_raw = plan_path.read_bytes(), phase_path.read_bytes()
    plan, phase = json.loads(plan_raw), json.loads(phase_raw)
    assert phase['plan_sha256'] == p2.sha(plan_raw)
    result = check(root, plan, phase)
    assert p2.file_sha(plan_path) == p2.sha(plan_raw) and p2.file_sha(phase_path) == p2.sha(phase_raw)
    result.update(phase_sha256=p2.sha(phase_raw), plan_sha256=p2.sha(plan_raw),
                  reviewer_script_sha256=p2.file_sha(Path(__file__)))
    publish_report(report, result)
    print(json.dumps({'passed': True, 'date': result['date'], 'count_verified': result['count_verified']}))


if __name__ == '__main__':
    main()

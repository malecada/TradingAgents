"""Invented Parquet days only; no retained empirical source is opened."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


c = module('fullpanel_check_day_test', 'research/onchain-graph-2026-09-16/fullpanel/check_day.py')
n = module('fullpanel_check_day_numeric_fixture', 'research/onchain-graph-2026-09-16/pilot/numeric.py')
f = module('fullpanel_check_day_rows_fixture', 'tests/research/test_onchain_graph_prototype.py')
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return {'path': str(path), 'sha256': sha(path.read_bytes())}


def blob(root, path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = zstd.ZstdCompressor(level=3, write_checksum=True, write_content_size=True).compress(raw)
    path.write_bytes(stored)
    return dict(path=str(path.relative_to(root)), raw_bytes=len(raw), stored_bytes=len(stored),
                raw_sha256=sha(raw), stored_sha256=sha(stored), codec='zstd', level=3,
                base64_theoretical_bytes=4 * ((len(raw) + 2) // 3))


def shard(root, path, rows):
    if not rows:
        return []
    raw = b''.join((json.dumps(row, separators=(',', ':')) + '\n').encode() for row in rows)
    return [dict(blob(root, path, raw), rows=len(rows))]


def parquet(data):
    stream = io.BytesIO()
    pq.write_table(pa.table(data), stream, row_group_size=3)
    return stream.getvalue()


def capture(root, plan, day, number, block_hash, parent, seconds, reused=False):
    rows = [list(row) for row in f.rows()]
    for row in rows:
        row[1:4] = [block_hash, number, seconds * 10**9]
    data = dict(zip(n.COLUMNS, zip(*rows, strict=True), strict=True))
    data['block_timestamp'] = pa.array(data['block_timestamp'], type=pa.timestamp('ns'))
    raw = parquet(data)
    blocks = parquet(dict(number=[number], hash=[block_hash], parent_hash=[parent],
                          timestamp=pa.array([seconds * 10**9], type=pa.timestamp('ns')),
                          transaction_count=[len(rows)]))
    footer = raw[-int.from_bytes(raw[-8:-4], 'little') - 8:]
    objects = {table: dict(key=f'{table}/{day}', etag='"synthetic"', size=len(body))
               for table, body in [('blocks', blocks), ('transactions', raw)]}
    projected = n.projection(objects['transactions'], footer, plan['limits'], plan['required_types'])
    requests = [(objects['blocks'], blocks, None, None),
                (objects['transactions'], raw[-8:], len(raw)-8, len(raw)-1),
                (objects['transactions'], footer, len(raw)-len(footer), len(raw)-1)]
    requests += [(objects['transactions'], raw[s['start']:s['end']+1], s['start'], s['end']) for s in projected['ranges']]
    def publish(directory, rows, with_projection):
        directory.mkdir()
        if with_projection:
            write_json(directory / 'projection.json', projected)
        for i, (obj, body, first, last) in enumerate(rows, 1):
            stem = f'request-{i:04d}'
            headers = {'If-Match': obj['etag']}
            response = {'etag': obj['etag']}
            if first is not None:
                headers['Range'] = f'bytes={first}-{last}'
                response['content-range'] = f'bytes {first}-{last}/{obj["size"]}'
            identity = dict(request_number=i, requested_at='2026-09-01T00:00:00+00:00',
                            url=plan['base_url'] + obj['key'], request_headers=headers)
            write_json(directory / (stem + '-intent.json'), dict(identity, method='GET'))
            meta = blob(directory, directory / (stem + '.body.zst'), body)
            write_json(directory / (stem + '.json'), dict(identity, status=200 if first is None else 206,
                       response_headers=response, bytes=len(body), sha256=sha(body), blob=meta))
        members = [dict(path=p.name, bytes=p.stat().st_size, sha256=sha(p.read_bytes())) for p in sorted(directory.iterdir())]
        manifest = root / (directory.name + '-manifest.json')
        write_json(manifest, dict(status='complete', date=day, files=members))
        return dict(directory=str(directory), manifest=dict(path=manifest.name, sha256=sha(manifest.read_bytes())))
    descriptor = publish(root / ('capture-' + day), requests[1:] if reused else requests, True)
    if reused:
        descriptor['reused_blocks'] = publish(root / ('reused-blocks-' + day), requests[:1], False)
    plan['captures'][day] = descriptor
    for table, obj in objects.items():
        plan['_inventory']['inventories'][0]['dates'].append(dict(table=table, date=day, status='complete', objects=[obj]))
    start = int(datetime.fromisoformat(day + 'T00:00:00+00:00').timestamp())
    identities = []
    events, integrity, activity = n.decode(projected, footer, blocks, lambda i: raw[projected['ranges'][i]['start']:projected['ranges'][i]['end']+1], start, start+86400, hash_sink=identities.extend)
    return events, integrity, json.loads(json.dumps(activity)), identities


def fixture(root, reused=False):
    day = '2024-01-03'
    start = int(datetime(2024, 1, 3, tzinfo=timezone.utc).timestamp())
    plan = dict(dates=['2024-01-02', day, '2024-01-04'], network_allowed=False,
                base_url='https://example.invalid/', inventory_input='inventory', inputs={}, captures={},
                expected_rows={d: 7 for d in ['2024-01-02', day, '2024-01-04']},
                required_types=dict(zip(n.COLUMNS, ['string', 'string', 'int64', 'timestamp[ns]', 'int64', 'string', 'string', 'double', 'int64'], strict=True)),
                block_required_types=dict(number='int64', hash='string', parent_hash='string', timestamp='timestamp[ns]', transaction_count='int64'),
                limits=dict(max_logical_bytes=8*2**30, max_footer_bytes=4*2**20,
                            max_projection_bytes=256*2**20, max_response_bytes=32*2**20, max_block_bytes=16*2**20),
                _inventory={'inventories': [{'dates': []}]})
    old_hash, current_hash, next_hash = ['0x' + x * 64 for x in '789']
    prev, before, _, _ = capture(root, plan, '2024-01-02', 99, old_hash, '0x'+'6'*64, start-1)
    events, integrity, activity, hashes = capture(root, plan, day, 100, current_hash, old_hash, start, reused)
    _, after, _, _ = capture(root, plan, '2024-01-04', 101, next_hash, current_hash, start+86400)
    inventory = root / 'inventory.json'
    write_json(inventory, plan.pop('_inventory'))
    plan['inputs']['inventory'] = dict(path=inventory.name, sha256=sha(inventory.read_bytes()))
    base = root / c.PREFIX / 'artifacts'
    scratch = base / 'scratch' / day
    source = dict(date=day, status='complete', expected_rows=7, integrity=integrity, activity=activity,
                  events=shard(root, scratch / 'events.zst', events), prefix=[],
                  transaction_hashes=[dict(blob(root, scratch / 'hashes.zst', b''.join(hashes)), hashes=len(hashes))])
    previous = dict(date='2024-01-02', integrity=before,
                    prefix=shard(root, base / 'prefixes/2024-01-02/prefix.zst', prev))
    audit = base / 'audit-2024-01-02.json'
    digest, count = c.canonical_rows(prev)
    write_json(audit, dict(passed=True, date='2024-01-02', prefix_digest=digest, prefix_events=count))
    previous['audit'] = dict(path=str(audit.relative_to(root)), sha256=sha(audit.read_bytes()))
    local, features, checks, _ = n.count_day(prev, events, start, start+86400)
    counted = dict(status='complete', features=features, checks=checks,
                   counts=shard(root, scratch / 'local.zst', sorted(local.items())))
    phase = dict(date=day, source=source, count=counted, previous=previous,
                 following=dict(date='2024-01-04', integrity=after), source_reused=False, count_reused=False)
    return plan, json.loads(json.dumps(phase))


@pytest.mark.parametrize('reused', [False, True])
def test_full_raw_reconstruction_dyads_and_reused_block_transport(tmp_path, reused):
    plan, phase = fixture(tmp_path, reused)
    result = c.check(tmp_path, plan, phase)
    assert result['passed'] and result['count_verified'] and result['boundary_status'] == 'passed'
    assert result['source_rows'] == 7 and result['events'] == 3 and result['prefix_events'] == 0
    assert result['count_check']['full_completion_and_cross_midnight_dyads_recounted']
    assert result['count_check']['bounded_subsets_recounted'] == 2


@pytest.mark.parametrize('change', ['annotation', 'activity', 'hashes', 'event', 'local', 'audit', 'prior_date', 'following', 'expected_rows'])
def test_independent_defects_rejected(tmp_path, change):
    plan, phase = fixture(tmp_path)
    if change == 'annotation':
        phase['source']['activity']['qualification'] = 'altered'
    elif change == 'activity':
        phase['source']['activity']['events'] += 1
    elif change == 'hashes':
        phase['source']['transaction_hashes'][0]['hashes'] -= 1
    elif change == 'event':
        phase['source']['events'] = []
    elif change == 'local':
        phase['count']['features']['local40_square_sums'][24] += 1
    elif change == 'audit':
        phase['previous']['audit']['sha256'] = '0' * 64
    elif change == 'prior_date':
        phase['previous']['date'] = '2024-01-01'
    elif change == 'following':
        phase['following']['integrity']['first_block'][2] = 'wrong-parent'
    else:
        plan['expected_rows'][phase['date']] = 8
    with pytest.raises(AssertionError):
        c.check(tmp_path, plan, phase)


@pytest.mark.parametrize('missing', ['previous', 'following'])
def test_boundary_unavailable_still_checks_all_source_rows(tmp_path, missing):
    plan, phase = fixture(tmp_path)
    phase[missing] = None
    phase['count'] = dict(status='unavailable', reason='missing boundary')
    result = c.check(tmp_path, plan, phase)
    assert result['passed'] and result['source_rows'] == 7 and not result['count_verified']
    assert result['boundary_status'].startswith('unavailable:')
    phase['count'] = dict(status='complete')
    with pytest.raises(AssertionError):
        c.check(tmp_path, plan, phase)


def test_valid_interval_prior_prefix_cannot_change_after_audit(tmp_path):
    plan, phase = fixture(tmp_path)
    meta = phase['previous']['prefix'][0]
    p2, reviewer = c.reviewers()
    rows = reviewer.shard_rows(tmp_path, [meta])
    rows[0][2] = f.C
    phase['previous']['prefix'] = shard(tmp_path, tmp_path / meta['path'], rows)
    with pytest.raises(AssertionError):
        c.check(tmp_path, plan, phase)


def test_network_prohibition():
    with pytest.raises(RuntimeError, match='network'):
        c.no_network('socket.connect', ())


def test_report_publication_is_exclusive(tmp_path):
    report = tmp_path / 'report.json'
    c.publish_report(report, {'passed': True})
    assert json.loads(report.read_bytes()) == {'passed': True}
    with pytest.raises(FileExistsError):
        c.publish_report(report, {'passed': False})
    assert json.loads(report.read_bytes()) == {'passed': True}

"""Synthetic adversarial checks of the continuation's independent reviewer."""
import importlib.util
import json
from pathlib import Path

import pytest
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[2]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


r = module('pilot2_independent_test', 'research/onchain-graph-2026-09-16/pilot2/check_independent.py')
n = module('pilot2_independent_numeric_fixture', 'research/onchain-graph-2026-09-16/pilot/numeric.py')
f = module('pilot2_independent_raw_fixture', 'tests/research/test_onchain_graph_prototype.py')


def write_blob(root, name, raw):
    path = root / r.PREFIX / 'artifacts' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    stored = zstd.ZstdCompressor(level=3, write_checksum=True, write_content_size=True).compress(raw)
    path.write_bytes(stored)
    return dict(path=str(path.relative_to(root)), codec='zstd', level=3, raw_bytes=len(raw),
                stored_bytes=len(stored), raw_sha256=r.sha(raw), stored_sha256=r.sha(stored),
                base64_theoretical_bytes=4 * ((len(raw) + 2) // 3))


def manifest(root):
    files = [dict(path=str(p.relative_to(root)), bytes=p.stat().st_size, sha256=r.file_sha(p))
             for p in sorted((root / r.PREFIX / 'artifacts').rglob('*')) if p.is_file()]
    return dict(files=files, bytes=sum(p['bytes'] for p in files))


def count_fixture(root):
    prefix = [(99, 1, 'a', 'b'), (99, 2, 'b', 'a')]
    events = [(100, 3, 'a', 'b'), (100, 4, 'a', 'c'), (101, 5, 'c', 'b')]
    local, summary, checks, _ = n.count_day(prefix, events, 100, 200)
    raw = b''.join((json.dumps(row, separators=(',', ':')) + '\n').encode() for row in sorted(local.items()))
    meta = write_blob(root, 'counts.jsonl.zst', raw)
    meta['rows'] = len(local)
    # Roundtrip gives the JSON-native list types actually published by workers.
    result = json.loads(json.dumps(dict(counts=[meta], features=summary, checks=checks)))
    return result, prefix, events


def test_independent_decode_reconstructs_hand_counted_source():
    plan, raw, footer, blocks = f.parquet_fixture()
    events, integrity, activity, hashes = r.prior_checker().decode_day(
        plan, footer, blocks, lambda i: raw[plan['ranges'][i]['start']:plan['ranges'][i]['end']+1],
        f.START // 10**9, f.END // 10**9)
    assert len(events) == 3 and len(hashes) == 7
    assert integrity['rows'] == 7 and integrity['missing_block_positions'] == 0
    assert activity['events'] == 3 and activity['reciprocal_dyads'] == 1


def test_independent_decode_rejects_projection_omission():
    plan, raw, footer, blocks = f.parquet_fixture()
    plan['ranges'].pop()
    with pytest.raises(AssertionError):
        r.prior_checker().decode_day(plan, footer, blocks, lambda i: raw[plan['ranges'][i]['start']:plan['ranges'][i]['end']+1], f.START // 10**9, f.END // 10**9)


def test_independent_completion_recount_and_oracle(tmp_path):
    result, prefix, events = count_fixture(tmp_path)
    checked = r.verify_counts(tmp_path, result, prefix, events, 100, 200)
    assert checked['full_completion_and_cross_midnight_dyads_recounted']
    assert checked['bounded_subsets_recounted'] == 2
    assert checked['full_day_star_triangle_recounted'] is False


def test_wrong_dyad_rejected_even_with_consistent_summary(tmp_path):
    result, prefix, events = count_fixture(tmp_path)
    rows = r.prior_checker().shard_rows(tmp_path, result['counts'])
    rows[0][1][24] += 1
    raw = b''.join((json.dumps(row, separators=(',', ':')) + '\n').encode() for row in rows)
    meta = write_blob(tmp_path, 'changed.jsonl.zst', raw)
    meta['rows'] = len(rows)
    result['counts'] = [meta]
    with pytest.raises(AssertionError):
        r.verify_counts(tmp_path, result, prefix, events, 100, 200)


@pytest.mark.parametrize('mutation', ['node_omitted', 'oracle_changed', 'summary_changed', 'old_prefix'])
def test_completion_defects_are_rejected(tmp_path, mutation):
    result, prefix, events = count_fixture(tmp_path)
    if mutation == 'node_omitted':
        result['counts'] = []
    elif mutation == 'oracle_changed':
        result['checks']['samples'][0]['local_counts']['a'][0] += 1
    elif mutation == 'summary_changed':
        result['features']['local40_square_sums'][0] += 1
    else:
        prefix = [(-4000, 0, 'x', 'y'), *prefix]
    with pytest.raises(AssertionError):
        r.verify_counts(tmp_path, result, prefix, events, 100, 200)


@pytest.mark.parametrize('index,bad', [(0, 103), (2, 'wrong'), (3, 10)])
def test_each_closing_boundary_property_is_required(index, bad):
    before = {'last_block': [100, 'a', 'z', 10, 0]}
    current = {'first_block': [101, 'b', 'a', 20, 0], 'last_block': [102, 'c', 'b', 30, 0]}
    following = {'first_block': [103, 'd', 'c', 40, 0]}
    r.verify_boundaries(before, current, following)
    current['first_block'][index] = bad
    with pytest.raises(AssertionError):
        r.verify_boundaries(before, current, following)


def test_new_tree_exact_membership_and_roundtrip(tmp_path):
    meta = write_blob(tmp_path, 'data.zst', b'evidence')
    result = tmp_path / r.PREFIX / 'artifacts/result.json'
    result.write_text(json.dumps({'blob': meta}))
    expected = manifest(tmp_path)
    assert r.check_tree(tmp_path, expected)['roundtripped_blobs'] == 1
    (result.parent / 'extra.txt').write_text('unregistered')
    with pytest.raises(AssertionError):
        r.check_tree(tmp_path, expected)


def test_unbound_blob_and_raw_hash_corruption_rejected(tmp_path):
    meta = write_blob(tmp_path, 'data.zst', b'evidence')
    with pytest.raises(AssertionError):
        r.check_tree(tmp_path, manifest(tmp_path))
    assert r.check_tree(tmp_path, manifest(tmp_path), strict=False)['unbound_blobs']
    meta['raw_sha256'] = '0' * 64
    with pytest.raises(AssertionError):
        r.plain_blob(tmp_path, meta)


def test_blob_path_escape_rejected(tmp_path):
    meta = write_blob(tmp_path, 'data.zst', b'evidence')
    meta['path'] = '../escape.zst'
    with pytest.raises(AssertionError):
        r.plain_blob(tmp_path, meta)


def retained_fixture(root):
    directory = root / 'retained'
    directory.mkdir()
    raw = b'bounded retained evidence'
    stored = zstd.ZstdCompressor(level=3, write_checksum=True, write_content_size=True).compress(raw)
    meta = dict(path='request-0001.body.zst', codec='zstd', level=3, raw_bytes=len(raw),
                stored_bytes=len(stored), raw_sha256=r.sha(raw), stored_sha256=r.sha(stored),
                base64_theoretical_bytes=4 * ((len(raw) + 2) // 3))
    record = dict(request_number=1, url='https://example.invalid/retained', request_headers={},
                  requested_at='2024-01-01T00:00:00+00:00', blob=meta, bytes=len(raw), sha256=r.sha(raw))
    intent = {k: record[k] for k in ('request_number', 'url', 'request_headers', 'requested_at')}
    intent['method'] = 'GET'
    (directory / meta['path']).write_bytes(stored)
    (directory / 'request-0001.json').write_text(json.dumps(record))
    (directory / 'request-0001-intent.json').write_text(json.dumps(intent))
    members = [dict(path=p.name, bytes=p.stat().st_size, sha256=r.file_sha(p)) for p in sorted(directory.iterdir())]
    frozen = root / 'manifest.json'
    frozen.write_text(json.dumps(dict(status='complete', date='2024-01-02', files=members)))
    plan = dict(captures={'2024-01-02': dict(directory=str(directory), manifest=dict(path=frozen.name, sha256=r.file_sha(frozen)))})
    return plan, raw, directory, frozen


def test_retained_manifest_checks_selected_bytes_without_erasing_old_extras(tmp_path):
    plan, raw, directory, _ = retained_fixture(tmp_path)
    (directory / 'preserved-old-derived.json').write_text('{}')
    _, _, records, read = r.capture_reader(tmp_path, plan, '2024-01-02')
    assert len(records) == 1 and read(0) == raw
    (directory / 'request-0001.body.zst').write_bytes(b'changed')
    with pytest.raises(AssertionError):
        r.capture_reader(tmp_path, plan, '2024-01-02')


@pytest.mark.parametrize('mutation', ['missing_intent', 'duplicate_member', 'path_escape'])
def test_retained_manifest_denominator_defects_rejected(tmp_path, mutation):
    plan, _, _, frozen = retained_fixture(tmp_path)
    value = json.loads(frozen.read_bytes())
    if mutation == 'missing_intent':
        value['files'] = [v for v in value['files'] if not v['path'].endswith('-intent.json')]
    elif mutation == 'duplicate_member':
        value['files'].append(value['files'][0])
    else:
        value['files'][0]['path'] = '../outside'
    frozen.write_text(json.dumps(value))
    plan['captures']['2024-01-02']['manifest']['sha256'] = r.file_sha(frozen)
    with pytest.raises(AssertionError):
        r.capture_reader(tmp_path, plan, '2024-01-02')

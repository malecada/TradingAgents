"""Synthetic retained-capture and numerical phase checks; no empirical inputs."""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import struct

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('pilot2_day_test', ROOT / 'research/onchain-graph-2026-09-16/pilot2/day.py')
day = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(day)
fixture = day.old.module('pilot2_synthetic_fixture', ROOT / 'tests/research/test_onchain_graph_prototype.py')


def capture(root):
    _, transactions, _, blocks = fixture.parquet_fixture()
    directory = root / 'capture'
    directory.mkdir()
    objects = {name: dict(key=name, etag='"fixed"', size=len(raw)) for name, raw in [('blocks', blocks), ('transactions', transactions)]}
    inventory = {'inventories': [{'dates': [dict(date='2024-01-01', table=name, status='complete', objects=[obj]) for name, obj in objects.items()]}]}
    raw = json.dumps(inventory).encode()
    (root / 'inventory.json').write_bytes(raw)
    types = lambda raw: {f.name: str(f.type) for f in day.numeric.pq.read_metadata(io.BytesIO(raw)).schema.to_arrow_schema()}
    plan = dict(base_url='https://example.test/', inventory_input='inventory',
                inputs={'inventory': dict(path='inventory.json', sha256=day.storage.sha(raw))},
                required_types=types(transactions), block_required_types=types(blocks),
                limits=dict(max_logical_bytes=8*1024**3, max_footer_bytes=4*1024**2,
                            max_projection_bytes=256*1024**2, max_response_bytes=32*1024**2))
    length = struct.unpack('<I', transactions[-8:-4])[0]
    footer = transactions[-length-8:]
    projected = day.numeric.projection(objects['transactions'], footer, plan['limits'], plan['required_types'])
    day.storage.atomic_json(directory / 'projection.json', projected)
    requests = [(objects['blocks'], blocks, None, None), (objects['transactions'], transactions[-8:], len(transactions)-8, len(transactions)-1),
                (objects['transactions'], footer, len(transactions)-len(footer), len(transactions)-1)]
    requests += [(objects['transactions'], transactions[r['start']:r['end']+1], r['start'], r['end']) for r in projected['ranges']]
    for number, (obj, body, first, last) in enumerate(requests, 1):
        stem = f'request-{number:04d}'
        headers = {'If-Match': obj['etag']}
        response = {'etag': obj['etag']}
        if first is not None:
            headers['Range'] = f'bytes={first}-{last}'
            response['content-range'] = f'bytes {first}-{last}/{obj["size"]}'
        base = dict(url=plan['base_url']+obj['key'], request_headers=headers, request_number=number)
        day.storage.atomic_json(directory / (stem+'-intent.json'), base)
        blob = day.storage.write_blob(directory / (stem+'.body.zst'), body)
        day.storage.atomic_json(directory / (stem+'.json'), dict(base, status=200 if first is None else 206,
            response_headers=response, blob=blob, bytes=len(body), sha256=day.storage.sha(body)))
    manifest = dict(status='complete', date='2024-01-01', files=day.old.artifact_manifest(directory, directory))
    raw = json.dumps(manifest).encode()
    (root / 'manifest.json').write_bytes(raw)
    plan['captures'] = {'2024-01-01': dict(directory=str(directory), manifest=dict(path='manifest.json', sha256=day.storage.sha(raw)))}
    return plan


def test_offline_source_and_completion_count(tmp_path):
    plan = capture(tmp_path)
    plan_raw = json.dumps(plan).encode()
    (tmp_path / 'plan.json').write_bytes(plan_raw)
    artifacts = tmp_path / 'research/onchain-graph-2026-09-16/pilot2/artifacts'
    artifacts.mkdir(parents=True)
    args = argparse.Namespace(root=str(tmp_path), plan='plan.json', mode='source', date='2024-01-01', result=str(artifacts/'source-result.json'))
    result = day.execute(args)
    assert result['status'] == 'complete', result
    assert result['requests'] == result['raw_bytes'] == 0
    assert sum(m['hashes'] for m in result['transaction_hashes']) == 7
    assert not list((artifacts/'source-2024-01-01').glob('request*'))
    prefix_dir = artifacts / 'previous'
    prefix_dir.mkdir()
    prefix = [[fixture.START//10**9-1, 1, fixture.A, fixture.B], [fixture.START//10**9-1, 2, fixture.B, fixture.A]]
    previous = dict(status='complete', mode='context', date='2023-12-31', plan_sha256=day.storage.sha(plan_raw),
        integrity={'last_block': [99, result['integrity']['first_block'][2], '0x'+'9'*64, fixture.START-10**9, 2]},
        prefix=day.old.shards(tmp_path, prefix_dir, 'prefix', prefix), artifacts=day.old.artifact_manifest(tmp_path, prefix_dir))
    previous_raw = json.dumps(previous).encode()
    previous_path = artifacts/'previous-result.json'
    previous_path.write_bytes(previous_raw)
    args.current_result = str(Path(args.result).relative_to(tmp_path))
    args.previous_result = str(previous_path.relative_to(tmp_path))
    args.current_sha256 = day.storage.sha(Path(args.result).read_bytes())
    args.previous_sha256 = day.storage.sha(previous_raw)
    args.mode, args.result = 'count', str(artifacts/'count-result.json')
    counted = day.execute(args)
    assert counted['status'] == 'complete', counted
    assert counted['features']['cross_midnight_unique_occurrences'] > 0
    with pytest.raises(FileExistsError):
        day.execute(args)


@pytest.mark.parametrize('change', ['manifest', 'blob', 'escape', 'duplicate', 'wrong_date'])
def test_corruption_and_manifest_rejection(tmp_path, change):
    plan = capture(tmp_path)
    descriptor = plan['captures']['2024-01-01']
    manifest_path = tmp_path/'manifest.json'
    if change == 'manifest':
        manifest_path.write_bytes(manifest_path.read_bytes()+b' ')
    elif change == 'blob':
        path = tmp_path/'capture/request-0001.body.zst'
        path.write_bytes(path.read_bytes()+b'x')
    else:
        manifest = json.loads(manifest_path.read_bytes())
        if change == 'escape':
            manifest['files'][0]['path'] = '../inventory.json'
        elif change == 'duplicate':
            manifest['files'].append(manifest['files'][0])
        else:
            manifest['date'] = '2024-01-02'
        raw = json.dumps(manifest).encode()
        manifest_path.write_bytes(raw)
        descriptor['manifest']['sha256'] = day.storage.sha(raw)
    with pytest.raises(ValueError):
        day.retained_capture(tmp_path, plan, '2024-01-01')


def test_network_guard_and_symlink_escape(tmp_path):
    with pytest.raises(RuntimeError, match='network'):
        day.deny_network('socket.connect', ())
    (tmp_path/'escape').symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(ValueError):
        day.within(tmp_path, 'escape/outside')

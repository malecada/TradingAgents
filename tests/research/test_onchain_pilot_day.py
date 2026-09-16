"""Synthetic phase helpers; no archive inputs or requests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[2] / 'research/onchain-graph-2026-09-16/pilot/day.py'
SPEC = importlib.util.spec_from_file_location('onchain_pilot_day_test', PATH)
day = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(day)


class DayTests(unittest.TestCase):
    def test_checked_response_rejects_silent_full_get_etag_and_range_changes(self):
        obj = {'etag': '"a"', 'size': 8}
        receipt = {'status': 206, 'response_headers': {'etag': '"a"', 'content-range': 'bytes 1-3/8'}}
        self.assertEqual(day.checked_response(b'abc', receipt, obj, 1, 3), b'abc')
        for bad in [dict(receipt, status=200), dict(receipt, response_headers={'etag': '"b"'}),
                    dict(receipt, response_headers={'etag': '"a"', 'content-range': 'bytes 0-2/8'})]:
            with self.assertRaises(ValueError):
                day.checked_response(b'abc', bad, obj, 1, 3)

    def test_shards_and_input_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = [[i, i, 'a', 'b'] for i in range(10001)]
            meta = day.shards(root, root, 'events', rows)
            self.assertEqual([m['rows'] for m in meta], [10000, 1])
            self.assertEqual(day.read_shards(root, meta), rows)
            raw = b'{"inventories": []}'
            (root / 'input.json').write_bytes(raw)
            plan = {'inputs': {'inventory': {'path': 'input.json', 'sha256': day.storage.sha(raw)}}}
            self.assertEqual(day.verified_input(root, plan, 'inventory'), raw)
            (root / 'input.json').write_bytes(raw + b' ')
            with self.assertRaises(ValueError):
                day.verified_input(root, plan, 'inventory')
            with self.assertRaises(ValueError):
                day.within(root, '../outside')

    def test_generated_artifact_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'raw').write_bytes(b'a')
            result = {'status': 'complete', 'artifacts': day.artifact_manifest(root, root)}
            (root / 'result.json').write_text(json.dumps(result))
            self.assertEqual(day.generated_result(root, 'result.json'), result)
            (root / 'raw').write_bytes(b'b')
            with self.assertRaises(ValueError):
                day.generated_result(root, 'result.json')

    def test_inventory_exact_unique_complete(self):
        row = {'date': '2024-01-02', 'table': 'blocks', 'status': 'complete', 'objects': [{'size': 99}]}
        inventory = {'inventories': [{'dates': [row]}]}
        self.assertEqual(day.object_for(inventory, 'blocks', '2024-01-02'), {'size': 99})
        with self.assertRaises(ValueError):
            day.object_for(inventory, 'transactions', '2024-01-02')
        row['objects'].append({'size': 44})
        with self.assertRaises(ValueError):
            day.object_for(inventory, 'blocks', '2024-01-02')


if __name__ == '__main__':
    unittest.main()


def test_end_to_end_mocked_archive_source_and_count():
    import argparse
    import io
    from unittest.mock import patch
    fixture = day.module('day_fixture', PATH.parents[3] / 'tests/research/test_onchain_graph_prototype.py')
    old, txraw, _, blocks = fixture.parquet_fixture()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        objects = {name: {'key': name, 'etag': '"fixed"', 'size': len(raw)}
                   for name, raw in [('blocks', blocks), ('transactions', txraw)]}
        inventory = {'inventories': [{'dates': [dict(date='2024-01-01', table=name, status='complete', objects=[obj])
                                                for name, obj in objects.items()]}]}
        input_raw = json.dumps(inventory).encode()
        (root / 'inventory.json').write_bytes(input_raw)
        def types(raw):
            return {f.name: str(f.type) for f in day.numeric.pq.read_metadata(io.BytesIO(raw)).schema.to_arrow_schema()}
        plan = dict(base_url='https://example.test/', inventory_input='inventory',
                    inputs={'inventory': {'path': 'inventory.json', 'sha256': day.storage.sha(input_raw)}},
                    required_types={k: v for k, v in types(txraw).items() if k in day.numeric.COLUMNS},
                    block_required_types=types(blocks),
                    limits=dict(max_requests=2100, max_total_bytes=2 * 1024 ** 3, max_response_bytes=32 * 1024 ** 2,
                                max_block_bytes=16 * 1024 ** 2, max_logical_bytes=8 * 1024 ** 3,
                                max_footer_bytes=4 * 1024 ** 2, max_projection_bytes=256 * 1024 ** 2, timeout_seconds=30))
        plan_raw = json.dumps(plan).encode()
        (root / 'plan.json').write_bytes(plan_raw)
        opened = []
        class Response(io.BytesIO):
            pass
        class Opener:
            def open(self, request, timeout):
                opened.append(request)
                name = request.full_url.rsplit('/', 1)[-1]
                raw = blocks if name == 'blocks' else txraw
                range_header = request.get_header('Range')
                assert request.get_header('If-match') == '"fixed"'
                headers = {'etag': '"fixed"'}
                if range_header:
                    begin, end = map(int, range_header.removeprefix('bytes=').split('-'))
                    headers['content-range'] = f'bytes {begin}-{end}/{len(raw)}'
                    body, status = raw[begin:end + 1], 206
                else:
                    body, status = raw, 200
                headers['content-length'] = str(len(body))
                response = Response(body)
                response.status, response.headers = status, headers
                return response
        args = argparse.Namespace(root=str(root), plan='plan.json', mode='source', date='2024-01-01',
                                  result=str(root / 'source-result.json'), max_requests=None, max_bytes=None)
        with patch.object(day.storage.urllib.request, 'build_opener', return_value=Opener()):
            result = day.execute(args)
        assert result['status'] == 'complete', result
        assert result['requests'] == 3 + len(old['ranges']) == len(opened)
        assert result['integrity']['rows'] == 7 and result['activity']['events'] == 3
        assert sum(meta['hashes'] for meta in result['transaction_hashes']) == 7
        digest = day.storage.read_blob(root / result['transaction_hashes'][0]['path'], result['transaction_hashes'][0])
        assert digest == b''.join(i.to_bytes(32, 'big') for i in range(7))
        previous_dir = root / 'previous'
        previous_dir.mkdir()
        first = result['integrity']['first_block']
        prefix = [[fixture.START // 10**9 - 1, 1, fixture.A, fixture.B],
                  [fixture.START // 10**9 - 1, 2, fixture.B, fixture.A]]
        previous = dict(status='complete', mode='context', date='2023-12-31', plan_sha256=day.storage.sha(plan_raw),
                        integrity={'last_block': [99, first[2], '0x' + '9' * 64, fixture.START - 10**9, 2]},
                        prefix=day.shards(root, previous_dir, 'prefix', prefix))
        previous['artifacts'] = day.artifact_manifest(root, previous_dir)
        previous_raw = json.dumps(previous).encode()
        (root / 'previous-result.json').write_bytes(previous_raw)
        args.mode, args.result = 'count', str(root / 'count-result.json')
        args.current_result, args.previous_result = 'source-result.json', 'previous-result.json'
        args.current_sha256 = day.storage.sha((root / args.current_result).read_bytes())
        args.previous_sha256 = day.storage.sha(previous_raw)
        counted = day.execute(args)
        assert counted['status'] == 'complete', counted
        assert counted['features']['cross_midnight_unique_occurrences'] > 0
        assert counted['counts'] and counted['requests'] == 0
        with __import__('pytest').raises(ValueError, match='hash mismatch'):
            day.generated_result(root, args.current_result, 'bad', day.storage.sha(plan_raw))
        with __import__('pytest').raises(ValueError, match='plan hash'):
            day.generated_result(root, args.current_result, args.current_sha256, 'bad')

"""One bounded pilot phase. No prices, labels, models, retries or implicit resumes."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import time
import urllib.parse

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


storage = module('pilot_storage_day', HERE / 'storage.py')
numeric = module('pilot_numeric_day', HERE / 'numeric.py')
PAIR_SHA = 'ff0f034a037b373f11191b5c19a4c0fe20fec33ac524dd31bdc1a1551dd4492e'


def within(root, path):
    path = (root / path).resolve()
    path.relative_to(root)
    return path


def verified_input(root, plan, name):
    reference = plan['inputs'][name]
    raw = within(root, reference['path']).read_bytes()
    if storage.sha(raw) != reference['sha256']:
        raise ValueError('input hash mismatch: ' + name)
    return raw


def validate_blocks(raw, required_types):
    schema = {field.name: str(field.type) for field in numeric.pq.read_metadata(io.BytesIO(raw)).schema.to_arrow_schema()}
    if any(schema.get(name) != dtype for name, dtype in required_types.items()):
        raise ValueError('block required schema changed')


def object_for(inventory, table, day):
    rows = [row for group in inventory['inventories'] for row in group['dates']
            if row['table'] == table and row['date'] == day]
    if len(rows) != 1 or rows[0]['status'] != 'complete' or len(rows[0]['objects']) != 1:
        raise ValueError('inventory object unavailable or ambiguous')
    return rows[0]['objects'][0]


def checked_response(body, receipt, obj, start=None, end=None):
    headers = receipt.get('response_headers', {})
    if body is None or receipt.get('error') or headers.get('etag') != obj['etag']:
        raise ValueError('unavailable body or changed object ETag')
    if start is None:
        if receipt['status'] != 200 or len(body) != obj['size']:
            raise ValueError('full object response mismatch')
    elif (receipt['status'] != 206 or len(body) != end - start + 1
          or headers.get('content-range') != f'bytes {start}-{end}/{obj["size"]}'):
        raise ValueError('conditional range status/size/content-range mismatch')
    return body


def shards(root, directory, name, rows):
    result = []
    for offset in range(0, len(rows), 10000):
        raw = b''.join((json.dumps(row, separators=(',', ':')) + '\n').encode()
                       for row in rows[offset:offset + 10000])
        path = directory / f'{name}-{offset // 10000:04d}.jsonl.zst'
        meta = storage.write_blob(path, raw)
        meta.update(path=str(path.relative_to(root)), rows=min(10000, len(rows) - offset))
        result.append(meta)
    return result


def read_shards(root, manifests):
    result = []
    for meta in manifests:
        raw = storage.read_blob(within(root, meta['path']), meta)
        rows = [json.loads(line) for line in raw.splitlines()]
        if len(rows) != meta['rows']:
            raise ValueError('shard row denominator changed')
        result.extend(rows)
    return result


def generated_result(root, path, expected_sha256=None, plan_sha256=None):
    raw_result = within(root, path).read_bytes()
    if expected_sha256 is not None and storage.sha(raw_result) != expected_sha256:
        raise ValueError('upstream result hash mismatch')
    value = json.loads(raw_result)
    if plan_sha256 is not None and value.get('plan_sha256') != plan_sha256:
        raise ValueError('upstream plan hash mismatch')
    if value['status'] != 'complete':
        raise ValueError('upstream phase unavailable')
    for item in value['artifacts']:
        raw = within(root, item['path']).read_bytes()
        if len(raw) != item['bytes'] or storage.sha(raw) != item['sha256']:
            raise ValueError('upstream artifact hash/size mismatch')
    return value


def artifact_manifest(root, directory):
    result = []
    for path in sorted(directory.rglob('*')):
        if path.is_file():
            raw = path.read_bytes()
            result.append(dict(path=str(path.relative_to(root)), bytes=len(raw), sha256=storage.sha(raw)))
    return result


def execute(args):
    root = Path(args.root).resolve()
    plan_path = within(root, args.plan)
    plan_raw = plan_path.read_bytes()
    plan = json.loads(plan_raw)
    date = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    start, end = int(date.timestamp()), int(date.timestamp()) + 86400
    directory = root / 'research/onchain-graph-2026-09-16/pilot/artifacts' / f'{args.mode}-{args.date}'
    directory.mkdir(parents=True, exist_ok=False)
    result = dict(mode=args.mode, date=args.date, status='unavailable', reason=None,
                  plan_sha256=storage.sha(plan_raw), requests=0, raw_bytes=0, denied=False,
                  events=[], prefix=[], counts=[], transaction_hashes=[], artifacts=[], timings={})
    capture = None
    began = time.monotonic()
    try:
        if args.mode == 'count':
            current = generated_result(root, args.current_result, args.current_sha256, result['plan_sha256'])
            previous = generated_result(root, args.previous_result, args.previous_sha256, result['plan_sha256'])
            if current['date'] != args.date or current['mode'] != 'source':
                raise ValueError('wrong current source day')
            prior_start = int(datetime.strptime(previous['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc).timestamp())
            if prior_start + 86400 != start or previous['mode'] not in {'context', 'source'}:
                raise ValueError('wrong preceding source day')
            numeric.linked(previous['integrity']['last_block'], current['integrity']['first_block'])
            events = read_shards(root, current['events'])
            prefix = read_shards(root, previous['prefix'])
            local, features, checks, timings = numeric.count_day(prefix, events, start, end)
            result.update(counts=shards(root, directory, 'local40', sorted(local.items())),
                          features=features, checks=checks, timings=timings,
                          source_result_sha256=storage.sha(within(root, args.current_result).read_bytes()),
                          previous_result_sha256=storage.sha(within(root, args.previous_result).read_bytes()))
        else:
            if args.mode == 'context':
                context = plan['context']
                old = json.loads(verified_input(root, plan, context['plan_input']))
                if old['day'] != args.date:
                    raise ValueError('wrong retained context day')
                blocks = numeric.prototype.raw_receipt(verified_input(root, plan, context['blocks_input']))
                footer = numeric.prototype.raw_receipt(verified_input(root, plan, context['footer_input']))
                validate_blocks(blocks, plan['block_required_types'])
                numeric.prototype.validate_plan(old, footer)
                if len(context['range_inputs']) != 117 or len(old['ranges']) != 117:
                    raise ValueError('context range denominator changed')
                benchmark = dict(ranges=117, receipt_json_bytes=0, raw_bytes=0,
                                 base64_theoretical_bytes=0, zstd_bytes=0, compression_seconds=0.0,
                                 roundtrip_verified=True, write_verify_seconds=0.0, blobs=[])
                retained = []
                for index, name in enumerate(context['range_inputs']):
                    raw_receipt = verified_input(root, plan, name)
                    receipt = json.loads(raw_receipt)
                    body = numeric.prototype.raw_receipt(raw_receipt)
                    span = old['ranges'][index]
                    checked_response(body, receipt, old['object'], span['start'], span['end'])
                    path = directory / f'baseline-range-{index:04d}.body.zst'
                    tick = time.monotonic()
                    meta = storage.write_blob(path, body)
                    benchmark['write_verify_seconds'] += time.monotonic() - tick
                    retained.append((path, meta))
                    benchmark['blobs'].append(dict(meta, path=str(path.relative_to(root))))
                    benchmark['receipt_json_bytes'] += len(raw_receipt)
                    benchmark['raw_bytes'] += len(body)
                    benchmark['base64_theoretical_bytes'] += meta['base64_theoretical_bytes']
                    benchmark['zstd_bytes'] += meta['stored_bytes']
                    benchmark['compression_seconds'] += meta['compression_seconds']
                benchmark['zstd_to_raw_ratio'] = benchmark['zstd_bytes'] / benchmark['raw_bytes'] if benchmark['raw_bytes'] else None
                benchmark['zstd_to_receipt_json_ratio'] = benchmark['zstd_bytes'] / benchmark['receipt_json_bytes']
                result['benchmark'] = benchmark
                projected = old
                read_range = lambda i: storage.read_blob(*retained[i])
            else:
                limits = dict(plan['limits'])
                limits['max_requests'] = min(limits['max_requests'], limits.get('max_day_requests', 291), 291)
                daily_bytes = (16 * 1024 ** 2 + 1 if args.mode == 'boundary' else 272 * 1024 ** 2)
                limits['max_total_bytes'] = min(limits['max_total_bytes'], limits.get('max_day_bytes', 272 * 1024 ** 2), daily_bytes)
                if args.max_requests is not None:
                    limits['max_requests'] = min(limits['max_requests'], args.max_requests)
                if args.max_bytes is not None:
                    limits['max_total_bytes'] = min(limits['max_total_bytes'], args.max_bytes)
                capture = storage.BinaryCapture(dict(limits, base_url=plan['base_url']), directory)
                inventory = json.loads(verified_input(root, plan, plan['inventory_input']))
                block_obj = object_for(inventory, 'blocks', args.date)
                if not 12 <= block_obj['size'] <= limits['max_block_bytes']:
                    raise ValueError('block object outside fixed bound')
                def fetch(obj, first=None, last=None):
                    url = plan['base_url'] + urllib.parse.quote(obj['key'], safe='/=')
                    headers = {'If-Match': obj['etag']}
                    if first is not None:
                        headers['Range'] = f'bytes={first}-{last}'
                    body, receipt = capture.get(url, headers)
                    return checked_response(body, receipt, obj, first, last), receipt
                blocks, _ = fetch(block_obj)
                validate_blocks(blocks, plan['block_required_types'])
                if args.mode == 'boundary':
                    rows = sorted(numeric.prototype.block_rows(blocks))
                    state = numeric.prototype.math.Integrity(rows, start * 10**9, end * 10**9)
                    result['integrity'] = dict(first_block=list(rows[0]), last_block=list(rows[-1]),
                                               blocks=len(rows), expected_rows=state.expected_rows,
                                               block_chain_admitted=True, transactions_checked=False)
                else:
                    obj = object_for(inventory, 'transactions', args.date)
                    if not 12 <= obj['size'] <= limits['max_logical_bytes']:
                        raise ValueError('transaction logical object outside fixed bound')
                    tail, _ = fetch(obj, obj['size'] - 8, obj['size'] - 1)
                    length = struct.unpack('<I', tail[:4])[0]
                    if tail[4:] != b'PAR1' or not 0 < length <= limits['max_footer_bytes'] or length + 12 > obj['size']:
                        raise ValueError('invalid bounded footer trailer')
                    footer, _ = fetch(obj, obj['size'] - length - 8, obj['size'] - 1)
                    if footer[-8:] != tail:
                        raise ValueError('footer trailer changed between conditional requests')
                    types = plan['required_types']
                    projected = numeric.projection(obj, footer, limits, types.get('transactions', types))
                    storage.atomic_json(directory / 'projection.json', projected)
                    retained = []
                    for span in projected['ranges']:
                        _, receipt = fetch(obj, span['start'], span['end'])
                        retained.append((directory / receipt['blob']['path'], receipt['blob']))
                    read_range = lambda i: storage.read_blob(*retained[i])
            if args.mode != 'boundary':
                tick = time.monotonic()
                def hash_sink(hashes):
                    for offset in range(0, len(hashes), 1_000_000):
                        part = hashes[offset:offset + 1_000_000]
                        if any(not isinstance(value, bytes) or len(value) != 32 for value in part):
                            raise ValueError('invalid transaction hash width')
                        path = directory / f'transaction-hashes-{offset // 1_000_000:04d}.bin.zst'
                        meta = storage.write_blob(path, b''.join(part))
                        meta.update(path=str(path.relative_to(root)), hashes=len(part))
                        result['transaction_hashes'].append(meta)
                events, integrity, activity = numeric.decode(projected, footer, blocks, read_range, start, end, hash_sink=hash_sink)
                result['timings']['decode_seconds'] = time.monotonic() - tick
                if args.mode == 'context' and (len(events) != 547332 or activity['pair_count_sha256'] != PAIR_SHA):
                    raise ValueError('retained forensic graph identity differs')
                result.update(integrity=integrity, activity=activity,
                              events=shards(root, directory, 'events', events),
                              prefix=shards(root, directory, 'prefix', [e for e in events if e[0] >= end - 3600]))
        result['status'] = 'complete'
    except Exception as exc:
        result.update(status='unavailable', reason=f'{type(exc).__name__}: {exc}', error_type=type(exc).__name__)
    finally:
        if capture is not None:
            result.update(requests=capture.count, raw_bytes=capture.total, denied=capture.denied)
        result['timings']['total_seconds'] = time.monotonic() - began
        result['artifacts'] = artifact_manifest(root, directory)
        storage.atomic_json(Path(args.result), result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--mode', required=True, choices=['context', 'boundary', 'source', 'count'])
    parser.add_argument('--date', required=True)
    parser.add_argument('--result', required=True)
    parser.add_argument('--max-requests', type=int)
    parser.add_argument('--max-bytes', type=int)
    parser.add_argument('--current-result')
    parser.add_argument('--previous-result')
    parser.add_argument('--current-sha256')
    parser.add_argument('--previous-sha256')
    args = parser.parse_args()
    if not Path(args.result).is_absolute():
        parser.error('--result must be absolute')
    if args.mode == 'count' and (not args.current_result or not args.previous_result or not args.current_sha256 or not args.previous_sha256):
        parser.error('count requires both --current-result/--previous-result and --current-sha256/--previous-sha256')
    value = execute(args)
    print(json.dumps({'status': value['status'], 'reason': value['reason']}))
    return 0  # Known phase unavailability is retained; the orchestrator completes remaining cells.


if __name__ == '__main__':
    raise SystemExit(main())

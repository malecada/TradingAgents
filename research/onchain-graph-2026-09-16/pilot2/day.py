"""Offline retained-byte adapter; frozen pilot mathematics remains unchanged."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time
import urllib.parse

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('pilot2_original_day', HERE.parent / 'pilot/day.py')
old = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(old)
storage, numeric = old.storage, old.numeric


def deny_network(event, args):
    if event.startswith(('socket.', 'http.client.', 'urllib.')):
        raise RuntimeError('offline numerical pilot prohibits network access')


def within(root, relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('non-relative or traversing evidence path')
    resolved = (root / path).resolve()
    resolved.relative_to(root.resolve())
    return resolved


def verified(root, reference):
    raw = within(root, reference['path']).read_bytes()
    if storage.sha(raw) != reference['sha256'] or ('bytes' in reference and len(raw) != reference['bytes']):
        raise ValueError('input hash/size mismatch')
    return raw


def retained_capture(root, plan, date, boundary=False):
    descriptor = plan['captures'][date]
    frozen_directory = Path(descriptor['directory'])
    directory = frozen_directory.resolve() if frozen_directory.is_absolute() else within(root, frozen_directory)
    manifest = json.loads(verified(root, descriptor['manifest']))
    state = manifest.get('result', manifest)
    if state['status'] != 'complete' or state['date'] != date:
        raise ValueError('capture unavailable or wrong date')
    members = {}
    for item in manifest['files']:
        if item['path'] in members:
            raise ValueError('duplicate capture manifest member')
        verified(directory, item)
        members[item['path']] = item

    def member(name):
        if name not in members:
            raise ValueError('capture member not sealed: ' + name)
        return verified(directory, members[name])

    inventory = json.loads(verified(root, plan['inputs'][plan['inventory_input']]))

    def read(number, obj, first=None, last=None):
        stem = f'request-{number:04d}'
        receipt = json.loads(member(stem + '.json'))
        intent = json.loads(member(stem + '-intent.json'))
        headers = {'If-Match': obj['etag']}
        if first is not None:
            headers['Range'] = f'bytes={first}-{last}'
        url = plan['base_url'] + urllib.parse.quote(obj['key'], safe='/=')
        if (receipt['request_number'] != number or receipt['url'] != url
                or receipt['request_headers'] != headers or intent['url'] != url
                or intent['request_headers'] != headers or intent['request_number'] != number):
            raise ValueError('retained request identity mismatch')
        blob = receipt['blob']
        if blob['path'] != stem + '.body.zst':
            raise ValueError('unexpected retained blob path')
        member(blob['path'])
        body = storage.read_blob(within(directory, blob['path']), blob)
        if len(body) != receipt['bytes'] or storage.sha(body) != receipt['sha256']:
            raise ValueError('receipt body hash/size mismatch')
        return old.checked_response(body, receipt, obj, first, last)

    block_obj = old.object_for(inventory, 'blocks', date)
    blocks = read(1, block_obj)
    old.validate_blocks(blocks, plan['block_required_types'])
    if boundary:
        return None, None, blocks, None
    obj = old.object_for(inventory, 'transactions', date)
    tail = read(2, obj, obj['size'] - 8, obj['size'] - 1)
    length = struct.unpack('<I', tail[:4])[0]
    if tail[4:] != b'PAR1' or not 0 < length <= plan['limits']['max_footer_bytes'] or length + 12 > obj['size']:
        raise ValueError('invalid footer trailer')
    footer = read(3, obj, obj['size'] - length - 8, obj['size'] - 1)
    if footer[-8:] != tail:
        raise ValueError('footer trailer mismatch')
    types = plan['required_types']
    projected = numeric.projection(obj, footer, plan['limits'], types.get('transactions', types))
    if json.loads(member('projection.json')) != projected:
        raise ValueError('retained projection differs from verified footer')
    expected = len(projected['ranges']) + 3
    receipts = {name for name in members if name.startswith('request-') and name.endswith('.json') and not name.endswith('-intent.json')}
    if receipts != {f'request-{n:04d}.json' for n in range(1, expected + 1)}:
        raise ValueError('retained request denominator mismatch')
    def read_range(index):
        span = projected['ranges'][index]
        return read(index + 4, obj, span['start'], span['end'])
    return projected, footer, blocks, read_range


def retained_context(root, plan, date):
    context = plan['context']
    get = lambda name: verified(root, plan['inputs'][name])
    projected = json.loads(get(context['plan_input']))
    if projected['day'] != date:
        raise ValueError('wrong retained context day')
    blocks = numeric.prototype.raw_receipt(get(context['blocks_input']))
    footer = numeric.prototype.raw_receipt(get(context['footer_input']))
    old.validate_blocks(blocks, plan['block_required_types'])
    numeric.prototype.validate_plan(projected, footer)
    if len(context['range_inputs']) != 117 or len(projected['ranges']) != 117:
        raise ValueError('context range denominator changed')
    def read_range(index):
        raw = get(context['range_inputs'][index])
        span = projected['ranges'][index]
        return old.checked_response(numeric.prototype.raw_receipt(raw), json.loads(raw),
                                    projected['object'], span['start'], span['end'])
    return projected, footer, blocks, read_range


def source_result(root, destination, path, digest, plan_digest):
    if not digest:
        raise ValueError('upstream result hash required')
    within(root, path).relative_to(destination)
    result = json.loads(verified(root, {'path': path, 'sha256': digest}))
    sealed = set()
    for item in result['artifacts']:
        within(root, item['path']).relative_to(destination)
        if item['path'] in sealed:
            raise ValueError('duplicate upstream artifact')
        verified(root, item)
        sealed.add(item['path'])
    for group in ('events', 'prefix', 'transaction_hashes'):
        for item in result.get(group, []):
            if item['path'] not in sealed:
                raise ValueError('unsealed upstream shard')
    if result.get('plan_sha256') != plan_digest or result['status'] != 'complete':
        raise ValueError('upstream plan mismatch or phase unavailable')
    return result


def execute(args):
    # Permanent process hook also protects imports/callees during every phase.
    sys.addaudithook(deny_network)
    root = Path(args.root).resolve()
    plan_raw = within(root, args.plan).read_bytes()
    plan = json.loads(plan_raw)
    date = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    start, end = int(date.timestamp()), int(date.timestamp()) + 86400
    destination = within(root, 'research/onchain-graph-2026-09-16/pilot2/artifacts')
    directory = destination / f'{args.mode}-{args.date}'
    result_path = Path(args.result).resolve()
    result_path.relative_to(root)
    if result_path.exists():
        raise FileExistsError('result already exists')
    directory.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    result = dict(mode=args.mode, date=args.date, status='unavailable', reason=None,
                  plan_sha256=storage.sha(plan_raw), requests=0, raw_bytes=0, denied=False,
                  events=[], prefix=[], counts=[], transaction_hashes=[], artifacts=[], timings={},
                  source_policy='retained bytes only; network denied')
    try:
        if args.mode == 'count':
            current = source_result(root, destination, args.current_result, args.current_sha256, result['plan_sha256'])
            previous = source_result(root, destination, args.previous_result, args.previous_sha256, result['plan_sha256'])
            prior = datetime.strptime(previous['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
            if current['date'] != args.date or current['mode'] != 'source' or int(prior.timestamp()) + 86400 != start or previous['mode'] not in {'context', 'source'}:
                raise ValueError('wrong source day or mode')
            numeric.linked(previous['integrity']['last_block'], current['integrity']['first_block'])
            local, features, checks, timings = numeric.count_day(old.read_shards(root, previous['prefix']), old.read_shards(root, current['events']), start, end)
            result.update(counts=old.shards(root, directory, 'local40', sorted(local.items())), features=features,
                          checks=checks, timings=timings, source_result_sha256=args.current_sha256,
                          previous_result_sha256=args.previous_sha256)
        else:
            projected, footer, blocks, read_range = (retained_context(root, plan, args.date) if args.mode == 'context'
                else retained_capture(root, plan, args.date, boundary=args.mode == 'boundary'))
            if args.mode == 'boundary':
                rows = sorted(numeric.prototype.block_rows(blocks))
                state = numeric.prototype.math.Integrity(rows, start * 10**9, end * 10**9)
                result['integrity'] = dict(first_block=list(rows[0]), last_block=list(rows[-1]), blocks=len(rows),
                                          expected_rows=state.expected_rows, block_chain_admitted=True, transactions_checked=False)
            else:
                def hash_sink(hashes):
                    for offset in range(0, len(hashes), 1_000_000):
                        part = hashes[offset:offset + 1_000_000]
                        if any(not isinstance(value, bytes) or len(value) != 32 for value in part):
                            raise ValueError('invalid transaction hash width')
                        path = directory / f'transaction-hashes-{offset // 1_000_000:04d}.bin.zst'
                        meta = storage.write_blob(path, b''.join(part))
                        meta.update(path=str(path.relative_to(root)), hashes=len(part))
                        result['transaction_hashes'].append(meta)
                tick = time.monotonic()
                events, integrity, activity = numeric.decode(projected, footer, blocks, read_range, start, end, hash_sink=hash_sink)
                result['timings']['decode_seconds'] = time.monotonic() - tick
                if args.mode == 'context' and (len(events) != 547332 or activity['pair_count_sha256'] != old.PAIR_SHA):
                    raise ValueError('retained forensic graph identity differs')
                result.update(integrity=integrity, activity=activity, events=old.shards(root, directory, 'events', events),
                              prefix=old.shards(root, directory, 'prefix', [e for e in events if e[0] >= end - 3600]))
        result['status'] = 'complete'
    except Exception as exc:
        result.update(reason=f'{type(exc).__name__}: {exc}', error_type=type(exc).__name__)
    finally:
        result['timings']['total_seconds'] = time.monotonic() - began
        result['artifacts'] = old.artifact_manifest(root, directory)
        storage.atomic_json(result_path, result)
    return result


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'plan', 'date', 'result'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--mode', required=True, choices=['context', 'boundary', 'source', 'count'])
    for name in ('current-result', 'previous-result', 'current-sha256', 'previous-sha256'):
        parser.add_argument('--' + name)
    args = parser.parse_args()
    if not Path(args.result).is_absolute():
        parser.error('--result must be absolute')
    if args.mode == 'count' and not all((args.current_result, args.previous_result, args.current_sha256, args.previous_sha256)):
        parser.error('count requires both source result paths and hashes')
    value = execute(args)
    print(json.dumps({'status': value['status'], 'reason': value['reason']}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

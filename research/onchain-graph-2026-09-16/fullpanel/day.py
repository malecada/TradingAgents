"""One offline numerical panel day, preserving prefixes and declared scratch."""
import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


old = load('fullpanel_original_day', HERE.parent / 'pilot/day.py')
numeric, storage = old.numeric, old.storage


def material(root, plan, date, boundary=False):
    return load('fullpanel_source_for_day', HERE / 'source.py').material(root, plan, date, boundary=boundary)


def deny_network(event, args):
    if event.startswith(('socket.', 'http.client.', 'urllib.')):
        raise RuntimeError('offline panel prohibits network access')


def within(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('evidence path must be relative and confined')
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    return path


def verified_json(root, reference):
    raw = within(root, reference['path']).read_bytes()
    if storage.sha(raw) != reference['sha256']:
        raise ValueError('referenced JSON hash mismatch')
    return json.loads(raw)


def read_rows(root, manifests):
    rows = []
    for item in manifests:
        raw = storage.read_blob(within(root, item['path']), item)
        part = [json.loads(line) for line in raw.splitlines()]
        if len(part) != item['rows']:
            raise ValueError('shard row denominator mismatch')
        rows.extend(part)
    return rows


def previous_day(root, args, date):
    path, digest = getattr(args, 'previous', None), getattr(args, 'previous_sha256', None)
    if not path:
        if digest:
            raise ValueError('previous hash without output')
        return None
    if not digest:
        raise ValueError('previous output hash required')
    value = verified_json(root, dict(path=path, sha256=digest))
    expected = (date - timedelta(days=1)).strftime('%Y-%m-%d')
    if value['date'] != expected or value['source']['date'] != expected or value['source']['status'] != 'complete':
        raise ValueError('previous day/source status mismatch')
    report = verified_json(root, value['audit'])
    if report.get('date') != expected or report.get('passed') is not True or value.get('independent') != report:
        raise ValueError('previous independent check unavailable or inconsistent')
    prefix = value['source']['prefix']
    rows = read_rows(root, prefix)
    start = int(date.timestamp())
    if any(len(row) != 4 or not start-3600 <= row[0] < start for row in rows):
        raise ValueError('previous prefix outside inclusive preceding hour')
    return dict(date=expected, integrity=value['source']['integrity'], prefix=prefix,
                audit=value['audit']), rows


def _hash_blob(root, directory, raw, index):
    if len(raw) % 32 or len(raw) > 32_000_000:
        raise ValueError('invalid bounded transaction hash payload')
    path = directory / f'transaction-hashes-{index:04d}.bin.zst'
    metadata = storage.write_blob(path, raw)
    metadata.update(path=str(path.relative_to(root)), hashes=len(raw)//32)
    return metadata


def execute(args):
    sys.addaudithook(deny_network)
    root = Path(args.root).resolve()
    plan_raw = within(root, args.plan).read_bytes()
    plan = json.loads(plan_raw)
    date = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    start, end = int(date.timestamp()), int(date.timestamp())+86400
    if args.date not in plan['dates']:
        raise ValueError('day outside frozen panel')
    phase_path = within(root, args.phase)
    scratch = within(root, f'research/onchain-graph-2026-09-16/fullpanel/artifacts/scratch/{args.date}')
    phase_path.relative_to(scratch)
    if phase_path.exists():
        raise FileExistsError('phase already exists')
    source_dir = scratch / 'source'
    source_dir.mkdir(parents=True, exist_ok=False)
    prefix_dir = within(root, f'research/onchain-graph-2026-09-16/fullpanel/artifacts/prefixes/{args.date}')
    prefix_dir.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    source = dict(date=args.date, status='unavailable', reason=None, events=[], prefix=[], transaction_hashes=[],
                  expected_rows=plan['expected_rows'][args.date], timings={})
    count = dict(date=args.date, status='unavailable', reason=None, counts=[], features=None, checks=None, timings={})
    phase = dict(date=args.date, plan_sha256=storage.sha(plan_raw), source=source, count=count,
                 previous=None, following=None, previous_output_sha256=getattr(args, 'previous_sha256', None),
                 source_reused=False, count_reused=False, requests=0)
    try:
        reuse = plan.get('reuse', {}).get(args.date, {})
        if reuse.get('source'):
            retained = verified_json(root, reuse['source'])
            if retained['date'] != args.date or retained['status'] != 'complete' or retained['mode'] not in {'source', 'context'}:
                raise ValueError('reused source day/mode/status mismatch')
            events = read_rows(root, retained['events'])
            retained_prefix = read_rows(root, retained['prefix'])
            if retained_prefix != [list(e) for e in events if e[0] >= end-3600]:
                raise ValueError('reused source prefix differs from events')
            for index, item in enumerate(retained['transaction_hashes']):
                raw = storage.read_blob(within(root, item['path']), item)
                if len(raw) != item['hashes'] * 32:
                    raise ValueError('reused transaction hash denominator mismatch')
                source['transaction_hashes'].append(_hash_blob(root, source_dir, raw, index))
            integrity, activity = retained['integrity'], retained['activity']
            phase['source_reused'] = True
            source['reused_result_sha256'] = reuse['source']['sha256']
        else:
            projection, footer, blocks, read_range = material(root, plan, args.date)
            def sink(hashes):
                for offset in range(0, len(hashes), 1_000_000):
                    part = hashes[offset:offset+1_000_000]
                    if any(not isinstance(v, bytes) or len(v) != 32 for v in part):
                        raise ValueError('invalid transaction hash width')
                    source['transaction_hashes'].append(_hash_blob(root, source_dir, b''.join(part), len(source['transaction_hashes'])))
            tick = time.monotonic()
            events, integrity, activity = numeric.decode(projection, footer, blocks, read_range, start, end, hash_sink=sink)
            source['timings']['decode_seconds'] = time.monotonic()-tick
        # Match the old separate source/count phases' JSON-shard row type.
        events = [list(event) for event in events]
        if (integrity.get('admitted') is not True or integrity['expected_rows'] != source['expected_rows']
                or sum(m['hashes'] for m in source['transaction_hashes']) != source['expected_rows']):
            raise ValueError('source transaction population mismatch')
        source.update(integrity=integrity, activity=activity, events=old.shards(root, source_dir, 'events', events),
                      prefix=old.shards(root, prefix_dir, 'prefix', [e for e in events if e[0] >= end-3600]), status='complete')
        prior = previous_day(root, args, date)
        if prior is not None:
            phase['previous'], prefix = prior
            numeric.linked(phase['previous']['integrity']['last_block'], integrity['first_block'])
        else:
            prefix = []
            if args.date != plan['dates'][0]:
                raise ValueError('interior day lacks checked previous output')
        if args.date != plan['dates'][-1]:
            next_day = (date+timedelta(days=1)).strftime('%Y-%m-%d')
            _, _, blocks, _ = material(root, plan, next_day, boundary=True)
            rows = sorted(numeric.prototype.block_rows(blocks))
            state = numeric.prototype.math.Integrity(rows, end*10**9, (end+86400)*10**9)
            following = dict(first_block=list(rows[0]), last_block=list(rows[-1]), blocks=len(rows),
                             expected_rows=state.expected_rows, block_chain_admitted=True, transactions_checked=False)
            numeric.linked(integrity['last_block'], following['first_block'])
            phase['following'] = dict(date=next_day, integrity=following)
        if prior is None or phase['following'] is None:
            count['reason'] = 'registered panel edge lacks preceding or following boundary'
        else:
            count_dir = scratch / 'count'
            count_dir.mkdir(exist_ok=False)
            if reuse.get('count'):
                retained = verified_json(root, reuse['count'])
                old_previous = plan.get('reuse', {}).get(phase['previous']['date'], {}).get('source', {})
                if (retained['date'] != args.date or retained['mode'] != 'count' or retained['status'] != 'complete'
                        or retained['source_result_sha256'] != reuse['source']['sha256']
                        or retained['previous_result_sha256'] != old_previous.get('sha256')):
                    raise ValueError('reused count source lineage mismatch')
                local_rows = read_rows(root, retained['counts'])
                features, checks = retained['features'], retained['checks']
                count['reused_result_sha256'] = reuse['count']['sha256']
                phase['count_reused'] = True
            else:
                local, features, checks, timings = numeric.count_day(prefix, events, start, end)
                local_rows = sorted(local.items())
                count['timings'] = timings
            count.update(status='complete', counts=old.shards(root, count_dir, 'local40', local_rows), features=features, checks=checks)
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
        if source['status'] != 'complete':
            source['reason'] = error
        count.update(status='unavailable', reason=error)
        phase['error_type'] = type(exc).__name__
    finally:
        phase['total_seconds'] = time.monotonic()-began
        source['artifacts'] = old.artifact_manifest(root, source_dir)+old.artifact_manifest(root, prefix_dir)
        storage.atomic_json(phase_path, phase)
    return phase


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'plan', 'date', 'phase'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--previous')
    parser.add_argument('--previous-sha256')
    args = parser.parse_args()
    if bool(args.previous) != bool(args.previous_sha256):
        parser.error('--previous and --previous-sha256 are required together')
    if not Path(args.root).is_absolute():
        parser.error('--root must be absolute')
    result = execute(args)
    print(json.dumps(dict(date=result['date'], source=result['source']['status'], count=result['count']['status'])))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

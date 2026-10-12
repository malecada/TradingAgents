"""Read-only joins for existing fixed39 local batch commitments, never authority."""
from pathlib import Path
import datetime
import hashlib
import json
import math
import os
import stat
import struct
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
STORE = ROOT / ('research_artifacts/onchain_representations/'
    'ada9fbd6764c8dc113bf837ff9cc71296dd9c09e6af2a9da4d7a841a2e91329f/'
    'eth-paper-real-data-end-to-end-resource-20261012-39/compact/'
    'mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba')
HEADER = struct.Struct('>8sIQQ32s32s')
RECORD = struct.Struct('>Q32sdIB')
ORIGIN = struct.Struct('>BQ')


def sha(body):
    return hashlib.sha256(body).hexdigest()


def read(path, limit):
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_size <= limit
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        body = os.read(fd, limit + 1)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    assert before == after == path.lstat() and len(body) == before.st_size
    return body


def observe(prior_name, output_name):
    assert Path(prior_name).name == prior_name and Path(output_name).name == output_name
    prior_raw = read(HERE / prior_name, 1024**2)
    prior = json.loads(prior_raw)
    stop = prior['hash_joined_local_completed_pairs']
    assert stop % 4096 == 0
    previous = prior['new_batches'][-1]
    result, sources, retained = [], [], []
    for index in range(stop // 4096, stop // 4096 + 8):
        stem = STORE / 'matching' / f'{index:08d}'
        if not stem.with_suffix('.prefix.json').exists():
            break
        bodies = {}
        for key in ('pending.json', 'records.bin', 'complete.json', 'prefix.json'):
            path = Path(str(stem) + '.' + key)
            body = read(path, 256*1024)
            bodies[key] = body
            retained.append((path, body))
            sources.append({'path':str(path.relative_to(ROOT)), 'bytes':len(body), 'sha256':sha(body)})
        p, c, x = (json.loads(bodies[k]) for k in ('pending.json', 'complete.json', 'prefix.json'))
        records = bodies['records.bin']
        assert p['schema'] == 3 and p['kind'] == 'engineering_pending'
        assert p['disposition'] == 'attempted_unknown_without_complete'
        assert p['start'] == stop and p['stop'] == stop + 4096
        assert p['workload_sha256'] == '21caf839b2b526ca0c270e23eea4247c1c73853bc666b2922141ebde1c203c5f'
        assert c['kind'] == 'engineering_complete' and c['schema'] == 3
        assert c['pending_sha256'] == sha(bodies['pending.json'])
        assert c['payload_sha256'] == sha(records) and c['payload_bytes'] == len(records)
        assert c['record_bytes'] == RECORD.size and len(records) == HEADER.size + 4096*RECORD.size
        assert HEADER.unpack_from(records) == (b'MCMBAT03', RECORD.size, stop, stop+4096,
            bytes.fromhex(c['pending_sha256']), bytes.fromhex(c['purposes_sha256']))
        purposes = hashlib.sha256()
        for ordinal, purpose, score, iterations, status in RECORD.iter_unpack(records[HEADER.size:]):
            assert ordinal == stop
            assert math.isfinite(score) and 0 <= score <= 1 and status in (0, 1)
            purposes.update(purpose)
            stop += 1
        assert purposes.hexdigest() == c['purposes_sha256']
        assert x['batch'] == index and x['start'] == p['start'] and x['stop'] == stop
        assert x['contract_sha256'] == '19a0c30e0001e706e00ccfe1981ad0e09f21decea858114f73b313fdb704d648'
        assert x['score_sha256'] == [sha(bodies[k]) for k in ('pending.json','records.bin','complete.json')]
        path = STORE / 'stream' / 'numeric-batches' / f'{index:012d}.json'
        body = read(path, 65536)
        summary = json.loads(body)
        retained.append((path, body))
        sources.append({'path':str(path.relative_to(ROOT)), 'bytes':len(body), 'sha256':sha(body)})
        assert sha(body) == x['summary_sha256']
        assert summary['batch'] == index and summary['start'] == p['start'] and summary['stop'] == stop
        path = STORE / 'stream' / 'numeric-origins.bin'
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            a = os.fstat(fd)
            origin = os.pread(fd, 9*4096, 9*p['start'])
            again = os.pread(fd, 9*4096, 9*p['start'])
            b = os.fstat(fd)
            assert (a.st_dev,a.st_ino) == (b.st_dev,b.st_ino) == (path.lstat().st_dev,path.lstat().st_ino)
            assert stat.S_ISREG(a.st_mode) and a.st_size >= 9*stop and b.st_size >= 9*stop
        finally:
            os.close(fd)
        assert origin == again and sha(origin) == x['origin_sha256'] == summary['origin_sha256']
        modes = [0, 0]
        for offset, (mode, owner) in enumerate(ORIGIN.iter_unpack(origin)):
            assert mode in (0, 1)
            ordinal = p['start'] + offset
            assert (owner == ordinal if mode == 0 else 0 <= owner < ordinal)
            modes[mode] += 1
        assert modes == [summary['computed'], summary['reused']]
        phases = summary['phase_totals']['phases']
        modified = Path(str(stem) + '.prefix.json').stat().st_mtime_ns
        span = (modified - previous['prefix_modified_ns']) / 1e9
        item = {'batch':index,'start':p['start'],'stop':stop,'computed':modes[0],'reused':modes[1],
            'numeric_call_elapsed_seconds':summary['elapsed_seconds'],'prefix_modified_ns':modified,
            'cumulative_phases':phases,'cumulative_counters':summary['counters'],
            'phase_deltas':{k:{q:v[q]-previous['cumulative_phases'][k][q] for q in v}
                for k,v in phases.items() if k in previous['cumulative_phases']},
            'publication_span_seconds':span,'publication_pairs_per_second':4096/span}
        result.append(item)
        previous = item
    assert result, 'No newly completed local prefix'
    for path, body in retained:
        assert read(path, 256*1024) == body
    value = {'kind':'read-only-live-batch-prefix-increment',
        'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'root_session':86263,
        'observer_sha256':sha(Path(__file__).read_bytes()),'prior_observation_sha256':sha(prior_raw),
        'previous_hash_joined_pairs':prior['hash_joined_local_completed_pairs'],'new_batches':result,
        'hash_joined_local_completed_pairs':stop,'sources':sources,
        'qualification':'Existing local commitments, bounded exact binary/purpose/origin checks and unchanged rereads only. Active origin file may append beyond the observed slices. No new authority, independent numerical reference comparison, external recovery, restart eligibility, whole graph, training or capacity. Publication mtime spans are proxies; phase rows are exclusive, callback timers inclusive.'}
    with (HERE / output_name).open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n')
    print(json.dumps({'output':output_name,'pairs':stop,'new_batches':len(result),
        'rates':[x['publication_pairs_per_second'] for x in result]}))


if __name__ == '__main__':
    observe(*sys.argv[1:])

"""Authenticate the five unused weekly graph inputs; never launch or read raws."""
import datetime
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
STUDY = ROOT / 'research/onchain-paper-replication-2026-09-24'
CASES = STUDY / 'full_sources/real-data-end-to-end-pilot-preparation01-2026-10-05/GRAPH_STAGE_CASES_DRAFT01.json'
IDENTITIES = tuple('eth-paper-real-pilot-graph-' + date + '-20261005-01'
                   for date in ('20220509', '20220516', '20220523', '20220530', '20220606'))


def compact(path, expected):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 4 * 1024**2:
        raise ValueError('compact input path/type/size differs')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('compact input hash differs: ' + str(path))
    return json.loads(raw)


def main():
    cases = json.loads(CASES.read_bytes())['graph_cases'][1:]
    if tuple(c['identity'] for c in cases) != IDENTITIES:
        raise ValueError('exact five unused identities differ')
    results = []
    for case in cases:
        name = case['identity']
        for namespace in (ROOT / 'research_runs' / name,
                          ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/runs' / name,
                          ROOT / 'research_artifacts/onchain-paper-replication-2026-09-24/sources' / name):
            if namespace.exists() or namespace.is_symlink():
                raise FileExistsError('unused graph identity is already reserved: ' + name)
        for spec in case['inputs'].values():
            compact(ROOT / spec['path'], spec['sha256'])
        spec = case['inputs']['weekly_source']
        weekly = compact(ROOT / spec['path'], spec['sha256'])
        if len(weekly['members']) != weekly['expected_members'] or weekly['expected_members'] != 7:
            raise ValueError('whole seven-day source cardinality differs')
        daily = []
        for member in weekly['members']:
            path = Path(member['path'])
            path.relative_to(ROOT)
            mapping = compact(path, member['sha256'])
            segments = []
            for span in mapping['spans']:
                raw_path = Path(span['path'])
                info = raw_path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_size != span['stored_bytes']:
                    raise ValueError('original compressed extent type/size differs')
                segments.append({'path': str(raw_path), 'bytes': info.st_size,
                    'device': info.st_dev, 'inode': info.st_ino,
                    'mtime_ns': info.st_mtime_ns, 'ctime_ns': info.st_ctime_ns,
                    'expected_stored_sha256': span['stored_sha256']})
            daily.append({'mapping_path': str(path.relative_to(ROOT)),
                'mapping_sha256': member['sha256'], 'expected_rows': member['expected_rows'],
                'object_logical_bytes': mapping['size'], 'segments': segments})
        if sum(d['expected_rows'] for d in daily) != weekly['expected_rows']:
            raise ValueError('weekly/daily declared rows differ')
        results.append({'identity': name, 'parent': case['parent'], 'week': case['week'],
            'inputs': case['inputs'], 'cells': case['cells'], 'outputs': case['outputs'],
            'expected_rows': weekly['expected_rows'], 'daily_members': daily,
            'largest_projected_parquet_bytes': max(d['object_logical_bytes'] for d in daily),
            'graph_nodes': None, 'graph_edges': None, 'run_started': False})
    value = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'kind': 'actual-five-unused-weekly-input-metadata',
        'case_source_sha256': hashlib.sha256(CASES.read_bytes()).hexdigest(), 'cases': results,
        'qualification': 'Original compressed bodies were statted, not read or rehashed. Exact stored hashes remain worker-enforced. No claim, numerical import, empirical outcome or capacity observation. Source integration, registration/entry review, actual previous cleanup and fresh resource checks remain mandatory before any next graph.'}
    with (HERE / 'RAW_EXTENTS01.json').open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({'unused_cases': len(results), 'daily_members': sum(len(c['daily_members']) for c in results),
        'compressed_extents': sum(len(d['segments']) for c in results for d in c['daily_members']),
        'declared_rows': sum(c['expected_rows'] for c in results), 'run_started': False}))


if __name__ == '__main__':
    main()

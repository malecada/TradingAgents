"""Read-only independent verification of the terminal graph pilot's saved arrays.

No production graph loader, validator, hash or feature producer is imported.
Raw transaction/exclusion semantics are not independently re-audited here.
"""
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
NAME = 'eth-paper-graph-resource-20260930-05'
SOURCE = ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME
RUN = ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME
LEDGER = ROOT/'research_runs'/NAME
BLOCK = 65536


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def streamed_identity(metadata, arrays):
    """Serialize the declared graph fields independently using standard JSON."""
    h = hashlib.sha256()
    values = dict(metadata, **arrays)
    h.update(b'{')
    for i, key in enumerate(sorted(values)):
        if i:
            h.update(b',')
        h.update(encode(key) + b':')
        value = values[key]
        if isinstance(value, np.ndarray):
            h.update(b'[')
            # Each row/scalar is independently encoded; never materialize a
            # complete array or use the production graph serialization helper.
            for j, item in enumerate(value):
                if j:
                    h.update(b',')
                h.update(encode(item.tolist()))
            h.update(b']')
        else:
            h.update(encode(value))
    h.update(b'}')
    return h.hexdigest()


def main():
    started = time.monotonic()
    # Exclusive reservation: never overwrite an attempted verification.
    with (HERE/'started.json').open('x') as stream:
        json.dump({'pid': os.getpid(), 'source_claim': NAME,
                   'script_sha256': file_hash(Path(__file__))}, stream)
        stream.flush(); os.fsync(stream.fileno())
    terminal = read(LEDGER/'complete.json')
    observer = read(RUN/'observer.json')
    guard = read(RUN/'guard/final.json')
    claim_hash = file_hash(LEDGER/'claim.json')
    claim = read(LEDGER/'claim.json')
    inputs = claim['experiment']['inputs']
    compact_bindings = {key: value for key, value in inputs.items()
                        if key in {'graph_plan','graph_config'} or key.startswith(('source_','mapping_'))}
    for entry in compact_bindings.values():
        assert file_hash(ROOT/entry['path']) == entry['sha256']
    assert terminal['claim_sha256'] == claim_hash
    assert observer['terminal_sha256'] == file_hash(LEDGER/'complete.json')
    assert observer['evidence_sha256']['guard/final.json'] == file_hash(RUN/'guard/final.json')
    assert guard['phase'] == 'complete' and guard['child_exit_code'] == 0 and guard['cleanup_verified']
    assert observer['all_cells_complete'] and observer['cgroup_empty']
    assert not Path(guard['cgroup']).exists()
    assert len(terminal['cells']) == terminal['cell_count'] == 8
    assert all(c['status'] == 'complete' for c in terminal['cells'])
    cell, = [c for c in terminal['cells'] if c['id'] == 'graph-2023-06-05']
    manifest_path = ROOT/cell['manifest_path']
    assert file_hash(manifest_path) == cell['manifest_sha256']
    manifest = read(manifest_path)
    coverage_path = ROOT/cell['coverage_path']
    assert file_hash(coverage_path) == cell['coverage_sha256']
    coverage = read(coverage_path)
    assert coverage['plan_sha256'] == inputs['graph_plan']['sha256']
    assert coverage['claim_sha256'] == claim_hash
    assert coverage['graph_manifest_sha256'] == cell['manifest_sha256']
    meta = manifest['metadata']
    assert meta['graph_config_hash'] == coverage['graph_config_hash']
    config = read(ROOT/'research/onchain-paper-replication-2026-09-24/config/graph.json')
    assert hashlib.sha256(encode(config)).hexdigest() == meta['graph_config_hash']
    assert meta['start_utc'] == coverage['week'] == '2023-06-05T00:00:00Z'
    assert meta['end_utc'] == coverage['end_utc'] == '2023-06-12T00:00:00Z'
    assert meta['available_at'] == '2023-06-13T00:00:00Z' and meta['asset'] == 'ETH'
    members = coverage['members']
    assert len(members) == 7
    plan = read(ROOT/inputs['graph_plan']['path'])
    assert plan['source_inputs'] == [m['source_input'] for m in members]
    assert plan['coverage'] == [[meta['start_utc'],meta['end_utc']]]
    assert sorted(m['sha256'] for m in members) == meta['source_hashes'] == cell['source_hashes']
    previous = meta['start_utc']
    for i, m in enumerate(members):
        assert m['start_utc'] == previous and m['start_utc'] < m['end_utc']
        previous = m['end_utc']
        daily = read(SOURCE/f'source-{i:06d}.json')
        assert daily in terminal['cells'] and daily['status'] == 'complete'
        assert daily['rows'] == m['expected_rows']
        assert daily['manifest_sha256'] == m['source_manifest_sha256']
        assert daily['input'] == m['source_input']
        assert inputs[m['source_input']]['sha256'] == m['source_manifest_sha256']
        assert inputs[f'mapping_{i:02d}_00']['sha256'] == m['sha256']
        wrapper = read(ROOT/inputs[m['source_input']]['path'])
        assert wrapper['status'] == 'complete' and wrapper['expected_members'] == 1
        assert wrapper['expected_rows'] == m['expected_rows']
        member, = wrapper['members']
        for key in ('start_utc','end_utc','expected_rows','sha256'):
            assert member[key] == m[key]
    assert previous == meta['end_utc']
    assert sum(m['expected_rows'] for m in members) == meta['raw_count'] == cell['raw_count'] == 7684076
    assert meta['admitted_count'] == cell['admitted_count']
    assert meta['exclusion_counts'] == cell['exclusion_counts']
    assert meta['admitted_count'] + sum(meta['exclusion_counts'].values()) == meta['raw_count']
    arrays = {}
    assert set(manifest['arrays']) == {'node_ids','node_features','edge_index','edge_features','edge_aggregates'}
    assert {p.name for p in manifest_path.parent.iterdir()} == {
        name+'.npy' for name in manifest['arrays']} | {'manifest.json','coverage.json'}
    for name, entry in manifest['arrays'].items():
        assert entry['path'] == name+'.npy'
        p = manifest_path.parent/entry['path']
        assert not p.is_symlink() and p.stat().st_size == entry['bytes']
        assert file_hash(p) == entry['sha256']
        arrays[name] = np.load(p, mmap_mode='r', allow_pickle=False)
    nodes, edges, raw = arrays['node_ids'], arrays['edge_index'], arrays['edge_aggregates']
    n = len(nodes); e = edges.shape[1]
    assert nodes.ndim == 1 and nodes.dtype.kind == 'U'
    assert edges.shape == (2,e) and edges.dtype == np.dtype('int64')
    assert arrays['node_features'].shape == (n,4)
    assert raw.shape == arrays['edge_features'].shape == (e,2)
    for name in ('node_features','edge_features','edge_aggregates'):
        assert arrays[name].dtype == np.dtype('float64')
    for start in range(0,n,BLOCK):
        ids = nodes[start:min(n,start+BLOCK+1)]
        assert np.all(ids != '') and np.all(ids[1:] > ids[:-1])
    count_sum = 0
    for start in range(0,e,BLOCK):
        stop = min(e,start+BLOCK)
        ends = edges[:,start:min(e,stop+1)]
        assert np.all((ends >= 0) & (ends < n))
        assert np.all((ends[0,1:] > ends[0,:-1]) |
                      ((ends[0,1:] == ends[0,:-1]) & (ends[1,1:] > ends[1,:-1])))
        values = raw[start:stop]
        assert np.isfinite(values).all() and np.all(values > 0)
        assert np.all(values[:,0] == np.floor(values[:,0]))
        count_sum += sum(map(int,values[:,0]))
        observed = arrays['edge_features'][start:stop]
        assert np.isfinite(observed).all() and np.all(observed >= 0)
        assert np.allclose(np.log1p(values), observed,rtol=1e-12,atol=1e-12)
    assert count_sum == meta['admitted_count']
    errors = {}
    # Count/value aggregation via independent bincount rather than producer loop.
    for column, direction, attribute in ((0,1,0),(1,0,0),(2,1,1),(3,0,1)):
        totals = np.bincount(edges[direction], weights=raw[:,attribute], minlength=n)
        expected = np.log1p(totals)
        observed = arrays['node_features'][:,column]
        assert np.isfinite(observed).all() and np.all(observed >= 0)
        errors[str(column)] = float(np.max(np.abs(expected-observed)))
        assert np.allclose(expected, observed, rtol=1e-12,atol=1e-12)
    identity = streamed_identity(meta, arrays)
    assert identity == manifest['graph_hash']
    result = {'status':'complete','source_claim':NAME,'claim_sha256':claim_hash,
              'terminal_sha256':file_hash(LEDGER/'complete.json'),
              'graph_manifest_sha256':cell['manifest_sha256'],'graph_hash':identity,
              'nodes':n,'directed_edges':e,'raw_rows':meta['raw_count'],
              'admitted_transactions':count_sum,'array_bytes':sum(x['bytes'] for x in manifest['arrays'].values()),
              'node_feature_max_absolute_errors':errors,'elapsed_seconds':time.monotonic()-started,
              'qualification':'Independent saved-array identity, structure and aggregate conservation verification. Source/exclusion counts reconcile producer receipts; raw transaction uniqueness, raw values and exclusion classification were not independently re-audited. No fit, sample, graph rebuild or new empirical claim.'}
    with (HERE/'result.json').open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    main()

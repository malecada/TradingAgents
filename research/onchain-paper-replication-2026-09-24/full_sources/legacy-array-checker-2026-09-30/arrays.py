"""Independent read-only saved-array checks; no research admission or raw audit.

Numerical checks derive from the retained graph-verification-10 verifier. This
candidate adds explicit extent budgets, file stability and mapping cleanup.
Execution on empirical arrays requires a separately reviewed guarded wrapper.
"""
import hashlib
import json
import os
from pathlib import Path
import stat

import numpy as np

NAMES = frozenset(('node_ids', 'edge_index', 'edge_aggregates',
                   'edge_features', 'node_features'))
BLOCK = 65536


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode()


def integer(value):
    return type(value) is int and value >= 0


def signature(path, device):
    s = path.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1 and s.st_dev == device,
            'file must be regular, single-link and on the manifest device')
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def members(root):
    found = set()
    with os.scandir(root) as entries:
        for entry in entries:
            found.add(entry.name)
            require(len(found) <= 6, 'unexpected directory members')
    require(found == {'manifest.json'} | {n + '.npy' for n in NAMES},
            'unexpected directory members')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def streamed_identity(metadata, arrays):
    # Exact canonical JSON, independently serialized without production helpers.
    # The largest temporary row is one edge-index row, bounded by array bytes.
    values = dict(metadata, **arrays)
    h = hashlib.sha256(b'{')
    for i, key in enumerate(sorted(values)):
        if i:
            h.update(b',')
        h.update(encode(key) + b':')
        value = values[key]
        if isinstance(value, np.ndarray):
            h.update(b'[')
            for j, item in enumerate(value):
                if j:
                    h.update(b',')
                h.update(encode(item.tolist()))
            h.update(b']')
        else:
            h.update(encode(value))
    h.update(b'}')
    return h.hexdigest()


def verify(manifest_path, *, expected_manifest_sha256, expected_array_bytes,
           max_array_bytes):
    path = Path(manifest_path)
    require(path.name == 'manifest.json', 'manifest filename')
    require(integer(expected_array_bytes) and integer(max_array_bytes)
            and 0 < expected_array_bytes <= max_array_bytes, 'array byte budget')
    device = path.parent.stat().st_dev
    signatures = {path: signature(path, device)}
    require(signatures[path][2] <= 65536, 'manifest size limit')
    members(path.parent)
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected_manifest_sha256,
            'manifest hash mismatch')
    manifest = json.loads(data, object_pairs_hook=unique_object)
    require(set(manifest) == {'arrays', 'metadata', 'graph_hash'}, 'manifest schema')
    require(set(manifest['arrays']) == NAMES, 'array membership')
    meta = manifest['metadata']
    require(isinstance(meta, dict) and not NAMES.intersection(meta), 'metadata schema')
    require(integer(meta['raw_count']) and integer(meta['admitted_count'])
            and isinstance(meta['exclusion_counts'], dict)
            and all(integer(v) for v in meta['exclusion_counts'].values()),
            'invalid transaction counts')
    require(meta['raw_count'] == meta['admitted_count'] + sum(meta['exclusion_counts'].values()),
            'raw/admitted/excluded conservation')
    total = 0
    for name, entry in manifest['arrays'].items():
        require(set(entry) == {'path', 'bytes', 'sha256'} and entry['path'] == name + '.npy',
                'array declaration schema')
        require(integer(entry['bytes']) and entry['bytes'] > 0, 'array extent')
        p = path.parent / entry['path']
        signatures[p] = signature(p, device)
        require(signatures[p][2] == entry['bytes'], 'array byte mismatch')
        total += entry['bytes']
    require(total == expected_array_bytes and total <= max_array_bytes, 'array byte budget')
    for name, entry in manifest['arrays'].items():
        p = path.parent / entry['path']
        require(digest(p) == entry['sha256'], 'array hash mismatch')
        require(signature(p, device) == signatures[p], 'array changed during hashing')
    arrays = {}
    try:
        for name in sorted(NAMES):
            p = path.parent / (name + '.npy')
            arrays[name] = np.load(p, mmap_mode='r', allow_pickle=False)
            a = arrays[name]
            require(isinstance(a, np.memmap) and a.offset + a.nbytes == signatures[p][2],
                    'NPY extent mismatch')
        nodes, edges, raw = arrays['node_ids'], arrays['edge_index'], arrays['edge_aggregates']
        require(nodes.ndim == 1 and nodes.dtype.kind == 'U' and len(nodes) > 0, 'node schema')
        require(edges.ndim == 2 and edges.shape[0] == 2 and edges.dtype == np.dtype('int64'),
                'edge schema')
        n, e = len(nodes), edges.shape[1]
        require(arrays['node_features'].shape == (n, 4), 'node feature shape')
        require(raw.shape == arrays['edge_features'].shape == (e, 2), 'edge feature shape')
        require(all(arrays[k].dtype == np.dtype('float64') for k in
                    ('node_features', 'edge_features', 'edge_aggregates')), 'feature dtype')
        for start in range(0, n, BLOCK):
            ids = nodes[start:min(n, start + BLOCK + 1)]
            require(np.all(ids != '') and np.all(ids[1:] > ids[:-1]), 'node order/uniqueness')
        count_sum = 0
        for start in range(0, e, BLOCK):
            stop = min(e, start + BLOCK)
            ends = edges[:, start:min(e, stop + 1)]
            require(np.all((ends >= 0) & (ends < n)), 'edge endpoints')
            require(np.all((ends[0, 1:] > ends[0, :-1]) |
                    ((ends[0, 1:] == ends[0, :-1]) & (ends[1, 1:] > ends[1, :-1]))),
                    'edge order/uniqueness')
            values = raw[start:stop]
            require(np.isfinite(values).all() and np.all(values > 0), 'edge aggregates')
            require(np.all(values[:, 0] == np.floor(values[:, 0])), 'fractional count')
            count_sum += sum(map(int, values[:, 0]))
            observed = arrays['edge_features'][start:stop]
            require(np.isfinite(observed).all() and np.all(observed >= 0)
                    and np.allclose(np.log1p(values), observed, rtol=1e-12, atol=1e-12),
                    'edge feature reconstruction')
        require(count_sum == meta['admitted_count'], 'edge count conservation')
        errors = {}
        for column, direction, attribute in ((0, 1, 0), (1, 0, 0), (2, 1, 1), (3, 0, 1)):
            expected = np.log1p(np.bincount(edges[direction], weights=raw[:, attribute], minlength=n))
            observed = arrays['node_features'][:, column]
            require(np.isfinite(expected).all() and np.isfinite(observed).all()
                    and np.all(observed >= 0)
                    and np.allclose(expected, observed, rtol=1e-12, atol=1e-12),
                    'node feature reconstruction')
            errors[str(column)] = float(np.max(np.abs(expected - observed)))
        identity = streamed_identity(meta, arrays)
        require(identity == manifest['graph_hash'], 'independent graph hash mismatch')
        members(path.parent)
        require(all(signature(p, device) == s for p, s in signatures.items()),
                'inputs changed during verification')
        result = dict(graph_hash=identity, nodes=n, directed_edges=e,
                      admitted_transactions=count_sum, array_bytes=total,
                      node_feature_max_absolute_errors=errors)
    finally:
        failures = []
        for a in arrays.values():
            try:
                mapping = getattr(a, '_mmap', None)
                if mapping is not None:
                    mapping.close()
                    if not mapping.closed:
                        failures.append('mapping remains open')
                elif isinstance(a, np.lib.npyio.NpzFile):
                    # np.load dispatches on file contents, not the .npy suffix.
                    a.close()
                    if a.zip is not None or a.fid is not None:
                        failures.append('rejected archive remains open')
            except Exception as exc:
                failures.append(str(exc))
        if failures:
            raise RuntimeError('array mapping cleanup failed: ' + '; '.join(failures))
    result['array_mappings_closed'] = True
    return result

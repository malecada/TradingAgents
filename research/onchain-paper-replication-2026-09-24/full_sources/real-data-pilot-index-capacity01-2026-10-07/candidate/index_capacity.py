"""Metadata-only early index reservation check for the selected seven ETH graphs.

Manifest SHA256 is authenticated; bounded NPY headers are observed, never array
payloads. This rejects known impossible reservations before import/graph loading.
It does not replace the later full-body/semantic graph validation or native cap.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct


def require(ok, message):
    if not ok:
        raise ValueError(message)


def demand(nodes, edges, node_width, edge_width, chunk, limit):
    require(all(type(v) is int and 0 < v < 2**63 for v in
                (nodes, node_width, edge_width, chunk, limit))
            and type(edges) is int and 0 <= edges < 2**63, 'invalid capacity dimensions')
    retained = 16 * (edges + nodes + 1)
    additive = retained + 16 * edges + 40 * (nodes + 1) + 4 * nodes + chunk * (64 + 2 * node_width + 2 * edge_width)
    # A complete induced neighborhood cannot contain more than all graph edges.
    # No degree inspection, sampling, truncation, or matching is needed.
    output = min(nodes, limit) * node_width + edges * (16 + edge_width)
    return {'retained_index_bytes': retained, 'index_additive_bytes': additive,
            'maximum_single_neighborhood_array_bytes': output,
            'output_inclusive_buffer_bytes': additive + 2 * output,
            'mcm_output_bytes': nodes * 32 * 4}


def _header(path, member):
    require(not path.is_symlink(), 'capacity array symlink')
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and type(member['bytes']) is int and before.st_size == member['bytes'],
                'capacity array extent differs')
        magic = stream.read(8)
        require(magic[:6] == b'\x93NUMPY' and magic[6:] in (b'\x01\x00', b'\x02\x00'), 'capacity NPY version')
        width = 2 if magic[6:] == b'\x01\x00' else 4
        rawlen = stream.read(width)
        require(len(rawlen) == width, 'capacity header length missing')
        length = struct.unpack('<H' if width == 2 else '<I', rawlen)[0]
        require(0 < length <= 10000, 'capacity header bound')
        raw = stream.read(length)
        require(len(raw) == length, 'capacity header truncated')
        header = ast.literal_eval(raw.decode('latin1'))
        require(type(header) is dict and set(header) == {'descr', 'fortran_order', 'shape'}, 'capacity header schema')
        shape = header['shape']; dtype = header['descr']
        require(type(shape) is tuple and all(type(v) is int and v >= 0 for v in shape)
                and header['fortran_order'] is False and dtype in ('<f8', '<i8'), 'capacity header type/order')
        require(8 + width + length + math.prod(shape) * 8 == before.st_size, 'capacity header payload extent')
        after = os.fstat(stream.fileno())
        fields = ('st_dev', 'st_ino', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
        require(all(getattr(before, f) == getattr(after, f) for f in fields), 'capacity header changed')
    return {'shape': list(shape), 'dtype': dtype, 'header_bytes': 8 + width + length,
            'header_sha256': hashlib.sha256(magic + rawlen + raw).hexdigest(),
            'member_sha256': member['sha256'], 'member_bytes': member['bytes'],
            'stat_identity': [getattr(after, f) for f in fields]}


def inspect(root, inputs, graph_inputs, numeric, dictionary):
    """Return exact scalar demands, with no graph loads and no policy mutation."""
    root = Path(root).resolve()
    require(type(graph_inputs) is dict and len(graph_inputs) == 7
            and len(set(graph_inputs.values())) == 7, 'exact seven capacity graphs required')
    require(type(numeric) is dict and set(numeric) == {'schema_version', 'max_buffer_bytes', 'edge_chunk', 'max_output_bytes', 'max_numeric_bytes'}
            and type(numeric['schema_version']) is int and numeric['schema_version'] == 1
            and all(type(numeric[k]) is int and 0 < numeric[k] < 2**63 for k in numeric if k != 'schema_version'), 'capacity numeric schema')
    limit = dictionary['maximum_neighborhood_nodes']; chunk = numeric['edge_chunk']
    require(dictionary['size'] == 32 and dictionary['hop_depth'] == 1, 'original dictionary contract required')
    rows = []
    for graph_hash, role in sorted(graph_inputs.items()):
        ref = inputs[role]; path = root / ref['path']
        require(path.resolve().is_relative_to(root) and not path.is_symlink(), 'capacity manifest containment')
        require(path.stat().st_size <= 65536, 'capacity manifest bound')
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'capacity manifest SHA differs')
        manifest = json.loads(raw)
        require(manifest['graph_hash'] == graph_hash and manifest['metadata']['asset'] == 'ETH', 'capacity graph join differs')
        headers = {}
        for name in ('node_features', 'edge_index', 'edge_features'):
            member = manifest['arrays'][name]
            require(member['path'] == name + '.npy', 'capacity member name differs')
            headers[name] = _header(path.parent / member['path'], member)
        nf, ei, ef = (headers[name] for name in ('node_features', 'edge_index', 'edge_features'))
        require(len(nf['shape']) == len(ei['shape']) == len(ef['shape']) == 2
                and nf['dtype'] == ef['dtype'] == '<f8' and ei['dtype'] == '<i8'
                and nf['shape'][1] == 4 and ef['shape'][1] == ei['shape'][0] == 2
                and ei['shape'][1] == ef['shape'][0], 'capacity graph axes/feature widths differ')
        n, e = nf['shape'][0], ei['shape'][1]
        rows.append({'graph_hash': graph_hash, 'role': role, 'manifest': dict(ref),
                     'headers': headers, 'nodes': n, 'edges': e,
                     'node_width_bytes': 32, 'edge_width_bytes': 16,
                     **demand(n, e, 32, 16, chunk, limit)})
    return {'graphs': rows, 'max_buffer_required': max(r['output_inclusive_buffer_bytes'] for r in rows),
            'max_output_required': max(r['mcm_output_bytes'] for r in rows),
            'qualification': 'Metadata reservation only; header observations are not fresh body authentication, peak RSS or capacity proof.'}


def validate(root, inputs, graph_inputs, numeric, dictionary):
    report = inspect(root, inputs, graph_inputs, numeric, dictionary)
    require(numeric['max_buffer_bytes'] >= report['max_buffer_required'],
            'seven-graph output-inclusive index allowance insufficient: required=' + str(report['max_buffer_required']) + ' allowed=' + str(numeric['max_buffer_bytes']))
    require(numeric['max_output_bytes'] >= report['max_output_required'], 'seven-graph MCM output allowance insufficient')
    require(numeric['max_numeric_bytes'] >= report['max_output_required'] + numeric['max_buffer_bytes'], 'seven-graph MCM numeric allowance insufficient')
    return report

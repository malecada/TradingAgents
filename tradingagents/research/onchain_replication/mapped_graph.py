"""Borrowed read-only graph maps, with explicit file-byte and lifetime bounds.

Backing files must remain frozen for the entire context. Read-only maps do not
provide isolation from external writers. Raw graph arrays/views must not escape
the context; consumers may retain only independently owned derived outputs.
The bound includes NPY headers, not validation/adjacency/model working memory.
"""
from contextlib import contextmanager
from dataclasses import fields
from pathlib import Path
from types import MappingProxyType
import json

import numpy as np

from .contracts import GraphSnapshot, validate_graph
from .neighborhoods import graph_hash
from .provenance import file_hash, require_hash


class _MappedGraphSnapshot(GraphSnapshot):
    # No new dataclass fields: canonical scientific identity stays unchanged.
    def __post_init__(self):
        for name in ('node_ids', 'node_features', 'edge_index', 'edge_features', 'edge_aggregates'):
            value = getattr(self, name)
            if name == 'edge_aggregates' and value is None:
                continue
            if not isinstance(value, np.memmap) or value.mode != 'r' or value.flags.writeable:
                raise ValueError('read-only graph file maps required')
            if name == 'node_ids':
                if value.ndim != 1 or value.dtype.kind != 'U':
                    raise ValueError('one-dimensional Unicode node IDs required')
            elif value.dtype.kind not in 'iuf':
                raise ValueError('real numeric graph file maps required')
        object.__setattr__(self, 'source_hashes', tuple(self.source_hashes))
        object.__setattr__(self, 'exclusion_counts', MappingProxyType(dict(self.exclusion_counts)))


def _close_maps(mappings, *, primary=None):
    errors = []
    for mapping in reversed(mappings):
        try:
            mapping.close()
        except BaseException as error:
            errors.append(error)
    if errors:
        if primary is not None:
            primary.add_note('graph mapping cleanup failed: ' + repr(errors[0]))
        else:
            raise RuntimeError('graph mapping cleanup failed') from errors[0]


@contextmanager
def open_mapped_graph(manifest_path, expected_hash, *, max_mapped_bytes):
    """Verify and borrow all graph arrays without making eager RAM copies."""
    if type(max_mapped_bytes) is not int or max_mapped_bytes <= 0:
        raise ValueError('positive graph mapping byte bound required')
    path = Path(manifest_path)
    require_hash(expected_hash)
    if path.stat().st_size > 65536:
        raise ValueError('graph manifest metadata bound exceeded')
    if file_hash(path) != expected_hash:
        raise ValueError('graph manifest hash differs')
    manifest = json.loads(path.read_bytes())
    required = {'node_ids', 'node_features', 'edge_index', 'edge_features'}
    allowed = required | {'edge_aggregates'}
    if (not isinstance(manifest, dict) or set(manifest) != {'metadata', 'graph_hash', 'arrays'}
            or not isinstance(manifest['arrays'], dict)
            or not required <= set(manifest['arrays']) <= allowed):
        raise ValueError('invalid graph member denominator')
    metadata = {f.name for f in fields(GraphSnapshot)} - allowed
    if not isinstance(manifest['metadata'], dict) or set(manifest['metadata']) != metadata:
        raise ValueError('invalid graph metadata fields')
    require_hash(manifest['graph_hash'])
    total = 0
    members = []
    for name, info in manifest['arrays'].items():
        if (not isinstance(info, dict) or set(info) != {'path', 'sha256', 'bytes'}
                or info['path'] != name + '.npy'
                or type(info['bytes']) is not int or info['bytes'] <= 0):
            raise ValueError('invalid graph member descriptor')
        require_hash(info['sha256'])
        total += info['bytes']
        members.append((name, path.parent / info['path'], info))
    if total > max_mapped_bytes:
        raise ValueError('graph mapping byte bound exceeded')
    # Complete size and content admission precedes the first mmap.
    for _, member, info in members:
        if member.is_symlink() or not member.is_file() or member.stat().st_size != info['bytes']:
            raise ValueError('graph member size/path differs')
    for _, member, info in members:
        if file_hash(member) != info['sha256']:
            raise ValueError('graph member hash differs')
        with member.open('rb') as stream:
            if np.lib.format.read_magic(stream) not in {(1, 0), (2, 0), (3, 0)}:
                raise ValueError('unsupported graph NPY version')
    opened = []
    failure = None
    try:
        arrays = {}
        for name, member, info in members:
            value = np.load(member, allow_pickle=False, mmap_mode='r', max_header_size=10000)
            if not isinstance(value, np.memmap):
                raise ValueError('graph member is not a mapped NPY array')
            opened.append(value._mmap)
            if value.offset + value.nbytes != info['bytes']:
                raise ValueError('graph member data extent differs')
            arrays[name] = value
        graph = _MappedGraphSnapshot(**manifest['metadata'], **arrays)
        validate_graph(graph)
        if graph_hash(graph) != manifest['graph_hash']:
            raise ValueError('graph content identity differs')
        yield graph
    except BaseException as error:
        failure = error
        raise
    finally:
        _close_maps(opened, primary=failure)

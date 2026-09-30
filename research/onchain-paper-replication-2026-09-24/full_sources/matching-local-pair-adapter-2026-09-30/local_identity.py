"""Type-tagged matching identities without inventing weekly slice metadata."""
import hashlib
import json
import numpy as np
from tradingagents.research.onchain_replication.contracts import (
    GraphSnapshot, AttributedGraph, validate_attributed)
from tradingagents.research.onchain_replication.neighborhoods import graph_hash


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def graph_identity(graph):
    if isinstance(graph, GraphSnapshot):
        # Keep the existing validated weekly identity inside a distinct typed
        # namespace; old untyped checkpoint identities are deliberately refused.
        return hashlib.sha256(b'matching-weekly-v1\0'+graph_hash(graph).encode()).hexdigest()
    if not isinstance(graph, AttributedGraph):
        raise ValueError('unknown matching graph contract')
    validate_attributed(graph)
    if any(not isinstance(node, str) or not node for node in graph.node_ids):
        raise ValueError('nonempty string local node identities required')
    result = hashlib.sha256(b'matching-local-v1\0')
    def frame(raw):
        result.update(len(raw).to_bytes(8, 'big')); result.update(raw)
    frame(canonical({'parent_hash': graph.parent_hash, 'center_id': graph.center_id,
                     'node_count': len(graph.node_ids)}))
    for start in range(0, len(graph.node_ids), 1024):
        frame(canonical(graph.node_ids[start:start+1024]))
    for name in ('node_features', 'edge_index', 'edge_features'):
        array = getattr(graph, name)
        if array.dtype.kind not in 'fiu' or not array.flags.c_contiguous:
            raise ValueError('contiguous real numeric local arrays required')
        frame(canonical({'name': name, 'dtype': array.dtype.str, 'shape': list(array.shape),
                         'bytes': array.nbytes}))
        # Empty arrays cannot always be cast through a shaped memoryview.
        if array.size:
            view = memoryview(array).cast('B')
            for start in range(0, array.nbytes, 1024**2):
                result.update(view[start:start+1024**2])
    return result.hexdigest()

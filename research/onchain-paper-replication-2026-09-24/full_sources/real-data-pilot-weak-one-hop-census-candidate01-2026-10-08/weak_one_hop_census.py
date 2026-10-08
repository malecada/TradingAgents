"""Exact weak-one-hop sizes for resource preparation; no graph/body loading.

Caller owns input provenance and must keep edge_index immutable during this call.
The explicit numeric-array envelope is 8*N + 8*E + 48*min(max(N, E), chunk_edges)
bytes, INCLUDING returned counts but EXCLUDING caller input, Python/NumPy
metadata, allocator overhead and NumPy internal iteration buffers. This is not
a process RAM bound or resource admission. Sorting is in-place heapsort on a
contiguous uint64 vector (zero sort workspace; O(E log E) worst-case time).
No neighborhood is truncated and no limit is accepted/changed by this helper.
"""

import sys

import numpy as np


def census(edge_index, node_count, *, max_work_bytes, chunk_edges=65536):
    """Return exact per-center counts and summaries at declared threshold 10000.

    Centers use the supplied graph's zero-based indices. Ties for maximum select
    the smallest index. Empty edge sets are valid; an empty node universe is not.
    Only ordinary integer ndarrays are accepted; no coercion/loading occurs.
    """
    if type(node_count) is not int or not 1 <= node_count <= 2**32:
        raise ValueError('node_count must be in [1, 2**32] for uint64 packing')
    if type(max_work_bytes) is not int or max_work_bytes < 1:
        raise ValueError('max_work_bytes must be a positive integer')
    if type(chunk_edges) is not int or chunk_edges < 1:
        raise ValueError('chunk_edges must be a positive integer')
    if type(edge_index) is not np.ndarray:
        raise TypeError('edge_index must be an ordinary ndarray')
    if edge_index.ndim != 2 or edge_index.shape[0] != 2:
        raise ValueError('edge_index must have shape (2, E)')
    if edge_index.dtype.kind not in 'iu' or edge_index.dtype.itemsize > 8:
        raise TypeError('edge_index must have an integer dtype of at most 64 bits')
    edge_count = edge_index.shape[1]
    block_size = min(max(node_count, edge_count), chunk_edges)
    envelope = 8 * node_count + 8 * edge_count + 48 * block_size
    if envelope > sys.maxsize or envelope > max_work_bytes:
        raise ValueError('explicit work-array envelope exceeds address/budget limit')
    # Validate all indices before allocating the work arrays; reduce in chunks.
    for start in range(0, edge_count, chunk_edges):
        block = edge_index[:, start:start + chunk_edges]
        if int(block.min()) < 0 or int(block.max()) >= node_count:
            raise ValueError('edge endpoint outside node universe')
    counts = np.ones(node_count, dtype=np.int64)
    keys = np.empty(edge_count, dtype=np.uint64)
    left = np.empty(block_size, dtype=np.uint64)
    right = np.empty(block_size, dtype=np.uint64)
    mask = np.empty(block_size, dtype=np.bool_)
    base = np.uint64(node_count)
    for start in range(0, edge_count, chunk_edges):
        stop = min(edge_count, start + chunk_edges)
        size = stop - start
        u, v = edge_index[:, start:stop]
        np.minimum(u, v, out=left[:size], casting='unsafe')
        np.maximum(u, v, out=right[:size], casting='unsafe')
        np.multiply(left[:size], base, out=keys[start:stop])
        np.add(keys[start:stop], right[:size], out=keys[start:stop])
    keys.sort(kind='heapsort')
    for start in range(0, edge_count, chunk_edges):
        block = keys[start:start + chunk_edges]
        size = len(block)
        mask[0] = start == 0 or block[0] != keys[start - 1]
        np.not_equal(block[1:], block[:-1], out=mask[1:size])
        unique = block[mask[:size]]
        size = len(unique)
        np.floor_divide(unique, base, out=left[:size])
        np.remainder(unique, base, out=right[:size])
        np.not_equal(left[:size], right[:size], out=mask[:size])
        # Repeated endpoint indices require add.at, not fancy-index +=.
        np.add.at(counts, left[:size][mask[:size]], 1)
        np.add.at(counts, right[:size][mask[:size]], 1)
        del unique
    above = 0
    # Chunk the summary too: never allocate an additional node_count mask.
    for start in range(0, node_count, chunk_edges):
        above += int(np.count_nonzero(counts[start:start + chunk_edges] > 10000))
    return {
        'cardinalities': counts,
        'node_count': node_count,
        'edge_count': edge_count,
        'minimum_cardinality': int(counts.min()),
        'maximum_cardinality': int(counts.max()),
        'maximum_center_index': int(counts.argmax()),
        'declared_threshold': 10000,
        'centers_above_declared_threshold': above,
        'explicit_work_array_envelope_bytes': envelope,
    }

"""Isolated exact greedy hardening by stable descending ranking.

Not a production backend or a resumable long-job implementation. The explicit
buffer allowance excludes the input, Python objects and NumPy sort workspace;
a process/cgroup cap is required before any capacity-scale measurement.
"""
import numpy as np


def explicit_bytes(n, m):
    # Includes finite-check scratch conservatively even though it is released
    # before sorting. NumPy's native stable-sort workspace is excluded.
    return (9 + np.dtype(np.intp).itemsize) * n * m + n + m + 16 * min(n, m)


def harden_pairs(matrix, *, max_pair_entries, max_explicit_bytes):
    for limit in (max_pair_entries, max_explicit_bytes):
        if type(limit) is not int or limit <= 0:
            raise ValueError('limits must be positive integers')
    # Require an existing array: constructing an unbounded input is not covered.
    if not isinstance(matrix, np.ndarray) or matrix.ndim != 2:
        raise ValueError('expected two-dimensional NumPy array')
    if matrix.dtype.kind not in 'bifu' or matrix.dtype.itemsize > 8:
        raise ValueError('expected real numeric dtype of at most eight bytes')
    n, m = matrix.shape
    if n * m > max_pair_entries or explicit_bytes(n, m) > max_explicit_bytes:
        raise ValueError('hardening capacity exceeded')
    key = np.array(matrix, dtype=np.float64, order='C', copy=True).reshape(-1)
    if not np.isfinite(key).all():
        raise ValueError('invalid soft assignment')
    np.negative(key, out=key)
    order = np.argsort(key, kind='stable')
    del key
    rows = np.zeros(n, dtype=np.bool_)
    cols = np.zeros(m, dtype=np.bool_)
    pairs = np.empty((min(n, m), 2), dtype=np.int64)
    count = 0
    for index in order:
        u, i = divmod(int(index), m)
        if rows[u] or cols[i]:
            continue
        pairs[count] = (u, i)
        rows[u] = True
        cols[i] = True
        count += 1
        if count == len(pairs):
            break
    if count != min(n, m):
        raise AssertionError('incomplete greedy assignment')
    return pairs

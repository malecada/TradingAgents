"""Unselected bounded RBF helper; no authority or matching-state ownership.

fill_agreement returns False without writing for unsupported inputs. On True,
only out[start:stop] changes. Selected rows must have finite absolute values
<=256. Features and indices require immutable bytes backing; each invocation
validates its selected rows anew. Width is exactly 2 or 4, chunk at most 1024.

The equation is exp(-sum((float(a)-float(b))**2)/width). NumPy reduction/exp
need not be bitwise math.fsum/math.exp: the prospective contract is C05 float64
atol=1e-8, rtol=1e-6, not original per-scalar exception/cursor equivalence.
Caller integration must retain the original route on False and separately
review operation accounting/checkpoints. Allocation errors propagate before
output assignment. Async interruption during final assignment is not atomic.
"""
import numpy as np

MAX_CHUNK = 1024


def _immutable(array, dtype, ndim):
    if (type(array) is not np.ndarray or array.dtype != dtype or
            array.ndim != ndim or not array.flags.c_contiguous or
            array.flags.writeable):
        return False
    base = array
    for _ in range(4):
        if type(base) is bytes:
            return True
        if type(base) is not np.ndarray or base.flags.writeable:
            return False
        base = base.base
    return False


def fill_agreement(left, right, left_indices, right_indices, out, start, stop):
    """Fill paired row agreements into out[start:stop], or refuse unchanged.

    Indices are native int64 vectors; features/output are native float64.
    Full input populations are never copied or scanned: scratch is O(chunk*4).
    The output is caller-owned, writable, contiguous and disjoint from inputs.
    No callbacks, caches, threads or source/Owner checks are performed here.
    """
    if (type(start) is not int or type(stop) is not int or
            not 0 <= start <= stop or stop-start > MAX_CHUNK):
        return False
    if not (_immutable(left, np.dtype('float64'), 2) and
            _immutable(right, np.dtype('float64'), 2) and
            _immutable(left_indices, np.dtype('int64'), 1) and
            _immutable(right_indices, np.dtype('int64'), 1)):
        return False
    if (left.shape[1] not in (2, 4) or right.shape[1] != left.shape[1] or
            stop > len(left_indices) or stop > len(right_indices) or
            type(out) is not np.ndarray or out.dtype != np.dtype('float64') or
            out.ndim != 1 or not out.flags.c_contiguous or
            not out.flags.writeable or stop > len(out)):
        return False
    if np.geterr() != dict(divide='warn', over='warn', under='ignore', invalid='warn'):
        return False
    if any(np.shares_memory(out, x) for x in (left, right, left_indices, right_indices)):
        return False
    li = left_indices[start:stop]
    ri = right_indices[start:stop]
    if (np.any(li < 0) or np.any(li >= len(left)) or
            np.any(ri < 0) or np.any(ri >= len(right))):
        return False
    a = left[li]
    b = right[ri]
    if (not np.isfinite(a).all() or not np.isfinite(b).all() or
            np.any(np.abs(a) > 256.) or np.any(np.abs(b) > 256.)):
        return False
    # Bounded temporaries, no whole edge-product or per-cell Python callback.
    np.subtract(a, b, out=a)
    np.square(a, out=a)
    values = np.sum(a, axis=1)
    np.negative(values, out=values)
    np.divide(values, left.shape[1], out=values)
    np.exp(values, out=values)
    out[start:stop] = values
    return True

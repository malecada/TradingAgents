"""Exact greedy row-major hardening with bounded numeric scratch and sparse output.

Input residency and Python/runtime overhead are outside the numeric allowance.
This component grants no matching-capacity override and has no empirical caller.
"""
import numpy as np


def harden_indices(matrix,*,max_buffer_bytes,chunk_entries=65536):
    if (not isinstance(matrix,np.ndarray) or matrix.ndim!=2 or matrix.dtype.kind not in 'biuf'
            or matrix.dtype.itemsize>8):raise ValueError('two-dimensional real matrix required')
    if type(max_buffer_bytes) is not int or max_buffer_bytes<=0 or type(chunk_entries) is not int or chunk_entries<=0:raise ValueError('positive numeric scratch bounds required')
    n,m=matrix.shape;matches=min(n,m);entries=n*m;chunk=min(chunk_entries,entries)
    # Output pairs + two sorted endpoint arrays + overlap-shift allowance, and
    # chunk values, source-cast coexistence, indices, membership/gather scratch.
    required=48*matches+64*chunk
    if required>max_buffer_bytes:raise ValueError('hardening numeric scratch allowance exceeded')
    for start in range(0,entries,chunk or 1):
        values=np.asarray(matrix.flat[start:start+chunk],dtype=np.float64)
        if not np.isfinite(values).all():raise ValueError('invalid soft assignment')
    if entries:del values
    pairs=np.empty((matches,2),dtype=np.int64)
    used_rows=np.empty(matches,dtype=np.int64);used_cols=np.empty(matches,dtype=np.int64)
    for step in range(matches):
        best_value=-np.inf;best_index=None
        for start in range(0,entries,chunk):
            stop=min(entries,start+chunk)
            values=np.asarray(matrix.flat[start:stop],dtype=np.float64)
            indexes=np.arange(start,stop,dtype=np.int64)
            rows=indexes//m;cols=indexes%m
            if step:
                positions=np.searchsorted(used_rows[:step],rows)
                np.minimum(positions,step-1,out=positions)
                values[used_rows[positions]==rows]=-np.inf
                del positions
                positions=np.searchsorted(used_cols[:step],cols)
                np.minimum(positions,step-1,out=positions)
                values[used_cols[positions]==cols]=-np.inf
                del positions
            offset=int(np.argmax(values));value=float(values[offset])
            # Strict greater preserves the first row-major occurrence across
            # chunks, matching np.argmax on the legacy full work matrix.
            if value>best_value:best_value=value;best_index=start+offset
            del values,indexes,rows,cols
        if best_index is None:raise RuntimeError('no feasible hardening entry')
        row,column=divmod(best_index,m);pairs[step]=(row,column)
        pos=int(np.searchsorted(used_rows[:step],row));used_rows[pos+1:step+1]=used_rows[pos:step];used_rows[pos]=row
        pos=int(np.searchsorted(used_cols[:step],column));used_cols[pos+1:step+1]=used_cols[pos:step];used_cols[pos]=column
    return pairs

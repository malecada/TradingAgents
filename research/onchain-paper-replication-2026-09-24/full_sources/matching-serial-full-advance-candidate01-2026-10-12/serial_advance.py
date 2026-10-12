"""UNINSTALLED: one-pair full-budget specialization, no authority capability.

try_advance_checked requires the unchanged same-call exclusive session proof.
None means unsupported with no numerical writes. advance is the fresh-check API.
The wrapper is an explicit selection; importing does not change installed code.
"""
import numpy as np
from tradingagents.research.onchain_replication import matching_annealing as ann
from tradingagents.research.onchain_replication.matching_immutable_session import graph_pin, rejoin
ORIGINAL = ann._advance_checked
SCRATCH_RESERVATION = 262144  # EXTRA prospective charge, not existing funded slack.
DEFAULT_ERRORS = dict(divide='warn', over='warn', under='ignore', invalid='warn')


def scratch_bound(n, m, total):
    # Geometry/indices/weights/product <=80T; scipy/reduction workspace <=536nm;
    # 32KiB fixed headers/pins/Python margin. Library allocator/RSS is not a cap.
    return 32768 + 80 * total + 536 * n * m


def eligibility(state, a, b, c, budget, normalizer, edge_cache_policy):
    if type(budget) is not int or budget <= 0:
        return None
    if (state['phase'] != 'nodes' or state['cursor'] != 0 or state['iterations'] != 0):
        return None
    n, m = state['shape']; total = a.edge_index.shape[1] * b.edge_index.shape[1]
    if not (1 <= n <= 16 and 1 <= m <= 16 and 8 <= total <= 1024):
        return None
    if state['max_chunk_entries'] < max(n*m, 2*n) or scratch_bound(n,m,total) > SCRATCH_RESERVATION:
        return None
    if not ann._reuse_runtime() or np.geterr() != DEFAULT_ERRORS:
        return None
    # Exact original scientific schedule; no broad/config-dependent specialization.
    for name, value in (('alpha',1.),('beta0',1.),('beta_final',30.),('beta_rate',.075),
                        ('max_iterations',50),('normalization_iterations',1),('solver','algorithm1_literal')):
        if c[name] != value:
            return None
    # Validate policy exactly as original before numerical mutation.
    ann._adaptive_selected(edge_cache_policy)
    try:
        pins = (graph_pin(a), graph_pin(b))
    except ValueError:
        return None
    for graph in (a,b):
        if graph.edge_index.dtype != np.int64:
            return None
        for array in (graph.node_features, graph.edge_features):
            if (array.dtype != np.float64 or array.dtype.metadata is not None
                    or array.shape[1] > 16 or not np.all(np.isfinite(array))
                    or np.any(np.abs(array)>256)):
                return None
    spans=[]
    for name in ann.NAMES:
        array=state[name]
        if type(array) is not np.ndarray or not array.flags.writeable:
            return None
        start=array.__array_interface__['data'][0];spans.append((start,start+array.nbytes))
    spans.sort()
    if any(x[1]>y[0] for x,y in zip(spans,spans[1:])):
        return None
    beta=c['beta0'];iterations=0
    while beta<=c['beta_final'] and iterations<c['max_iterations']:
        beta*=1+c['beta_rate'];iterations+=1
    needed=n*m+iterations*(total+5)
    if budget<needed:
        return None
    return n,m,total,iterations,needed,pins


def try_advance_checked(state,a,b,c,*,max_operations,edge_cache_policy=None,
                        normalizer=None,edge_chunk_fill=None):
    """No-write None fallback; eligible mutations have original phase/cursor semantics.

    No hardening here: unchanged engine owns the original zero-op handoff.
    The <=1024 domain uses original scalar agreements/local half-weight reuse,
    so the numeric adapter is intentionally not invoked, exactly as baseline.
    """
    key=eligibility(state,a,b,c,max_operations,normalizer,edge_cache_policy)
    if key is None:
        return None
    n,m,total,iterations,needed,pins=key
    # Allocate bounded scratch before marking state unsafe or changing matrices.
    positions=np.arange(total,dtype=np.int64)
    left,right=np.divmod(positions,b.edge_index.shape[1])
    u=a.edge_index[0,left];v=a.edge_index[1,left]
    i=b.edge_index[0,right];j=b.edge_index[1,right]
    weights=np.empty(total,dtype=np.float64)
    product=np.empty(total,dtype=np.float64)
    V,M,Q=(state[name] for name in ann.NAMES)
    scalar_entries=scalar_chunks=0;used=0
    state['safe']=False
    try:
        for row in range(n):
            for col in range(m):
                V[row,col]=ann.agreement(a.node_features[row],b.node_features[col])
                state['cursor']+=1;used+=1;scalar_entries+=1;scalar_chunks+=1
        M[:]=V;state.update(phase='outer',cursor=0)
        for iteration in range(iterations):
            # Preserve fresh original runtime checks; input pins are local to call.
            rejoin(a,pins[0]);rejoin(b,pins[1])
            if not ann._reuse_runtime() or np.geterr()!=DEFAULT_ERRORS:
                raise ValueError('serial matching runtime changed during advance')
            Q[:]=c['alpha']*V;state.update(phase='edges',cursor=0);used+=1
            ann.phase_timing.add_count('chunk_'+('8to255' if total<256 else '256to1023' if total<1024 else '1024')+'_calls',1)
            if iteration==0:
                offset=0
                try:
                    for offset in range(total):
                        weights[offset]=.5*ann.agreement(a.edge_features[left[offset]],b.edge_features[right[offset]])
                        scalar_entries+=1;scalar_chunks+=1
                except BaseException:
                    # Same scalar prefix/cursor as the baseline chunk failure.
                    for done in range(offset):
                        Q[u[done],i[done]]+=weights[done]*M[v[done],j[done]]
                        state['cursor']+=1;used+=1
                    raise
            np.multiply(weights,M[v,j],out=product)
            np.add.at(Q,(u,i),product)
            used+=total;state.update(phase='normalize_scale',cursor=0)
            if np.any(Q<0) or (state['beta']>1 and float(Q.max())>np.finfo(np.float64).max/state['beta']):
                raise ValueError('invalid or overflowing normalization input')
            np.multiply(Q.reshape(-1),state['beta'],out=M.reshape(-1))
            used+=1;state.update(phase='normalize_rows',cursor=0)
            M-=(ann.logsumexp(M,axis=1,keepdims=True) if normalizer is None else normalizer.lse(M,axis=1,keepdims=True,fallback=ann.logsumexp))
            used+=1;state.update(phase='normalize_columns',cursor=0)
            M-=(ann.logsumexp(M,axis=0,keepdims=True) if normalizer is None else normalizer.lse(M,axis=0,keepdims=True,fallback=ann.logsumexp))
            used+=1;state.update(phase='normalize_exp',cursor=0)
            np.exp(M.reshape(-1),out=M.reshape(-1))
            used+=1;state['beta']*=1+c['beta_rate'];state['iterations']+=1
            state.update(phase='outer',cursor=0)
        if max_operations>needed:
            state['phase']='done'  # original termination transition uses zero ops
        state['safe']=True
        return used
    except BaseException:
        state['safe']=False
        raise
    finally:
        ann.phase_timing.add_count('agreement_scalar_entries',scalar_entries)
        ann.phase_timing.add_count('agreement_scalar_chunks',scalar_chunks)


def advance_checked(state,a,b,c,*,max_operations,edge_cache_policy=None,
                    normalizer=None,edge_chunk_fill=None):
    """Explicit selected seam; original fallback receives original arguments once."""
    options=dict(max_operations=max_operations,edge_cache_policy=edge_cache_policy,
                 normalizer=normalizer,edge_chunk_fill=edge_chunk_fill)
    used=try_advance_checked(state,a,b,c,**options)
    if used is None:
        return ORIGINAL(state,a,b,c,**options)
    return used


def advance(state,a,b,c,*,max_operations,edge_cache_policy=None):
    """Public direct entry preserves fresh validation on every invocation."""
    if type(max_operations) is not int or max_operations<=0:
        raise ValueError('positive operation budget required')
    ann.check(state,a,b,c)
    return advance_checked(state,a,b,c,max_operations=max_operations,edge_cache_policy=edge_cache_policy)

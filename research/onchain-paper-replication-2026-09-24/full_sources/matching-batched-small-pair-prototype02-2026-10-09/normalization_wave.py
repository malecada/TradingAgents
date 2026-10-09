"""Uninstalled operation-compatible normalization wave; no authority capability.

Own states exclusively during call. Exactly one original row/column operation
may be grouped; every other supplied logical advance delegates unchanged.
After valid argument/ownership admission, failure closes all supplied states and
preserves the primary exception; rejected argument extents remain caller-owned.
"""
import numpy as np
from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import batched_numeric_reuse as reuse
ann=engine.ann
SCRATCH_LIMIT=262144
MAX_PAIRS=32

def scratch_bound(count,n,m):
    # Pinned real float64 SciPy path: stack/output/masks/copies/reduction arrays
    # charged conservatively as64 eight-byte full-block arrays, plus64KiB.
    return 65536+512*count*n*m

def close_all(states,primary=None):
    first=None
    for state in states:
        try:engine.close(state)
        except BaseException as cleanup:
            if primary is not None:primary.add_note('batch state cleanup failed: '+repr(cleanup))
            elif first is None:first=cleanup
            else:first.add_note('additional batch cleanup failed: '+repr(cleanup))
    if primary is None and first is not None:raise first

def _key(state,pair,budget):
    if budget!=1 or type(budget) is not int or state['phase']!='annealing':return None
    inner=state['annealing'];phase=inner['phase'];n,m=inner['shape']
    if phase not in ('normalize_rows','normalize_columns') or inner['cursor']!=0:return None
    if not 1<=n<=16 or not 1<=m<=16 or inner['max_chunk_entries']<max(n*m,2*n):return None
    if not ann._reuse_runtime() or np.geterr()!=dict(divide='warn',over='warn',under='ignore',invalid='warn'):return None
    if not all(reuse.immutable(g) for g in pair):return None
    if any(type(inner[k]) is not np.ndarray for k in ann.NAMES):return None
    matrix=inner['M']
    if not matrix.flags.writeable or not matrix.flags.c_contiguous or np.any(np.abs(matrix)>100):return None
    return phase,n,m

def _disjoint(states):
    spans=[]
    for state in states:
        for name in ann.NAMES:
            x=state['annealing'][name];start=x.__array_interface__['data'][0];spans.append((start,start+x.nbytes))
    spans.sort()
    return all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))

def advance_batch(states,pairs,config,max_operations):
    """Return (per-pair used, diagnostic); identical original per-pair schemas.

    max_operations is a finite sequence of distinct per-pair positive budgets.
    Current1M-op callers retain their original route/cache lifetime. This API does
    not add polling or replace caller checkpoint/authority responsibilities.
    """
    if type(states) not in (list,tuple) or not 1<=len(states)<=MAX_PAIRS:raise ValueError('bounded1..32 states required')
    if type(pairs) not in (list,tuple) or type(max_operations) not in (list,tuple) or len(states)!=len(pairs) or len(states)!=len(max_operations):raise ValueError('batch extent differs')
    if len({id(s) for s in states})!=len(states):raise ValueError('distinct state ownership required')
    used=[];waves=0;peak=0;at=0
    try:
        while at<len(states):
            state=states[at];a,b=pairs[at];budget=max_operations[at]
            engine.check(state,a,b,config)
            key=_key(state,(a,b),budget)
            group=[state];end=at+1
            if key is not None:
                phase,n,m=key
                while end<len(states) and scratch_bound(end-at+1,n,m)<=SCRATCH_LIMIT:
                    other=states[end];left,right=pairs[end]
                    # Actual original current identity/state checks, no cached authority.
                    engine.check(other,left,right,config)
                    if _key(other,(left,right),max_operations[end])!=key:break
                    group.append(other);end+=1
            if key is None or len(group)<2 or not _disjoint(group):
                used.append(engine.advance(state,a,b,config,max_operations=budget));at+=1;continue
            bound=scratch_bound(len(group),n,m)
            if bound>SCRATCH_LIMIT:raise ValueError('normalization scratch admission differs')
            # All graph/state checks completed; no external callback inside this wave.
            for item in group:item['safe']=False;item['annealing']['safe']=False
            work=np.stack([item['annealing']['M'] for item in group],axis=0)
            work-=ann.logsumexp(work,axis=2 if phase=='normalize_rows' else 1,keepdims=True)
            # Publish exactly the result/cursor/phase of ONE original operation.
            for index,item in enumerate(group):
                inner=item['annealing'];inner['M'][:]=work[index]
                inner.update(phase='normalize_columns' if phase=='normalize_rows' else 'normalize_exp',cursor=0,safe=True)
                item['safe']=True;used.append(1)
            del work
            waves+=1;peak=max(peak,bound);at=end
        return used,{'waves':waves,'max_scratch_charge_bytes':peak,'scratch_limit':SCRATCH_LIMIT}
    except BaseException as primary:
        close_all(states,primary);raise

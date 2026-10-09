"""Uninstalled bounded full-budget prototype; original states/used/handoff.

No authority/poll capability. Fresh same-shape full advances only; unsupported
calls delegate once, without splitting the original local agreement cache.
Cross-pair exception ordering differs. After valid argument admission any error
closes all supplied states; no failed/partial batch is resumable through this API.
"""
import numpy as np
from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import batched_numeric_reuse as reuse
ann=engine.ann
SCRATCH_LIMIT=262144
MAX_PAIRS=32

def scratch_bound(count,n,m,edge_pairs):
    # StackV/M/Q24K + conservative SciPy workspace512K; edge arrays/indices,
    # product/gather and indexing allowance64T; batch indices8B;64KiB margin.
    return 65536+count*(536*n*m+64*edge_pairs+8)

def close_all(states,primary=None):
    first=None
    for state in states:
        try:engine.close(state)
        except BaseException as cleanup:
            if primary is not None:primary.add_note('batch state cleanup failed: '+repr(cleanup))
            elif first is None:first=cleanup
            else:first.add_note('additional batch cleanup failed: '+repr(cleanup))
    if primary is None and first is not None:raise first

def _key(state,pair,c,budget):
    if type(budget) is not int or budget<=0 or state['phase']!='annealing':return None
    inner=state['annealing'];n,m=inner['shape'];a,b=pair;ea,eb=a.edge_index.shape[1],b.edge_index.shape[1];total=ea*eb
    if inner['phase']!='nodes' or inner['cursor']!=0 or inner['iterations']!=0:return None
    if not 1<=n<=16 or not 1<=m<=16 or not 0<total<=1024 or inner['max_chunk_entries']<max(n*m,2*n):return None
    if not ann._reuse_runtime() or np.geterr()!=dict(divide='warn',over='warn',under='ignore',invalid='warn'):return None
    if not (0<=c['alpha']<=100 and 0<c['beta0']<=c['beta_final']<=100 and 0<c['beta_rate']<=1 and 0<c['max_iterations']<=50):return None
    if not all(reuse.immutable(g) for g in pair):return None
    for g in pair:
        for x in (g.node_features,g.edge_features):
            if x.dtype!=np.float64 or x.shape[1]>16 or np.any(np.abs(x)>1e10):return None
    if any(type(inner[k]) is not np.ndarray or not inner[k].flags.writeable for k in ann.NAMES):return None
    beta=c['beta0'];iterations=0
    while beta<=c['beta_final'] and iterations<c['max_iterations']:beta*=1+c['beta_rate'];iterations+=1
    needed=n*m+iterations*(1+total+4)
    if budget<needed:return None
    return n,m,ea,eb,iterations,needed,beta

def _disjoint(states):
    spans=[]
    for state in states:
        for name in ann.NAMES:
            x=state['annealing'][name];start=x.__array_interface__['data'][0];spans.append((start,start+x.nbytes))
    spans.sort();return all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))

def _full(states,pairs,c,budgets,key):
    n,m,ea,eb,iterations,needed,final_beta=key;count=len(states);total=ea*eb
    charge=scratch_bound(count,n,m,total)
    if charge>SCRATCH_LIMIT:raise ValueError('batch scratch exceeds original reservation')
    for state in states:state['safe']=False;state['annealing']['safe']=False
    V=np.empty((count,n,m),dtype=np.float64);M=np.empty_like(V);Q=np.empty_like(V)
    weights=np.empty((count,total),dtype=np.float64)
    u=np.empty((count,total),dtype=np.int64);v=np.empty_like(u);i=np.empty_like(u);j=np.empty_like(u);batch=np.arange(count,dtype=np.int64)[:,None]
    for p,(a,b) in enumerate(pairs):
        for row in range(n):
            for col in range(m):V[p,row,col]=ann.agreement(a.node_features[row],b.node_features[col])
        for k in range(ea):
            for l in range(eb):
                z=k*eb+l;u[p,z],v[p,z]=a.edge_index[:,k];i[p,z],j[p,z]=b.edge_index[:,l]
                weights[p,z]=.5*ann.agreement(a.edge_features[k],b.edge_features[l])
    M[:]=V;beta=c['beta0']
    for _ in range(iterations):
        Q[:]=c['alpha']*V
        contributions=weights*M[batch,v,j]
        np.add.at(Q,(batch,u,i),contributions);del contributions
        np.multiply(Q,beta,out=M)
        M-=ann.logsumexp(M,axis=2,keepdims=True)
        M-=ann.logsumexp(M,axis=1,keepdims=True)
        np.exp(M,out=M);beta*=1+c['beta_rate']
    assert beta==final_beta
    for p,(state,(a,b),budget) in enumerate(zip(states,pairs,budgets,strict=True)):
        inner=state['annealing'];inner['V'][:]=V[p];inner['M'][:]=M[p];inner['Q'][:]=Q[p]
        inner.update(phase='outer',cursor=0,beta=beta,iterations=iterations,safe=True);state['safe']=True
    del V,M,Q,weights,u,v,i,j,batch
    for state,(a,b),budget in zip(states,pairs,budgets,strict=True):
        if budget>needed:
            # Original zero-op termination and original matrix/ranking handoff.
            assert engine.advance(state,a,b,c,max_operations=budget-needed)==0
    return [needed]*count,charge

def advance_batch(states,pairs,config,max_operations):
    """(used_per_pair, diagnostic); 1..32 exclusive original composite states.

    Positive per-pair budgets retain original meaning. Exactly-needed budget ends
    at outer; larger budgets include original zero-op termination/ranking handoff.
    Invalid API extents remain caller-owned; after admission failures close all.
    """
    if type(states) not in (list,tuple) or not 1<=len(states)<=MAX_PAIRS:raise ValueError('bounded1..32 states required')
    if type(pairs) not in (list,tuple) or type(max_operations) not in (list,tuple) or len(states)!=len(pairs) or len(states)!=len(max_operations):raise ValueError('batch extent differs')
    if len({id(s) for s in states})!=len(states):raise ValueError('distinct state ownership required')
    used=[];at=0;groups=[]
    try:
        while at<len(states):
            state=states[at];a,b=pairs[at];budget=max_operations[at];engine.check(state,a,b,config)
            key=_key(state,(a,b),config,budget);end=at+1
            if key is not None:
                n,m,ea,eb,*_=key
                while end<len(states) and scratch_bound(end-at+1,n,m,ea*eb)<=SCRATCH_LIMIT:
                    other=states[end];left,right=pairs[end];engine.check(other,left,right,config)
                    if _key(other,(left,right),config,max_operations[end])!=key:break
                    end+=1
            group=states[at:end]
            if key is None or len(group)<2 or not _disjoint(group):
                used.append(engine.advance(state,a,b,config,max_operations=budget));at+=1;continue
            counts,charge=_full(group,pairs[at:end],config,max_operations[at:end],key)
            used.extend(counts);groups.append({'start':at,'stop':end,'scratch_charge_bytes':charge});at=end
        return used,{'fast_groups':groups,'scratch_limit':SCRATCH_LIMIT}
    except BaseException as primary:
        close_all(states,primary);raise

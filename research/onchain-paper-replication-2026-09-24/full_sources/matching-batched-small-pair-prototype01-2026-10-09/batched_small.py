"""Uninstalled bounded synchronous prototype, NOT a checkpoint/polling adapter.

Pairs remain mathematically independent. Cross-pair evaluation/exception order
and operation publication differ from sequential PairExecutor. No empirical use.
"""
import numpy as np
from scipy.special import logsumexp
from tradingagents.research.onchain_replication import matching_checkpoint as engine
from tradingagents.research.onchain_replication import batched_numeric_reuse as reuse
ann=engine.ann
MAX_ITEMS=32
MAX_NODES=16
MAX_EDGE_PAIRS=1024

def sequential(pairs,config,policy,trace=False):
    results=[];history=[]
    for a,b in pairs:
        state=engine.create(a,b,config,**policy);steps=[]
        try:
            inner=state['annealing']
            if trace:
                ann.advance(inner,a,b,config,max_operations=len(a.node_ids)*len(b.node_ids))
                total=a.edge_index.shape[1]*b.edge_index.shape[1]
                while inner['beta']<=config['beta_final'] and inner['iterations']<config['max_iterations']:
                    ann.advance(inner,a,b,config,max_operations=1+total+4)
                    assert inner['phase']=='outer'
                    steps.append((inner['M'].copy(),inner['Q'].copy(),inner['beta'],inner['iterations']))
            while state['phase']!='done':engine.advance(state,a,b,config,max_operations=1000000)
            results.append(engine.result(state,a,b,config));history.append(steps)
        finally:engine.close(state)
    return results,history,{'route':'original_sequential','iterations':[v.iterations for v in results]}

def eligible(pairs,config,policy):
    if not 1<=len(pairs)<=MAX_ITEMS or not ann._reuse_runtime():return False
    if np.geterr()!=dict(divide='warn',over='warn',under='ignore',invalid='warn'):return False
    n,m=len(pairs[0][0].node_ids),len(pairs[0][1].node_ids)
    ea,eb=(g.edge_index.shape[1] for g in pairs[0])
    if not (1<=n<=MAX_NODES and 1<=m<=MAX_NODES and 0<ea*eb<=MAX_EDGE_PAIRS):return False
    if policy['normalization_chunk_entries']<max(n*m,2*n):return False
    if config['normalization_iterations']!=1 or config['solver']!='algorithm1_literal':return False
    if not (type(config['alpha']) in (int,float) and 0<=config['alpha']<=100 and 0<config['beta0']<=config['beta_final']<=100 and 0<config['beta_rate']<=1 and 0<config['max_iterations']<=50):return False
    for a,b in pairs:
        if (len(a.node_ids),len(b.node_ids),a.edge_index.shape[1],b.edge_index.shape[1])!=(n,m,ea,eb):return False
        if not reuse.immutable(a) or not reuse.immutable(b):return False
        for g in (a,b):
            for x in (g.node_features,g.edge_features):
                if x.dtype!=np.float64 or x.shape[1]>16 or not np.isfinite(x).all() or np.any(np.abs(x)>1e10):return False
    return True

def match_batch(pairs,config,policy,trace=False):
    """At most32 same-shape pairs; unsupported domain uses original sequential API.

    No supplied callback/checkpoint semantics: all supported pairs run synchronously.
    Explicit prototype arrays are bounded by item/node/edge-pair caps; SciPy scratch
    and graph storage still belong to the process memory limit, not a live reservation.
    """
    if not eligible(pairs,config,policy):return sequential(pairs,config,policy,trace)
    count=len(pairs);n,m=len(pairs[0][0].node_ids),len(pairs[0][1].node_ids)
    ea,eb=(g.edge_index.shape[1] for g in pairs[0]);total=ea*eb
    states=[];history=[[] for _ in pairs]
    try:
        # Actual original engine creation/identity/policy validation for every pair.
        for a,b in pairs:states.append(engine.create(a,b,config,**policy))
        V=np.empty((count,n,m),dtype=np.float64);Q=np.empty_like(V);M=np.empty_like(V)
        weights=np.empty((count,total),dtype=np.float64)
        u=np.empty((count,total),dtype=np.int64);v=np.empty_like(u);i=np.empty_like(u);j=np.empty_like(u)
        batch=np.arange(count,dtype=np.int64)[:,None]
        for p,(a,b) in enumerate(pairs):
            for row in range(n):
                for col in range(m):V[p,row,col]=ann.agreement(a.node_features[row],b.node_features[col])
            for k in range(ea):
                for l in range(eb):
                    z=k*eb+l;u[p,z],v[p,z]=a.edge_index[:,k];i[p,z],j[p,z]=b.edge_index[:,l]
                    weights[p,z]=.5*ann.agreement(a.edge_features[k],b.edge_features[l])
        M[:]=V;betas=[config['beta0'] for _ in pairs];iterations=[0 for _ in pairs]
        # Independent stop mask retained; common config means all reach48 together.
        active=[p for p in range(count) if betas[p]<=config['beta_final'] and iterations[p]<config['max_iterations']]
        while active:
            assert len(active)==count # same initial config; no cross-pair adaptive state
            Q[:]=config['alpha']*V
            contributions=weights*M[batch,v,j]
            # C-order broadcasting traverses pair then original (left edge,right edge).
            # Each Q destination receives exactly its original ordered additions.
            np.add.at(Q,(batch,u,i),contributions)
            np.multiply(Q,np.asarray(betas)[:,None,None],out=M)
            M-=logsumexp(M,axis=2,keepdims=True)
            M-=logsumexp(M,axis=1,keepdims=True)
            np.exp(M,out=M)
            for p in active:
                betas[p]*=1+config['beta_rate'];iterations[p]+=1
                if trace:history[p].append((M[p].copy(),Q[p].copy(),betas[p],iterations[p]))
            active=[p for p in active if betas[p]<=config['beta_final'] and iterations[p]<config['max_iterations']]
        results=[]
        for p,((a,b),state) in enumerate(zip(pairs,states,strict=True)):
            inner=state['annealing'];inner['V'][:]=V[p];inner['M'][:]=M[p];inner['Q'][:]=Q[p]
            inner.update(beta=betas[p],iterations=iterations[p],phase='outer',cursor=0,safe=True)
            # Original engine validates final numeric state and performs hardening/objective.
            while state['phase']!='done':engine.advance(state,a,b,config,max_operations=1000000)
            results.append(engine.result(state,a,b,config))
        arrays=[V,Q,M,weights,u,v,i,j,batch,contributions]
        return results,history,{'route':'batched_prototype','iterations':iterations,'explicit_arrays_bytes':sum(x.nbytes for x in arrays),'operation_checkpoint_compatible':False}
    finally:
        for state in states:engine.close(state)

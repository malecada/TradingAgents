"""Float64 scalar transcription of rendered Algorithm1 and Eq1.

The displayed half coefficient is retained; this is NOT asserted to be the exact
Eq2 derivative. See study PROTOCOL.md for rectangular and isolated-node semantics.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from scipy.special import logsumexp
from .contracts import validate_attributed


@dataclass(frozen=True)
class MatchResult:
    assignment: np.ndarray
    score: float
    convergence: str
    iterations: int
    soft_assignment: np.ndarray | None = None


def validate_pair(left,right,config):
    validate_attributed(left);validate_attributed(right)
    n,m=len(left.node_ids),len(right.node_ids)
    if not n or not m:raise ValueError('empty graph has undefined matching')
    if n*m>config['max_pair_entries']:raise ValueError('matching capacity exceeded')
    if left.node_features.shape[1]!=right.node_features.shape[1] or left.edge_features.shape[1]!=right.edge_features.shape[1]:raise ValueError('attribute dimensions mismatch')
    if not left.node_features.shape[1] or not left.edge_features.shape[1]:raise ValueError('empty attribute dimension')
    if not 0<config['beta0']<=config['beta_final'] or config['beta_rate']<=0 or config['alpha']<0:raise ValueError('invalid matching schedule')
    if config['normalization_iterations']!=1 or config['solver']!='algorithm1_literal':raise ValueError('unsupported solver variant')


def agreement(a,b):
    return math.exp(-math.fsum((float(x)-float(y))**2 for x,y in zip(a,b,strict=True))/len(a))


def harden(matrix):
    matrix=np.asarray(matrix)
    if matrix.ndim!=2 or not np.isfinite(matrix).all():raise ValueError('invalid soft assignment')
    work=matrix.astype(np.float64,copy=True)
    out=np.zeros(work.shape,dtype=np.int8)
    for _ in range(min(work.shape)):
        u,i=np.unravel_index(np.argmax(work),work.shape)
        out[u,i]=1;work[u,:]=-np.inf;work[:,i]=-np.inf
    return out


def score_assignment(left,right,assignment,config):
    validate_pair(left,right,config)
    n,m=len(left.node_ids),len(right.node_ids)
    M=np.asarray(assignment)
    if M.shape!=(n,m) or not np.isin(M,[0,1]).all() or (M.sum(0)>1).any() or (M.sum(1)>1).any():raise ValueError('infeasible hard assignment')
    node=math.fsum(float(M[u,i])*agreement(left.node_features[u],right.node_features[i]) for u in range(n) for i in range(m))/math.sqrt(n*m)
    terms=(float(M[u,i])*float(M[v,j])*agreement(left.edge_features[k],right.edge_features[l])
           for k,(u,v) in enumerate(left.edge_index.T)
           for l,(i,j) in enumerate(right.edge_index.T))
    l1,l2=left.edge_index.shape[1],right.edge_index.shape[1]
    edge=math.fsum(terms)/(2*math.sqrt(l1*l2)) if l1*l2 else 0.
    return (edge+config['alpha']*node)/(1+config['alpha'])


def match_reference(left,right,config):
    validate_pair(left,right,config)
    n,m=len(left.node_ids),len(right.node_ids)
    V=np.array([[agreement(a,b) for b in right.node_features] for a in left.node_features],dtype=np.float64)
    M=V.copy()  # Algorithm1 line4: node agreement, despite source s1/s2 swap.
    beta=config['beta0'];iterations=0
    while beta<=config['beta_final'] and iterations<config['max_iterations']:
        Q=config['alpha']*V
        # Literal line7, not a derivative correction or normalized Eq1 gradient.
        for k,(u,v) in enumerate(left.edge_index.T):
            for l,(i,j) in enumerate(right.edge_index.T):
                Q[u,i]+=.5*agreement(left.edge_features[k],right.edge_features[l])*M[v,j]
        log_M=beta*Q                           # line8 exp, evaluated in log space
        log_M-=logsumexp(log_M,axis=1,keepdims=True)  # line10 row normalization
        log_M-=logsumexp(log_M,axis=0,keepdims=True)  # line11 column normalization
        M=np.exp(log_M)
        beta*=1+config['beta_rate']             # line12 multiplicative schedule
        iterations+=1
    assignment=harden(M)                      # line14 greedy injective hardening
    return MatchResult(assignment,score_assignment(left,right,assignment,config),
                       'temperature_complete' if beta>config['beta_final'] else 'iteration_cap',iterations,M.copy())

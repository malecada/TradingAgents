"""Literal float64 reference Eq1 score without a dense hard-assignment matrix.

Graph/pair inputs, graph validation internals and Python/runtime allocations are
outside the numeric scratch allowance. The frozen pair-capacity check still runs.
Acceptance is restricted to a checked conservative representable-agreement
envelope, narrower than finite graph attributes. This prototype is not substituted for the accelerated Torch reduction path.
"""
import math
import sys
import numpy as np
from tradingagents.research.onchain_replication.matching_reference import agreement,validate_pair


def check_agreement_domain(left, right):
    """Conservative componentwise envelope; explicitly narrower than finite inputs.

    Reject if any squared difference or their envelope sum cannot be represented
    by float64 scalar arithmetic. No per-attribute array is allocated. Correlated
    extrema can cause conservative rejection even when all actual pairs are safe.
    """
    def squares():
        for column in range(left.shape[1]):
            low_left, high_left = float(left[:, column].min()), float(left[:, column].max())
            low_right, high_right = float(right[:, column].min()), float(right[:, column].max())
            delta = max(abs(high_left-low_right), abs(high_right-low_left))
            if not math.isfinite(delta) or delta > math.sqrt(sys.float_info.max):
                raise ValueError('agreement arithmetic domain exceeds representable envelope')
            yield delta ** 2
    try:
        bound = math.fsum(squares())
    except OverflowError as exc:
        raise ValueError('agreement arithmetic domain exceeds representable envelope') from exc
    if not math.isfinite(bound):
        raise ValueError('agreement arithmetic domain exceeds representable envelope')


def score_indices(left,right,pairs,config,*,max_buffer_bytes,chunk_edges=65536):
    if type(max_buffer_bytes) is not int or max_buffer_bytes<=0 or type(chunk_edges) is not int or chunk_edges<=0:raise ValueError('positive numeric scratch bounds required')
    if not isinstance(pairs,np.ndarray) or pairs.ndim!=2 or pairs.shape[1]!=2 or pairs.dtype!=np.dtype(np.int64):raise ValueError('int64 assignment pairs required')
    count=len(pairs);right_edges=right.edge_index.shape[1]
    required=64*count+32*min(chunk_edges,right_edges)
    if required>max_buffer_bytes:raise ValueError('sparse score numeric scratch allowance exceeded')
    validate_pair(left,right,config)
    n,m=len(left.node_ids),len(right.node_ids)
    if count>min(n,m) or (pairs<0).any() or (pairs[:,0]>=n).any() or (pairs[:,1]>=m).any():raise ValueError('infeasible assignment pairs')
    if len(np.unique(pairs[:,0]))!=count or len(np.unique(pairs[:,1]))!=count:raise ValueError('non-injective assignment pairs')
    check_agreement_domain(left.node_features,right.node_features)
    if left.edge_index.shape[1] and right_edges:
        check_agreement_domain(left.edge_features,right.edge_features)
    order=np.argsort(pairs[:,0],kind='stable');rows=pairs[order,0];columns=pairs[order,1];del order
    # Row ordering and right-edge ordering match the scalar oracle after zero
    # terms are removed. Nonzero terms and math.fsum arithmetic are unchanged.
    node=math.fsum(agreement(left.node_features[u],right.node_features[i]) for u,i in zip(rows,columns,strict=True))/math.sqrt(n*m)
    def destination(node):
        pos=int(np.searchsorted(rows,node))
        return int(columns[pos]) if pos<count and rows[pos]==node else None
    def terms():
        for k,(u,v) in enumerate(left.edge_index.T):
            i,j=destination(u),destination(v)
            if i is None or j is None:continue
            for start in range(0,right_edges,chunk_edges):
                stop=min(right_edges,start+chunk_edges)
                mask=(right.edge_index[0,start:stop]==i)&(right.edge_index[1,start:stop]==j)
                for offset in np.flatnonzero(mask):
                    yield agreement(left.edge_features[k],right.edge_features[start+int(offset)])
    left_edges=left.edge_index.shape[1]
    edge=math.fsum(terms())/(2*math.sqrt(left_edges*right_edges)) if left_edges*right_edges else 0.
    return (edge+config['alpha']*node)/(1+config['alpha'])

"""Uninstalled small-pair normalization prototype; no authority/checkpoint API."""
import ctypes
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication import matching_reference as original
_lib=ctypes.CDLL(str(Path(__file__).with_name('normalization.so')))
_ptr=ctypes.POINTER(ctypes.c_double)
_lib.normalize.argtypes=[_ptr,_ptr,ctypes.c_int,ctypes.c_int,ctypes.c_double]
_lib.normalize.restype=ctypes.c_int
def normalize(Q,beta):
    if type(Q)is not np.ndarray or Q.dtype!=np.float64 or not Q.flags.c_contiguous or Q.ndim!=2:raise ValueError('exact contiguous float64 matrix required')
    if not all(1<=d<=32 for d in Q.shape):raise ValueError('small pair domain exceeded')
    M=np.empty_like(Q)
    if _lib.normalize(Q.ctypes.data_as(_ptr),M.ctypes.data_as(_ptr),*Q.shape,beta):raise ValueError('unsupported normalization input/rounding')
    return M

def match(left,right,config):
    original.validate_pair(left,right,config)
    n,m=len(left.node_ids),len(right.node_ids)
    if not (1<=n<=32 and 1<=m<=32):raise ValueError('small pair domain exceeded')
    V=np.array([[original.agreement(a,b) for b in right.node_features] for a in left.node_features],dtype=np.float64)
    M=V.copy();beta=config['beta0'];iterations=0
    while beta<=config['beta_final'] and iterations<config['max_iterations']:
        Q=config['alpha']*V
        for k,(u,v) in enumerate(left.edge_index.T):
            for l,(i,j) in enumerate(right.edge_index.T):
                Q[u,i]+=.5*original.agreement(left.edge_features[k],right.edge_features[l])*M[v,j]
        M=normalize(Q,beta)
        beta*=1+config['beta_rate'];iterations+=1
    assignment=original.harden(M)
    return original.MatchResult(assignment,original.score_assignment(left,right,assignment,config),
        'temperature_complete' if beta>config['beta_final'] else 'iteration_cap',iterations,M.copy())

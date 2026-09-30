"""Isolated C-order scalar normalization with successful-return safe points.

Q must remain immutable and exclusively owned by the caller throughout. Only
create-generated scratch states are supported. This is not a durable checkpoint
format or an empirically admitted replacement. It preserves pinned SciPy's
formula; a singleton column block is duplicated to preserve its reduction layout.

One dense output costs 8*n*m retained bytes, excluding Q and caller references.
max_chunk_entries bounds the input elements of one native normalization call,
INCLUDING singleton padding. SciPy makes several temporaries; this is neither an
RSS bound nor a wall-time bound. Creation performs full input validation.
"""
import math
import numpy as np
from scipy.special import logsumexp


def create(q,beta,*,max_chunk_entries,max_state_bytes):
    if (not isinstance(q,np.ndarray) or q.ndim!=2 or q.dtype!=np.float64
            or not q.flags.c_contiguous or not all(q.shape)
            or not np.isfinite(q).all() or np.any(q<0)):
        raise ValueError('finite nonnegative C-order float64 matrix required')
    if isinstance(beta,bool) or not isinstance(beta,(int,float)) or not math.isfinite(beta) or beta<=0:
        raise ValueError('positive finite temperature required')
    n,m=q.shape
    minimum=max(m,n if m==1 else 2*n)
    if type(max_chunk_entries) is not int or max_chunk_entries<minimum:
        raise ValueError('capacity for a complete reduction axis and singleton padding required')
    if type(max_state_bytes) is not int or max_state_bytes<q.nbytes:
        raise ValueError('retained output allowance exceeded')
    if beta>1 and float(q.max())>np.finfo(np.float64).max/beta:
        raise ValueError('scaled matrix would overflow')
    return {'q':q,'matrix':np.zeros(q.shape,dtype=np.float64),'beta':beta,
            'max_chunk_entries':max_chunk_entries,'phase':'scale','cursor':0,'safe':True}


def advance(state,*,max_blocks):
    if type(max_blocks) is not int or max_blocks<=0 or state['safe'] is not True:
        raise ValueError('safe state and positive block budget required')
    q=state['q'];a=state['matrix'];n,m=q.shape;cap=state['max_chunk_entries']
    phase=state['phase'];limit={'scale':n*m,'rows':n,'columns':m,'exp':n*m,'done':0}
    if phase not in limit or type(state['cursor']) is not int or (phase=='done' and state['cursor']!=0) or (phase!='done' and not 0<=state['cursor']<limit[phase]):
        raise ValueError('unreachable normalization cursor')
    used=0;state['safe']=False
    try:
        while used<max_blocks and state['phase']!='done':
            phase=state['phase'];start=state['cursor']
            if phase in ('scale','exp'):
                end=min(n*m,start+cap);target=a.reshape(-1)[start:end]
                if phase=='scale':np.multiply(q.reshape(-1)[start:end],state['beta'],out=target)
                else:np.exp(target,out=target)
                next_phase='rows' if phase=='scale' else 'done'
            elif phase=='rows':
                end=min(n,start+max(1,cap//m));block=a[start:end]
                block-=logsumexp(block,axis=1,keepdims=True)
                next_phase='columns'
            else:
                end=min(m,start+max(1,cap//n));block=a[:,start:end]
                if block.shape[1]==1 and m>1:
                    padded=np.repeat(block,2,axis=1)
                    values=logsumexp(padded,axis=0,keepdims=True)[:,:1]
                    block-=values
                else:
                    block-=logsumexp(block,axis=0,keepdims=True)
                next_phase='exp'
            state['cursor']=end;used+=1
            if end==limit[phase]:state.update(phase=next_phase,cursor=0)
        state['safe']=True
        return used
    except BaseException:
        state['safe']=False
        raise

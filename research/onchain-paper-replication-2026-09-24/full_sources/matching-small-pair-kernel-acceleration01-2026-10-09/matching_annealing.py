"""Isolated scalar annealing state machine; no registered/accelerated substitution.

Retained numeric state is three dense float64 matrices. Input validation, identity
hashing, normalization temporaries, hardening/scoring and caller-held old states
are excluded from that bound. Initialization, validation and remaining atomic transforms are not wall-time bounded
here; any production integration needs an outer guard and execution admission.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import numpy as np
import sys
from . import checkpoint_chunks as chunks
from scipy.special import logsumexp
from tradingagents.research.onchain_replication.matching_reference import validate_pair,agreement,harden,score_assignment,MatchResult
from . import matching_identity as typed_identity
graph_hash=typed_identity.graph_identity

# Local-call reuse only under the frozen scientific runtime and round-to-nearest.
from .contracts import AttributedGraph
import builtins
try:
    import ctypes
    _nearest_rounding = ctypes.CDLL(None).fegetround
    _nearest_rounding.argtypes = []
    _nearest_rounding.restype = ctypes.c_int
except (AttributeError, OSError):
    _nearest_rounding = None
_AGREEMENT_ORIGINAL = agreement
_AGREEMENT_CODE = agreement.__code__
_AGREEMENT_MATH = (math.exp, math.fsum)
_BUILTINS_ORIGINAL = (float,zip,len)
_NUMPY_ORIGINAL = (np.exp,np.multiply,np.add,np.empty,np.zeros,np.repeat,np.any)
_NORMALIZATION_ORIGINAL = logsumexp
_NORMALIZATION_CODE = logsumexp.__code__



# Specialization of the pinned SciPy public wrapper for this kernel's real,
# nonempty float64 matrices. All floating operations remain in original order.
from scipy._lib.array_api_compat import numpy as _normalization_xp
_NORMALIZATION_INNER = logsumexp.__globals__['_logsumexp']
_NORMALIZATION_INNER_CODE = _NORMALIZATION_INNER.__code__

def _matrix_logsumexp(a, *, axis, keepdims):
    if (type(a) is not np.ndarray or a.dtype != np.float64 or a.ndim != 2
            or not a.size or axis not in (0, 1) or keepdims is not True
            or logsumexp is not _NORMALIZATION_ORIGINAL
            or logsumexp.__code__ is not _NORMALIZATION_CODE
            or logsumexp.__globals__.get('_logsumexp') is not _NORMALIZATION_INNER
            or _NORMALIZATION_INNER.__code__ is not _NORMALIZATION_INNER_CODE):
        return logsumexp(a, axis=axis, keepdims=keepdims)
    xp = _normalization_xp
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        b_exp_a = xp.exp(a)
        sum_ = xp.sum(b_exp_a, axis=axis, keepdims=True)
        out_inf = xp.log(sum_)
    with np.errstate(divide='ignore', invalid='ignore'):
        out, sgn = _NORMALIZATION_INNER(a, None, axis=axis, return_sign=False, xp=xp)
    out_finite = xp.isfinite(out)
    return xp.where(out_finite, out, out_inf)

def _immutable_edges(graph):
    if type(graph) is not AttributedGraph:return False
    array=graph.edge_features
    if type(array) is not np.ndarray or array.dtype!=np.float64 or not array.flags.c_contiguous:return False
    for _ in range(4):
        if type(array) is bytes:return True
        if type(array) is not np.ndarray or array.flags.writeable:return False
        array=array.base
    return False


def _reuse_runtime():
    return (agreement is _AGREEMENT_ORIGINAL and agreement.__code__ is _AGREEMENT_CODE
            and (math.exp,math.fsum)==_AGREEMENT_MATH
            and (builtins.float,builtins.zip,builtins.len)==_BUILTINS_ORIGINAL
            and (np.exp,np.multiply,np.add,np.empty,np.zeros,np.repeat,np.any)==_NUMPY_ORIGINAL
            and agreement.__globals__.get('math') is math
            and not any(name in agreement.__globals__ for name in ('float','zip','len'))
            and logsumexp is _NORMALIZATION_ORIGINAL and logsumexp.__code__ is _NORMALIZATION_CODE
            and _nearest_rounding is not None and _nearest_rounding()==0
            and sys.gettrace() is None and sys.getprofile() is None)

NAMES=('V','M','Q')
META={'schema_version','identity','phase','cursor','iterations','beta','shape','safe','max_chunk_entries'}
NORMALIZATION=('normalize_scale','normalize_rows','normalize_columns','normalize_exp')


def body(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()

def identity(a,b,c):
    return {'left':graph_hash(a),'right':graph_hash(b),'configuration':hashlib.sha256(body(c)).hexdigest()}

_IDENTITY_ORIGINAL = identity

# Same-call validation reuse only; all graph bytes are still freshly hashed.
_PAIR_VALIDATOR = validate_pair
_PAIR_CODE = validate_pair.__code__
_GRAPH_VALIDATOR = typed_identity.validate_attributed
_GRAPH_VALIDATOR_CODE = _GRAPH_VALIDATOR.__code__
_GRAPH_IDENTITY = graph_hash
_GRAPH_IDENTITY_CODE = graph_hash.__code__

def _identity_after_pair_validation(a,b,c):
    eligible=(type(c) is dict and all(type(k) is str and type(v) in (str,int,float,bool) for k,v in c.items())
              and validate_pair is _PAIR_VALIDATOR and validate_pair.__code__ is _PAIR_CODE
              and validate_pair.__globals__.get('validate_attributed') is _GRAPH_VALIDATOR
              and typed_identity.validate_attributed is _GRAPH_VALIDATOR
              and _GRAPH_VALIDATOR.__code__ is _GRAPH_VALIDATOR_CODE
              and graph_hash is _GRAPH_IDENTITY and graph_hash.__code__ is _GRAPH_IDENTITY_CODE
              and identity is _IDENTITY_ORIGINAL)
    if eligible:
        for graph in (a,b):
            if (type(graph) is not AttributedGraph or type(graph.node_ids) is not tuple
                    or any(type(node) is not str for node in graph.node_ids)
                    or type(graph.parent_hash) is not str or type(graph.center_id) is not str):
                eligible=False;break
            for name in ('node_features','edge_index','edge_features'):
                array=getattr(graph,name)
                for _ in range(4):
                    if type(array) is bytes:break
                    if type(array) is not np.ndarray or array.flags.writeable:
                        eligible=False;break
                    array=array.base
                else:eligible=False
                if not eligible:break
            if not eligible:break
    if not eligible:return identity(a,b,c)
    return {'left':typed_identity._attributed_identity_checked(a),
            'right':typed_identity._attributed_identity_checked(b),
            'configuration':hashlib.sha256(body(c)).hexdigest()}


def bound(n,m,maximum):
    if type(maximum) is not int or maximum<=0 or 24*n*m>maximum:raise ValueError('retained numeric state allowance exceeded')

def normalization_policy(n,m,cap):
    if type(cap) is not int or cap<max(m,n if m==1 else 2*n):
        raise ValueError('complete reduction axis and singleton padding allowance required')


def create(a,b,c,*,max_state_bytes,max_chunk_entries=65536):
    validate_pair(a,b,c);n,m=len(a.node_ids),len(b.node_ids);bound(n,m,max_state_bytes)
    normalization_policy(n,m,max_chunk_entries)
    return {'max_chunk_entries':max_chunk_entries,'schema_version':3,'safe':True,'identity':identity(a,b,c),'phase':'nodes','cursor':0,'iterations':0,'beta':c['beta0'],'shape':[n,m],
            **{name:np.zeros((n,m),dtype=np.float64) for name in NAMES}}

def check(state,a,b,c):
    validate_pair(a,b,c)
    return _check_state_identity(state,a,b,c,lambda:(_identity_after_pair_validation(a,b,c) if type(state) is dict else identity(a,b,c)))

def _check_state_identity(state,a,b,c,expected_identity):
    """Private mutable-state checks after current exclusive immutable-input proof."""
    if set(state)!=META|set(NAMES) or type(state['schema_version']) is not int or state['schema_version']!=3 or state['safe'] is not True or state['identity']!=expected_identity() or state['shape']!=[len(a.node_ids),len(b.node_ids)]:raise ValueError('matching state identity differs')
    if state['phase'] not in ('nodes','outer','edges','done')+NORMALIZATION:raise ValueError('state phase differs')
    if type(state['iterations']) is not int or not 0<=state['iterations']<=c['max_iterations']:raise ValueError('state iteration differs')
    beta=c['beta0']
    for _ in range(state['iterations']):beta*=1+c['beta_rate']
    if isinstance(state['beta'],bool) or not math.isfinite(state['beta']) or state['beta']<=0 or state['beta']!=beta:raise ValueError('state temperature differs')
    n,m=state['shape'];normalization_policy(n,m,state['max_chunk_entries'])
    limits={'nodes':n*m,'edges':a.edge_index.shape[1]*b.edge_index.shape[1],
            'normalize_scale':n*m,'normalize_rows':n,'normalize_columns':m,'normalize_exp':n*m}
    limit=limits.get(state['phase'],0)
    if type(state['cursor']) is not int or not 0<=state['cursor']<=limit:raise ValueError('state cursor differs')
    eligible=state['beta']<=c['beta_final'] and state['iterations']<c['max_iterations']
    if state['phase']=='nodes' and (state['iterations']!=0 or state['cursor']>=limit):raise ValueError('unreachable node phase')
    if state['phase']=='edges' and (not eligible or (limit>0 and state['cursor']>=limit)):raise ValueError('unreachable edge phase')
    if state['phase'] in NORMALIZATION and (not eligible or state['cursor']>=limit):raise ValueError('unreachable normalization phase')
    if state['phase']=='done' and eligible:raise ValueError('unreachable completion phase')
    for name in NAMES:
        x=state[name]
        if not isinstance(x,np.ndarray) or x.dtype!=np.float64 or list(x.shape)!=state['shape'] or not x.flags.c_contiguous or not np.isfinite(x).all():raise ValueError('state numeric matrix differs')


def advance(state,a,b,c,*,max_operations):
    if type(max_operations) is not int or max_operations<=0:raise ValueError('positive operation budget required')
    check(state,a,b,c)
    return _advance_checked(state,a,b,c,max_operations=max_operations)
def _advance_checked(state,a,b,c,*,max_operations):
    """Private body for an exclusively owned state checked in this same call.

    The caller must validate state, inputs and positive operation budget before
    entry, with no intervening mutation of them or external callback.
    """
    n,m=state['shape'];right_edges=b.edge_index.shape[1];total=a.edge_index.shape[1]*right_edges
    # At most4096float64 weights+4096validity bytes =36864B; no state fields.
    reuse=(0<total<=4096 and max_operations>total and _immutable_edges(a) and _immutable_edges(b)
           and all(type(state[name]) is np.ndarray for name in NAMES) and _reuse_runtime())
    feature_pins=(a.edge_features,b.edge_features);cached=valid=None
    state['safe']=False
    try:
        used=0
        while used<max_operations and state['phase']!='done':
            phase=state['phase']
            if phase=='nodes':
                u,i=divmod(state['cursor'],m)
                state['V'][u,i]=agreement(a.node_features[u],b.node_features[i]);state['cursor']+=1;used+=1
                if state['cursor']==n*m:
                    state['M'][:]=state['V'];state.update(phase='outer',cursor=0)
            elif phase=='outer':
                if reuse and (a.edge_features is not feature_pins[0] or b.edge_features is not feature_pins[1] or not _reuse_runtime()):
                    reuse=False;cached=valid=None
                if state['beta']>c['beta_final'] or state['iterations']>=c['max_iterations']:
                    state['phase']='done';continue
                state['Q'][:]=c['alpha']*state['V'];state.update(phase='edges',cursor=0);used+=1
            elif phase=='edges':
                if state['cursor']==total:state.update(phase='normalize_scale',cursor=0);continue
                # Bounded ordered edge accumulation; no agreement approximation.
                # Keep single-operation and nonstandard error-mode calls scalar.
                count=min(1024,total-state['cursor'],max_operations-used)
                if (count>=8 and a.edge_features.dtype==np.float64 and b.edge_features.dtype==np.float64
                        and np.geterr()['under']=='ignore'
                        and all(mode in ('ignore','warn') for mode in np.geterr().values())):
                    start=state['cursor']
                    positions=np.arange(start,start+count,dtype=np.int64)
                    left,right=np.divmod(positions,right_edges)
                    u,v=a.edge_index[:,left];i,j=b.edge_index[:,right]
                    old_values=state['M'][v,j]
                    # Per-chunk proof domain: each product has magnitude <=.5;
                    # at most 1024 additions start from finite |Q|<=1e100.
                    # Overflow/invalid cannot occur; underflow must be ignored.
                    # Outside this domain retain the literal scalar operation.
                    if np.all(np.abs(old_values)<=1.) and np.all(np.abs(state['Q'][u,i])<=1e100):
                        weights=np.empty(count,dtype=np.float64)
                        if reuse and cached is not None and valid[start:start+count].all():
                            # Exact copy only: lazy population and ordered arithmetic remain below.
                            weights[:]=cached[start:start+count]
                        else:
                            try:
                                for offset in range(count):
                                    position=start+offset
                                    if reuse and cached is not None and valid[position]:
                                        weights[offset]=cached[position]
                                    else:
                                        weights[offset]=.5*agreement(a.edge_features[left[offset]],b.edge_features[right[offset]])
                                        if reuse:
                                            if cached is None:
                                                cached=np.empty(total,dtype=np.float64);valid=np.zeros(total,dtype=np.bool_)
                                            cached[position]=weights[offset];valid[position]=True
                            except BaseException:
                                # Reproduce the scalar prefix and cursor on agreement failure.
                                for offset2 in range(offset):
                                    k,l=left[offset2],right[offset2]
                                    u,v=a.edge_index[:,k];i,j=b.edge_index[:,l]
                                    state['Q'][u,i]+=weights[offset2]*state['M'][v,j]
                                    state['cursor']+=1;used+=1
                                raise
                        np.multiply(weights,old_values,out=weights)
                        np.add.at(state['Q'],(u,i),weights)
                        state['cursor']+=count;used+=count
                        if state['cursor']==total:state.update(phase='normalize_scale',cursor=0)
                        continue
                k,l=divmod(state['cursor'],right_edges);u,v=a.edge_index[:,k];i,j=b.edge_index[:,l]
                state['Q'][u,i]+=.5*agreement(a.edge_features[k],b.edge_features[l])*state['M'][v,j]
                state['cursor']+=1;used+=1
                if state['cursor']==total:state.update(phase='normalize_scale',cursor=0)
            elif phase in NORMALIZATION:
                # Q is complete and the old M is no longer needed for edge
                # accumulation. Reuse M as normalization scratch, retaining only
                # V/M/Q rather than allocating a fourth dense state matrix.
                start=state['cursor'];cap=state['max_chunk_entries'];matrix=state['M']
                if phase=='normalize_scale':
                    if start==0 and (np.any(state['Q']<0) or (state['beta']>1 and float(state['Q'].max())>np.finfo(np.float64).max/state['beta'])):
                        raise ValueError('invalid or overflowing normalization input')
                    end=min(n*m,start+cap)
                    np.multiply(state['Q'].reshape(-1)[start:end],state['beta'],out=matrix.reshape(-1)[start:end])
                    limit=n*m;next_phase='normalize_rows'
                elif phase=='normalize_rows':
                    end=min(n,start+max(1,cap//m));block=matrix[start:end]
                    block-=_matrix_logsumexp(block,axis=1,keepdims=True)
                    limit=n;next_phase='normalize_columns'
                elif phase=='normalize_columns':
                    end=min(m,start+max(1,cap//n));block=matrix[:,start:end]
                    if block.shape[1]==1 and m>1:
                        padded=np.repeat(block,2,axis=1)
                        block-=_matrix_logsumexp(padded,axis=0,keepdims=True)[:,:1]
                    else:
                        block-=_matrix_logsumexp(block,axis=0,keepdims=True)
                    limit=m;next_phase='normalize_exp'
                else:
                    end=min(n*m,start+cap)
                    target=matrix.reshape(-1)[start:end];np.exp(target,out=target)
                    limit=n*m;next_phase='outer'
                state['cursor']=end;used+=1
                if end==limit:
                    if phase=='normalize_exp':
                        state['beta']*=1+c['beta_rate'];state['iterations']+=1
                    state.update(phase=next_phase,cursor=0)
        state['safe']=True
        return used
    except BaseException:
        state['safe']=False
        raise



def result(state,a,b,c):
    check(state,a,b,c)
    if state['phase']!='done':raise ValueError('annealing not complete')
    assignment=harden(state['M'])
    return MatchResult(assignment,score_assignment(a,b,assignment,c),'temperature_complete' if state['beta']>c['beta_final'] else 'iteration_cap',state['iterations'],state['M'].copy())


def sync(directory):
    fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def save(state,directory,a,b,c,*,max_checkpoint_bytes,checkpoint_layout=None):
    if checkpoint_layout is not None:return chunks.anneal_save(sys.modules[__name__],state,directory,a,b,c,max_checkpoint_bytes,checkpoint_layout)
    check(state,a,b,c)
    if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes<=0:raise ValueError('positive checkpoint allowance required')
    # Logical bytes only; physical allocation/RSS require the outer owner policy.
    needed=sum(state[name].nbytes for name in NAMES)+65536
    if needed>max_checkpoint_bytes:raise ValueError('checkpoint logical allowance exceeded')
    directory=Path(directory);directory.mkdir(exist_ok=False);sync(directory.parent)
    files={}
    for name in NAMES:
        path=directory/(name+'.npy')
        with path.open('xb') as f:np.save(f,state[name],allow_pickle=False);f.flush();os.fsync(f.fileno())
        files[name]={'sha256':sha(path),'bytes':path.stat().st_size}
    manifest={**{k:state[k] for k in META},'files':files}
    raw=body(manifest)
    if len(raw)>65536 or len(raw)+sum(v['bytes'] for v in files.values())>max_checkpoint_bytes:raise ValueError('checkpoint metadata allowance exceeded')
    with (directory/'manifest.json').open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    sync(directory)
    return hashlib.sha256(raw).hexdigest()


def load(directory,a,b,c,*,expected_sha256,max_state_bytes,max_chunk_entries=65536,checkpoint_layout=None):
    if checkpoint_layout is not None:return chunks.anneal_load(sys.modules[__name__],directory,a,b,c,expected_sha256,max_state_bytes,max_chunk_entries,checkpoint_layout)
    directory=Path(directory);manifest_path=directory/'manifest.json'
    if manifest_path.stat().st_size>65536 or sha(manifest_path)!=expected_sha256:raise ValueError('checkpoint manifest differs')
    meta=json.loads(manifest_path.read_bytes());n,m=len(a.node_ids),len(b.node_ids);validate_pair(a,b,c);bound(n,m,max_state_bytes)
    normalization_policy(n,m,max_chunk_entries)
    if set(meta)!=META|{'files'} or meta['schema_version']!=3 or meta['max_chunk_entries']!=max_chunk_entries or meta['identity']!=identity(a,b,c) or meta['shape']!=[n,m] or set(meta['files'])!=set(NAMES):raise ValueError('checkpoint identity differs')
    for name in NAMES:
        path=directory/(name+'.npy');info=meta['files'][name]
        if path.is_symlink() or path.stat().st_size!=info['bytes'] or path.stat().st_size>8*n*m+10000 or sha(path)!=info['sha256']:raise ValueError('checkpoint array hash/extent differs')
        with path.open('rb') as f:
            if np.lib.format.read_magic(f)!=(1,0):raise ValueError('checkpoint array version differs')
            shape,fortran,dtype=np.lib.format.read_array_header_1_0(f,max_header_size=10000)
            if shape!=(n,m) or dtype!=np.dtype(np.float64) or fortran or f.tell()+8*n*m!=path.stat().st_size:raise ValueError('checkpoint array header differs')
    state={k:meta[k] for k in META}
    state.update({name:np.load(directory/(name+'.npy'),allow_pickle=False) for name in NAMES})
    check(state,a,b,c)
    return state

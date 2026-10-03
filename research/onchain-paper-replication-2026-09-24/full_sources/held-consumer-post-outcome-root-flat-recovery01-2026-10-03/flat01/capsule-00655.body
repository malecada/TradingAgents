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
from . import score_batches as io
import numpy as np
from scipy.special import logsumexp
from tradingagents.research.onchain_replication.matching_reference import validate_pair,agreement,harden,score_assignment,MatchResult
from . import matching_identity as typed_identity
graph_hash=typed_identity.graph_identity

NAMES=('V','M','Q')
META={'schema_version','identity','phase','cursor','iterations','beta','shape','safe','max_chunk_entries'}
NORMALIZATION=('normalize_scale','normalize_rows','normalize_columns','normalize_exp')


def body(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(path):
    h=hashlib.sha256()
    with io._opened(Path(path),'rb') as f:
        for block in iter(lambda:f.read(1024**2),b''):h.update(block)
    return h.hexdigest()

def identity(a,b,c):
    return {'left':graph_hash(a),'right':graph_hash(b),'configuration':hashlib.sha256(body(c)).hexdigest()}

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
    if set(state)!=META|set(NAMES) or type(state['schema_version']) is not int or state['schema_version']!=3 or state['safe'] is not True or state['identity']!=identity(a,b,c) or state['shape']!=[len(a.node_ids),len(b.node_ids)]:raise ValueError('matching state identity differs')
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
    check(state,a,b,c);n,m=state['shape'];right_edges=b.edge_index.shape[1];total=a.edge_index.shape[1]*right_edges
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
                if state['beta']>c['beta_final'] or state['iterations']>=c['max_iterations']:
                    state['phase']='done';continue
                state['Q'][:]=c['alpha']*state['V'];state.update(phase='edges',cursor=0);used+=1
            elif phase=='edges':
                if state['cursor']==total:state.update(phase='normalize_scale',cursor=0);continue
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
                    block-=logsumexp(block,axis=1,keepdims=True)
                    limit=n;next_phase='normalize_columns'
                elif phase=='normalize_columns':
                    end=min(m,start+max(1,cap//n));block=matrix[:,start:end]
                    if block.shape[1]==1 and m>1:
                        padded=np.repeat(block,2,axis=1)
                        block-=logsumexp(padded,axis=0,keepdims=True)[:,:1]
                    else:
                        block-=logsumexp(block,axis=0,keepdims=True)
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
    finally: io._release(lambda: os.close(fd))

def save(state,directory,a,b,c,*,max_checkpoint_bytes):
    check(state,a,b,c)
    if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes<=0:raise ValueError('positive checkpoint allowance required')
    # Logical bytes only; physical allocation/RSS require the outer owner policy.
    needed=sum(state[name].nbytes for name in NAMES)+65536
    if needed>max_checkpoint_bytes:raise ValueError('checkpoint logical allowance exceeded')
    directory=Path(directory);directory.mkdir(exist_ok=False);sync(directory.parent)
    files={}
    for name in NAMES:
        path=directory/(name+'.npy')
        with io._opened(path,'xb') as f:np.save(f,state[name],allow_pickle=False);f.flush();os.fsync(f.fileno())
        files[name]={'sha256':sha(path),'bytes':path.stat().st_size}
    manifest={**{k:state[k] for k in META},'files':files}
    raw=body(manifest)
    if len(raw)>65536 or len(raw)+sum(v['bytes'] for v in files.values())>max_checkpoint_bytes:raise ValueError('checkpoint metadata allowance exceeded')
    with io._opened(directory/'manifest.json','xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    sync(directory)
    return hashlib.sha256(raw).hexdigest()


def load(directory,a,b,c,*,expected_sha256,max_state_bytes,max_chunk_entries=65536):
    directory=Path(directory);manifest_path=directory/'manifest.json'
    if manifest_path.stat().st_size>65536 or sha(manifest_path)!=expected_sha256:raise ValueError('checkpoint manifest differs')
    meta=json.loads(io._read_path(manifest_path,65536));n,m=len(a.node_ids),len(b.node_ids);validate_pair(a,b,c);bound(n,m,max_state_bytes)
    normalization_policy(n,m,max_chunk_entries)
    if set(meta)!=META|{'files'} or meta['schema_version']!=3 or meta['max_chunk_entries']!=max_chunk_entries or meta['identity']!=identity(a,b,c) or meta['shape']!=[n,m] or set(meta['files'])!=set(NAMES):raise ValueError('checkpoint identity differs')
    for name in NAMES:
        path=directory/(name+'.npy');info=meta['files'][name]
        if path.is_symlink() or path.stat().st_size!=info['bytes'] or path.stat().st_size>8*n*m+10000 or sha(path)!=info['sha256']:raise ValueError('checkpoint array hash/extent differs')
        with io._opened(path,'rb') as f:
            if np.lib.format.read_magic(f)!=(1,0):raise ValueError('checkpoint array version differs')
            shape,fortran,dtype=np.lib.format.read_array_header_1_0(f,max_header_size=10000)
            if shape!=(n,m) or dtype!=np.dtype(np.float64) or fortran or f.tell()+8*n*m!=path.stat().st_size:raise ValueError('checkpoint array header differs')
    state={k:meta[k] for k in META}
    for name in NAMES:
        with io._opened(directory/(name+'.npy'),'rb') as stream:
            state[name]=np.load(stream,allow_pickle=False)
    check(state,a,b,c)
    return state

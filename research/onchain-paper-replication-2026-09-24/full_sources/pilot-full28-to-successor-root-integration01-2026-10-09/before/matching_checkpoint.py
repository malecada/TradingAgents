"""Isolated scalar annealing + ranked checkpoints + sparse score finalization.

Caller owns states and input graphs exclusively. Call close before replacing or
discarding a state. Numeric budgets exclude graphs, Python/runtime, allocator,
native sort workspace and I/O scratch; a process guard remains mandatory.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from tradingagents.research.onchain_replication.matching import MatchScore
from . import matching_annealing as ann
from . import matching_hardening as hard
from . import matching_sparse as sparse
from . import checkpoint_chunks as chunks
FIELDS={'version','safe','phase','policy','annealing','hardening','matrix_sha256'}
POLICY_FIELDS={'max_state_bytes','normalization_chunk_entries','hardening_chunk_entries','hardening_buffer_bytes'}
MANIFEST_FIELDS={'version','phase','policy','matrix_sha256','annealing_sha256','hardening_sha256'}
LIMIT=65536


def policy(n,m,c,*,max_state_bytes,normalization_chunk_entries,hardening_chunk_entries,hardening_buffer_bytes):
    ann.normalization_policy(n,m,normalization_chunk_entries)
    hard.policy(n,m,c['max_pair_entries'],hardening_buffer_bytes)
    if type(max_state_bytes) is not int or max_state_bytes<32*n*m:raise ValueError('combined retained numeric state allowance exceeded')
    if type(hardening_chunk_entries) is not int or not 0<hardening_chunk_entries<=65536:raise ValueError('bounded ranked scan allowance required')
    return dict(max_state_bytes=max_state_bytes,normalization_chunk_entries=normalization_chunk_entries,hardening_chunk_entries=hardening_chunk_entries,hardening_buffer_bytes=hardening_buffer_bytes)


def matrix_identity(matrix):
    if matrix.dtype!=np.float64 or not matrix.flags.c_contiguous:raise ValueError('C-order float64 matrix required')
    return hashlib.sha256(memoryview(matrix).cast('B')).hexdigest()


def create(a,b,c,*,max_state_bytes,normalization_chunk_entries=65536,hardening_chunk_entries=65536,hardening_buffer_bytes=80*1024**2):
    n,m=len(a.node_ids),len(b.node_ids)
    p=policy(n,m,c,max_state_bytes=max_state_bytes,normalization_chunk_entries=normalization_chunk_entries,hardening_chunk_entries=hardening_chunk_entries,hardening_buffer_bytes=hardening_buffer_bytes)
    inner=ann.create(a,b,c,max_state_bytes=max_state_bytes-8*n*m,max_chunk_entries=normalization_chunk_entries)
    return dict(version=3,safe=True,phase='annealing',policy=p,annealing=inner,hardening=None,matrix_sha256=None)


def check(s,a,b,c):
    return _check_owned(s,a,b,c,ann.check)

def _check_owned(s,a,b,c,annealing_check):
    """Private state check with an explicit same-call input validator."""
    if not isinstance(s,dict) or set(s)!=FIELDS or type(s['version']) is not int or s['version']!=3 or s['safe'] is not True:raise ValueError('invalid or poisoned ranked composite')
    if not isinstance(s['policy'],dict) or set(s['policy'])!=POLICY_FIELDS:raise ValueError('policy schema differs')
    p=policy(len(a.node_ids),len(b.node_ids),c,**s['policy']);annealing_check(s['annealing'],a,b,c)
    if s['annealing']['max_chunk_entries']!=p['normalization_chunk_entries']:raise ValueError('annealing policy differs')
    if s['phase']=='annealing':
        if s['annealing']['phase']=='done' or s['hardening'] is not None or s['matrix_sha256'] is not None:raise ValueError('unreachable annealing phase')
    elif s['phase'] in ('hardening','done'):
        hard.check(s['hardening']);h=s['hardening'];matrix=s['annealing']['M']
        if (s['annealing']['phase']!='done' or matrix.flags.writeable or h['input_sha256']!=s['matrix_sha256'] or h['shape']!=list(matrix.shape)
            or h['max_pair_entries']!=c['max_pair_entries'] or h['max_explicit_bytes']!=p['hardening_buffer_bytes'] or (s['phase']=='done')!=(h['phase']=='done')):raise ValueError('hardening identity, ownership or policy differs')
    else:raise ValueError('composite phase differs')


def close(s):
    """Invalidate state, release mapped ranking, and drop dense array ownership."""
    s['safe']=False
    try:
        if s.get('hardening') is not None:hard.close(s['hardening'])
    finally:s['annealing']=None


def advance(s,a,b,c,*,max_operations):
    check(s,a,b,c)
    if type(max_operations) is not int or max_operations<=0:raise ValueError('positive operation allowance required')
    return _advance_owned(s,a,b,c,max_operations=max_operations)

def _advance_owned(s,a,b,c,*,max_operations):
    """Private body; composite/input/budget checks precede entry, no callbacks."""
    s['safe']=False
    try:
        used=0
        if s['phase']=='annealing':
            used=ann._advance_checked(s['annealing'],a,b,c,max_operations=max_operations)
            if s['annealing']['phase']=='done':
                matrix=s['annealing']['M'];digest=matrix_identity(matrix)
                h=hard.create(matrix,max_pair_entries=c['max_pair_entries'],max_explicit_bytes=s['policy']['hardening_buffer_bytes'])
                if h['input_sha256']!=digest:raise ValueError('matrix changed during atomic ranking')
                matrix.flags.writeable=False;s.update(phase='hardening',hardening=h,matrix_sha256=digest)
        elif s['phase']=='hardening':
            used=hard.advance(s['hardening'],input_sha256=s['matrix_sha256'],max_entries=min(max_operations,s['policy']['hardening_chunk_entries']))
            if s['hardening']['phase']=='done':s['phase']='done'
        s['safe']=True;return used
    except BaseException:s['safe']=False;raise


def result(s,a,b,c):
    """Dense diagnostic output only; production-scale callers need score_only."""
    check(s,a,b,c)
    if s['phase']!='done':raise ValueError('composite matching incomplete')
    inner=s['annealing'];assignment=np.zeros(inner['M'].shape,dtype=np.int8)
    for u,i in s['hardening']['pairs']:assignment[u,i]=1
    return ann.MatchResult(assignment,ann.score_assignment(a,b,assignment,c),'temperature_complete' if inner['beta']>c['beta_final'] else 'iteration_cap',inner['iterations'],inner['M'].copy())


def score_only(s,a,b,c,*,max_buffer_bytes,chunk_edges=65536):
    if type(max_buffer_bytes) is not int or max_buffer_bytes<=0 or type(chunk_edges) is not int or not 0<chunk_edges<=65536:raise ValueError('positive bounded scoring policy required')
    count=min(len(a.node_ids),len(b.node_ids))
    if 80*count+32*min(chunk_edges,b.edge_index.shape[1])>max_buffer_bytes:raise ValueError('score-only numeric allowance exceeded')
    check(s,a,b,c)
    if s['phase']!='done':raise ValueError('composite matching incomplete')
    pairs=np.asarray(s['hardening']['pairs'],dtype=np.int64).reshape(-1,2)
    score=sparse.score_indices(a,b,pairs,c,max_buffer_bytes=max_buffer_bytes-16*count,chunk_edges=chunk_edges)
    inner=s['annealing'];return MatchScore(score,'temperature_complete' if inner['beta']>c['beta_final'] else 'iteration_cap',inner['iterations'])


def save(s,directory,a,b,c,*,max_checkpoint_bytes,checkpoint_layout=None):
    if checkpoint_layout is not None:return _save_sharded(s,directory,a,b,c,max_checkpoint_bytes,checkpoint_layout)
    check(s,a,b,c);n,m=len(a.node_ids),len(b.node_ids)
    hard_allowance=8*n*m+128+LIMIT
    # Three dense headers, one rank header and three bounded manifests.
    needed=32*n*m+512+3*LIMIT
    if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes<needed:raise ValueError('combined logical checkpoint allowance exceeded')
    if s['hardening'] is not None:
        meta={k:v for k,v in s['hardening'].items() if k!='order'}
        if len(hard.body(meta|{'order_sha256':'0'*64,'order_bytes':8*n*m+128}))>LIMIT:raise ValueError('hardening metadata allowance exceeded')
    directory=Path(directory);directory.mkdir(exist_ok=False);ann.sync(directory.parent)
    inner_sha=ann.save(s['annealing'],directory/'annealing',a,b,c,max_checkpoint_bytes=max_checkpoint_bytes-hard_allowance-LIMIT)
    hard_sha=None
    if s['hardening'] is not None:hard_sha=hard.save(s['hardening'],directory/'hardening',max_checkpoint_bytes=hard_allowance)
    meta={k:s[k] for k in ('version','phase','policy','matrix_sha256')};meta.update(annealing_sha256=inner_sha,hardening_sha256=hard_sha);raw=ann.body(meta)
    if len(raw)>LIMIT:raise ValueError('outer manifest allowance exceeded')
    with (directory/'manifest.json').open('xb') as f:f.write(raw);f.flush();ann.os.fsync(f.fileno())
    ann.sync(directory);return hashlib.sha256(raw).hexdigest()


def load(directory,a,b,c,*,expected_sha256,max_state_bytes,normalization_chunk_entries=65536,hardening_chunk_entries=65536,hardening_buffer_bytes=80*1024**2,checkpoint_layout=None):
    if checkpoint_layout is not None:return _load_sharded(directory,a,b,c,expected_sha256,max_state_bytes,normalization_chunk_entries,hardening_chunk_entries,hardening_buffer_bytes,checkpoint_layout)
    directory=Path(directory);manifest=directory/'manifest.json'
    if directory.is_symlink() or manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size>LIMIT or ann.sha(manifest)!=expected_sha256:raise ValueError('outer manifest identity differs')
    meta=json.loads(manifest.read_bytes());n,m=len(a.node_ids),len(b.node_ids)
    p=policy(n,m,c,max_state_bytes=max_state_bytes,normalization_chunk_entries=normalization_chunk_entries,hardening_chunk_entries=hardening_chunk_entries,hardening_buffer_bytes=hardening_buffer_bytes)
    if not isinstance(meta,dict) or set(meta)!=MANIFEST_FIELDS or type(meta['version']) is not int or meta['version']!=3 or meta['policy']!=p or meta['phase'] not in ('annealing','hardening','done'):raise ValueError('outer schema or policy differs')
    if meta['phase']=='annealing' and (meta['hardening_sha256'] is not None or meta['matrix_sha256'] is not None):raise ValueError('unexpected pre-ranking metadata')
    h=None
    try:
        if meta['phase']!='annealing':h=hard.load(directory/'hardening',expected_sha256=meta['hardening_sha256'],input_sha256=meta['matrix_sha256'],max_pair_entries=c['max_pair_entries'],max_explicit_bytes=hardening_buffer_bytes)
        inner=ann.load(directory/'annealing',a,b,c,expected_sha256=meta['annealing_sha256'],max_state_bytes=max_state_bytes-8*n*m,max_chunk_entries=normalization_chunk_entries)
        if h is not None:
            if matrix_identity(inner['M'])!=meta['matrix_sha256']:raise ValueError('restored ranked matrix identity differs')
            inner['M'].flags.writeable=False
        s=dict(version=3,safe=True,phase=meta['phase'],policy=p,annealing=inner,hardening=h,matrix_sha256=meta['matrix_sha256']);check(s,a,b,c);return s
    except BaseException as error:
        if h is not None:
            try:hard.close(h)
            except BaseException as cleanup_error:error.add_note('Ranked-state cleanup also failed: '+type(cleanup_error).__name__)
        raise


def _save_sharded(s,directory,a,b,c,maximum,selected):
    selected=chunks.layout(selected);check(s,a,b,c);n,m=len(a.node_ids),len(b.node_ids)
    array_bytes=chunks.describe([n,m],'<f8',selected,'M')['bytes']
    hard_allowance=array_bytes+LIMIT
    needed=4*array_bytes+3*LIMIT
    chunks.need(type(maximum) is int and maximum>=needed,'sharded composite checkpoint allowance exceeded')
    directory=Path(directory);directory.mkdir(exist_ok=False);ann.sync(directory.parent)
    inner_sha=ann.save(s['annealing'],directory/'annealing',a,b,c,max_checkpoint_bytes=maximum-hard_allowance-LIMIT,checkpoint_layout=selected)
    hard_sha=None
    if s['hardening'] is not None:
        hard_sha=hard.save(s['hardening'],directory/'hardening',max_checkpoint_bytes=hard_allowance,checkpoint_layout=selected)
    meta={k:s[k] for k in ('version','phase','policy','matrix_sha256')}
    meta.update(annealing_sha256=inner_sha,hardening_sha256=hard_sha,checkpoint_layout=selected)
    return chunks.manifest(directory,meta)


def _load_sharded(directory,a,b,c,expected,maximum,normalization,hard_chunk,hard_buffer,selected):
    selected=chunks.layout(selected);directory=Path(directory);meta=chunks.metadata(directory,expected)
    n,m=len(a.node_ids),len(b.node_ids)
    p=policy(n,m,c,max_state_bytes=maximum,normalization_chunk_entries=normalization,hardening_chunk_entries=hard_chunk,hardening_buffer_bytes=hard_buffer)
    chunks.need(set(meta)==MANIFEST_FIELDS|{'checkpoint_layout'} and type(meta['version']) is int and meta['version']==3
        and meta['checkpoint_layout']==selected and meta['policy']==p and meta['phase'] in ('annealing','hardening','done'),'sharded composite identity differs')
    if meta['phase']=='annealing':chunks.need(meta['hardening_sha256'] is None and meta['matrix_sha256'] is None,'sharded pre-ranking identity differs')
    names={'manifest.json','annealing'}|({'hardening'} if meta['phase']!='annealing' else set())
    chunks.need(directory.resolve()==directory and {p.name for p in directory.iterdir()}==names,'sharded composite inventory differs')
    h=None
    try:
        if meta['phase']!='annealing':
            h=hard.load(directory/'hardening',expected_sha256=meta['hardening_sha256'],input_sha256=meta['matrix_sha256'],max_pair_entries=c['max_pair_entries'],max_explicit_bytes=hard_buffer,checkpoint_layout=selected)
        inner=ann.load(directory/'annealing',a,b,c,expected_sha256=meta['annealing_sha256'],max_state_bytes=maximum-8*n*m,max_chunk_entries=normalization,checkpoint_layout=selected)
        if h is not None:
            chunks.need(matrix_identity(inner['M'])==meta['matrix_sha256'],'sharded restored matrix differs')
            inner['M'].flags.writeable=False
        state=dict(version=3,safe=True,phase=meta['phase'],policy=p,annealing=inner,hardening=h,matrix_sha256=meta['matrix_sha256'])
        check(state,a,b,c);return state
    except BaseException as error:
        if h is not None:
            try:hard.close(h)
            except BaseException as failure:error.add_note('Sharded rank cleanup also failed: '+type(failure).__name__)
        raise

"""Isolated annealing and greedy-hardening checkpoint composition.

States and inputs must remain exclusively owned and unmodified by the caller.
Read-only M prevents accidental writes, not hostile alias mutation. Identity
hashing, component checks, publication and final scoring remain atomic. The
numeric allowances are component bounds, not whole-process RSS guarantees.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import numpy as np

HERE = Path(__file__).resolve().parent


def component(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ann = component('isolated_annealing', HERE.with_name('matching-normalization-checkpoints-2026-09-30')/'annealing.py')
hard = component('isolated_hardening', HERE.with_name('hardening-checkpoints-2026-09-30')/'resume.py')
FIELDS = {'version', 'safe', 'phase', 'policy', 'annealing', 'hardening', 'matrix_sha256'}
POLICY_FIELDS = {'normalization_chunk_entries', 'hardening_chunk_entries', 'hardening_buffer_bytes'}
MANIFEST_FIELDS = {'version', 'phase', 'policy', 'matrix_sha256', 'annealing_sha256', 'hardening_sha256'}


def policy(n, m, normalization_chunk_entries, hardening_chunk_entries, hardening_buffer_bytes):
    ann.normalization_policy(n, m, normalization_chunk_entries)
    if (type(hardening_chunk_entries) is not int or not 0 < hardening_chunk_entries <= 65536
            or type(hardening_buffer_bytes) is not int
            or hardening_buffer_bytes < 48*min(n,m)+64*min(hardening_chunk_entries,n*m)):
        raise ValueError('hardening numeric policy allowance exceeded')
    return dict(normalization_chunk_entries=normalization_chunk_entries,
                hardening_chunk_entries=hardening_chunk_entries,
                hardening_buffer_bytes=hardening_buffer_bytes)


def matrix_identity(matrix):
    if matrix.dtype != np.float64 or not matrix.flags.c_contiguous:
        raise ValueError('C-order float64 assignment required')
    return hashlib.sha256(memoryview(matrix).cast('B')).hexdigest()


def create(a, b, c, *, max_state_bytes, normalization_chunk_entries=65536,
           hardening_chunk_entries=65536, hardening_buffer_bytes=8*1024**2):
    p = policy(len(a.node_ids),len(b.node_ids),normalization_chunk_entries,
               hardening_chunk_entries,hardening_buffer_bytes)
    inner = ann.create(a,b,c,max_state_bytes=max_state_bytes,max_chunk_entries=normalization_chunk_entries)
    return dict(version=1,safe=True,phase='annealing',policy=p,annealing=inner,
                hardening=None,matrix_sha256=None)


def check(s,a,b,c):
    if set(s)!=FIELDS or type(s['version']) is not int or s['version']!=1 or s['safe'] is not True:
        raise ValueError('invalid or poisoned composite state')
    if not isinstance(s['policy'],dict) or set(s['policy'])!=POLICY_FIELDS:
        raise ValueError('composite policy differs')
    p=policy(len(a.node_ids),len(b.node_ids),**s['policy'])
    ann.check(s['annealing'],a,b,c)
    if s['annealing']['max_chunk_entries']!=p['normalization_chunk_entries']:
        raise ValueError('annealing policy differs')
    if s['phase']=='annealing':
        if s['annealing']['phase']=='done' or s['hardening'] is not None or s['matrix_sha256'] is not None:
            raise ValueError('unreachable annealing composite state')
    elif s['phase'] in ('hardening','done'):
        hard.check(s['hardening'])
        h=s['hardening'];matrix=s['annealing']['M']
        if (s['annealing']['phase']!='done' or matrix.flags.writeable
                or h['input_sha256']!=s['matrix_sha256'] or h['shape']!=list(matrix.shape)
                or h['dtype']!=matrix.dtype.str or h['chunk_entries']!=p['hardening_chunk_entries']
                or h['max_buffer_bytes']!=p['hardening_buffer_bytes']
                or (s['phase']=='done')!=(h['phase']=='done')):
            raise ValueError('hardening ownership, identity or policy differs')
    else:
        raise ValueError('composite phase differs')


def advance(s,a,b,c,*,max_operations):
    check(s,a,b,c)
    if type(max_operations) is not int or max_operations<=0:
        raise ValueError('positive operation allowance required')
    s['safe']=False
    try:
        used=0
        if s['phase']=='annealing':
            used=ann.advance(s['annealing'],a,b,c,max_operations=max_operations)
            if s['annealing']['phase']=='done':
                matrix=s['annealing']['M'];digest=matrix_identity(matrix)
                h=hard.create(matrix,input_sha256=digest,
                              chunk_entries=s['policy']['hardening_chunk_entries'],
                              max_buffer_bytes=s['policy']['hardening_buffer_bytes'])
                matrix.flags.writeable=False
                s.update(phase='hardening',hardening=h,matrix_sha256=digest)
        elif s['phase']=='hardening':
            used=hard.advance(s['hardening'],s['annealing']['M'],
                              input_sha256=s['matrix_sha256'],max_chunks=max_operations)
            if s['hardening']['phase']=='done':s['phase']='done'
        s['safe']=True
        return used
    except BaseException:
        s['safe']=False
        raise


def result(s,a,b,c):
    check(s,a,b,c)
    if s['phase']!='done':raise ValueError('composite matching is incomplete')
    inner=s['annealing'];assignment=np.zeros(inner['M'].shape,dtype=np.int8)
    for u,i in s['hardening']['pairs']:assignment[u,i]=1
    return ann.MatchResult(assignment,ann.score_assignment(a,b,assignment,c),
                           'temperature_complete' if inner['beta']>c['beta_final'] else 'iteration_cap',
                           inner['iterations'],inner['M'].copy())


def save(s,directory,a,b,c,*,max_checkpoint_bytes):
    check(s,a,b,c)
    needed=sum(s['annealing'][n].nbytes for n in ann.NAMES)+3*65536
    if type(max_checkpoint_bytes) is not int or max_checkpoint_bytes<needed:
        raise ValueError('composite logical checkpoint allowance exceeded')
    if s['hardening'] is not None and len(ann.body(s['hardening']))>65536:
        raise ValueError('hardening checkpoint metadata allowance exceeded')
    directory=Path(directory);directory.mkdir(exist_ok=False);ann.sync(directory.parent)
    inner_sha=ann.save(s['annealing'],directory/'annealing',a,b,c,
                       max_checkpoint_bytes=max_checkpoint_bytes-2*65536)
    hard_sha=None
    if s['hardening'] is not None:
        hard_sha=hard.save(s['hardening'],directory/'hardening.json',max_checkpoint_bytes=65536)
    meta={k:s[k] for k in ('version','phase','policy','matrix_sha256')}
    meta.update(annealing_sha256=inner_sha,hardening_sha256=hard_sha)
    raw=ann.body(meta)
    if len(raw)>65536:raise ValueError('composite manifest allowance exceeded')
    with (directory/'manifest.json').open('xb') as f:
        f.write(raw);f.flush();ann.os.fsync(f.fileno())
    ann.sync(directory)
    return hashlib.sha256(raw).hexdigest()


def load(directory,a,b,c,*,expected_sha256,max_state_bytes,
         normalization_chunk_entries=65536,hardening_chunk_entries=65536,
         hardening_buffer_bytes=8*1024**2):
    directory=Path(directory);manifest=directory/'manifest.json'
    if manifest.is_symlink() or manifest.stat().st_size>65536 or ann.sha(manifest)!=expected_sha256:
        raise ValueError('composite manifest identity differs')
    meta=json.loads(manifest.read_bytes())
    p=policy(len(a.node_ids),len(b.node_ids),normalization_chunk_entries,
             hardening_chunk_entries,hardening_buffer_bytes)
    if (not isinstance(meta,dict) or set(meta)!=MANIFEST_FIELDS
            or type(meta['version']) is not int or meta['version']!=1 or meta['policy']!=p
            or meta['phase'] not in ('annealing','hardening','done')):
        raise ValueError('composite manifest schema or policy differs')
    h=None
    if meta['phase']!='annealing':
        h=hard.load(directory/'hardening.json',expected_sha256=meta['hardening_sha256'],max_checkpoint_bytes=65536)
    elif meta['hardening_sha256'] is not None or meta['matrix_sha256'] is not None:
        raise ValueError('unexpected pre-hardening metadata')
    inner=ann.load(directory/'annealing',a,b,c,expected_sha256=meta['annealing_sha256'],
                   max_state_bytes=max_state_bytes,max_chunk_entries=normalization_chunk_entries)
    if h is not None:
        if matrix_identity(inner['M'])!=meta['matrix_sha256']:
            raise ValueError('restored hardening matrix identity differs')
        inner['M'].flags.writeable=False
    s=dict(version=1,safe=True,phase=meta['phase'],policy=p,annealing=inner,
           hardening=h,matrix_sha256=meta['matrix_sha256'])
    check(s,a,b,c)
    return s

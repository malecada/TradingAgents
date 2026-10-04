"""Exact weak one-hop cardinalities; execution requires separate admission.

Scratch/output disk is bounded before creation. Whole-invocation wall containment
below 600 seconds is a release prerequisite, supplied by the registered launcher.
Completed phases are durable; interrupted partial files are never called complete.
Existing output directories are refused, including interrupted identities.
"""
from pathlib import Path
import hashlib
import json
import os
import time
import numpy as np


def _sync_dir(directory):
    fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def _body(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()


def _write(path,body):
    with path.open('xb') as stream:
        stream.write(body)
        stream.flush();os.fsync(stream.fileno())
    _sync_dir(path.parent)


def _json(path,value):
    _write(path,_body(value))


def _hash(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return digest.hexdigest()


def _flush(array,path):
    array.flush()
    with path.open('rb') as stream:os.fsync(stream.fileno())


def _save(path,array):
    with path.open('xb') as stream:
        np.save(stream,array,allow_pickle=False);stream.flush();os.fsync(stream.fileno())
    _sync_dir(path.parent)


def census(edge_index,node_count,directory,*,identity,edge_chunk=65536,max_output_bytes=512*1024**2,checkpoint=None):
    if type(node_count) is not int or not 0<node_count<=3037000499:raise ValueError('node count or pair-key overflow')
    if type(edge_chunk) is not int or edge_chunk<=0:raise ValueError('positive edge chunk required')
    if type(max_output_bytes) is not int or max_output_bytes<=0:raise ValueError('positive output allowance required')
    if not isinstance(identity,dict) or not identity or len(json.dumps(identity).encode())>16384:raise ValueError('bounded identity object required')
    if not isinstance(edge_index,np.ndarray) or edge_index.ndim!=2 or edge_index.shape[0]!=2 or edge_index.dtype!=np.dtype(np.int64):raise ValueError('int64 edge index with two rows required')
    n=node_count;e=edge_index.shape[1];directory=Path(directory)
    # Pair keys + cardinalities + worst-case maxima + histogram; .npy headers
    # and bounded identity/checkpoint/summary JSON have separate fixed reserve.
    required=8*e+32*n+131072
    if required>max_output_bytes:raise ValueError('output and scratch allowance exceeded')
    for start in range(0,e,edge_chunk):
        part=edge_index[:,start:start+edge_chunk]
        if part.size and (part.min()<0 or part.max()>=n):raise ValueError('edge endpoint outside node domain')
    directory.mkdir(exist_ok=False);_sync_dir(directory.parent)
    (directory/'checkpoints').mkdir();_sync_dir(directory)
    begin=time.monotonic();keys=None;counts=None;primary_error=None
    def record(number,phase,names):
        value={'schema_version':1,'identity':identity,'phase':phase,'elapsed_seconds':time.monotonic()-begin,
               'files':{name:{'sha256':_hash(directory/name),'bytes':(directory/name).stat().st_size} for name in names}}
        _json(directory/'checkpoints'/f'{number:02d}-{phase}.json',value)
        if checkpoint is not None:checkpoint(phase)
    try:
        keypath=directory/'sorted_pairs.npy'
        # Zero-length mappings are represented by a normal empty .npy array.
        if e:
            keys=np.lib.format.open_memmap(keypath,mode='w+',dtype=np.int64,shape=(e,))
            for start in range(0,e,edge_chunk):
                a,b=edge_index[:,start:start+edge_chunk]
                lo=np.minimum(a,b);hi=np.maximum(a,b)
                coded=lo*n+hi;coded[lo==hi]=-1
                keys[start:start+len(coded)]=coded
            del a,b,lo,hi,coded
            # In-place heapsort has constant auxiliary storage; duplicates are
            # removed during streaming counting, including across chunk borders.
            keys.sort(kind='heapsort');_flush(keys,keypath)
        else:_save(keypath,np.empty(0,dtype=np.int64));keys=np.empty(0,dtype=np.int64)
        _sync_dir(directory);record(1,'sorted_pairs',['sorted_pairs.npy'])
        countpath=directory/'cardinalities.npy'
        counts=np.lib.format.open_memmap(countpath,mode='w+',dtype=np.int64,shape=(n,));counts[:]=1
        previous=-1;unique_pairs=0
        for start in range(0,e,edge_chunk):
            block=keys[start:start+edge_chunk]
            keep=np.empty(len(block),dtype=bool);keep[0]=block[0]!=previous
            keep[1:]=block[1:]!=block[:-1];keep &= block>=0
            distinct=block[keep];previous=int(block[-1]);unique_pairs+=len(distinct)
            np.add.at(counts,distinct//n,1);np.add.at(counts,distinct%n,1)
        if e:del block,keep,distinct
        _flush(counts,countpath);record(2,'cardinalities',['cardinalities.npy'])
        low=int(counts.min());high=int(counts.max())
        maxima=np.flatnonzero(counts==high);_save(directory/'maxima_indices.npy',maxima)
        del maxima
        bins=np.bincount(counts,minlength=high+1)
        values=np.flatnonzero(bins);histogram=np.column_stack((values,bins[values]))
        _save(directory/'histogram.npy',histogram);del bins,values,histogram
        names=['sorted_pairs.npy','cardinalities.npy','maxima_indices.npy','histogram.npy']
        result={'schema_version':1,'identity':identity,'nodes':n,'directed_edges':e,'unique_nonself_pairs':unique_pairs,
                'minimum':low,'maximum':high,'above_10000':int(np.count_nonzero(counts>10000)),
                'elapsed_seconds':time.monotonic()-begin,'output_bytes':sum((directory/name).stat().st_size for name in names),
                'output_bytes_scope':'four numeric array files; metadata counted separately by the registered wrapper',
                'reserved_output_bytes':required,'max_output_bytes':max_output_bytes,
                'files':{name:{'sha256':_hash(directory/name),'bytes':(directory/name).stat().st_size} for name in names}}
        body=_body(result)
        final={'schema_version':1,'identity':identity,'phase':'summary','elapsed_seconds':time.monotonic()-begin,
               'files':dict(result['files'],**{'summary.json':{'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)}})}
        final_body=_body(final)
        actual=sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())+len(body)+len(final_body)
        if actual>required:raise RuntimeError('output accounting envelope exceeded')
        # The exact logical-byte envelope is checked before publishing either
        # completion file. Filesystem allocation is measured by the wrapper.
        _write(directory/'summary.json',body)
        _write(directory/'checkpoints'/'03-summary.json',final_body)
        if checkpoint is not None:checkpoint('summary')
        return result
    except BaseException as exc:
        primary_error=exc
        raise
    finally:
        cleanup_errors=[]
        for array in (counts,keys):
            if isinstance(array,np.memmap):
                try:array._mmap.close()
                except BaseException as exc:cleanup_errors.append(exc)
        if cleanup_errors:
            if primary_error is not None:
                for exc in cleanup_errors:primary_error.add_note('census mapping cleanup failure: '+repr(exc))
            else:raise RuntimeError('census mapping cleanup failed') from cleanup_errors[0]

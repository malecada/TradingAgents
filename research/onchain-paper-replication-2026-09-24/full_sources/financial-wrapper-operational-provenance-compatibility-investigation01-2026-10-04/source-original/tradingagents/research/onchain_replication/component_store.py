"""Immutable, streamed numeric component checkpoints without object pickle.

Publication does not grant a research lease or permit restarting a terminal job.
The registered producer owns directories and binds manifest hashes externally.
"""
from pathlib import Path
from dataclasses import dataclass
from math import prod
import json,os
import numpy as np
import torch
from .provenance import canonical_bytes,digest,file_hash,durable_mkdir,sync_directory


def save_component(directory,payload,context):
    directory=Path(directory);durable_mkdir(directory.parent)
    directory.mkdir(exist_ok=False);sync_directory(directory.parent)
    arrays={}
    def encode(value):
        if isinstance(value,(np.ndarray,torch.Tensor)):
            tensor=isinstance(value,torch.Tensor)
            array=value.detach().cpu().numpy() if tensor else value
            if array.dtype.hasobject or array.dtype.kind not in 'biuf':raise ValueError('numeric component array required')
            name=f'array-{len(arrays):06d}.npy';path=directory/name
            with path.open('xb') as stream:np.save(stream,array,allow_pickle=False);stream.flush();os.fsync(stream.fileno())
            arrays[name]={'sha256':file_hash(path),'bytes':path.stat().st_size,'shape':list(array.shape),'dtype':str(array.dtype)}
            return {'kind':'tensor' if tensor else 'array','member':name}
        if isinstance(value,np.generic):value=value.item()
        if isinstance(value,dict):return {'kind':'dict','items':[[encode(k),encode(v)] for k,v in value.items()]}
        if isinstance(value,(list,tuple)):return {'kind':'tuple' if isinstance(value,tuple) else 'list','items':[encode(x) for x in value]}
        if value is None or type(value) in (bool,str,int,float):
            canonical_bytes(value)
            return {'kind':'scalar','value':value}
        raise ValueError('unsupported checkpoint component type: '+type(value).__name__)
    tree=encode(payload)
    manifest={'schema_version':1,'context':context,'tree':tree,'arrays':arrays}
    with (directory/'manifest.json').open('xb') as stream:stream.write(canonical_bytes(manifest));stream.flush();os.fsync(stream.fileno())
    sync_directory(directory)
    return directory/'manifest.json'


@dataclass(frozen=True)
class ArrayReference:
    """Verified descriptor, never a retained mmap or a grant to run research."""
    path: Path
    sha256: str
    file_bytes: int
    shape: tuple
    dtype: str
    tensor: bool

    @property
    def nbytes(self):return prod(self.shape)*np.dtype(self.dtype).itemsize

    def _open(self):
        if self.path.is_symlink() or self.path.stat().st_size!=self.file_bytes or file_hash(self.path)!=self.sha256:raise ValueError('component array hash/size differs')
        array=np.load(self.path,allow_pickle=False,mmap_mode='r')
        if array.dtype.hasobject or array.dtype.kind not in 'biuf' or tuple(array.shape)!=self.shape or str(array.dtype)!=self.dtype:raise ValueError('component array dimensions/type differ')
        return array

    def load(self):
        array=self._open();copied=np.array(array,copy=True)
        if file_hash(self.path)!=self.sha256:raise ValueError('component array changed during load')
        return torch.from_numpy(copied) if self.tensor else copied

    def feed_hash(self,hasher):
        array=self._open()
        # The eager identity uses ascontiguousarray, which promotes 0-D to (1,).
        hasher.update(canonical_bytes({'shape':array.shape or (1,),'dtype':str(array.dtype)}))
        # Stored arrays may be Fortran ordered. Feature identities use C order.
        with np.nditer(array,flags=['external_loop','buffered','zerosize_ok'],
                       op_flags=['readonly'],order='C',buffersize=65536) as chunks:
            for chunk in chunks:hasher.update(chunk.tobytes(order='C'))
        if file_hash(self.path)!=self.sha256:raise ValueError('component array changed during hashing')


def reference_bytes(value):
    if isinstance(value,ArrayReference):return value.nbytes
    if isinstance(value,np.ndarray):return value.nbytes
    if isinstance(value,torch.Tensor):return value.numel()*value.element_size()
    if isinstance(value,dict):return sum(reference_bytes(x) for x in value.values())
    if isinstance(value,(list,tuple)):return sum(map(reference_bytes,value))
    return 0


def materialize_component(value,*,max_array_bytes):
    if type(max_array_bytes) is not int or max_array_bytes<=0 or reference_bytes(value)>max_array_bytes:raise ValueError('component materialization bound exceeded')
    def load(item):
        if isinstance(item,ArrayReference):return item.load()
        if isinstance(item,dict):return {k:load(v) for k,v in item.items()}
        if isinstance(item,(list,tuple)):return type(item)(load(x) for x in item)
        return item
    return load(value)


def load_component(manifest_path,expected_hash,expected_context,*,max_array_bytes,materialize_arrays=True):
    if type(materialize_arrays) is not bool:raise ValueError('component materialization policy must be boolean')
    if type(max_array_bytes) is not int or max_array_bytes<=0:raise ValueError('explicit component allocation bound required')
    path=Path(manifest_path);raw=path.read_bytes()
    if path.is_symlink() or digest(raw)!=expected_hash:raise ValueError('component manifest hash differs')
    manifest=json.loads(raw)
    if set(manifest)!={'schema_version','context','tree','arrays'} or manifest['schema_version']!=1:raise ValueError('component schema differs')
    if canonical_bytes(manifest['context'])!=canonical_bytes(expected_context):raise ValueError('component context differs')
    declared=manifest['arrays'];used=set();allocated=[0]
    def decode(node):
        kind=node['kind']
        if kind in ('tensor','array'):
            if set(node)!={'kind','member'}:raise ValueError('component array reference differs')
            name=node['member']
            if name not in declared or name in used or name!=f'array-{int(name[6:12]):06d}.npy':raise ValueError('invalid or duplicate component member')
            used.add(name);info=declared[name];member=path.parent/name
            if member.is_symlink() or type(info['bytes']) is not int or not 0<info['bytes']<=max_array_bytes or member.stat().st_size!=info['bytes'] or file_hash(member)!=info['sha256']:raise ValueError('component array hash/size differs')
            array=np.load(member,allow_pickle=False,mmap_mode='r')
            if array.dtype.hasobject or array.dtype.kind not in 'biuf' or list(array.shape)!=info['shape'] or str(array.dtype)!=info['dtype']:raise ValueError('component array dimensions/type differ')
            allocated[0]+=array.nbytes
            if allocated[0]>max_array_bytes:raise ValueError('component total allocation bound exceeded')
            reference=ArrayReference(member,info['sha256'],info['bytes'],tuple(array.shape),str(array.dtype),kind=='tensor')
            # The descriptor retains no mapped array. Eager callers still receive
            # independent writable bytes, including optimizer restoration state.
            copied=np.array(array,copy=True) if materialize_arrays else None
            if file_hash(member)!=info['sha256']:raise ValueError('component array changed during load')
            if not materialize_arrays:return reference
            return torch.from_numpy(copied) if kind=='tensor' else copied
        if kind=='scalar':
            if set(node)!={'kind','value'} or (node['value'] is not None and type(node['value']) not in (bool,str,int,float)):raise ValueError('component scalar differs')
            canonical_bytes(node['value']);return node['value']
        if kind in ('dict','list','tuple'):
            if set(node)!={'kind','items'}:raise ValueError('component collection differs')
            if kind=='dict':
                pairs=[(decode(k),decode(v)) for k,v in node['items']]
                result=dict(pairs)
                if len(result)!=len(pairs):raise ValueError('duplicate component dictionary keys')
                return result
            values=[decode(x) for x in node['items']]
            return tuple(values) if kind=='tuple' else values
        raise ValueError('unknown component encoding')
    result=decode(manifest['tree'])
    if used!=set(declared):raise ValueError('unreferenced component arrays')
    if file_hash(path)!=expected_hash:raise ValueError('component manifest changed during load')
    return result

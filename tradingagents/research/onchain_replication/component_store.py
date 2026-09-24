"""Immutable, streamed numeric component checkpoints without object pickle.

Publication does not grant a research lease or permit restarting a terminal job.
The registered producer owns directories and binds manifest hashes externally.
"""
from pathlib import Path
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


def load_component(manifest_path,expected_hash,expected_context,*,max_array_bytes):
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
            # Return independent, writable bytes; callers may restore optimizer state.
            copied=np.array(array,copy=True)
            if file_hash(member)!=info['sha256']:raise ValueError('component array changed during load')
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

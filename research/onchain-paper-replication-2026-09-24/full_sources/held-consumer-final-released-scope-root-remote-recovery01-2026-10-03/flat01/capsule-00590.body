"""File-streamed graph checkpoints; no pickle and no full JSON array materialization."""
from pathlib import Path
import json
import os
import math
import io
import struct
import hashlib
import stat
from .owned_io import _closing
import numpy as np
from .contracts import GraphSnapshot,validate_graph
from .neighborhoods import graph_hash
from .provenance import canonical_bytes,file_hash,sync_directory,durable_mkdir
from .mapped_graph import open_mapped_graph


def save_graph(directory,graph):
    directory=Path(directory);durable_mkdir(directory.parent);directory.mkdir();sync_directory(directory.parent)
    arrays={'node_features':graph.node_features,'edge_index':graph.edge_index,'edge_features':graph.edge_features,'node_ids':np.asarray(graph.node_ids)}
    if graph.edge_aggregates is not None:arrays['edge_aggregates']=graph.edge_aggregates
    for name,value in arrays.items():
        with _closing((directory/(name+'.npy')).open('xb')) as stream:np.save(stream,value,allow_pickle=False);stream.flush();os.fsync(stream.fileno())
    meta={name:getattr(graph,name) for name in ('asset','start_utc','end_utc','available_at','source_hashes','graph_config_hash','raw_count','admitted_count')}
    meta['exclusion_counts']=dict(graph.exclusion_counts)
    manifest={'metadata':meta,'graph_hash':graph_hash(graph),'arrays':{name:{'path':name+'.npy','sha256':file_hash(directory/(name+'.npy')),'bytes':(directory/(name+'.npy')).stat().st_size} for name in arrays}}
    with _closing((directory/'manifest.json').open('xb')) as stream:stream.write(canonical_bytes(manifest)+b'\n');stream.flush();os.fsync(stream.fileno())
    sync_directory(directory);return directory/'manifest.json'


def _resident_array(member,info):
    # Admit the actual NPY extent before NumPy can allocate the header's shape.
    with _closing(member.open('rb')) as stream:
        before=os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or type(info['bytes']) is not int or before.st_size!=info['bytes']:
            raise ValueError('resident graph member extent differs')
        magic=stream.read(8)
        if magic[:6]!=b'\x93NUMPY' or magic[6:] not in (b'\x01\x00',b'\x02\x00'):
            raise ValueError('resident graph NPY version unsupported')
        width=2 if magic[6:]==b'\x01\x00' else 4
        prefix=stream.read(width)
        if len(prefix)!=width:raise ValueError('resident graph header length missing')
        length=struct.unpack('<H' if width==2 else '<I',prefix)[0]
        if not 0<length<=10000 or 8+width+length>before.st_size:
            raise ValueError('resident graph header length exceeds bound')
        header=stream.read(length)
        if len(header)!=length:raise ValueError('resident graph header truncated')
        # Parse the captured bounded header once; mutable file bytes cannot
        # redefine the allocation through a second NumPy load.
        captured=io.BytesIO(prefix+header)
        reader=np.lib.format.read_array_header_1_0 if width==2 else np.lib.format.read_array_header_2_0
        shape,fortran,dtype=reader(captured,max_header_size=10000)
        if dtype.hasobject or any(type(n) is not int or n<0 for n in shape) or stream.tell()+math.prod(shape)*dtype.itemsize!=before.st_size:
            raise ValueError('resident graph header extent differs')
        value=np.empty(shape,dtype=dtype,order='F' if fortran else 'C')
        payload=memoryview(value.ravel(order='K')).cast('B');offset=0
        checksum=hashlib.sha256(magic+prefix+header)
        while offset<len(payload):
            end=min(len(payload),offset+1048576)
            n=stream.readinto(payload[offset:end])
            if not n:raise ValueError('resident graph payload changed or truncated')
            checksum.update(payload[offset:offset+n]);offset+=n
        if stream.read(1) or checksum.hexdigest()!=info['sha256']:
            raise ValueError('resident graph payload hash changed')
        after=os.fstat(stream.fileno())
        if any(getattr(before,k)!=getattr(after,k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')):
            raise ValueError('resident graph changed during allocation')
    if file_hash(member)!=info['sha256']:raise ValueError('resident graph changed after allocation')
    return value


def load_graph(manifest_path,expected_hash,*,resident=False):
    if type(resident) is not bool:raise ValueError("graph residency selection must be boolean")
    path=Path(manifest_path)
    if file_hash(path)!=expected_hash:raise ValueError('graph manifest hash differs')
    with _closing(path.open('rb')) as stream:manifest=json.loads(stream.read())
    arrays={}
    for name,info in manifest['arrays'].items():
        if name not in {'node_features','edge_index','edge_features','node_ids','edge_aggregates'} or info['path']!=name+'.npy':raise ValueError('invalid graph member')
        member=path.parent/info['path']
        if member.is_symlink() or file_hash(member)!=info['sha256']:raise ValueError('graph member hash differs')
        arrays[name]=_resident_array(member,info) if resident else np.load(member,allow_pickle=False,mmap_mode='r')
    arrays['node_ids']=tuple(arrays['node_ids'].tolist());g=GraphSnapshot(**manifest['metadata'],**arrays)
    validate_graph(g)
    if graph_hash(g)!=manifest['graph_hash']:raise ValueError('graph content identity differs')
    return g

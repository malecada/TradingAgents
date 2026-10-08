"""Opt-in complete flat NPY chunks; bounded files, no numerical transformation.

The caller owns arrays exclusively. Hash/stat checks detect observed mutation,
not writer exclusion. Full restored arrays still consume admitted numeric state.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import numpy as np

FORMAT='sharded-npy-v1'
LIMIT=65536
MAX_ENTRIES=262144  # 2 MiB float64/int64 payload, plus exactly128 NPY header bytes.
MAX_CHUNKS=256  # finite descriptor/inventory work; manifest byte caps also apply.


def need(value,message):
    if not value:raise ValueError(message)


def layout(value):
    need(type(value) is dict and set(value)=={'format','chunk_entries'} and value['format']==FORMAT
         and type(value['chunk_entries']) is int and 0<value['chunk_entries']<=MAX_ENTRIES,'explicit bounded checkpoint layout required')
    return dict(value)


def io_scratch_bytes(selected):
    selected=layout(selected)
    # Conservative simultaneously live raw/BytesIO/copy bodies and read block.
    # Python metadata, allocator/runtime and filesystem cache remain excluded.
    return 3*(8*selected['chunk_entries']+128)+65536


def body(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def digest(value):return hashlib.sha256(value).hexdigest()
def pin(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def sync(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


def read(path,maximum):
    path=Path(path);need(path.resolve()==path,'checkpoint path redirected')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<=before.st_size<=maximum,'checkpoint regular extent differs')
        data=bytearray()
        while len(data)<before.st_size:
            block=os.read(fd,min(65536,before.st_size-len(data)));need(bool(block),'checkpoint partial file');data.extend(block)
        need(not os.read(fd,1) and pin(before)==pin(os.fstat(fd))==pin(path.lstat()),'checkpoint file changed')
        return bytes(data)
    finally:os.close(fd)


def write(path,raw):
    need(len(raw)<=MAX_ENTRIES*8+128,'checkpoint physical file bound')
    with Path(path).open('xb') as file:file.write(raw);file.flush();os.fsync(file.fileno())


def manifest(directory,value):
    raw=body(value);need(len(raw)<=LIMIT,'checkpoint chunk manifest allowance exceeded')
    write(Path(directory)/'manifest.json',raw);sync(directory);return digest(raw)


def metadata(directory,expected):
    raw=read(Path(directory)/'manifest.json',LIMIT);need(digest(raw)==expected,'checkpoint manifest hash differs')
    return json.loads(raw)


def describe(shape,dtype,selected,prefix):
    selected=layout(selected)
    need(type(shape) in (list,tuple) and 1<=len(shape)<=2 and all(type(v) is int and v>0 for v in shape),'positive array shape required')
    need(dtype in ('<f8','<i8') and prefix in ('M','Q','V','order'),'checkpoint array type/name differs')
    entries=math.prod(shape);need(entries<2**60,'checkpoint array extent overflow')
    count=(entries+selected['chunk_entries']-1)//selected['chunk_entries']
    need(count<=MAX_CHUNKS,'checkpoint chunk count allowance exceeded')
    chunks=[]
    for i,start in enumerate(range(0,entries,selected['chunk_entries'])):
        size=min(selected['chunk_entries'],entries-start)
        chunks.append({'name':f'{prefix}-{i:08d}.npy','start':start,'entries':size,'bytes':8*size+128,'sha256':'0'*64})
    return {'format':FORMAT,'shape':list(shape),'dtype':dtype,'entries':entries,'bytes':sum(c['bytes'] for c in chunks),'chunks':chunks}


def save_array(directory,array,selected,prefix):
    need(type(array) in (np.ndarray,np.memmap) and array.flags.c_contiguous,'contiguous numeric array required')
    descriptor=describe(array.shape,array.dtype.str,selected,prefix)
    flat=array.reshape(-1)
    for item in descriptor['chunks']:
        path=Path(directory)/item['name'];chunk=flat[item['start']:item['start']+item['entries']]
        with path.open('xb') as f:np.save(f,chunk,allow_pickle=False);f.flush();os.fsync(f.fileno())
        raw=read(path,item['bytes']);need(len(raw)==item['bytes'],'checkpoint chunk NPY extent differs')
        item['sha256']=digest(raw)
    return descriptor


def validate_descriptor(value,shape,dtype,selected,prefix):
    expected=describe(shape,dtype,selected,prefix)
    need(type(value) is dict and set(value)==set(expected) and type(value['chunks']) is list
         and len(value['chunks'])==len(expected['chunks']),'checkpoint ordered chunk descriptor differs')
    for key in set(expected)-{'chunks'}:need(value[key]==expected[key],'checkpoint array descriptor differs')
    for got,want in zip(value['chunks'],expected['chunks'],strict=True):
        need(type(got) is dict and set(got)==set(want),'checkpoint chunk schema differs')
        need(all(got[k]==want[k] for k in set(want)-{'sha256'}),'checkpoint chunk order/extent differs')
        h=got['sha256'];need(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),'checkpoint chunk digest differs')
    return expected['bytes']


def audit_array(directory,value,shape,dtype,selected,prefix,*,destination=None):
    import io
    total=validate_descriptor(value,shape,dtype,selected,prefix)
    for item in value['chunks']:
        raw=read(Path(directory)/item['name'],item['bytes'])
        need(len(raw)==item['bytes'] and digest(raw)==item['sha256'],'checkpoint chunk hash/extent differs')
        stream=io.BytesIO(raw)
        need(np.lib.format.read_magic(stream)==(1,0),'checkpoint chunk NPY version differs')
        actual,fortran,kind=np.lib.format.read_array_header_1_0(stream,max_header_size=128)
        need(actual==(item['entries'],) and not fortran and kind.str==dtype and stream.tell()==128,'checkpoint chunk NPY header differs')
        if destination is not None:
            destination[item['start']:item['start']+item['entries']]=np.frombuffer(raw,dtype=dtype,offset=128)
        stream.close();del stream,raw
    return total


def load_array(directory,value,shape,dtype,selected,prefix):
    # Authenticate all chunks before allocating the complete restored body; then
    # reauthenticate each bounded chunk as its exact bytes are copied.
    audit_array(directory,value,shape,dtype,selected,prefix)
    result=np.empty(shape,dtype=dtype)
    audit_array(directory,value,shape,dtype,selected,prefix,destination=result.reshape(-1))
    return result


def inventory(directory,names):
    directory=Path(directory);need(directory.resolve()==directory,'checkpoint directory redirected')
    need({p.name for p in directory.iterdir()}==set(names),'checkpoint chunk inventory differs')
    for name in names:
        info=(directory/name).lstat()
        need(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_dev==directory.stat().st_dev,'checkpoint member identity differs')


def array_names(descriptors):return {item['name'] for d in descriptors for item in d['chunks']}


def anneal_save(module,state,directory,a,b,c,maximum,selected):
    selected=layout(selected);module.check(state,a,b,c)
    planned={name:describe(state[name].shape,state[name].dtype.str,selected,name) for name in module.NAMES}
    meta={**{k:state[k] for k in module.META},'files':planned,'checkpoint_layout':selected}
    need(type(maximum) is int and maximum>=sum(d['bytes'] for d in planned.values())+LIMIT,'sharded annealing allowance exceeded')
    need(len(body(meta))<=LIMIT,'sharded annealing manifest bound')
    directory=Path(directory);directory.mkdir(exist_ok=False);sync(directory.parent)
    meta['files']={name:save_array(directory,state[name],selected,name) for name in module.NAMES}
    return manifest(directory,meta)


def anneal_load(module,directory,a,b,c,expected,maximum,cap,selected):
    selected=layout(selected);meta=metadata(directory,expected);n,m=len(a.node_ids),len(b.node_ids)
    module.validate_pair(a,b,c);module.bound(n,m,maximum);module.normalization_policy(n,m,cap)
    need(set(meta)==module.META|{'files','checkpoint_layout'} and meta['checkpoint_layout']==selected and meta['schema_version']==3
         and meta['max_chunk_entries']==cap and meta['identity']==module.identity(a,b,c) and meta['shape']==[n,m]
         and set(meta['files'])==set(module.NAMES),'sharded annealing identity differs')
    for name in module.NAMES:validate_descriptor(meta['files'][name],[n,m],'<f8',selected,name)
    inventory(directory,{'manifest.json'}|array_names(meta['files'].values()))
    state={k:meta[k] for k in module.META}
    state.update({name:load_array(directory,meta['files'][name],[n,m],'<f8',selected,name) for name in module.NAMES})
    module.check(state,a,b,c);return state


def hard_save(module,state,directory,maximum,selected):
    selected=layout(selected);module.check(state)
    descriptor=describe(state['order'].shape,'<i8',selected,'order')
    meta={k:v for k,v in state.items() if k!='order'};meta.update(order_chunks=descriptor,checkpoint_layout=selected)
    need(type(maximum) is int and maximum>=descriptor['bytes']+LIMIT,'sharded hardening allowance exceeded')
    need(len(body(meta))<=LIMIT,'sharded hardening manifest bound')
    directory=Path(directory);directory.mkdir(exist_ok=False);sync(directory.parent)
    meta['order_chunks']=save_array(directory,state['order'],selected,'order');return manifest(directory,meta)


def hard_load(module,directory,expected,input_sha,pairs,maximum,selected):
    selected=layout(selected);meta=metadata(directory,expected)
    need(type(meta) is dict and set(meta)==module.FIELDS-{'order'}|{'order_chunks','checkpoint_layout'}
         and meta['checkpoint_layout']==selected and meta['input_sha256']==input_sha
         and meta['max_pair_entries']==pairs and meta['max_explicit_bytes']==maximum,'sharded hardening identity differs')
    shape=meta['shape'];need(type(shape) is list and len(shape)==2 and all(type(v) is int and v>0 for v in shape),'sharded rank shape')
    n,m=shape;module.policy(n,m,pairs,maximum)
    descriptor=meta.pop('order_chunks');meta.pop('checkpoint_layout');meta['order']=None;module._check_metadata(meta)
    validate_descriptor(descriptor,[n*m],'<i8',selected,'order')
    inventory(directory,{'manifest.json'}|array_names([descriptor]))
    order=load_array(directory,descriptor,[n*m],'<i8',selected,'order');order.flags.writeable=False
    meta['order']=order;module.check(meta);return meta

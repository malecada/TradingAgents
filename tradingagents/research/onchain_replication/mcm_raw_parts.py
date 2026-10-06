"""Bounded original f64/f32 byte joins; these utilities grant no authority.

Conversion stays in compact_mcm_output's original NumPy expression. This module
checks its raw result independently, including the sign bit of zero. No decimal
serialization or replacement numerical values enter the output.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct

MAX_PART=4*1024**2
KINDS={'score-batch-f64':8,'mcm-output-f32':4}

def require(value,message):
    if not value:raise ValueError(message)

def layout(kind,cells,part_bytes):
    require(kind in KINDS,'unknown original payload kind')
    width=KINDS[kind]
    require(type(cells) is int and 0<cells<2**63//width,'finite positive original cell count required')
    require(type(part_bytes) is int and width<=part_bytes<=MAX_PART and part_bytes%width==0,'finite aligned payload part required')
    size=width*cells
    return size,(size+part_bytes-1)//part_bytes

def cast_equal(raw64,raw32):
    """Exact IEEE binary32 join to original binary64 scores, O(one part).

    Values are the original finite scores; struct conversion independently checks
    the retained NumPy cast. Bitwise comparison includes negative zero.
    """
    require(type(raw64) is bytes and type(raw32) is bytes and 0<len(raw64)<=MAX_PART and len(raw64)%8==0 and len(raw32)*2==len(raw64),'bounded paired original payload extents required')
    for index,(value,) in enumerate(struct.iter_unpack('<d',raw64)):
        require(math.isfinite(value),'nonfinite original score')
        try:expected=struct.pack('<f',value)
        except (OverflowError,struct.error) as error:raise ValueError('nonfinite output cast') from error
        require(math.isfinite(struct.unpack('<f',expected)[0]) and raw32[4*index:4*index+4]==expected,'original f64 to f32 bits differ')
    return {'f64_sha256':hashlib.sha256(raw64).hexdigest(),'f32_sha256':hashlib.sha256(raw32).hexdigest(),'cells':len(raw32)//4}

def signature(info):
    return tuple(getattr(info,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))

def descriptor(kind,identity,index,offset,raw,*,cells,part_bytes):
    size,count=layout(kind,cells,part_bytes)
    require(type(identity) is str and len(identity)==64 and all(c in '0123456789abcdef' for c in identity),'exact payload binding hash required')
    require(type(index) is int and 0<=index<count and type(offset) is int and offset==index*part_bytes,'original payload order differs')
    require(type(raw) is bytes and len(raw)==min(part_bytes,size-offset),'original payload part extent differs')
    return {'schema_version':1,'kind':kind,'binding_sha256':identity,'index':index,'offset':offset,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'cells':len(raw)//KINDS[kind],'dtype':'<f8' if kind=='score-batch-f64' else '<f4','order':'row-major'}

def read_exact(fd,size):
    require(type(size) is int and 0<=size<=MAX_PART,'bounded read required')
    result=bytearray()
    while len(result)<size:
        part=os.read(fd,size-len(result));require(bool(part),'original payload truncated');result.extend(part)
    return bytes(result)

def parts(path,*,kind,cells,part_bytes,expected_sha256,lease):
    """Pinned no-follow local reader, provisional until complete EOF/lease exit.

    Caller must consume the generator fully before acknowledging any result.
    Endpoint checks are sampled, not continuous exclusion of external writers.
    """
    size,count=layout(kind,cells,part_bytes);path=Path(path)
    require(callable(lease) and path.is_absolute() and path.resolve()==path,'canonical original payload path/live lease required')
    require(type(expected_sha256) is str and len(expected_sha256)==64 and all(c in '0123456789abcdef' for c in expected_sha256),'original full payload hash required')
    lease();parent=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fd=None
    try:
        parent_pin=os.fstat(parent)
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent)
        info=os.fstat(fd);pin=signature(info)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size==size,'original payload type/link/extent differs')
        def check():
            require(signature(os.fstat(fd))==pin==signature(os.stat(path.name,dir_fd=parent,follow_symlinks=False)),'original payload changed')
            current=path.parent.lstat();require((current.st_dev,current.st_ino)==(parent_pin.st_dev,parent_pin.st_ino) and path.parent.resolve()==path.parent,'original payload parent changed')
        digest=hashlib.sha256()
        for index in range(count):
            lease();check();raw=read_exact(fd,min(part_bytes,size-index*part_bytes));digest.update(raw);check();yield index,index*part_bytes,raw
        require(os.read(fd,1)==b'' and digest.hexdigest()==expected_sha256,'original payload EOF/hash differs')
        lease();check()
    finally:
        from .owned_io import _cleanup
        actions=[]
        if fd is not None:actions.append(lambda:os.close(fd))
        actions.append(lambda:os.close(parent));_cleanup(actions)


ASSUMPTION='original-full-recovery-and-cast-proof; current-remote-availability-unasserted'

def storage_policy(value):
    fields={'schema_version','kind','input','input_sha256','part_bytes','closed_check_assumption'}
    require(type(value) is dict and set(value)==fields and type(value['schema_version']) is int and value['schema_version']==1 and value['kind']=='mcm-output-f32-archive','explicit output storage policy required')
    require(type(value['input']) is str and value['input'] and type(value['input_sha256']) is str and len(value['input_sha256'])==64 and all(c in '0123456789abcdef' for c in value['input_sha256']),'registered output storage input required')
    layout('mcm-output-f32',1,value['part_bytes'])
    require(value['closed_check_assumption']==ASSUMPTION,'explicit historical output proof assumption required')
    return dict(value)

def output_binding(args,start):
    from .cache import cache_key
    return {'schema_version':1,'kind':'mcm-output-f32','owner':args['contract']['owner'],
        'stage':args['stage_root'].name,'stage_sha256':args['stage_sha256'],
        'contract_sha256':cache_key(args['contract']),'scope':args['expected_scope'],
        'rows':start['rows'],'motifs':start['motifs'],'dtype':'<f4','order':'row-major',
        'storage_policy':storage_policy(args['storage_policy'])}

def _native_limit(size):
    import resource
    limits=resource.getrlimit(resource.RLIMIT_FSIZE)
    require(all(type(v) is int and size<=v<2**63 for v in limits),'finite native file readback must cover original matrix and selected chunks')

def _write_all(fd,raw):
    view=memoryview(raw)
    while view:
        n=os.write(fd,view);require(n>0,'original output write made no progress');view=view[n:]

def publish_output(directory,*,args,owner,stage,lease):
    """Genuine held producer; original matrix file plus bounded transfer parts.

    The original mapped matrix remains local. Its actual full extent requires a
    separately selected finite native file cap; transport parts stay <=4 MiB.
    """
    from . import compact_mcm_output as output,typed_payload_operations as typed
    from .provenance import durable_mkdir
    from . import compact_owner as owners
    held=getattr(owner,'_held_transition',None)
    require(type(owner) is owners.Owner and type(stage) is owners.Stage
        and type(held) is owners._HeldTransition and stage.owner is owner
        and owner.stages.get(stage.name) is stage and stage.closed and owner.active is None,
        'actual completed MCM and captured owner transition required before writes')
    held.check(owner);owner.boundary();stage.integrity();owners.verify_current(owner)
    io=output.io;start=output._source(args);cfg=storage_policy(args['storage_policy'])
    require(callable(lease),'original output lease required')
    selected=typed.selected(owner)
    require(selected is not None and selected['input']==cfg['input'] and selected['input_sha256']==cfg['input_sha256'],'same admitted shared typed budget required')
    require(stage.root==args['stage_root'] and stage.reference==args['stage_sha256'] and stage.owner is owner,'original completed stage differs')
    size,count=layout('mcm-output-f32',start['rows']*start['motifs'],cfg['part_bytes'])
    require(size+2*io.META_LIMIT<=args['max_output_bytes'],'selected matrix and two metadata bodies exceed reservation')
    _native_limit(max(size,cfg['part_bytes'],io.META_LIMIT))
    root=Path(directory);require(root.is_absolute() and root.resolve()==root and not os.path.lexists(root),'fresh canonical output namespace required')
    lease();root.mkdir();parent,pfd=io._open(root.parent)
    try:os.fsync(pfd);io._root(parent,pfd)
    finally:io._release(lambda:os.close(pfd))
    # Transfer receipts/cache belong to the separately charged shared typed
    # budget, outside the matrix artifact's own logical reservation.
    transport=root.parent/'transport';durable_mkdir(transport)
    root,fd=io._open(root);child=None;binding=output_binding(args,start)
    try:
        child=os.open('matrix.f32',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=fd)
        digest=hashlib.sha256();original=hashlib.sha256();written=index=cells=0
        # Complete actual batch recovery operations before distinct output birth.
        # There is no nested capability replacement or fabricated active parent.
        for raw64,raw32 in output._archived_chunks(owner,stage,args,start,transport):
            require(len(raw64)%8==0 and len(raw32)*2==len(raw64),'original paired f64/f32 extents differ')
            lease();io._root(root,fd);_write_all(child,raw32)
            original.update(raw64);digest.update(raw32);cells+=len(raw64)//8;written+=len(raw32)
        require(written==size and cells==start['rows']*start['motifs'],'complete original output population required')
        os.fsync(child);lease();io._root(root,fd)
        with typed.operation(owner,stage,kind='mcm-output-f32',binding=binding,payload_bytes=size,chunk_count=count) as op:
            for index,offset,raw in parts(root/'matrix.f32',kind='mcm-output-f32',cells=cells,
                    part_bytes=cfg['part_bytes'],expected_sha256=digest.hexdigest(),lease=op.lease):
                source=transport/f'source-{index:012d}.f32'
                troot,tfd=io._open(transport)
                try:io._write(tfd,source.name,raw);io._root(troot,tfd)
                finally:io._release(lambda:os.close(tfd))
                h=hashlib.sha256(raw).hexdigest()
                receipt=op.preserve(source,expected_sha256=h,expected_bytes=len(raw),index=index,attempt=transport/f'part-{index:012d}')
                require(receipt['source_sha256']==h and receipt['bytes']==len(raw),'genuine full-get output receipt differs')
                op.retire_source(source,expected_sha256=h,expected_bytes=len(raw))
            index+=1
            require(index==count,'complete original output part population required')
        history=op.history()
        require(output._source(args)==start,'original stage changed during selected output publication')
        state={'schema_version':1,'format':'mcm-output-recovery-proof-v1','binding':binding,
            'history':history,'cells':cells,'f64_bytes':cells*8,'f64_sha256':original.hexdigest(),
            'f32_bytes':written,'f32_sha256':digest.hexdigest(),'parts':index,'assumption':ASSUMPTION}
        storage_sha=io._write(fd,'storage.json',io._json(state))
        value=output._manifest(args,start,digest.hexdigest())|{'schema_version':2,'storage_sha256':storage_sha}
        reference=io._write(fd,'manifest.json',io._json(value));io._root(root,fd)
        output._verified(root,reference,args,lease)
        return reference
    except BaseException:
        owner.poisoned=True;raise
    finally:
        actions=[]
        if child is not None:actions.append(lambda:os.close(child))
        actions.append(lambda:os.close(fd));io._cleanup(actions)

def inspect_output(directory,expected_sha256,args):
    """Anchored historical recovery and actual local f32 bytes; no remote IO.

    It proves no current remote availability. Future remote restoration requires
    a new genuine operation and fresh full byte recovery, never this receipt.
    """
    from . import compact_mcm_output as output,typed_payload_operations as typed
    io=output.io;start=output._source(args);cfg=storage_policy(args['storage_policy']);binding=output_binding(args,start)
    root,fd=io._open(directory);child=None
    try:
        raw=io._read(fd,'manifest.json',io.META_LIMIT);require(io._hash(raw)==expected_sha256,'original selected output manifest differs')
        value=json.loads(raw);proof_raw=io._read(fd,'storage.json',io.META_LIMIT)
        require(io._hash(proof_raw)==value['storage_sha256'],'original output recovery proof differs')
        proof=json.loads(proof_raw);size,count=layout('mcm-output-f32',start['rows']*start['motifs'],cfg['part_bytes'])
        require(set(proof)=={'schema_version','format','binding','history','cells','f64_bytes','f64_sha256','f32_bytes','f32_sha256','parts','assumption'} and type(proof['schema_version']) is int and proof['schema_version']==1 and proof['format']=='mcm-output-recovery-proof-v1' and proof['binding']==binding and proof['cells']==start['rows']*start['motifs'] and proof['f64_bytes']==size*2 and proof['f32_bytes']==size and proof['parts']==count and proof['assumption']==ASSUMPTION,'original output cast/recovery binding differs')
        io._identity(proof['f64_sha256']);io._identity(proof['f32_sha256'])
        child,pin=output._file(fd,size);digest=hashlib.sha256();seen=0
        for index,part in enumerate(typed.iter_history_parts(proof['history'],binding=binding,kind='mcm-output-f32')):
            require(index<count and part['index']==index,'historical output order differs')
            expected=min(cfg['part_bytes'],size-index*cfg['part_bytes']);receipt=part['receipt']
            actual=read_exact(child,expected)
            require(receipt['bytes']==expected and hashlib.sha256(actual).hexdigest()==receipt['source_sha256'],'current local f32 bytes differ from original fresh-recovery proof')
            digest.update(actual);seen+=1
        require(seen==count and os.read(child,1)==b'' and digest.hexdigest()==proof['f32_sha256'],'output complete hash/order/EOF differs')
        require(pin==io._signature(os.fstat(child))==io._signature(os.stat('matrix.f32',dir_fd=fd,follow_symlinks=False)),'local original output changed')
        require(value==output._manifest(args,start,digest.hexdigest())|{'schema_version':2,'storage_sha256':io._hash(proof_raw)} and raw==io._json(value),'selected original output manifest fields differ')
        require(output._source(args)==start and io._read(fd,'storage.json',io.META_LIMIT)==proof_raw and io._read(fd,'manifest.json',io.META_LIMIT)==raw,'selected output anchors changed')
        output.stages.inventory(root,{'matrix.f32','manifest.json','storage.json'});io._root(root,fd)
        return value,pin
    finally:
        actions=[]
        if child is not None:actions.append(lambda:os.close(child))
        actions.append(lambda:os.close(fd));io._cleanup(actions)

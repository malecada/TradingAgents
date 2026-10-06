"""Draft node counts from bounded original headers and pinned accepted evidence.

No array payload read, numerical import, complete-body rehash or run authority.
The existing completed-body receipt schema and post-retirement stat schema are
explicitly supported; other evidence formats require a separately reviewed join.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct

META_MAX=4*1024**2
HEADER_MAX=10000

def need(ok,message):
    if not ok:raise ValueError(message)

def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def signature(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def mode(s):return stat.S_IMODE(s.st_mode)

def path_at(root,name):
    p=Path(name)
    need(not p.is_absolute() and '..' not in p.parts and not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in p.parts),'unsafe metadata/member path')
    p=root/p;need(p.resolve(strict=True)==p and p.is_relative_to(root),'redirected path')
    return p

def read_exact(fd,n):
    out=bytearray()
    while len(out)<n:
        b=os.read(fd,n-len(out));need(bool(b),'truncated metadata/header');out.extend(b)
    return bytes(out)

def metadata(root,ref):
    need(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'exact metadata reference required')
    need(type(ref['bytes']) is int and 0<ref['bytes']<=META_MAX,'bounded metadata required')
    p=path_at(root,ref['path']);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==ref['bytes'],'metadata type/extent differs')
        raw=read_exact(fd,before.st_size)
        need(signature(before)==signature(os.fstat(fd))==signature(p.lstat()) and mode(before)==mode(p.lstat()) and sha(raw)==ref['sha256'],'metadata identity/hash differs')
        return json.loads(raw)
    finally:os.close(fd)

def header(fd,extent,kind):
    """Read only magic, version, finite header length and captured header bytes."""
    magic=read_exact(fd,8);need(magic[:6]==b'\x93NUMPY' and magic[6:] in (b'\x01\x00',b'\x02\x00'),'unsupported original NPY version')
    width=2 if magic[6:]==b'\x01\x00' else 4
    prefix=read_exact(fd,width);length=struct.unpack('<H' if width==2 else '<I',prefix)[0]
    need(0<length<=HEADER_MAX and 8+width+length<=extent,'bounded header extent differs')
    raw=read_exact(fd,length);need(raw.endswith(b'\n'),'NPY header newline absent')
    tree=ast.parse(raw.decode('latin1').strip(),mode='eval')
    need(len(list(ast.walk(tree)))<=32 and isinstance(tree.body,ast.Dict),'bounded literal header required')
    keys=tree.body.keys;need(all(isinstance(k,ast.Constant) and type(k.value) is str for k in keys),'literal header keys required')
    need(len(keys)==3 and {k.value for k in keys}=={'descr','fortran_order','shape'},'exact unique NPY keys required')
    value=ast.literal_eval(tree)
    need(value['fortran_order'] is False and type(value['shape']) is tuple and all(type(n) is int and 0<n<2**63 for n in value['shape']),'original C-contiguous positive shape required')
    descr=value['descr'];shape=value['shape']
    if kind=='node_features':
        need(descr in ('<f4','<f8') and len(shape)==2,'original floating feature matrix required');itemsize=int(descr[2:])
    elif kind=='node_ids':
        need(type(descr) is str and re.fullmatch(r'<U[1-9][0-9]{0,3}',descr) is not None and len(shape)==1,'original nonobject Unicode node vector required');itemsize=4*int(descr[2:])
    else:raise ValueError('only node feature/id headers allowed')
    offset=8+width+length;need(offset+math.prod(shape)*itemsize==extent,'header shape/dtype extent differs')
    captured=magic+prefix+raw
    return {'shape':list(shape),'descr':descr,'fortran_order':False,'npy_version':list(magic[6:]),'header_bytes_read':len(captured),'header_sha256':sha(captured),'captured_header_hex':captured.hex(),'payload_bytes_read':0}

def _join(review,ref):need(review.get('evidence',{}).get(ref['path'])==ref['sha256'],'accepted evidence edge absent')
def _one(rows,path):
    matches=[r for r in rows if r['path']==path];need(len(matches)==1,'unique accepted original row absent');return matches[0]

def observe(root,refs):
    """Caller supplies pinned actual accepted receipts, never self-asserted booleans."""
    root=Path(root);need(root.is_absolute() and root.resolve(strict=True)==root,'canonical root required')
    need(set(refs)=={'manifest','body_hash','completion_review','preservation_review','disposition_review','retirement_complete'},'exact declared evidence chain required')
    docs={k:metadata(root,r) for k,r in refs.items()}
    complete=docs['completion_review'];preserved=docs['preservation_review'];disposition=docs['disposition_review'];retired=docs['retirement_complete']
    need(complete.get('decision')=='accepted' and complete.get('outcome',{}).get('graph_manifest_sha256')==refs['manifest']['sha256'],'accepted completed graph required')
    _join(complete,refs['manifest']);_join(complete,refs['body_hash'])
    need(preserved.get('decision')=='accepted' and preserved.get('full_scope_byte_recovery') is True,'accepted body preservation required')
    _join(preserved,refs['completion_review']);_join(preserved,refs['body_hash']);_join(preserved,refs['manifest'])
    need(disposition.get('decision')=='accepted-actual-two-file-retirement-metadata-readback','compatible accepted current disposition required')
    _join(disposition,refs['preservation_review']);_join(disposition,refs['retirement_complete'])
    need(retired.get('arrays_retained') is True and retired.get('identity')==disposition.get('identity'),'retirement disposition differs')
    body=docs['body_hash'];need(body.get('decision')=='pass','accepted completed body pass absent')
    graph=docs['manifest'];need(set(graph)=={'metadata','graph_hash','arrays'},'graph manifest fields differ')
    need(graph['graph_hash']==complete['outcome']['graph_hash'],'completed graph identity differs')
    directory=Path(refs['manifest']['path']).parent;observations={}
    for name in ('node_features','node_ids'):
        descriptor=graph['arrays'][name];need(set(descriptor)=={'path','sha256','bytes'} and descriptor['path']==name+'.npy','original member descriptor differs')
        relative=str(directory/descriptor['path']);need(relative not in retired['removed'] and relative not in disposition['removed_paths_absent'],'original array retired')
        b=_one(body['files'],relative);s=_one(disposition['rows'],relative)
        need(b['sha256']==descriptor['sha256']==s['sha256_inherited'] and b['bytes']==descriptor['bytes']==s['bytes'],'inherited body hash/extent differs')
        p=path_at(root,relative);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
        try:
            before=os.fstat(fd);need(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and signature(before)==b['stat_identity'],'original full-body identity changed')
            need([before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns]==s['original_stat_identity'] and mode(before)==s['mode'],'accepted disposition identity/mode changed')
            obs=header(fd,before.st_size,name)
            need(signature(before)==signature(os.fstat(fd))==signature(p.lstat()) and mode(before)==mode(p.lstat()),'member changed during header observation')
            observations[name]=dict(obs,path=relative,body_sha256_inherited=b['sha256'],body_bytes_inherited=b['bytes'],stat_identity=signature(before),mode=mode(before))
        finally:os.close(fd)
    rows=observations['node_features']['shape'][0];need(rows==observations['node_ids']['shape'][0],'node feature/id row count differs')
    return {'schema_version':1,'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','method':'retained-header-only','graph_manifest_sha256':refs['manifest']['sha256'],'graph_hash':graph['graph_hash'],'rows':rows,'evidence_chain':refs,'observations':observations,'array_payload_bytes_read':0,'full_body_hash_passes_performed':0,'qualification':'Counts come from parsed original headers and matching dimensions, not file-size inference. Complete body hashes are inherited from accepted historical receipts joined to unchanged current inode/link/extent/mode/mtime/ctime. Headers are freshly observed; unchanged metadata is sampled evidence, not immutable writer exclusion, a fresh complete-body hash, semantic graph validation or admission.'}

def publish(root,refs,evidence_path,count_path):
    evidence=observe(root,refs);root=Path(root);evidence_path=Path(evidence_path);count_path=Path(count_path)
    need(evidence_path.parent.resolve()==evidence_path.parent and count_path.parent.resolve()==count_path.parent and evidence_path.is_relative_to(root) and count_path.is_relative_to(root),'output must be canonical inside root')
    raw=encode(evidence)
    with evidence_path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    wrapper={'schema_version':1,'kind':'graph-node-count-metadata-v1','graph_manifest_sha256':refs['manifest']['sha256'],'node_features_sha256':evidence['observations']['node_features']['body_sha256_inherited'],'rows':evidence['rows'],'method':'retained-header-only','evidence':{'path':str(evidence_path.relative_to(root)),'sha256':sha(raw),'bytes':len(raw)}}
    with count_path.open('xb') as stream:stream.write(encode(wrapper));stream.flush();os.fsync(stream.fileno())
    return wrapper

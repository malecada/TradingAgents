"""Semantic batch recovery helpers; no authority grant or transport mock."""
import hashlib,json,os,struct,tarfile
from pathlib import Path
from . import preservation,batched_journal
TOKEN=struct.Struct('>QQQ32s')
SUFFIXES=('.pending.json','.records.bin','.complete.json')
def require(ok,message):
    if not ok:raise ValueError(message)
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def binding(journal,batch,tokens,manifest):
    require(type(journal) is batched_journal.BatchJournal,'exact admitted batched journal required')
    require(type(batch) is int and batch>=0 and len(tokens)==3*TOKEN.size,'batch token extent')
    return {'format':'mcm-batched-bundle-v3','batch':batch,'root':str(journal.root),'root_pin':list(journal.pin),'source_tokens':bytes(tokens).hex(),'manifest_sha256':sha(raw(manifest))}
def current(journal,batch,tokens):
    require(type(journal) is batched_journal.BatchJournal,'exact admitted batched journal required')
    journal._root();rows=journal.read_complete(batch)
    for index,suffix in enumerate(SUFFIXES):
        dev,ino,size,digest=TOKEN.unpack_from(tokens,index*TOKEN.size)
        data,_=journal._read(f'{batch:08d}'+suffix,pin=(dev,ino))
        require(len(data)==size and hashlib.sha256(data).digest()==digest,'source batch currentness differs')
    journal._root();return rows

def recover(data,manifest,journal,batch,tokens,directory):
    require(type(journal) is batched_journal.BatchJournal,'exact admitted batched journal required')
    require(type(data) is bytes and 0<len(data)<=4*1024**2 and len(tokens)==3*TOKEN.size,'bounded recovered bundle required')
    require(manifest['files']==3 and len(manifest['members'])==3,'three batch members required')
    require(directory.parent.resolve()==directory.parent,'canonical recovery parent required');directory.mkdir(exist_ok=False)
    archive=directory/'recovered.tar'
    with archive.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    preservation.verify_bundle(archive,manifest)
    reader=type(journal)(directory/'tree',batch_cells=4096,max_cells=2**63,max_bytes=4*1024**2,max_body_bytes=1024**2,boundary=lambda:None)
    try:
        with tarfile.open(archive,'r:') as tar:
            members=tar.getmembers();require(len(members)==3,'archive denominator differs')
            for index,(member,suffix) in enumerate(zip(members,SUFFIXES,strict=True)):
                require(member.isfile() and member.name==f'files/{batch*3+index:08d}','archive member order differs')
                with tar.extractfile(member) as handle:payload=handle.read(4*1024**2+1)
                dev,ino,size,digest=TOKEN.unpack_from(tokens,index*TOKEN.size)
                require(len(payload)==size and hashlib.sha256(payload).digest()==digest,'recovered original bytes differ')
                reader._write(f'{batch:08d}'+suffix,payload,4*1024**2)
        rows=reader.read_complete(batch)
        # Recorded closure is durable and bound to the original bytes, not pins
        # invented for reconstructed files. Recovery copies are never originals.
        evidence={'schema_version':1,'format':'batched-semantic-recovery-v1','binding':binding(journal,batch,tokens,manifest),'archive_sha256':sha(data),'start':rows[0][0],'stop':rows[-1][0]+1,'files':3,'root_pin':list(reader.pin)}
        with (directory/'verified.json').open('xb') as f:f.write(raw(evidence));f.flush();os.fsync(f.fileno())
        fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
        return evidence
    finally:reader.close()

def dispose_recovery(directory,manifest,batch,tokens):
    """Dispose only freshly generated recovery bodies; verified.json remains."""
    from .typed_payload_operations import dispose
    for index,suffix in enumerate(SUFFIXES):
        dev,ino,size,digest=TOKEN.unpack_from(tokens,index*TOKEN.size)
        dispose(directory/'tree'/(f'{batch:08d}'+suffix),size,digest.hex())
    (directory/'tree').rmdir()
    dispose(directory/'recovered.tar',manifest['archive_bytes'],manifest['archive_sha256'])

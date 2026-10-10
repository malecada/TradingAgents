"""Bounded original-byte group validation; no authority or transport construction."""
import hashlib,json,os,tarfile
from pathlib import Path
from . import preservation,batched_journal,batched_offload_semantics as single
TOKEN=single.TOKEN;SUFFIXES=single.SUFFIXES;LIMIT=4*1024**2;MAX_BATCHES=16
require=single.require;raw=single.raw;sha=single.sha

def roster(value):
    require(type(value) is tuple and 0<len(value)<=MAX_BATCHES,'finite group tuple required')
    first=None
    for i,item in enumerate(value):
        require(type(item) is tuple and len(item)==2 and type(item[0]) is int and item[0]>=0 and type(item[1]) is bytes and len(item[1])==3*TOKEN.size,'group batch/token shape')
        if first is None:first=item[0]
        require(item[0]==first+i,'group batches must be consecutive ordered')
    return value

def binding(journal,items,manifest):
    items=roster(items);require(type(journal) is batched_journal.BatchJournal,'exact shared journal required')
    require(manifest['files']==3*len(items) and len(manifest['members'])==3*len(items) and 0<manifest['archive_bytes']<=LIMIT,'group manifest extent')
    result={'format':'mcm-batched-group-v1','first_batch':items[0][0],'batches':len(items),'root':str(journal.root),'root_pin':list(journal.pin),'source_tokens':b''.join(t for _,t in items).hex(),'manifest_sha256':sha(raw(manifest))}
    require(len(raw(result))<=8192,'typed group binding extent');return result

def from_binding(value):
    require(value['format']=='mcm-batched-group-v1' and type(value['first_batch']) is int and type(value['batches']) is int and 0<value['batches']<=MAX_BATCHES,'group binding format')
    tokens=bytes.fromhex(value['source_tokens']);require(len(tokens)==value['batches']*3*TOKEN.size,'group token extent')
    return roster(tuple((value['first_batch']+i,tokens[i*3*TOKEN.size:(i+1)*3*TOKEN.size]) for i in range(value['batches'])))

def current(journal,items):
    items=roster(items);start=stop=None;cells=0
    for batch,tokens in items:
        rows=single.current(journal,batch,tokens)
        require(rows and all(row[0]==rows[0][0]+i for i,row in enumerate(rows)),'group record ordinal continuity')
        if start is None:start=rows[0][0]
        else:require(rows[0][0]==stop,'group cell range gap')
        stop=rows[-1][0]+1;cells+=len(rows);del rows
    return {'start':start,'stop':stop,'cells':cells,'first_batch':items[0][0],'batches':len(items)}

def source_rows(journal,items):
    current(journal,items);source=[]
    for batch,tokens in items:
        for index,suffix in enumerate(SUFFIXES):
            _,_,size,digest=TOKEN.unpack_from(tokens,index*TOKEN.size);path=journal.root/f'{batch:08d}{suffix}';st=path.stat()
            source.append({'source_path':str(path),'resolved_path':str(path),'bytes':size,'mtime_ns':st.st_mtime_ns,'expected_sha256':digest.hex()})
    return source

def archive_bound(rows):
    size=((sum(512+((r['bytes']+511)//512)*512 for r in rows)+1024+10239)//10240)*10240
    require(0<size<=LIMIT,'group archive exceeds4MiB');return size

def recover(data,manifest,journal,items,directory,consume=None):
    items=roster(items);bound=binding(journal,items,manifest)
    require(type(data) is bytes and 0<len(data)==manifest['archive_bytes']<=LIMIT,'group recovered bytes extent')
    directory=Path(directory);require(directory.parent.resolve()==directory.parent,'canonical group recovery parent');directory.mkdir(exist_ok=False)
    archive=directory/'recovered.tar'
    with archive.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    preservation.verify_bundle(archive,manifest)
    reader=batched_journal.BatchJournal(directory/'tree',batch_cells=4096,max_cells=2**63,max_bytes=LIMIT,max_body_bytes=1024**2,boundary=lambda:None)
    primary=None
    try:
        with tarfile.open(archive,'r:') as tar:
            members=tar.getmembers();require(len(members)==3*len(items),'group member denominator')
            for position,member in enumerate(members):
                offset,index=divmod(position,3);batch,tokens=items[offset]
                require(member.isfile() and member.name==f'files/{batch*3+index:08d}','group member order differs')
                _,_,size,digest=TOKEN.unpack_from(tokens,index*TOKEN.size)
                require(member.size==size<=LIMIT,'group member extent')
                with tar.extractfile(member) as handle:body=handle.read(LIMIT+1)
                require(len(body)==size and hashlib.sha256(body).digest()==digest,'group original body hash')
                reader._write(f'{batch:08d}{SUFFIXES[index]}',body,LIMIT)
        # Reconstructed identities differ; verify original bytes, then actual journal semantics.
        start=stop=None
        for batch,_ in items:
            rows=reader.read_complete(batch)
            require(rows and all(row[0]==rows[0][0]+i for i,row in enumerate(rows)),'recovered group ordinal continuity')
            if start is None:start=rows[0][0]
            else:require(rows[0][0]==stop,'recovered group range gap')
            stop=rows[-1][0]+1
            if consume is not None:consume(batch,rows);require(rows==reader.read_complete(batch),'group consumer changed its batch')
            del rows
        # All callbacks have ended: repeat every original-byte hash and every semantic read.
        for batch,tokens in items:
            for index,suffix in enumerate(SUFFIXES):
                body,_=reader._read(f'{batch:08d}{suffix}');_,_,size,digest=TOKEN.unpack_from(tokens,index*TOKEN.size)
                require(len(body)==size and hashlib.sha256(body).digest()==digest,'group changed during consumer')
            reader.read_complete(batch)
        reader._root()
        evidence={'schema_version':1,'format':'group-semantic-recovery-v1','binding':bound,'archive_sha256':sha(data),'start':start,'stop':stop,'files':3*len(items),'root_pin':list(reader.pin)}
        with (directory/'verified.json').open('xb') as stream:stream.write(raw(evidence));stream.flush();os.fsync(stream.fileno())
        fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
        sync_error=None
        try:os.fsync(fd)
        except BaseException as error:sync_error=error;raise
        finally:
            try:os.close(fd)
            except BaseException as cleanup:
                if sync_error is None:raise
                sync_error.add_note('group sync cleanup: '+repr(cleanup))
        return evidence
    except BaseException as error:primary=error;raise
    finally:
        try:reader.close()
        except BaseException as cleanup:
            if primary is None:raise
            primary.add_note('group reader cleanup: '+repr(cleanup))

def dispose_recovery(directory,manifest,items):
    from .typed_payload_operations import dispose
    directory=Path(directory)
    for batch,tokens in roster(items):
        for index,suffix in enumerate(SUFFIXES):
            _,_,size,digest=TOKEN.unpack_from(tokens,index*TOKEN.size)
            dispose(directory/'tree'/f'{batch:08d}{suffix}',size,digest.hex())
    (directory/'tree').rmdir();dispose(directory/'recovered.tar',manifest['archive_bytes'],manifest['archive_sha256'])

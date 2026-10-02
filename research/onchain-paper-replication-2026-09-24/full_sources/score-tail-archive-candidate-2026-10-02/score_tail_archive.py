"""Engineering candidate: exact 80-byte tail codec and retained local archive seal.

No numerical imports, network, disposal or live producer substitution. LocalChunk
is a storage primitive, NOT Owner/ResearchRun authority. Its externally trusted
contract must be derived by an admitted owner adapter before empirical use.
Receipt semantics explicitly mean local verification, never remote recovery.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys

MAX_CELLS=65536
MAX_BYTES=8*1024**2
META=8192
BLOCK=65536
FRAME=struct.Struct('<Qd32s')
SCOPE={'graph','node_order','dictionary','ordered_motifs','matching','workflow'}
HASHES={'owner','stage_intent_sha256','job_sha256','binding_sha256','original_matching_sha256',
    'previous_mapping_sha256','batch_start_sha256','batch_previous_sha256','transport_identity',
    'tail_start_sha256','tail_terminal_sha256','batch_header_sha256','batch_payload_sha256'}
FIELDS=HASHES|{'schema_version','format','stage','source_commit','job_input','scope','ordered_motifs',
    'rows','motifs','chunk_cells','index','batch_directory','remote'}
MEMBERS={'contract.json','tail-start.json','tail-terminal.json','records.bin','batch-header.json','batch.bin','complete.json'}


def require(test,message):
    if not test:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def identity(value):require(type(value) is str and re.fullmatch('[0-9a-f]{64}',value),'hash identity differs')


def encode(value):
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    require(len(raw)<=META,'metadata bound exceeded');return raw


def decode(raw):
    require(type(raw) is bytes and len(raw)<=META,'bounded metadata required')
    value=json.loads(raw)
    require(type(value) is dict and encode(value)==raw,'canonical metadata object required');return value


def contract(value):
    require(type(value) is dict and set(value)==FIELDS,'tail archive contract schema')
    require(type(value['schema_version']) is int and value['schema_version']==1
        and value['format']=='score-tail-archive-v1','tail archive format')
    for key in HASHES:identity(value[key])
    require(type(value['source_commit']) is str and re.fullmatch('[0-9a-f]{40}',value['source_commit']),'source commit')
    require(type(value['scope']) is dict and set(value['scope'])==SCOPE,'tail scope schema')
    for v in value['scope'].values():identity(v)
    require(type(value['ordered_motifs']) is list and len(value['ordered_motifs'])==32,'exact 32 ordered motifs required')
    for v in value['ordered_motifs']:identity(v)
    require(digest(json.dumps(value['ordered_motifs'],separators=(',',':')).encode())==value['scope']['ordered_motifs'],'ordered motif identity differs')
    require(type(value['stage']) is str and value['stage']=='mcm-'+value['scope']['graph'],'graph/stage differs')
    require(type(value['job_input']) is str and re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,127}',value['job_input']),'job input')
    require(type(value['remote']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,127}',value['remote']),'remote object name')
    for key in ('rows','motifs','chunk_cells','index'):require(type(value[key]) is int,'integer denominator required')
    total=value['rows']*32
    require(value['rows']>0 and total<2**63 and value['motifs']==32
        and 0<value['chunk_cells']<=MAX_CELLS and 0<=value['index']<10**12
        and value['index']*value['chunk_cells']<total,'tail archive denominator')
    path=Path(value['batch_directory'])
    require(type(value['batch_directory']) is str and path.is_absolute() and '..' not in path.parts,'batch directory')
    return decode(encode(value))


def verify_bytes(value,start_raw,terminal_raw,records,header_raw,payload):
    """Callback-free exact original tail and float64-batch comparison, <=5 MiB.

    Purpose hashes are preserved and ordered, but derivation from actual graph
    neighborhoods remains the genuine matcher/stage's separate responsibility.
    """
    c=contract(value);begin=c['index']*c['chunk_cells'];cells=min(c['chunk_cells'],c['rows']*32-begin)
    require(type(records) is bytes and len(records)==cells*80<=MAX_BYTES
        and type(payload) is bytes and len(payload)==cells*8,'tail/batch exact extent')
    for raw,key in ((start_raw,'tail_start_sha256'),(terminal_raw,'tail_terminal_sha256'),(header_raw,'batch_header_sha256'),(payload,'batch_payload_sha256')):
        require(type(raw) is bytes and digest(raw)==c[key],'tail/batch source hash differs')
    start=decode(start_raw);terminal=decode(terminal_raw);header=decode(header_raw)
    destination=digest(encode(dict(directory=c['batch_directory'],start_sha256=c['batch_start_sha256'],
        index=c['index'],start_cell=begin,cells=cells)))
    expected=dict(schema_version=1,kind='mcm-score-tail',scope=c['scope'],owner=c['owner'],start_cell=begin,cells=cells,
        destination=destination,record_format='<Qd32s32s',record_bytes=80)
    require(start==expected and all(type(start[k]) is int for k in ('schema_version','start_cell','cells','record_bytes')),'tail start differs')
    require(set(terminal)=={'schema_version','start_sha256','status','reason','acknowledged_cells','head','records_bytes','records_sha256'}
        and type(terminal['schema_version']) is int and terminal['schema_version']==1
        and type(terminal['acknowledged_cells']) is int and terminal['acknowledged_cells']==cells
        and type(terminal['records_bytes']) is int and terminal['records_bytes']==len(records)
        and terminal['start_sha256']==c['tail_start_sha256'] and terminal['records_sha256']==digest(records)
        and terminal['status']=='complete' and terminal['reason']=='','complete original tail required')
    expected_header=dict(schema_version=1,start_sha256=c['batch_start_sha256'],previous=c['batch_previous_sha256'],
        index=c['index'],start_cell=begin,cells=cells,payload_sha256=c['batch_payload_sha256'])
    require(header==expected_header and all(type(header[k]) is int for k in ('schema_version','index','start_cell','cells')),'batch header differs')
    head=c['tail_start_sha256'];scores=hashlib.sha256()
    for slot in range(cells):
        raw=records[slot*80:(slot+1)*80];frame=raw[:48];ordinal,score,purpose=FRAME.unpack(frame)
        head=digest(bytes.fromhex(head)+frame)
        require(ordinal==begin+slot and math.isfinite(score) and 0<=score<=1
            and raw[48:]==bytes.fromhex(head) and frame[8:16]==payload[slot*8:(slot+1)*8],
            'tail order, float64 value or checksum differs')
        scores.update(frame)
    require(head==terminal['head'],'tail acknowledged head differs')
    return dict(schema_version=1,contract_sha256=digest(encode(c)),start_cell=begin,cells=cells,
        payload_sha256=digest(records),head=head,score_sha256=scores.hexdigest(),
        batch_payload_sha256=digest(payload),semantics='local-bytes-verified-only',remote_verified=False)


class CleanupFailure(BaseException):pass


def cleanup(actions,primary=None):
    """Each descriptor once; retain the first fatal object even across cleanup."""
    failures=[]
    for action in actions:
        try:action()
        except BaseException as error:failures.append(error)
    if not failures:return
    candidates=(([primary] if primary is not None else [])+failures)
    fatal=next((e for e in candidates if not isinstance(e,Exception) or isinstance(e,MemoryError)),None)
    if fatal is None:fatal=CleanupFailure('owned descriptor cleanup uncertain; stop worker')
    for error in failures:
        if error is not fatal:fatal.add_note('cleanup: '+repr(error))
    raise fatal from (primary if primary is not fatal else None)


def signature(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))


def name_check(name):require(type(name) is str and re.fullmatch('[a-z][a-z0-9.-]{0,63}',name),'single owned member name required')


def root_check(root,fd):
    s=os.fstat(fd);p=root.lstat()
    require(root.resolve()==root and stat.S_ISDIR(p.st_mode) and (s.st_dev,s.st_ino)==(p.st_dev,p.st_ino),'directory redirected')


def open_root(root):
    root=Path(root);require(root.is_absolute() and root.resolve()==root,'canonical owned directory required')
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:root_check(root,fd)
    except BaseException as error:cleanup((lambda:os.close(fd),),error);raise
    return root,fd


def read_member(fd,name,limit):
    name_check(name);require(type(limit) is int and 0<limit<=MAX_BYTES,'read bound')
    child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=fd)
    try:
        before=os.fstat(child)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<=before.st_size<=limit,'regular unaliased bounded file required')
        blocks=[];remaining=before.st_size
        while remaining:
            raw=os.read(child,min(BLOCK,remaining));require(bool(raw),'truncated member');blocks.append(raw);remaining-=len(raw)
        require(not os.read(child,1) and signature(before)==signature(os.fstat(child))
            ==signature(os.stat(name,dir_fd=fd,follow_symlinks=False)),'member identity changed')
        return b''.join(blocks)
    finally:cleanup((lambda:os.close(child),),sys.exception())


def publish(fd,name,raw):
    """Exclusive bounded write + fsync; no overwrite, unlink or descriptor retry."""
    name_check(name);require(type(raw) is bytes and len(raw)<=MAX_BYTES,'write bound')
    child=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=fd)
    try:
        before=os.fstat(child);position=0
        while position<len(raw):
            n=os.write(child,raw[position:position+BLOCK]);require(n>0,'write made no progress');position+=n
        os.fsync(child);after=os.fstat(child)
        require(stat.S_ISREG(after.st_mode) and after.st_nlink==1 and after.st_size==len(raw)
            and (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino)
            and signature(after)==signature(os.stat(name,dir_fd=fd,follow_symlinks=False)),'published member identity changed')
    finally:cleanup((lambda:os.close(child),),sys.exception())
    os.fsync(fd);require(read_member(fd,name,max(1,len(raw)))==raw,'published readback differs')
    return digest(raw)


def publish_receipt(fd,name,raw):
    """Atomically link a fully fsynced new receipt; never overwrite a target.

    Only this invocation's successful pending hardlink is removed. Any failure
    leaves all partial evidence. Readers reject the temporary two-link state.
    """
    name_check(name);require(type(raw) is bytes and len(raw)<=META,'receipt metadata bound')
    pending='pending-'+name
    publish(fd,pending,raw)
    before=os.stat(pending,dir_fd=fd,follow_symlinks=False)
    require(stat.S_ISREG(before.st_mode) and before.st_nlink==1,'pending receipt identity')
    os.link(pending,name,src_dir_fd=fd,dst_dir_fd=fd,follow_symlinks=False)
    for member in (pending,name):
        now=os.stat(member,dir_fd=fd,follow_symlinks=False)
        require(now.st_nlink==2 and (now.st_dev,now.st_ino)==(before.st_dev,before.st_ino),
            'receipt link publication differs')
    os.fsync(fd);os.unlink(pending,dir_fd=fd);os.fsync(fd)
    require(read_member(fd,name,max(1,len(raw)))==raw,'atomic receipt readback differs')
    return digest(raw)


def inventory(fd,names):
    seen=set()
    with os.scandir(fd) as entries:
        for entry in entries:
            require(entry.name in names and entry.name not in seen,'unexpected archive member');seen.add(entry.name)
    require(seen==names,'missing archive member')


class LocalChunk:
    """Single-use retained byte snapshot, not upload or source-disposal authority."""
    def __init__(self,root,value,*,lease):
        self.contract=contract(value);self.pin=encode(self.contract);require(callable(lease),'live storage lease required')
        self.lease=lease;self.closed=False;self.fd=None
        self.root=Path(root);require(self.root.is_absolute() and self.root.resolve()==self.root,'canonical new directory required')
        lease();parent,pfd=open_root(self.root.parent)
        try:
            try:
                root_check(parent,pfd);os.mkdir(self.root.name,mode=0o700,dir_fd=pfd);os.fsync(pfd)
                self.root,self.fd=open_root(self.root);root_check(parent,pfd)
            finally:cleanup((lambda:os.close(pfd),),sys.exception())
        except BaseException as error:
            self.close(primary=error);raise
        try:
            publish(self.fd,'contract.json',self.pin);self._check()
        except BaseException as error:self.close(primary=error);raise
    def _check(self):
        require(not self.closed,'chunk terminal');self.lease()
        require(encode(self.contract)==self.pin,'chunk contract changed during callback');root_check(self.root,self.fd)
        require(read_member(self.fd,'contract.json',META)==self.pin,'contract source changed')
    def seal(self,*parts):
        try:
            self._check();result=verify_bytes(self.contract,*parts)
            names=('tail-start.json','tail-terminal.json','records.bin','batch-header.json','batch.bin')
            for name,raw in zip(names,parts,strict=True):self._check();publish(self.fd,name,raw)
            self._check()
            saved=tuple(read_member(self.fd,n,MAX_BYTES if n in ('records.bin','batch.bin') else META) for n in names)
            require(saved==parts and verify_bytes(self.contract,*saved)==result,'snapshot changed')
            raw=encode(result);ref=publish_receipt(self.fd,'complete.json',raw)
            self._check();inventory(self.fd,MEMBERS)
            require(read_local(self.root,contract=self.contract,receipt_sha256=ref,lease=lambda:None)==result,'sealed snapshot differs')
            self.close();return ref
        except BaseException as error:self.close(primary=error);raise
    def close(self,primary=None):
        if self.closed:return
        self.closed=True;fd=self.fd;self.fd=None
        if fd is not None:cleanup((lambda:os.close(fd),),primary)


def read_local(root,*,contract,receipt_sha256,lease):
    """A local snapshot cannot assert remote availability or numerical authority."""
    c=globals()['contract'](contract);identity(receipt_sha256);require(callable(lease),'live read lease required');lease()
    path,fd=open_root(root)
    try:
        inventory(fd,MEMBERS);pin=encode(c);require(read_member(fd,'contract.json',META)==pin,'local contract differs')
        names=('tail-start.json','tail-terminal.json','records.bin','batch-header.json','batch.bin')
        parts=tuple(read_member(fd,n,MAX_BYTES if n in ('records.bin','batch.bin') else META) for n in names)
        result=verify_bytes(c,*parts);raw=read_member(fd,'complete.json',META)
        require(raw==encode(result) and digest(raw)==receipt_sha256,'local completion differs')
        lease();root_check(path,fd);inventory(fd,MEMBERS)
        require(read_member(fd,'contract.json',META)==pin and read_member(fd,'complete.json',META)==raw,'metadata changed after lease')
        for n,expected in zip(names,parts,strict=True):require(read_member(fd,n,max(1,len(expected)))==expected,'body changed after lease')
        return result
    finally:cleanup((lambda:os.close(fd),),sys.exception())

"""Original COMPLETE-tail content adapter; metadata pins are caller-authenticated.

No Owner or provenance capability is constructed here. Emitted chunks are
provisional retained bytes until the complete tail/batch verification returns.
Transport uses existing archive_chunks, never its byte receipt as semantic proof.
"""
from dataclasses import dataclass
from contextlib import contextmanager
import hashlib, math, os, stat, sys, time
from pathlib import Path
from . import score_tail_archive as bank
from . import score_tail_semantics as semantic

require=bank.require
MAX_FILE_BYTES=4*1024**2
CHUNK_BYTES=(MAX_FILE_BYTES//80)*80
NAMES={'intent','stage','stream_start','stream_complete','seal','batch_start','batch_header','tail_start','tail_terminal'}

@dataclass(frozen=True)
class Binding:
    contract_raw: bytes
    metadata: tuple
    pins: tuple
    previous_seal: str
    chunk_records: int
    max_file_bytes: int
    @property
    def identity(self):
        return bank.digest(bank.encode({'contract':bank.digest(self.contract_raw),'pins':dict(self.pins),'previous_seal':self.previous_seal,'chunk_records':self.chunk_records,'max_file_bytes':self.max_file_bytes}))


def bind(value,metadata,pins,*,previous_seal,chunk_records,max_file_bytes):
    """Join trusted original pins; syntactic agreement does not authenticate them.

    The caller must derive pins/contract/previous seal from the genuine original
    closed Stage, Target, Binding, roster and source, not from an archive receipt.
    This function checks one tail, not the complete original history roster.
    """
    require(type(max_file_bytes) is int and 65536<=max_file_bytes<=MAX_FILE_BYTES and type(chunk_records) is int and 0<chunk_records<=max_file_bytes//80,'explicit finite record-aligned chunk/native-file bound')
    c=bank.contract(value);require(len(c['remote'])<=116,'remote prefix must leave room for typed chunk suffix');require(set(metadata)==set(pins)==NAMES,'exact original metadata set')
    bank.identity(previous_seal);decoded={}
    for name in sorted(NAMES):
        bank.identity(pins[name]);raw=metadata[name]
        require(type(raw) is bytes and bank.digest(raw)==pins[name],'original '+name+' pin differs')
        decoded[name]=bank.decode(raw)
    def exact(name,expected,ints):
        v=decoded[name];require(v==expected and all(type(v[k]) is int for k in ints),name+' schema/binding differs')
    total=c['rows']*32;first=c['index']*c['chunk_cells'];count=min(c['chunk_cells'],total-first)
    for name,key in [('intent','stage_intent_sha256'),('batch_start','batch_start_sha256'),('batch_header','batch_header_sha256'),('tail_start','tail_start_sha256'),('tail_terminal','tail_terminal_sha256')]:
        require(pins[name]==c[key],name+' contract differs')
    intent=decoded['intent'];stage=decoded['stage']
    require(type(intent.get('scope')) is dict and set(intent['scope'])=={'workflow','config','policy','context','numerical_source'},'original event scope schema')
    for v in intent['scope'].values():bank.identity(v)
    require(set(intent)=={'schema_version','owner','stage','kind','scope','pairs','logical_reservation_bytes','policy_sha256'} and type(intent['schema_version']) is int and intent['schema_version']==1 and intent['owner']==c['owner'] and intent['stage']==c['stage'] and intent['kind']=='mcm' and type(intent['pairs']) is int and intent['pairs']==total and type(intent['logical_reservation_bytes']) is int and intent['logical_reservation_bytes']>0,'original exact MCM stage intent differs')
    stage_fields={'schema_version','kind','owner','scope','policy_sha256','completed_pairs','log_terminal_sha256','stream_terminal_sha256','stream_start_sha256','log_start_sha256','matching_scores_sha256','checkpoints','checkpoint_logical_bytes','checkpoints_sha256','execution_admitted'}
    require(set(stage)==stage_fields and type(stage['schema_version']) is int and stage['schema_version']==1 and stage['kind']=='mcm' and stage['owner']==c['owner'] and stage['scope']==intent['scope'] and stage['scope']['workflow']==c['scope']['workflow'] and stage['policy_sha256']==intent['policy_sha256'] and type(stage['completed_pairs']) is int and stage['completed_pairs']==total and stage['execution_admitted'] is False,'closed original stage receipt differs')
    for k in ('policy_sha256','log_terminal_sha256','stream_terminal_sha256','stream_start_sha256','log_start_sha256','matching_scores_sha256','checkpoints_sha256'):bank.identity(stage[k])
    for k in ('checkpoints','checkpoint_logical_bytes'):require(type(stage[k]) is int and 0<=stage[k]<2**63,'stage bounded count')
    require(stage['stream_terminal_sha256']==pins['stream_complete'] and stage['stream_start_sha256']==pins['stream_start'],'stage/stream pins differ')
    exact('stream_start',dict(schema_version=1,kind='mcm-score-stream',scope=c['scope'],owner=c['owner'],rows=c['rows'],motifs=32,batch_start_sha256=c['batch_start_sha256'],chunk_cells=c['chunk_cells']),('schema_version','rows','motifs','chunk_cells'))
    complete=decoded['stream_complete'];chunks=(total+c['chunk_cells']-1)//c['chunk_cells']
    require(set(complete)=={'schema_version','start_sha256','head','cells','chunks','batch_terminal_sha256'} and all(type(complete[k]) is int for k in ('schema_version','cells','chunks')) and complete['schema_version']==1 and complete['start_sha256']==pins['stream_start'] and complete['cells']==total and complete['chunks']==chunks,'original stream completion denominator')
    bank.identity(complete['head']);bank.identity(complete['batch_terminal_sha256'])
    if c['index']==0:
        require(previous_seal==pins['stream_start'],'first seal predecessor differs')
        require(c['batch_previous_sha256']==c['batch_start_sha256'],'first batch predecessor differs')
    if c['index']==chunks-1:require(complete['head']==pins['seal'],'last seal differs from complete head')
    exact('seal',dict(schema_version=1,start_sha256=pins['stream_start'],previous=previous_seal,index=c['index'],start_cell=first,cells=count,tail_terminal_sha256=c['tail_terminal_sha256'],batch_header_sha256=c['batch_header_sha256']),('schema_version','index','start_cell','cells'))
    exact('batch_start',dict(schema_version=1,scope=c['scope'],owner=c['owner'],rows=c['rows'],motifs=32,chunk_cells=c['chunk_cells'],dtype='<f8',order='row-major'),('schema_version','rows','motifs','chunk_cells'))
    exact('batch_header',dict(schema_version=1,start_sha256=c['batch_start_sha256'],previous=c['batch_previous_sha256'],index=c['index'],start_cell=first,cells=count,payload_sha256=c['batch_payload_sha256']),('schema_version','index','start_cell','cells'))
    destination=bank.digest(bank.encode(dict(directory=c['batch_directory'],start_sha256=c['batch_start_sha256'],index=c['index'],start_cell=first,cells=count)))
    exact('tail_start',dict(schema_version=1,kind='mcm-score-tail',scope=c['scope'],owner=c['owner'],start_cell=first,cells=count,destination=destination,record_format='<Qd32s32s',record_bytes=80),('schema_version','start_cell','cells','record_bytes'))
    t=decoded['tail_terminal']
    require(set(t)==semantic.TERMINAL_FIELDS and type(t['schema_version']) is int and t['schema_version']==1 and t['start_sha256']==c['tail_start_sha256'] and t['status']=='complete' and type(t['acknowledged_cells']) is int and t['acknowledged_cells']==count and type(t['records_bytes']) is int and t['records_bytes']==count*80 and isinstance(t['reason'],str) and len(t['reason'].encode())<=1024,'complete original tail denominator')
    bank.identity(t['head']);bank.identity(t['records_sha256'])
    return Binding(bank.encode(c),tuple((n,metadata[n]) for n in sorted(NAMES)),tuple(sorted(pins.items())),previous_seal,chunk_records,max_file_bytes)


def recheck(binding):
    require(type(binding) is Binding,'typed closed-tail binding required')
    return bind(bank.decode(binding.contract_raw),dict(binding.metadata),dict(binding.pins),previous_seal=binding.previous_seal,chunk_records=binding.chunk_records,max_file_bytes=binding.max_file_bytes)

@dataclass(frozen=True)
class Chunk:
    binding_sha256: str
    index: int
    first_record: int
    raw: bytes
    def descriptor(self):
        bank.identity(self.binding_sha256)
        require(type(self.index) is int and self.index>=0 and type(self.first_record) is int and self.first_record>=0 and type(self.raw) is bytes and 0<len(self.raw)<=CHUNK_BYTES and len(self.raw)%80==0,'typed aligned chunk bounds')
        return dict(schema_version=1,kind='original-score-tail-records',binding_sha256=self.binding_sha256,index=self.index,first_record=self.first_record,records=len(self.raw)//80,bytes=len(self.raw),sha256=bank.digest(self.raw),record_format='<Qd32s32s',provisional=True)


def verify(binding,read,batch_read,*,lease,max_seconds,emit=None):
    """Single bounded pass. emit receives provisional chunks, never authority.

    The deadline is sampled around all callbacks; it cannot preempt a blocked
    reader/lease/sink. Callers must supply the original finite outer supervisor.
    """
    b=recheck(binding);c=bank.decode(b.contract_raw);m=dict(b.metadata)
    require(callable(read) and callable(batch_read) and callable(lease) and (emit is None or callable(emit)),'bounded readers/live lease required')
    require(type(max_seconds) in (int,float) and math.isfinite(max_seconds) and 0<max_seconds<=1800,'finite sampled deadline')
    began=time.monotonic();record=bytearray();chunk=bytearray();scores=hashlib.sha256();frames=hashlib.sha256();index=offset=0
    total_bytes=bank.decode(m['tail_terminal'])['records_bytes']
    def check():
        require(time.monotonic()-began<=max_seconds,'tail sampled deadline');lease();require(time.monotonic()-began<=max_seconds,'tail sampled deadline')
    def bounded(reader,n):
        check();raw=reader(n);check();require(type(raw) is bytes and len(raw)<=n,'bounded stream reader required');return raw
    def flush():
        nonlocal index,offset
        if chunk:
            item=Chunk(b.identity,index,offset,bytes(chunk));item.descriptor()
            if emit is not None:check();emit(item);check()
            offset+=len(chunk)//80;index+=1;chunk.clear()
    def tapped(n):
        raw=bounded(read,n)
        # Semantic verifier requests exactly one record at a time, then EOF.
        if offset*80+len(chunk)+len(record)<total_bytes:
            record.extend(raw)
            if len(record)==80:
                score=semantic._read_exact(lambda n:bounded(batch_read,n),8)
                require(bytes(record[8:16])==score,'original float64 batch bits differ')
                scores.update(score);frames.update(record[:48]);chunk.extend(record);record.clear()
                if len(chunk)==b.chunk_records*80:flush()
        return raw
    check()
    result=semantic.verify_complete(tapped,start_raw=m['tail_start'],terminal_raw=m['tail_terminal'],start_sha256=c['tail_start_sha256'],terminal_sha256=c['tail_terminal_sha256'],scope=c['scope'],owner=c['owner'])
    require(not record and bounded(batch_read,1)==b'' and scores.hexdigest()==c['batch_payload_sha256'],'batch EOF/hash differs')
    flush();check()
    return dict(kind='original-closed-tail-content-verified',binding_sha256=b.identity,tail=result,chunks=index,records=offset,batch_payload_sha256=scores.hexdigest(),score_frames_sha256=frames.hexdigest(),authority=None,whole_roster_verified=False,remote_verified=False,deletion_authority=False)


def verify_recovery(binding,chunks,batch_read,*,lease,max_seconds):
    """Reassemble typed recovered chunks lazily, then repeat original semantics."""
    b=recheck(binding);iterator=iter(chunks);pending=b'';number=offset=0;ended=False
    def read(n):
        nonlocal pending,number,offset,ended
        if not pending and not ended:
            try:item=next(iterator)
            except StopIteration:ended=True
            else:
                require(type(item) is Chunk,'typed recovery chunk required');_,_,d=_descriptor(b,item.descriptor())
                require(d['binding_sha256']==b.identity and d['index']==number and d['first_record']==offset,'recovery chunk identity/order differs')
                pending=item.raw;number+=1;offset+=d['records']
        raw=pending[:n];pending=pending[n:];return raw
    return verify(b,read,batch_read,lease=lease,max_seconds=max_seconds)


@contextmanager
def original_readers(binding,stage_root,*,lease):
    """Read original tail/batch through pinned no-follow descriptors, no arrays.

    Metadata must already be genuinely authenticated by the caller. Endpoint
    file/parent checks detect sampled drift, not unobserved adversarial writes.
    """
    b=recheck(binding);c=bank.decode(b.contract_raw);root=Path(stage_root)
    require(callable(lease) and root.name==c['stage'] and str(root/'stream/batches')==c['batch_directory'],'original stage path/lease differs')
    tail=root/'stream/tails'/f"tail-{c['index']:012d}";batch=root/'stream/batches';owned=[];pins=[]
    paths={'intent':root/'intent.json','stage':root/'stage-complete.json','stream_start':root/'stream/start.json','stream_complete':root/'stream/complete.json','seal':root/'stream'/f"seal-{c['index']:012d}.json",'batch_start':batch/'start.json','batch_header':batch/f"chunk-{c['index']:012d}.json",'tail_start':tail/'start.json','tail_terminal':tail/'terminal.json'}
    def open_file(path,size):
        parent,pfd=bank.open_root(path.parent);owned.append(pfd)
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=pfd);owned.append(fd);s=os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==size,'original file type/link/extent differs')
        pins.append((parent,pfd,path.name,fd,bank.signature(s)));return fd
    def endpoints():
        for parent,pfd,name,fd,sig in pins:
            bank.root_check(parent,pfd);require(bank.signature(os.fstat(fd))==sig==bank.signature(os.stat(name,dir_fd=pfd,follow_symlinks=False)),'original member changed')
    try:
        lease()
        for name,raw in b.metadata:
            fd=open_file(paths[name],len(raw));require(os.read(fd,len(raw)+1)==raw,'original metadata body differs')
        total=bank.decode(dict(b.metadata)['tail_terminal'])['records_bytes'];tfd=open_file(tail/'records.bin',total);bfd=open_file(batch/f"chunk-{c['index']:012d}.bin",total//10)
        endpoints();lease();endpoints()
        yield (lambda n:os.read(tfd,n)),(lambda n:os.read(bfd,n))
        lease();endpoints()
        for name,raw in b.metadata:
            # Metadata FD positions are irrelevant; pread does not reopen paths.
            fd=next(fd for parent,pfd,filename,fd,sig in pins if parent/filename==paths[name]);require(os.pread(fd,len(raw)+1,0)==raw,'metadata changed during read callback')
        endpoints()
    finally:bank.cleanup(tuple(lambda fd=fd:os.close(fd) for fd in reversed(owned)),sys.exception())


def _descriptor(binding,value):
    b=recheck(binding);c=bank.decode(b.contract_raw)
    require(type(value) is dict and set(value)=={'schema_version','kind','binding_sha256','index','first_record','records','bytes','sha256','record_format','provisional'},'typed descriptor fields')
    require(all(type(value[k]) is int for k in ('schema_version','index','first_record','records','bytes')),'typed descriptor integers')
    count=bank.decode(dict(b.metadata)['tail_start'])['cells'];index=value['index'];begin=index*b.chunk_records
    require(index>=0 and begin<count and value==dict(schema_version=1,kind='original-score-tail-records',binding_sha256=b.identity,index=index,first_record=begin,records=min(b.chunk_records,count-begin),bytes=min(b.chunk_records,count-begin)*80,sha256=value['sha256'],record_format='<Qd32s32s',provisional=True) and value['provisional'] is True,'typed descriptor binding/denominator')
    bank.identity(value['sha256']);return b,c,dict(value)


def _transport(b,c,transport):
    require(transport.identity==c['transport_identity'],'selected transport identity differs')
    import resource
    native=resource.getrlimit(resource.RLIMIT_FSIZE)
    require(all(type(n) is int and b.max_file_bytes<=n<2**63 for n in native),'finite native file limit must cover selected chunk/metadata cap')
    from tradingagents.research.onchain_replication.archive_transport import Transport,Budget
    require(type(transport) is Transport and type(transport.budget) is Budget,'original finite archive transport and budget required')
    require(type(transport.budget.remaining) is int and transport.budget.remaining>=0 and type(transport.max_seconds) in (int,float) and math.isfinite(transport.max_seconds) and transport.max_seconds>0 and type(transport.rate_bytes) is int and transport.rate_bytes>0 and callable(transport.live),'finite transport budget/deadline/lease differs')


def preserve_chunk(binding,chunk,*,source,attempt,remote,transport,lease,free_floor_bytes):
    """Reuse bounded archive preserve; its receipt is never tail/Owner authority.

    Caller writes exact chunk.raw to a fresh retained source. Existing transport
    owns finite cumulative quota/deadline/real lease and no-retry semantics.
    """
    require(type(chunk) is Chunk,'typed chunk required');b,c,d=_descriptor(binding,chunk.descriptor())
    _transport(b,c,transport)
    require(remote==c['remote']+f"-part-{d['index']:06d}",'typed remote chunk mapping differs')
    from tradingagents.research.onchain_replication import archive_chunks
    return archive_chunks.preserve(source=source,attempt=attempt,expected_sha256=d['sha256'],expected_bytes=d['bytes'],scope=bank.digest(bank.encode(d)),remote=remote,transport=transport,lease=lease,free_floor_bytes=free_floor_bytes)


def retrieve_chunk(binding,expected,*,receipt_root,receipt_sha256,attempt,transport,lease,free_floor_bytes):
    """Fresh archive recovery from metadata; no original chunk payload required."""
    b,c,d=_descriptor(binding,expected)
    _transport(b,c,transport)
    from tradingagents.research.onchain_replication import archive_chunks
    path,rfd=bank.open_root(receipt_root)
    try:
        raw=bank.read_member(rfd,'complete.json',bank.META);require(bank.digest(raw)==receipt_sha256,'archive original receipt pin differs');r=bank.decode(raw)
        require(r['remote']==c['remote']+f"-part-{d['index']:06d}" and r['scope']==bank.digest(bank.encode(d)) and r['bytes']==d['bytes'] and r['source_sha256']==d['sha256'] and r['transport_identity']==c['transport_identity'],'byte receipt/typed chunk differs')
    finally:bank.cleanup((lambda:os.close(rfd),),sys.exception())
    recovered=archive_chunks.retrieve(receipt_root,receipt_sha256=receipt_sha256,attempt=attempt,transport=transport,lease=lease,free_floor_bytes=free_floor_bytes)
    parent,fd=bank.open_root(recovered.parent)
    try:raw=bank.read_member(fd,recovered.name,b.max_file_bytes);bank.root_check(parent,fd)
    finally:bank.cleanup((lambda:os.close(fd),),sys.exception())
    require(bank.digest(raw)==d['sha256'] and len(raw)==d['bytes'],'recovered typed chunk differs')
    return Chunk(d['binding_sha256'],d['index'],d['first_record'],raw)


def activate(*args,**kwargs):
    raise ValueError('Genuine closed-Stage/Owner/Target roster, held lease and typed transport ledger activation remain caller-bound; content metadata is not authority')


@dataclass(frozen=True)
class ArchivedBinding:
    stage_sha256: str
    contract_sha256: str
    stream_sha256: str
    recovery_sha256: str
    matching_scores_sha256: str
    cells: int


def bind_archived(stage_root,*,expected_stage_sha256,contract):
    """Actual archived marker, never a synthesized legacy stage receipt.

    The externally trusted original marker anchors prior full byte/semantic
    recovery. This content-only binding grants no live capability and asserts
    no present remote availability. Any byte use requires fresh typed recovery.
    """
    from . import archive_owner_seal, typed_score_store
    result=archive_owner_seal.check_content(Path(stage_root),expected_sha256=expected_stage_sha256,contract=contract)
    require(result['kind']=='mcm' and 'typed_score_recovery_sha256' in result,'selected genuine archived score result required')
    proof=typed_score_store.check(Path(stage_root)/'stream',terminal=contract['stream_terminal_sha256'],owner=contract['owner'],scope=contract['scope'],pairs=contract['pairs'],chunk_cells=contract['policy']['score_chunk_cells'])
    complete,_=typed_score_store.read(Path(stage_root)/'stream','typed-complete.json',result['typed_score_recovery_sha256'])
    require(bank.digest(complete)==result['typed_score_recovery_sha256'] and proof['matching_scores_sha256']==result['matching_scores_sha256'] and proof['cells']==result['completed_pairs'],'archived original scientific recovery join')
    return ArchivedBinding(expected_stage_sha256,bank.digest(bank.encode(contract)),contract['stream_terminal_sha256'],result['typed_score_recovery_sha256'],result['matching_scores_sha256'],result['completed_pairs'])

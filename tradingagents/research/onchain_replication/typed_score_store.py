"""Selected original f64 score evidence, recovered in bounded typed parts.

No numerical method is implemented here. The genuine stream performs original
local seal validation first. Successful parts retain remote originals, original
metadata and durable prior full-recovery proofs. Future byte use retrieves anew.
"""
import hashlib
import json
import os
from pathlib import Path
from . import typed_payload_operations as operations, typed_payload_policy as policy
from . import score_tail_semantics as semantics

require=policy.require

def read(root,name,expected=None):
    raw=operations._read(Path(root)/name,8192)
    if expected is not None:require(policy.sha(raw)==expected,'typed original metadata hash differs')
    return raw,json.loads(raw)

def write(root,name,value):
    operations._write(Path(root)/name,value);return policy.sha(policy.raw(value))

def inventory(root,names):
    from .archive_chunks import _inventory,io
    path,fd=io._open(root)
    try:_inventory(fd,set(names));io._root(path,fd)
    finally:io._release(lambda:os.close(fd))

class _Parts:
    def __init__(self,op,receipts,root):self.op=op;self.receipts=iter(receipts);self.root=root;self.raw=b'';self.index=0;self.pos=0
    def read(self,n):
        require(type(n) is int and 0<n<=80,'typed semantic read bound')
        if self.pos==len(self.raw):
            receipt=next(self.receipts,None)
            if receipt is None:return b''
            self.raw=self.op.recover(receipt,attempt=self.root/f'read-{self.index:012d}');self.index+=1;self.pos=0
        result=self.raw[self.pos:self.pos+n];self.pos+=len(result);return result

def selected(stream):
    target=stream._imported
    if target is None:return None
    record=operations.selected(target.owner)
    if record is None:return None
    owner=target.owner;stage=owner.active
    require(stage is not None and stage.kind=='mcm' and stage.name=='mcm-'+stream.parent,'typed live original MCM stage')
    graph=record['policy']['graphs'].get(stream.parent)
    require(graph is not None and graph['rows']==stream.n and graph['chunk_cells']==stream.batches.chunk_cells and stream.k==32,'typed actual original denominator differs')
    return Store(stream,owner,stage,record)

class Store:
    def __init__(self,stream,owner,stage,record):
        self.stream=stream;self.owner=owner;self.stage=stage;self.record=record
        self.frames=hashlib.sha256();self.chain=hashlib.sha256();self.count=0

    def seal(self,index):
        s=self.stream;require(index==self.count,'typed seal order')
        tr=s.root/'tails'/f'tail-{index:012d}'
        sr,start=read(tr,'start.json');er,end=read(tr,'terminal.json')
        lr,link=read(s.root,f'seal-{index:012d}.json');hr,header=read(s.batches.root,f'chunk-{index:012d}.json',link['batch_header_sha256'])
        require(policy.sha(er)==link['tail_terminal_sha256'],'typed terminal/seal join')
        batch=operations._read(s.batches.root/f'chunk-{index:012d}.bin',start['cells']*8)
        require(policy.sha(batch)==header['payload_sha256'] and len(batch)==start['cells']*8,'typed f64 original hash/extent')
        binding={'schema_version':1,'owner':s.owner,'scope':s.scope,'stream_start_sha256':s.start_sha,'seal_sha256':policy.sha(lr),'tail_start_sha256':policy.sha(sr),'tail_terminal_sha256':policy.sha(er),'batch_header_sha256':policy.sha(hr),'index':index}
        maxpart=self.record['policy']['graphs'][s.parent]['kinds']['score-tail-f64']['chunk_bytes']
        size=end['records_bytes'];parts=(size+maxpart-1)//maxpart
        scratch=tr/'typed';scratch.mkdir();receipts=[]
        from .archive_chunks import io
        parent,pfd=io._open(tr)
        try:os.fsync(pfd);io._root(parent,pfd)
        finally:io._release(lambda:os.close(pfd))
        with operations.operation(self.owner,self.stage,kind='score-tail-f64',binding=binding,payload_bytes=size,chunk_count=parts) as op:
            from .archive_chunks import io
            root,fd=io._open(tr)
            try:
                source=os.open('records.bin',os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
                try:
                    pin=io._signature(os.fstat(source));h=hashlib.sha256();offset=0
                    for part in range(parts):
                        n=min(maxpart,size-offset);raw=os.pread(source,n,offset);require(len(raw)==n,'typed source truncation');h.update(raw)
                        path=scratch/f'part-{part:012d}.bin'
                        sf=io._open(scratch)
                        try:io._write(sf[1],path.name,raw)
                        finally:io._release(lambda:os.close(sf[1]))
                        receipt=op.preserve(path,expected_sha256=policy.sha(raw),expected_bytes=n,index=part,attempt=scratch/f'put-{part:012d}');receipts.append(receipt)
                        op.retire_source(path,expected_sha256=policy.sha(raw),expected_bytes=n);offset+=n
                    require(h.hexdigest()==end['records_sha256'] and io._signature(os.fstat(source))==pin and io._signature(os.stat('records.bin',dir_fd=fd,follow_symlinks=False))==pin,'typed original records changed')
                finally:io._release(lambda:os.close(source))
            finally:io._release(lambda:os.close(fd))
            reader=_Parts(op,receipts,scratch);position=0;frame=bytearray();frames=hashlib.sha256()
            def observed(n):
                nonlocal position
                raw=reader.read(n);frame.extend(raw)
                if len(frame)==80:
                    require(bytes(frame[8:16])==batch[position*8:(position+1)*8],'typed recovered original f64 bits differ')
                    frames.update(frame[:48]);self.frames.update(frame[:48]);position+=1;frame.clear()
                require(len(frame)<80,'typed frame fragmentation bound')
                return raw
            semantic=semantics.verify_complete(observed,start_raw=sr,terminal_raw=er,start_sha256=policy.sha(sr),terminal_sha256=policy.sha(er),scope=s.scope,owner=s.owner)
            require(position==start['cells'] and not frame,'typed recovered full frame population')
        tail_history=op.history()
        # Batch payload is unchanged original f64; preserve it independently.
        batchbinding=dict(binding,kind='score-batch-f64')
        with operations.operation(self.owner,self.stage,kind='score-batch-f64',binding=batchbinding,payload_bytes=len(batch),chunk_count=1) as batchop:
            receipt=batchop.preserve(s.batches.root/f'chunk-{index:012d}.bin',expected_sha256=header['payload_sha256'],expected_bytes=len(batch),index=0,attempt=scratch/'batch-put')
            batchop.retire_source(s.batches.root/f'chunk-{index:012d}.bin',expected_sha256=header['payload_sha256'],expected_bytes=len(batch))
        proof={'schema_version':1,'format':'typed-score-seal-v1','binding':binding,'semantic':semantic,'frames_sha256':frames.hexdigest(),'tail_history':tail_history,'batch_binding':batchbinding,'batch_history':batchop.history(),'assumption':policy.ASSUMPTION}
        ref=write(tr,'typed.json',proof)
        # Prior semantic full recovery and both durable ledger completions exist.
        self.owner.lease();operations.dispose(tr/'records.bin',size,end['records_sha256'])
        self.chain.update(bytes.fromhex(ref));self.count+=1

    def finish(self,terminal):
        s=self.stream
        require(self.count==s.batches.chunks and s.cells==s.n*32,'typed full stream population')
        summary={'schema_version':1,'format':'typed-score-history-v1','owner':s.owner,'scope':s.scope,'stream_start_sha256':s.start_sha,'batch_terminal_sha256':terminal,'cells':s.cells,'chunks':self.count,'seal_head':s.head,'typed_seals_sha256':self.chain.hexdigest(),'matching_scores_sha256':self.frames.hexdigest(),'policy_input':self.record['input'],'policy_sha256':self.record['input_sha256'],'assumption':policy.ASSUMPTION}
        return write(s.root,'typed-complete.json',summary)

def check(root,*,terminal,owner,scope,pairs,chunk_cells):
    """Anchored historical recovery only; no current remote availability claim."""
    root=Path(root);cr,complete=read(root,'complete.json',terminal)
    require(set(complete)=={'schema_version','start_sha256','head','cells','chunks','batch_terminal_sha256','typed_proof_sha256'} and complete['schema_version']==2,'selected typed completion schema')
    _,start=read(root,'start.json',complete['start_sha256'])
    _,proof=read(root,'typed-complete.json',complete['typed_proof_sha256'])
    require(start['schema_version']==2 and start['kind']=='mcm-score-stream' and start['owner']==owner and start['scope']['workflow']==scope['workflow'] and start['motifs']==32 and start['rows']*32==pairs and start['chunk_cells']==chunk_cells,'typed original stream scope/denominator')
    require(proof=={'schema_version':1,'format':'typed-score-history-v1','owner':owner,'scope':start['scope'],'stream_start_sha256':complete['start_sha256'],'batch_terminal_sha256':complete['batch_terminal_sha256'],'cells':pairs,'chunks':complete['chunks'],'seal_head':complete['head'],'typed_seals_sha256':proof['typed_seals_sha256'],'matching_scores_sha256':proof['matching_scores_sha256'],'policy_input':start['typed_payload_input'],'policy_sha256':start['typed_payload_sha256'],'assumption':policy.ASSUMPTION},'typed recovery summary binding')
    count=(pairs+chunk_cells-1)//chunk_cells;require(complete['cells']==pairs and complete['chunks']==count,'typed complete denominator')
    _,bs=read(root/'batches','start.json',start['batch_start_sha256']);_,bt=read(root/'batches','terminal.json',complete['batch_terminal_sha256'])
    require(bs=={'schema_version':1,'scope':start['scope'],'owner':owner,'rows':start['rows'],'motifs':32,'chunk_cells':chunk_cells,'dtype':'<f8','order':'row-major'} and bt['status']=='complete' and bt['cells']==pairs and bt['chunks']==count and not bt['pending'],'typed batch completion')
    previous=complete['start_sha256'];batchprevious=start['batch_start_sha256'];chain=hashlib.sha256()
    for index in range(count):
        lr,link=read(root,f'seal-{index:012d}.json');offset=index*chunk_cells;cells=min(chunk_cells,pairs-offset)
        require(link=={'schema_version':1,'start_sha256':complete['start_sha256'],'previous':previous,'index':index,'start_cell':offset,'cells':cells,'tail_terminal_sha256':link['tail_terminal_sha256'],'batch_header_sha256':link['batch_header_sha256']},'typed original seal predecessor')
        tr=root/'tails'/f'tail-{index:012d}';sr,ts=read(tr,'start.json');er,te=read(tr,'terminal.json',link['tail_terminal_sha256']);pr,p=read(tr,'typed.json')
        hr,bh=read(root/'batches',f'chunk-{index:012d}.json',link['batch_header_sha256'])
        binding={'schema_version':1,'owner':owner,'scope':start['scope'],'stream_start_sha256':complete['start_sha256'],'seal_sha256':policy.sha(lr),'tail_start_sha256':policy.sha(sr),'tail_terminal_sha256':policy.sha(er),'batch_header_sha256':policy.sha(hr),'index':index}
        require(p['binding']==binding and p['batch_binding']==dict(binding,kind='score-batch-f64') and p['assumption']==policy.ASSUMPTION,'typed historical seal join')
        tailproof=operations.check_history(p['tail_history'],binding=binding,kind='score-tail-f64');batchproof=operations.check_history(p['batch_history'],binding=p['batch_binding'],kind='score-batch-f64')
        partcount=tailproof['parts']
        inventory(tr/'typed',{'batch-put'}|{f'put-{i:012d}' for i in range(partcount)}|{f'read-{i:012d}' for i in range(partcount)})
        for part in operations.iter_history_parts(p['tail_history'],binding=binding,kind='score-tail-f64'):
            i=part['index'];check_attempt(tr/'typed'/f'put-{i:012d}',part['receipt'],reading=False);check_attempt(tr/'typed'/f'read-{i:012d}',part['receipt'],reading=True)
        batchparts=list(operations.iter_history_parts(p['batch_history'],binding=p['batch_binding'],kind='score-batch-f64'))
        require(len(batchparts)==1,'typed batch part denominator')
        check_attempt(tr/'typed/batch-put',batchparts[0]['receipt'],reading=False)
        require(tailproof['preserved_bytes']==cells*80 and batchproof['preserved_bytes']==cells*8 and p['semantic']['records_sha256']==te['records_sha256'] and p['semantic']['terminal_sha256']==policy.sha(er) and p['semantic']['start_sha256']==policy.sha(sr) and p['semantic']['cells_verified']==cells and p['semantic']['start_cell']==offset,'typed original recovered semantic count')
        require(bh=={'schema_version':1,'start_sha256':start['batch_start_sha256'],'previous':batchprevious,'index':index,'start_cell':offset,'cells':cells,'payload_sha256':bh['payload_sha256']} and batchparts[0]['receipt']['source_sha256']==bh['payload_sha256'],'typed original f64 header join')
        require(ts['scope']==start['scope'] and ts['owner']==owner and ts['start_cell']==offset and ts['cells']==cells and ts['destination']==policy.sha(policy.raw({'directory':str(root/'batches'),'start_sha256':start['batch_start_sha256'],'index':index,'start_cell':offset,'cells':cells})),'typed original tail destination')
        inventory(tr,{'start.json','terminal.json','typed.json','typed'});chain.update(bytes.fromhex(policy.sha(pr)));previous=policy.sha(lr);batchprevious=policy.sha(hr)
    require(previous==complete['head'] and batchprevious==bt['head'] and chain.hexdigest()==proof['typed_seals_sha256'],'typed historical full roster/head')
    inventory(root,{'start.json','complete.json','typed-complete.json','batches','tails'}|{f'seal-{i:012d}.json' for i in range(count)})
    inventory(root/'tails',{f'tail-{i:012d}' for i in range(count)})
    inventory(root/'batches',{'start.json','terminal.json'}|{f'chunk-{i:012d}.json' for i in range(count)})
    return proof

def batch_bytes(owner,stage,index,attempt):
    """Fresh original f64 payload use under genuine current held authority."""
    from . import compact_owner
    compact_owner._stage_content(stage)
    from .typed_tail_binding import bind_archived
    from .provenance import thaw
    bind_archived(stage.root,expected_stage_sha256=stage.reference,contract=thaw(stage.contract))
    tr=stage.root/'stream/tails'/f'tail-{index:012d}';raw,p=read(tr,'typed.json')
    compact_owner._stage_content(stage)
    require(read(tr,'typed.json')[0]==raw,'typed batch original marker changed')
    history=operations.check_history(p['batch_history'],binding=p['batch_binding'],kind='score-batch-f64')
    parts=list(operations.iter_history_parts(p['batch_history'],binding=p['batch_binding'],kind='score-batch-f64'))
    require(len(parts)==1,'typed original bounded batch part')
    with operations.operation(owner,stage,kind='score-batch-f64',binding={'restore_of':p['batch_history'],'index':index},payload_bytes=0,chunk_count=0) as op:
        result=op.recover(parts[0]['receipt'],attempt=attempt)
    return result


def check_attempt(root,receipt,*,reading):
    ref=policy.sha(policy.raw(receipt))
    if reading:
        intent={'schema_version':1,'format':'archive-consume-v1','receipt_sha256':ref,'receipt':receipt}
        verified={'schema_version':1,'intent_sha256':policy.sha(policy.raw(intent)),'bytes':receipt['bytes'],'payload_sha256':receipt['source_sha256']}
        bodies={'intent.json':intent,'verified.json':verified,'complete.json':{'schema_version':1,'verified_sha256':policy.sha(policy.raw(verified)),'owned_cache_disposed':True}}
    else:bodies={'intent.json':receipt,'complete.json':receipt,'disposed.json':{'schema_version':1,'receipt_sha256':ref,'owned_transfer_payloads_disposed':True}}
    inventory(root,set(bodies))
    for name,value in bodies.items():require(read(root,name)[0]==policy.raw(value),'typed actual transfer/disposal proof changed')


class _BatchReader:
    def __init__(self,op,stage,proof):
        self.op=op;self.stage=stage;self.proof=proof;self.next=0;self.chain=hashlib.sha256()
    def read(self,index,attempt):
        self.op.lease();require(index==self.next and type(index) is int and index<self.proof['chunks'],'typed original batch order')
        raw,p=read(self.stage.root/'stream/tails'/f'tail-{index:012d}','typed.json')
        require(p['binding']['index']==index and p['binding']['owner']==self.op.owner.identity and p['binding']['scope']==self.proof['scope'] and p['binding']['stream_start_sha256']==self.proof['stream_start_sha256'],'typed batch scope differs')
        parts=list(operations.iter_history_parts(p['batch_history'],binding=p['batch_binding'],kind='score-batch-f64'));require(len(parts)==1,'typed f64 batch part')
        result=self.op.recover(parts[0]['receipt'],attempt=attempt)
        self.chain.update(bytes.fromhex(policy.sha(raw)));self.next+=1
        return result


from contextlib import contextmanager
@contextmanager
def batch_reader(owner,stage):
    """One actual held reader, full scientific evidence at both boundaries.

    Every ordered chunk is freshly recovered. The original anchored marker chain
    is exhausted before success; earlier returned bytes remain provisional until
    context exit. No random access, shortcut, or partial completion is accepted.
    """
    from . import compact_owner
    from .provenance import thaw
    from .typed_tail_binding import bind_archived
    compact_owner._stage_content(stage);contract=thaw(stage.contract)
    anchored=bind_archived(stage.root,expected_stage_sha256=stage.reference,contract=contract)
    _,proof=read(stage.root/'stream','typed-complete.json',anchored.recovery_sha256)
    with operations.operation(owner,stage,kind='score-batch-f64',binding={'read_stream':anchored.stream_sha256,'recovery_sha256':anchored.recovery_sha256},payload_bytes=0,chunk_count=0) as op:
        reader=_BatchReader(op,stage,proof);yield reader
        require(reader.next==proof['chunks'] and reader.chain.hexdigest()==proof['typed_seals_sha256'],'typed full original batch roster not exhausted')
    compact_owner._stage_content(stage)
    require(thaw(stage.contract)==contract and bind_archived(stage.root,expected_stage_sha256=stage.reference,contract=contract)==anchored,'typed scientific boundary changed')

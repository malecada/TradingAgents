"""Selected typed payload operations under an actual held archive Owner.

Owned writer children are sequential; the original parent remains active. Closed
MCM output uses a separate durable operation while no parent is active. All
reservations are monotone and use the SAME dispatch transport/physical budget.
Historical receipts assert a previous full read, never present availability.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
from threading import get_ident
from . import typed_payload_policy as policy
from .provenance import thaw

require=policy.require

def selected(owner):
    from . import archive_dispatch as dispatch, archive_owner_operations as ops
    ledger=getattr(owner,'_archive_operations',None)
    if ledger is None:return None
    require(type(ledger) is ops.Ledger and ledger.owner is owner,'typed actual ledger')
    view=ledger.selection._transport
    if type(view) is not dispatch.View:return None
    record=view._context._record.get('typed_payloads')
    if record is None:return None
    require(owner.bound._run is view._context._run,'typed actual run')
    return json.loads(policy.raw(record))

def _read(path, limit=131072):
    from . import archive_chunks as a
    root,fd=a.io._open(Path(path).parent)
    try:
        raw=a.io._read(fd,Path(path).name,limit);a.io._root(root,fd);return raw
    finally:a.io._release(lambda:os.close(fd))

def _write(path,value):
    from . import archive_chunks as a
    root,fd=a.io._open(Path(path).parent)
    try:a.io._write(fd,Path(path).name,policy.raw(value));a.io._root(root,fd)
    finally:a.io._release(lambda:os.close(fd))

def dispose(path, size, sha):
    """Only caller-owned verified payload; sampled no-callback final join."""
    from . import archive_chunks as a
    root,fd=a.io._open(Path(path).parent)
    try:
        before=os.stat(Path(path).name,dir_fd=fd,follow_symlinks=False)
        a._read(Path(path),size,sha)
        require(a.io._signature(before)==a.io._signature(os.stat(Path(path).name,dir_fd=fd,follow_symlinks=False)),'typed disposal source changed')
        a.io._root(root,fd);os.unlink(Path(path).name,dir_fd=fd);os.fsync(fd)
    finally:a.io._release(lambda:os.close(fd))

class _Operation:
    def __init__(self,owner,stage,kind,binding,payload_bytes,chunk_count,*,target=None):
        from . import archive_dispatch as d, archive_owner_operations as a
        self._target=target;self._target_pin=target
        if target is not None:
            from .imported_mcm_identity import Target
            require(type(target) is Target and target.owner is owner and target.execution._owner is owner,'genuine same-owner target required')
            target.lease()
        self.owner=owner;self.stage=stage;self.ledger=getattr(owner,'_archive_operations',None)
        require(type(owner) is a.owners.Owner and type(stage) is a.owners.Stage and type(self.ledger) is a.Ledger,'actual typed Owner/Stage/ledger required')
        self.held=getattr(owner,'_held_transition',None)
        require(type(self.held) is a.owners._HeldTransition,'actual owned transition required');self.held.check(owner)
        self.view=self.ledger.selection._transport;require(type(self.view) is d.View,'actual dispatch transport required')
        self.context=self.view._context;self.parent=self.context._cap
        record=selected(owner);require(record is not None,'typed payload not selected')
        self.policy=policy.validate(record['policy']);self.graph=stage.name[4:]
        require(stage.kind=='mcm' and stage.name=='mcm-'+self.graph and owner.stages.get(stage.name) is stage and stage.name in owner.required,'actual required MCM stage')
        require(self.graph in self.policy['graphs'] and kind in policy.KINDS,'registered typed graph/kind')
        self.budget=self.policy['graphs'][self.graph]['kinds'][kind]
        require(stage.pairs==32*self.policy['graphs'][self.graph]['rows'],'typed full original row population')
        require(type(binding) is dict and 0<len(policy.raw(binding))<=8192,'bounded typed source binding')
        require(type(payload_bytes) is int and 0<=payload_bytes<=self.budget['max_preserved_bytes'] and type(chunk_count) is int and 0<=chunk_count<=self.budget['max_chunks'],'typed operation finite declaration')
        batched_open=(self.parent is None and self.policy['schema_version']==2 and kind==policy.BATCHED_KIND and not stage.closed)
        if self.parent is not None:
            require(self.parent['ledger'] is self.ledger and self.parent['held'] is self.held and self.parent['view'] is self.view and self.parent['thread']==get_ident(),'typed parent capability differs')
            require((self.ledger._active is not None and self.ledger._active._stage is stage) or (type(self.parent.get('typed_operation')) is _Operation and self.parent['typed_operation'].stage is stage),'typed actual parent operation')
            self.parent_operation=self.ledger._active
        else:
            require(self.ledger._active is None and ((batched_open and self.policy['batched_parent']=='actual-active-mcm-stage-v1' and owner.active is stage) or (stage.closed and owner.active is None)),'typed standalone requires selected actual active batched stage or closed idle stage')
            self.parent_operation=None
        self.context._outer();self.ledger._current(full=True);self.ledger._stage(stage)
        registry=getattr(self.ledger,'_typed_payload_registry',None)
        if registry is None:
            registry={};self.ledger._typed_payload_registry=registry
        require(getattr(self.ledger,'_typed_payload_registry_pin',policy.sha(policy.raw({})))==policy.sha(policy.raw(registry)),'typed cumulative registry changed/refunded')
        self.registry=registry;key=self.graph+':'+kind
        previous=registry.get(key,dict(operations=0,preserved=0,recovered=0,chunks=0))
        self.counter=dict(previous);self.counter['operations']+=1
        require(self.counter['operations']<=self.budget['max_operations'],'typed operation allowance exhausted')
        self.counter['preserved']+=payload_bytes;self.counter['chunks']+=chunk_count
        require(self.counter['preserved']<=self.budget['max_preserved_bytes'] and self.counter['chunks']<=self.budget['max_chunks'],'typed reservation exhausted')
        self.key=key;registry[key]=self.counter;self.ledger._typed_payload_registry_pin=policy.sha(policy.raw(registry))
        self.record={'schema_version':1,'format':'typed-payload-operation-v1','owner':owner.identity,'stage':stage.name,
            'stage_intent_sha256':stage.intent_sha256,'stage_reference':stage.reference if stage.closed else None,
            'kind':kind,'binding':binding,'input':record['input'],'input_sha256':record['input_sha256'],
            'ledger_identity':self.ledger._identity,'parent_claim_sha256':None if self.parent is None else self.parent['claim_sha256'],
            'ordinal':self.counter['operations'],'reserved_payload_bytes':payload_bytes,'reserved_chunks':chunk_count,'reserved':dict(self.counter)}
        if batched_open:self.record['batched_parent']='actual-active-mcm-stage-v1'
        self.sha=policy.sha(policy.raw(self.record));self.closed=False;self.proofs=[];self.preserved=0;self.recovered=0
        self.claim_name='typed-'+self.sha+'.json';self._publish(self.claim_name,self.record)
        # Context also persists the reservation before any command. Parent event
        # reservation stays charged; these are additional selected payload bytes.
        self.context._spent['logical_bytes']+=2*payload_bytes
        # canonical_bytes uses no newline; retain the actual source encoder.
        from .provenance import canonical_bytes
        self.context._spent_pin=canonical_bytes(self.context._spent)
        require(self.context._spent['logical_bytes']<=self.context._record['capacity']['logical_bytes'],'typed shared logical capacity')
        self.context._publish(self.claim_name,{'claim':self.record,'spent':self.context._spent})
        self.remote=self.ledger.selection.writer_policy(stage.name)['remote_prefix']+'-p'+self.sha[:16]
        require(len(self.remote)+13<=127,'typed remote namespace bound')
        self.cap={'ledger':self.ledger,'held':self.held,'lease':self.lease,'view':self.view,'thread':get_ident(),'claim_sha256':self.sha,'remote_prefix':self.remote,'typed_operation':self}
        self.context._cap=self.cap
        self.pin=policy.raw(self.record);self._counter_pin=policy.raw(self.counter)
        self._authority=(self.owner,self.stage,self.ledger,self.held,self.view,self.context,self.parent,self.parent_operation,self.registry,self.counter,self.budget,self.policy)
        self._policy_pin=policy.raw(self.policy)

    def _publish(self,name,value):
        raw=policy.raw(value)
        require(len(raw)<=8192,'typed ledger metadata bound')
        spent=getattr(self.ledger,'_typed_control_spent',0)
        require(type(spent) is int and getattr(self.ledger,'_typed_control_pin',policy.sha(policy.raw(0)))==policy.sha(policy.raw(spent)),'typed control counter changed')
        spent+=len(raw);self.ledger._typed_control_spent=spent;self.ledger._typed_control_pin=policy.sha(policy.raw(spent))
        require(spent<=self.policy['max_control_bytes'],'typed cumulative metadata exhausted')
        self.ledger._write(self.ledger.root,name,raw);self.ledger._expected[name]=raw
        if not hasattr(self.ledger,'_typed_expected'):self.ledger._typed_expected={}
        self.ledger._typed_expected[name]=policy.sha(raw)
        self.ledger._typed_expected_pin=policy.sha(policy.raw(self.ledger._typed_expected))

    def lease(self):
        self.held.check(self.owner)
        require(all(a is b for a,b in zip(self._authority,(self.owner,self.stage,self.ledger,self.held,self.view,self.context,self.parent,self.parent_operation,self.registry,self.counter,self.budget,self.policy))) and policy.raw(self.policy)==self._policy_pin,'typed authority/policy object changed')
        require(not self.closed and self.context._cap is self.cap and self.ledger._typed_payload_registry is self.registry and self.registry.get(self.key) is self.counter and policy.raw(self.counter)==self._counter_pin and policy.raw(self.record)==self.pin and self.ledger._typed_payload_registry_pin==policy.sha(policy.raw(self.registry)),'typed operation replaced/refunded')
        if self.parent is not None:
            require(self.ledger._active is self.parent_operation,'typed parent changed')
            self.parent['lease']()
        else:
            self.ledger._current(full=False);self.ledger._stage(self.stage)
            require(self.ledger._active is None and ((self.record.get('batched_parent')=='actual-active-mcm-stage-v1' and self.policy['schema_version']==2 and self.record['kind']==policy.BATCHED_KIND and self.owner.active is self.stage and not self.stage.closed) or (self.stage.closed and self.owner.active is None and self.stage.reference==self.record['stage_reference'])),'typed selected stage changed')
        self.held.check(self.owner)
        self._poll_target()

    def _poll_target(self):
        require(self._target is self._target_pin,'typed target replaced')
        if self._target is not None:
            require(self._target.owner is self.owner and self._target.execution._owner is self.owner,'typed target owner changed')
            self._target.lease()
            require(self._target is self._target_pin and self.context._cap is self.cap,'typed target/capability changed after poll')
            self.held.check(self.owner)

    def preserve(self,source,*,expected_sha256,expected_bytes,index,attempt):
        from . import archive_chunks as a
        self.lease();require(type(index) is int and index==len(self.proofs) and index<self.record['reserved_chunks'],'typed chunk order')
        require(0<expected_bytes<=self.budget['chunk_bytes'] and self.preserved+expected_bytes<=self.record['reserved_payload_bytes'],'typed chunk extent')
        attempt=Path(attempt);source=Path(source)
        self._path(source);self._path(attempt)
        scope=policy.sha(policy.raw({'operation':self.sha,'index':index,'bytes':expected_bytes,'sha256':expected_sha256}))
        ref=a.preserve(source=source,attempt=attempt,expected_sha256=expected_sha256,expected_bytes=expected_bytes,scope=scope,remote=self.remote+f'-{index:012d}',transport=self.view,lease=self.lease,free_floor_bytes=self.policy['local_free_floor_bytes'])
        receipt=json.loads(_read(attempt/'complete.json'));require(policy.sha(policy.raw(receipt))==ref,'typed preserved receipt differs')
        proof={'schema_version':1,'operation_sha256':self.sha,'index':index,'source':str(source),'receipt':receipt,'receipt_sha256':ref,'fresh_full_recovery':True}
        self._publish('typed-part-'+self.sha+f'-{index:012d}.json',proof)
        self.lease()
        for name in ('snapshot.bin','readback.bin'):dispose(attempt/name,expected_bytes,expected_sha256)
        _write(attempt/'disposed.json',{'schema_version':1,'receipt_sha256':ref,'owned_transfer_payloads_disposed':True})
        self.proofs.append(proof);self.preserved+=expected_bytes
        return receipt

    def _path(self,path):
        require(path.is_absolute() and path.resolve()==path,'typed canonical owned path')
        root=self.owner.bound._run.admission.root/'research_artifacts'
        require(path.is_relative_to(root),'typed payload outside actual owned artifacts')

    def recover(self,receipt,*,attempt):
        from . import archive_consume
        from .provenance import canonical_bytes
        self.lease();self._path(Path(attempt))
        require(type(receipt) is dict and receipt['transport_identity']==self.view.identity,'typed recovery endpoint')
        # Original scope is authenticated by consumer's anchored receipt; remote
        # is deliberately restricted to this actual stage's typed namespace.
        prefix=self.ledger.selection.writer_policy(self.stage.name)['remote_prefix']+'-p'
        require(receipt['remote'].startswith(prefix),'typed recovery foreign stage')
        n=receipt['bytes'];require(type(n) is int and 0<n<=self.budget['chunk_bytes'],'typed recovery extent')
        self.counter['recovered']+=n;self.counter['chunks']+=1;self._counter_pin=policy.raw(self.counter);self.ledger._typed_payload_registry_pin=policy.sha(policy.raw(self.registry))
        require(self.counter['recovered']<=self.budget['max_recovered_bytes'] and self.counter['chunks']<=self.budget['max_chunks'],'typed recovery allowance exhausted')
        self.context._spent['logical_bytes']+=n;self.context._spent_pin=canonical_bytes(self.context._spent)
        require(self.context._spent['logical_bytes']<=self.context._record['capacity']['logical_bytes'],'typed shared recovery allowance')
        self._publish('typed-read-'+self.sha+f'-{self.recovered:016d}.json',{'receipt_sha256':policy.sha(policy.raw(receipt)),'bytes':n,'reserved':dict(self.counter)})
        # View checks exact operation remote prefix; restrict the temporary child
        # to the authenticated requested historical object, restore on any error.
        previous=self.cap['remote_prefix'];self.cap['remote_prefix']=receipt['remote'].rsplit('-',1)[0]
        try:return archive_consume.consume(receipt_bytes=policy.raw(receipt),receipt_sha256=policy.sha(policy.raw(receipt)),expected_scope=receipt['scope'],attempt=attempt,transport=self.view,lease=self.lease,free_floor_bytes=self.policy['local_free_floor_bytes'])
        finally:self.cap['remote_prefix']=previous;self.recovered+=n

    def retire_source(self,source,*,expected_sha256,expected_bytes):
        self.lease();source=Path(source);self._path(source)
        require(any(p['source']==str(source) and p['receipt']['source_sha256']==expected_sha256 and p['receipt']['bytes']==expected_bytes for p in self.proofs),'typed original source lacks successful full recovery')
        dispose(source,expected_bytes,expected_sha256)

    def retire_batched_sources(self,receipt,*,manifest,journal,batch,tokens,attempt,semantic_root):
        """Selected bundle only: fresh real transport recovery precedes retirement.

        This is sequential three-file retirement, not an atomic group unlink.
        The durable intent and archive proof retain partial-failure disposition.
        """
        from . import batched_offload_semantics as semantic
        self.lease()
        require(self.record['kind']==policy.BATCHED_KIND and self.policy['schema_version']==2,'new batched kind not selected')
        require(journal.root==self.stage.root/'matching','only actual stage generated batch namespace')
        binding=semantic.binding(journal,batch,tokens,manifest)
        require(self.record['binding']==binding,'batched original binding differs')
        require(any(p['receipt']==receipt for p in self.proofs),'archive lacks this operation preserve proof')
        raw=self.recover(receipt,attempt=attempt) # Genuine View/held/shared budget, never callback success.
        self._path(Path(semantic_root))
        semantic.recover(raw,manifest,journal,batch,tokens,Path(semantic_root))
        semantic.dispose_recovery(Path(semantic_root),manifest,batch,tokens)
        intent={'schema_version':1,'kind':'batched-retirement-intent-v1','operation_sha256':self.sha,
                'binding':binding,'receipt_sha256':policy.sha(policy.raw(receipt)),
                'recovery_attempt':str(attempt),'semantic_root':str(semantic_root),
                'failure_disposition':'any subset may be retired; archive recovery required'}
        self._publish('typed-batched-retirement-'+self.sha+'.json',intent)
        self.lease() # Last external lease before exact no-callback source join/unlinks.
        require(semantic.binding(journal,batch,tokens,manifest)==binding and journal.root==self.stage.root/'matching','retirement namespace binding changed')
        semantic.current(journal,batch,tokens)
        for suffix in semantic.SUFFIXES:
            os.unlink(f'{batch:08d}'+suffix,dir_fd=journal.fd)
        os.fsync(journal.fd);journal._root()
        self._publish('typed-batched-retired-'+self.sha+'.json',{'schema_version':1,
                      'operation_sha256':self.sha,'binding':binding,'files':3,'receipt_sha256':intent['receipt_sha256']})

    def retire_batched_group(self,receipt,*,manifest,journal,items,attempt,semantic_root):
        """Selected original-byte group: real recovery before any original unlink."""
        from . import grouped_offload_semantics as semantic
        self.lease()
        require(self.record['kind']==policy.BATCHED_KIND and self.policy['schema_version']==2,'actual selected grouped payload kind required')
        items=semantic.roster(items);binding=semantic.binding(journal,items,manifest)
        require(journal.root==self.stage.root/'matching' and self.record['binding']==binding,'group source binding differs')
        require(any(p['receipt']==receipt for p in self.proofs),'group lacks actual preservation proof')
        data=self.recover(receipt,attempt=attempt)
        self._path(Path(semantic_root));semantic.recover(data,manifest,journal,items,Path(semantic_root))
        semantic.dispose_recovery(Path(semantic_root),manifest,items)
        intent={'schema_version':1,'kind':'grouped-retirement-intent-v1','operation_sha256':self.sha,'binding':binding,'receipt_sha256':policy.sha(policy.raw(receipt)),'recovery_attempt':str(attempt),'semantic_root':str(semantic_root),'failure_disposition':'any subset may be retired; full group archive recovery required; no resume'}
        self._publish('typed-grouped-retirement-'+self.sha+'.json',intent)
        self.lease()
        require(semantic.binding(journal,items,manifest)==binding and journal.root==self.stage.root/'matching','group retirement binding changed')
        semantic.current(journal,items) # All originals rejoined after last callback.
        for batch,_ in items:
            for suffix in semantic.SUFFIXES:os.unlink(f'{batch:08d}'+suffix,dir_fd=journal.fd)
        os.fsync(journal.fd);journal._root()
        self._publish('typed-grouped-retired-'+self.sha+'.json',{'schema_version':1,'operation_sha256':self.sha,'binding':binding,'files':3*len(items),'receipt_sha256':intent['receipt_sha256']})

    def history(self):
        require(self.closed,'typed completion not yet anchored')
        return {'directory':str(self.ledger.root),'intent':self.claim_name,'intent_sha256':self.sha,'complete':self.complete_name,'complete_sha256':self.complete_sha}

@contextmanager
def operation(owner,stage,*,kind,binding,payload_bytes,chunk_count,target=None):
    op=None
    try:
        op=_Operation(owner,stage,kind,binding,payload_bytes,chunk_count,**({'target':target} if target is not None else {}))
        op.lease();yield op;op.lease()
        require(op.preserved==payload_bytes and len(op.proofs)==chunk_count,'typed operation incomplete')
        result={'schema_version':1,'operation_sha256':op.sha,'parts':len(op.proofs),'parts_sha256':policy.sha(b''.join(bytes.fromhex(policy.sha(policy.raw(p))) for p in op.proofs)),'preserved_bytes':op.preserved,'recovered_bytes':op.recovered,'assumption':policy.ASSUMPTION}
        op.complete_name='typed-complete-'+op.sha+'.json';op.complete_sha=policy.sha(policy.raw(result));op._publish(op.complete_name,result)
        op.lease();op.context._outer()
        op.closed=True
    except BaseException as error:
        owner.poisoned=True
        ledger=getattr(owner,'_archive_operations',None)
        if ledger is not None:ledger._poisoned=True
        if op is not None:
            op.context._failed=True
            try:op._publish('typed-failed-'+op.sha+'.json',{'error_type':type(error).__name__,'reservations_retained':True})
            except BaseException as failure:error.add_note('typed failure evidence: '+repr(failure))
        raise
    finally:
        if op is not None:op.closed=True;op.context._cap=op.parent

def check_history(record,*,binding,kind):
    """Caller MUST anchor record in original scientific/output completion hash."""
    require(type(record) is dict and set(record)=={'directory','intent','intent_sha256','complete','complete_sha256'},'typed historical reference schema')
    for k in ('intent','complete'):require(Path(record[k]).name==record[k] and record[k] not in ('.','..'),'typed history member')
    require(record['intent']=='typed-'+record['intent_sha256']+'.json' and record['complete']=='typed-complete-'+record['intent_sha256']+'.json','typed original claim names')
    root=Path(record['directory']);intent_raw=_read(root/record['intent']);complete_raw=_read(root/record['complete'])
    require(policy.sha(intent_raw)==record['intent_sha256'] and policy.sha(complete_raw)==record['complete_sha256'],'typed historical anchored bytes differ')
    intent=json.loads(intent_raw);complete=json.loads(complete_raw)
    require(intent['format']=='typed-payload-operation-v1' and intent['kind']==kind and intent['binding']==binding and complete['operation_sha256']==record['intent_sha256'] and complete['assumption']==policy.ASSUMPTION,'typed historical binding differs')
    count=complete['parts'];require(type(count) is int and 0<=count==intent['reserved_chunks']<=10**12,'typed historical part count')
    require(complete['preserved_bytes']==intent['reserved_payload_bytes'],'typed historical byte reservation')
    return complete

def iter_history_parts(record,*,binding,kind):
    import hashlib
    complete=check_history(record,binding=binding,kind=kind);root=Path(record['directory']);count=complete['parts'];chain=hashlib.sha256();total=0
    for index in range(count):
        p=json.loads(_read(root/('typed-part-'+record['intent_sha256']+f'-{index:012d}.json')))
        require(p['index']==index and p['operation_sha256']==record['intent_sha256'] and p['fresh_full_recovery'] is True and policy.sha(policy.raw(p['receipt']))==p['receipt_sha256'],'typed historical part differs')
        require(_read(root/('typed-part-'+record['intent_sha256']+f'-{index:012d}.json'))==policy.raw(p),'typed original ledger part changed')
        receipt=p['receipt']
        require(set(receipt)=={'schema_version','format','transport_identity','remote','member','scope','source_sha256','bytes'} and receipt['schema_version']==1 and receipt['format']=='archive-chunk-v1' and receipt['member']==receipt['remote']+'/payload.bin' and type(receipt['bytes']) is int and 0<receipt['bytes']<=4*1024**2,'typed original receipt schema')
        require(receipt['scope']==policy.sha(policy.raw({'operation':record['intent_sha256'],'index':index,'bytes':receipt['bytes'],'sha256':receipt['source_sha256']})),'typed original receipt operation join')
        chain.update(bytes.fromhex(policy.sha(policy.raw(p))));total+=receipt['bytes']
        yield p
    require(total==complete['preserved_bytes'] and chain.hexdigest()==complete['parts_sha256'],'typed historical part chain')


def ledger_evidence(ledger,*,terminal=False):
    if not hasattr(ledger,'_typed_expected'):return {}
    require(policy.sha(policy.raw(ledger._typed_expected))==ledger._typed_expected_pin and policy.sha(policy.raw(ledger._typed_payload_registry))==ledger._typed_payload_registry_pin and policy.sha(policy.raw(ledger._typed_control_spent))==ledger._typed_control_pin,'typed ledger pins changed')
    result={}
    for name,sha in ledger._typed_expected.items():
        require(name.startswith('typed-') and Path(name).name==name,'typed ledger member')
        raw=ledger._expected[name];require(policy.sha(raw)==sha and _read(ledger.root/name)==raw,'typed ledger original bytes changed');result[name]=raw
        if terminal:
            item=json.loads(raw)
            require(not name.startswith('typed-failed-'),'typed failed operation cannot complete')
            if item.get('format')=='typed-payload-operation-v1':
                complete='typed-complete-'+sha+'.json'
                require(complete in ledger._typed_expected,'typed unfinished operation')
                history=dict(directory=str(ledger.root),intent=name,intent_sha256=sha,complete=complete,complete_sha256=ledger._typed_expected[complete])
                for _ in iter_history_parts(history,binding=item['binding'],kind=item['kind']):pass
    require(sum(len(v) for v in result.values())==ledger._typed_control_spent,'typed cumulative metadata accounting differs')
    return result

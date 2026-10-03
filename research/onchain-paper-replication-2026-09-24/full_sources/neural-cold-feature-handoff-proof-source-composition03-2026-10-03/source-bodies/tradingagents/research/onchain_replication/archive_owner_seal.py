"""Explicit archived stage seals and current-owner local evidence checking.

Sealing includes a new full reserved read, never promotion of a caller-supplied
completion. These public entries own the transition; locked scientific producers
and whole-owner/terminal dispatch still require explicit integration.
"""
import json
import os
import sys
from pathlib import Path
from threading import get_ident

from . import archive_owner_stage as reads, archive_owner_operations as operations
from . import archived_stage
from .provenance import freeze, thaw

io=operations.io
require=io._require
FORMAT='archived-owner-stage-v1'


def _contract(ledger,stage,claim,result):
    writer=ledger._writers[stage.name]
    for op,kind in ((writer,'writer'),(claim,'reader')):
        require(type(op) is operations.Operation and op._ledger is ledger and op._stage is stage
            and ledger._operations.get(op.root.name) is op and op.record['kind']==kind
            and op.record['stage_intent_sha256']==stage.intent_sha256
            and set(op._terminal or {})=={'complete.json'},'archived seal completed claim binding differs')
        require(json.loads(op._terminal['complete.json'])['intent_sha256']==io._hash(io._json(thaw(op.record))),
            'archived seal claim intent differs')
    reference=io._hash(io._json(result))
    require(json.loads(writer._terminal['complete.json'])['reference_sha256']==result['archive_complete_sha256']
        and json.loads(claim._terminal['complete.json'])['reference_sha256']==reference,
        'archived seal claim references differ')
    count=result['completed_pairs']
    require(type(count) is int and (count==stage.pairs if stage.count_policy is None else 0<=count<=stage.pairs),
        'archived seal scientific denominator differs')
    path=reads.attempt_path(ledger,claim);info=path.lstat()
    contract={'owner':ledger.owner.identity,'scope':thaw(stage.scope),'policy':thaw(ledger.owner.policy),
        'kind':stage.kind,'pairs':count,'log_terminal_sha256':result['log_terminal_sha256'],
        'stream_terminal_sha256':result['stream_terminal_sha256'],
        'archive':{'backend':operations.policy.BACKEND,'writer_claim':writer.root.name,
            'writer_intent_sha256':io._hash(io._json(thaw(writer.record))),
            'reader_claim':claim.root.name,'reader_intent_sha256':io._hash(io._json(thaw(claim.record))),
            'directory':str(path),'inode':[info.st_dev,info.st_ino],'proof_sha256':reference,
            'ledger_inode':list(ledger._inode),'ledger_start_sha256':io._hash(ledger._expected['start.json']),
            'writer_inode':list(ledger._pins[writer.root.name]),'reader_inode':list(ledger._pins[claim.root.name]),
            'transport_identity':ledger.selection.record['policy']['transport_identity']}}
    if stage.retention_selection is not None:
        from . import stage_retention
        pin=stage_retention._reference(stage)
        require(all(io._json(result['retention'][k])==io._json(v) for k,v in pin.items()),
            'archived retention original producer seal differs')
        contract['retention']=result['retention']
    else:require('retention' not in result,'unselected retention proof')
    return contract


def _marker(ledger,stage,contract,result):
    return io._json({'schema_version':1,'format':FORMAT,'owner':ledger.owner.identity,'stage':stage.name,
        'stage_intent_sha256':stage.intent_sha256,'stage_inode':list(stage.inode),
        'contract':contract,'scientific_result':result,'execution_admitted':False})


class _LocalTransport:
    """Identity-only verifier endpoint; content checks cannot invoke transfers."""
    def __init__(self, identity): self.identity=identity
    def mkdir(self,*args,**kwargs): raise RuntimeError('local archive content check cannot transfer')
    put=get=mkdir


def check_content(root, *, expected_sha256, contract):
    """Callback-free local content, using an externally trusted original seal.

    This does not establish live owner authority. The caller must anchor the seal
    and serialized contract in its producer/terminal reference, not freshly hash
    untrusted content. Current-owner wrappers additionally join actual operations.
    """
    root=Path(root);io._identity(expected_sha256)
    pin=contract['archive'];journal=root.parent.parent
    ledger_root=journal/'archive-operations'
    require(pin['backend']==operations.policy.BACKEND
        and pin['directory']==str(journal/('archive-stage-read-'+pin['reader_intent_sha256'])),
        'archived content deterministic namespace differs')
    path,fd=io._open(root)
    try:
        raw=io._read(fd,'stage-complete.json',io.META_LIMIT)
        require(io._hash(raw)==expected_sha256,'archived content trusted seal differs')
        marker=json.loads(raw)
        require(type(marker.get('schema_version')) is int and marker['schema_version']==1
            and marker.get('format')==FORMAT and marker.get('execution_admitted') is False
            and io._json(marker['contract'])==io._json(contract)
            and marker['owner']==contract['owner'] and marker['stage']==root.name
            and marker['stage_inode']==list(io._signature(os.fstat(fd))[:2]),
            'archived content stage contract differs')
        intent=io._read(fd,'intent.json',io.META_LIMIT)
        require(io._hash(intent)==marker['stage_intent_sha256'],'archived content stage intent differs')
        ledger_path,lfd=io._open(ledger_root)
        try:
            require(list(io._signature(os.fstat(lfd))[:2])==pin['ledger_inode'],
                'archived content ledger inode differs')
            start=io._read(lfd,'start.json',io.META_LIMIT)
            require(io._hash(start)==pin['ledger_start_sha256'],'archived content ledger start differs')
            ledger_start=json.loads(start)
            for kind in ('writer','reader'):
                name=pin[kind+'_claim'];require(Path(name).name==name,'archived content claim name differs')
                claim_root,cfd=io._open(ledger_root/name)
                try:
                    require(list(io._signature(os.fstat(cfd))[:2])==pin[kind+'_inode'],
                        'archived content claim inode differs')
                    reads.reader.archive._inventory(cfd,{'intent.json','complete.json'})
                    claim_raw=io._read(cfd,'intent.json',io.META_LIMIT);claim=json.loads(claim_raw)
                    require(io._hash(claim_raw)==pin[kind+'_intent_sha256']
                        and claim['owner']==contract['owner'] and claim['stage']==root.name
                        and claim['stage_intent_sha256']==marker['stage_intent_sha256']
                        and claim['selection_sha256']==ledger_start['selection_sha256']
                        and claim['kind']==kind,'archived content claim binding differs')
                    completion=json.loads(io._read(cfd,'complete.json',io.META_LIMIT))
                    reference=(marker['scientific_result']['archive_complete_sha256']
                        if kind=='writer' else pin['proof_sha256'])
                    require(io._json(completion)==io._json({'schema_version':1,'reference_sha256':reference,
                        'intent_sha256':pin[kind+'_intent_sha256'],'completion_semantics':'caller-reference-only'}),
                        'archived content claim completion differs')
                    io._root(claim_root,cfd)
                finally:operations._close_descriptor(cfd)
            io._root(ledger_path,lfd)
        finally:operations._close_descriptor(lfd)
        attempt=Path(pin['directory']);info=attempt.lstat()
        require([info.st_dev,info.st_ino]==pin['inode'],'archived content read inode differs')
        result=archived_stage.check(root,attempt=attempt,expected_sha256=pin['proof_sha256'],
            transport=_LocalTransport(pin['transport_identity']),lease=lambda:None)
        require(result['policy_sha256']==operations.owners.cache_key(contract['policy']),
            'archived content policy differs')
        for name in ('owner','scope','policy','kind','pairs','log_terminal_sha256','stream_terminal_sha256'):
            # The proof uses completed_pairs for the exact scientific denominator.
            key='completed_pairs' if name=='pairs' else name
            if key in result:require(io._json(result[key])==io._json(contract[name]),
                'archived content scientific field differs: '+name)
        require(io._json(result)==io._json(marker['scientific_result']), 'archived content scientific proof differs')
        if 'restart_retention' in contract['policy']:
            require(io._json(result['retention'])==io._json(contract['retention'])
                and io._json(json.loads(intent)['restart_retention_selection'])==io._json(contract['retention']['selection']),
                'archived content original retention selector differs')
        names={'intent.json','matching','checkpoints','stage-complete.json'}|({'stream'} if contract['kind']=='mcm' else set())
        reads.reader.archive._inventory(fd,names)
        require(io._read(fd,'stage-complete.json',io.META_LIMIT)==raw,'archived content final seal differs')
        io._root(path,fd)
        return result
    finally:operations._close_descriptor(fd)


def _content_owned(owner,stage):
    """Original owner object membership; enclosing active/terminal entry authorizes."""
    ledger=getattr(owner,'_archive_operations',None)
    require(type(ledger) is operations.Ledger and ledger.owner is owner
        and ledger.selection._owner is owner and ledger._transition is owner._transition
        and not ledger._poisoned and owner.stages.get(stage.name) is stage and stage.owner is owner,
        'archived content original ledger membership differs')
    ledger._evidence();ledger._stage(stage)
    contract=thaw(stage.contract);pin=contract['archive']
    claim=ledger._operations.get(pin['reader_claim'])
    require(stage.closed and not stage.closing and type(claim) is operations.Operation,
        'archived content original completed stage required')
    result=check_content(stage.root,expected_sha256=stage.reference,contract=contract)
    require(io._json(_contract(ledger,stage,claim,result))==io._json(contract),
        'archived content original claims differ')
    return result


def _journal_members(owner):
    """Derive exact permitted namespaces from original admitted operations."""
    ledger=getattr(owner,'_archive_operations',None)
    if ledger is None:return set(),None
    require(type(ledger) is operations.Ledger and ledger.owner is owner
        and ledger.selection._owner is owner and ledger._transition is owner._transition
        and ledger.root==owner.root.parent/'archive-operations'
        and not ledger._poisoned and ledger._active is None,
        'archive terminal ledger authority differs')
    expected={'start.json':io._json(thaw(ledger.record))}
    if ledger._closed:
        expected['closed.json']=io._json({'schema_version':1,'reserved':thaw(ledger.reserved),
            'poisoned':False,'execution_admitted':False})
    require(ledger._expected==expected,'archive terminal canonical ledger metadata differs')
    ledger._evidence()
    require(set(ledger._writers)==set(owner.required),'archive required writers incomplete')
    names={ledger.root.name};claims={}
    for name,op in ledger._operations.items():
        require(op._ledger is ledger and owner.stages.get(op.record['stage']) is op._stage
            and op.root==ledger.root/name and set(op._terminal or {})=={'complete.json'},
            'archive terminal operation membership differs')
        if op.record['kind']=='reader': names.add(reads.attempt_path(ledger,op).name)
        else:require(op.record['kind']=='writer' and ledger._writers.get(op._stage.name) is op,
            'archive terminal writer membership differs')
        claims[name]={'record':thaw(op.record),'terminal':{k:io._hash(v) for k,v in op._terminal.items()},
            'inode':list(ledger._pins[name])}
    pin=operations.owners.cache_key({'ledger':ledger._identity,'claims':claims,
        'reads':ledger._reads,'reserved':thaw(ledger.reserved)})
    return names,pin


def _saved(ledger,stage,fd,raw,contract,*,closing,lock):
    """Callback-free exact evidence join; enclosing entry owns captured lock."""
    owner=ledger.owner
    require(not ledger._closed and not ledger._poisoned and getattr(owner,'_archive_operations',None) is ledger
        and ledger.selection._owner is owner and owner._transition is lock
        and ledger._transition is lock and lock.locked(),'archived seal owner/ledger authority differs')
    operations.owners.verify_current(owner);ledger._evidence();ledger._stage(stage)
    if closing:
        require(owner.active is stage and stage.closing and not stage.closed
            and stage.reference is None and stage.contract is None,'archived seal closing phase differs')
    else:
        require(stage.closed and not stage.closing and owner.active is not stage
            and stage.reference==io._hash(raw) and io._json(thaw(stage.contract))==io._json(contract),
            'archived sealed stage runtime contract differs')
    names={'intent.json','matching','checkpoints','stage-complete.json'}|({'stream'} if stage.kind=='mcm' else set())
    reads.reader.archive._inventory(fd,names)
    require(io._read(fd,'intent.json',io.META_LIMIT)==stage.intent
        and io._read(fd,'stage-complete.json',io.META_LIMIT)==raw,'archived stage marker changed')
    owner._stage_bindings(stage)
    require(io._signature(os.fstat(fd))[:2]==stage.inode,'archived stage original inode differs')
    claim=ledger._operations.get(contract['archive']['reader_claim'])
    require(type(claim) is operations.Operation,'archived stage reader claim absent')
    result=check_content(stage.root,expected_sha256=io._hash(raw),contract=contract)
    require(io._json(_contract(ledger,stage,claim,result))==io._json(contract)
        and _marker(ledger,stage,contract,result)==raw,'archived stage scientific contract differs')
    reads.reader.archive._inventory(fd,names)
    require(io._read(fd,'stage-complete.json',io.META_LIMIT)==raw,'archived stage final marker changed')
    io._root(stage.root,fd)
    return result


def _publish(ledger,stage,claim,result,lock):
    """Called only from the full read entry while it owns the original lock."""
    reads._unsealed_stage(ledger,stage)
    contract=_contract(ledger,stage,claim,result);raw=_marker(ledger,stage,contract,result)
    # Stage admission already reserved two META_LIMIT records: intent and seal.
    require(len(stage.intent)<=io.META_LIMIT and len(raw)<=io.META_LIMIT,
        'archived stage marker exceeds original stage allowance')
    path,fd=io._open(stage.root)
    try:
        require(io._signature(os.fstat(fd))[:2]==stage.inode,'archived seal stage directory changed')
        require(not os.path.lexists(stage.root/'stage-complete.json'),'archived stage seal already exists')
        stage.closing=True
        reads.reader.archive._capacity(path,ledger.selection.record['policy']['local_free_floor_bytes'],1,len(raw))
        reference=io._write(fd,'stage-complete.json',raw)
        ledger._current(full=False)
        _saved(ledger,stage,fd,raw,contract,closing=True,lock=lock)
        return reference,freeze(contract)
    finally:operations._close_descriptor(fd)


def seal(ledger,stage,*,stream_terminal_sha256=None):
    return reads._execute(ledger,stage,stream_terminal_sha256=stream_terminal_sha256,publish=True)


def _failed_check(ledger,stage,reference,primary):
    # One owner-level failure record uses the fixed four-record ledger allowance.
    # Earlier successful read claims are historical evidence and stay unchanged.
    ledger.owner.poisoned=True;ledger._poisoned=True
    name='failed-stage-check.json'
    raw=io._json({'schema_version':1,'status':'failed','stage':stage.name,
        'stage_sha256':reference,'error_type':type(primary).__name__,'prior_claims_preserved':True})
    try:
        if name not in ledger._expected:
            ledger._write(ledger.root,name,raw);ledger._expected[name]=raw
    except io.CleanupFailure as error:raise error from primary
    except BaseException as error:primary.add_note('archived stage check failure evidence unavailable: '+repr(error))


def check(ledger,stage):
    require(type(ledger) is operations.Ledger and type(stage) is operations.owners.Stage
        and stage.owner is ledger.owner,'actual archived ledger and stage required')
    owner=ledger.owner;lock=owner._transition;thread=get_ident()
    require(ledger._transition is lock and lock.acquire(blocking=False),'concurrent archived sealed check')
    checking=False;fd=None;reference=None
    try:
        require(not owner.closed and not owner.closing and not owner.poisoned and not ledger._closed
            and not ledger._poisoned and stage.closed and not stage.closing
            and stage.reference is not None and stage.contract is not None,
            'current sealed archived stage required')
        reference=stage.reference;contract=thaw(stage.contract);checking=True
        path,fd=io._open(stage.root);raw=io._read(fd,'stage-complete.json',io.META_LIMIT)
        require(io._hash(raw)==reference,'archived stage trusted seal hash differs')
        def live():
            require(get_ident()==thread and owner._transition is lock and lock.locked(),
                'archived sealed check transition changed')
            ledger._current(full=False)
            require(get_ident()==thread and owner._transition is lock and lock.locked(),
                'archived sealed check transition changed during lease')
        try:
            live();_saved(ledger,stage,fd,raw,contract,closing=False,lock=lock)
            live();result=_saved(ledger,stage,fd,raw,contract,closing=False,lock=lock)
        finally:
            owned=fd;fd=None;operations._close_descriptor(owned)
        return freeze(result)
    except BaseException as primary:
        if checking:_failed_check(ledger,stage,reference,primary)
        raise
    finally:
        try:
            if fd is not None:operations._close_descriptor(fd)
        finally:
            primary=sys.exception()
            try:lock.release()
            except BaseException as error:
                owner.poisoned=True
                fatal=io.CleanupFailure('archived sealed check lock release unresolved; worker must stop')
                fatal.add_note(repr(error));raise fatal from (primary if primary is not None else error)

"""Explicit archived stage seals and current-owner local evidence checking.

Sealing includes a new full reserved read, never promotion of a caller-supplied
completion. These public entries own the transition; locked scientific producers
and whole-owner/terminal dispatch still require explicit integration.
"""
import json
import os
import sys
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
    return {'owner':ledger.owner.identity,'scope':thaw(stage.scope),'policy':thaw(ledger.owner.policy),
        'kind':stage.kind,'pairs':count,'log_terminal_sha256':result['log_terminal_sha256'],
        'stream_terminal_sha256':result['stream_terminal_sha256'],
        'archive':{'backend':operations.policy.BACKEND,'writer_claim':writer.root.name,
            'writer_intent_sha256':io._hash(io._json(thaw(writer.record))),
            'reader_claim':claim.root.name,'reader_intent_sha256':io._hash(io._json(thaw(claim.record))),
            'directory':str(path),'inode':[info.st_dev,info.st_ino],'proof_sha256':reference}}


def _marker(ledger,stage,contract,result):
    return io._json({'schema_version':1,'format':FORMAT,'owner':ledger.owner.identity,'stage':stage.name,
        'stage_intent_sha256':stage.intent_sha256,'stage_inode':list(stage.inode),
        'contract':contract,'scientific_result':result,'execution_admitted':False})


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
    result=archived_stage.check(stage.root,attempt=reads.attempt_path(ledger,claim),
        expected_sha256=contract['archive']['proof_sha256'],transport=ledger.selection._transport,lease=lambda:None)
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

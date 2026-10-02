"""Reserved archived scientific reads under the actual current owner.

One full remote replay per consumed read claim. Completion remains provisional
until final local joins and descriptor cleanup succeed. No stage seal, producer
switch, post-owner-close authority or empirical admission is supplied here.
"""
import json
import os
import sys
from threading import get_ident

from . import archive_owner_operations as operations, archived_stage
from . import archive_pair_reader as reader
from .archive_owner_writer import _abort
from .provenance import freeze, thaw

io=operations.io
require=io._require


def attempt_path(ledger,claim):
    """Deterministic sibling of the ledger, outside both strict inventories."""
    return ledger.root.parent/('archive-stage-read-'+io._hash(io._json(thaw(claim.record))))


def verify(ledger,stage,*,stream_terminal_sha256=None):
    require(type(ledger) is operations.Ledger and type(stage) is operations.owners.Stage,
        'actual archive ledger and stage required')
    owner=ledger.owner;lock=owner._transition;thread=get_ident()
    require(ledger._transition is lock and lock.acquire(blocking=False),
        'concurrent reserved archive read transition')
    previous=set(ledger._operations);claim=None;active=True
    source_fd=attempt_fd=None
    try:
        try:
            claim=ledger._claim(stage,'reader')
            def lease():
                require(active and get_ident()==thread and owner._transition is lock
                    and ledger._transition is lock and lock.locked(),'archive read lease expired or transition changed')
                ledger._live(claim)
                require(active and get_ident()==thread and owner._transition is lock
                    and ledger._transition is lock and lock.locked(),'archive read transition changed during lease')
            writer=ledger._writers[stage.name]
            require(set(writer._terminal)=={'complete.json'},'archive writer has conflicting terminal evidence')
            reference=json.loads(writer._terminal['complete.json'])['reference_sha256']
            policy=thaw(owner.policy);scope=thaw(stage.scope)
            archive_policy=ledger.selection.writer_policy(stage.name)
            limits=ledger.selection.record['policy'];attempt=attempt_path(ledger,claim)
            lease();owner._stage_bindings(stage)
            source,source_fd=io._open(stage.root/'matching')
            snapshot=reader._Snapshot(source,source_fd,reference,owner.identity,scope,
                archive_policy,ledger.selection._transport)
            require(snapshot.limits==policy['log'] and snapshot.start['max_iterations']==owner.matching['max_iterations'],
                'archive scientific matching limits differ')
            count=snapshot.terminal['state']['completed_pairs']
            require(type(count) is int and (count==stage.pairs if stage.count_policy is None
                else 0<=count<=stage.pairs),'archive scientific pair denominator differs')
            expected=None
            def complete(result):
                nonlocal attempt_fd,expected
                # Pin the actual verifier namespace before completion callbacks.
                path,attempt_fd=io._open(attempt)
                expected=io._json(thaw(result))
                require(io._read(attempt_fd,'complete.json',io.META_LIMIT)==expected,
                    'archive scientific completion differs')
                io._root(path,attempt_fd)
                ledger._complete_locked(claim,io._hash(expected))
            result=archived_stage.verify(stage.root,owner=owner.identity,scope=scope,policy=policy,
                kind=stage.kind,pairs=count,log_terminal_sha256=snapshot.complete['terminal_sha256'],
                stream_terminal_sha256=stream_terminal_sha256,archive_complete_sha256=reference,
                archive_policy=archive_policy,attempt=attempt,transport=ledger.selection._transport,
                lease=lease,max_read_metadata_bytes=limits['max_read_metadata_bytes'],
                max_stage_bytes=limits['max_stage_bytes'],on_verified=complete)
            # All external callbacks and generic verifier cleanup are over.
            operations.owners.verify_current(owner);ledger._evidence();ledger._stage(stage)
            owner._stage_bindings(stage);snapshot.check()
            require(not ledger._closed and not ledger._poisoned and ledger._active is None
                and owner._transition is lock and ledger._transition is lock and lock.locked()
                and getattr(owner,'_archive_operations',None) is ledger
                and set(claim._terminal)=={'complete.json'},'archive read final authority differs')
            require(io._json(result)==expected and io._read(attempt_fd,'complete.json',io.META_LIMIT)==expected,
                'archive read final completion differs')
            reader.archive._inventory(attempt_fd,{'intent.json','checkpoint-references.bin','events','complete.json'})
            io._root(attempt,attempt_fd)
            return freeze(result)
        finally:
            # Independent descriptors each close once even if an earlier close
            # is uncertain. No success escapes an unresolved owned descriptor.
            try:
                if attempt_fd is not None:operations._close_descriptor(attempt_fd)
            finally:
                if source_fd is not None:operations._close_descriptor(source_fd)
    except BaseException as primary:
        if claim is None:
            candidates=[op for name,op in ledger._operations.items() if name not in previous]
            if len(candidates)==1:claim=candidates[0]
        if claim is not None:_abort(ledger,claim,None,primary)
        raise
    finally:
        active=False;primary=sys.exception()
        try:lock.release()
        except BaseException as error:
            owner.poisoned=True
            fatal=io.CleanupFailure('archive read transition release unresolved; worker must stop')
            fatal.add_note(repr(error))
            raise fatal from (primary if primary is not None else error)

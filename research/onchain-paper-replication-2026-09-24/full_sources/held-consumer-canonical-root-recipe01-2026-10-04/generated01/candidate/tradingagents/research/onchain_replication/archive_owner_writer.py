"""Actual archive writer under a reserved, exclusive current-owner transition.

This additive callback boundary does not switch the scientific producers or
seal a stage. Callback values are caller-owned; only the writer's event archive
is finalized here. Final checks observe local evidence, not remote availability
after the writer's own full replay. No extra unreserved replay is performed.
"""
import os
import sys
from threading import get_ident

from . import archive_owner_operations as operations
from . import archive_pair_writer as writer, archive_pair_reader as reader
from .provenance import thaw, freeze

io = operations.io
require = io._require


def _abort(ledger, claim, log, primary):
    cleanup = []
    try:
        if log is not None and not log.closed:
            try:log.fail('reserved archive producer failed')
            except BaseException as error:
                primary.add_note('archive log failure: '+repr(error))
                if not isinstance(error,Exception):cleanup.append(error)
            if not log.closed:
                try:log.close()
                except BaseException as error:cleanup.append(error)
        if claim is not None and 'failed.json' not in (claim._terminal or {}):
            try:ledger._failure(claim,primary)
            except BaseException as error:cleanup.append(error)
    finally:ledger.owner.poisoned = True
    if cleanup:
        fatal = io.CleanupFailure('reserved archive writer cleanup unresolved; worker must stop')
        for error in cleanup:fatal.add_note(repr(error))
        raise fatal from primary


def run(ledger, stage, produce):
    """Run one callback(log, live_lease) and return (caller_value, frozen_receipt).

    The public entry acquires the lock itself. A surrounding scientific producer
    already holding that lock must be restructured explicitly; testing locked()
    alone does not establish caller ownership and is not an alternate entry.
    """
    require(type(ledger) is operations.Ledger and type(stage) is operations.owners.Stage
        and callable(produce),'actual archive ledger/stage and producer required')
    with operations.owners._held(ledger.owner) as held:
        return _run_locked(ledger, stage, produce, held=held, science_lease=lambda: None)


def _run_locked(ledger, stage, produce, *, held, science_lease):
    require(type(ledger) is operations.Ledger and type(stage) is operations.owners.Stage
        and type(held) is operations.owners._HeldTransition
        and callable(produce) and callable(science_lease), 'actual archive producer required')
    owner = ledger.owner; held.check(owner); lock = held.lock; thread = held.thread
    require(ledger._transition is lock, 'archive writer transition differs')
    previous = ledger._writers.get(stage.name)
    claim = log = None;active = True
    dispatch_scope=None
    try:
        claim = ledger._claim(stage,'writer')
        def lease():
            held.check(owner); science_lease()
            require(active and get_ident() == thread and owner._transition is lock
                and ledger._transition is lock and lock.locked(), 'archive writer lease expired or transition changed')
            ledger._live(claim); science_lease(); held.check(owner)
            require(active and get_ident() == thread and owner._transition is lock
                and ledger._transition is lock and lock.locked(), 'archive writer transition changed during lease')
        from .archive_dispatch import binding
        context=binding(ledger.selection._transport,ledger,stage,claim,held,lease)
        context.__enter__();dispatch_scope=context
        archive_policy = ledger.selection.writer_policy(stage.name)
        p = thaw(owner.policy);scope = thaw(stage.scope);root = stage.root/'matching'
        lease()
        log = writer.ArchivePairLog(root,owner=owner.identity,scope=scope,limits=p['log'],
            max_iterations=owner.matching['max_iterations'],lease=lease,
            transport=ledger.selection._transport,archive_policy=archive_policy)
        inode = log.root_identity;start = log.start_sha;archive_start = log.archive_start_sha
        value = produce(log,lease)
        lease()
        count = log.state['completed_pairs']
        require((stage.count_policy is not None and count <= stage.pairs) or
            (stage.count_policy is None and count == stage.pairs),'archive writer pair denominator differs')
        terminal = log.finish();complete = log.archive_complete_sha
        path,fd = io._open(root)
        try:
            require(io._signature(os.fstat(fd))[:2] == inode,'archive writer source directory changed')
            snapshot = reader._Snapshot(root,fd,complete,owner.identity,scope,archive_policy,
                ledger.selection._transport)
            require(snapshot.start_sha == start and snapshot.archive_sha == archive_start
                and snapshot.complete['terminal_sha256'] == terminal
                and snapshot.limits == p['log'] and snapshot.start['max_iterations'] == owner.matching['max_iterations']
                and snapshot.terminal['state']['completed_pairs'] == count,
                'archive writer original source pins differ')
            receipt = freeze({'schema_version':1,'owner':owner.identity,'stage':stage.name,
                'stage_intent_sha256':stage.intent_sha256,'writer_intent_sha256':io._hash(io._json(thaw(claim.record))),
                'start_sha256':start,'terminal_sha256':terminal,'archive_complete_sha256':complete,
                'completed_pairs':count,'execution_admitted':False})
            ledger._complete_locked(claim,complete)
            ledger._current(full=False);ledger._stage(stage)
            # Last external owner callback is over. Rejoin source and claim
            # evidence without calling the already closed writer or its lease.
            snapshot.check();ledger._evidence();operations.owners.verify_current(owner)
            require(owner.active is stage and not stage.closed and owner._transition is lock
                and ledger._transition is lock and lock.locked(),'archive writer final transition differs')
            io._root(path,fd)
        finally:operations._close_descriptor(fd)
        return value,receipt
    except BaseException as primary:
        if claim is None:
            candidate = ledger._writers.get(stage.name)
            if candidate is not previous:claim = candidate
        # A preexisting claim/refused duplicate is left byte-for-byte intact.
        if claim is not None:_abort(ledger,claim,log,primary)
        raise
    finally:
        try:
            if dispatch_scope is not None:dispatch_scope.__exit__(*sys.exc_info())
        finally:active = False

"""Durable whole-operation allowances; not transport metering or stage admission.

Claims bind the exact current owner and actual stage. All allowances are spent
before returning control to a caller, including failed/ambiguous operations.
No recovery/reopen API exists. Scientific and post-owner-close routes must be
integrated separately; completion only records a caller-supplied reference.
"""
import os
import sys
from pathlib import Path

from . import archive_owner_policy as policy, compact_owner as owners
from .provenance import freeze, thaw

io = owners.io
require = io._require


def _close_descriptor(fd):
    primary = sys.exc_info()[1]
    if primary is not None:io._close_after_failure(lambda:os.close(fd),primary)
    else:io._cleanup((lambda:os.close(fd),))


def control_bytes(stages, reads):
    return (4+3*stages*(1+reads))*io.META_LIMIT


class Operation:
    __slots__ = ('_ledger','_stage','_record','_root','_terminal')
    def __init__(self, ledger, stage, root, record):
        for key,value in (('_ledger',ledger),('_stage',stage),('_root',root),
                          ('_record',freeze(record)),('_terminal',False)):
            object.__setattr__(self,key,value)
    def __setattr__(self,name,value):raise AttributeError('archive operation is immutable')
    root = property(lambda self:self._root)
    record = property(lambda self:self._record)
    def lease(self):self._ledger._lease(self)
    def complete(self, reference_sha256):self._ledger._complete(self,reference_sha256)
    def fail(self, error):self._ledger._fail(self,error)


class Ledger:
    def __init__(self, selection):
        self.selection = selection;self.owner = selection._owner
        self._transition = self.owner._transition
        self.root = Path(self.owner.bound.record['journal_directory'])/'archive-operations'
        self.record = freeze({'schema_version':1,'format':'archive-owner-reservations-v1',
            'selection_sha256':owners.cache_key(thaw(selection.record)),
            'owner':self.owner.identity,'control_metadata_bytes':control_bytes(
                len(self.owner.required),selection.record['policy']['max_stage_verifications']),
            'completion_semantics':'caller-reference-only','execution_admitted':False})
        self._operations = {};self._writers = {};self._reads = {};self._active = None
        self._spent = {'remote_payload_bytes':0,'decoded_transfer_bytes':0,'metadata_bytes':0}
        self._spent_sha = owners.cache_key(self._spent)
        self._closed = self._poisoned = False
        self._expected = {'start.json':io._json(thaw(self.record))}
        self._pins = {}
        policy.writer.archive._capacity(self.root.parent,selection.record['policy']['local_free_floor_bytes'],
            1,self.record['control_metadata_bytes'])
        self.root.mkdir()
        parent,fd = io._open(self.root.parent)
        try:os.fsync(fd);io._root(parent,fd)
        finally:_close_descriptor(fd)
        path,fd = io._open(self.root)
        try:
            self._inode = io._signature(os.fstat(fd))[:2]
            io._write(fd,'start.json',self._expected['start.json'])
        finally:_close_descriptor(fd)
        self._identity = owners.cache_key(self._configuration())

    reserved = property(lambda self:freeze(self._spent))

    def _configuration(self):
        return {'root':str(self.root),'inode':list(self._inode),'record':thaw(self.record),
            'selection':thaw(self.selection.record),'owner':self.owner.identity}

    def _evidence(self):
        require(owners.cache_key(self._configuration()) == self._identity,
            'archive reservation identity changed')
        require(owners.cache_key(self._spent) == self._spent_sha,'archive reservation accounting changed')
        root,fd = io._open(self.root)
        try:
            require(io._signature(os.fstat(fd))[:2] == self._inode,'archive reservation directory changed')
            policy.writer.archive._inventory(fd,set(self._expected)|set(self._operations))
            for name,raw in self._expected.items():
                require(io._read(fd,name,io.META_LIMIT) == raw,'archive reservation metadata changed')
            io._root(root,fd)
        finally:_close_descriptor(fd)
        for name,operation in self._operations.items():
            root,fd = io._open(self.root/name)
            try:
                require(io._signature(os.fstat(fd))[:2] == self._pins[name], 'archive claim directory changed')
                expected = {'intent.json':io._json(thaw(operation.record))}
                if operation._terminal:expected.update(operation._terminal)
                policy.writer.archive._inventory(fd,set(expected))
                for member,raw in expected.items():
                    require(io._read(fd,member,io.META_LIMIT) == raw,'archive claim metadata changed')
                io._root(root,fd)
            finally:_close_descriptor(fd)

    def _current(self, *, full):
        require(not self._closed and not self._poisoned,'archive reservations are terminal')
        require(getattr(self.owner,'_archive_operations',None) is self,
            'archive reservation owner binding changed')
        require(self.selection._owner is self.owner and self._transition is self.owner._transition,
            'archive selection owner or transition changed')
        if full:self.selection.check()
        else:self.owner.lease()
        require(policy.writer.archive._transport(self.selection._transport) ==
            self.selection.record['policy']['transport_identity'],'archive endpoint changed')
        owners.verify_current(self.owner)
        self._evidence()
        require(not self._closed and not self._poisoned
            and getattr(self.owner,'_archive_operations',None) is self,
            'archive reservation revoked during callback')

    def _stage(self, stage):
        require(type(stage) is owners.Stage and stage.owner is self.owner
            and self.owner.stages.get(stage.name) is stage and stage.name in self.owner.required,
            'actual archive reservation stage required')
        stage.integrity();owners.exact(stage.root,'intent.json',stage.intent)
        require(io._signature(stage.root.lstat())[:2] == stage.inode,'archive stage directory changed')

    def _live(self, operation):
        require(not operation._terminal and self._active is operation
            and self._operations.get(operation.root.name) is operation,'archive operation is terminal or replaced')
        self._current(full=False);self._stage(operation._stage)
        require(not operation._terminal and self._active is operation
            and self._operations.get(operation.root.name) is operation,
            'archive operation revoked during callback')
        if operation.record['kind'] == 'writer':
            require(self.owner.active is operation._stage and not operation._stage.closed,
                'archive writer stage is no longer active')

    @owners.transition
    def _lease(self, operation):
        require(self._active is operation and not operation._terminal,'archive operation is terminal')
        try:self._live(operation)
        except BaseException as error:self._failure(operation,error);raise

    def _write(self, root, name, raw):
        policy.writer.archive._capacity(root,self.selection.record['policy']['local_free_floor_bytes'],1,len(raw))
        path,fd = io._open(root)
        try:
            pin = self._inode if root == self.root else self._pins[root.name]
            require(io._signature(os.fstat(fd))[:2] == pin,'archive publication directory changed')
            io._write(fd,name,raw);io._root(path,fd)
        finally:_close_descriptor(fd)

    def _claim(self, stage, kind):
        self._current(full=True);self._stage(stage)
        require(self._active is None,'archive operation already active')
        if kind == 'writer':
            require(self.owner.active is stage and not stage.closed and stage.name not in self._writers,
                'archive writer already claimed or stage inactive')
            ordinal = 0
        else:
            writer = self._writers.get(stage.name)
            require(writer is not None and writer._terminal and 'complete.json' in writer._terminal,
                'completed archive writer reservation required')
            ordinal = self._reads.get(stage.name,0)
            require(ordinal < self.selection.record['policy']['max_stage_verifications'],
                'archive verification allowance exhausted')
        payload = self.owner.policy['log']['max_events']*policy.writer.events.RECORD_BYTES
        limits = self.selection.record['policy']
        metadata = limits['max_writer_metadata_bytes'] if kind == 'writer' else limits['max_stage_bytes']
        record = {'schema_version':1,'owner':self.owner.identity,'stage':stage.name,
            'stage_intent_sha256':stage.intent_sha256,'kind':kind,'ordinal':ordinal,
            'selection_sha256':self.record['selection_sha256'],
            'reserved_remote_payload_bytes':payload if kind == 'writer' else 0,
            'reserved_decoded_transfer_bytes':payload*(3 if kind == 'writer' else 1),
            'reserved_metadata_bytes':metadata+3*io.META_LIMIT,'execution_admitted':False}
        totals = {name:self._spent[name]+record['reserved_'+name] for name in self._spent}
        require(all(totals[name] <= limits['max_workflow_metadata_bytes' if name == 'metadata_bytes' else 'max_'+name] for name in totals),'archive reservation budget exhausted')
        # All callbacks precede the reservation/creation transition.
        self._current(full=False);self._stage(stage)
        name = kind+'-'+stage.name+f'-{ordinal:04d}'
        operation = Operation(self,stage,self.root/name,record)
        self._spent = totals;self._spent_sha = owners.cache_key(totals)
        self._active = operation;self._operations[name] = operation
        if kind == 'writer':self._writers[stage.name] = operation
        else:self._reads[stage.name] = ordinal+1
        try:
            operation.root.mkdir()
            path,fd = io._open(operation.root)
            try:self._pins[name] = io._signature(os.fstat(fd))[:2]
            finally:_close_descriptor(fd)
            self._write(operation.root,'intent.json',io._json(record))
            parent,fd = io._open(self.root)
            try:os.fsync(fd);io._root(parent,fd)
            finally:_close_descriptor(fd)
            self._live(operation)
            return operation
        except BaseException as error:
            self._failure(operation,error);raise

    @owners.transition
    def writer(self, stage):return self._claim(stage,'writer')
    @owners.transition
    def reader(self, stage):return self._claim(stage,'reader')

    def _failure(self, operation, error):
        self._poisoned = True
        raw = io._json({'schema_version':1,'status':'failed','error_type':type(error).__name__,
            'reservations_retained':True})
        try:
            self._write(operation.root,'failed.json',raw)
            previous = operation._terminal or {}
            object.__setattr__(operation,'_terminal',dict(previous,**{'failed.json':raw}))
        except BaseException as evidence:error.add_note('archive failed-claim evidence unavailable: '+repr(evidence))

    @owners.transition
    def _complete(self, operation, reference):
        io._identity(reference)
        require(self._active is operation and not operation._terminal,'archive operation is terminal')
        raw = io._json({'schema_version':1,'reference_sha256':reference,
            'intent_sha256':io._hash(io._json(thaw(operation.record))),
            'completion_semantics':'caller-reference-only'})
        try:
            self._live(operation)
            self._write(operation.root,'complete.json',raw)
            object.__setattr__(operation,'_terminal',{'complete.json':raw})
            self._current(full=False);self._stage(operation._stage)
            self._active = None
        except BaseException as error:self._failure(operation,error);raise

    @owners.transition
    def _fail(self, operation, error):
        require(isinstance(error,BaseException),'archive failure cause required')
        require(self._active is operation and not operation._terminal,'archive operation already terminal')
        self._failure(operation,error)

    @owners.transition
    def close(self):return self._close()

    def _close(self):
        if self._closed:return
        self._closed = True
        if self._active and not self._active._terminal:
            self._failure(self._active,RuntimeError('archive reservation abandoned'))
        raw = io._json({'schema_version':1,'reserved':self._spent,'poisoned':self._poisoned,
            'execution_admitted':False})
        self._write(self.root,'closed.json',raw);self._expected['closed.json'] = raw


def attach(selection):
    require(type(selection) is policy.Selection,'actual registered archive selection required')
    owner = selection._owner
    require(type(owner) is owners.Owner and owner._transition.acquire(blocking=False),
        'concurrent compact owner transition')
    try:
        require(not hasattr(owner,'_archive_operations') and not owner.stages and owner.active is None,
            'fresh owner without archive reservation ledger required')
        selection.check();owners.verify_current(owner)
        require(not owner.stages and owner.active is None,'fresh owner changed during archive activation')
        required = control_bytes(len(owner.required),selection.record['policy']['max_stage_verifications'])
        require(selection.record['capacity'].get('operation_control_metadata_bytes') == required,
            'registered archive reservation metadata allowance absent')
        ledger = Ledger(selection);owner._archive_operations = ledger
        try:ledger._current(full=True)
        except BaseException as error:
            ledger._poisoned = True
            io._close_after_failure(ledger._close,error);raise
        return ledger
    finally:owner._transition.release()

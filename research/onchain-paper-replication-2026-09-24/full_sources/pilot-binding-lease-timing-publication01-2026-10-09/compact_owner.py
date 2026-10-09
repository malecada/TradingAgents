"""Explicit registered compact ownership layered on a live first-owner Binding.

This does not enable native production or replace its representation seal. It
binds the selected compact policy and exclusively owns dictionary/MCM evidence
stages. Scientific workload derivation and numerical artifact publication remain
producer responsibilities. No failed-owner reopen or successor is inferred.

Full Binding.check runs at stage boundaries. Inner leases verify the current
claim/guard and small immutable owner/intent records under the caller's frozen
source/input contract; they do not rehash graph payloads or replay pair history.
"""
import json
import os
import hashlib
import sys
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from threading import Lock, get_ident

from . import matching_owner, compact_policy, compact_matcher, compact_stage
from . import score_batches as io
from .cache import cache_key
from .provenance import canonical_bytes, freeze, thaw

require = io._require
LIMIT = 65536
OWNER_BYTES = 2 * LIMIT
STAGE_BYTES = 2 * io.META_LIMIT
DICTIONARY_COUNT_POLICY = 'capacity-with-exact-completion-v1'


class _HeldTransition:
    __slots__ = ('owner','lock','thread','active')
    def __init__(self, owner, lock):
        for name,value in (('owner',owner),('lock',lock),('thread',get_ident()),('active',True)):
            object.__setattr__(self,name,value)

    def __setattr__(self,name,value): raise AttributeError('captured transition is immutable')

    def check(self, owner):
        require(self.active and self.owner is owner and get_ident() == self.thread
            and owner._transition is self.lock and getattr(owner, '_held_transition', None) is self
            and self.lock.locked(), 'captured compact transition expired or changed')


@contextmanager
def _held(owner):
    """Own one exact transition; its token cannot outlive or cross this scope."""
    require(type(owner) is Owner, 'actual compact owner required')
    if owner.required[0]=='dictionary-import':
        with _held_import(owner) as token:yield token
        return
    lock = owner._transition
    require(lock.acquire(blocking=False), 'concurrent compact owner transition')
    token = _HeldTransition(owner, lock); owner._held_transition = token
    try:
        token.check(owner); yield token; token.check(owner)
    finally:
        primary = sys.exception(); object.__setattr__(token,'active',False)
        if getattr(owner, '_held_transition', None) is token: del owner._held_transition
        try: lock.release()
        except BaseException as error:
            owner.poisoned = True
            fatal = io.CleanupFailure('compact transition release unresolved; worker must stop')
            fatal.add_note(repr(error)); raise fatal from (primary if primary is not None else error)


@contextmanager
def _held_import(owner):
    from . import import_metadata as import_io
    lock=owner._transition
    require(lock.acquire(blocking=False),'concurrent compact owner transition')
    token=None
    def release():
        try:lock.release()
        except BaseException:
            owner.poisoned=True
            raise
    try:
        token=_HeldTransition(owner,lock);owner._held_transition=token
        token.check(owner);yield token;token.check(owner)
    finally:
        if token is not None:
            object.__setattr__(token,'active',False)
            if getattr(owner,'_held_transition',None) is token:del owner._held_transition
        import_io.close_actions((release,))


def _stage_content(stage):
    """Callback-free content only; callers supply active or terminal authority."""
    if getattr(stage,'kind',None)=='dictionary-import':
        from .original_import_stage import content
        return content(stage)
    contract = thaw(stage.contract)
    if 'batched' in contract:
        from .compact_mcm_batched import stage_content
        return stage_content(stage)
    if 'archive' not in contract:
        return compact_stage.verify(stage.root, expected_sha256=stage.reference,
                                    lease=lambda: None, **contract)
    from . import archive_owner_seal
    return archive_owner_seal._content_owned(stage.owner, stage)


def transition(function):
    @wraps(function)
    def call(self, *args, **kwargs):
        require(self._transition.acquire(blocking=False), 'concurrent compact owner transition')
        try: return function(self, *args, **kwargs)
        finally:
            def release():
                try:self._transition.release()
                except BaseException:self.poisoned=True;raise
            io._release(release)
    return call


def present(path): return path.exists() or path.is_symlink()


def body(value):
    raw = canonical_bytes(value); require(len(raw) <= LIMIT, 'compact owner metadata capacity')
    return raw


def entries(root, allowed, *, required,_imported=False):
    if _imported:
        from . import import_metadata as import_io
        return import_io.entries(root,allowed,required=required)
    path, fd = io._open(root)
    try:
        seen = set()
        with io._closing(os.scandir(fd)) as iterator:
            for entry in iterator:
                require(len(seen) < len(allowed) and entry.name in allowed, 'foreign compact owner inventory')
                seen.add(entry.name)
        require(required <= seen, 'missing compact owner inventory'); io._root(path, fd)
    finally: io._release(lambda: os.close(fd))


def exact(root, name, expected):
    path, fd = io._open(root)
    try:
        require(io._read(fd, name, LIMIT) == expected, 'compact owner metadata changed')
        io._root(path, fd)
    finally: io._release(lambda: os.close(fd))


class Stage:
    def __init__(self, owner, name, scope, pairs, reservation, count_policy=None, retention_selection=None):
        self.owner = owner; self.name = name; self.root = owner.root / name
        self.scope = freeze(scope); self.pairs = pairs; self.reservation = reservation
        self.kind = 'dictionary' if name == 'dictionary' else 'mcm'
        self.count_policy = freeze(count_policy) if count_policy is not None else None
        self.retention_selection = freeze(retention_selection) if retention_selection is not None else None
        self.closed = self.closing = False; self.reference = None; self.contract = None
        self.intent = io._json(self.intent_value())
        self.intent_sha256 = io._hash(self.intent)
        owner.lease()  # Scope/source hashing must not leave a stale creation lease.
        self.root.mkdir()
        parent, fd = io._open(owner.root)
        try: os.fsync(fd); io._root(parent, fd)
        finally: io._release(lambda: os.close(fd))
        root, fd = io._open(self.root)
        try:
            self.inode = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
            io._write(fd, 'intent.json', self.intent); io._root(root, fd)
        finally: io._release(lambda: os.close(fd))

    def intent_value(self):
        value = {'schema_version': 1, 'owner': self.owner.identity, 'stage': self.name,
            'kind': self.kind, 'scope': thaw(self.scope), 'pairs': self.pairs,
            'logical_reservation_bytes': self.reservation, 'policy_sha256': cache_key(thaw(self.owner.policy))}
        if self.count_policy is not None: value['pair_count_policy'] = thaw(self.count_policy)
        if self.retention_selection is not None:value['restart_retention_selection']=thaw(self.retention_selection)
        return value

    def integrity(self):
        require(io._hash(self.intent) == self.intent_sha256 and io._json(self.intent_value()) == self.intent
            and self.root == self.owner.root / self.name, 'compact stage runtime contract changed')

    def lease(self):
        require(not self.closed, 'compact stage is terminal')
        self.integrity()
        self.owner.lease()
        require(self.owner.active is self and self.owner.stages.get(self.name) is self, 'compact stage owner differs')
        info = self.root.lstat()
        require((info.st_dev, info.st_ino) == self.inode, 'compact stage directory changed')
        exact(self.root, 'intent.json', self.intent)
        allowed = {'intent.json', 'matching', 'checkpoints'}
        if self.kind == 'mcm': allowed.add('stream')
        if self.closing: allowed.add('stage-complete.json')
        entries(self.root, allowed, required={'intent.json'})


class Owner:
    def __init__(self, bound, policy_input, envelope, descriptor, *, imported=None):
        self.bound = bound; self.policy = freeze(envelope['stage_policy'])
        self._bound = bound; self._run = bound._run
        self._binding_sha256 = cache_key(self.binding_value())
        self.maximum = envelope['max_workflow_retained_logical_bytes']
        self.matching = freeze(descriptor['configs']['matching'])
        if imported is None:
            require('dictionary_origin' not in descriptor,'imported stage requires typed prebirth preparation')
            self.required = ('dictionary',) + tuple('mcm-' + h for h in descriptor['required_graphs'])
        else:
            from .original_import_preparation import PreparedImport
            require(type(imported) is PreparedImport and imported._bound is bound,'actual original preparation required')
            contract=imported.stage_contract()
            require(contract['descriptor_sha256']==bound.record['workflow_identity'],'imported owner descriptor differs')
            self.required=tuple(contract['required_stages'])
        require(len(set(self.required)) == len(self.required), 'duplicate compact required stage')
        self.root = Path(bound.record['journal_directory']) / 'compact'
        self.active = None; self.stages = {}; self.reserved = self._reserved = OWNER_BYTES
        require(self.maximum >= OWNER_BYTES, 'compact workflow cannot reserve owner metadata')
        self._transition = Lock()
        self.poisoned = self.closed = self.closing = False
        record = {'schema_version': 1, 'backend': compact_policy.BACKEND, 'binding': thaw(bound.record),
            'context': thaw(bound.context), 'policy_input': policy_input,
            'policy_sha256': bound._run.admission.inputs[policy_input]['sha256'],
            'required_stages': list(self.required), 'maximum_retained_logical_bytes': self.maximum}
        if imported is not None:record['original_import']=contract
        self.identity = cache_key(record); self.start = body(record)
        self.configuration_sha256 = cache_key(self.configuration())
        if imported is not None:
            from . import import_metadata
            bound.check();self.inode=import_metadata.birth(self.root)
            import_metadata.write(self.root,'owner.json',self.start)
        else:
            bound.check(); self.root.mkdir()
            parent, fd = io._open(self.root.parent)
            try: os.fsync(fd); io._root(parent, fd)
            finally: io._release(lambda: os.close(fd))
            root, fd = io._open(self.root)
            try:
                self.inode = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
                io._write(fd, 'owner.json', self.start); io._root(root, fd)
            finally: io._release(lambda: os.close(fd))
        self.lease()

    def configuration(self):
        return {'maximum': self.maximum, 'required': self.required, 'policy': thaw(self.policy),
            'matching': thaw(self.matching), 'root': str(self.root), 'identity': self.identity,
            'owner_bytes': io._hash(self.start)}

    def binding_value(self):
        return {'record': thaw(self.bound.record), 'context': thaw(self.bound.context),
            'limits': thaw(self.bound.limits), 'run_directory': str(self.bound._run.directory),
            'run_claim_sha256': self.bound._run._claim_sha256,
            'metadata_snapshots': {str(path): value for path,value in self.bound._snapshots.items()}}

    def check_binding(self):
        require(self.bound is self._bound and self.bound._run is self._run,
                'compact binding or run object replaced')
        require(cache_key(self.binding_value()) == self._binding_sha256, 'compact binding authority changed')

    def select_binding_timing(self,selection):
        require(type(self) is Owner and matching_owner.binding_timing_policy(selection) is not None,'actual selected owner timing required')
        if not hasattr(self,'_binding_timing_pin'):
            self._binding_timing=matching_owner.BindingLeaseTiming(self.bound)
            self._binding_timing_pin=self._binding_timing
        require(self._binding_timing is self._binding_timing_pin,'selected binding observer changed')
        self._binding_timing._check(self.bound)
        return self._binding_timing

    def lease(self):
        require(not self.poisoned and not self.closed, 'compact owner is terminal or poisoned')
        self.check_binding()
        require(cache_key(self.configuration()) == self.configuration_sha256
            and self.reserved == self._reserved, 'compact owner runtime contract changed')
        journal = Path(self.bound.record['journal_directory'])
        require(not any(present(journal / name) for name in ('failed.json', 'complete.json')),
                'representation terminal marker exists')
        if not hasattr(self,'_binding_timing_pin'):
            self.bound.lease()
        else:
            observer=self._binding_timing
            require(observer is self._binding_timing_pin and type(observer) is matching_owner.BindingLeaseTiming,'selected binding observer changed')
            observer._check(self.bound)
            self.bound.lease(observer=observer)
        self.check_binding()
        info = self.root.lstat()
        require((info.st_dev, info.st_ino) == self.inode, 'compact owner directory changed')
        if self.required[0]=='dictionary-import':
            from .import_metadata import exact as import_exact
            import_exact(self.root,'owner.json',self.start)
        else:exact(self.root, 'owner.json', self.start)
        require(not present(self.root / 'failed.json') and
            (self.closing or not present(self.root / 'complete.json')), 'compact owner terminal marker exists')

    def boundary(self):
        self.check_binding()
        self.bound.check(); self.lease()
        allowed = {'owner.json'} | set(self.stages)
        if self.closing: allowed.add('complete.json')
        entries(self.root, allowed, required={'owner.json'} | set(self.stages),_imported=self.required[0]=='dictionary-import')
        total = OWNER_BYTES
        for name, stage in self.stages.items():
            require(name == stage.name and stage.owner is self, 'compact stage membership changed')
            stage.integrity()
            if stage.kind!='dictionary-import':exact(stage.root, 'intent.json', stage.intent)
            total += stage.reservation
        require(total == self.reserved <= self.maximum, 'compact workflow cumulative reservation differs')

    @transition
    def begin(self, name, *, workload_sha256, pairs):
        """Existing exact-count contract; never relaxed during completion."""
        return self._begin(name, workload_sha256, pairs, None)

    def _dictionary_count_policy(self):
        run = self.bound._run; record = self.bound.record
        selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][record['representation']]
        item = json.loads(run.read_input(selected['plan_input']))['producers'][record['producer']]
        require(selected.get('compact_dictionary_count_policy') == item.get('compact_dictionary_count_policy')
            == DICTIONARY_COUNT_POLICY, 'explicit dictionary count policy differs')
        settings = selected['descriptor']['configs'].get('dictionary')
        require(type(settings) is dict, 'registered dictionary configuration required')
        fields = ('sample_count', 'size', 'partition_threshold', 'partition_size')
        require(all(k in settings for k in fields), 'dictionary capacity configuration incomplete')
        capacity = compact_policy.dictionary_capacity(**{k: settings[k] for k in fields})
        return {'name': DICTIONARY_COUNT_POLICY, 'dictionary_config_sha256': cache_key(settings),
                'capacity': capacity}

    @transition
    def begin_dictionary(self, *, workload_sha256):
        """Reserve the registered upper bound; producer later supplies actual count.

        Identical ordered subsets may share complete distance matrices. Capacity
        is not an expected completion denominator or proof of scientific work.
        """
        self.boundary(); policy = self._dictionary_count_policy()
        return self._begin('dictionary', workload_sha256, policy['capacity']['max_pairs'], policy)

    def _begin(self, name, workload_sha256, pairs, count_policy, *, retention_selection=None):
        self.boundary()
        require(self.active is None and name in self.required and name not in self.stages,
                'compact stage absent, active or already claimed')
        prerequisite=self.required[0]
        require(name!='dictionary-import','use actual imported stage constructor')
        require(name == 'dictionary' or (prerequisite in self.stages and self.stages[prerequisite].closed),
                'dictionary/import must complete before MCM stage')
        io._identity(workload_sha256)
        kind = 'dictionary' if name == 'dictionary' else 'mcm'
        require(('restart_retention' in self.policy)==(retention_selection is not None),
            'stage retention selector requires explicit policy')
        if retention_selection is not None:
            from .stage_retention import _selection
            _selection(retention_selection)
            require(retention_selection['kind']==kind and getattr(self,'_archive_operations',None) is not None,
                'retention stage requires archived owner authority')
        reservation = compact_policy.validate(thaw(self.policy), kind=kind, pairs=pairs)['logical_reservation_bytes'] + STAGE_BYTES
        require(self.reserved + reservation <= self.maximum, 'compact workflow reservation exhausted')
        scope = compact_matcher.scope(thaw(self.matching), thaw(self.bound.context), thaw(self.policy['pair']),
            workload_sha256, thaw(self.policy['schedule']))
        try:
            stage = Stage(self, name, scope, pairs, reservation, count_policy, retention_selection)
            self.stages[name] = stage; self.active = stage
            self.reserved += reservation; self._reserved = self.reserved
            stage.lease(); return stage
        except BaseException:
            self.poisoned = True; raise

    @transition
    def finish_stage(self, stage, *, log_terminal_sha256, stream_terminal_sha256, completed_pairs=None):
        return self._finish_stage(stage, log_terminal_sha256=log_terminal_sha256,
            stream_terminal_sha256=stream_terminal_sha256, completed_pairs=completed_pairs)

    def _finish_stage(self, stage, *, log_terminal_sha256, stream_terminal_sha256, completed_pairs=None):
        """Internal transition; caller holds _transition for the whole producer."""
        self.boundary()
        require(self.active is stage and self.stages.get(stage.name) is stage and not stage.closed,
                'actual active compact stage required')
        stage.lease()
        if stage.count_policy is None:
            require(completed_pairs is None, 'exact stage denominator cannot be overridden')
            count = stage.pairs
        else:
            require(type(completed_pairs) is int and 0 <= completed_pairs <= stage.pairs,
                    'explicit bounded dictionary completion count required')
            count = completed_pairs
        contract = {'owner': self.identity, 'scope': thaw(stage.scope), 'policy': thaw(self.policy),
            'kind': stage.kind, 'pairs': count, 'log_terminal_sha256': log_terminal_sha256,
            'stream_terminal_sha256': stream_terminal_sha256}
        try:
            self._stage_bindings(stage)
            stage.closing = True
            ref = compact_stage.seal(stage.root, lease=stage.lease, **contract)
            stage.lease()
            compact_stage.verify(stage.root, expected_sha256=ref, lease=lambda: None, **contract)
            stage.reference = ref; stage.contract = freeze(contract); stage.closed = True
            self.active = None; return ref
        except BaseException:
            self.poisoned = True; raise

    def _stage_bindings(self, stage):
        if stage.contract is not None and 'batched' in stage.contract:
            _stage_content(stage);return
        if stage.kind=='dictionary-import':
            _stage_content(stage);return
        if stage.count_policy is not None:
            require(stage.kind == 'dictionary' and thaw(stage.count_policy) == self._dictionary_count_policy()
                and stage.pairs == stage.count_policy['capacity']['max_pairs'],
                'dictionary capacity differs from registered count policy')
        if stage.contract is not None:
            count = stage.contract['pairs']
            require(type(count) is int and (count == stage.pairs if stage.count_policy is None
                else 0 <= count <= stage.pairs), 'completed stage denominator differs')
        start, _ = compact_stage.read(stage.root / 'matching', 'start.json')
        require(type(start['max_iterations']) is int and start['max_iterations'] == self.matching['max_iterations'],
                'compact log iteration limit differs from registered matching config')
        if stage.kind == 'mcm':
            stream_start, _ = compact_stage.read(stage.root / 'stream', 'start.json')
            require(stream_start['scope']['graph'] == stage.name[4:], 'compact MCM required graph differs')

    def _verified_stages(self):
        digest = hashlib.sha256(); count = pairs = 0
        for name in self.required:
            stage = self.stages[name]
            if stage.kind=='dictionary-import':
                result=_stage_content(stage)
                digest.update(body({'stage':name,'receipt_sha256':stage.reference}));count+=1
                require(result['completed_pairs']==0,'import cannot credit historical pairs')
                continue
            self._stage_bindings(stage)
            exact(stage.root, 'intent.json', stage.intent)
            entries(stage.root, {'intent.json', 'matching', 'checkpoints', 'stage-complete.json'} |
                ({'stream'} if stage.kind == 'mcm' else set()), required={'intent.json', 'matching', 'checkpoints', 'stage-complete.json'})
            result = _stage_content(stage)
            digest.update(body({'stage': name, 'receipt_sha256': stage.reference}))
            count += 1; pairs += result['completed_pairs']
        return {'stages': count, 'pairs': pairs, 'stage_receipts_sha256': digest.hexdigest()}

    @transition
    def finish(self):
        return self._finish()

    def _finish(self):
        """Finish while the caller holds this owner's transition lock."""
        self.boundary()
        require(self.active is None and set(self.stages) == set(self.required)
            and all(s.closed for s in self.stages.values()), 'compact required stages incomplete')
        try:
            result = {'schema_version': 1, 'owner': self.identity, **self._verified_stages(),
                'reserved_logical_bytes': self.reserved, 'representation_admitted': False}
            raw = body(result); self.closing = True
            self.lease(); require(self._verified_stages() == {k: result[k] for k in ('stages', 'pairs', 'stage_receipts_sha256')},
                                  'compact stages changed before closure')
            if self.required[0]=='dictionary-import':
                from . import import_metadata
                ref=import_metadata.write(self.root,'complete.json',raw)
            else:
                root, fd = io._open(self.root)
                try: ref = io._write(fd, 'complete.json', raw); io._root(root, fd)
                finally: io._release(lambda: os.close(fd))
            self.boundary()
            require(self._verified_stages() == {k: result[k] for k in ('stages', 'pairs', 'stage_receipts_sha256')},
                    'compact stages changed during closure')
            if self.required[0]=='dictionary-import':import_metadata.exact(self.root,'complete.json',raw)
            else:exact(self.root, 'complete.json', raw)
            ledger = getattr(self, '_archive_operations', None)
            if ledger is not None:
                require(ledger.owner is self and not ledger._closed and not ledger._poisoned
                    and ledger._active is None, 'archive ledger cannot close successfully')
                ledger._evidence(); ledger._close(); ledger._evidence()
            self.closed = True; return ref
        except BaseException:
            self.poisoned = True; raise


def verify_current(owner, *, sampled_archive_evidence=False):
    """Callback-free final rejoin after an already successful live guard lease.

    Checks current claim, binding metadata and exact compact owner state. Does
    not invoke user/owner/guard callbacks or replace the preceding live resource
    guard. Boundaries remain sampled, not an atomic filesystem snapshot.
    """
    require(type(owner) is Owner,'actual compact Owner required')
    require(not owner.poisoned and not owner.closed and not owner.closing,
        'compact owner is terminal, closing or poisoned')
    owner.check_binding()
    require(cache_key(owner.configuration()) == owner.configuration_sha256
        and owner.reserved == owner._reserved,'compact owner runtime contract changed')
    owner.bound._run._active()
    require(not any(present(owner.bound._run.directory/name) for name in ('complete.json','failed.json')),
        'current run terminal marker exists')
    journal = Path(owner.bound.record['journal_directory'])
    require(owner.bound._ancestry_arguments is None,'fresh compact owner required')
    entries(journal.parent,{journal.name},required={journal.name},_imported=owner.required[0]=='dictionary-import')
    ledger=getattr(owner,'_archive_operations',None)
    if ledger is not None:
        from . import archive_owner_operations
        require(type(ledger) is archive_owner_operations.Ledger and ledger.owner is owner
            and ledger.selection._owner is owner and ledger._transition is owner._transition
            and ledger.root==journal/'archive-operations' and not ledger._closed and not ledger._poisoned,
            'current original attached archive ledger differs')
        # Ledger lives INSIDE journal, beside compact. The parent inventory above
        # is unchanged; only the genuine exact attached ledger is joined here.
        if sampled_archive_evidence is True and ledger._history is not None and not hasattr(ledger,'_typed_expected'):
            # Only the explicit hot lease may sample registered closed history.
            # Keep the ledger directory's canonical identity current on every call.
            root,fd = io._open(ledger.root)
            try:
                require(io._signature(os.fstat(fd))[:2] == ledger._inode,
                    'archive reservation directory changed')
                io._root(root,fd)
            finally:archive_owner_operations._close_descriptor(fd)
            ledger._evidence(sampled=True)
        else:ledger._evidence()
    require(not any(present(journal/name) for name in ('failed.json','complete.json')),
        'representation terminal marker exists')
    reader=matching_owner.metadata
    if owner.bound.record.get('resource_only') is True:
        from .import_metadata import metadata as reader
    for path,expected in owner.bound._snapshots.items():
        require(reader(path,owner.bound._run.admission.root)[1] == expected,
            'compact binding metadata changed')
    require(owner.root == journal/'compact' and owner.root.resolve() == owner.root,'compact owner root redirected')
    require(owner.root.stat().st_dev == owner.bound._run.admission.root.stat().st_dev,'compact owner device changed')
    info = owner.root.lstat()
    require((info.st_dev,info.st_ino) == owner.inode,'compact owner directory changed')
    if owner.required[0]=='dictionary-import':
        from .import_metadata import exact as import_exact
        import_exact(owner.root,'owner.json',owner.start)
    else:exact(owner.root,'owner.json',owner.start)
    expected = {'owner.json'} | set(owner.stages)
    entries(owner.root,expected,required=expected,_imported=owner.required[0]=='dictionary-import')
    total = OWNER_BYTES
    for name,stage in owner.stages.items():
        require(name == stage.name and stage.owner is owner,'compact stage membership changed')
        stage.integrity()
        if stage.kind!='dictionary-import':exact(stage.root,'intent.json',stage.intent)
        total += stage.reservation
    require(total == owner.reserved <= owner.maximum,'compact cumulative reservation differs')


def attach(bound, *, policy_input):
    require(type(bound) is matching_owner.Binding and bound._ancestry_arguments is None,
            'actual fresh matching owner Binding required')
    bound.check(); run = bound._run
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound.record['representation']]
    plan = json.loads(run.read_input(selected['plan_input']))
    item = plan['producers'][bound.record['producer']]
    for value in (selected, item):
        require(value.get('native_backend') == compact_policy.BACKEND
            and value.get('compact_policy_input') == policy_input, 'explicit registered compact selection differs')
    descriptor = selected['descriptor']
    require(canonical_bytes(item['descriptor']) == canonical_bytes(descriptor)
        and cache_key(descriptor) == bound.record['workflow_identity'], 'compact descriptor differs from owner')
    require(descriptor.get('compact_execution') == {'backend': compact_policy.BACKEND,
        'policy_sha256': run.admission.inputs[policy_input]['sha256']}, 'compact descriptor policy differs')
    envelope = json.loads(run.read_input(policy_input))
    require(set(envelope) == {'schema_version', 'backend', 'stage_policy', 'max_workflow_retained_logical_bytes'}
        and type(envelope['schema_version']) is int and envelope['schema_version'] == 1
        and envelope['backend'] == compact_policy.BACKEND, 'compact owner policy schema')
    compact_policy.positive((envelope['max_workflow_retained_logical_bytes'],))
    compact_policy.validate(envelope['stage_policy'], kind='dictionary', pairs=0)
    require(canonical_bytes(envelope['stage_policy']['pair']) == canonical_bytes(thaw(bound.limits)),
            'compact pair policy differs from registered numerical owner')
    require(type(descriptor.get('configs', {}).get('matching')) is dict, 'compact matching configuration required')
    from .compact_training import _retention_extension
    _retention_extension(run,selected,item)
    return Owner(bound, policy_input, envelope, descriptor)

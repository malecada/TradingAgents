"""Fresh-owner scalar matcher with compact completion evidence.

Numerical create/advance/score_only/close are unchanged. A prospective schedule
groups bounded advance calls before saving a progress checkpoint; this changes
checkpoint cadence and requires explicit registration before empirical use.
Stable ranking can still occur inside advance; operation counts are not a bound
on sorting time, scratch or RSS. An outer process/storage guard is mandatory.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
from weakref import WeakKeyDictionary

from . import matching_pair as pair, score_batches as io
from .compact_pair_log import PairLog, FRAME, RECORD_BYTES, ZERO
from .cache import cache_key
from .matching_identity import graph_identity

require = io._require
from . import matching_checkpoint as engine, compact_policy
_RETENTION = WeakKeyDictionary()
_CAPACITY_PINS = WeakKeyDictionary()


class CheckpointStop(RuntimeError):
    """Progress is retained; this consumer is poisoned, never self-resumed."""


class CleanupFailure(BaseException):
    """Fatal to the worker; cannot become an ordinary unavailable cell."""


def _components(checkpoint_layout=None, policy=None):
    modules = (engine, engine.ann, engine.hard, engine.sparse, engine.ann.typed_identity, engine.chunks)
    if policy is not None and compact_policy.PAIR_CAPACITY_FIELD in policy:
        modules += (compact_policy,)
    return {Path(m.__file__).name + ':' + Path(m.__file__).parent.name:
        hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules}


def scope(config, context, policy, workload_sha256, schedule, *, checkpoint_layout=None):
    compact_policy.effective_matching(config, policy)
    checkpoint_layout=policy.get('checkpoint_layout',checkpoint_layout)
    if checkpoint_layout is not None:checkpoint_layout=engine.chunks.layout(checkpoint_layout)
    return {'workflow': workload_sha256, 'config': cache_key(config),
        'context': cache_key(context), 'policy': cache_key({'pair': policy, 'schedule': schedule}),
        'numerical_source': cache_key(_components(checkpoint_layout, policy))}


def _file(path, size, expected):
    """Hash a bounded saved file with 64KiB reads, no numeric array allocation."""
    io._identity(expected)
    require(type(size) is int and size >= 0 and path.resolve() == path, 'checkpoint file extent/path')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size == size,
                'checkpoint regular extent differs')
        digest = hashlib.sha256(); remaining = size
        while remaining:
            block = os.read(fd, min(65536, remaining))
            require(bool(block), 'checkpoint truncated'); digest.update(block); remaining -= len(block)
        require(digest.hexdigest() == expected and io._signature(before) == io._signature(os.fstat(fd))
            == io._signature(path.lstat()), 'checkpoint content/identity differs')
    finally: io._release(lambda: os.close(fd))


def _snapshot(directory, state_sha, identity, policy, *, checkpoint_layout=None):
    checkpoint_layout=policy.get('checkpoint_layout',checkpoint_layout)
    if checkpoint_layout is not None:return _sharded_snapshot(directory,state_sha,identity,policy,checkpoint_layout)
    """Validate engine-generated hash tree and fixed inventory without loading arrays."""
    root, fd = io._open(directory)
    try:
        def metadata(relative, expected):
            path = directory / relative
            require(path.resolve() == path, 'checkpoint metadata redirected')
            parent, child_fd = io._open(path.parent)
            try: raw = io._read(child_fd, path.name, pair.LIMIT)
            finally: io._release(lambda: os.close(child_fd))
            require(io._hash(raw) == expected, 'checkpoint metadata hash differs')
            return json.loads(raw), len(raw)
        meta, total = metadata('manifest.json', state_sha)
        require(set(meta) == engine.MANIFEST_FIELDS and meta['version'] == 3
            and meta['policy'] == {k: policy[k] for k in pair.ENGINE_FIELDS}, 'checkpoint policy/schema')
        anneal, size = metadata('annealing/manifest.json', meta['annealing_sha256']); total += size
        require(anneal['identity'] == identity['ordered_pair'] and anneal['safe'] is True
            and anneal['max_chunk_entries'] == policy['normalization_chunk_entries']
            and set(anneal['files']) == {'M', 'Q', 'V'}, 'checkpoint annealing identity differs')
        n, m = anneal['shape']
        require(type(n) is int and type(m) is int and n > 0 and m > 0
            and 32*n*m <= policy['max_state_bytes'], 'checkpoint matrix capacity')
        files = {'manifest.json', 'annealing/manifest.json'}; directories = {'.', 'annealing'}
        for name, item in anneal['files'].items():
            require(item['bytes'] == 8*n*m + 128, 'checkpoint array extent')
            relative = 'annealing/' + name + '.npy'
            _file(directory / relative, item['bytes'], item['sha256'])
            files.add(relative); total += item['bytes']
        if meta['hardening_sha256'] is not None:
            hard, size = metadata('hardening/manifest.json', meta['hardening_sha256']); total += size
            require(hard['shape'] == [n, m] and hard['safe'] is True
                and hard['input_sha256'] == meta['matrix_sha256']
                and hard['max_explicit_bytes'] == policy['hardening_buffer_bytes']
                and hard['order_bytes'] == 8*n*m + 128, 'checkpoint hardening identity differs')
            _file(directory / 'hardening/order.npy', hard['order_bytes'], hard['order_sha256'])
            total += hard['order_bytes']; files.update({'hardening/manifest.json', 'hardening/order.npy'})
            directories.add('hardening')
        pending = [directory]; seen_files = set(); seen_dirs = set(); count = 0
        while pending:
            current = pending.pop(); seen_dirs.add(str(current.relative_to(directory)))
            with os.scandir(current) as entries:
                for entry in entries:
                    count += 1; require(count <= 11, 'checkpoint inventory bound')
                    info = entry.stat(follow_symlinks=False)
                    require(info.st_dev == os.fstat(fd).st_dev, 'checkpoint crossed device')
                    relative = str(Path(entry.path).relative_to(directory))
                    if stat.S_ISDIR(info.st_mode):
                        require(relative in directories, 'foreign checkpoint directory'); pending.append(Path(entry.path))
                    else:
                        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                            and relative in files, 'foreign checkpoint file'); seen_files.add(relative)
        require(seen_dirs == directories and seen_files == files and total <= policy['max_checkpoint_bytes'],
                'checkpoint inventory/logical bound differs')
        io._root(root, fd)
        return total
    finally: io._release(lambda: os.close(fd))


class CompactMatcher:
    def __init__(self, log, *, config, context, policy, workload_sha256, schedule, lease, retention=None, durability_barrier=None, checkpoint_layout=None, diagnostic=None):
        require(isinstance(log, PairLog) and log.events == 0 and log.state['pending'] is None,
                'fresh compact log required')
        require(callable(lease), 'live compact matcher lease required')
        require(set(context) == {'namespace', 'source_commit', 'runtime_hash'}, 'numerical context schema')
        for key, value in context.items(): pair.hash_string(value, 40 if key == 'source_commit' else 64)
        pair.hash_string(workload_sha256)
        require(set(schedule) == {'operations_per_call', 'calls_per_checkpoint', 'max_checkpoints',
            'max_total_checkpoints', 'max_total_checkpoint_bytes'}
            and all(type(v) is int and 0 < v < 2**63 for v in schedule.values()), 'compact execution schedule')
        compact_policy.pair_policy(policy)
        effective = compact_policy.effective_matching(config, policy)
        require(schedule['max_checkpoints'] <= policy['max_publications'], 'checkpoint count exceeds pair policy')
        require(pair.LIMIT + schedule['max_checkpoints'] * (policy['max_checkpoint_bytes'] + pair.LIMIT)
            <= policy['total_checkpoint_bytes'], 'per-pair cumulative checkpoint budget insufficient')
        require(checkpoint_layout is None or checkpoint_layout==policy.get('checkpoint_layout'),'layout must be bound into pair policy')
        checkpoint_layout=policy.get('checkpoint_layout')
        if checkpoint_layout is not None:checkpoint_layout=engine.chunks.layout(checkpoint_layout)
        require(log.start['scope'] == scope(config, context, policy, workload_sha256, schedule,checkpoint_layout=checkpoint_layout)
            and log.start['max_iterations'] == config['max_iterations'], 'compact log execution scope differs')
        require(durability_barrier is None or callable(durability_barrier), "optional coupled durability barrier")
        if diagnostic is not None:
            from .real_pilot_partial_progress import ScoringDiagnostic
            require(type(diagnostic) is ScoringDiagnostic,'exact registered scoring diagnostic required')
        self._diagnostic = diagnostic
        self._durability_barrier = durability_barrier
        self.log = log; self.config = effective; self.context = copy.deepcopy(context)
        if compact_policy.PAIR_CAPACITY_FIELD in policy:
            self.original_config = copy.deepcopy(config)
            _CAPACITY_PINS[self] = (cache_key(config), cache_key(effective),
                cache_key({'pair': policy, 'schedule': schedule}))
        self.policy = copy.deepcopy(policy); self.schedule = copy.deepcopy(schedule)
        self.checkpoint_layout=copy.deepcopy(checkpoint_layout);self._checkpoint_layout_pin=cache_key(checkpoint_layout)
        self.components = _components(checkpoint_layout, policy); self.workload = workload_sha256; self.lease = lease
        self.busy = self.poisoned = False
        self.checkpoints = self.reserved_bytes = 0
        self.root = log.root.parent / 'checkpoints'
        self.lease(); self.root.mkdir()
        parent, fd = io._open(self.root.parent)
        try: os.fsync(fd); io._root(parent, fd)
        finally: os.close(fd)
        info = self.root.lstat(); self.root_identity = (info.st_dev, info.st_ino)
        self.retention = None
        if retention is not None:
            from .stage_retention import Controller
            self.retention = Controller(self, **retention)
            _RETENTION[self] = self.retention

    def _timed(self, phase, function, *args, **kwargs):
        if self._diagnostic is None:return function(*args, **kwargs)
        return self._diagnostic.measure(phase,function,*args,**kwargs)

    def pair_identity(self, a, b):
        return {'ordered_pair': engine.ann.identity(a, b, self.config), 'context': self.context,
                'backend': pair.BACKEND.copy(), 'numerical_components': self.components}

    def _check(self):
        require(cache_key(self.checkpoint_layout)==self._checkpoint_layout_pin,'checkpoint layout changed')
        self.lease(); self.log._check()
        if self in _CAPACITY_PINS:
            require((cache_key(self.original_config), cache_key(self.config),
                cache_key({'pair': self.policy, 'schedule': self.schedule})) == _CAPACITY_PINS[self],
                'original/effective matching resource policy changed')
        if self in _RETENTION:
            require(self.retention is _RETENTION[self] and self.retention.matcher is self,
                'original matcher retention route changed')
        require(io._hash(io._json(self.log.start)) == self.log.start_sha, 'in-memory log contract changed')
        info = self.root.lstat()
        require(self.root.resolve() == self.root and stat.S_ISDIR(info.st_mode)
                and (info.st_dev, info.st_ino) == self.root_identity, 'checkpoint root changed')

    def _expected_event(self, kind, *, purpose=None, identity=None, score=0., iterations=0, artifact=ZERO):
        pending = self.log.state['pending']
        ordinal = self.log.state['started_pairs'] if kind == 0 else pending['ordinal']
        if kind != 0:
            purpose = pending['purpose_sha256']; identity = pending['identity_sha256']
        frame = FRAME.pack(self.log.events, kind, ordinal, score, iterations, bytes.fromhex(purpose),
                           bytes.fromhex(identity), bytes.fromhex(artifact))
        head = io._hash(bytes.fromhex(self.log.head) + frame)
        return self.log.events, head, frame + bytes.fromhex(head)

    def _ack_check(self, expected):
        """Actual fixed-record byte acknowledgement; selected durability is separate."""
        event, head, raw = expected
        require(self.log.events == event + 1 and self.log.head == head, 'log acknowledged another event')
        io._root(self.log.root, self.log.fd)
        require(io._hash(io._read(self.log.fd, 'start.json', io.META_LIMIT)) == self.log.start_sha,
                'log start changed before numerical acknowledgement')
        chunk, slot = divmod(event, self.log.start['limits']['chunk_events'])
        name = f'events-{chunk:012d}.bin'
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.log.fd)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and info.st_size == (slot + 1) * RECORD_BYTES
                and os.pread(fd, RECORD_BYTES, slot * RECORD_BYTES) == raw
                and io._signature(info) == io._signature(os.fstat(fd))
                    == io._signature(os.stat(name, dir_fd=self.log.fd, follow_symlinks=False)),
                'log event bytes/identity changed before acknowledgement')
        finally: os.close(fd)

    def _save(self, state, a, b, identity, purpose):
        self._check()
        self.log.durability_barrier()
        if self._durability_barrier is not None:self._durability_barrier()
        if self.retention is not None:
            result = self.retention.checkpoint(state,a,b,identity,purpose)
            self.checkpoints += 1
            return result
        reserved = self.policy['max_checkpoint_bytes'] + 2 * io.META_LIMIT
        require(self.checkpoints < self.schedule['max_total_checkpoints']
            and self.reserved_bytes + reserved <= self.schedule['max_total_checkpoint_bytes'],
            'cumulative checkpoint reservation exhausted')
        self.checkpoints += 1; self.reserved_bytes += reserved
        directory = self.log.checkpoint_path(); directory.mkdir()
        parent, fd = io._open(directory.parent)
        try: os.fsync(fd)
        finally: os.close(fd)
        root, fd = io._open(directory)
        try:
            intent = {'schema_version': 1, 'log_start_sha256': self.log.start_sha,
                'event': self.log.events, 'pair': dict(self.log.state['pending']),
                'identity': identity, 'purpose': purpose, 'policy': self.policy,
                'reserved_bytes': reserved, 'cumulative_reserved_bytes': self.reserved_bytes,
                'cumulative_checkpoints': self.checkpoints}
            intent_sha = io._write(fd, 'intent.json', io._json(intent))
            self._check()
            state_sha = engine.save(state, directory / 'state', a, b, self.config,
                                    max_checkpoint_bytes=self.policy['max_checkpoint_bytes'],**({'checkpoint_layout':self.checkpoint_layout} if self.checkpoint_layout is not None else {}))
            self._check(); total = _snapshot(directory / 'state', state_sha, identity, self.policy,checkpoint_layout=self.checkpoint_layout)
            meta = {'schema_version': 1, 'intent_sha256': intent_sha, 'state_sha256': state_sha,
                    'state_logical_bytes': total, 'reserved_bytes': reserved}
            result = io._write(fd, 'manifest.json', io._json(meta))
            self._check()
            require(io._hash(io._read(fd, 'intent.json', io.META_LIMIT)) == intent_sha
                and io._hash(io._read(fd, 'manifest.json', io.META_LIMIT)) == result,
                'checkpoint publication metadata changed')
            _snapshot(directory / 'state', state_sha, identity, self.policy,checkpoint_layout=self.checkpoint_layout)
            io._root(root, fd)
            expected = self._expected_event(3, artifact=result)
            self._timed('event_publication',self.log.progress,result)
            self.log.durability_barrier()
            self._check()
            require(io._hash(io._read(fd, 'intent.json', io.META_LIMIT)) == intent_sha
                and io._hash(io._read(fd, 'manifest.json', io.META_LIMIT)) == result,
                'checkpoint changed during progress event publication')
            _snapshot(directory / 'state', state_sha, identity, self.policy,checkpoint_layout=self.checkpoint_layout)
            io._root(root, fd)
            self._ack_check(expected)
        finally: os.close(fd)

    def __call__(self, purpose, a, b):
        require(not self.busy and not self.poisoned, 'compact matcher busy or poisoned')
        self.busy = True; state = None; primary = None
        try:
            self._check(); purpose = copy.deepcopy(purpose)
            require(purpose.get('schema_version') == 1 and purpose.get('kind') in ('mcm', 'dictionary')
                and purpose.get('workload_sha256') == self.workload
                and purpose.get('typed_graphs') == [graph_identity(a), graph_identity(b)], 'compact matcher purpose differs')
            self._timed('pair_validation',pair.policy_check,a, b, self.config, compact_policy.pair_policy(self.policy), allow_checkpoint_layout=True)
            require(self.log.events + 2 + self.schedule['max_checkpoints'] <= self.log.start['limits']['max_events'],
                    'insufficient completion/progress event capacity')
            reserved = self.policy['max_checkpoint_bytes'] + 2 * io.META_LIMIT
            require(self.checkpoints + self.schedule['max_checkpoints'] <= self.schedule['max_total_checkpoints']
                and self.reserved_bytes + self.schedule['max_checkpoints'] * reserved
                    <= self.schedule['max_total_checkpoint_bytes'],
                'insufficient cumulative checkpoint capacity before allocation')
            if self.retention is not None:self.retention.before_pair()
            identity = self.pair_identity(a, b)
            expected = self._expected_event(0, purpose=cache_key(purpose), identity=pair.digest(identity))
            self._timed('event_publication',self.log.begin,cache_key(purpose),pair.digest(identity))
            self._check()
            self._ack_check(expected)
            if self.retention is not None:
                self.log.durability_barrier()
                self.retention.begin(purpose,a,b,identity,expected)
            state = self._timed('state_create',engine.create,a, b, self.config, **{k: self.policy[k] for k in pair.ENGINE_FIELDS})
            for _ in range(self.schedule['max_checkpoints']):
                for _ in range(self.schedule['calls_per_checkpoint']):
                    self._check()
                    self._timed('advance_hardening' if state['phase']=='hardening' else 'advance_annealing_including_rank_transition',engine.advance,state, a, b, self.config, max_operations=self.schedule['operations_per_call'])
                    if state['phase'] == 'done': break
                if state['phase'] == 'done':
                    self._check()
                    result = self._timed('score_only',engine.score_only,state, a, b, self.config,
                        max_buffer_bytes=self.policy['max_score_buffer_bytes'], chunk_edges=self.policy['chunk_edges'])
                    try: engine.close(state)
                    except BaseException as failure:
                        raise CleanupFailure('ranked matcher cleanup unresolved; worker must stop') from failure
                    finally: state = None
                    self._check()
                    expected = self._expected_event(1 if result.convergence == 'temperature_complete' else 2,
                        score=float(result.score), iterations=result.iterations)
                    answer = self._timed('event_publication',self.log.complete,float(result.score),result.convergence,result.iterations)
                    self._check(); self._ack_check(expected)
                    if self.retention is not None:
                        self.log.durability_barrier()
                        self.retention.complete(expected,float(result.score),result.iterations,result.convergence)
                    if self._diagnostic is not None:self._diagnostic.completed_pair(self.log)
                    return answer
                self._save(state, a, b, identity, purpose)
            raise CheckpointStop('bounded calls exhausted; checkpoint retained for separately admitted successor')
        except BaseException as error:
            primary = error; self.poisoned = True
            for flush in [self.log.durability_barrier] + ([self._durability_barrier] if self._durability_barrier is not None else []):
                try:flush()
                except BaseException as durability_error:
                    error.add_note('Failure durability barrier refused: '+repr(durability_error))
            retained=_RETENTION.get(self)
            if retained is not None:retained.fail(error)
            if any('cleanup also failed' in note.lower() for note in getattr(error, '__notes__', ())):
                raise CleanupFailure('engine construction/advance reported unresolved cleanup') from error
            raise
        finally:
            self.busy = False
            if state is not None:
                try: engine.close(state)
                except BaseException as error:
                    self.poisoned = True
                    fatal = CleanupFailure('ranked matcher cleanup unresolved; worker must stop')
                    if primary is not None: fatal.add_note('Primary failure: ' + repr(primary))
                    raise fatal from error


def _sharded_snapshot(directory,state_sha,identity,policy,selected):
    """Full saved-tree authentication; no dense array construction."""
    chunks=engine.chunks;selected=chunks.layout(selected);directory=Path(directory)
    root,fd=io._open(directory)
    try:
        meta=chunks.metadata(directory,state_sha)
        require(set(meta)==engine.MANIFEST_FIELDS|{'checkpoint_layout'} and type(meta['version']) is int and meta['version']==3
            and meta['checkpoint_layout']==selected and meta['policy']=={k:policy[k] for k in pair.ENGINE_FIELDS}
            and meta['phase'] in ('annealing','hardening','done'),'sharded checkpoint policy/schema')
        anneal=chunks.metadata(directory/'annealing',meta['annealing_sha256'])
        require(set(anneal)==engine.ann.META|{'files','checkpoint_layout'} and anneal['checkpoint_layout']==selected
            and anneal['identity']==identity['ordered_pair'] and anneal['safe'] is True
            and anneal['max_chunk_entries']==policy['normalization_chunk_entries'] and set(anneal['files'])=={'M','Q','V'},'sharded checkpoint annealing differs')
        n,m=anneal['shape'];require(type(n) is int and type(m) is int and n>0 and m>0 and 32*n*m<=policy['max_state_bytes'],'sharded checkpoint state capacity')
        total=len(chunks.read(directory/'manifest.json',chunks.LIMIT))+len(chunks.read(directory/'annealing/manifest.json',chunks.LIMIT))
        for name,descriptor in anneal['files'].items():total+=chunks.audit_array(directory/'annealing',descriptor,[n,m],'<f8',selected,name)
        chunks.inventory(directory/'annealing',{'manifest.json'}|chunks.array_names(anneal['files'].values()))
        expected={'manifest.json','annealing'}
        if meta['phase']=='annealing':require(meta['hardening_sha256'] is None and meta['matrix_sha256'] is None,'sharded premature hardening')
        else:
            hard=chunks.metadata(directory/'hardening',meta['hardening_sha256'])
            require(set(hard)==engine.hard.FIELDS-{'order'}|{'order_chunks','checkpoint_layout'} and hard['checkpoint_layout']==selected
                and hard['shape']==[n,m] and hard['safe'] is True and hard['input_sha256']==meta['matrix_sha256']
                and hard['max_explicit_bytes']==policy['hardening_buffer_bytes'],'sharded checkpoint hardening differs')
            total+=len(chunks.read(directory/'hardening/manifest.json',chunks.LIMIT))
            total+=chunks.audit_array(directory/'hardening',hard['order_chunks'],[n*m],'<i8',selected,'order')
            chunks.inventory(directory/'hardening',{'manifest.json'}|chunks.array_names([hard['order_chunks']]))
            expected.add('hardening')
        require({p.name for p in directory.iterdir()}==expected and total<=policy['max_checkpoint_bytes'],'sharded checkpoint inventory/logical bound')
        io._root(root,fd);return total
    finally:io._release(lambda:os.close(fd))

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
from pathlib import Path

from . import matching_owner, compact_policy, compact_matcher, compact_stage
from . import score_batches as io
from .cache import cache_key
from .provenance import canonical_bytes, freeze, thaw

require = io._require
LIMIT = 65536


def body(value):
    raw = canonical_bytes(value); require(len(raw) <= LIMIT, 'compact owner metadata capacity')
    return raw


def entries(root, allowed, *, required):
    path, fd = io._open(root)
    try:
        seen = set()
        with os.scandir(fd) as iterator:
            for entry in iterator:
                require(len(seen) < len(allowed) and entry.name in allowed, 'foreign compact owner inventory')
                seen.add(entry.name)
        require(required <= seen, 'missing compact owner inventory'); io._root(path, fd)
    finally: os.close(fd)


def exact(root, name, expected):
    path, fd = io._open(root)
    try:
        require(io._read(fd, name, LIMIT) == expected, 'compact owner metadata changed')
        io._root(path, fd)
    finally: os.close(fd)


class Stage:
    def __init__(self, owner, name, scope, pairs, reservation):
        self.owner = owner; self.name = name; self.root = owner.root / name
        self.scope = freeze(scope); self.pairs = pairs; self.reservation = reservation
        self.kind = 'dictionary' if name == 'dictionary' else 'mcm'
        self.closed = self.closing = False; self.reference = None; self.contract = None
        self.intent = body({'schema_version': 1, 'owner': owner.identity, 'stage': name,
            'kind': self.kind, 'scope': scope, 'pairs': pairs, 'logical_reservation_bytes': reservation,
            'policy_sha256': cache_key(thaw(owner.policy))})
        self.root.mkdir()
        parent, fd = io._open(owner.root)
        try: os.fsync(fd); io._root(parent, fd)
        finally: os.close(fd)
        root, fd = io._open(self.root)
        try:
            self.inode = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
            io._write(fd, 'intent.json', self.intent); io._root(root, fd)
        finally: os.close(fd)

    def lease(self):
        require(not self.closed, 'compact stage is terminal')
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
    def __init__(self, bound, policy_input, envelope, descriptor):
        self.bound = bound; self.policy = freeze(envelope['stage_policy'])
        self.maximum = envelope['max_workflow_retained_logical_bytes']
        self.matching = freeze(descriptor['configs']['matching'])
        self.required = ('dictionary',) + tuple('mcm-' + h for h in descriptor['required_graphs'])
        require(len(set(self.required)) == len(self.required), 'duplicate compact required stage')
        self.root = Path(bound.record['journal_directory']) / 'compact'
        self.active = None; self.stages = {}; self.reserved = 0
        self.poisoned = self.closed = self.closing = False
        record = {'schema_version': 1, 'backend': compact_policy.BACKEND, 'binding': thaw(bound.record),
            'context': thaw(bound.context), 'policy_input': policy_input,
            'policy_sha256': bound._run.admission.inputs[policy_input]['sha256'],
            'required_stages': list(self.required), 'maximum_retained_logical_bytes': self.maximum}
        self.identity = cache_key(record); self.start = body(record)
        bound.check(); self.root.mkdir()
        parent, fd = io._open(self.root.parent)
        try: os.fsync(fd); io._root(parent, fd)
        finally: os.close(fd)
        root, fd = io._open(self.root)
        try:
            self.inode = (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
            io._write(fd, 'owner.json', self.start); io._root(root, fd)
        finally: os.close(fd)
        self.lease()

    def lease(self):
        require(not self.poisoned and not self.closed, 'compact owner is terminal or poisoned')
        self.bound.lease()
        info = self.root.lstat()
        require((info.st_dev, info.st_ino) == self.inode, 'compact owner directory changed')
        exact(self.root, 'owner.json', self.start)
        require(not (self.root / 'failed.json').exists() and
            (self.closing or not (self.root / 'complete.json').exists()), 'compact owner terminal marker exists')

    def boundary(self):
        self.bound.check(); self.lease()
        allowed = {'owner.json'} | set(self.stages)
        if self.closing: allowed.add('complete.json')
        entries(self.root, allowed, required={'owner.json'} | set(self.stages))

    def begin(self, name, *, workload_sha256, pairs):
        self.bound.check(); self.bound.lease(); self.bound._run._active()
        self.boundary()
        require(self.active is None and name in self.required and name not in self.stages,
                'compact stage absent, active or already claimed')
        require(name == 'dictionary' or ('dictionary' in self.stages and self.stages['dictionary'].closed),
                'dictionary must complete before MCM stage')
        io._identity(workload_sha256)
        kind = 'dictionary' if name == 'dictionary' else 'mcm'
        reservation = compact_policy.validate(thaw(self.policy), kind=kind, pairs=pairs)['logical_reservation_bytes']
        require(self.reserved + reservation <= self.maximum, 'compact workflow reservation exhausted')
        scope = compact_matcher.scope(thaw(self.matching), thaw(self.bound.context), thaw(self.policy['pair']),
            workload_sha256, thaw(self.policy['schedule']))
        try:
            stage = Stage(self, name, scope, pairs, reservation)
            self.stages[name] = stage; self.active = stage; self.reserved += reservation
            stage.lease(); return stage
        except BaseException:
            self.poisoned = True; raise

    def finish_stage(self, stage, *, log_terminal_sha256, stream_terminal_sha256):
        self.boundary()
        require(self.active is stage and self.stages.get(stage.name) is stage and not stage.closed,
                'actual active compact stage required')
        stage.lease()
        contract = {'owner': self.identity, 'scope': thaw(stage.scope), 'policy': thaw(self.policy),
            'kind': stage.kind, 'pairs': stage.pairs, 'log_terminal_sha256': log_terminal_sha256,
            'stream_terminal_sha256': stream_terminal_sha256}
        try:
            stage.closing = True
            ref = compact_stage.seal(stage.root, lease=stage.lease, **contract)
            stage.lease()
            compact_stage.verify(stage.root, expected_sha256=ref, lease=lambda: None, **contract)
            stage.reference = ref; stage.contract = freeze(contract); stage.closed = True
            self.active = None; return ref
        except BaseException:
            self.poisoned = True; raise

    def _verified_stages(self):
        digest = __import__('hashlib').sha256(); count = pairs = 0
        for name in self.required:
            stage = self.stages[name]
            exact(stage.root, 'intent.json', stage.intent)
            entries(stage.root, {'intent.json', 'matching', 'checkpoints', 'stage-complete.json'} |
                ({'stream'} if stage.kind == 'mcm' else set()), required={'intent.json', 'matching', 'checkpoints', 'stage-complete.json'})
            result = compact_stage.verify(stage.root, expected_sha256=stage.reference,
                lease=lambda: None, **thaw(stage.contract))
            digest.update(body({'stage': name, 'receipt_sha256': stage.reference}))
            count += 1; pairs += result['completed_pairs']
        return {'stages': count, 'pairs': pairs, 'stage_receipts_sha256': digest.hexdigest()}

    def finish(self):
        self.boundary()
        require(self.active is None and set(self.stages) == set(self.required)
            and all(s.closed for s in self.stages.values()), 'compact required stages incomplete')
        try:
            result = {'schema_version': 1, 'owner': self.identity, **self._verified_stages(),
                'reserved_logical_bytes': self.reserved, 'representation_admitted': False}
            raw = body(result); self.closing = True
            self.lease(); require(self._verified_stages() == {k: result[k] for k in ('stages', 'pairs', 'stage_receipts_sha256')},
                                  'compact stages changed before closure')
            root, fd = io._open(self.root)
            try: ref = io._write(fd, 'complete.json', raw); io._root(root, fd)
            finally: os.close(fd)
            self.boundary()
            require(self._verified_stages() == {k: result[k] for k in ('stages', 'pairs', 'stage_receipts_sha256')},
                    'compact stages changed during closure')
            exact(self.root, 'complete.json', raw); self.closed = True; return ref
        except BaseException:
            self.poisoned = True; raise


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
    return Owner(bound, policy_input, envelope, descriptor)

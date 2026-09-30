"""Isolated ordered-pair artifact adapter; loading does not admit research.

The caller owns graphs exclusively, supplies trusted exact references, enforces
the process guard and admits any empirical owner/failed-parent relation outside
this layer. This adapter never discovers a latest checkpoint or reopens a name.
Production dictionary, MCM, journals, cache and registered policies are unchanged.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'pair_ranked_engine', HERE.with_name('matching-ranked-composite-2026-09-30')/'combined.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
LIMIT = 65536
ENGINE_FIELDS = {'max_state_bytes', 'normalization_chunk_entries',
                 'hardening_chunk_entries', 'hardening_buffer_bytes'}
POLICY_FIELDS = ENGINE_FIELDS | {'max_score_buffer_bytes', 'chunk_edges',
                                'max_checkpoint_bytes', 'max_publications',
                                'total_checkpoint_bytes'}
BACKEND = dict(name='scalar_ranked_reference', version=1, device='cpu',
               affinity='scalar_float64', normalization='scipy_float64',
               hardening='stable_descending_row_major', objective='sparse_scalar_float64',
               output='float64_score', checkpoint_schema=2)


def body(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(body(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def hash_string(value, size=64):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{'+str(size)+'}', value),
            'invalid hash identity')


def write(path, value):
    raw = body(value)
    require(len(raw) <= LIMIT, 'compact manifest allowance exceeded')
    with path.open('xb') as file:
        file.write(raw); file.flush(); os.fsync(file.fileno())
    engine.ann.sync(path.parent)
    return hashlib.sha256(raw).hexdigest()


def safe_root(root):
    root = Path(root).absolute()
    require(root.is_dir() and root.resolve() == root, 'existing nonsymlink artifact root required')
    return root


def safe_reference(root, reference):
    require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}, 'reference schema')
    hash_string(reference['sha256'])
    path = Path(reference['path'])
    require(path.is_absolute() and path.resolve() == path and path.is_relative_to(root)
            and path.name == 'manifest.json' and path.is_file(), 'reference containment')
    require(path.stat().st_size <= LIMIT, 'manifest read allowance exceeded')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'manifest hash differs')
    return path, json.loads(raw)


def identity(a, b, config, context):
    require(isinstance(context, dict) and set(context) == {'namespace', 'source_commit', 'runtime_hash'},
            'explicit workflow/source/runtime context required')
    for field, value in context.items():
        hash_string(value, 40 if field == 'source_commit' else 64)
    # Numerical component bytes are additional to the caller's registered source
    # and runtime closure. The latter must still be verified by admission.
    components = {Path(module.__file__).name + ':' + Path(module.__file__).parent.name:
                  hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                  for module in (engine, engine.ann, engine.hard, engine.sparse)}
    return dict(ordered_pair=engine.ann.identity(a, b, config), context=dict(context),
                backend=BACKEND.copy(), numerical_components=components)


def policy_check(a, b, config, policy):
    require(isinstance(policy, dict) and set(policy) == POLICY_FIELDS, 'pair policy schema')
    require(all(type(v) is int and v > 0 for v in policy.values()), 'positive integer policy required')
    engine.policy(len(a.node_ids), len(b.node_ids), config,
                  **{k: policy[k] for k in ENGINE_FIELDS})
    require(policy['chunk_edges'] <= 65536, 'bounded edge chunk required')
    n, m = len(a.node_ids), len(b.node_ids)
    require(policy['max_checkpoint_bytes'] >= 32*n*m+512+3*LIMIT, 'checkpoint state allowance')
    needed = 80*min(n, m)+32*min(policy['chunk_edges'], b.edge_index.shape[1])
    require(policy['max_score_buffer_bytes'] >= needed, 'score buffer allowance')
    require(policy['total_checkpoint_bytes'] >= LIMIT+policy['max_checkpoint_bytes']+LIMIT,
            'owner and one publication reservation required')
    return dict(policy)


class PairSession:
    @classmethod
    def _reserve(cls, root, name, a, b, config, owner, ident, policy):
        root = safe_root(root)
        require(isinstance(name, str) and re.fullmatch('[A-Za-z0-9_-]{1,100}', name), 'exclusive local name required')
        hash_string(owner)
        self = cls()
        self.root = root; self.directory = root/name
        self.a, self.b, self.config = a, b, config
        self.owner, self.identity, self.policy = owner, ident, policy
        self.state = None; self.result = None; self.safe = True
        self.publications = 0; self.reserved_bytes = LIMIT; self.complete_published = False
        self.directory.mkdir(exist_ok=False); engine.ann.sync(root)
        write(self.directory/'owner.json', dict(schema_version=1, owner=owner,
                                               identity=ident, policy=policy))
        return self

    @classmethod
    def create(cls, root, name, a, b, config, *, owner, context, policy):
        policy = policy_check(a, b, config, policy)
        ident = identity(a, b, config, context)
        self = cls._reserve(root, name, a, b, config, owner, ident, policy)
        try:
            self.state = engine.create(a, b, config, **{k: policy[k] for k in ENGINE_FIELDS})
            return self
        except BaseException:
            self.close()
            raise

    @classmethod
    def resume(cls, root, name, a, b, config, reference, *, owner, expected_owner, context, policy):
        root = safe_root(root); policy = policy_check(a, b, config, policy)
        ident = identity(a, b, config, context); hash_string(expected_owner)
        path, meta = safe_reference(root, reference)
        keys = {'schema_version', 'kind', 'owner', 'identity', 'policy', 'state_sha256', 'result'}
        require(isinstance(meta, dict) and set(meta) == keys and type(meta['schema_version']) is int
                and meta['schema_version'] == 1, 'pair manifest schema')
        require(meta['owner'] == expected_owner and meta['identity'] == ident
                and meta['policy'] == policy, 'ordered pair/backend/owner/source/policy differs')
        result = None
        if meta['kind'] == 'complete':
            result = meta['result']
            require(meta['state_sha256'] is None and isinstance(result, dict)
                    and set(result) == {'score', 'convergence', 'iterations'}, 'completion schema')
            require(type(result['score']) in (float, int) and math.isfinite(result['score'])
                    and type(result['iterations']) is int and 0 <= result['iterations'] <= config['max_iterations']
                    and result['convergence'] in ('temperature_complete', 'iteration_cap'), 'completion values')
        else:
            require(meta['kind'] == 'progress' and meta['result'] is None, 'pair phase')
            hash_string(meta['state_sha256'])
        self = cls._reserve(root, name, a, b, config, owner, ident, policy)
        try:
            if result is not None:
                self.result = engine.MatchScore(**result)
            else:
                self.state = engine.load(path.parent/'state', a, b, config,
                                         expected_sha256=meta['state_sha256'],
                                         **{k: policy[k] for k in ENGINE_FIELDS})
            return self
        except BaseException:
            self.close()
            raise

    def step(self, *, max_operations):
        require(self.safe, 'closed or poisoned pair session')
        require(type(max_operations) is int and max_operations > 0, 'positive operation bound required')
        if self.result is not None:
            return self.result
        try:
            engine.advance(self.state, self.a, self.b, self.config, max_operations=max_operations)
            if self.state['phase'] == 'done':
                self.result = engine.score_only(self.state, self.a, self.b, self.config,
                                               max_buffer_bytes=self.policy['max_score_buffer_bytes'],
                                               chunk_edges=self.policy['chunk_edges'])
                engine.close(self.state); self.state = None
            return self.result
        except BaseException:
            self.close()
            raise

    def save(self):
        require(self.safe and not self.complete_published, 'closed/poisoned/already published pair')
        reserve = self.policy['max_checkpoint_bytes']+LIMIT
        require(self.publications < self.policy['max_publications']
                and self.reserved_bytes+reserve <= self.policy['total_checkpoint_bytes'],
                'pair publication count/byte allowance')
        directory = self.directory/f'artifact-{self.publications:06d}'
        self.publications += 1; self.reserved_bytes += reserve
        try:
            directory.mkdir(exist_ok=False); engine.ann.sync(self.directory)
            state_sha = None
            if self.result is None:
                state_sha = engine.save(self.state, directory/'state', self.a, self.b, self.config,
                                        max_checkpoint_bytes=self.policy['max_checkpoint_bytes'])
            result = None if self.result is None else dict(score=self.result.score,
                       convergence=self.result.convergence, iterations=self.result.iterations)
            meta = dict(schema_version=1, kind='progress' if result is None else 'complete',
                        owner=self.owner, identity=self.identity, policy=self.policy,
                        state_sha256=state_sha, result=result)
            path = directory/'manifest.json'; sha = write(path, meta)
            if result is not None:
                self.complete_published = True
            return dict(path=str(path), sha256=sha)
        except BaseException:
            self.close()
            raise

    def close(self):
        self.safe = False
        if self.state is not None:
            try:
                engine.close(self.state)
            finally:
                self.state = None

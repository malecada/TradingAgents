"""Current-owner resident sampling with durable bounded draw acknowledgements.

Uses the preserved leased kernel unchanged. This publishes draw evidence, not a
numeric sample artifact or scientific sample-admission receipt. The returned
resident samples still require durable numeric publication and its provenance
join before dictionary use. Failed/complete namespaces cannot be restarted.
Logical metadata limits exclude array scratch, Python/RSS and filesystem costs;
those remain subject to the separately registered outer resource guard.
"""
import importlib.util
import json
import os
from pathlib import Path

import numpy as np
from . import compact_training, compact_owner, compact_policy, neighborhood_policy, score_batches as io
from .cache import cache_key
from .neighborhoods import graph_hash
from .provenance import canonical_bytes, durable_mkdir, file_hash, freeze, thaw

require = io._require
ROOT = Path(__file__).resolve().parents[3]
CORE = 'research/onchain-paper-replication-2026-09-24/full_sources/sampler-leased-core-2026-10-01/core.py'
LIMIT = 2 * 1024**2


def directory(training):
    record = training.owner.bound.record
    return (training.owner.bound._run.admission.root / 'research_artifacts/onchain_compact_sampler' /
        record['workflow_identity'] / record['experiment'])


def _sources(training):
    ad = training.owner.bound._run.admission
    expected = ad.experiment['source_files'].get(CORE)
    require(expected is not None and file_hash(ROOT / CORE) == expected
        and file_hash(ad.root / CORE) == expected, 'leased sampler core source not admitted or changed')
    return {CORE: expected}


def _kernel():
    spec = importlib.util.spec_from_file_location('compact_leased_sampler', ROOT / CORE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _prepare(training, input_name):
    training.check(); sources = _sources(training)
    owner = training.owner; run = owner.bound._run; record = owner.bound.record
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][record['representation']]
    item = json.loads(run.read_input(selected['plan_input']))['producers'][record['producer']]
    require(type(input_name) is str and input_name in run.admission.inputs
        and item.get('compact_sampler_input') == selected.get('compact_sampler_input') == input_name
        and item.get('native_backend') == selected.get('native_backend') == compact_policy.BACKEND,
        'explicit compact sampler route differs')
    policy = json.loads(run.read_input(input_name))
    require(set(policy) == {'schema_version', 'kernel', 'max_metadata_bytes', 'max_attempt_bytes', 'limits'}
        and type(policy['schema_version']) is int and policy['schema_version'] == 1
        and policy['kernel'] == 'resident-leased-v1', 'compact sampler policy schema differs')
    require(type(policy['max_metadata_bytes']) is int and 0 < policy['max_metadata_bytes'] <= LIMIT
        and type(policy['max_attempt_bytes']) is int and 0 < policy['max_attempt_bytes'] < 2**63,
        'compact sampler metadata bounds differ')
    limits = policy['limits']
    require(type(limits) is dict and set(limits) == {'schema_version', 'max_centers', 'max_direct_weight_bytes', 'neighborhood'}
        and type(limits['schema_version']) is int and limits['schema_version'] == 1
        and all(type(limits[k]) is int and limits[k] > 0 for k in ('max_centers', 'max_direct_weight_bytes')),
        'compact sampler limits differ')
    require(neighborhood_policy.validate_neighborhood_policy(limits['neighborhood']) is not None,
        'bounded sampler neighborhoods required')
    count = training.settings['sample_count']; total = sum(len(g.node_ids) for g in training.training_graphs)
    require(0 < count < 10**6 and count <= total <= limits['max_centers']
        and 16 * total <= limits['max_direct_weight_bytes'], 'compact sampler center/weight bounds differ')
    reserved = (count + 3) * policy['max_metadata_bytes']  # start, draws, complete AND failure
    require(reserved <= policy['max_attempt_bytes'], 'compact sampler logical reservation insufficient')
    start = {'schema_version': 1, 'kind': 'compact-sampler-draws', 'owner': owner.identity,
        'binding_sha256': cache_key(thaw(owner.bound.record)), 'training_sha256': cache_key(thaw(training.record)),
        'input': input_name, 'policy_sha256': run.admission.inputs[input_name]['sha256'],
        'sources': sources, 'configuration_sha256': cache_key(thaw(training.settings)),
        'training_graphs': training.training_hashes, 'seed': training.seed, 'numpy': np.__version__,
        'bit_generator': 'PCG64', 'draw_count': count, 'reserved_logical_bytes': reserved,
        'numeric_artifact_published': False, 'sample_provenance_admitted': False, 'resumable': False}
    _body(start, policy)
    # Preflight the complete receipt's variable-size references before allocation.
    _body(start | {'start_sha256': '0'*64, 'draw_sha256': ['0'*64]*count,
        'sample_fingerprint': '0'*64, 'sample_identity': '0'*64}, policy)
    return policy, start


def _body(value, policy):
    raw = canonical_bytes(value)
    require(len(raw) <= policy['max_metadata_bytes'], 'compact sampler metadata bound exceeded')
    return raw


def _fingerprint(samples):
    return cache_key({'identity': samples.identity, 'source_hashes': samples.source_hashes,
        'seed': samples.seed, 'rng_state': thaw(samples.rng_state), 'records': thaw(samples.records),
        'graphs': [graph_hash(g) for g in samples.graphs]})


def _read_exact(fd, name, expected, cap):
    raw = io._read(fd, name, cap)
    require(io._hash(raw) == expected, 'compact sampler draw/metadata hash differs')
    return json.loads(raw)


class Draws:
    """Live owner plus retained draw files and pinned resident samples; no reload."""
    def __init__(self, training, policy, start, root, inode, samples, receipt, reference):
        self._training = self._authority = training; self._samples = self._original_samples = samples
        self._policy = freeze(policy); self._start = freeze(start); self._directory = root; self._inode = inode
        self._record = freeze(receipt); self._reference = reference
        self._pin = cache_key(self._configuration())

    samples = property(lambda self: self._samples)
    record = property(lambda self: self._record)
    directory = property(lambda self: self._directory)
    receipt_sha256 = property(lambda self: self._reference)

    def _configuration(self):
        return {'policy': thaw(self._policy), 'start': thaw(self._start), 'record': thaw(self._record),
            'directory': str(self._directory), 'inode': self._inode, 'reference': self._reference}

    def _integrity(self):
        require(self._training is self._authority and self._samples is self._original_samples
            and cache_key(self._configuration()) == self._pin, 'compact sampler live view changed')

    def lease(self):
        self._integrity(); self._training.lease(); self._integrity()
        require(self._record['owner'] == self._training.owner.identity
            and self._record['training_sha256'] == cache_key(thaw(self._training.record)),
            'compact sampler training authority changed')

    def _verify(self):
        self._integrity(); root, fd = io._open(self._directory)
        try:
            info = os.fstat(fd)
            require((info.st_dev, info.st_ino) == self._inode, 'compact sampler directory changed')
            names = {'start.json', 'complete.json'} | {f'draw-{i:06d}.json' for i in range(self._record['draw_count'])}
            compact_owner.entries(root, names, required=names)
            cap = self._policy['max_metadata_bytes']
            saved = _read_exact(fd, 'complete.json', self._reference, cap)
            require(canonical_bytes(saved) == canonical_bytes(self._record), 'compact sampler receipt differs')
            start = _read_exact(fd, 'start.json', self._record['start_sha256'], cap)
            require(canonical_bytes(start) == canonical_bytes(self._start), 'compact sampler start differs')
            previous = None; rng = np.random.Generator(np.random.PCG64(start['seed']))
            for i, sha in enumerate(self._record['draw_sha256']):
                draw = _read_exact(fd, f'draw-{i:06d}.json', sha, cap)
                _draw(draw, i, previous, rng, start)
                require(canonical_bytes(draw['record']) == canonical_bytes(self._samples.records[i]),
                    'compact sampler resident record differs')
                previous = draw['sha256']
            require(canonical_bytes(rng.bit_generator.state) == canonical_bytes(self._samples.rng_state)
                and _fingerprint(self._samples) == self._record['sample_fingerprint'],
                'compact sampler resident sample changed')
            io._root(root, fd)
        finally: os.close(fd)

    def check(self):
        self.lease(); self._training.check(); _sources(self._training)
        self._verify(); self.lease()
        self._verify()  # Callback-free join after the last external live callback.


def _draw(draw, index, previous, rng, start):
    require(draw['schema_version'] == 1 and type(draw['index']) is int and draw['index'] == index
        and draw['previous_sha256'] == previous
        and cache_key({k: v for k, v in draw.items() if k != 'sha256'}) == draw['sha256']
        and draw['configuration_sha256'] == start['configuration_sha256']
        and canonical_bytes(draw['training_graphs']) == canonical_bytes(start['training_graphs'])
        and draw['seed'] == start['seed'] and draw['numpy'] == start['numpy']
        and draw['bit_generator'] == 'PCG64'
        and canonical_bytes(draw['rng_before']) == canonical_bytes(rng.bit_generator.state),
        'compact sampler draw chain differs')
    # Pinned NumPy weighted choice consumes one PCG64 uniform draw. No selection
    # or weight array is recreated by this chain check.
    rng.random(())
    require(canonical_bytes(draw['rng_after']) == canonical_bytes(rng.bit_generator.state),
        'compact sampler RNG transition differs')


def produce(training, *, input_name):
    require(type(training) is compact_training.Training, 'actual compact training route required')
    owner = training.owner
    require(owner._transition.acquire(blocking=False), 'concurrent compact sampler transition')
    fd = None
    try:
        policy, start = _prepare(training, input_name)
        require(not owner.stages and owner.active is None, 'sampling must precede matching stages')
        root = directory(training)
        require(root.is_absolute() and root.resolve() == root, 'compact sampler path redirected')
        require(not compact_owner.present(root), 'compact sampler namespace already claimed')
        kernel = _kernel(); training.lease(); durable_mkdir(root.parent)
        require(root.resolve() == root, 'compact sampler parent redirected')
        training.lease(); root.mkdir()
        try:
            parent, parent_fd = io._open(root.parent)
            try: os.fsync(parent_fd); io._root(parent, parent_fd)
            finally: os.close(parent_fd)
            root, fd = io._open(root); info = os.fstat(fd); inode = (info.st_dev, info.st_ino)
            require(info.st_dev == owner.bound._run.admission.root.stat().st_dev, 'compact sampler device differs')
            written = {}
            def write(name, value):
                ref = io._write(fd, name, _body(value, policy)); written[name] = ref
                return ref
            start_sha = write('start.json', start)
            def lease():
                training.lease(); io._root(root, fd)
            draws = []; previous = None; rng = np.random.Generator(np.random.PCG64(training.seed))
            def checkpoint(event):
                nonlocal previous
                lease(); value = thaw(event); _draw(value, len(draws), previous, rng, start)
                draws.append(write(f'draw-{len(draws):06d}.json', value))
                previous = value['sha256']; lease()
            samples = kernel.sample(training.graphs, thaw(training.settings), training.seed,
                policy=policy['limits'], lease=lease, checkpoint=checkpoint)
            require(len(draws) == len(samples.graphs) == len(samples.records) == start['draw_count']
                and samples.source_hashes == training.training_hashes and samples.seed == training.seed,
                'compact sampler completed population differs')
            receipt = start | {'start_sha256': start_sha, 'draw_sha256': draws,
                'sample_fingerprint': _fingerprint(samples), 'sample_identity': samples.identity}
            training.check(); _sources(training); lease()
            reference = write('complete.json', receipt)
            result = Draws(training, policy, start, root, inode, samples, receipt, reference)
            result.check(); return result
        except BaseException:
            owner.poisoned = True
            if fd is not None:
                try:
                    io._write(fd, 'failed.json', _body({'schema_version': 1, 'status': 'failed',
                        'owner': start['owner'], 'resumable': False}, policy))
                except (OSError, ValueError): pass  # Partial namespace itself bars reuse.
            raise
    finally:
        if fd is not None: os.close(fd)
        owner._transition.release()

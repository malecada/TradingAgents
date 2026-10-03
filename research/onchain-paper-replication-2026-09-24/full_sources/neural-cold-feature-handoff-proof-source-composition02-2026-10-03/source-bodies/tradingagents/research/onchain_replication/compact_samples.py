"""Bounded numeric publication tied to a current compact sampler result.

This persists and verifies the actual sampled bytes without redrawing. It does
not independently reconstruct weighted choices/induced neighborhoods, admit a
scientific sample proof, reopen an attempt, or seal a representation. Original
and loaded numeric payloads are explicitly reserved together; metadata/Python
objects, I/O scratch and RSS remain the outer registered guard's responsibility.
"""
import importlib.util
import io as buffers
import json
import os
from pathlib import Path

import numpy as np
from . import compact_sampler, compact_owner, component_store, score_batches as io
from .cache import cache_key
from .provenance import canonical_bytes, durable_mkdir, file_hash, freeze, thaw

require = io._require
ROOT = Path(__file__).resolve().parents[3]
READER = 'research/onchain-paper-replication-2026-09-24/full_sources/pair-component-reader-2026-10-01/reader.py'
MANIFEST_LIMIT = 2 * 1024**2


def directory(draws):
    training = draws._training; record = training.owner.bound.record
    return (training.owner.bound._run.admission.root / 'research_artifacts/onchain_compact_samples' /
        record['workflow_identity'] / record['experiment'])


def _sources(draws):
    ad = draws._training.owner.bound._run.admission
    expected = ad.experiment['source_files'].get(READER)
    require(expected is not None and file_hash(ROOT / READER) == expected
        and file_hash(ad.root / READER) == expected, 'strict sample reader source not admitted or changed')
    return {READER: expected}


def _reader():
    spec = importlib.util.spec_from_file_location('compact_numeric_reader', ROOT / READER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _payload(samples):
    return {'graphs': [{'node_ids': g.node_ids, 'node_features': g.node_features,
        'edge_index': g.edge_index, 'edge_features': g.edge_features,
        'parent_hash': g.parent_hash, 'center_id': g.center_id} for g in samples.graphs],
        'records': thaw(samples.records), 'source_hashes': samples.source_hashes,
        'rng_state': thaw(samples.rng_state), 'seed': samples.seed, 'identity': samples.identity}


def _encoded_size(payload, context, cap):
    """Preflight exact component bytes with bounded intermediate metadata.

    The running lower bound charges 20 structural bytes per encoded tree node,
    scalar value bytes and array descriptors. Every supported node's encoding is
    at least that large; refusal precedes constructing an unbounded whole tree.
    This limits encoded metadata, not Python allocator overhead.
    """
    arrays = {}; numeric = 0; lower = 0
    def charge(n):
        nonlocal lower
        lower += n; require(lower <= cap, 'sample manifest bound exceeded before publication')
    def encode(value):
        nonlocal numeric
        charge(20)
        if isinstance(value, np.ndarray):
            require(value.dtype in (np.dtype('float64'), np.dtype('int64')) and value.flags.c_contiguous,
                'native contiguous sample arrays required')
            header = buffers.BytesIO()
            np.lib.format.write_array_header_1_0(header, np.lib.format.header_data_from_array_1_0(value))
            name = f'array-{len(arrays):06d}.npy'; numeric += value.nbytes
            info = {'sha256': '0'*64, 'bytes': len(header.getvalue()) + value.nbytes,
                'shape': list(value.shape), 'dtype': str(value.dtype)}
            charge(len(canonical_bytes(info))); arrays[name] = info
            return {'kind': 'array', 'member': name}
        if isinstance(value, np.generic): value = value.item()
        if isinstance(value, dict):
            return {'kind': 'dict', 'items': [[encode(k), encode(v)] for k, v in value.items()]}
        if isinstance(value, (list, tuple)):
            return {'kind': 'tuple' if isinstance(value, tuple) else 'list', 'items': [encode(x) for x in value]}
        require(value is None or type(value) in (bool, str, int, float), 'sample scalar type differs')
        require(not isinstance(value, str) or len(value) <= cap, 'sample metadata string too large')
        charge(len(canonical_bytes(value)))
        return {'kind': 'scalar', 'value': value}
    tree = encode(payload)
    manifest = len(canonical_bytes({'schema_version': 1, 'context': context, 'tree': tree, 'arrays': arrays}))
    require(manifest <= cap, 'sample manifest bound exceeded before publication')
    return manifest, manifest + sum(x['bytes'] for x in arrays.values()), numeric


def _prepare(draws, input_name):
    draws.check(); sources = _sources(draws)
    training = draws._training; owner = training.owner; run = owner.bound._run; record = owner.bound.record
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][record['representation']]
    item = json.loads(run.read_input(selected['plan_input']))['producers'][record['producer']]
    require(type(input_name) is str and input_name in run.admission.inputs
        and selected.get('compact_samples_input') == item.get('compact_samples_input') == input_name,
        'explicit compact sample publication route differs')
    policy = json.loads(run.read_input(input_name))
    fields = {'schema_version', 'max_manifest_bytes', 'max_artifact_bytes', 'max_resident_array_bytes', 'max_attempt_bytes'}
    require(set(policy) == fields and type(policy['schema_version']) is int and policy['schema_version'] == 1
        and all(type(policy[k]) is int and 0 < policy[k] < 2**63 for k in fields - {'schema_version'})
        and policy['max_manifest_bytes'] <= MANIFEST_LIMIT, 'compact sample publication policy differs')
    reserved = policy['max_artifact_bytes'] + 3 * io.META_LIMIT
    require(reserved <= policy['max_attempt_bytes'], 'compact sample publication reservation insufficient')
    start = {'schema_version': 1, 'kind': 'compact-sample-numeric', 'owner': owner.identity,
        'binding_sha256': cache_key(thaw(owner.bound.record)), 'training_sha256': cache_key(thaw(training.record)),
        'draw_receipt_sha256': draws.receipt_sha256, 'sample_fingerprint': draws.record['sample_fingerprint'],
        'sample_identity': draws.samples.identity, 'policy_input': input_name,
        'policy_sha256': run.admission.inputs[input_name]['sha256'], 'sources': sources,
        'reserved_logical_bytes': reserved, 'resumable': False, 'sample_provenance_admitted': False}
    context = start | {'numeric_artifact_published': True}
    manifest, artifact, numeric = _encoded_size(_payload(draws.samples), context, policy['max_manifest_bytes'])
    require(artifact <= policy['max_artifact_bytes'] and 2 * numeric <= policy['max_resident_array_bytes'],
        'compact sample artifact/resident payload bound exceeded')
    proof = context | {'encoded_manifest_bytes': manifest, 'encoded_artifact_bytes': artifact,
        'numeric_payload_bytes': numeric, 'reserved_resident_payload_bytes': 2 * numeric}
    io._json(start); io._json(proof | {'start_sha256': '0'*64, 'artifact_sha256': '0'*64})
    return policy, start, context, proof


def _equal_numeric(actual, expected):
    """Compare bounded byte views, without an array-sized boolean temporary."""
    if isinstance(expected, np.ndarray):
        require(isinstance(actual, np.ndarray) and actual.dtype == expected.dtype
            and actual.shape == expected.shape and actual.flags.c_contiguous,
            'saved sample array dimensions/type differ')
        if expected.size:
            a = memoryview(actual).cast('B'); b = memoryview(expected).cast('B')
            for offset in range(0, len(a), 262144):
                require(a[offset:offset+262144] == b[offset:offset+262144], 'saved sample numeric bytes differ')
    elif isinstance(expected, dict):
        require(type(actual) is dict and set(actual) == set(expected), 'saved sample metadata keys differ')
        for k in expected: _equal_numeric(actual[k], expected[k])
    elif isinstance(expected, (list, tuple)):
        require(type(actual) is type(expected) and len(actual) == len(expected), 'saved sample sequence differs')
        for a, b in zip(actual, expected, strict=True): _equal_numeric(a, b)
    else:
        require(type(actual) is type(expected) and canonical_bytes(actual) == canonical_bytes(expected),
            'saved sample scalar differs')


class Published:
    """Current-owner numeric evidence with original resident samples; no reopen."""
    def __init__(self, draws, policy, start, context, proof, root, inode, reference, reader):
        self._draws = self._authority = draws; self._policy = freeze(policy)
        self._start = freeze(start); self._context = freeze(context); self._record = freeze(proof)
        self._directory = root; self._inode = inode; self._reference = reference; self._reader = reader
        self._pin = cache_key(self._configuration())

    samples = property(lambda self: self._draws.samples)
    record = property(lambda self: self._record)
    directory = property(lambda self: self._directory)
    receipt_sha256 = property(lambda self: self._reference)

    def _configuration(self):
        return {'policy': thaw(self._policy), 'start': thaw(self._start), 'context': thaw(self._context),
            'record': thaw(self._record), 'directory': str(self._directory), 'inode': self._inode, 'reference': self._reference}

    def _integrity(self):
        require(self._draws is self._authority and cache_key(self._configuration()) == self._pin,
            'compact sample publication view changed')

    def lease(self):
        self._integrity(); self._draws.lease(); self._integrity()
        require(self._record['draw_receipt_sha256'] == self._draws.receipt_sha256
            and self._record['owner'] == self._draws.record['owner'], 'compact sample current draw authority changed')

    def _evidence(self):
        self._integrity(); root, fd = io._open(self._directory)
        try:
            info = os.fstat(fd)
            require((info.st_dev, info.st_ino) == self._inode, 'compact sample directory changed')
            names = {'start.json', 'artifact', 'complete.json'}
            compact_owner.entries(root, names, required=names)
            require(io._read(fd, 'start.json', io.META_LIMIT) == io._json(thaw(self._start)),
                'compact sample start differs')
            raw = io._read(fd, 'complete.json', io.META_LIMIT)
            require(io._hash(raw) == self._reference and raw == io._json(thaw(self._record)),
                'compact sample completion differs')
            args = (root / 'artifact/manifest.json', self._record['artifact_sha256'], thaw(self._context))
            manifest, _, _, _ = self._reader.inspect_component(*args, root,
                self._policy['max_manifest_bytes'], self._policy['max_artifact_bytes'],
                self._policy['max_resident_array_bytes'] // 2)
            manifest_bytes = (root / 'artifact/manifest.json').stat().st_size
            require(manifest_bytes == self._record['encoded_manifest_bytes']
                and manifest_bytes + sum(x['bytes'] for x in manifest['arrays'].values()) == self._record['encoded_artifact_bytes'],
                'compact sample encoded size differs')
            io._root(root, fd)
            return args
        finally: os.close(fd)

    def check(self):
        self.lease(); self._draws.check(); _sources(self._draws)
        args = self._evidence()
        payload = self._reader.read_component(*args, root=self._directory,
            max_manifest_bytes=self._policy['max_manifest_bytes'], max_artifact_bytes=self._policy['max_artifact_bytes'],
            max_array_bytes=self._policy['max_resident_array_bytes'] // 2, lease=self.lease)
        _equal_numeric(payload, _payload(self.samples)); del payload
        self.lease()
        # Rejoin original resident samples and saved draws after the final live
        # callback, as well as the newly published artifact. Neither verifier
        # invokes an external lease callback.
        self._draws._verify(); self._evidence()


def publish(draws, *, input_name):
    require(type(draws) is compact_sampler.Draws, 'actual compact sampler result required')
    owner = draws._training.owner
    require(owner._transition.acquire(blocking=False), 'concurrent compact sample publication')
    fd = None
    try:
        policy, start, context, proof = _prepare(draws, input_name)
        require(not owner.stages and owner.active is None, 'sample publication must precede matching')
        root = directory(draws)
        require(root.is_absolute() and root.resolve() == root, 'compact sample path redirected')
        require(not compact_owner.present(root), 'compact sample namespace already claimed')
        reader = _reader(); draws.lease(); durable_mkdir(root.parent)
        require(root.resolve() == root, 'compact sample parent redirected')
        draws.lease(); root.mkdir()
        try:
            parent, parent_fd = io._open(root.parent)
            try: os.fsync(parent_fd); io._root(parent, parent_fd)
            finally: os.close(parent_fd)
            root, fd = io._open(root); info = os.fstat(fd); inode = (info.st_dev, info.st_ino)
            require(info.st_dev == owner.bound._run.admission.root.stat().st_dev, 'compact sample device differs')
            start_sha = io._write(fd, 'start.json', io._json(start))
            draws.lease(); io._root(root, fd)
            # A live callback after sizing must not grow/change arrays before
            # publication. The pinned draw fingerprint includes all sample bytes.
            draws._verify()
            require(io._read(fd, 'start.json', io.META_LIMIT) == io._json(start),
                'compact sample start changed before publication')
            path = component_store.save_component(root / 'artifact', _payload(draws.samples), context)
            artifact_sha = file_hash(path)
            draws.check(); _sources(draws); io._root(root, fd)
            proof = proof | {'start_sha256': start_sha, 'artifact_sha256': artifact_sha}
            ref = io._write(fd, 'complete.json', io._json(proof))
            result = Published(draws, policy, start, context, proof, root, inode, ref, reader)
            result.check(); return result
        except BaseException:
            owner.poisoned = True
            if fd is not None:
                try: io._write(fd, 'failed.json', io._json({'schema_version': 1, 'status': 'failed', 'owner': start['owner']}))
                except (OSError, ValueError): pass
            raise
    finally:
        if fd is not None: os.close(fd)
        owner._transition.release()

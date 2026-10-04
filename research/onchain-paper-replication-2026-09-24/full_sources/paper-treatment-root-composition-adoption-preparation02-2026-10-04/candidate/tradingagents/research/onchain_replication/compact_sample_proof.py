"""Current-owner scientific join of published samples to saved training draws.

This verifies existing evidence; it never invokes the sampler, writes a sample,
restarts a job or opens pair work. The saved uniform variate is audited against
its weighted CDF interval, not used to select a new center. Actual induced
neighborhoods and exact dictionary scope are required. Complete example/calendar
coverage, reconstructed prices/labels and empirical release remain separate.
"""
from contextlib import ExitStack
import math
import os

import numpy as np
from . import compact_samples, compact_sampler, compact_owner, matching_pair, score_batches as io
from .cache import cache_key
from .matching_identity import graph_identity
from .neighborhoods import SampleManifest, graph_hash, node_order_hash
from .neighborhood_policy import open_array_index, sample_array_bytes
from .provenance import canonical_bytes, freeze, thaw

require = io._require


def _parents(training):
    training._integrity()
    require(tuple(graph_hash(g) for g in training.training_graphs) == training.training_hashes,
        'scientific sample training parent changed')


def _events(draws):
    draws._verify(); root, fd = io._open(draws.directory)
    try:
        result = [compact_sampler._read_exact(fd, f'draw-{i:06d}.json', sha,
            draws._policy['max_metadata_bytes']) for i, sha in enumerate(draws.record['draw_sha256'])]
        io._root(root, fd); return result
    finally: os.close(fd)


def _audit(training, samples, events, policy, *, lease):
    """Bounded semantic audit; the caller separately admits saved-event hashes."""
    _parents(training); config = thaw(training.settings); count = config['sample_count']; seed = training.seed
    require(type(samples) is SampleManifest and type(samples.seed) is int and samples.seed == seed,
        'scientific sample type/seed differs')
    require(len(samples.graphs) == len(samples.records) == len(events) == count
        and samples.source_hashes == training.training_hashes, 'scientific sample population differs')
    require(samples.identity == cache_key({'training_graphs': samples.source_hashes, 'config': config,
        'seed': seed, 'records': samples.records, 'rng_state': samples.rng_state}), 'sample configuration/order identity differs')
    parents = dict(zip(training.training_hashes, training.training_graphs, strict=True))
    offsets = {}; total = 0
    for h, g in parents.items(): offsets[h] = total; total += len(g.node_ids)
    limits = policy['limits']; neighborhood = limits['neighborhood']
    require(count <= total <= limits['max_centers'] and 16 * total <= limits['max_direct_weight_bytes'],
        'scientific sample audit weight capacity differs')
    lease(); _parents(training)
    weights = np.ones(total, dtype=np.float64); cdf = np.empty(total, dtype=np.float64)
    rng = np.random.Generator(np.random.PCG64(seed)); seen = set(); typed = []; retained = 0
    active = None; index = None
    with ExitStack() as stack:
        for local, record, draw in zip(samples.graphs, samples.records, events, strict=True):
            lease()
            require(set(record) == {'graph_hash', 'center_id', 'center_index', 'probability', 'node_count', 'edge_count'}
                and canonical_bytes(draw['record']) == canonical_bytes(record), 'sample draw/record schema differs')
            h = record['graph_hash']; center = record['center_index']; probability = record['probability']
            require(h in parents and type(center) is int and 0 <= center < len(parents[h].node_ids),
                'sample center membership differs')
            require((h, center) not in seen, 'duplicate sampled center'); seen.add((h, center))
            require(local.parent_hash == h and local.center_id == record['center_id'] == parents[h].node_ids[center]
                and type(record['node_count']) is int and record['node_count'] == len(local.node_ids)
                and type(record['edge_count']) is int and record['edge_count'] == local.edge_index.shape[1],
                'sample local parent/center/dimensions differ')
            chosen = offsets[h] + center
            np.divide(weights, weights.sum(), out=cdf)
            require(type(probability) is float and math.isfinite(probability)
                and 0 < probability == float(cdf[chosen]) <= 1, 'sample overlap-weight probability differs')
            # NumPy's pinned weighted choice normalizes the cumulative p array
            # once more. Reuse the probability buffer; there is no third N-array.
            np.cumsum(cdf, out=cdf); cdf /= cdf[-1]
            require(canonical_bytes(draw['rng_before']) == canonical_bytes(rng.bit_generator.state),
                'sample saved uniform initial state differs')
            uniform = float(rng.random(()))
            require(canonical_bytes(draw['rng_after']) == canonical_bytes(rng.bit_generator.state),
                'sample saved uniform terminal state differs')
            lower = float(cdf[chosen - 1]) if chosen else 0.0
            require(lower <= uniform < float(cdf[chosen]), 'sample saved uniform CDF interval differs')
            if active != h:
                stack.close(); index = stack.enter_context(open_array_index(parents[h], neighborhood)); active = h
                require(index.identity == h, 'sample induced parent identity differs')
            identity = graph_identity(local)
            induced = index.neighborhood(center, config)
            require(identity == graph_identity(induced), 'sample is not actual induced training neighborhood')
            del induced
            selected = index.selected(center, config)
            require(node_order_hash(selected) == draw['selected_indices_sha256'], 'sample selected-index hash differs')
            retained += sample_array_bytes(local)
            require(type(draw['retained_array_bytes']) is int and retained == draw['retained_array_bytes']
                and retained <= neighborhood['max_sample_array_bytes'], 'sample retained-byte prefix differs')
            weights[chosen] = 0
            for start in range(0, len(selected), 512):
                positions = offsets[h] + selected[start:start+512]
                weights[positions] *= .5
            del selected, positions  # Do not retain prior index scratch into extraction.
            typed.append(identity)
        require(canonical_bytes(samples.rng_state) == canonical_bytes(rng.bit_generator.state),
            'sample final RNG identity differs')
    del weights, cdf
    lease(); _parents(training)  # Callback-free parent rehash after the last audit callback.
    scope = cache_key({'schema_version': 1, 'kind': 'dictionary',
        'workflow': training.owner.bound.record['workflow_identity'], 'backend': matching_pair.BACKEND,
        'sample': samples.identity, 'typed_sample_graphs': typed,
        'matching': thaw(training.descriptor['configs']['matching']), 'dictionary': config, 'seed': seed})
    return {'scope': scope, 'typed_sample_graphs': typed, 'weighted_draws_verified': count,
        'induced_neighborhoods_verified': count, 'retained_numeric_bytes': retained,
        'direct_weight_buffer_bytes': 16 * total}


class Proof:
    def __init__(self, published, audit):
        self._published = self._authority = published
        training = published._draws._training
        self._record = freeze({'schema_version': 1, 'kind': 'compact-scientific-samples',
            'owner': training.owner.identity, 'publication_sha256': published.receipt_sha256,
            'draw_receipt_sha256': published._draws.receipt_sha256, 'training_sha256': cache_key(thaw(training.record)),
            'sample_identity': published.samples.identity, 'sample_provenance_admitted': True,
            'complete_calendar_admitted': False, 'representation_admitted': False, **audit})
        require(len(canonical_bytes(self._record)) <= compact_owner.LIMIT, 'sample proof metadata bound exceeded')
        self._pin = cache_key(thaw(self._record))

    samples = property(lambda self: self._published.samples)
    record = property(lambda self: self._record)
    scope = property(lambda self: self._record['scope'])
    owner = property(lambda self: self._published._draws._training.owner)

    def _integrity(self):
        require(self._published is self._authority and cache_key(thaw(self._record)) == self._pin,
            'scientific sample proof changed')

    def _final(self):
        self._integrity(); self._published._draws._verify(); self._published._evidence()
        _parents(self._published._draws._training)
        require(self._record['publication_sha256'] == self._published.receipt_sha256
            and self._record['owner'] == self.owner.identity, 'scientific sample authority differs')

    def lease(self):
        # Frozen resident inputs and saved evidence between full checks; no
        # repeated parent hashing or semantic re-audit at every pair comparison.
        self._integrity(); self._published.lease(); self._integrity()
        require(self._record['publication_sha256'] == self._published.receipt_sha256
            and self._record['owner'] == self.owner.identity, 'scientific sample authority differs')

    def check(self):
        self.lease(); self._published.check()
        draws = self._published._draws
        audit = _audit(draws._training, self.samples, _events(draws), thaw(draws._policy), lease=self.lease)
        require(all(canonical_bytes(v) == canonical_bytes(self._record[k]) for k, v in audit.items()),
            'scientific sample audit changed')
        self.lease(); self._final()


def admit(published):
    require(type(published) is compact_samples.Published, 'actual published compact samples required')
    draws = published._draws; training = draws._training; owner = training.owner
    require(owner._transition.acquire(blocking=False), 'concurrent scientific sample admission')
    try:
        published.check()
        require(not owner.stages and owner.active is None, 'scientific sample admission must precede matching')
        audit = _audit(training, published.samples, _events(draws), thaw(draws._policy), lease=published.lease)
        proof = Proof(published, audit); proof.lease(); proof._final()
        return proof
    finally: owner._transition.release()

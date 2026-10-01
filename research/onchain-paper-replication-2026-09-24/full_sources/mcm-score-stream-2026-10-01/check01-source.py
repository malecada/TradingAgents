"""MCM callback adapter for exact-purpose durable tails and sealed score chunks.

The supplied compute callback retains responsibility for matcher convergence,
checkpointing and cleanup. This does not replace its per-pair journal/scratch,
provide successor admission, or authorize a registered financial execution.
"""
import os
from pathlib import Path

from . import score_batches as batch, score_tail as tail
from .cache import cache_key
from .dictionary import dictionary_hash
from .matching_identity import graph_identity
from .matching_pair import BACKEND
from .neighborhoods import graph_hash, node_order_hash
from .provenance import thaw

require = batch._require


class MCMScoreStream:
    def __init__(self, root, *, graph, dictionary, matching_config, workflow,
                 backend, owner, chunk_cells, compute, lease):
        batch._identity(workflow); batch._identity(owner)
        require(callable(compute) and callable(lease), 'compute and live lease required')
        require(cache_key(backend) == cache_key(BACKEND), 'explicit scalar backend required')
        require(dictionary_hash(dictionary) == dictionary.identity
            and cache_key(dictionary.config.get('pair_execution')) == cache_key(backend)
            and dictionary.matching_config_hash == cache_key({'config': matching_config, 'backend': backend}),
            'dictionary/backend/matching identity differs')
        self.nodes = graph.node_ids; self.motifs = tuple(graph_identity(m) for m in dictionary.representatives)
        self.n = len(self.nodes); self.k = len(self.motifs)
        batch._shape(self.n, self.k, chunk_cells)
        tail._shape(0, chunk_cells)
        self.parent = graph_hash(graph); node_order = node_order_hash(self.nodes)
        self.workload = cache_key({'schema_version': 1, 'kind': 'mcm', 'workflow': workflow,
            'backend': backend, 'graph': self.parent, 'node_order': node_order,
            'dictionary': dictionary.identity, 'ordered_motifs': list(self.motifs),
            'matching': matching_config, 'dtype': 'float32'})
        self.scope = {'graph': self.parent, 'node_order': node_order,
            'dictionary': dictionary.identity, 'ordered_motifs': cache_key(list(self.motifs)),
            'matching': dictionary.matching_config_hash, 'workflow': self.workload}
        self.owner = owner; self.compute = compute; self.lease = lease
        self.cells = 0; self.closed = False; self.active = None; self.batches = None
        root = Path(root)
        require(root.is_absolute() and root.resolve() == root, 'canonical stream root required')
        lease(); root.mkdir()
        parent, parent_fd = batch._open(root.parent)
        try:
            os.fsync(parent_fd); batch._root(parent, parent_fd)
        finally:
            os.close(parent_fd)
        self.root, self.fd = batch._open(root)
        try:
            self.batches = batch.ScoreBatches(root / 'batches', scope=self.scope, owner=owner,
                rows=self.n, motifs=self.k, chunk_cells=chunk_cells, lease=lease)
            (root / 'tails').mkdir(); os.fsync(self.fd)
            start = {'schema_version': 1, 'kind': 'mcm-score-stream', 'scope': self.scope,
                'owner': owner, 'rows': self.n, 'motifs': self.k,
                'batch_start_sha256': self.batches.start_sha, 'chunk_cells': chunk_cells}
            self.start_sha = self.head = batch._write(self.fd, 'start.json', batch._json(start))
            self._check()
        except BaseException:
            self.close(); raise

    def _check(self):
        require(not self.closed, 'score stream is closed')
        self.lease(); batch._root(self.root, self.fd)

    def __call__(self, purpose, a, b):
        self._check()
        try:
            require(self.cells < self.n * self.k, 'all MCM cells already completed')
            center, motif = divmod(self.cells, self.k)
            require(isinstance(purpose, dict) and type(purpose.get('center_index')) is int
                and type(purpose.get('motif_index')) is int
                and purpose['center_index'] == center and purpose['motif_index'] == motif,
                'MCM occurrence order differs')
            require(getattr(a, 'parent_hash', None) == self.parent
                and getattr(a, 'center_id', None) == self.nodes[center], 'MCM local graph attribution differs')
            typed = [graph_identity(a), graph_identity(b)]
            require(typed[1] == self.motifs[motif], 'MCM motif identity differs')
            expected = {'schema_version': 1, 'kind': 'mcm', 'workload_sha256': self.workload,
                'graph_hash': self.parent, 'center_index': center, 'center_id': self.nodes[center],
                'motif_index': motif, 'typed_graphs': typed}
            require(cache_key(purpose) == cache_key(expected), 'exact MCM purpose differs')
            key = cache_key(expected)
            if self.active is None:
                count = min(self.batches.chunk_cells, self.n * self.k - self.cells)
                self.active = tail.ScoreTail(self.root / 'tails' / f'tail-{self.batches.chunks:012d}',
                    scope=self.scope, owner=self.owner, start_cell=self.cells, cells=count,
                    destination=tail.destination(self.batches), lease=self.lease)
            self._check()
            result = self.compute(thaw(expected), a, b)
            self._check()
            require(isinstance(result, dict) and set(result) == {'purpose_sha256', 'score'}
                and result['purpose_sha256'] == key, 'matcher returned another purpose')
            saved = self.active.append(self.cells, key, result['score'])
            self.cells += 1
            if self.active.acknowledged == self.active.start['cells']:
                index = self.batches.chunks; start_cell = self.active.start['start_cell']
                root = self.active.root; terminal = self.active.finish()
                head = tail.seal(root, terminal_sha256=terminal, batches=self.batches, lease=self.lease)
                link = {'schema_version': 1, 'start_sha256': self.start_sha, 'previous': self.head,
                    'index': index, 'start_cell': start_cell, 'cells': self.active.start['cells'],
                    'tail_terminal_sha256': terminal, 'batch_header_sha256': head}
                raw = batch._json(link)
                name = f'seal-{index:012d}.json'
                self.head = batch._write(self.fd, name, raw)
                self._check()
                require(batch._read(self.fd, name, batch.META_LIMIT) == raw, 'seal link publication changed')
                self.active = None
            return saved
        except BaseException:
            # Preserve all successful, interrupted and ambiguous files. The
            # outer owner records failure; this identity never reopens itself.
            self.close(); raise

    def finish(self):
        self._check()
        require(self.cells == self.n * self.k and self.active is None, 'MCM stream incomplete')
        try:
            terminal = self.batches.finish()
            record = {'schema_version': 1, 'start_sha256': self.start_sha, 'head': self.head,
                'cells': self.cells, 'chunks': self.batches.chunks, 'batch_terminal_sha256': terminal}
            raw = batch._json(record); result = batch._write(self.fd, 'complete.json', raw)
            self._check()
            require(batch._read(self.fd, 'complete.json', batch.META_LIMIT) == raw,
                    'MCM completion publication changed')
            return {**record, 'terminal_sha256': result}
        finally:
            self.close()

    def close(self):
        if not self.closed:
            self.closed = True
            if self.active is not None: self.active.close()
            if self.batches is not None: self.batches.close()
            os.close(self.fd)

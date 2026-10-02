"""MCM callback adapter for exact-purpose durable tails and sealed score chunks.

The supplied compute callback retains responsibility for matcher convergence,
checkpointing and cleanup. This does not replace its per-pair journal/scratch,
provide successor admission, or authorize a registered financial execution.
"""
import json
import os
from pathlib import Path
import re

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
                 backend, owner, chunk_cells, compute, lease, _imported=None):
        batch._identity(workflow); batch._identity(owner)
        require(callable(compute) and callable(lease), 'compute and live lease required')
        require(cache_key(backend) == cache_key(BACKEND), 'explicit scalar backend required')
        self._imported=self._imported_pin=_imported
        if _imported is None:
            require(dictionary_hash(dictionary) == dictionary.identity
                and cache_key(dictionary.config.get('pair_execution')) == cache_key(backend)
                and dictionary.matching_config_hash == cache_key({'config': matching_config, 'backend': backend}),
                'dictionary/backend/matching identity differs')
        else:
            from .imported_mcm_identity import Target
            require(type(_imported) is Target,'genuine imported target required')
            _imported.check()
            require(graph is _imported.graph and dictionary is _imported.dictionary and owner==_imported.owner.identity and workflow==_imported.owner.bound.record['workflow_identity'],'imported stream authority differs')
            require(cache_key(matching_config)==cache_key(thaw(_imported.owner.matching)),'imported stream matching differs')
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
        if _imported is not None:
            expected=_imported.derive_scope()
            require(expected==_imported.scope,'imported stream independently derived workload differs')
            self.scope=expected;self.workload=expected['workflow']
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
        except BaseException as primary:
            batch._close_after_failure(self.close, primary)
            raise

    def _check(self):
        require(not self.closed, 'score stream is closed')
        self.lease(); batch._root(self.root, self.fd)
        require(self._imported is self._imported_pin,'imported stream authority replaced')
        if self._imported is not None:
            self._imported.final(full_graph=False)
            require(self.scope==self._imported.derive_scope() and self.workload==self.scope['workflow'],'imported stream workload changed')

    def _seal_check(self, index, expected_sha):
        """Callback-free bounded verification of one tail/link/destination."""
        batch._root(self.root, self.fd)
        require(batch._hash(batch._read(self.fd, 'start.json', batch.META_LIMIT)) == self.start_sha,
                'stream start changed')
        raw = batch._read(self.fd, f'seal-{index:012d}.json', batch.META_LIMIT)
        require(batch._hash(raw) == expected_sha, 'seal link hash differs')
        link = json.loads(raw)
        offset = index * self.batches.chunk_cells
        count = min(self.batches.chunk_cells, self.n * self.k - offset)
        require(set(link) == {'schema_version', 'start_sha256', 'previous', 'index', 'start_cell',
            'cells', 'tail_terminal_sha256', 'batch_header_sha256'} and link['schema_version'] == 1
            and link['start_sha256'] == self.start_sha and link['index'] == index
            and link['start_cell'] == offset and link['cells'] == count, 'seal link identity differs')
        item = tail.verify(self.root / 'tails' / f'tail-{index:012d}', scope=self.scope,
            owner=self.owner, terminal_sha256=link['tail_terminal_sha256'], lease=lambda: None)
        expected_destination = batch._hash(batch._json({'directory': str(self.batches.root),
            'start_sha256': self.batches.start_sha, 'index': index, 'start_cell': offset, 'cells': count}))
        require(item['status'] == 'complete' and item['destination'] == expected_destination
            and item['start_cell'] == offset and item['cells'] == count, 'tail seal destination differs')
        root, fd = batch._open(self.batches.root)
        try:
            require(batch._hash(batch._read(fd, 'start.json', batch.META_LIMIT)) == self.batches.start_sha,
                    'batch start differs')
            header = batch._read(fd, f'chunk-{index:012d}.json', batch.META_LIMIT)
            payload = batch._read(fd, f'chunk-{index:012d}.bin', count * 8)
            require(batch._hash(header) == link['batch_header_sha256']
                and payload == item['values'].tobytes(), 'sealed score bytes/header differ')
            batch._root(root, fd)
        finally:
            os.close(fd)
        return link

    def _history_check(self, terminal, complete_raw):
        """All external callbacks have finished; no numerical work is repeated."""
        result = batch.verify(self.batches.root, scope=self.scope, owner=self.owner,
            terminal_sha256=terminal, lease=lambda: None)
        require(result['status'] == 'complete' and result['cells'] == self.cells
            and result['chunks'] == self.batches.chunks, 'completed batch denominator differs')
        previous = self.start_sha
        for index in range(self.batches.chunks):
            raw = batch._read(self.fd, f'seal-{index:012d}.json', batch.META_LIMIT)
            digest = batch._hash(raw)
            link = self._seal_check(index, digest)
            require(link['previous'] == previous, 'seal chain predecessor differs')
            previous = digest
        require(previous == self.head, 'seal chain terminal differs')
        for root, fixed, pattern, expected in (
            (self.root, {'start.json', 'batches', 'tails', 'complete.json'}, r'seal-([0-9]{12})\.json', 4),
            (self.root / 'tails', set(), r'tail-([0-9]{12})', 0)):
            directory, fd = batch._open(root)
            try:
                seen = 0
                with os.scandir(fd) as entries:
                    for entry in entries:
                        seen += 1; match = re.fullmatch(pattern, entry.name)
                        require(seen <= expected + self.batches.chunks and (entry.name in fixed
                            or (match is not None and int(match[1]) < self.batches.chunks)),
                            'unexpected stream inventory')
                require(seen == expected + self.batches.chunks, 'incomplete stream inventory')
                batch._root(directory, fd)
            finally:
                os.close(fd)
        require(batch._read(self.fd, 'complete.json', batch.META_LIMIT) == complete_raw,
                'stream completion changed during verification')
        batch._root(self.root, self.fd)

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
                self._seal_check(index, self.head)
                self.active = None
            return saved
        except BaseException as primary:
            # Preserve evidence; cleanup uncertainty must stay worker-fatal.
            batch._close_after_failure(self.close, primary)
            raise

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
            self._history_check(terminal, raw)
        except BaseException as primary:
            batch._close_after_failure(self.close, primary)
            raise
        self.close()
        return {**record, 'terminal_sha256': result}

    def close(self):
        if not self.closed:
            self.closed = True
            actions = []
            if self.active is not None: actions.append(self.active.close)
            if self.batches is not None: actions.append(self.batches.close)
            actions.append(lambda: os.close(self.fd))
            batch._cleanup(actions)

"""Engineering-only ordered MCM delivery; never a Produced/Owner capability."""
import hashlib
import json
import math
import numpy as np
from tradingagents.research.onchain_replication.array_neighborhoods import ArrayNeighborhoodIndex
from tradingagents.research.onchain_replication.neighborhoods import graph_hash, node_order_hash
from tradingagents.research.onchain_replication.matching_identity import graph_identity


def require(ok, message):
    if not ok:
        raise ValueError(message)


def drive(graph, dictionary, *, descriptor, policy, journal, executor, consumer,
          max_chunk_bytes):
    """Consume a fresh journal; deliver (ordinal,center,motif_start,f32 bytes).

    Consumer must copy/persist each chunk synchronously and treat all output as
    incomplete until this function returns. On error, its current chunk may be
    partially delivered; the original error gains an explicit progress note.
    No retry, resume, authority or registered representation is constructed.
    """
    rows = cells = 0
    primary = None
    try:
        require(callable(executor) and callable(consumer), 'explicit executor/consumer required')
        require(type(max_chunk_bytes) is int and 4 <= max_chunk_bytes <= 128, 'bounded f32 chunk required')
        require(journal.cells == 0 and journal.batch == 0 and not journal.closed and not journal.poisoned,
                'fresh open journal required')
        motifs = dictionary.representatives
        n = len(graph.node_ids)
        require(type(descriptor) is dict and set(descriptor) == {'rows','cells','motifs','graph_hash','node_order_hash','workload_sha256'}, 'exact engineering descriptor required')
        require(all(type(descriptor[k]) is int for k in ('rows','cells','motifs')) and n > 0
                and descriptor['rows'] == n and descriptor['motifs'] == len(motifs) == 32
                and descriptor['cells'] == n * 32 and journal.max_cells == n * 32,
                'full ordered MCM denominator differs')
        scope = descriptor['workload_sha256']
        require(type(scope) is str and len(scope) == 64 and all(c in '0123456789abcdef' for c in scope), 'typed workload digest required')
        parent = graph_hash(graph)
        require(parent == descriptor['graph_hash'] and node_order_hash(graph.node_ids) == descriptor['node_order_hash'], 'graph/center order differs')
        require(type(policy) is dict and set(policy) == {'max_buffer_bytes','edge_chunk','extraction_limit'}
                and all(type(v) is int and 0 < v < 2**63 for v in policy.values()), 'explicit extraction bounds required')
        require(policy['extraction_limit'] >= dictionary.config['maximum_neighborhood_nodes'], 'extraction ceiling cannot reduce original capacity')
        extraction = dict(dictionary.config)
        extraction['maximum_neighborhood_nodes'] = policy['extraction_limit']
        typed = [graph_identity(m) for m in motifs]
        chunk_cells = min(32, journal.batch_cells, max_chunk_bytes // 4)
        require(chunk_cells > 0, 'empty journal batch')
        with ArrayNeighborhoodIndex(graph, max_buffer_bytes=policy['max_buffer_bytes'],
                                    edge_chunk=policy['edge_chunk']) as index:
            for center in range(n):
                local = index.neighborhood(center, extraction)
                tasks = []
                try:
                    local_id = graph_identity(local)
                    for start in range(0, 32, chunk_cells):
                        tasks = []
                        keys = []
                        for motif in range(start, min(32, start + chunk_cells)):
                            purpose = {'schema_version':1,'kind':'mcm','workload_sha256':scope,
                                'graph_hash':parent,'center_index':center,'center_id':graph.node_ids[center],
                                'motif_index':motif,'typed_graphs':[local_id,typed[motif]],
                                'ordinal':center * 32 + motif}
                            key = hashlib.sha256((json.dumps(purpose,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()).digest()
                            keys.append(key)
                            tasks.append((purpose, local, motifs[motif]))
                        records = journal.run_batch(tasks, executor)
                        require(len(records) == len(tasks), 'completed batch count differs')
                        values = []
                        for offset, record in enumerate(records):
                            require(record[0] == center * 32 + start + offset and record[1] == keys[offset]
                                    and type(record[2]) is float and math.isfinite(record[2]) and 0 <= record[2] <= 1,
                                    'completed ordered score differs')
                            values.append(record[2])
                        payload = np.asarray(values, dtype=np.float32).tobytes()
                        require(len(payload) == 4 * len(tasks) <= max_chunk_bytes, 'output chunk bound differs')
                        consumer(center * 32 + start, center, start, payload)
                        cells += len(tasks)
                        tasks.clear()
                    rows += 1
                finally:
                    tasks.clear()
                    del local
        require(rows == n and cells == n * 32 and journal.cells == cells, 'incomplete full MCM coverage')
        return {'status':'engineering_ordered_cells_delivered','completed_rows':rows,
                'completed_cells':cells,'output_bytes':4*cells,'workload_sha256':scope,
                'representation_complete':False}
    except BaseException as error:
        primary = error
        error.add_note('MCM delivery incomplete: '+json.dumps({'fully_delivered_rows':rows,
            'confirmed_sink_cells':cells,'journal_completed_cells':journal.cells,
            'remaining_disposition':'unavailable; current consumer chunk may be partial; no retry'},sort_keys=True))
        raise
    finally:
        try:
            journal.close()
        except BaseException as cleanup:
            if primary is None:
                raise
            primary.add_note('Journal close failed: '+repr(cleanup))

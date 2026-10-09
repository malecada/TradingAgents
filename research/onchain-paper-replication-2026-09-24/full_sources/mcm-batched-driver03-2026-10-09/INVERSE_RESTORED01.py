"""Engineering-only streaming ordered MCM driver; no empirical capability."""
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


def _tasks(graph, motifs, extraction, policy, descriptor, typed):
    """One driver-owned local; consumer must drop prior task before next()."""
    with ArrayNeighborhoodIndex(graph, max_buffer_bytes=policy['max_buffer_bytes'],
                                edge_chunk=policy['edge_chunk']) as index:
        for center in range(len(graph.node_ids)):
            local = index.neighborhood(center, extraction)
            try:
                local_id = graph_identity(local)
                for motif in range(32):
                    purpose = {'schema_version':2,'kind':'mcm',
                        'workload_sha256':descriptor['workload_sha256'],
                        'graph_hash':descriptor['graph_hash'],'center_index':center,
                        'center_id':graph.node_ids[center],'motif_index':motif,
                        'typed_graphs':[local_id,typed[motif]],'ordinal':center*32+motif}
                    yield purpose, local, motifs[motif]
            finally:
                del local


def _batch(upstream, count, keys):
    for _ in range(count):
        task = next(upstream)
        purpose = task[0]
        keys.append(hashlib.sha256((json.dumps(purpose,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()).digest())
        try:
            yield task
        finally:
            del task


def drive(graph, dictionary, *, descriptor, policy, journal, executor, consumer,
          max_chunk_bytes):
    """Consume a fresh journal; consumer(ordinal,center,motif_start,f32_bytes).

    Consumer must synchronously copy/persist chunks, treating everything as
    incomplete until return. At most32 values/128bytes are delivered per call.
    Journal03 must drop each graph reference before requesting the next task.
    """
    delivered = 0
    upstream = None
    primary = None
    try:
        require(callable(executor) and callable(consumer), 'explicit executor/consumer required')
        require(type(max_chunk_bytes) is int and 4 <= max_chunk_bytes <= 128, 'bounded f32 chunk required')
        require(journal.cells == journal.batch == 0 and not journal.closed and not journal.poisoned,
                'fresh open journal required')
        motifs = dictionary.representatives
        n = len(graph.node_ids)
        fields = {'rows','cells','motifs','graph_hash','node_order_hash','workload_sha256','purpose_schema_version'}
        require(type(descriptor) is dict and set(descriptor) == fields, 'exact engineering descriptor required')
        require(all(type(descriptor[k]) is int for k in ('rows','cells','motifs','purpose_schema_version'))
                and descriptor['purpose_schema_version'] == 2 and n > 0 and descriptor['rows'] == n
                and descriptor['motifs'] == len(motifs) == 32 and descriptor['cells'] == n*32
                and journal.max_cells == n*32, 'full ordered MCM denominator differs')
        scope = descriptor['workload_sha256']
        require(type(scope) is str and len(scope) == 64 and all(c in '0123456789abcdef' for c in scope), 'workload digest required')
        require(graph_hash(graph) == descriptor['graph_hash'] and node_order_hash(graph.node_ids) == descriptor['node_order_hash'], 'graph/order differs')
        require(type(policy) is dict and set(policy) == {'max_buffer_bytes','edge_chunk','extraction_limit'}
                and all(type(v) is int and 0 < v < 2**63 for v in policy.values()), 'explicit extraction bounds required')
        require(policy['extraction_limit'] >= dictionary.config['maximum_neighborhood_nodes'], 'extraction ceiling cannot reduce original capacity')
        extraction = dict(dictionary.config)
        extraction['maximum_neighborhood_nodes'] = policy['extraction_limit']
        typed = [graph_identity(m) for m in motifs]
        descriptor = dict(descriptor)
        upstream = _tasks(graph, motifs, extraction, policy, descriptor, typed)
        while journal.cells < n*32:
            start = journal.cells
            count = min(journal.batch_cells, n*32-start)
            keys = []
            tasks = _batch(upstream, count, keys)
            try:
                records = journal.run_batch_stream(count, tasks, executor, descriptor)
            finally:
                tasks.close()
            require(journal.cells == start+count and len(records) == len(keys) == count, 'completed stream extent differs')
            # The real03 reader validates complete closure before output delivery.
            require(records == journal.read_complete(journal.batch-1), 'completed stream readback differs')
            for offset, record in enumerate(records):
                require(record[0] == start+offset and record[1] == keys[offset]
                        and type(record[2]) is float and math.isfinite(record[2]) and 0 <= record[2] <= 1,
                        'completed ordered score differs')
            offset = 0
            while offset < count:
                ordinal = start+offset
                center, motif = divmod(ordinal, 32)
                width = min(count-offset, 32-motif, max_chunk_bytes//4)
                payload = np.asarray([r[2] for r in records[offset:offset+width]],dtype=np.float32).tobytes()
                require(len(payload) == 4*width <= max_chunk_bytes, 'output bound differs')
                consumer(ordinal, center, motif, payload)
                delivered += width
                offset += width
        try:
            next(upstream)
        except StopIteration:
            pass
        else:
            raise ValueError('extra MCM task beyond full coverage')
        require(delivered == journal.cells == n*32, 'incomplete MCM coverage')
        return {'status':'engineering_ordered_cells_delivered','completed_rows':n,
                'completed_cells':delivered,'output_bytes':4*delivered,
                'workload_sha256':scope,'representation_complete':False}
    except BaseException as error:
        primary = error
        error.add_note('MCM delivery incomplete: '+json.dumps({'confirmed_sink_cells':delivered,
            'journal_completed_cells':journal.cells,'remaining_disposition':'unavailable; current sink chunk may be partial; no retry'},sort_keys=True))
        raise
    finally:
        close_error = None
        for owned in (upstream, journal):
            if owned is not None:
                try:
                    owned.close()
                except BaseException as cleanup:
                    if primary is not None:
                        primary.add_note('MCM close failed: '+repr(cleanup))
                    elif close_error is None:
                        close_error = cleanup
                    else:
                        close_error.add_note('MCM close failed: '+repr(cleanup))
        if close_error is not None:
            raise close_error

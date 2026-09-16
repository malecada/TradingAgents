"""One frozen offline local temporal-motif engineering benchmark."""
import argparse
from collections import Counter
import gc
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import urllib.parse

import pyarrow as pa
import pyarrow.parquet as pq
from raphtory import Graph, algorithms
from tradingagents.research import ResearchRun
from tradingagents.research.verify import verify_run

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENT = 'eth-temporal-motifs-20260916'
REGISTRATION = 'research/onchain-graph-2026-09-16/motifs/gates.json'
DELTA = 3600
SHARD_SIZE = 10000


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


original = load('motif_original_projection', HERE.parent / 'prototype/run.py')
oracle = load('motif_exhaustive_oracle', HERE / 'oracle.py')


def recover_events(read):
    """Revalidate every row before releasing an explicitly normalized event stream."""
    plan = json.loads(read('plan'))
    footer = original.raw_receipt(read('footer'))
    blocks = original.raw_receipt(read('blocks'))
    expected = json.loads(read('forensic_result'))
    metadata = original.validate_plan(plan, footer)
    events, normalized = [], 0
    url = plan['base_url'] + urllib.parse.quote(plan['object']['key'], safe='/=')
    state = original.math.Integrity(original.block_rows(blocks), plan['start_ns'], plan['end_ns'])
    with tempfile.TemporaryFile() as sparse:
        sparse.truncate(plan['object']['size']); sparse.write(b'PAR1')
        sparse.seek(plan['footer_start']); sparse.write(footer)
        for number, span in enumerate(plan['ranges'], 1):
            raw = read(f'range-{number:03d}'); record = json.loads(raw); body = original.raw_receipt(raw)
            headers = {'Range': f'bytes={span["start"]}-{span["end"]}', 'If-Match': plan['object']['etag']}
            if record['url'] != url or record['request_headers'] != headers or record['request_number'] != number:
                raise ValueError('retained range identity differs')
            original.transport.validate_range(record, body, span['start'], span['end'], plan['object'])
            sparse.seek(span['start']); sparse.write(body)
        sparse.flush()
        reader = original.AcquiredReader(sparse, [(r['start'],r['end']) for r in plan['ranges']]
            + [(0,3), (plan['footer_start'],plan['object']['size']-1)])
        parquet = pq.ParquetFile(reader, metadata=metadata, pre_buffer=False)
        names = ['hash','block_hash','block_number','block_timestamp','transaction_index',
                 'from_address','to_address','value','receipt_status']
        for group, rows in enumerate(plan['groups']):
            frame = parquet.read_row_group(group, columns=names, use_threads=False)
            if frame.num_rows != rows: raise ValueError('row-group denominator changed')
            columns = [(frame[n].cast(pa.int64()) if n == 'block_timestamp' else frame[n]).to_pylist() for n in names]
            for row in zip(*columns, strict=True):
                if row[6] == 'None':
                    row = (*row[:6], None, *row[7:]); normalized += 1
                before = state.categories['graph_event']
                state.add(row)
                if state.categories['graph_event'] > before:
                    if row[3] % 1000000000: raise ValueError('timestamp is not exact integer seconds')
                    events.append((row[2],row[4],row[3]//1000000000,row[5].lower(),row[6].lower()))
            del columns, frame
    integrity = state.finish()
    passed = integrity.pop('admitted')
    integrity['checks_pass_after_declared_normalization'] = passed
    if not passed or integrity != expected['integrity'] or normalized != expected['normalization']['affected_rows']:
        raise ValueError('normalized integrity differs from retained forensic evidence')
    fingerprint = hashlib.sha256()
    for (a,b), count in sorted(state.pairs.items()): fingerprint.update(f'{a},{b},{count}\n'.encode())
    if fingerprint.hexdigest() != expected['diagnostic_graph']['pair_count_sha256']:
        raise ValueError('static pair identity changed')
    outgoing, incoming = Counter(), Counter()
    for a,b in state.pairs: outgoing[a] += 1; incoming[b] += 1
    centers = sorted(set([n for n,_ in sorted(outgoing.items(),key=lambda p:(-p[1],p[0]))[:3]]
                        + [n for n,_ in sorted(incoming.items(),key=lambda p:(-p[1],p[0]))[:3]]))
    del state, outgoing, incoming
    events.sort(key=lambda e:(e[0],e[1]))
    previous = None
    ordered, order_hash = [], hashlib.sha256()
    for order,(block,index,seconds,a,b) in enumerate(events):
        if previous and ((block,index) <= previous[:2] or seconds < previous[2]):
            raise ValueError('canonical event order or clock failed')
        previous = (block,index,seconds)
        ordered.append((seconds,order,a,b))
        order_hash.update(f'{block},{index},{seconds},{order},{a},{b}\n'.encode())
    return ordered, centers, {'integrity':integrity, 'exact_sentinels_excluded':normalized,
        'events':len(ordered),'ordered_events_sha256':order_hash.hexdigest(),
        'pair_count_sha256':fingerprint.hexdigest(), 'expected_nodes':expected['diagnostic_graph']['nodes'],
        'expected_directed_pairs':expected['diagnostic_graph']['directed_pairs'],
        'ordering':'timestamp=integer Unix seconds; event_id=ordinal after (block,transaction_index) sort',
        'historical_feature_panel_admitted':False,'original_lifecycle_changed':False}


def graph_for(events):
    graph = Graph()
    for seconds,order,a,b in events: graph.add_edge(seconds,a,b,event_id=order)
    if graph.count_temporal_edges() != len(events): raise ValueError('Raphtory lost event multiplicity')
    return graph


def small_checks(events, centers):
    samples = {center:[] for center in centers}
    for event in events:
        for center in event[2:]:
            if center in samples and len(samples[center]) < 30: samples[center].append(event)
    results = []
    for center, sample in samples.items():
        actual = algorithms.local_temporal_three_node_motifs(graph_for(sample), DELTA, threads=2)
        actual = {n.name:v['motif_counter'] for n,v in actual.items()}
        expected = oracle.brute_local(sample, DELTA)
        if actual != expected: raise ValueError('bounded real-event combinatorial oracle mismatch')
        results.append({'center':center,'events':sample,'local_counts':actual,'matched':True})
    return {'selection':'union of top3 distinct-neighbor out-degree and top3 in-degree nodes; address breaks ties; first30 incident eligible events per center',
            'samples':results,'qualification':'induced event subsets; not full-day local counts for these centers'}


def export_local(graph, local, publish):
    names = sorted(graph.nodes.name)
    totals, square_sums, maxima, max_nodes = [0]*40,[0]*40,[0]*40,[None]*40
    nonzero, top = 0, []
    fingerprint = hashlib.sha256()
    row_count = 0
    for shard,start in enumerate(range(0,len(names),SHARD_SIZE)):
        lines = []
        for name in names[start:start+SHARD_SIZE]:
            counts = local.get(name)['motif_counter']
            if len(counts) != 40 or any(type(v) is not int or v < 0 for v in counts):
                raise ValueError('invalid Local40 vector')
            line = json.dumps([name,counts],separators=(',',':'))+'\n'
            fingerprint.update(line.encode()); lines.append(line)
            total = sum(counts); nonzero += total > 0
            top.append((total,name)); top = sorted(top,key=lambda x:(-x[0],x[1]))[:10]
            for i,v in enumerate(counts):
                totals[i] += v; square_sums[i] += v*v
                if v > maxima[i]: maxima[i],max_nodes[i] = v,name
            row_count += 1
        publish(f'local-{shard:03d}.json',{'encoding':'JSON-lines [address, Local40 integer vector]',
            'row_count':len(lines),'rows_jsonl':''.join(lines)})
    if any(totals[24+i] != totals[31-i] for i in range(4)) or any(v % 3 for v in totals[32:]):
        raise ValueError('local motif role conservation failed')
    total_unique = sum(totals[:24]) + sum(totals[24:32])//2 + sum(totals[32:])//3
    return {'node_count':row_count,'nonzero_nodes':nonzero,'local40_sums':totals,
        'local40_square_sums':square_sums,'local40_maxima':maxima,'local40_max_nodes':max_nodes,
        'local40_top_node_shares':[m/t if t else None for m,t in zip(maxima,totals)],
        'top10_by_local_role_participations':[{'node':n,'count':v} for v,n in top],
        'unique_three_event_occurrences':total_unique,'local_role_participations':sum(totals),
        'local_rows_sha256':fingerprint.hexdigest(),'shards':(len(names)+SHARD_SIZE-1)//SHARD_SIZE,
        'qualification':'Local40 roles:24star centers,8two-node endpoint directions,8triangle roles. Local role participation sums are not unique motif totals.'}


def execute(read, publish):
    begin = time.monotonic()
    if importlib.metadata.version('raphtory') != '0.17.0': raise ValueError('Raphtory version changed')
    events, centers, integrity = recover_events(read)
    publish('integrity.json',integrity)
    decoded_at = time.monotonic()
    samples = small_checks(events,centers); publish('bounded-oracle.json',samples)
    checked_at = time.monotonic()
    graph = graph_for(events)
    if graph.count_nodes() != integrity['expected_nodes'] or graph.count_edges() != integrity['expected_directed_pairs']:
        raise ValueError('Raphtory graph identity differs')
    del events; gc.collect()
    built_at = time.monotonic()
    publish('graph-build.json',{'nodes':graph.count_nodes(),'pairs':graph.count_edges(),
        'events':graph.count_temporal_edges(),'delta_seconds':DELTA,'threads':2,
        'boundary':'All3events inside Jan1,2024UTC; no cross-midnight motifs or outside context',
        'same_second_rule':'total chain order through event_id; not strictly increasing physical timestamps',
        'new_chain_requests':0})
    local = algorithms.local_temporal_three_node_motifs(graph, DELTA, threads=2)
    counted_at = time.monotonic()
    summary = export_local(graph,local,publish)
    if summary['node_count'] != integrity['expected_nodes']: raise ValueError('local result denominator differs')
    summary.update(delta_seconds=DELTA,raphtory_version='0.17.0',engineering_only=True,
                   historical_feature_panel_admitted=False,financial_evaluation_admitted=False)
    publish('motif-summary.json',summary)
    publish('timings.json',{'decode_validate_order_seconds':decoded_at-begin,
        'bounded_oracle_seconds':checked_at-decoded_at,'graph_build_seconds':built_at-checked_at,
        'local_motif_seconds':counted_at-built_at,'export_summary_seconds':time.monotonic()-counted_at,
        'elapsed_seconds':time.monotonic()-begin})
    return [{'id':name,'status':'complete'} for name in ['input-semantics','ordered-events','bounded-oracle','local-motifs','local-export']]


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--source',required=True)
    args = parser.parse_args()
    for parent in ['eth-graph-source-20260916','eth-graph-prototype-20260916']:
        verify_run(ROOT/'research_runs'/parent)
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        run.finish(execute(run.read_input,run.write_json))


if __name__ == '__main__': main()

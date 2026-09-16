"""Independent retained-byte motif closure; no production numerical imports."""
import argparse
import base64
from collections import Counter, deque
from datetime import datetime, timezone
import hashlib
import io
from itertools import combinations, groupby
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq
from tradingagents.research_amended.verify import verify_run, verify_claim


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def brute(events, delta=3600):
    """Classify ordered triples directly from endpoint identity and direction."""
    counts = {v: [0] * 40 for e in events for v in e[2:]}
    triangle_codes = {(2, 1, 0, 2): 0, (2, 1, 2, 0): 1,
                      (1, 2, 0, 2): 2, (1, 2, 2, 0): 3,
                      (2, 0, 1, 2): 4, (2, 0, 2, 1): 5,
                      (0, 2, 1, 2): 6, (0, 2, 2, 1): 7}
    for triple in combinations(sorted(events), 3):
        if triple[2][0] - triple[0][0] > delta:
            continue
        endpoint_frequency = Counter(v for e in triple for v in e[2:])
        if len(endpoint_frequency) == 2:
            for v in endpoint_frequency:
                direction = int(''.join('1' if e[2] == v else '0' for e in triple), 2)
                counts[v][24 + direction] += 1
        elif len(endpoint_frequency) == 3:
            centers = [v for v, n in endpoint_frequency.items() if n == 3]
            if centers:
                center, = centers
                leaves = [e[3] if e[2] == center else e[2] for e in triple]
                repeated_positions = [i for i in range(3) if leaves.count(leaves[i]) == 2]
                role = {(0, 1): 0, (0, 2): 8, (1, 2): 16}[tuple(repeated_positions)]
                direction = int(''.join('1' if e[2] == center else '0' for e in triple), 2)
                counts[center][role + direction] += 1
            else:
                a, b = triple[0][2:]
                third, = set(endpoint_frequency) - {a, b}
                rename = {a: 0, b: 1, third: 2}
                code = tuple(rename[v] for e in triple[1:] for v in e[2:])
                for v in endpoint_frequency:
                    counts[v][32 + triangle_codes[code]] += 1
    return counts


def two_node(events, delta=3600):
    """Independent rolling ordered-triple counts for each unordered dyad."""
    key = lambda e: (min(e[2:]), max(e[2:]))
    events.sort(key=lambda e: (*key(e), e[0], e[1]))
    result = {}
    for (a, b), group in groupby(events, key=key):
        single, double, triple, queue = [0, 0], [0]*4, [0]*8, deque()
        for seconds, _, sender, _ in group:
            while queue and queue[0][0] < seconds - delta:
                _, old = queue.popleft()
                single[old] -= 1
                for last in (0, 1):
                    double[old*2 + last] -= single[last]
            direction = int(sender == a)
            for pair in range(4):
                triple[pair*2 + direction] += double[pair]
            for first in (0, 1):
                double[first*2 + direction] += single[first]
            single[direction] += 1
            queue.append((seconds, direction))
        if any(triple):
            left = result.setdefault(a, [0]*8)
            right = result.setdefault(b, [0]*8)
            for i, count in enumerate(triple):
                left[i] += count
                right[7-i] += count
    return result


def reconcile_local(output, nodes, independent_two):
    """Recompute exported summary while checking every full-day two-node vector."""
    summary = output('motif-summary.json')
    totals, squares, maxima, maximum_nodes = [0]*40, [0]*40, [0]*40, [None]*40
    local_hash = hashlib.sha256(); local_nodes = set(); nonzero = 0; top = []
    previous = None
    for shard in range(39):
        chunk = output(f'local-{shard:03d}.json')
        lines = chunk['rows_jsonl'].splitlines(keepends=True)
        assert len(lines) == chunk['row_count'] == (10000 if shard < 38 else 1191)
        for line in lines:
            name, values = json.loads(line)
            assert name in nodes and name not in local_nodes and (previous is None or name > previous)
            assert len(values) == 40 and all(type(n) is int and n >= 0 for n in values)
            assert line == json.dumps([name, values], separators=(',', ':')) + '\n'
            assert values[24:32] == independent_two.get(name, [0]*8)
            local_hash.update(line.encode()); local_nodes.add(name); previous = name
            total = sum(values); nonzero += total > 0
            top.append((total, name)); top = sorted(top, key=lambda x: (-x[0], x[1]))[:10]
            for i, count in enumerate(values):
                totals[i] += count; squares[i] += count*count
                if count > maxima[i]: maxima[i], maximum_nodes[i] = count, name
    assert local_nodes == nodes
    assert totals == summary['local40_sums'] and squares == summary['local40_square_sums']
    assert maxima == summary['local40_maxima'] and maximum_nodes == summary['local40_max_nodes']
    assert summary['local40_top_node_shares'] == [m/t if t else None for m, t in zip(maxima, totals)]
    assert summary['top10_by_local_role_participations'] == [{'node': n, 'count': t} for t, n in top]
    assert all(totals[24+i] == totals[31-i] for i in range(4))
    assert all(n % 3 == 0 for n in totals[32:])
    unique = sum(totals[:24]) + sum(totals[24:32])//2 + sum(totals[32:])//3
    assert summary['unique_three_event_occurrences'] == unique
    assert summary['local_role_participations'] == sum(totals) and summary['nonzero_nodes'] == nonzero
    assert summary['node_count'] == len(nodes) and summary['shards'] == 39
    assert summary['local_rows_sha256'] == local_hash.hexdigest()
    assert summary['engineering_only'] and not summary['historical_feature_panel_admitted']
    assert not summary['financial_evaluation_admitted']
    assert summary['delta_seconds'] == 3600 and summary['raphtory_version'] == '0.17.0'
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    root = Path(args.root)
    here = root / 'research/onchain-graph-2026-09-16/motifs8gib'
    run = root / 'research_runs/eth-temporal-motifs-8gib-20260916'
    load = lambda path: json.loads(path.read_bytes())
    assert len(os.sched_getaffinity(0)) <= 2
    # Full-result checks are forbidden until successful completion exists.
    assert (run / 'complete.json').exists() and not (run / 'failed.json').exists()
    structural = verify_run(run)
    assert structural['status'] == 'complete' and structural['unavailable_count'] == 0
    assert structural['cell_count'] == 5 and structural['output_count'] == 44
    claim = verify_claim(run)
    terminal = load(run / 'complete.json')
    output_files = sorted(p.name for p in (run / 'outputs').iterdir())
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert source == claim['source'] == terminal['source']
    assert datetime.fromisoformat(claim['started_at']) < datetime.fromisoformat(terminal['ended_at'])
    gate = load(here / 'gates-v2.json')
    experiment = gate['experiments']['eth-temporal-motifs-8gib-20260916']
    assert claim['family']['prior_attempts'] == 2 and claim['family']['attempt_budget'] == 3
    assert claim['budget_amendment']['effective_budget'] == 4
    assert claim['budget_amendment']['prior_claim_count'] == 1
    assert len(experiment['inputs']) == 128
    assert len(experiment['outputs']) == 44 and len(experiment['cells']) == 5
    assert len(list((root / 'research_runs').glob('*/claim.json'))) == 41
    for name, digest in experiment['source_files'].items():
        assert file_sha(root / name) == digest
        assert sha(subprocess.check_output(['git', 'show', source + ':' + name], cwd=root)) == digest
    for name, digest in experiment['runtime_hashes'].items():
        path = (root / 'tradingagents/research' / name.removeprefix('original/')
                if name.startswith('original/') else root / 'tradingagents/research_amended' / name)
        assert file_sha(path) == digest
    for item in experiment['inputs'].values():
        assert file_sha(root / item['path']) == item['sha256']
    history = load(here / 'history.json')
    for name, digest in history['metadata_hashes'].items():
        assert file_sha(root / name) == digest
    resource = load(here / 'resource.json')
    assert resource['source'] == source and resource['child_exit_code'] == 0
    assert resource['limit_reason'] is None and resource['elapsed_time_kill'] is False
    assert resource['peak_sampled_tree_rss_bytes'] <= resource['rss_limit_bytes'] == 8 * 1024**3
    read_input = lambda name: load(root / experiment['inputs'][name]['path'])
    output = lambda name: load(run / 'outputs' / name)
    def body(record):
        raw = base64.b64decode(record['body_base64'], validate=True)
        assert sha(raw) == record['sha256'] and len(raw) == record['bytes']
        return raw
    plan = read_input('plan')
    footer = body(read_input('footer'))
    metadata = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
    blocks = pq.read_table(io.BytesIO(body(read_input('blocks'))),
        columns=['number', 'hash', 'timestamp', 'transaction_count'], use_threads=False)
    block_map = dict(zip(blocks['number'].to_pylist(), zip(blocks['hash'].to_pylist(),
        blocks['timestamp'].cast(pa.int64()).to_pylist(), blocks['transaction_count'].to_pylist())))
    assert len(block_map) == blocks.num_rows == 7107
    positions = {n: bytearray(c) for n, (_, _, c) in block_map.items()}
    hash_format = re.compile(r'0x[0-9a-fA-F]{64}\Z')
    address_format = re.compile(r'0x[0-9a-fA-F]{40}\Z')
    seen_hash, pairs, events = set(), Counter(), []
    categories, flags = Counter(), Counter()
    rows = sentinels = inversions = raw_bytes = 0
    previous = None
    names = ['hash', 'block_hash', 'block_number', 'block_timestamp', 'transaction_index',
             'from_address', 'to_address', 'value', 'receipt_status']
    with tempfile.TemporaryFile() as sparse:
        sparse.truncate(plan['object']['size']); sparse.write(b'PAR1')
        sparse.seek(plan['footer_start']); sparse.write(footer)
        for i, span in enumerate(plan['ranges'], 1):
            receipt = read_input(f'range-{i:03d}'); raw = body(receipt)
            assert receipt['status'] == 206 and receipt['request_number'] == i
            assert receipt['request_headers']['If-Match'] == receipt['response_headers']['etag'] == plan['object']['etag']
            assert receipt['response_headers']['content-range'] == f"bytes {span['start']}-{span['end']}/{plan['object']['size']}"
            assert len(raw) == span['bytes']
            sparse.seek(span['start']); sparse.write(raw); raw_bytes += len(raw)
        sparse.flush()
        parquet = pq.ParquetFile(sparse, metadata=metadata, pre_buffer=False)
        for group in range(metadata.num_row_groups):
            table = parquet.read_row_group(group, columns=names, use_threads=False)
            cols = [(table[n].cast(pa.int64()) if n == 'block_timestamp' else table[n]).to_pylist() for n in names]
            for th, bh, bn, ns, txi, a, b, value, status in zip(*cols, strict=True):
                rows += 1
                assert hash_format.fullmatch(th) and hash_format.fullmatch(bh)
                ident = bytes.fromhex(th[2:]); assert ident not in seen_hash; seen_hash.add(ident)
                wanted_hash, wanted_ns, count = block_map[bn]
                assert bh.lower() == wanted_hash.lower() and ns == wanted_ns
                assert plan['start_ns'] <= ns < plan['end_ns'] and ns % 10**9 == 0
                assert type(txi) is int and 0 <= txi < count and positions[bn][txi] == 0
                positions[bn][txi] = 1
                position = (bn, txi)
                inversions += previous is not None and position < previous; previous = position
                assert address_format.fullmatch(a) and type(status) is int and status in (0, 1)
                assert type(value) in (int, float) and math.isfinite(value) and value >= 0
                if b == 'None': sentinels += 1; b = None
                assert b is None or address_format.fullmatch(b)
                a = a.lower(); b = b.lower() if b is not None else None
                flags['failed_receipt'] += status == 0; flags['null_recipient'] += b is None
                flags['zero_value'] += value == 0; flags['self_transfer'] += a == b
                category = ('reverted' if status == 0 else 'null_recipient' if b is None else
                            'zero_value' if value == 0 else 'self_transfer' if a == b else 'graph_event')
                categories[category] += 1
                if category == 'graph_event':
                    events.append((bn, txi, ns // 10**9, a, b)); pairs[a, b] += 1
            del table, cols
    assert rows == len(seen_hash) == sum(map(len, positions.values())) == sum(map(sum, positions.values())) == 1101465
    assert sentinels == 777 and inversions == 3 and raw_bytes == 118730958
    del seen_hash, positions, blocks, block_map
    integrity = output('integrity.json')
    assert integrity['exact_sentinels_excluded'] == sentinels
    assert integrity['integrity']['categories'] == dict(categories, invalid=0)
    assert integrity['integrity']['flags_nonexclusive'] == dict(flags)
    assert integrity['integrity']['rows'] == rows
    forensic = read_input('forensic_result')
    assert integrity['integrity'] == forensic['integrity']
    pair_hash = hashlib.sha256()
    out_degree, in_degree = Counter(), Counter()
    nodes = set()
    for (a, b), n in sorted(pairs.items()):
        pair_hash.update(f'{a},{b},{n}\n'.encode())
        out_degree[a] += 1; in_degree[b] += 1; nodes.update((a, b))
    assert pair_hash.hexdigest() == integrity['pair_count_sha256'] == forensic['diagnostic_graph']['pair_count_sha256']
    centers = sorted(set([v for v, _ in sorted(out_degree.items(), key=lambda p: (-p[1], p[0]))[:3]]
                         + [v for v, _ in sorted(in_degree.items(), key=lambda p: (-p[1], p[0]))[:3]]))
    del pairs, out_degree, in_degree
    events.sort(key=lambda e: e[:2])
    ordered_hash = hashlib.sha256(); last = None
    for ordinal, (bn, txi, seconds, a, b) in enumerate(events):
        assert last is None or ((bn, txi) > last[:2] and seconds >= last[2])
        last = (bn, txi, seconds)
        ordered_hash.update(f'{bn},{txi},{seconds},{ordinal},{a},{b}\n'.encode())
        events[ordinal] = (seconds, ordinal, a, b)
    assert len(events) == integrity['events'] == 547332
    assert ordered_hash.hexdigest() == integrity['ordered_events_sha256']
    expected_samples = {v: [] for v in centers}
    for event in events:
        for v in event[2:]:
            if v in expected_samples and len(expected_samples[v]) < 30:
                expected_samples[v].append(event)
    actual_samples = output('bounded-oracle.json')['samples']
    assert [x['center'] for x in actual_samples] == centers
    for sample in actual_samples:
        exact = expected_samples[sample['center']]
        assert [list(e) for e in exact] == sample['events']
        assert brute(exact) == sample['local_counts'] and sample['matched'] is True
    build = output('graph-build.json')
    assert build['nodes'] == len(nodes) == 381191 and build['pairs'] == 443937
    assert build['events'] == len(events) and build['delta_seconds'] == 3600
    assert build['threads'] == 2 and build['new_chain_requests'] == 0
    independent_two = two_node(events)
    del events
    summary = reconcile_local(output, nodes, independent_two)
    for item in experiment['inputs'].values():
        assert file_sha(root / item['path']) == item['sha256']
    report = {'passed': True, 'benchmark_complete': True,
        'reviewed_at': datetime.now(timezone.utc).isoformat(),
        'reviewer_script_sha256': file_sha(Path(__file__)), 'source': source,
        'claim_sha256': file_sha(run/'claim.json'),
        'terminal_sha256': file_sha(run/'complete.json'),
        'gate_sha256': file_sha(here/'gates-v2.json'), 'structural_verification': structural,
        'raw_transactions': rows, 'eligible_events': 547332, 'excluded_exact_sentinels': sentinels,
        'ordered_events_sha256': ordered_hash.hexdigest(), 'bounded_subsets_recomputed': len(centers),
        'bounded_subset_event_counts': [len(expected_samples[v]) for v in centers],
        'nodes': len(nodes), 'directed_pairs': 443937,
        'retained_output_sha256': {name: file_sha(run/'outputs'/name) for name in output_files},
        'expected_outputs': 44, 'retained_outputs': 44, 'registered_cells': 5,
        'all_full_day_two_node_vectors_independently_recounted': True,
        'full_day_star_triangle_independently_recounted': False,
        'summary': summary,
        'execution_resource': resource, 'new_network_requests': 0, 'financial_admission': False,
        'qualification': 'Raw event/order identity, six subsets, all local exports and whole-day two-node vectors independently reconciled. Whole-day stars and triangles have synthetic/subset, export and role-conservation checks, not independent full-day recounts. No financial or historical feature-panel admission.'}
    with Path(args.report).open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'summary'}, indent=2))
    print('UNIQUE_OCCURRENCES', summary['unique_three_event_occurrences'],
          'LOCAL_PARTICIPATIONS', summary['local_role_participations'],
          'NONZERO_NODES', summary['nonzero_nodes'])


if __name__ == '__main__':
    main()

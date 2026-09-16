"""Independent retained-byte closure check; no subject graph implementation imports."""
import argparse
import base64
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile

import pyarrow as pa
import pyarrow.parquet as pq


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    root = Path(args.root)
    here = root / 'research/onchain-graph-2026-09-16/forensic'
    read = lambda path: json.loads(path.read_bytes())
    contract_raw = (here / 'contract.json').read_bytes()
    contract = json.loads(contract_raw)
    result = read(here / 'results/result.json')
    start = read(here / 'results/start.json')
    resource = read(here / 'resource.json')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert source == result['source'] == start['source'] == resource['source']
    assert digest(contract_raw) == result['contract_sha256'] == start['contract_sha256']
    assert datetime.fromisoformat(start['started_at']) < datetime.fromisoformat(result['completed_at'])
    assert not (here / 'results/failed.json').exists()
    assert resource['child_exit_code'] == 0 and resource['limit_reason'] is None
    assert resource['elapsed_time_kill'] is False
    assert resource['peak_sampled_tree_rss_bytes'] < resource['rss_limit_bytes'] == 2 * 1024**3
    for name, expected in contract['source_files'].items():
        assert digest((root / name).read_bytes()) == expected
        assert digest(subprocess.check_output(['git', 'show', source + ':' + name], cwd=root)) == expected
    for reference in contract['inputs'].values():
        assert digest((root / reference['path']).read_bytes()) == reference['sha256']

    def input_json(name):
        return read(root / contract['inputs'][name]['path'])

    parent = input_json('parent_terminal')
    assert parent['cell_count'] == 119 and parent['unavailable_count'] == 2
    assert result['original_raw_integrity'] == input_json('parent_integrity')
    assert result['original_raw_integrity']['admitted'] is False
    assert result['source_admitted_feature_panel'] is False
    assert result['original_lifecycle_result_changed'] is False
    assert result['financial_evaluation_admitted'] is False and result['new_network_requests'] == 0

    def body(record):
        value = base64.b64decode(record['body_base64'], validate=True)
        assert digest(value) == record['sha256'] and len(value) == record['bytes']
        return value

    plan = input_json('plan')
    footer = body(input_json('footer'))
    metadata = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
    blocks = pq.read_table(io.BytesIO(body(input_json('blocks'))),
                          columns=['number', 'hash', 'timestamp', 'transaction_count'], use_threads=False)
    block_map = dict(zip(blocks['number'].to_pylist(), zip(blocks['hash'].to_pylist(),
        blocks['timestamp'].cast(pa.int64()).to_pylist(), blocks['transaction_count'].to_pylist())))
    positions = {n: bytearray(count) for n, (_, _, count) in block_map.items()}
    address = re.compile(r'0x[0-9a-fA-F]{40}\Z')
    hash_pattern = re.compile(r'0x[0-9a-fA-F]{64}\Z')
    hashes, pairs = set(), Counter()
    outgoing, incoming = defaultdict(set), defaultdict(set)
    sent, received = Counter(), Counter()
    categories, flags = Counter(), Counter()
    sentinels = rows = inversions = raw_bytes = 0
    last = None
    groups = []
    names = ['hash', 'block_hash', 'block_number', 'block_timestamp', 'transaction_index',
             'from_address', 'to_address', 'value', 'receipt_status']
    with tempfile.TemporaryFile() as sparse:
        sparse.truncate(plan['object']['size'])
        sparse.write(b'PAR1')
        sparse.seek(plan['footer_start'])
        sparse.write(footer)
        for number, span in enumerate(plan['ranges'], 1):
            record = input_json(f'range-{number:03d}')
            raw = body(record)
            assert record['status'] == 206 and record['request_number'] == number
            assert record['request_headers']['If-Match'] == record['response_headers']['etag'] == plan['object']['etag']
            assert record['response_headers']['content-range'] == f"bytes {span['start']}-{span['end']}/{plan['object']['size']}"
            assert len(raw) == span['bytes']
            sparse.seek(span['start'])
            sparse.write(raw)
            raw_bytes += len(raw)
        sparse.flush()
        parquet = pq.ParquetFile(sparse, metadata=metadata, pre_buffer=False)
        for group in range(metadata.num_row_groups):
            frame = parquet.read_row_group(group, columns=names, use_threads=False)
            columns = [(frame[n].cast(pa.int64()) if n == 'block_timestamp' else frame[n]).to_pylist() for n in names]
            count_sentinels = 0
            for th, bh, number, ts, index, sender, recipient, value, status in zip(*columns, strict=True):
                rows += 1
                assert hash_pattern.fullmatch(th) and hash_pattern.fullmatch(bh)
                identity = bytes.fromhex(th[2:])
                assert identity not in hashes
                hashes.add(identity)
                expected_hash, expected_time, count = block_map[number]
                assert bh.lower() == expected_hash.lower() and ts == expected_time
                assert type(index) is int and 0 <= index < count and positions[number][index] == 0
                positions[number][index] = 1
                position = (number, index)
                inversions += last is not None and position < last
                last = position
                assert address.fullmatch(sender) and type(status) is int and status in (0, 1)
                assert type(value) in (int, float) and math.isfinite(value) and value >= 0
                if recipient == 'None':
                    count_sentinels += 1
                    recipient = None
                assert recipient is None or address.fullmatch(recipient)
                sender = sender.lower()
                recipient = recipient.lower() if recipient is not None else None
                flags['failed_receipt'] += status == 0
                flags['null_recipient'] += recipient is None
                flags['zero_value'] += value == 0
                flags['self_transfer'] += recipient == sender
                if status == 0:
                    categories['reverted'] += 1
                elif recipient is None:
                    categories['null_recipient'] += 1
                elif value == 0:
                    categories['zero_value'] += 1
                elif recipient == sender:
                    categories['self_transfer'] += 1
                else:
                    categories['graph_event'] += 1
                    pairs[sender, recipient] += 1
                    outgoing[sender].add(recipient)
                    incoming[recipient].add(sender)
                    sent[sender] += 1
                    received[recipient] += 1
            sentinels += count_sentinels
            groups.append({'group': group, 'rows': frame.num_rows, 'exact_sentinels_normalized': count_sentinels})
            del frame, columns
    assert rows == len(hashes) == sum(len(v) for v in positions.values()) == sum(sum(v) for v in positions.values()) == 1101465
    assert raw_bytes == 118730958 and sentinels == contract['expected_exact_sentinels'] == 777
    expected_categories = {k: categories[k] for k in ['invalid', 'reverted', 'null_recipient', 'zero_value', 'self_transfer', 'graph_event']}
    assert expected_categories == result['integrity']['categories']
    assert dict(flags) == result['integrity']['flags_nonexclusive'] and groups == result['groups']
    assert inversions == result['integrity']['source_order_inversions'] == 3
    assert result['integrity']['checks_pass_after_declared_normalization'] is True
    nodes = set(outgoing) | set(incoming)
    edges, events = len(pairs), sum(pairs.values())
    reciprocal = sum(1 for a, neighbors in outgoing.items() for b in neighbors if a in outgoing.get(b, set()))
    in_hist = Counter(len(incoming.get(n, ())) for n in nodes)
    out_hist = Counter(len(outgoing.get(n, ())) for n in nodes)
    pair_hash = hashlib.sha256()
    for a, b in sorted(pairs):
        pair_hash.update(f'{a},{b},{pairs[a,b]}\n'.encode())
    metrics = {'nodes': len(nodes), 'directed_pairs': edges, 'events': events,
        'repeated_events': events-edges, 'repeated_event_fraction': (events-edges)/events,
        'reciprocal_directed_pairs': reciprocal, 'reciprocal_dyads': reciprocal//2,
        'reciprocal_directed_pair_fraction': reciprocal/edges,
        'in_degree_histogram': {str(k): v for k, v in sorted(in_hist.items())},
        'out_degree_histogram': {str(k): v for k, v in sorted(out_hist.items())},
        'in_degree_sum': sum(k*v for k,v in in_hist.items()),
        'out_degree_sum': sum(k*v for k,v in out_hist.items()),
        'max_in_degree': max(in_hist), 'max_out_degree': max(out_hist),
        'sender_event_square_sum': sum(v*v for v in sent.values()),
        'recipient_event_square_sum': sum(v*v for v in received.values()),
        'sender_event_hhi': sum(v*v for v in sent.values())/events**2,
        'recipient_event_hhi': sum(v*v for v in received.values())/events**2,
        'pair_count_sha256': pair_hash.hexdigest()}
    assert all(result['diagnostic_graph'][k] == value for k, value in metrics.items())
    for reference in contract['inputs'].values():
        assert digest((root / reference['path']).read_bytes()) == reference['sha256']
    report = {'reviewed_at': datetime.now(timezone.utc).isoformat(), 'passed': True,
        'reviewer_source_sha256': digest(Path(__file__).read_bytes()), 'execution_source': source,
        'result_sha256': digest((here / 'results/result.json').read_bytes()),
        'contract_sha256': digest(contract_raw), 'diagnostic_only': True,
        'new_network_requests': 0, 'original_lifecycle_unavailable_cells': 2,
        'raw_requests': len(plan['ranges']), 'raw_bytes': raw_bytes,
        'rows': rows, 'exact_sentinels_excluded': sentinels, 'categories': expected_categories,
        'metrics': metrics, 'execution_resource': resource,
        'qualification': 'Independent raw reconstruction without subject graph math or reconstruction imports; no financial values, predictive tests, independent chain canonicality or historical availability admission.'}
    with Path(args.report).open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({k:v for k,v in metrics.items() if 'histogram' not in k}, indent=2))


if __name__ == '__main__':
    main()

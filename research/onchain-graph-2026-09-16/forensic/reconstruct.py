"""Frozen offline forensic reconstruction. Does not amend or admit a lifecycle run."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.parse

import pyarrow as pa
import pyarrow.parquet as pq
from tradingagents.research.verify import verify_run

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('original_graph_prototype', HERE.parent / 'prototype/run.py')
original = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(original)


def normalize_recipient(row):
    """Only the exact observed source sentinel is normalized; input remains immutable."""
    if row[6] == 'None':
        fixed = list(row)
        fixed[6] = None
        return tuple(fixed), True
    return row, False


def reconstruct(plan, footer, blocks, read_range):
    begin = time.monotonic()
    metadata = original.validate_plan(plan, footer)
    normalization, groups = 0, []
    url = plan['base_url'] + urllib.parse.quote(plan['object']['key'], safe='/=')
    with tempfile.TemporaryFile() as sparse:
        sparse.truncate(plan['object']['size'])
        sparse.write(b'PAR1'); sparse.seek(plan['footer_start']); sparse.write(footer)
        for number, item in enumerate(plan['ranges'], 1):
            raw = read_range(number)
            receipt = json.loads(raw)
            body = original.raw_receipt(raw)
            expected = {'Range': f'bytes={item["start"]}-{item["end"]}', 'If-Match': plan['object']['etag']}
            if receipt['url'] != url or receipt['request_headers'] != expected or receipt['request_number'] != number:
                raise ValueError('retained range request identity differs')
            original.transport.validate_range(receipt, body, item['start'], item['end'], plan['object'])
            sparse.seek(item['start']); sparse.write(body)
        sparse.flush()
        reader = original.AcquiredReader(sparse, [(r['start'], r['end']) for r in plan['ranges']]
            + [(0, 3), (plan['footer_start'], plan['object']['size'] - 1)])
        parquet = pq.ParquetFile(reader, metadata=metadata, pre_buffer=False)
        state = original.math.Integrity(original.block_rows(blocks), plan['start_ns'], plan['end_ns'])
        reconstruction_seconds = time.monotonic() - begin
        started = time.monotonic()
        for group, expected in enumerate(plan['groups']):
            frame = parquet.read_row_group(group, columns=plan['columns'], use_threads=False)
            if frame.num_rows != expected: raise ValueError('decoded group row count differs')
            order = ['hash', 'block_hash', 'block_number', 'block_timestamp', 'transaction_index', 'from_address', 'to_address', 'value', 'receipt_status']
            columns = [(frame[n].cast(pa.int64()) if n == 'block_timestamp' else frame[n]).to_pylist() for n in order]
            group_normalized = 0
            for row in zip(*columns, strict=True):
                fixed, changed = normalize_recipient(row)
                group_normalized += changed
                state.add(fixed)
            normalization += group_normalized
            groups.append({'group': group, 'rows': frame.num_rows, 'exact_sentinels_normalized': group_normalized})
            del columns, frame
        integrity = state.finish()
        passed = integrity.pop('admitted')
        integrity['checks_pass_after_declared_normalization'] = passed
        decode_seconds = time.monotonic() - started
        started = time.monotonic()
        graph = original.math.graph_features(state.pairs) if passed else None
        graph_seconds = time.monotonic() - started
    return {'artifact_kind': 'post-hoc-offline-forensic-reconstruction', 'new_network_requests': 0,
            'original_lifecycle_result_changed': False, 'source_admitted_feature_panel': False,
            'financial_evaluation_admitted': False, 'groups': groups, 'integrity': integrity,
            'normalization': {'field': 'to_address', 'exact_literal': 'None', 'replacement': None,
                              'affected_rows': normalization, 'all_affected_rows_excluded_from_graph': True,
                              'contract_creation_attribution_proven': False},
            'diagnostic_graph': graph, 'timings': {'saved_range_reconstruction_seconds': reconstruction_seconds,
                'decode_integrity_pair_count_seconds': decode_seconds, 'graph_summary_seconds': graph_seconds,
                'elapsed_seconds': time.monotonic() - begin}}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    root = HERE.parents[2]
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() != args.source:
        raise ValueError('execution HEAD differs')
    relative = str((HERE / 'contract.json').relative_to(root))
    contract_raw = (HERE / 'contract.json').read_bytes()
    if subprocess.check_output(['git', 'show', args.source + ':' + relative], cwd=root) != contract_raw:
        raise ValueError('contract is not the committed version')
    contract = json.loads(contract_raw)
    for path, digest in contract['source_files'].items():
        if sha((root / path).read_bytes()) != digest or sha(subprocess.check_output(['git', 'show', args.source + ':' + path], cwd=root)) != digest:
            raise ValueError('forensic source bytes changed')
    verify_run(root / 'research_runs/eth-graph-prototype-20260916')
    directory = HERE / 'results'
    directory.mkdir()  # Exclusive reservation; no repeat or overwrite.
    def write(name, value):
        with (directory / name).open('x') as stream:
            json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False); stream.write('\n')
    write('start.json', {'started_at': datetime.now(timezone.utc).isoformat(), 'source': args.source,
                         'contract_sha256': sha(contract_raw), 'artifact_kind': 'forensic-only; no new lifecycle claim'})
    try:
        def read(name):
            reference = contract['inputs'][name]
            raw = (root / reference['path']).read_bytes()
            if sha(raw) != reference['sha256']: raise ValueError('retained input bytes changed: ' + name)
            return raw
        for name in contract['inputs']: read(name)
        result = reconstruct(json.loads(read('plan')), original.raw_receipt(read('footer')),
                             original.raw_receipt(read('blocks')), lambda n: read(f'range-{n:03d}'))
        result['original_raw_integrity'] = json.loads(read('parent_integrity'))
        if result['normalization']['affected_rows'] != contract['expected_exact_sentinels']:
            raise ValueError('sentinel count differs from independently diagnosed captured cohort')
        if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() != args.source:
            raise ValueError('execution HEAD changed')
        for path, digest in contract['source_files'].items():
            if sha((root / path).read_bytes()) != digest: raise ValueError('source changed during check')
        for name in contract['inputs']: read(name)
        result.update(source=args.source, contract_sha256=sha(contract_raw), completed_at=datetime.now(timezone.utc).isoformat())
        write('result.json', result)
        print(json.dumps({k: result[k] for k in ['artifact_kind', 'normalization', 'timings']}))
    except BaseException as exc:
        write('failed.json', {'type': type(exc).__name__, 'error': str(exc), 'source': args.source})
        raise


if __name__ == '__main__': main()

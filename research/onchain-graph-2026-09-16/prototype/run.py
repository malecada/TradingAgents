"""One frozen projection and static graph benchmark; no price or model inputs."""
import argparse
import base64
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import time
import urllib.parse

import pyarrow as pa
import pyarrow.parquet as pq
from tradingagents.research import ResearchRun


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


HERE = Path(__file__).resolve().parent
transport = module('graph_source_transport', HERE.parent / 'source_probe.py')
math = module('graph_count_math', HERE / 'graph_math.py')


def raw_receipt(raw):
    record = json.loads(raw)
    body = base64.b64decode(record['body_base64'], validate=True)
    if record.get('error') or record['bytes'] != len(body) or hashlib.sha256(body).hexdigest() != record['sha256']:
        raise ValueError('parent response bytes do not match retained receipt')
    return body


def block_rows(raw):
    frame = pq.read_table(io.BytesIO(raw), columns=['number', 'hash', 'parent_hash', 'timestamp', 'transaction_count'], use_threads=False)
    return zip(frame['number'].to_pylist(), frame['hash'].to_pylist(), frame['parent_hash'].to_pylist(),
               frame['timestamp'].cast(pa.int64()).to_pylist(), frame['transaction_count'].to_pylist())


def validate_plan(plan, footer):
    if len(footer) > 4 * 1024**2 or plan['object']['size'] > 2 * 1024**3:
        raise ValueError('footer/logical temporary file exceeds bound')
    metadata = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
    expected = []
    for group in range(metadata.num_row_groups):
        rg = metadata.row_group(group)
        for column in range(rg.num_columns):
            c = rg.column(column)
            if c.file_path:
                raise ValueError('external Parquet file reference')
            if c.path_in_schema not in plan['columns']: continue
            start = min(x for x in [c.dictionary_page_offset, c.data_page_offset] if x is not None and x > 0)
            expected.append({'id': f'group-{group:02d}-{c.path_in_schema}', 'group': group,
                             'column': c.path_in_schema, 'start': start,
                             'end': start + c.total_compressed_size - 1, 'bytes': c.total_compressed_size})
    if (expected != plan['ranges'] or metadata.num_rows != plan['rows']
            or [metadata.row_group(i).num_rows for i in range(metadata.num_row_groups)] != plan['groups']
            or len(expected) != plan['max_requests']
            or len(plan['columns']) * len(plan['groups']) != len(expected)
            or plan['footer_start'] != plan['object']['size'] - len(footer)):
        raise ValueError('frozen plan differs from retained footer')
    previous = 3
    for item in sorted(expected, key=lambda r: r['start']):
        if not previous < item['start'] <= item['end'] < plan['footer_start']:
            raise ValueError('overlap or invalid column bounds')
        previous = item['end']
    if sum(r['bytes'] for r in expected) > plan['max_total_bytes'] or any(r['bytes'] > plan['max_response_bytes'] for r in expected):
        raise ValueError('column request budgets exceeded')
    return metadata


class AcquiredReader(io.RawIOBase):
    """Fail if Arrow tries to decode bytes outside the acquired column intervals."""
    def __init__(self, file, ranges):
        self.file = file
        self.intervals = []
        for start, end in sorted(ranges):
            if self.intervals and start <= self.intervals[-1][1] + 1:
                self.intervals[-1][1] = max(end, self.intervals[-1][1])
            else:
                self.intervals.append([start, end])

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.file.tell()
    def seek(self, offset, whence=0): return self.file.seek(offset, whence)

    def read(self, size=-1):
        start = self.tell()
        if size < 0: raise ValueError('unbounded projection read prohibited')
        if size and not any(a <= start and start + size - 1 <= b for a, b in self.intervals):
            raise ValueError('attempt to read unacquired sparse-file bytes')
        return self.file.read(size)

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


def execute(plan, footer, blocks, publish):
    begin = time.monotonic()
    metadata = validate_plan(plan, footer)
    cap = transport.Capture(plan, publish)
    cells, group_results = [], []
    integrity = {'admitted': False, 'reason': 'column extraction incomplete'}
    graph = {'status': 'unavailable', 'reason': 'integrity not admitted'}
    timings = {}
    object_url = plan['base_url'] + urllib.parse.quote(plan['object']['key'], safe='/=')
    # This sparse temporary file contains only already-retained footer + captured columns.
    # Its raw column bodies remain recoverable from the immutable request receipts.
    with tempfile.TemporaryFile() as sparse:
        sparse.truncate(plan['object']['size'])
        sparse.write(b'PAR1')
        sparse.seek(plan['footer_start'])
        sparse.write(footer)
        for item in plan['ranges']:
            try:
                body, record = cap.get(object_url, {'Range': f'bytes={item["start"]}-{item["end"]}', 'If-Match': plan['object']['etag']})
                transport.validate_range(record, body, item['start'], item['end'], plan['object'])
                sparse.seek(item['start']); sparse.write(body)
                cells.append({'id': item['id'], 'status': 'complete'})
            except Exception as exc:
                cells.append({'id': item['id'], 'status': 'unavailable', 'reason': f'{type(exc).__name__}: {exc}'})
        for number in range(cap.count + 1, plan['max_requests'] + 1):
            for suffix in ['-intent', '']:
                publish(f'request-{number:02d}{suffix}.json', {'status': 'not_attempted', 'reason': 'source denial or prerequisite/resource failure; no retry'})
        timings['acquisition_seconds'] = time.monotonic() - begin
        if all(c['status'] == 'complete' for c in cells):
            try:
                state = math.Integrity(block_rows(blocks), plan['start_ns'], plan['end_ns'])
                sparse.flush()
                reader = AcquiredReader(sparse, [(r['start'], r['end']) for r in plan['ranges']]
                    + [(0, 3), (plan['footer_start'], plan['object']['size'] - 1)])
                parquet = pq.ParquetFile(reader, metadata=metadata, pre_buffer=False)
                if parquet.metadata.num_rows != plan['rows'] or parquet.metadata.num_row_groups != len(plan['groups']):
                    raise ValueError('reconstructed metadata differs')
                started = time.monotonic()
                for group, expected in enumerate(plan['groups']):
                    frame = parquet.read_row_group(group, columns=plan['columns'], use_threads=False)
                    if frame.num_rows != expected: raise ValueError('decoded group row count differs')
                    order = ['hash', 'block_hash', 'block_number', 'block_timestamp', 'transaction_index', 'from_address', 'to_address', 'value', 'receipt_status']
                    columns = [(frame[n].cast(pa.int64()) if n == 'block_timestamp' else frame[n]).to_pylist() for n in order]
                    before = state.rows
                    for row in zip(*columns, strict=True): state.add(row)
                    group_results.append({'group': group, 'status': 'complete', 'rows': state.rows - before,
                                          'cumulative_errors': dict(state.errors)})
                    del columns, frame
                timings['decode_integrity_pair_count_seconds'] = time.monotonic() - started
                integrity = state.finish()
                if integrity['admitted']:
                    started = time.monotonic()
                    graph = {'status': 'complete', **math.graph_features(state.pairs)}
                    timings['graph_summary_seconds'] = time.monotonic() - started
                else:
                    graph = {'status': 'unavailable', 'reason': 'row integrity gate failed; no partial graph admitted'}
            except Exception as exc:
                integrity = {'admitted': False, 'reason': f'{type(exc).__name__}: {exc}'}
    for group in range(len(plan['groups'])):
        result = next((r for r in group_results if r['group'] == group),
                      {'group': group, 'status': 'unavailable', 'reason': 'complete extraction/decoding prerequisite failed'})
        publish(f'group-{group:02d}.json', result)
    publish('integrity.json', integrity)
    publish('graph.json', graph)
    cells.append({'id': 'integrity', 'status': 'complete' if integrity['admitted'] else 'unavailable',
                  **({} if integrity['admitted'] else {'reason': integrity.get('reason', 'transaction/block integrity checks failed')})})
    cells.append({'id': 'graph', 'status': graph['status'], **({'reason': graph['reason']} if graph['status'] == 'unavailable' else {})})
    timings['elapsed_seconds'] = time.monotonic() - begin
    publish('benchmark.json', {'cells': cells, 'requests': cap.count, 'raw_response_bytes': cap.total, 'timings': timings,
                               'financial_evaluation_admitted': False, 'historical_publication_admitted': False,
                               'motifs_benchmarked': False, 'full_history_admitted': False})
    return cells


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=Path(args.root), registration='research/onchain-graph-2026-09-16/prototype/gates.json',
                           experiment='eth-graph-prototype-20260916', source=args.source) as run:
        plan = json.loads(run.read_input('plan'))
        footer = raw_receipt(run.read_input('footer'))
        blocks = raw_receipt(run.read_input('blocks'))
        run.finish(execute(plan, footer, blocks, run.write_json))


if __name__ == '__main__':
    main()

"""Day → retained-span mapping and hash-verified parquet reassembly.

`projected_table`, `AcquiredReader` and the span-verification logic are ported
from Branch A's `tradingagents/research/onchain_replication/eth_source.py`
(Codex, 2026-09/10) with simplifications; the metadata mapping follows
`research/onchain-paper-replication-2026-09-24/prepare_pilot_sources.py`.
Raw stores are read in place; nothing is fetched or copied.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tempfile
from pathlib import Path

import pyarrow.parquet as pq
import zstandard

from .config import ROOT

COLUMNS = ('hash', 'block_timestamp', 'from_address', 'to_address', 'value', 'receipt_status')
PLAN_PATH = ROOT / 'research/onchain-graph-2026-09-16/fullpanel/plan.json'
PLAN_SHA = '19f3716454216afc172aec2939a9908ba3b57921e99249951e1860b995d1d691'
# Untracked retained captures (e.g. the 2024-01-01 prototype day) exist only in the
# original data checkout; every byte is still hash-verified against tracked metadata.
RETAINED_ROOT = Path(os.environ.get('ONCHAIN_B_RETAINED_ROOT', '/home/malecada/master_thesis/TradingAgents-audit-fixes'))


def _retained(rel) -> Path:
    local = ROOT / rel
    return local if local.exists() else RETAINED_ROOT / rel


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load(path, expected=None):
    raw = Path(path).read_bytes()
    if expected is not None and digest(raw) != expected:
        raise ValueError(f'metadata hash mismatch {path}')
    return json.loads(raw)


def load_plan() -> dict:
    return _load(PLAN_PATH, PLAN_SHA)


def _span(blob, start, end, base):
    path = Path(base) / blob['path'] if base is not None else _retained(blob['path'])
    if path.stat().st_size != blob['stored_bytes']:
        raise ValueError('stored size differs')
    if blob['raw_bytes'] != end - start or blob['codec'] != 'zstd':
        raise ValueError('range framing differs')
    return {'path': str(path), 'start': start, 'end': end,
            **{k: blob[k] for k in ('raw_bytes', 'raw_sha256', 'stored_bytes', 'stored_sha256', 'codec')}}


def _ordinary(entry, day, expected_rows):
    manifest = _load(ROOT / entry['manifest']['path'], entry['manifest']['sha256'])
    if manifest['status'] != 'complete' or manifest['date'] != day:
        raise ValueError('incomplete source')
    directory = Path(entry['directory'])
    files = {f['path']: f for f in manifest['files']}

    def read(name):
        return _load(directory / name, files[name]['sha256'])

    projection = read('projection.json')
    obj = projection['object']
    requests = {}
    for name in files:
        if re.fullmatch(r'request-\d+\.json', name):
            receipt = read(name)
            if receipt['url'].endswith(obj['key']) and receipt['status'] == 206:
                a, b = map(int, receipt['request_headers']['Range'].removeprefix('bytes=').split('-'))
                if receipt['request_headers'].get('If-Match') != obj['etag'] or receipt['response_headers']['etag'] != obj['etag']:
                    raise ValueError('object ETag differs')
                requests[(a, b + 1)] = receipt
    ranges = [(r['start'], r['end'] + 1) for r in projection['ranges']] + [(projection['footer_start'], obj['size'])]
    spans = []
    for a, b in ranges:
        blob = requests[(a, b)]['blob']
        registered = files[blob['path']]
        if registered['sha256'] != blob['stored_sha256'] or registered['bytes'] != blob['stored_bytes']:
            raise ValueError('blob inventory differs')
        spans.append(_span(blob, a, b, directory))
    if sum(projection['groups']) != expected_rows:
        raise ValueError('row denominator differs')
    return {'size': obj['size'], 'spans': spans, 'object': obj}


def _special_2024_01_01(expected_rows):
    prefix = 'research/onchain-graph-2026-09-16/'
    plan = _load(_retained(prefix + 'prototype/plan.json'), '4e3716ad928b43902b111e0c4a1e849bfd7c9b35cdbc32993dcc887ddcf07800')
    # pin from tracked research/onchain-graph-2026-09-16/pilot/partial-artifacts-import.json
    receipt = _load(_retained(prefix + 'pilot/artifacts/results/context-2024-01-01.json'),
                    '86be76dbe2aeeb33eb158562679df0dbdcc250a4d280429b271edcd6995a5d52')
    if plan['rows'] != expected_rows:
        raise ValueError('context rows differ')
    spans = [_span(b, r['start'], r['end'] + 1, None)
             for r, b in zip(plan['ranges'], receipt['benchmark']['blobs'], strict=True)]
    footer_path = _retained('research_runs/eth-graph-source-20260916/outputs/request-11.json')
    footer = _load(footer_path, '4b568e9995a4d7cb234c6103dda1b4be55389b49e4252c6e8b65c8e007dec16e')
    spans.append({'path': str(footer_path), 'start': plan['footer_start'], 'end': plan['object']['size'],
                  'raw_bytes': footer['bytes'], 'raw_sha256': footer['sha256'],
                  'stored_bytes': footer_path.stat().st_size, 'stored_sha256': digest(footer_path.read_bytes()),
                  'codec': 'receipt_base64'})
    return {'size': plan['object']['size'], 'spans': spans, 'object': plan['object']}


def day_manifest(plan: dict, day: str) -> dict:
    rows = plan['expected_rows'][day]
    return _special_2024_01_01(rows) if day == '2024-01-01' else _ordinary(plan['captures'][day], day, rows)


class AcquiredReader(io.RawIOBase):
    """Random-access view over a sparse temp file; reads outside acquired intervals are errors."""

    def __init__(self, file, intervals, size):
        self.file, self.intervals, self.size = file, intervals, size

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.file.tell()

    def seek(self, offset, whence=0):
        return self.file.seek(offset, whence)

    def read(self, size=-1):
        pos = self.tell()
        end = self.size if size is None or size < 0 else min(self.size, pos + size)
        if pos < end and not any(a <= pos and end <= b for a, b in self.intervals):
            raise ValueError(f'read outside acquired ranges [{pos},{end})')
        return self.file.read(end - pos)

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


def _decompress(span, stored):
    if span['codec'] == 'zstd':
        n = span['end'] - span['start']
        if zstandard.frame_content_size(stored) != n:
            raise ValueError('range decompression length')
        return zstandard.ZstdDecompressor().decompress(stored, max_output_size=n, allow_extra_data=False)
    if span['codec'] == 'receipt_base64':
        import base64
        receipt = json.loads(stored)
        raw = base64.b64decode(receipt['body_base64'], validate=True)
        if len(raw) != span['end'] - span['start'] or receipt['sha256'] != span['raw_sha256']:
            raise ValueError('receipt body framing')
        return raw
    raise ValueError('unregistered range codec')


def projected_table(manifest: dict, scratch: Path, columns=COLUMNS):
    size = manifest['size']
    if not isinstance(size, int) or not 12 <= size <= 8 * 1024 ** 3:
        raise ValueError('logical parquet size limit')
    intervals = []
    with tempfile.TemporaryFile(dir=scratch) as file:
        file.truncate(size)
        for span in sorted(manifest['spans'], key=lambda s: s['start']):
            a, b = span['start'], span['end']
            if not 0 <= a < b <= size or (intervals and a < intervals[-1][1]):
                raise ValueError('invalid/overlapping ranges')
            stored = Path(span['path']).read_bytes()
            if len(stored) != span['stored_bytes'] or digest(stored) != span['stored_sha256']:
                raise ValueError('stored range hash')
            raw = _decompress(span, stored)
            if digest(raw) != span['raw_sha256']:
                raise ValueError('raw range hash')
            file.seek(a)
            file.write(raw)
            if intervals and intervals[-1][1] == a:
                intervals[-1] = (intervals[-1][0], b)      # contiguous spans form one readable interval
            else:
                intervals.append((a, b))
        file.flush()
        file.seek(size - 8)
        trailer = file.read(8)
        if trailer[4:] != b'PAR1':
            raise ValueError('invalid parquet trailer')
        length = int.from_bytes(trailer[:4], 'little')
        file.seek(size - length - 8)
        footer = file.read(length + 8)
        metadata = pq.read_metadata(io.BytesIO(b'PAR1' + footer))
        reader = AcquiredReader(file, intervals, size)
        reader.seek(0)
        parquet = pq.ParquetFile(reader, metadata=metadata, pre_buffer=False)
        return parquet.read(columns=list(columns), use_threads=False)


def read_day(manifest: dict, scratch: Path, columns=COLUMNS):
    return projected_table(manifest, scratch, columns)

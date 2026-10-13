"""One UTC day of ETH transactions: streamed from the AWS public bucket, or read from
Branch B's retained hash-verified spans for 2022–2024. Only six columns are read;
nothing raw is written to disk."""
from __future__ import annotations

import time
import urllib.request

import numpy as np
import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq

from . import config

COLUMNS = ('hash', 'block_timestamp', 'from_address', 'to_address', 'value', 'receipt_status')


class DayUnavailable(RuntimeError):
    def __init__(self, day, errors):
        super().__init__(f'{day} unavailable after {len(errors)} attempts: {errors[-1] if errors else ""}')
        self.day, self.errors = day, errors


def https_head(url, timeout=30):
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'onchain-b2-research'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        size = r.headers.get('Content-Length')
        return {'etag': r.headers.get('ETag'), 'size': int(size) if size is not None else None}


def check_timestamps(table, day):
    start = np.datetime64(day, 'ns')
    ts = table.column('block_timestamp').to_numpy().astype('datetime64[ns]')
    if len(ts) and ((ts < start).any() or (ts >= start + np.timedelta64(1, 'D')).any()):
        raise ValueError(f'block_timestamp outside {day}')


def read_s3_day(day, *, filesystem, root, https, head_fn):
    prefix = config.load()['s3']['prefix']
    infos = [f for f in filesystem.get_file_info(pafs.FileSelector(f'{root}/{prefix}{day}'))
             if f.path.endswith('.parquet')]
    if not infos:
        raise FileNotFoundError(f'no parquet parts for {day}')
    tables, files = [], []
    for info in sorted(infos, key=lambda f: f.path):
        with filesystem.open_input_file(info.path) as fh:
            t = pq.ParquetFile(fh).read(columns=list(COLUMNS))
        key = info.path[len(root):].lstrip('/')
        head = head_fn(https + key)
        if head.get('size') is not None and head['size'] != info.size:
            raise ValueError(f'size mismatch for {key}')
        files.append({'key': key, 'size': info.size, 'etag': head.get('etag'), 'rows': t.num_rows})
        tables.append(t.select(list(COLUMNS)))
    table = pa.concat_tables(tables)
    check_timestamps(table, day)
    return table, {'day': day, 'source': 's3', 'rows': table.num_rows, 'files': files}


def read_local_day(day, scratch):
    from ..onchain_b import sources
    manifest = sources.day_manifest(sources.load_plan(), day)
    table = sources.read_day(manifest, scratch, sources.COLUMNS)
    check_timestamps(table, day)
    return table, {'day': day, 'source': 'local', 'rows': table.num_rows, 'object': manifest['object'].get('key')}


def _s3(cfg):
    return pafs.S3FileSystem(anonymous=True, region=cfg['region'])


def read_day(day, *, scratch, filesystem=None, head_fn=None, sleep=time.sleep, cfg=None):
    c = cfg or config.load()
    s = c['s3']
    local = c['local_span_days']['first'] <= day <= c['local_span_days']['last']

    def once():
        if local:
            return read_local_day(day, scratch)
        return read_s3_day(day, filesystem=filesystem or _s3(s), root=s['bucket'], https=s['https'],
                           head_fn=head_fn or https_head)

    waits, errors = list(s['retries']), []
    for attempt in range(len(waits) + 1):
        try:
            return once()
        except Exception as e:        # network, decode or integrity failure: retry, then mark unavailable
            errors.append(repr(e))
            if attempt < len(waits):
                sleep(waits[attempt])
    raise DayUnavailable(day, errors)
"""First fixed raw graph tranche. Metadata validation only; no graph or prices."""
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import urllib.parse

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('matched_capture_day', HERE.parent/'pilot/day.py')
day = importlib.util.module_from_spec(spec)
spec.loader.exec_module(day)
storage = day.storage
DATES = tuple(f'2022-01-{d:02d}' for d in range(1, 8))
DISK_FLOOR = 20 * 1024**3


def capture_graph(directory, inventory, plan, *, disk_usage=shutil.disk_usage):
    """Capture exactly seven selected-column days; preserve every unavailable cell.

    Each day has an independent inherited 272 MiB/291 request ceiling. Source
    denial or a low-space check stops all subsequent acquisition. No retry or
    implicit continuation. A complete day means raw ranges checked, not numerical
    transaction integrity, boundary admission or valid motif features.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    results = []
    stopped = None
    for date in DATES:
        own = directory / date
        own.mkdir()
        limits = dict(plan['limits'])
        limits.update(max_requests=291, max_total_bytes=272*1024**2)
        capture = storage.BinaryCapture(dict(limits, base_url=plan['base_url']), own)
        result = dict(date=date, status='unavailable', reason=None)
        try:
            if stopped:
                raise ValueError(stopped)
            def fetch(obj, first=None, last=None):
                nonlocal stopped
                # Reserve worst-case daily raw bytes plus temporary compression,
                # beyond the floor; current free space is rechecked per request.
                if disk_usage(own).free < DISK_FLOOR + 2*272*1024**2:
                    stopped = 'disk reserve reached; no automatic retry'
                    raise ValueError(stopped)
                url = plan['base_url'] + urllib.parse.quote(obj['key'], safe='/=')
                headers = {'If-Match': obj['etag']}
                if first is not None:
                    headers['Range'] = f'bytes={first}-{last}'
                body, receipt = capture.get(url, headers)
                return day.checked_response(body, receipt, obj, first, last)
            blocks = day.object_for(inventory, 'blocks', date)
            if not 12 <= blocks['size'] <= limits['max_block_bytes']:
                raise ValueError('block size exceeds fixed bound')
            day.validate_blocks(fetch(blocks), plan['block_required_types'])
            obj = day.object_for(inventory, 'transactions', date)
            if not 12 <= obj['size'] <= limits['max_logical_bytes']:
                raise ValueError('transaction object exceeds fixed bound')
            tail = fetch(obj, obj['size']-8, obj['size']-1)
            size = struct.unpack('<I', tail[:4])[0]
            if tail[4:] != b'PAR1' or not 0 < size <= limits['max_footer_bytes'] or size+12 > obj['size']:
                raise ValueError('invalid footer trailer')
            footer = fetch(obj, obj['size']-size-8, obj['size']-1)
            if footer[-8:] != tail:
                raise ValueError('footer changed')
            projection = day.numeric.projection(obj, footer, limits, plan['required_types'])
            storage.atomic_json(own/'projection.json', projection)
            for span in projection['ranges']:
                fetch(obj, span['start'], span['end'])
            result.update(status='complete', projected_rows=projection['rows'],
                          selected_bytes=sum(r['bytes'] for r in projection['ranges']),
                          numerical_integrity_admitted=False)
        except Exception as exc:
            result['reason'] = f'{type(exc).__name__}: {exc}'
        if capture.denied:
            stopped = 'source denied; no subsequent acquisition'
        result.update(requests=capture.count, received_bytes=capture.total,
                      denied=capture.denied, stopped=stopped)
        storage.atomic_json(own/'result.json', result)
        results.append(result)
        print(json.dumps(dict(phase='graph_raw_capture', **result)), flush=True)
    summary = dict(days=results, requests=sum(r['requests'] for r in results),
                   received_bytes=sum(r['received_bytes'] for r in results),
                   graph_integrity_or_motifs_admitted=False)
    storage.atomic_json(directory/'summary.json', summary)
    return summary

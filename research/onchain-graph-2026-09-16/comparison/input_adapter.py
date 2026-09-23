"""Pure adapters for the fixed retrospective comparison; no empirical entry point.

Call only inside a subsequently registered run after binding all input bytes,
source receipts and independent review. Assumed clocks are explicitly separate
from verified historical availability. No network, raw-store writes or fitting.
"""
import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import zipfile

import pandas as pd

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('matched_spot_schema', HERE/'spot_capture.py')
spot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spot)
MONTHS = spot.MONTHS
GRAPH_EXPERIMENT = 'eth-full-history-feature-panel-resume2-20260922'
COUNTS = ('events', 'nodes', 'directed_pairs', 'stars', 'dyads', 'triangles',
          'overlap_nodes', 'nonzero_nodes')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_graph_review(panel_raw, terminal_raw, report, guard, *, source):
    """Check content linkage and successful review, not lifecycle authorization.

    The consuming registration must bind the report, guard, terminal and source.
    A matching self-supplied report alone is not independent evidence.
    """
    require(report.get('passed') is True and report.get('passing_full_panel') is True,
            'passing full-panel independent review required')
    terminal = json.loads(terminal_raw)
    require(terminal.get('status') == 'complete' and terminal.get('experiment_id') == GRAPH_EXPERIMENT,
            'expected completed graph identity required')
    require(terminal.get('source') == report.get('source') == source, 'graph source mismatch')
    require(hashlib.sha256(terminal_raw).hexdigest() == report.get('terminal_sha256'),
            'review terminal hash mismatch')
    digest = hashlib.sha256(panel_raw).hexdigest()
    require(terminal.get('output_sha256', {}).get('panel.json') == digest
            and report.get('output_sha256', {}).get('panel.json') == digest,
            'review panel hash mismatch')
    require(guard.get('phase') == 'complete' and type(guard.get('child_exit_code')) is int
            and guard['child_exit_code'] == 0 and guard.get('limit_reason') is None
            and guard.get('cleanup_verified') is True, 'clean review guard exit required')
    events = guard.get('memory_events', {})
    require(all(type(events.get(k)) is int and events[k] == 0
                for k in ('oom', 'oom_kill', 'oom_group_kill')), 'known zero review OOM events required')
    command = guard.get('command', [])
    require(isinstance(command, list) and len(command) >= 5
            and Path(command[2]).name == 'check_final.py'
            and command.count('--source') == 1
            and command[command.index('--source')+1:command.index('--source')+2] == [source],
            'review checker command/source mismatch')


def _assumed(frame):
    frame.attrs.update(availability_basis='protocol_assumption',
                       historical_availability_verified=False)
    return frame


def spot_month(month, zip_raw, checksum_raw):
    """Decode only admitted 2021-12-01 through 2025-01-01 price rows.

    Validate the entire archive calendar first, including the 2025 timestamp
    unit change. Later January 2025 prices remain uninterpreted.
    """
    meta = spot.validate_month(month, zip_raw, checksum_raw)
    with zipfile.ZipFile(io.BytesIO(zip_raw)) as archive:
        csv_raw = archive.read(meta['csv_member'])
    rows = []
    for row in csv.reader(io.StringIO(csv_raw.decode('utf-8')), strict=True):
        day = pd.to_datetime(int(row[0]), unit=meta['timestamp_unit'], utc=True)
        if not pd.Timestamp('2021-12-01T00:00:00Z') <= day <= pd.Timestamp('2025-01-01T00:00:00Z'):
            continue
        opening, high, low, close, volume, quote_volume = [float(row[i]) for i in (1, 2, 3, 4, 5, 7)]
        require(all(math.isfinite(v) and v > 0 for v in (opening, high, low, close)),
                'finite positive spot prices required')
        require(low <= min(opening, close) <= max(opening, close) <= high, 'spot OHLC range mismatch')
        require(all(math.isfinite(v) and v >= 0 for v in (volume, quote_volume)),
                'finite nonnegative spot volumes required')
        rows.append(dict(day=day, open=opening, close=close, quote_volume=quote_volume,
                         available_at=day+pd.Timedelta(days=1, minutes=5)))
    return _assumed(pd.DataFrame(rows))


def market_rows(month_bytes):
    """Require the exact already captured cohort; no partial-market fallback."""
    require(set(month_bytes) == set(MONTHS), 'all 38 captured spot months required')
    frame = pd.concat([spot_month(m, *month_bytes[m]) for m in MONTHS], ignore_index=True)
    expected = pd.date_range('2021-12-01', '2025-01-01', freq='D', tz='UTC')
    require(pd.DatetimeIndex(frame.day).equals(expected), 'spot decision/warmup calendar mismatch')
    return _assumed(frame)


def graph_rows(panel):
    """Convert reviewed summary counts and retain every graph exclusion.

    Input days must be ordered and unique. The future consuming gate must also
    bind the exact 1096-day calendar and two registered boundary exclusions.
    """
    require(panel.get('global_uniqueness_admitted') is True, 'global graph identity admission required')
    rows, exclusions, previous = [], [], None
    for item in panel['days']:
        day = pd.Timestamp(item['day'], tz='UTC')
        require(not pd.isna(day) and day == day.floor('D') and (previous is None or day > previous),
                'unique ordered midnight graph days required')
        previous = day
        if item.get('source_admitted') is not True or item.get('graph_admitted') is not True:
            require(bool(item.get('reason')), 'unavailable graph day requires a reason')
            exclusions.append(dict(day=item['day'], reason=item['reason']))
            continue
        require(item.get('source_status') == item.get('graph_status') == 'complete',
                'admitted graph/source status mismatch')
        counts = {k: item[k] for k in COUNTS}
        require(all(type(v) is int and 0 <= v < 2**53 for v in counts.values()),
                'exact nonnegative integer graph counts required')
        local = item['local40']
        roles = local['local40_sums']
        require(len(roles) == 40 and all(type(v) is int and 0 <= v < 2**53 for v in roles),
                '40 exact nonnegative integer role sums required')
        require(sum(roles[24:32]) % 2 == 0 and sum(roles[32:]) % 3 == 0,
                'role conservation divisibility failed')
        require((sum(roles[:24]), sum(roles[24:32])//2, sum(roles[32:])//3)
                == (counts['stars'], counts['dyads'], counts['triangles']), 'motif sums differ')
        require(local['unique_occurrences'] == counts['stars']+counts['dyads']+counts['triangles']
                and local['overlap_node_count'] == counts['overlap_nodes']
                and local['nonzero_nodes'] == counts['nonzero_nodes'], 'local40 aggregate mismatch')
        require(counts['nodes'] <= counts['overlap_nodes']
                and counts['nonzero_nodes'] <= counts['overlap_nodes']
                and counts['directed_pairs'] <= counts['events'], 'inconsistent graph denominators')
        require(counts['events'] != 0 or all(counts[k] == 0 for k in
                ('nodes', 'directed_pairs', 'stars', 'dyads', 'triangles')), 'motifs without events')
        assumed = day+pd.Timedelta(days=2)
        if item.get('available_at') is not None:
            actual = pd.Timestamp(item['available_at'])
            require(not pd.isna(actual) and actual.tzinfo is not None, 'invalid supplied graph availability')
            assumed = max(assumed, actual.tz_convert('UTC'))
        rows.append(dict(day=day, available_at=assumed, **counts))
    require(bool(rows), 'no admitted graph days')
    return _assumed(pd.DataFrame(rows)), exclusions

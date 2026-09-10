"""Read immutable public funding snapshots; never query a provider or legacy store.

Query exhaustion and historical economic completeness are separate claims. Daily
admission deliberately retains the paper book's qualified cadence inference.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


class FundingSnapshotError(ValueError):
    """A configured snapshot cannot establish its declared input provenance."""


def _require(condition, reason):
    if not condition:
        raise FundingSnapshotError(reason)


def _time(value, label):
    try:
        stamp = pd.Timestamp(value)
        _require(not pd.isna(stamp) and stamp.tzinfo is not None, f'{label}: timezone-aware UTC time required')
        return stamp.tz_convert('UTC')
    except (TypeError, ValueError) as exc:
        raise FundingSnapshotError(f'{label}: invalid timestamp') from exc


def _integer(value):
    return type(value) is int


def _file(root, relative, digest):
    _require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), 'invalid snapshot file path')
    path = (root / relative).resolve()
    _require(path.is_relative_to(root), 'snapshot file escapes its directory')
    _require(isinstance(digest, str) and len(digest) == 64, 'missing snapshot file hash')
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise FundingSnapshotError(f'missing or unreadable snapshot file: {relative}') from exc
    _require(hashlib.sha256(raw).hexdigest() == digest, f'snapshot file hash mismatch: {relative}')
    return path, raw


def _json(raw, label):
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise FundingSnapshotError(f'invalid JSON: {label}') from exc


def _number(value, label, *, positive=False):
    try:
        _require(not isinstance(value, bool), f'{label}: boolean is not numeric')
        result = float(value)
        _require(math.isfinite(result) and (not positive or result > 0), f'{label}: nonfinite or invalid value')
        return result
    except (ValueError, TypeError, OverflowError) as exc:
        raise FundingSnapshotError(f'{label}: invalid number') from exc


def _receipts(root, manifest, started, completed):
    receipts = manifest.get('requests')
    _require(isinstance(receipts, list) and receipts, 'request receipts unavailable')
    out, contracts = [], {}
    endpoints = {'/fapi/v1/time', '/fapi/v1/exchangeInfo', '/fapi/v1/fundingInfo',
                 '/fapi/v1/premiumIndex', '/fapi/v1/fundingRate'}
    for receipt in receipts:
        _require(isinstance(receipt, dict) and receipt.get('endpoint') in endpoints and
                 isinstance(receipt.get('params'), dict), 'invalid public request receipt')
        received = _time(receipt.get('received_utc'), 'request received_utc')
        _require(started <= received <= completed, 'request availability outside snapshot acquisition window')
        body = None
        if receipt.get('body_file') is not None:
            _, raw = _file(root, receipt['body_file'], receipt.get('body_sha256'))
            # Error bodies may be HTML; preserve/hash them without treating them as data.
            if receipt.get('status') == 200 and receipt.get('error') is None:
                body = _json(raw, receipt['body_file'])
        elif receipt.get('status') == 200 and receipt.get('error') is None:
            raise FundingSnapshotError('successful request has no raw receipt')
        if receipt['endpoint'] == '/fapi/v1/exchangeInfo' and body is not None:
            _require(isinstance(body, dict) and isinstance(body.get('symbols'), list), 'exchange identity receipt malformed')
            for contract in body['symbols']:
                _require(isinstance(contract, dict) and isinstance(contract.get('symbol'), str), 'malformed exchange contract')
                symbol = contract['symbol']
                _require(symbol not in contracts or contracts[symbol] == contract, 'conflicting contract identity receipts')
                contracts[symbol] = contract
        out.append((receipt, received, body))
    return out, contracts


def _metadata(manifest, receipts, contracts):
    """Verify current acquisition metadata without inferring historical schedules."""
    selected = manifest['requested_symbols']
    observations = manifest.get('schedule_observations')
    _require(isinstance(observations, list) and len(observations) == 2, 'current schedule receipt references unavailable')
    references = {o.get('endpoint'): o for o in observations if isinstance(o, dict)}
    for endpoint in ('/fapi/v1/time', '/fapi/v1/exchangeInfo', '/fapi/v1/fundingInfo', '/fapi/v1/premiumIndex'):
        successful = [(i, received, body) for i, (receipt, received, body) in enumerate(receipts)
                      if receipt['endpoint'] == endpoint and body is not None]
        _require(len(successful) == 1, f'{endpoint}: required unique successful metadata receipt unavailable')
        i, received, body = successful[0]
        received_ms = int(received.timestamp() * 1000)
        if endpoint.endswith('/time'):
            stamp = body.get('serverTime') if isinstance(body, dict) else None
            _require(_integer(stamp) and stamp == manifest['window']['end_ms'] and abs(stamp-received_ms) <= 300_000,
                     'exchange time receipt does not establish capture cutoff')
        elif endpoint.endswith('/exchangeInfo'):
            continue  # Raw identities were checked while reading receipts.
        else:
            ref = references.get(endpoint)
            _require(isinstance(body, list) and isinstance(ref, dict) and ref.get('receipt_index') == i and
                     ref.get('historical_schedule') is False and ref.get('rows') == len(body) and
                     _time(ref.get('observed_at'), 'schedule observation') == received,
                     'current schedule provenance reference mismatch')
            seen = set()
            for item in body:
                _require(isinstance(item, dict) and isinstance(item.get('symbol'), str) and item['symbol'] not in seen,
                         'malformed or duplicate current schedule identity')
                symbol = item['symbol']; seen.add(symbol)
                if endpoint.endswith('/fundingInfo'):
                    interval = item.get('fundingIntervalHours')
                    _require(_integer(interval) and interval in (1, 2, 4, 8) and
                             _number(item.get('adjustedFundingRateFloor'), 'funding floor') <=
                             _number(item.get('adjustedFundingRateCap'), 'funding cap'), 'invalid current funding interval/limits')
                elif symbol in selected and contracts.get(symbol, {}).get('status') == 'TRADING':
                    stamp, next_time = item.get('time'), item.get('nextFundingTime')
                    _require(_integer(stamp) and _integer(next_time) and next_time > stamp and
                             0 <= received_ms-stamp <= 300_000, 'current funding schedule timestamp missing or stale')
            if endpoint.endswith('/premiumIndex'):
                active = {s for s in selected if contracts.get(s, {}).get('status') == 'TRADING' and
                          contracts[s].get('contractType') == 'PERPETUAL' and contracts[s].get('quoteAsset') == 'USDT' and
                          contracts[s].get('marginAsset') == 'USDT'}
                _require(active <= seen, 'current schedule omits requested active instruments')


def _query_events(symbol, entry, receipts):
    """Verify history pagination and each full page's complete final-time group."""
    start, end = entry.get('query_start_ms'), entry.get('query_end_ms')
    _require(_integer(start) and _integer(end) and start <= end and entry.get('query_complete') is True,
             f'{symbol}: bounded completed query unavailable')
    cursor, exhausted, values, pending_boundary = start, False, {}, None
    crypto = entry['contract'].get('underlyingType') == 'COIN'

    def decode(event, lower, upper):
        _require(isinstance(event, dict) and event.get('symbol') == symbol and _integer(event.get('fundingTime')),
                 f'{symbol}: funding event identity/timestamp invalid')
        stamp = event['fundingTime']
        _require(lower <= stamp <= upper, f'{symbol}: funding event outside query page')
        rate_type = event.get('rateType')
        if rate_type is None and crypto:
            rate_type = 'unspecified_crypto'
        _require(rate_type in ('Regular', 'unspecified_crypto') and
                 (rate_type != 'unspecified_crypto' or crypto), f'{symbol}: ambiguous event rate type')
        return stamp, (_number(event.get('fundingRate'), 'fundingRate'),
                       _number(event.get('markPrice'), 'markPrice', positive=True), rate_type)

    for receipt, received, body in receipts:
        params = receipt['params']
        if receipt['endpoint'] != '/fapi/v1/fundingRate' or params.get('symbol') != symbol:
            continue
        if body is None:
            continue  # A failed attempt may have a later successful retry.
        purpose = receipt.get('purpose') or 'history'
        if purpose == 'boundary_check':
            _require(pending_boundary is not None and params.get('startTime') == pending_boundary and
                     params.get('endTime') == pending_boundary and params.get('limit') == 1000 and
                     isinstance(body, list) and 0 < len(body) < 1000,
                     f'{symbol}: incomplete or unexpected boundary group evidence')
            for event in body:
                stamp, value = decode(event, pending_boundary, pending_boundary)
                _require(value == values[stamp][:3], f'{symbol}: boundary group conflicts with funding history')
            pending_boundary = None
            continue
        _require(purpose == 'history' and pending_boundary is None and not exhausted,
                 f'{symbol}: missing boundary evidence or unexpected history page')
        _require(params.get('startTime') == cursor and params.get('endTime') == end and
                 _integer(params.get('limit')) and 1 <= params['limit'] <= 1000,
                 f'{symbol}: request page coverage is discontinuous')
        _require(isinstance(body, list) and len(body) <= params['limit'], f'{symbol}: malformed funding page')
        times = []
        for event in body:
            stamp, value = decode(event, cursor, end)
            times.append(stamp)
            _require(stamp not in values or values[stamp][:3] == value, f'{symbol}: conflicting raw funding events')
            values.setdefault(stamp, (*value, received))
        _require(times == sorted(times), f'{symbol}: unordered funding page')
        if len(body) == params['limit']:
            pending_boundary = times[-1]
        exhausted = not times or len(body) < params['limit'] or times[-1] >= end
        if not exhausted:
            _require(times[-1] + 1 > cursor, f'{symbol}: query made no progress')
            cursor = times[-1] + 1
    _require(exhausted and pending_boundary is None, f'{symbol}: query exhaustion lacks successful page/boundary evidence')
    return values


def _events(root, symbol, entry, receipts, contracts, window, started, completed):
    contract = entry.get('contract')
    _require(isinstance(contract, dict) and contract.get('symbol') == symbol and
             contract.get('contractType') == 'PERPETUAL' and contract.get('quoteAsset') == 'USDT' and
             contract.get('marginAsset') == 'USDT' and contract.get('status') == 'TRADING' and
             contracts.get(symbol) == contract,
             f'{symbol}: unsupported or unproven contract identity')
    onboard = contract.get('onboardDate')
    _require(_integer(onboard) and 0 < onboard <= window['end_ms'] and
             _integer(entry.get('query_start_ms')) and _integer(entry.get('query_end_ms')) and
             entry['query_start_ms'] == max(window['start_ms'], onboard) and entry['query_end_ms'] == window['end_ms'],
             f'{symbol}: query does not match window and original contract onboarding')
    raw_values = _query_events(symbol, entry, receipts)
    path, _ = _file(root, entry.get('file'), entry.get('sha256'))
    try:
        frame = pd.read_parquet(path)
    except (OSError, ValueError) as exc:
        raise FundingSnapshotError(f'{symbol}: invalid event Parquet') from exc
    _require(isinstance(frame.index, pd.DatetimeIndex) and frame.index.tz is not None and
             str(frame.index.tz) == 'UTC' and frame.index.is_unique and frame.index.is_monotonic_increasing and
             not frame.index.hasnans, f'{symbol}: invalid UTC event clock')
    _require(frame.columns.is_unique and {'fundingRate', 'markPrice', 'rateType', 'observed_at'} <= set(frame.columns),
             f'{symbol}: missing normalized event fields')
    _require(_integer(entry.get('row_count')) and entry['row_count'] == len(frame) == len(raw_values),
             f'{symbol}: event count differs from receipt/manifest')
    times = [int(t.value // 1_000_000) for t in frame.index]
    _require(all(t.value % 1_000_000 == 0 for t in frame.index) and times == sorted(raw_values),
             f'{symbol}: normalized timestamps differ from raw events')
    _require(entry.get('first_event_ms') == (times[0] if times else None) and
             entry.get('last_event_ms') == (times[-1] if times else None), f'{symbol}: event bounds mismatch')
    for stamp, (_, row) in zip(times, frame.iterrows()):
        observed = _time(row['observed_at'], f'{symbol} observed_at')
        value = (_number(row['fundingRate'], 'fundingRate'), _number(row['markPrice'], 'markPrice', positive=True), row['rateType'])
        _require(value == raw_values[stamp][:3] and observed == raw_values[stamp][3] and started <= observed <= completed,
                 f'{symbol}: normalized event/availability differs from first raw receipt')
    return frame


def _hour_labels(index):
    """Derived comparison clock under the prospective 7654889 amendment."""
    labels = index.floor('h')
    offsets = ((index - labels).asi8 // 1_000_000).astype(int)
    off_grid = int((offsets > 1000).sum())
    duplicate_mask = labels.duplicated(keep=False)
    duplicate_hours = int(labels[duplicate_mask].nunique())
    reason = ('raw timestamps outside the prospective 0..1000ms hourly tolerance' if off_grid else
              'distinct raw timestamps map to the same comparison hour' if duplicate_hours else None)
    evidence = dict(policy_version='utc_hour_forward_1s_v1', tolerance_ms=1000,
                    qualification='Prospective engineering tolerance; not a provider schedule guarantee. Raw daily membership is unchanged.',
                    max_offset_ms=int(offsets.max()) if len(offsets) else None,
                    off_grid_events=off_grid, duplicate_grid_hours=duplicate_hours,
                    duplicate_grid_events=int(duplicate_mask.sum()),
                    status='aligned' if reason is None else 'unavailable', reason=reason)
    return labels, evidence


def load_funding_snapshot(snapshot_dir, symbols, index, *, measurement_time=None):
    """Return qualified daily rates and full source/availability denominators.

    A valid partial capture can supply its captured names. Missing/quarantined
    names remain NaN; a false captured claim or corrupt provenance rejects the
    configured snapshot entirely. No other data source is consulted.
    """
    root = Path(snapshot_dir).resolve()
    try:
        manifest_raw = (root / 'manifest.json').read_bytes()
    except OSError as exc:
        raise FundingSnapshotError('configured funding snapshot manifest unavailable') from exc
    manifest = _json(manifest_raw, 'manifest.json')
    _require(isinstance(manifest, dict) and type(manifest.get('schema_version')) is int and manifest['schema_version'] == 1 and
             manifest.get('kind') == 'binance-usdm-funding-capture', 'unsupported funding snapshot schema')
    source = manifest.get('source')
    _require(isinstance(source, dict) and source.get('venue') == 'Binance USD-M' and
             source.get('base_url') == 'https://fapi.binance.com', 'unsupported funding source')
    _require(isinstance(source.get('git_commit'), str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', source['git_commit']) and
             isinstance(source.get('collector_sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', source['collector_sha256']),
             'declared collector code identity unavailable or invalid')
    _require(manifest.get('status') in {'captured', 'partial'}, 'funding snapshot did not capture usable data')
    now = _time(measurement_time if measurement_time is not None else pd.Timestamp.now(tz='UTC'), 'measurement_time')
    started, completed = _time(manifest.get('started_utc'), 'started_utc'), _time(manifest.get('completed_utc'), 'completed_utc')
    _require(started <= completed <= now, 'funding snapshot not yet available at measurement time')
    window = manifest.get('window')
    _require(isinstance(window, dict) and all(_integer(window.get(k)) for k in ('start_ms', 'end_ms')) and
             window['start_ms'] <= window['end_ms'] <= int(now.timestamp() * 1000), 'invalid snapshot query window')
    requested, entries = manifest.get('requested_symbols'), manifest.get('instruments')
    _require(isinstance(requested, list) and all(isinstance(s, str) and s for s in requested) and
             len(set(requested)) == len(requested) and isinstance(entries, dict) and set(entries) == set(requested),
             'missing or duplicate requested-symbol denominator')
    index = pd.DatetimeIndex(index)
    _require(index.tz is not None and str(index.tz) == 'UTC' and index.is_unique and index.is_monotonic_increasing and
             not index.hasnans and index.equals(index.normalize()), 'measurement days must be unique sorted UTC midnights')
    symbols = list(symbols)
    _require(len(set(symbols)) == len(symbols), 'duplicate requested consumer symbols')
    receipts, contracts = _receipts(root, manifest, started, completed)
    _metadata(manifest, receipts, contracts)
    frames = {}
    for symbol, entry in entries.items():
        _require(isinstance(entry, dict) and entry.get('status') in {'captured', 'unavailable', 'quarantined'},
                 f'{symbol}: invalid capture status')
        if entry['status'] == 'captured':
            frames[symbol] = _events(root, symbol, entry, receipts, contracts, window, started, completed)
        else:
            _require(isinstance(entry.get('reason'), str) and entry['reason'], f'{symbol}: unavailable capture has no reason')
            _require(manifest['status'] == 'partial', 'captured snapshot omits unavailable instrument denominator')
    daily = pd.DataFrame(np.nan, index=index, columns=symbols)
    coverage = dict(method='snapshot_observed_cadence_inference',
        alignment_policy_version='utc_hour_forward_1s_v1',
        qualification='Query exhaustion is verified; historical schedules are unavailable. Prior 7d minimum-spacing inference can miss unknown faster events. Daily funding uses opening notionals, not event-marked account debits.',
        snapshot={'path': str(root), 'sha256': hashlib.sha256(manifest_raw).hexdigest(),
                  'started_utc': manifest['started_utc'], 'completed_utc': manifest['completed_utc'],
                  'measurement_utc': now.isoformat(), 'status': manifest['status'], 'window': window,
                  'source': dict(source)},
        requested_symbols=requested, capture_statuses={s: {'status': e['status'], 'reason': e.get('reason')} for s, e in entries.items()},
        symbols={})
    for symbol in symbols:
        entry = entries.get(symbol, {'status': 'unavailable', 'reason': 'symbol not requested in snapshot'})
        info = dict(status=entry['status'], reason=entry.get('reason'), covered_days=0, requested_days=len(index),
                    query_complete=entry.get('query_complete') is True, days={})
        coverage['symbols'][symbol] = info
        if symbol not in frames:
            continue
        rates = frames[symbol]['fundingRate'].astype(float)
        labels, alignment = _hour_labels(rates.index)
        info['alignment'] = alignment
        for day in index:
            boundary = day + pd.Timedelta(days=1)
            reason = 'complete regular event grid and following captured boundary unavailable'
            if alignment['reason'] is not None:
                reason = alignment['reason']
            elif entry['query_start_ms'] <= int(day.timestamp()*1000) and entry['query_end_ms'] >= int(boundary.timestamp()*1000):
                prior = labels[(rates.index >= day-pd.Timedelta(days=7)) & (rates.index < day)]
                if len(prior) >= 3:
                    delta = prior.to_series().diff().dropna().min()
                    if delta.total_seconds()/3600 in (1, 2, 4, 8):
                        expected = pd.date_range(day, boundary, freq=delta)
                        observed_labels = labels[(labels >= day) & (labels <= boundary)]
                        boundary_events = rates.index[labels == boundary]
                        if (observed_labels.equals(expected) and len(boundary_events) == 1 and
                                int(boundary_events[0].value//1_000_000) <= entry['query_end_ms']):
                            # Economic membership is always the unmodified raw interval.
                            daily.loc[day, symbol] = float(rates.loc[(rates.index >= day) & (rates.index < boundary)].sum())
                            reason = None
            else:
                reason = 'requested day or following boundary outside exhausted query window'
            info['days'][day.isoformat()] = {'status': 'admitted_inferred' if reason is None else 'unavailable', 'reason': reason}
        info['covered_days'] = int(daily[symbol].notna().sum())
        info['reason'] = None if info['covered_days'] == len(index) else 'one or more requested days lack inferred coverage'
    _require((root / 'manifest.json').read_bytes() == manifest_raw, 'snapshot manifest changed during admission')
    return daily, coverage

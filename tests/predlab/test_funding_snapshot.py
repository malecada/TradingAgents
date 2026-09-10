"""Synthetic immutable snapshot admission; no provider or research-data access."""
import hashlib
import importlib
import json
from pathlib import Path

import pandas as pd
import pytest


def load(*args, **kwargs):
    return importlib.import_module('tradingagents.predlab.funding_snapshot').load_funding_snapshot(*args, **kwargs)


def ms(value):
    return int(pd.Timestamp(value).timestamp() * 1000)


def snapshot(path, *, names=('AAA',), missing_boundary=False):
    path.mkdir(parents=True)
    received = '2026-09-03T00:05:00+00:00'
    start, end = ms('2026-08-26T00:00Z'), ms('2026-09-03T00:00Z')
    manifest = dict(schema_version=1, kind='binance-usdm-funding-capture', status='captured',
        source={'venue': 'Binance USD-M', 'base_url': 'https://fapi.binance.com',
                'git_commit': 'a' * 40, 'collector_sha256': 'b' * 64},
        window={'start_ms': start, 'end_ms': end}, started_utc='2026-09-03T00:00:00+00:00',
        completed_utc='2026-09-03T00:06:00+00:00', requested_symbols=list(names), instruments={}, requests=[])
    contracts = [dict(symbol=s, contractType='PERPETUAL', underlyingType='COIN', quoteAsset='USDT',
                      marginAsset='USDT', status='TRADING', onboardDate=ms('2025-01-01T00:00Z')) for s in names]
    def receipt(endpoint, params, body):
        rel = f'raw/{len(manifest["requests"])}.json'
        target = path / rel
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(body))
        manifest['requests'].append(dict(endpoint=endpoint, params=params, received_utc=received,
            status=200, body_file=rel, body_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), error=None))
    for endpoint, body in [('/fapi/v1/time', {'serverTime': end}),
                           ('/fapi/v1/exchangeInfo', {'symbols': contracts}),
                           ('/fapi/v1/fundingInfo', []), ('/fapi/v1/premiumIndex', [dict(symbol=s, time=end, nextFundingTime=end+8*3_600_000) for s in names])]:
        receipt(endpoint, {}, body)
    manifest['schedule_observations'] = [dict(endpoint=manifest['requests'][i]['endpoint'], observed_at=received,
         receipt_index=i, rows=len(json.loads((path / manifest['requests'][i]['body_file']).read_text())),
         historical_schedule=False) for i in (2, 3)]
    for contract in contracts:
        sym = contract['symbol']
        index = pd.date_range('2026-08-26', '2026-09-03', freq='8h', tz='UTC', name='fundingTime')
        if missing_boundary: index = index[:-1]
        events = pd.DataFrame({'fundingRate': .001, 'markPrice': 100., 'rateType': 'unspecified_crypto',
                               'observed_at': received}, index=index)
        rel = f'events/{sym}.parquet'; target = path / rel; target.parent.mkdir(exist_ok=True)
        events.to_parquet(target)
        manifest['instruments'][sym] = dict(status='captured', reason=None, contract=contract,
            query_start_ms=start, query_end_ms=end, query_complete=True, file=rel,
            sha256=hashlib.sha256(target.read_bytes()).hexdigest(), row_count=len(events),
            first_event_ms=ms(index[0]), last_event_ms=ms(index[-1]))
        receipt('/fapi/v1/fundingRate', {'symbol': sym, 'startTime': start, 'endTime': end, 'limit': 1000},
                [dict(symbol=sym, fundingTime=ms(t), fundingRate='.001', markPrice='100') for t in index])
    rewrite_manifest(path, manifest)
    return manifest


def rewrite_manifest(path, manifest):
    (path / 'manifest.json').write_text(json.dumps(manifest))


def read_day(path, symbols=('AAA',), time='2026-09-03T00:20Z'):
    return load(path, symbols, pd.DatetimeIndex(['2026-09-02T00:00Z']), measurement_time=time)


def test_realized_daily_sum_excludes_next_midnight_and_records_manifest_provenance(tmp_path):
    path = tmp_path / 'capture'; snapshot(path)
    daily, coverage = read_day(path)
    assert daily.iloc[0, 0] == pytest.approx(.003)
    assert coverage['method'] == 'snapshot_observed_cadence_inference'
    assert coverage['snapshot']['sha256'] == hashlib.sha256((path / 'manifest.json').read_bytes()).hexdigest()
    assert coverage['snapshot']['completed_utc'] == '2026-09-03T00:06:00+00:00'
    assert coverage['requested_symbols'] == ['AAA']
    assert coverage['symbols']['AAA']['query_complete'] is True


@pytest.mark.parametrize('problem', ['missing', 'tamper', 'missing_file', 'source', 'future', 'schema',
                                    'raw_tamper', 'incomplete_query', 'failed_request', 'traversal', 'time_naive'])
def test_invalid_snapshot_never_supplies_funding(tmp_path, problem):
    path = tmp_path / 'capture'; manifest = snapshot(path)
    if problem == 'missing': (path / 'manifest.json').unlink()
    elif problem == 'tamper': (path / 'events/AAA.parquet').write_bytes(b'changed')
    elif problem == 'missing_file': (path / 'events/AAA.parquet').unlink()
    elif problem == 'source': manifest['source']['base_url'] = 'https://other.invalid'
    elif problem == 'future': manifest['completed_utc'] = '2026-09-03T01:00:00+00:00'
    elif problem == 'schema': manifest['schema_version'] = 9
    elif problem == 'raw_tamper': (path / 'raw/4.json').write_bytes(b'[]')
    elif problem == 'incomplete_query': manifest['instruments']['AAA']['query_complete'] = False
    elif problem == 'failed_request': manifest['requests'][-1]['status'] = 429
    elif problem == 'traversal': manifest['instruments']['AAA']['file'] = '../outside.parquet'
    else: manifest['completed_utc'] = '2026-09-03T00:06:00'
    if problem != 'missing': rewrite_manifest(path, manifest)
    with pytest.raises(ValueError): read_day(path)


@pytest.mark.parametrize('problem', ['duplicate', 'nan', 'ambiguous_type', 'wrong_contract', 'event_future', 'wrong_count'])
def test_hashed_but_invalid_event_schema_is_rejected(tmp_path, problem):
    path = tmp_path / 'capture'; manifest = snapshot(path)
    entry = manifest['instruments']['AAA']; file = path / entry['file']; frame = pd.read_parquet(file)
    if problem == 'duplicate': frame = pd.concat([frame, frame.iloc[[-1]]])
    elif problem == 'nan': frame.iloc[0, 0] = float('nan')
    elif problem == 'ambiguous_type': frame.iloc[0, frame.columns.get_loc('rateType')] = 'Daily'
    elif problem == 'wrong_contract': entry['contract']['underlyingType'] = 'STOCK'
    elif problem == 'event_future': frame['observed_at'] = '2026-09-03T03:00Z'
    else: entry['row_count'] += 1
    frame.to_parquet(file); entry['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
    rewrite_manifest(path, manifest)
    with pytest.raises(ValueError): read_day(path)


def test_partial_snapshot_preserves_unavailable_denominator_and_valid_symbol(tmp_path):
    path = tmp_path / 'capture'; manifest = snapshot(path)
    manifest['status'] = 'partial'; manifest['requested_symbols'].append('BBB')
    manifest['instruments']['BBB'] = dict(status='quarantined', reason='conflicting event values', contract=None)
    rewrite_manifest(path, manifest)
    daily, coverage = read_day(path, ('AAA', 'BBB', 'CCC'))
    assert daily['AAA'].iloc[0] == pytest.approx(.003)
    assert daily[['BBB', 'CCC']].isna().all().all()
    assert coverage['requested_symbols'] == ['AAA', 'BBB']
    assert coverage['symbols']['BBB']['status'] == 'quarantined'
    assert coverage['symbols']['CCC']['status'] == 'unavailable'


def test_missing_boundary_and_outside_window_are_unavailable_without_zero(tmp_path):
    path = tmp_path / 'capture'; snapshot(path, missing_boundary=True)
    daily, coverage = read_day(path)
    assert daily['AAA'].isna().all()
    assert coverage['symbols']['AAA']['covered_days'] == 0
    daily, _ = load(path, ['AAA'], pd.DatetimeIndex(['2026-08-25T00:00Z']), measurement_time='2026-09-03T00:20Z')
    assert daily['AAA'].isna().all()


def test_real_collector_manifest_and_pagination_are_consumable(tmp_path, monkeypatch):
    from tradingagents.predlab.funding_capture import capture_run
    from .test_funding_capture import PublicFixture, event, NOW, DAY
    monkeypatch.setattr('tradingagents.predlab.funding_capture.utc_now', lambda: pd.Timestamp(NOW, unit='ms', tz='UTC').isoformat())
    times = list(range((NOW // DAY - 8) * DAY, (NOW // DAY) * DAY + 1, 8 * 3_600_000))
    path = tmp_path / 'collector'
    result = capture_run(path, transport=PublicFixture([event(t) for t in times]), pace_seconds=0, page_limit=7)
    assert result['status'] == 'captured'
    day = pd.Timestamp((NOW // DAY - 1) * DAY, unit='ms', tz='UTC')
    daily, coverage = load(path, ['BTCUSDT'], pd.DatetimeIndex([day]))
    assert daily.iloc[0, 0] == pytest.approx(.003)
    assert coverage['snapshot']['status'] == 'captured'

@pytest.mark.parametrize('problem', ['missing_boundary_receipt', 'conflicting_boundary'])
def test_full_page_boundary_evidence_cannot_be_omitted_or_contradict_history(tmp_path, problem, monkeypatch):
    from tradingagents.predlab.funding_capture import capture_run
    from .test_funding_capture import PublicFixture, NOW
    monkeypatch.setattr('tradingagents.predlab.funding_capture.utc_now', lambda: pd.Timestamp(NOW, unit='ms', tz='UTC').isoformat())
    path = tmp_path / 'collector'
    manifest = capture_run(path, transport=PublicFixture(), pace_seconds=0, page_limit=1)
    receipt = next(r for r in manifest['requests'] if r.get('purpose') == 'boundary_check')
    if problem == 'missing_boundary_receipt':
        manifest['requests'].remove(receipt)
    else:
        file = path / receipt['body_file']; body = json.loads(file.read_text())
        body[0]['fundingRate'] = '.9'; file.write_text(json.dumps(body))
        receipt['body_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
    rewrite_manifest(path, manifest)
    with pytest.raises(ValueError):
        load(path, ['BTCUSDT'], pd.DatetimeIndex(['2024-10-03T00:00Z']))


@pytest.mark.parametrize('problem', ['missing_code_identity', 'invalid_code_hash', 'wrong_server_cutoff',
                                    'missing_schedule_receipt', 'stale_schedule', 'schedule_history_claim',
                                    'not_trading', 'onboard_after_query_start'])
def test_declared_source_clock_schedule_and_contract_identity_are_verified(tmp_path, problem):
    path = tmp_path / 'capture'; manifest = snapshot(path)
    if problem == 'missing_code_identity': manifest['source'].pop('git_commit')
    elif problem == 'invalid_code_hash': manifest['source']['collector_sha256'] = 'invalid'
    elif problem == 'missing_schedule_receipt': manifest['requests'][2]['status'] = 503
    elif problem == 'schedule_history_claim': manifest['schedule_observations'][0]['historical_schedule'] = True
    else:
        receipt_index = 0 if problem == 'wrong_server_cutoff' else 3 if problem == 'stale_schedule' else 1
        receipt = manifest['requests'][receipt_index]; file = path / receipt['body_file']; body = json.loads(file.read_text())
        if problem == 'wrong_server_cutoff': body['serverTime'] += 1
        elif problem == 'stale_schedule': body[0]['time'] -= 3_600_000
        else:
            key, value = ('status', 'BREAK') if problem == 'not_trading' else ('onboardDate', manifest['window']['start_ms'] + 8*3_600_000)
            body['symbols'][0][key] = value
            manifest['instruments']['AAA']['contract'][key] = value
        file.write_text(json.dumps(body)); receipt['body_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
    rewrite_manifest(path, manifest)
    with pytest.raises(ValueError): read_day(path)


def shifted_snapshot(path, offsets):
    """Raw events remain distinct receipts; only the test provider's timestamps vary."""
    manifest = snapshot(path)
    entry = manifest['instruments']['AAA']; file = path / entry['file']; frame = pd.read_parquet(file)
    frame.index = frame.index + pd.to_timedelta(offsets, unit='ms')
    # A fixed cutoff after the following boundary accommodates genuine delayed labels.
    end = ms('2026-09-03T00:00:02Z'); manifest['window']['end_ms'] = end; entry['query_end_ms'] = end
    for receipt in manifest['requests']:
        body_path = path / receipt['body_file']; body = json.loads(body_path.read_text())
        if receipt['endpoint'].endswith('/time'): body['serverTime'] = end
        if receipt['endpoint'].endswith('/fundingRate'):
            receipt['params']['endTime'] = end
            body = [dict(symbol='AAA', fundingTime=ms(t), fundingRate='.001', markPrice='100') for t in frame.index]
        body_path.write_text(json.dumps(body)); receipt['body_sha256'] = hashlib.sha256(body_path.read_bytes()).hexdigest()
    frame.to_parquet(file); entry.update(sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
        row_count=len(frame), first_event_ms=ms(frame.index[0]), last_event_ms=ms(frame.index[-1]))
    rewrite_manifest(path, manifest)
    return manifest


@pytest.mark.parametrize('offset', [0, 9, 1000])
def test_narrow_prospective_hour_alignment_keeps_raw_daily_membership(tmp_path, offset):
    path = tmp_path / 'capture'; shifted_snapshot(path, offset)
    before = (path/'events/AAA.parquet').read_bytes()
    daily, coverage = read_day(path)
    assert daily.iloc[0, 0] == pytest.approx(.003)  # following boundary excluded from the daily sum
    alignment = coverage['symbols']['AAA']['alignment']
    assert alignment['policy_version'] == 'utc_hour_forward_1s_v1'
    assert alignment['max_offset_ms'] == offset and alignment['off_grid_events'] == 0
    assert (path/'events/AAA.parquet').read_bytes() == before


@pytest.mark.parametrize('offset', [1001, -1])
def test_off_grid_or_pre_hour_events_are_never_rounded_into_coverage(tmp_path, offset):
    path = tmp_path / 'capture'
    offsets = [0] * 25; offsets[15] = offset
    shifted_snapshot(path, offsets)
    daily, coverage = read_day(path)
    assert daily['AAA'].isna().all()
    assert coverage['symbols']['AAA']['alignment']['off_grid_events'] == 1


def test_two_distinct_raw_times_in_one_hour_are_ambiguous_even_at_same_rate(tmp_path):
    path = tmp_path / 'capture'; manifest = shifted_snapshot(path, 3)
    entry = manifest['instruments']['AAA']; file = path/entry['file']; frame = pd.read_parquet(file)
    extra = frame.iloc[[15]].copy(); extra.index = extra.index - pd.Timedelta(milliseconds=1)
    frame = pd.concat([frame, extra]).sort_index(); frame.to_parquet(file)
    entry.update(sha256=hashlib.sha256(file.read_bytes()).hexdigest(), row_count=len(frame))
    receipt = manifest['requests'][-1]; body_path=path/receipt['body_file']
    body_path.write_text(json.dumps([dict(symbol='AAA', fundingTime=ms(t), fundingRate='.001', markPrice='100') for t in frame.index]))
    receipt['body_sha256']=hashlib.sha256(body_path.read_bytes()).hexdigest(); rewrite_manifest(path,manifest)
    daily, coverage=read_day(path)
    assert daily['AAA'].isna().all()
    assert coverage['symbols']['AAA']['alignment']['duplicate_grid_hours']==1
    assert coverage['symbols']['AAA']['alignment']['duplicate_grid_events']==2


def test_shifted_following_boundary_must_be_observed_inside_query(tmp_path):
    path=tmp_path/'capture';manifest=shifted_snapshot(path,9)
    entry=manifest['instruments']['AAA'];file=path/entry['file'];frame=pd.read_parquet(file).iloc[:-1]
    frame.to_parquet(file);entry.update(sha256=hashlib.sha256(file.read_bytes()).hexdigest(),row_count=len(frame),last_event_ms=ms(frame.index[-1]))
    receipt=manifest['requests'][-1];body_path=path/receipt['body_file'];body=json.loads(body_path.read_text())[:-1]
    body_path.write_text(json.dumps(body));receipt['body_sha256']=hashlib.sha256(body_path.read_bytes()).hexdigest();rewrite_manifest(path,manifest)
    daily,coverage=read_day(path)
    assert daily['AAA'].isna().all()
    assert 'boundary' in coverage['symbols']['AAA']['days']['2026-09-02T00:00:00+00:00']['reason']

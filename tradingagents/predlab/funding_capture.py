"""Immutable public funding observations; no credentials or account endpoints.

A captured query is exhausted public history, not proof of an economic schedule
or account cash debit. Current schedule observations are never backdated.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

BASE_URL = 'https://fapi.binance.com'
DAY_MS = 86_400_000
ENDPOINTS = {'/fapi/v1/time', '/fapi/v1/exchangeInfo', '/fapi/v1/fundingInfo',
             '/fapi/v1/premiumIndex', '/fapi/v1/fundingRate'}
# Preserve provider Unicode identities; reject separators/control characters.
SYMBOL = re.compile(r'^\w{1,40}USDT$', flags=re.UNICODE)
DOC_URL = 'https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data'


class CaptureError(ValueError):
    pass


class RequestFailure(CaptureError):
    pass


class RateLimited(RequestFailure):
    pass


class ResponseReadFailure(Exception):
    def __init__(self, status, headers, cause):
        super().__init__(f'{type(cause).__name__}: {cause}')
        self.status, self.headers = status, headers
        self.partial = getattr(cause, 'partial', b'')


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def source_identity():
    """Identify this module's checkout, or its immutable release marker.

    An enclosing repository is never the collector's source. An owned checkout
    takes precedence; SOURCE_COMMIT is the fallback for archives without Git.
    The marker declares provenance, while collector_sha256 identifies the bytes.
    """
    root = Path(__file__).resolve().parents[2]
    if (root/'.git').exists():
        try:
            top = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'],
                cwd=root, stderr=subprocess.DEVNULL).decode().strip()
            if Path(top).resolve() == root:
                commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                    cwd=root, stderr=subprocess.DEVNULL).decode().strip()
                if re.fullmatch(r'[0-9a-fA-F]{40}', commit):
                    return dict(git_commit=commit.lower(), source_identity_method='git_checkout')
        except (OSError, subprocess.CalledProcessError, UnicodeError):
            pass
    try:
        marker = (root/'SOURCE_COMMIT').read_bytes()
    except OSError as exc:
        raise CaptureError('source identity unavailable: no owned Git checkout or readable SOURCE_COMMIT') from exc
    if not re.fullmatch(rb'[0-9a-fA-F]{40}\n', marker):
        raise CaptureError('invalid SOURCE_COMMIT: expected exactly 40 hexadecimal characters and LF')
    return dict(git_commit=marker[:-1].decode().lower(), source_identity_method='release_marker')


def save_json(path, value):
    # New files only: never revise a completed run or replace prior evidence.
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def public_get(endpoint, params):
    if endpoint not in ENDPOINTS:
        raise CaptureError('endpoint is not public funding-capture scope')
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(BASE_URL + endpoint + ('?' + query if query else ''),
        headers={'Accept':'application/json', 'User-Agent':'s1-public-funding-capture/1'})
    def read_response(response, status):
        headers = dict(response.headers)
        try:
            return status, headers, response.read()
        except Exception as exc:
            raise ResponseReadFailure(status, headers, exc) from exc
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            return read_response(response, response.status)
    except urllib.error.HTTPError as error:
        with error:
            return read_response(error, error.code)


class Receipts:
    def __init__(self, directory, transport, pace_seconds):
        self.directory, self.transport, self.pace = directory, transport, pace_seconds
        self.rows, self.last_request = [], None

    def get(self, endpoint, params, *, purpose=None):
        if endpoint not in ENDPOINTS:
            raise CaptureError('endpoint is outside declared public scope')
        if self.last_request is not None:
            time.sleep(max(0., self.pace - (time.monotonic()-self.last_request)))
        self.last_request = time.monotonic()
        started = utc_now()
        status, headers, body, error = None, {}, b'', None
        try:
            status, headers, body = self.transport(endpoint, params)
            if not isinstance(body, bytes):
                raise TypeError('transport body must be raw bytes')
        except Exception as exc:
            # Includes HTTPException/IncompleteRead; preserve partial received bytes.
            status = getattr(exc, 'status', status)
            headers = getattr(exc, 'headers', headers)
            partial = getattr(exc, 'partial', b'')
            body = partial if isinstance(partial, bytes) else b''
            error = f'{type(exc).__name__}: {exc}'
        received = utc_now()
        relative = f'raw/{len(self.rows):06d}.body'
        with (self.directory/relative).open('xb') as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        safe_headers = {k.lower():v for k,v in headers.items()
                        if k.lower() in {'date','content-type','retry-after'} or k.lower().startswith('x-mbx-used-weight')}
        row = dict(endpoint=endpoint, url=BASE_URL+endpoint, params=dict(params),
                   purpose=purpose or ('history' if endpoint.endswith('/fundingRate') else 'metadata'),
                   started_utc=started, received_utc=received, status=status,
                   headers=safe_headers, body_file=relative, body_sha256=sha256(body),
                   body_bytes=len(body), error=error)
        self.rows.append(row)
        with (self.directory/'requests.jsonl').open('a') as stream:
            stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            stream.flush(); os.fsync(stream.fileno())
        if status in (418,429):
            raise RateLimited(f'public endpoint HTTP {status}; capture stopped')
        if error or status != 200:
            raise RequestFailure(error or f'public endpoint HTTP {status}')
        try:
            data = json.loads(body, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except (ValueError, UnicodeError) as exc:
            raise RequestFailure(f'invalid JSON response: {exc}') from exc
        return data, received


def eligible(row):
    return (isinstance(row,dict) and isinstance(row.get('symbol'),str) and SYMBOL.fullmatch(row['symbol'])
            and row.get('contractType') == 'PERPETUAL' and row.get('status') == 'TRADING'
            and row.get('quoteAsset') == row.get('marginAsset') == 'USDT')


def decimal_value(value, label, *, positive=False):
    if not isinstance(value,(str,int,float)) or isinstance(value,bool):
        raise CaptureError(f'invalid {label}')
    try:
        dec = Decimal(str(value))
    except InvalidOperation as exc:
        raise CaptureError(f'invalid {label}') from exc
    if not dec.is_finite() or not math.isfinite(float(dec)) or (positive and dec <= 0):
        raise CaptureError(f'nonfinite or invalid {label}')
    return dec


def fetch_events(receipts, symbol, contract, start_ms, end_ms, limit):
    cursor, events, duplicates = start_ms, {}, 0
    def admit(page, lower, upper, observed):
        nonlocal duplicates
        if not isinstance(page, list):
            raise CaptureError('history is not a list')
        previous = None
        for row in page:
            if not isinstance(row,dict) or row.get('symbol') != symbol:
                raise CaptureError('unexpected history instrument')
            stamp = row.get('fundingTime')
            if type(stamp) is not int or not lower <= stamp <= upper:
                raise CaptureError('history timestamp outside requested page')
            if previous is not None and stamp < previous:
                raise CaptureError('history is not ascending')
            previous = stamp
            rate = decimal_value(row.get('fundingRate'),'fundingRate')
            mark = decimal_value(row.get('markPrice'),'markPrice',positive=True)
            kind = row.get('rateType')
            if kind is None and contract.get('underlyingType') == 'COIN':
                kind = 'unspecified_crypto'
            if kind not in ('Regular','unspecified_crypto'):
                raise CaptureError('unsupported or ambiguous funding rateType')
            value = (rate,mark,kind)
            if stamp in events:
                if events[stamp][0] != value:
                    raise CaptureError('conflicting funding event observations')
                duplicates += 1
            else:
                events[stamp] = (value,observed)

    # Check the last timestamp group before advancing beyond a full page: two
    # unlike events may share that timestamp and otherwise be silently skipped.
    for _ in range(250):
        params = dict(symbol=symbol,startTime=cursor,endTime=end_ms,limit=limit)
        page, observed = receipts.get('/fapi/v1/fundingRate',params)
        if not isinstance(page,list) or len(page)>limit:
            raise CaptureError('history is not a bounded list')
        admit(page,cursor,end_ms,observed)
        if len(page) == limit:
            boundary = page[-1]['fundingTime']
            group, observed = receipts.get('/fapi/v1/fundingRate',
                dict(symbol=symbol,startTime=boundary,endTime=boundary,limit=1000),purpose='boundary_check')
            if not isinstance(group,list) or not group or len(group)>=1000:
                raise CaptureError('ambiguous full-page boundary group')
            admit(group,boundary,boundary,observed)
        if len(page)<limit or (page and page[-1]['fundingTime'] == end_ms):
            break
        if not page or page[-1]['fundingTime'] < cursor:
            raise CaptureError('funding cursor did not advance')
        cursor = page[-1]['fundingTime'] + 1
    else:
        raise CaptureError('funding pagination budget exhausted')
    if not events:
        raise CaptureError('empty published funding history')
    stamps = sorted(events)
    frame = pd.DataFrame({
        'fundingRate':[float(events[t][0][0]) for t in stamps],
        'markPrice':[float(events[t][0][1]) for t in stamps],
        'rateType':[events[t][0][2] for t in stamps],
        'observed_at':[events[t][1] for t in stamps]},
        index=pd.to_datetime(stamps,unit='ms',utc=True))
    frame.index.name = 'fundingTime'
    return frame, duplicates


def capture_run(directory, *, symbols=None, transport=public_get, pace_seconds=1.,
                page_limit=1000, lookback_days=9, progress=None):
    """Create a new immutable run, preserving partial results and failures.

    `transport` injection is solely a synthetic test seam. Public CLI pacing,
    bounds and endpoint choice are fixed; no credentials or alternate host.
    """
    if not 1 <= page_limit <= 1000 or not 9 <= lookback_days <= 14 or pace_seconds < 0:
        raise ValueError('invalid capture limits')
    if symbols is not None and (not symbols or any(not isinstance(s,str) or not SYMBOL.fullmatch(s) for s in symbols)):
        raise ValueError('explicit symbols must be nonempty valid USDT names')
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    (directory/'raw').mkdir(); (directory/'events').mkdir()
    receipts = Receipts(directory,transport,pace_seconds)
    source = dict(venue='Binance USD-M',base_url=BASE_URL,documentation=DOC_URL,
                  market_type='USDT-margined USDT-quoted PERPETUAL',
                  rate_units='signed fraction per published funding event; positive paid by longs',
                  mark_units='USDT per base unit; associated event mark',
                  time_policy='raw UTC millisecond event labels; no timestamp rounding')
    source['collector_sha256'] = sha256(Path(__file__).read_bytes())
    result = dict(schema_version=1,kind='binance-usdm-funding-capture',status='failed',
                  started_utc=utc_now(),completed_utc=None,source=source,window=None,
                  requested_symbols=sorted(set(symbols or [])),instruments={},requests=receipts.rows,
                  qualification='Query exhaustion is not historical schedule completeness or exact account cashflow. Current schedules are observed now, never backdated.')
    try:
        source.update(source_identity())
        clock,clock_received = receipts.get('/fapi/v1/time',{})
        end = clock.get('serverTime') if isinstance(clock,dict) else None
        if type(end) is not int or end <= 0:
            raise CaptureError('invalid exchange server time')
        local_ms = int(datetime.fromisoformat(clock_received).timestamp()*1000)
        if abs(local_ms-end) > 300_000:
            raise CaptureError('exchange server clock differs from acquisition by more than five minutes')
        start = (end//DAY_MS-(lookback_days-1))*DAY_MS
        result['window'] = dict(start_ms=start,end_ms=end)
        info,_ = receipts.get('/fapi/v1/exchangeInfo',{})
        if not isinstance(info,dict) or not isinstance(info.get('symbols'),list) or not info['symbols']:
            raise CaptureError('invalid or empty instrument metadata')
        identities = {}
        for row in info['symbols']:
            if not isinstance(row,dict) or not isinstance(row.get('symbol'),str):
                raise CaptureError('malformed instrument metadata')
            if row['symbol'] in identities:
                raise CaptureError('duplicate instrument identities')
            identities[row['symbol']] = row
        selected = sorted(set(symbols)) if symbols is not None else sorted(s for s,r in identities.items() if eligible(r))
        if not selected:
            raise CaptureError('empty eligible universe')
        result['requested_symbols'] = selected
        for symbol in selected:
            result['instruments'][symbol] = dict(status='unavailable',reason='not attempted',query_complete=False,
                                                 contract=identities.get(symbol))
        for endpoint in ('/fapi/v1/fundingInfo','/fapi/v1/premiumIndex'):
            schedule,observed = receipts.get(endpoint,{})
            if not isinstance(schedule,list):
                raise CaptureError('invalid schedule snapshot')
            seen = set()
            for item in schedule:
                if not isinstance(item,dict) or not isinstance(item.get('symbol'),str) or item['symbol'] in seen:
                    raise CaptureError('malformed or duplicate schedule identity')
                seen.add(item['symbol'])
                if endpoint.endswith('/fundingInfo'):
                    interval = item.get('fundingIntervalHours')
                    if type(interval) is not int or interval not in (1,2,4,8):
                        raise CaptureError('unsupported current funding interval')
                    floor = decimal_value(item.get('adjustedFundingRateFloor'),'adjustedFundingRateFloor')
                    cap = decimal_value(item.get('adjustedFundingRateCap'),'adjustedFundingRateCap')
                    if floor > cap: raise CaptureError('inverted current funding limits')
                elif item['symbol'] in selected and eligible(identities.get(item['symbol'])):
                    stamp,next_time = item.get('time'),item.get('nextFundingTime')
                    received_ms = int(datetime.fromisoformat(observed).timestamp()*1000)
                    if (type(stamp) is not int or type(next_time) is not int or
                            not 0 <= received_ms-stamp <= 300_000 or next_time <= stamp):
                        raise CaptureError('missing or stale current funding schedule timestamp')
            if endpoint.endswith('/premiumIndex') and any(s not in seen for s in selected if eligible(identities.get(s))):
                raise CaptureError('current schedule snapshot omits requested active instruments')
            result.setdefault('schedule_observations',[]).append(dict(endpoint=endpoint,observed_at=observed,
                receipt_index=len(receipts.rows)-1,rows=len(schedule),historical_schedule=False))
        consecutive_failures, stopped = 0, None
        for n,symbol in enumerate(selected):
            entry = result['instruments'][symbol]
            contract = identities.get(symbol)
            if stopped:
                entry['reason'] = stopped
                continue
            if not eligible(contract):
                entry['reason'] = 'requested instrument absent or not a currently trading USDT perpetual'
                continue
            onboard = contract.get('onboardDate')
            if type(onboard) is not int or not 0 < onboard <= end:
                entry['reason'] = 'original contract onboard identity unavailable'
                continue
            query_start = max(start,onboard)
            entry.update(query_start_ms=query_start,query_end_ms=end)
            try:
                frame,duplicates = fetch_events(receipts,symbol,contract,query_start,end,page_limit)
                relative = f'events/{symbol}.parquet'
                frame.to_parquet(directory/relative)
                entry.update(status='captured',reason=None,query_complete=True,file=relative,
                    sha256=sha256((directory/relative).read_bytes()),row_count=len(frame),
                    first_event_ms=int(frame.index[0].value//1_000_000),
                    last_event_ms=int(frame.index[-1].value//1_000_000),exact_duplicates=duplicates)
                consecutive_failures = 0
            except RateLimited as exc:
                entry['reason'] = stopped = str(exc)
            except RequestFailure as exc:
                entry['reason'] = str(exc)
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    stopped = 'three consecutive public request failures; remaining symbols not attempted'
            except (CaptureError, OSError) as exc:
                entry.update(status='quarantined',reason=str(exc))
            if progress is not None and ((n+1)%25==0 or n+1==len(selected)):
                progress(dict(processed=n+1,requested=len(selected),captured=sum(e['status']=='captured' for e in result['instruments'].values())))
        result['status'] = 'captured' if all(e['status']=='captured' for e in result['instruments'].values()) else 'partial'
    except (CaptureError,OSError) as exc:
        result['error'] = str(exc)
    finally:
        result['completed_utc'] = utc_now()
        save_json(directory/'manifest.json',result)
    return result

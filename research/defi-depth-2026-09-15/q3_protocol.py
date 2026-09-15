"""Q3 source-policy primitives; injected transport only, no empirical main.

No financial calculations. This module is not yet an admitted acquisition
runner. Context binding, complete lifecycle outputs and preflight remain needed.
"""
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
_loader = importlib.util.spec_from_file_location('q3_preserved_r1_helpers', HERE / 'r1_source_v2.py')
old = importlib.util.module_from_spec(_loader)
_loader.loader.exec_module(old)


def request_key(method, params):
    return json.dumps([method, params], sort_keys=True, separators=(',', ':'), allow_nan=False)


def prior_header_keys(receipts):
    """Attempted requests stay excluded even if their response failed."""
    result = set()
    for receipt in receipts:
        if not receipt.get('attempted'):
            continue
        payload = receipt['request']
        for member in payload if isinstance(payload, list) else [payload]:
            if member['method'] != 'eth_getBlockByNumber':
                raise ValueError('header receipt contains a different method')
            key = request_key(member['method'], member['params'])
            if key in result:
                raise ValueError('duplicate prior header request key')
            result.add(key)
    return result


def new_header_plan(design, days, previous_keys):
    """Two exact adjacent headers per never-attempted Q3 date, no search."""
    proposed = {day['date']: day for day in design['new_header_days']}
    original = {day['date']: day for day in days}
    if len(proposed) != len(design['new_header_days']) or not proposed.keys() <= original.keys():
        raise ValueError('new header dates duplicate or escape the fixed calendar')
    result, seen = {}, set()
    for date, day in sorted(proposed.items()):
        if day != original[date] or date <= '2023-11-28':
            raise ValueError('new header date changes old calibration or attempts an old date')
        requests = []
        for side, offset in (('left', 0), ('right', 1)):
            member = {'jsonrpc': '2.0', 'id': date + '-header-' + side,
                      'method': 'eth_getBlockByNumber', 'params': [hex(day['candidate_block'] + offset), False]}
            key = request_key(member['method'], member['params'])
            if key in previous_keys or key in seen:
                raise ValueError('proposed header repeats an attempted or planned key')
            seen.add(key)
            requests.append(member)
        result[date] = requests
    return result


def _raw_envelopes(receipt):
    body = base64.b64decode(receipt['body_base64'], validate=True)
    if len(body) != receipt['body_bytes'] or hashlib.sha256(body).hexdigest() != receipt['body_sha256']:
        raise ValueError('retained source body hash or length mismatch')
    if receipt.get('error') or receipt['http_status'] != 200 or not receipt['body_complete']:
        raise ValueError(receipt.get('error') or 'retained HTTP response incomplete')
    members = receipt['request'] if isinstance(receipt['request'], list) else [receipt['request']]
    decoded = old.q1.helpers.strict_json(body)
    if isinstance(receipt['request'], list):
        return old.batch_envelopes(body, members)
    if not isinstance(decoded, dict) or decoded.get('jsonrpc') != '2.0' or decoded.get('id') != members[0]['id']:
        raise ValueError('retained response envelope mismatch')
    return {decoded['id']: decoded}


def qualify_retained_bracket(day, receipt):
    """Q3 qualification of R1 raw bytes, never creation of an R1 output."""
    try:
        expected = [
            {'jsonrpc': '2.0', 'id': day['date'] + '-header-left', 'method': 'eth_getBlockByNumber',
             'params': [hex(day['candidate_block']), False]},
            {'jsonrpc': '2.0', 'id': day['date'] + '-header-right', 'method': 'eth_getBlockByNumber',
             'params': [hex(day['candidate_block'] + 1), False]},
        ]
        # The original R1 IDs are retained exactly; caller cannot alias them.
        if receipt['request'] != expected:
            raise ValueError('retained header intent differs from exact day calibration')
        envelopes = _raw_envelopes(receipt)
        observed = datetime.fromisoformat(receipt['retrieval_utc']).timestamp()
        headers = []
        for index, member in enumerate(expected):
            item = envelopes.get(member['id'])
            if not item or 'error' in item or item.get('result') is None:
                raise ValueError('retained header member failed or absent')
            headers.append(old.parse_header(item['result'], day['candidate_block'] + index, observed))
        block = old.bracket(*headers, day['timestamp'])
        return {'status': 'complete', 'value': block, 'source_role': 'Q3 qualification of retained raw source'}
    except (ValueError, TypeError, KeyError) as exc:
        return {'status': 'unavailable', 'reason': str(exc), 'source_role': 'retained failure; no retry'}


def boundary_eligibility(cells):
    """Observability filter only: never compare a positive price's magnitude."""
    expected = ('canonical-bracket', 'wrapper-decimals', 'wrapper-code', 'oracle-unit',
                'oracle-base', 'oracle-wsteth-price', 'oracle-wsteth-source', 'oracle-source-code')
    failed = [name for name in expected if cells.get(name, {}).get('status') != 'complete']
    if failed:
        return {'status': 'unavailable', 'reason': 'Boundary fields unavailable: ' + ', '.join(failed)}
    try:
        if cells['wrapper-decimals']['value']['words'] != [18]:
            raise ValueError('wrapper decimals differ')
        if cells['oracle-unit']['value']['words'] != [10**8] or cells['oracle-base']['value']['words'] != ['0x' + '0' * 40]:
            raise ValueError('oracle currency/unit differ')
        if cells['oracle-wsteth-price']['value']['words'][0] <= 0:
            raise ValueError('nonpositive oracle price')
        address = cells['oracle-wsteth-source']['value']['words'][0]
        old.q1.helpers.hexdata(address, 20)
        if int(address, 16) == 0:
            raise ValueError('zero source address')
        for field in ('wrapper-code', 'oracle-source-code'):
            if cells[field]['value']['bytecode_bytes'] <= 0:
                raise ValueError('empty code')
        return {'status': 'complete', 'scope': 'source observability only; semantic/execution qualification unavailable'}
    except (KeyError, TypeError, ValueError) as exc:
        return {'status': 'unavailable', 'reason': str(exc)}


def cohort_eligibility(cohorts, boundaries):
    result = {}
    for label, window in cohorts.items():
        failed = [date for date in (window['start'], window['end']) if boundaries.get(date, {}).get('status') != 'complete']
        result[label] = {'status': 'unavailable', 'reason': 'Unqualified boundaries: ' + ', '.join(failed)} if failed else {
            'status': 'complete', 'scope': 'eligible for fixed interior source acquisition only'}
    return result


def day_eligible(day, cohorts, eligibility):
    return any(window['start'] <= day <= window['end'] and eligibility[label]['status'] == 'complete'
               for label, window in cohorts.items())


class PacedSource:
    """Single synchronous RPC, fixed spacing and immediate limiting stop.

    The caller injects the reviewed read-only transport, publisher and clocks.
    Each invocation retains its intent and exact raw receipt, even if suppressed.
    No redirect/proxy/account/transaction authority is added here.
    """
    def __init__(self, design, publish, fetch, *, monotonic=time.monotonic,
                 sleep=time.sleep, utc=lambda: datetime.now(timezone.utc)):
        self.design, self.publish, self.fetch = design, publish, fetch
        self.monotonic, self.sleep, self.utc = monotonic, sleep, utc
        self.last_response, self.stopped, self.ids = {}, {}, set()
        self.http_requests = self.rpc_subcalls = self.raw_bytes = 0

    def _limited(self, body):
        try:
            parsed = old.q1.helpers.strict_json(body)
        except (ValueError, TypeError):
            return None
        replies = parsed if isinstance(parsed, list) else [parsed]
        for reply in replies:
            if not isinstance(reply, dict) or not isinstance(reply.get('error'), dict):
                continue
            error = reply['error']
            message = str(error.get('message', '')).casefold()
            policy = self.design['recognized_rpc_throttling']
            if error.get('code') in policy['codes'] or any(fragment in message for fragment in policy['message_fragments_casefold']):
                return 'recognized RPC throttling: ' + str(error)
        return None

    def request(self, chain, member, parser, *, dependency=None):
        if chain not in self.design['chains']:
            raise ValueError('unregistered chain')
        if not isinstance(member, dict) or member.get('jsonrpc') != '2.0' or member.get('method') not in ('eth_chainId', 'eth_getBlockByNumber', 'eth_call', 'eth_getCode'):
            raise ValueError('one registered read-only RPC required')
        rid = member.get('id')
        if not isinstance(rid, str) or not rid or rid in self.ids:
            raise ValueError('unique nonempty request ID required')
        self.ids.add(rid)
        url = self.design['chains'][chain]['url']
        reason = self.stopped.get(chain) or dependency
        if reason is None:
            delay = self.design['pacing']['minimum_seconds_after_previous_response_same_endpoint']
            if chain in self.last_response:
                while (remaining := self.last_response[chain] + delay - self.monotonic()) > 0:
                    self.sleep(min(remaining, 5))
        start = self.utc().isoformat()
        intent = {'id': rid, 'url': url, 'request_utc': start, 'attempted': reason is None,
                  'request': member if reason is None else None, 'reason': reason}
        self.publish(rid + '-attempt.json', intent)
        if reason is None:
            self.http_requests += 1
            self.rpc_subcalls += 1
            if self.rpc_subcalls > self.design['max_rpc_subcalls'] or self.http_requests > self.design['max_http_requests']:
                raise ValueError('Q3 source request reservation exceeded')
            response = self.fetch(url, member)
            self.last_response[chain] = self.monotonic()
        else:
            response = {'body': b'', 'http_status': None, 'headers': {}, 'error': reason, 'body_complete': False}
        body = response['body']
        if not isinstance(body, bytes) or len(body) > self.design['max_response_bytes']:
            raise ValueError('source transport body contract violated')
        self.raw_bytes += len(body)
        if self.raw_bytes > self.design['worst_case_raw_bytes']:
            raise ValueError('Q3 raw reservation exceeded')
        if response['http_status'] in self.design['denials_stop_endpoint']:
            self.stopped[chain] = 'HTTP denial: ' + str(response['http_status'])
        throttle = self._limited(body)
        if throttle:
            self.stopped[chain] = throttle
        ended = self.utc()
        self.publish(rid + '-receipt.json', {**intent, 'retrieval_utc': ended.isoformat(),
                     'http_status': response['http_status'], 'headers': response['headers'],
                     'body_complete': response['body_complete'], 'error': response['error'],
                     'body_bytes': len(body), 'body_sha256': hashlib.sha256(body).hexdigest(),
                     'body_base64': base64.b64encode(body).decode(), 'endpoint_stopped_reason': self.stopped.get(chain)})
        try:
            if response['error'] or response['http_status'] != 200 or not response['body_complete']:
                raise ValueError(response['error'] or 'incomplete HTTP response')
            value = old.q1.envelope(body, member)
            return {'id': rid, 'status': 'complete', 'value': parser(value, ended.timestamp())}
        except (ValueError, TypeError, KeyError) as exc:
            return {'id': rid, 'status': 'unavailable', 'reason': str(exc)}

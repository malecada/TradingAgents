"""One registered six-field source-capability check on each of three chains."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time
from tradingagents.research import ResearchRun

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('broader_dex_transport', HERE/'dex_transport.py')
transport = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transport)
EXPERIMENT = 'allocation-dex-source-20260915'
REGISTRATION = 'research/broader-allocation-2026-09-15/gates-dex-source.json'
SPEC_SHA256 = 'd637814ef5d90332992f3939de2034b57adc63ec7ae4b11e0ec3867aa9487237'
GROUPS = ('chain', 'finalized', 'pool', 'gas', 'history_header', 'history_code')


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def bad(value):
        raise ValueError('nonfinite JSON number')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def quantity(value):
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)', value):
        raise ValueError('invalid RPC hexadecimal quantity')
    return int(value, 16)


def hexdata(value, size=None):
    if not isinstance(value, str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*', value):
        raise ValueError('invalid RPC byte string')
    if size is not None and len(value) != 2 + size*2:
        raise ValueError('RPC byte string length mismatch')
    return value.lower()


def parse(raw, payload, chain, kind, observed_at, context):
    data = strict_json(raw)
    if not isinstance(data, dict) or data.get('jsonrpc') != '2.0' or data.get('id') != payload['id']:
        raise ValueError('RPC envelope or response ID mismatch')
    if 'error' in data or 'result' not in data or data['result'] is None:
        raise ValueError('RPC error or null result: ' + str(data.get('error', 'missing result'))[:500])
    result = data['result']
    if kind == 'chain':
        cid = quantity(result)
        if cid != chain['chain_id']:
            raise ValueError('chain identity mismatch')
        return {'chain_id': cid}
    if kind in ('finalized', 'history_header'):
        if not isinstance(result, dict):
            raise ValueError('block header object required')
        number, stamp = quantity(result.get('number')), quantity(result.get('timestamp'))
        block_hash = hexdata(result.get('hash'), 32)
        if int(block_hash, 16) == 0 or stamp <= 0 or stamp > observed_at:
            raise ValueError('invalid/future block hash or timestamp')
        if kind == 'history_header':
            if number != chain['historical_block']:
                raise ValueError('wrong historical block number')
            if 'finalized' in context and (number >= context['finalized']['number'] or stamp >= context['finalized']['timestamp']):
                raise ValueError('historical probe is not before finalized anchor')
        return {'number': number, 'hash': block_hash, 'timestamp': stamp,
                'timestamp_utc': datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                'provider_finality_assertion_only': kind == 'finalized'}
    if kind == 'pool':
        word = hexdata(result, 32)
        if word[2:26] != '0'*24:
            raise ValueError('invalid ABI address padding')
        address = '0x' + word[-40:]
        return {'pool_address': address, 'pool_found': int(address,16) != 0,
                'fee_tier': 3000, 'block': context['finalized'],
                'scope': 'Factory mapping only; zero address means absent at this tier; no liquidity or safety claim'}
    if kind == 'gas':
        return {'provider_suggested_gas_price_wei': str(quantity(result)),
                'scope': 'Unanchored suggestion at retrieval; not full swap gas, L1 data fee or executable cost'}
    if kind == 'history_code':
        code = hexdata(result)
        if code == '0x':
            raise ValueError('empty historical code; archive state not established')
        return {'code_bytes': (len(code)-2)//2, 'code_sha256': hashlib.sha256(bytes.fromhex(code[2:])).hexdigest(),
                'block': context['history_header'], 'scope': 'One nonempty code response at a canonical hash; not archive coverage or code audit'}
    raise ValueError('unknown group')


def request_for(chain, kind, context):
    if kind == 'chain':
        method, params = 'eth_chainId', []
    elif kind == 'finalized':
        method, params = 'eth_getBlockByNumber', ['finalized', False]
    elif kind == 'pool':
        method, params = 'eth_call', [{'to': chain['factory'], 'data': chain['get_pool_calldata']},
            {'blockHash': context['finalized']['hash'], 'requireCanonical': True}]
    elif kind == 'gas':
        method, params = 'eth_gasPrice', []
    elif kind == 'history_header':
        method, params = 'eth_getBlockByNumber', [hex(chain['historical_block']), False]
    elif kind == 'history_code':
        method, params = 'eth_getCode', [chain['factory'],
            {'blockHash': context['history_header']['hash'], 'requireCanonical': True}]
    else:
        raise ValueError('unknown group')
    return {'jsonrpc': '2.0', 'id': chain['name']+'-'+kind, 'method': method, 'params': params}


def capture(spec, fetch=transport.public_post, persist=None):
    canonical = json.dumps(spec, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest() != SPEC_SHA256:
        raise ValueError('unregistered request specification')
    deadline = time.monotonic() + spec['cooperative_seconds']
    rows, receipts, attempted = [], [], 0
    for chain in spec['chains']:
        context, denied = {}, False
        for kind in GROUPS:
            rowid = chain['name']+'-'+kind
            before = time.monotonic()
            started = datetime.now(timezone.utc)
            reason = ('not attempted after HTTP denial' if denied else
                      'chain identity unavailable; dependent request not attempted' if kind != 'chain' and 'chain' not in context else
                      'finalized anchor unavailable; pool request not attempted' if kind == 'pool' and 'finalized' not in context else
                      'historical header unavailable; code request not attempted' if kind == 'history_code' and 'history_header' not in context else
                      'insufficient remaining cooperative time' if before+spec['timeout_seconds'] > deadline else None)
            payload = None
            if reason is None:
                payload = request_for(chain, kind, context)
                attempted += 1
                if attempted > spec['max_requests']:
                    raise ValueError('request bound exceeded')
                response = fetch(chain['url'], payload)
            else:
                response = {'body': b'', 'http_status': None, 'headers': {}, 'body_complete': False, 'error': reason}
            body = response['body']
            if not isinstance(body, bytes):
                raise ValueError('transport must preserve bytes')
            if len(body) > spec['max_response_bytes']:
                body = body[:spec['max_response_bytes']]
                response = {**response, 'body_complete': False, 'error': 'oversized response; prefix retained'}
            if response['http_status'] in transport.DENIALS:
                denied = True
            ended = datetime.now(timezone.utc)
            receipt = {'id': rowid, 'url': chain['url'], 'request': payload, 'attempted': reason is None,
                'request_utc': started.isoformat(), 'retrieval_utc': ended.isoformat(),
                'elapsed_seconds': time.monotonic()-before, 'http_status': response['http_status'],
                'headers': response['headers'], 'error': response['error'], 'body_complete': response['body_complete'],
                'body_bytes': len(body), 'body_sha256': hashlib.sha256(body).hexdigest(),
                'body_base64': base64.b64encode(body).decode()}
            receipts.append(receipt)
            if persist:
                persist(rowid+'-receipt.json', receipt)
            if response['error'] or response['http_status'] != 200 or response['body_complete'] is not True:
                row = {'id': rowid, 'status': 'unavailable', 'reason': response['error'] or 'incomplete HTTP response'}
            else:
                try:
                    fields = parse(body, payload, chain, kind, ended.timestamp(), context)
                    context[kind] = fields
                    row = {'id': rowid, 'status': 'complete', 'fields': fields}
                except (ValueError, TypeError, KeyError, OverflowError) as exc:
                    row = {'id': rowid, 'status': 'unavailable', 'reason': type(exc).__name__+': '+str(exc)}
            rows.append(row)
    summary = {'scope': spec['scope'], 'implementation_admitted': False,
               'reported_network_route': spec['reported_network_route'], 'attempted_requests': attempted,
               'registered_requests': 18, 'cells': rows,
               'unmeasured': ['token bytecode/decimals/safety', 'pool depth and two-way execution',
                  'swap gas and L1 data fees', 'full historical pool/event coverage', 'funding/withdrawal/access costs',
                  'low-cap point-in-time universe', 'profitability and benchmark value']}
    size = sum(len((json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()) for v in [*receipts,summary])
    if size > spec['max_output_bytes']:
        raise ValueError('lifecycle-encoded output cap exceeded; published receipts retained')
    return summary, receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=HERE.parents[1], registration=REGISTRATION, experiment=EXPERIMENT, source=args.source) as run:
        spec = strict_json(run.read_input('spec'))
        run.read_input('ancestry')
        run.read_input('failed_launch')
        summary, _ = capture(spec, persist=run.write_json)
        run.write_json('source-summary.json', summary)
        run.finish([{k:row[k] for k in ('id','status','reason') if k in row} for row in summary['cells']])


if __name__ == '__main__':
    main()

"""Registered protocol-state observations; finite requests, no run wall timer."""
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
ROOT = HERE.parents[1]
EXPERIMENT = 'defi-depth-q1-20260915'
REGISTRATION = 'research/defi-depth-2026-09-15/gates-q1.json'
loader = importlib.util.spec_from_file_location('preserved_dex_helpers', HERE.parent/'broader-allocation-2026-09-15/dex_source.py')
helpers = importlib.util.module_from_spec(loader)
loader.loader.exec_module(helpers)


def decode_words(value, types):
    raw = helpers.hexdata(value, 32*len(types))[2:]
    result = []
    for i, kind in enumerate(types):
        word = int(raw[i*64:(i+1)*64], 16)
        if kind == 'address':
            if word >= 2**160:
                raise ValueError('noncanonical address padding')
            item = '0x'+format(word, '040x')
        elif kind == 'bool':
            if word not in (0, 1):
                raise ValueError('noncanonical Boolean')
            item = bool(word)
        elif re.fullmatch(r'(?:u?int)(?:8|16|24|32|56|128|160|256)', kind):
            bits = int(re.search(r'\d+', kind)[0])
            if kind.startswith('uint'):
                if word >= 2**bits:
                    raise ValueError('noncanonical unsigned padding')
                item = word
            else:
                item = word-2**256 if word >= 2**255 else word
                if not -(2**(bits-1)) <= item < 2**(bits-1):
                    raise ValueError('noncanonical signed extension')
        else:
            raise ValueError('unregistered ABI type')
        result.append(item)
    return result


def envelope(body, payload):
    data = helpers.strict_json(body)
    if not isinstance(data, dict) or data.get('jsonrpc') != '2.0' or data.get('id') != payload['id']:
        raise ValueError('RPC envelope/ID mismatch')
    if 'error' in data or data.get('result') is None:
        raise ValueError('RPC error/null: '+str(data.get('error', 'null result'))[:500])
    return data['result']


def header(result, chain, epoch, observed, context):
    if not isinstance(result, dict):
        raise ValueError('block header required')
    number = helpers.quantity(result.get('number'))
    stamp = helpers.quantity(result.get('timestamp'))
    block_hash = helpers.hexdata(result.get('hash'), 32)
    if not int(block_hash, 16) or not 0 < stamp <= observed:
        raise ValueError('invalid block clock/hash')
    if epoch == 'history':
        old = chain['history_header']
        if (number, stamp, block_hash) != (old['number'], old['timestamp'], old['hash']):
            raise ValueError('historical anchor differs from retained predecessor')
    else:
        old = chain['history_header']
        if number <= old['number'] or stamp <= old['timestamp']:
            raise ValueError('finalized anchor does not follow history')
    return {'number': number, 'timestamp': stamp, 'hash': block_hash,
            'provider_assertion_only': True}


def validate_slot(words):
    price, tick, index, cardinality, next_cardinality, _, _ = words
    if not 4295128739 <= price < 1461446703485210103287273052203988822378723970342:
        raise ValueError('pool price outside initialized v3 bounds')
    if not -887272 <= tick <= 887272:
        raise ValueError('pool tick outside v3 domain')
    if cardinality < 1 or next_cardinality < cardinality or index >= cardinality:
        raise ValueError('invalid initialized oracle cardinality/index')


def cell_ids(spec):
    ids = []
    for chain in spec['chains']:
        prefix = chain['name']+'-'
        ids += [prefix+k for k in ('chain', 'history-header', 'finalized-header')]
        for epoch in spec['epochs']:
            ids += [prefix+epoch+'-'+a['key'] for a in chain['actions']]
            ids += [prefix+epoch+'-'+k for k in spec['consistency_cells']]
    return ids


def capture(spec, publish, fetch=helpers.transport.public_post):
    rows = []
    attempts = 0
    raw_bytes = 0
    began = time.monotonic()
    for chain in spec['chains']:
        context = {}
        denied = False

        def request(key, method, params, parse, dependency=None):
            nonlocal attempts, raw_bytes, denied
            rid = chain['name']+'-'+key
            start = datetime.now(timezone.utc)
            tick = time.monotonic()
            reason = 'endpoint denied; no further request' if denied else dependency
            payload = {'jsonrpc': '2.0', 'id': rid, 'method': method, 'params': params}
            if reason is None:
                attempts += 1
                if attempts > spec['max_requests']:
                    raise ValueError('request inventory exceeded')
                # Intent is durable before transport; a process failure cannot hide a started request.
                publish(rid+'-attempt.json', {'id': rid, 'attempted': True,
                        'request_utc': start.isoformat(), 'url': chain['url'], 'request': payload})
                response = fetch(chain['url'], payload)
            else:
                publish(rid+'-attempt.json', {'id': rid, 'attempted': False, 'reason': reason})
                response = {'body': b'', 'http_status': None, 'headers': {},
                            'error': reason, 'body_complete': False}
            body = response['body']
            if not isinstance(body, bytes) or len(body) > spec['max_response_bytes']:
                raise ValueError('transport response contract violation')
            raw_bytes += len(body)
            if raw_bytes > spec['max_raw_bytes']:
                raise ValueError('declared worst-case byte reservation exceeded')
            if response['http_status'] in spec['http_denials_stop_endpoint']:
                denied = True
            end = datetime.now(timezone.utc)
            receipt = {'id': rid, 'attempted': reason is None, 'url': chain['url'],
                       'request': payload if reason is None else None,
                       'request_utc': start.isoformat(), 'retrieval_utc': end.isoformat(),
                       'elapsed_seconds': time.monotonic()-tick,
                       'http_status': response['http_status'], 'headers': response['headers'],
                       'body_complete': response['body_complete'], 'error': response['error'],
                       'body_bytes': len(body), 'body_sha256': hashlib.sha256(body).hexdigest(),
                       'body_base64': base64.b64encode(body).decode()}
            publish(rid+'-receipt.json', receipt)
            try:
                if response['error'] or response['http_status'] != 200 or not response['body_complete']:
                    raise ValueError(response['error'] or 'incomplete HTTP result')
                value = parse(envelope(body, payload), end.timestamp())
                row = {'id': rid, 'status': 'complete', 'value': value}
            except (ValueError, TypeError, KeyError, OverflowError) as exc:
                row = {'id': rid, 'status': 'unavailable', 'reason': type(exc).__name__+': '+str(exc)}
            rows.append(row)
            publish(rid+'-result.json', row)
            print(json.dumps({'cell': rid, 'status': row['status'], 'attempts': attempts}), flush=True)
            return row

        def parse_chain(value, observed):
            actual = helpers.quantity(value)
            if actual != chain['chain_id']:
                raise ValueError('wrong chain identity')
            return actual

        identity = request('chain', 'eth_chainId', [], parse_chain)
        missing_chain = None if identity['status'] == 'complete' else 'chain identity unavailable'
        for epoch in spec['epochs']:
            tag = hex(chain['historical_block']) if epoch == 'history' else 'finalized'
            row = request(epoch+'-header', 'eth_getBlockByNumber', [tag, False],
                          lambda value, observed: header(value, chain, epoch, observed, context), missing_chain)
            if row['status'] == 'complete':
                context[epoch] = row['value']
        for epoch in spec['epochs']:
            found = {}
            for action in chain['actions']:
                missing = missing_chain or (None if epoch in context else 'canonical header unavailable')
                block = {'blockHash': context[epoch]['hash'], 'requireCanonical': True} if epoch in context else None

                def parse_action(value, observed):
                    decoded = decode_words(value, action['types'])
                    if 'expected' in action and decoded != action['expected']:
                        raise ValueError('contract identity/configuration differs from frozen value')
                    return {'words': decoded, 'block': context[epoch], 'signature': action['signature']}

                row = request(epoch+'-'+action['key'], 'eth_call',
                              [{'to': action['to'], 'data': action['data']}, block], parse_action, missing)
                if row['status'] == 'complete':
                    found[action['key']] = row['value']['words']
            for kind in spec['consistency_cells']:
                rid = chain['name']+'-'+epoch+'-'+kind
                try:
                    if kind == 'aave-supply-identity':
                        required = ('aave-pool-identity', 'aave-underlying', 'usdc-decimals',
                                    'aave-income', 'aave-scaled-supply', 'aave-total-supply')
                        if any(k not in found for k in required):
                            raise ValueError('required Aave source field unavailable')
                        index, scaled, total = (found[k][0] for k in required[-3:])
                        predicted = (scaled*index+5*10**26)//10**27
                        if index <= 0 or abs(predicted-total) > 1:
                            raise ValueError('reserve ray index/scaled supply identity fails')
                        value = {'index_scaled_supply_reconciliation_base_units': total-predicted,
                                 'scope': 'Public protocol supply identity only; cash balance is not user withdrawal capacity'}
                    else:
                        required = ('lp-factory', 'lp-token0', 'lp-token1', 'lp-fee', 'lp-spacing',
                                    'usdc-decimals', 'weth-decimals', 'lp-slot0', 'lp-liquidity',
                                    'lp-fee0', 'lp-fee1', 'lp-lower', 'lp-upper')
                        if any(k not in found for k in required):
                            raise ValueError('required LP source field unavailable')
                        validate_slot(found['lp-slot0'])
                        value = {'positive_active_liquidity': found['lp-liquidity'][0] > 0,
                                 'scope': 'Named pool source coherence; no full historical range, executable capacity or fee return claim'}
                    row = {'id': rid, 'status': 'complete', 'value': value}
                except (ValueError, KeyError, TypeError) as exc:
                    row = {'id': rid, 'status': 'unavailable', 'reason': str(exc)}
                rows.append(row)
                publish(rid+'-result.json', row)
    if [r['id'] for r in rows] != cell_ids(spec):
        raise ValueError('result denominator differs from frozen inventory')
    return {'scope': spec['scope'], 'cells': rows, 'requests': attempts, 'raw_bytes': raw_bytes,
            'elapsed_seconds': time.monotonic()-began, 'elapsed_time_kill': False,
            'financial_outcomes_computed': False, 'implementation_admitted': False,
            'limits': 'Per-request timeout and finite request/body bounds; no overall wall-time or CPU-duration cutoff'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    with ResearchRun.start(root=ROOT, registration=REGISTRATION, experiment=EXPERIMENT, source=args.source) as run:
        spec = helpers.strict_json(run.read_input('spec'))
        grant = helpers.strict_json(run.read_input('phase'))
        if grant['slots']['Q1'] != {'kind': 'source', 'experiment': EXPERIMENT} or grant['elapsed_time_kill'] is not False:
            raise ValueError('phase grant differs from frozen source slot')
        for name in ('old_claim', 'old_source', 'core_ancestry', 'defi_ancestry', 'old_closure',
                     'aave_ethereum', 'aave_base', 'aave_arbitrum'):
            run.read_input(name)
        report = capture(spec, run.write_json)
        run.write_json('summary.json', report)
        run.finish([{k: r[k] for k in ('id', 'status', 'reason') if k in r} for r in report['cells']])


if __name__ == '__main__':
    main()

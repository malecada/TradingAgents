"""R1 exact Q2 source panel repair: split state batches at10, no returns."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from tradingagents.research_defi_repair import ResearchRun

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPERIMENT = 'defi-depth-r1-20260915'
REGISTRATION = 'research/defi-depth-2026-09-15/gates-r1-v2.json'

def module(name, path):
    loader = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(result)
    return result

q1 = module('preserved_depth_q1', HERE/'q1_source.py')
transport = module('depth_q2_transport', HERE/'q2_transport.py')


def batch_envelopes(body, payload):
    data = q1.helpers.strict_json(body)
    expected = {p['id'] for p in payload}
    if not isinstance(data, list):
        raise ValueError('batch response is not a list; no format fallback')
    found = {}
    for item in data:
        if not isinstance(item, dict) or item.get('jsonrpc') != '2.0':
            raise ValueError('invalid batch member')
        rid = item.get('id')
        if not isinstance(rid, str) or rid not in expected or rid in found:
            raise ValueError('extra/duplicate/non-string batch ID')
        found[rid] = item
    # Missing members remain individually unavailable; no retry or aliasing.
    return found


def parse_header(value, expected_number, observed):
    if not isinstance(value, dict):
        raise ValueError('header unavailable')
    h = {k: q1.helpers.quantity(value.get(k)) for k in ('number', 'timestamp', 'baseFeePerGas')}
    h.update({k: q1.helpers.hexdata(value.get(k), 32) for k in ('hash', 'parentHash')})
    if h['number'] != expected_number or not 0 < h['timestamp'] <= observed or not int(h['hash'], 16):
        raise ValueError('header number/clock/hash invalid')
    return h


def bracket(left, right, target):
    if right['number'] != left['number']+1 or right['parentHash'] != left['hash']:
        raise ValueError('adjacent canonical headers do not link')
    if not left['timestamp'] <= target < right['timestamp'] or right['timestamp']-left['timestamp'] != 2:
        raise ValueError('fixed two-second mapping does not bracket target')
    return {'number': left['number'], 'hash': left['hash'], 'timestamp': left['timestamp'],
            'target_timestamp': target, 'provider_assertion_only': True}


def parse_action(result, action):
    if action.get('method') == 'eth_getCode':
        raw = q1.helpers.hexdata(result)
        if raw == '0x':
            raise ValueError('contract deployment absent')
        return {'bytecode_sha256': hashlib.sha256(bytes.fromhex(raw[2:])).hexdigest(), 'bytecode_bytes': len(raw[2:])//2}
    words = q1.decode_words(result, action['types'])
    if 'expected' in action and words != action['expected']:
        raise ValueError('frozen identity/unit differs')
    if action.get('positive') and words[0] <= 0:
        raise ValueError('positive source value required')
    if action.get('nonzero_address') and int(words[0], 16) == 0:
        raise ValueError('implementation/source address absent')
    if action['key'] == 'lp-slot0':
        q1.validate_slot(words)
    return {'words': words}


def actions_for(spec, day):
    return spec['daily_actions'] + (spec['boundary_actions'] if day['date'] in spec['boundaries'] else [])


def cells_for(spec):
    cells = ['base-chain']
    for day in spec['days']:
        prefix = day['date']+'-'
        cells += [prefix+k for k in ('header-left', 'header-right', 'canonical-bracket')]
        cells += [prefix+a['key'] for a in actions_for(spec, day)]
        cells += [prefix+'aave-supply-identity']
    cells += ['cohort-'+year+'-'+kind for year in spec['cohorts'] for kind in ('lending-source', 'lp-source', 'executable-route')]
    return cells


def outputs_for(spec):
    names = ['chain-attempt.json', 'chain-receipt.json', 'chain-result.json']
    for day in spec['days']:
        prefix = day['date']+'-'
        names += [prefix+'headers-'+kind+'.json' for kind in ('attempt','receipt')]
        chunks = (len(actions_for(spec, day))+9)//10
        for number in range(chunks):
            names += [prefix+'state-'+str(number)+'-'+kind+'.json' for kind in ('attempt','receipt')]
        names.append(prefix+'results.json')
    return names+['summary.json']


def repair_bounds(spec):
    http = 1+sum(1+(len(actions_for(spec,day))+9)//10 for day in spec['days'])
    return {'max_http_requests':http, 'max_raw_bytes':http*spec['max_response_bytes'], 'max_batch_members':10}


def capture(spec, publish, fetch=transport.public_post):
    spec = {**spec, **repair_bounds(spec)}  # Authored transport override only; input bytes stay frozen.
    cells = []
    daily = []
    http_requests = rpc_subcalls = raw_bytes = 0
    denied = False
    start = time.monotonic()

    def request(name, members, unavailable=None):
        nonlocal http_requests, rpc_subcalls, raw_bytes, denied
        if not 1 <= len(members) <= 10:
            raise ValueError('repair permits at most10 members per HTTP batch')
        reason = 'endpoint denied; no further requests' if denied else unavailable
        began = datetime.now(timezone.utc)
        tick = time.monotonic()
        intent = {'attempted': reason is None, 'request_utc': began.isoformat(), 'url': spec['url'],
                  'request': members if reason is None else None, 'reason': reason}
        publish(name+'-attempt.json', intent)
        if reason is None:
            http_requests += 1
            rpc_subcalls += len(members)
            if http_requests > spec['max_http_requests'] or rpc_subcalls > spec['max_rpc_subcalls']:
                raise ValueError('frozen request reservation exceeded')
            response = fetch(spec['url'], members)
        else:
            response = {'body': b'', 'http_status': None, 'headers': {}, 'error': reason, 'body_complete': False}
        body = response['body']
        if not isinstance(body, bytes) or len(body) > spec['max_response_bytes']:
            raise ValueError('transport body contract violated')
        raw_bytes += len(body)
        if raw_bytes > spec['max_raw_bytes']:
            raise ValueError('raw byte reservation exceeded')
        if response['http_status'] in (403,418,429,451):
            denied = True
        ended = datetime.now(timezone.utc)
        publish(name+'-receipt.json', {**intent, 'retrieval_utc': ended.isoformat(),
                'elapsed_seconds': time.monotonic()-tick, 'http_status': response['http_status'],
                'headers': response['headers'], 'body_complete': response['body_complete'], 'error': response['error'],
                'body_bytes': len(body), 'body_sha256': hashlib.sha256(body).hexdigest(),
                'body_base64': base64.b64encode(body).decode()})
        try:
            if response['error'] or response['http_status'] != 200 or not response['body_complete']:
                raise ValueError(response['error'] or 'incomplete HTTP response')
            return batch_envelopes(body, members), None, ended.timestamp()
        except (ValueError, TypeError, KeyError) as exc:
            return {}, str(exc), ended.timestamp()

    def decode(rid, members, problem, parser):
        try:
            if problem:
                raise ValueError(problem)
            item = members.get(rid)
            if item is None or 'error' in item or item.get('result') is None:
                raise ValueError('missing/error/null member: '+str(item)[:500])
            row = {'id': rid, 'status': 'complete', 'value': parser(item['result'])}
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            row = {'id': rid, 'status': 'unavailable', 'reason': str(exc)}
        cells.append(row)
        return row

    chain_payload = [{'jsonrpc':'2.0','id':'base-chain','method':'eth_chainId','params':[]}]
    found, reason, _ = request('chain', chain_payload)
    def chain_value(value):
        actual = q1.helpers.quantity(value)
        if actual != 8453:
            raise ValueError('wrong chain identity')
        return actual
    chain = decode('base-chain', found, reason, chain_value)
    publish('chain-result.json', chain)
    for n, day in enumerate(spec['days'], 1):
        date, target, height = day['date'], day['timestamp'], day['candidate_block']
        prefix = date+'-'
        rows_start = len(cells)
        payload = [{'jsonrpc':'2.0','id':prefix+'header-'+side,'method':'eth_getBlockByNumber','params':[hex(height+offset),False]}
                   for offset, side in enumerate(('left','right'))]
        missing = None if chain['status'] == 'complete' else 'chain identity unavailable'
        found, reason, observed = request(prefix+'headers', payload, missing)
        left = decode(prefix+'header-left', found, reason, lambda value: parse_header(value, height, observed))
        right = decode(prefix+'header-right', found, reason, lambda value: parse_header(value, height+1, observed))
        try:
            if left['status'] != 'complete' or right['status'] != 'complete':
                raise ValueError('one or both adjacent headers unavailable')
            block = bracket(left['value'], right['value'], target)
            anchor = {'id':prefix+'canonical-bracket','status':'complete','value':block}
        except (ValueError, KeyError) as exc:
            block = None
            anchor = {'id':prefix+'canonical-bracket','status':'unavailable','reason':str(exc)}
        cells.append(anchor)
        actions = actions_for(spec, day)
        tag = {'blockHash':block['hash'],'requireCanonical':True} if block else None
        payload = []
        for action in actions:
            method = action.get('method','eth_call')
            if method == 'eth_call':
                params = [{'to':action['to'],'data':action['data']},tag]
            elif method == 'eth_getStorageAt':
                params = [action['to'],action['slot'],tag]
            else:
                params = [action['to'],tag]
            payload.append({'jsonrpc':'2.0','id':prefix+action['key'],'method':method,'params':params})
        found, problems = {}, {}
        for number, offset in enumerate(range(0,len(payload),10)):
            chunk = payload[offset:offset+10]
            result, problem, _ = request(prefix+'state-'+str(number),chunk,
                    missing or (None if block else 'canonical bracket unavailable'))
            found.update(result)
            problems.update({member['id']:problem for member in chunk})
        values = {}
        for action in actions:
            row = decode(prefix+action['key'], found, problems[prefix+action['key']], lambda value: parse_action(value, action))
            if row['status'] == 'complete':
                values[action['key']] = row['value']
        try:
            index, scaled, total = [values[k]['words'][0] for k in ('aave-income','aave-scaled-supply','aave-total-supply')]
            residual = total-(scaled*index+5*10**26)//10**27
            if index <= 0 or abs(residual) > 1:
                raise ValueError('scaled/index supply identity mismatch')
            row = {'id':prefix+'aave-supply-identity','status':'complete','value':{'residual_base_units':residual}}
        except (ValueError, KeyError) as exc:
            row = {'id':prefix+'aave-supply-identity','status':'unavailable','reason':str(exc)}
        cells.append(row)
        day_rows = cells[rows_start:]
        publish(prefix+'results.json', {'day':day, 'canonical_block':block, 'cells':day_rows,
                 'scope':'Source states and provider valuation proxies; no cashflow or execution admission'})
        daily.append({'date':date,'complete':sum(r['status']=='complete' for r in day_rows),
                      'unavailable':sum(r['status']=='unavailable' for r in day_rows)})
        print(json.dumps({'date':date,'day':n,'days':len(spec['days']),'http_requests':http_requests,
                          'rpc_subcalls':rpc_subcalls,'unavailable':daily[-1]['unavailable']}),flush=True)
    row_map = {r['id']:r for r in cells}
    for year, cohort in spec['cohorts'].items():
        dates = [d['date'] for d in spec['days'] if cohort['start'] <= d['date'] <= cohort['end']]
        for kind in ('lending-source','lp-source','executable-route'):
            rid = 'cohort-'+year+'-'+kind
            keys = spec['coverage_fields'].get(kind, [])
            absent = [date+'-'+key for date in dates for key in keys if row_map[date+'-'+key]['status'] != 'complete']
            if kind == 'executable-route':
                row = {'id':rid,'status':'unavailable','reason':'Historical executable swaps, complete L1/L2 gas, user funding/exit and withdrawal/version terms not established by source states'}
            elif absent:
                row = {'id':rid,'status':'unavailable','reason':f'{len(absent)} required daily source cells unavailable',
                       'value':{'missing_ids':absent,'days':len(dates)}}
            else:
                row = {'id':rid,'status':'complete','value':{'days':len(dates),'scope':'Daily field coverage only; no financial or deployment/version admission'}}
            cells.append(row)
    if [r['id'] for r in cells] != cells_for(spec):
        raise ValueError('result denominator differs from registration')
    return {'cells':cells,'daily':daily,'http_requests':http_requests,'rpc_subcalls':rpc_subcalls,
            'raw_bytes':raw_bytes,'elapsed_seconds':time.monotonic()-start,'elapsed_time_kill':False,
            'financial_outcomes_computed':False,'implementation_admitted':False, 'repair_transport_bounds':repair_bounds(spec)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True)
    args = p.parse_args()
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        spec = q1.helpers.strict_json(run.read_input('spec'))
        phase = q1.helpers.strict_json(run.read_input('phase'))
        if phase['slots']['R1']['experiment'] != EXPERIMENT or phase['slots']['R1']['kind'] != 'repair' or phase['elapsed_time_kill'] is not False:
            raise ValueError('wrong phase slot')
        for name in run.admission.inputs:
            if name not in ('spec','phase'):
                run.read_input(name)
        report = capture(spec,run.write_json)
        run.write_json('summary.json',report)
        run.finish([{k:r[k] for k in ('id','status','reason') if k in r} for r in report['cells']])

if __name__ == '__main__':
    main()

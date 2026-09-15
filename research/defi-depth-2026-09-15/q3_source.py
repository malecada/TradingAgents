"""Frozen Q3 staking source collection; no financial outcomes or retries."""
import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
from tradingagents.research import ResearchRun

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPERIMENT = 'defi-depth-q3-20260915'
REGISTRATION = 'research/defi-depth-2026-09-15/gates-q3.json'
loader = importlib.util.spec_from_file_location('staking_q3_protocol', HERE/'q3_protocol.py')
p = importlib.util.module_from_spec(loader)
loader.loader.exec_module(p)
old = p.old


def member(rid, method, params):
    return {'jsonrpc': '2.0', 'id': rid, 'method': method, 'params': params}


def action_member(rid, action, block):
    tag = {'blockHash': block['hash'], 'requireCanonical': True} if block else None
    params = [{'to': action['to'], 'data': action['data']}, tag] if action['method'] == 'eth_call' else [action['to'], tag]
    return member(rid, action['method'], params)


def unavailable(reason):
    return {'status': 'unavailable', 'reason': reason}


def manifests(design, days):
    """All potential request outputs and skipped cells remain in denominator."""
    requests = ['ethereum-chain', 'base-chain']
    cells = ['history-integrity', 'ethereum-anchor', 'ethereum-chain']
    eth = ['ethereum-'+a['key'] for a in design['chains']['ethereum']['actions']]
    requests += eth
    cells += eth + ['ethereum-conversion-consistency', 'ethereum-queue-consistency', 'base-chain']
    outputs = ['history.json', 'ethereum.json', 'boundaries.json', 'summary.json']
    new = {d['date'] for d in design['new_header_days']}
    boundaries = design['chains']['base']['boundary_dates']
    for day in days:
        date = day['date']; prefix = 'base-'+date+'-'
        if date in new:
            requests += [prefix+'header-'+side for side in ('left', 'right')]
            cells += [prefix+'header-'+side for side in ('left', 'right')]
        cells += [prefix+'canonical-bracket']
        actions = list(design['chains']['base']['daily_actions'])
        if date in boundaries:
            actions += design['chains']['base']['boundary_actions']
            actions += design['chains']['base']['imported_boundary_actions']
            actions += [design['chains']['base']['dependent_boundary_action']]
        for action in actions:
            cells.append(prefix+action['key'])
            if not (date == boundaries[0] and action['key'] in ('oracle-unit', 'oracle-base')):
                requests.append(prefix+action['key'])
        if date in boundaries:
            cells.append(prefix+'boundary-eligibility')
        outputs.append(prefix+'results.json')
    for year in design['cohorts']:
        cells += ['cohort-'+year+'-'+kind for kind in ('boundary-eligibility', 'daily-source', 'semantic-qualification', 'executable-route')]
    cells += ['native-historical-conversions', 'historical-queue-waits']
    outputs += [rid+'-'+kind+'.json' for rid in requests for kind in ('attempt', 'receipt')]
    if len(requests) != design['max_rpc_subcalls'] or len(set(outputs)) != len(outputs) or len(set(cells)) != len(cells):
        raise ValueError('duplicate denominator or request reservation differs')
    return cells, outputs


def retained_context(design, days, inputs):
    """Qualify exact pinned receipts; no transport or financial calculations."""
    receipts = {date: inputs['r1-header-'+date] for date in [d['date'] for d in days if d['date'] <= '2023-11-28']}
    keys = p.prior_header_keys(receipts.values())
    planned = p.new_header_plan(design, days, keys)
    if len(keys) != 176 or len(planned) != 1008:
        raise ValueError('retained/new header inventory differs')
    r1 = inputs['r1_claim']; terminal = inputs['r1_terminal']
    if r1['experiment_id'] != 'defi-depth-r1-20260915' or r1['source'] != 'aa926ef5c3ce3c0125af6bfc43d4b84bec80acfa':
        raise ValueError('wrong R1 source lineage')
    if not terminal or 'KeyboardInterrupt' not in json.dumps(terminal):
        raise ValueError('R1 provider-stop terminal differs')
    q1spec = inputs['q1_spec']
    chain = next(c for c in q1spec['chains'] if c['name'] == 'ethereum')
    receipt = inputs['ethereum_header_receipt']
    envelopes = p._raw_envelopes(receipt)
    raw = envelopes['ethereum-finalized-header']['result']
    anchor = old.q1.header(raw, chain, 'finalized', datetime.fromisoformat(receipt['retrieval_utc']).timestamp(), {})
    if receipt['request'] != member('ethereum-finalized-header','eth_getBlockByNumber',['finalized',False]) or inputs['ethereum_header_result'].get('value') != anchor:
        raise ValueError('Q1 finalized anchor/raw identity differs')
    first = days[0]
    bracket = p.qualify_retained_bracket(first, receipts[first['date']])
    imported = {}
    for action in design['chains']['base']['imported_boundary_actions']:
        rid = first['date']+'-'+action['key']
        expected = action_member(rid, action, bracket.get('value'))
        try:
            if bracket['status'] != 'complete':
                raise ValueError('R1 first boundary bracket unavailable')
            matches = [r for r in inputs['r1_boundary_receipts'] if r['attempted'] and expected in r['request']]
            if len(matches) != 1:
                raise ValueError('exact first boundary state request missing/duplicate')
            response = p._raw_envelopes(matches[0]).get(rid, {})
            if 'error' in response or response.get('result') is None:
                raise ValueError('retained first boundary state unavailable')
            imported[action['key']] = {'status':'complete','value':old.parse_action(response['result'],action), 'source_role':'retained R1 raw'}
        except (ValueError, KeyError, TypeError) as exc:
            imported[action['key']] = unavailable(str(exc))
    return {'headers':receipts, 'new_headers':planned, 'ethereum_anchor':anchor,
            'first_boundary':imported, 'prior_header_keys':sorted(keys)}


def public_post(url, payload):
    return (old.transport.public_post if url == 'https://mainnet.base.org' else old.q1.helpers.transport.public_post)(url,payload)


def capture(design, days, context, publish, fetch=public_post, **clocks):
    source = p.PacedSource(design,publish,fetch,**clocks)
    rows = {}
    def save(rid, row):
        if rid in rows:
            raise ValueError('duplicate source cell')
        rows[rid] = {**row,'id':rid}
        return rows[rid]
    save('history-integrity', {'status':'complete','value':{'attempted_header_keys':len(context['prior_header_keys']), 'new_header_dates':len(context['new_headers'])}})
    publish('history.json', {'prior_header_keys':context['prior_header_keys'], 'scope':'exact attempted-key exclusion; original results unchanged'})
    save('ethereum-anchor', {'status':'complete','value':context['ethereum_anchor']})
    def chain_identity(chain):
        def parse(value, observed):
            actual = old.q1.helpers.quantity(value)
            if actual != design['chains'][chain]['chain_id']:
                raise ValueError('chain identity differs')
            return actual
        rid=chain+'-chain'
        return save(rid,source.request(chain,member(rid,'eth_chainId',[]),parse))
    eth = chain_identity('ethereum')
    eth_values = {}
    for action in design['chains']['ethereum']['actions']:
        rid='ethereum-'+action['key']
        row = source.request('ethereum',action_member(rid,action,context['ethereum_anchor']),
                             lambda value, observed: old.parse_action(value,action),
                             dependency=None if eth['status']=='complete' else 'chain identity unavailable')
        eth_values[action['key']] = save(rid,row)
    for kind in ('conversion','queue'):
        try:
            required = ('steth-per-wrapper','wrapper-per-steth','one-wrapper-conversion','one-steth-conversion') if kind=='conversion' else ('queue-last-request','queue-last-finalized','queue-unfinalized-count')
            if any(eth_values[k]['status']!='complete' for k in required):
                raise ValueError('required interface observations unavailable')
            values=[eth_values[k]['value']['words'][0] for k in required]
            if kind=='conversion' and (values[0]!=values[2] or values[1]!=values[3]):
                raise ValueError('one-unit conversion views disagree')
            if kind=='queue' and (values[1]>values[0] or values[0]-values[1]!=values[2]):
                raise ValueError('queue ID/count views disagree')
            row={'status':'complete','scope':'same-block interface identities only; no staking yield or investor wait'}
        except (ValueError,KeyError,TypeError) as exc:
            row=unavailable(str(exc))
        save('ethereum-'+kind+'-consistency',row)
    publish('ethereum.json', {'cells':[r for k,r in rows.items() if k.startswith('ethereum-')]})
    base = chain_identity('base')
    cfg=design['chains']['base']; boundaries={}; day_map={d['date']:d for d in days}
    def collect_day(date, eligible=True):
        day=day_map[date]; prefix='base-'+date+'-'; local={}
        missing = 'chain identity unavailable' if base['status']!='complete' else (None if eligible else 'fixed cohort boundary qualification unavailable')
        if date in context['headers']:
            bracket = p.qualify_retained_bracket(day,context['headers'][date])
            if missing:
                bracket=unavailable(missing)
        else:
            headers=[]
            for i, item in enumerate(context['new_headers'][date]):
                item={**item,'id':prefix+'header-'+('left','right')[i]}
                row=source.request('base',item,lambda value,observed:old.parse_header(value,day['candidate_block']+i,observed),dependency=missing)
                save(item['id'],row); headers.append(row)
            try:
                if any(r['status']!='complete' for r in headers):
                    raise ValueError('one or both adjacent headers unavailable')
                bracket={'status':'complete','value':old.bracket(headers[0]['value'],headers[1]['value'],day['timestamp'])}
            except (ValueError,KeyError,TypeError) as exc:
                bracket=unavailable(str(exc))
        local['canonical-bracket']=save(prefix+'canonical-bracket',bracket)
        block=bracket.get('value') if bracket['status']=='complete' else None
        missing = missing or (None if block else 'canonical bracket unavailable')
        actions = list(cfg['daily_actions'])
        if date in cfg['boundary_dates']:
            actions += cfg['boundary_actions']+cfg['imported_boundary_actions']+[cfg['dependent_boundary_action']]
        for original in actions:
            action=dict(original); reason=missing
            if date==cfg['boundary_dates'][0] and action['key'] in context['first_boundary']:
                row=context['first_boundary'][action['key']] if not missing else unavailable(missing)
            else:
                if action['key']=='oracle-source-code':
                    parent=local['oracle-wsteth-source']
                    if parent['status']!='complete':
                        reason=reason or 'same-block oracle source address unavailable'
                        action['to']='0x'+'0'*40
                    else:
                        action['to']=parent['value']['words'][0]
                rid=prefix+action['key']
                row=source.request('base',action_member(rid,action,block),lambda value,observed:old.parse_action(value,action),dependency=reason)
            local[action['key']]=save(prefix+action['key'],row)
        if date in cfg['boundary_dates']:
            boundaries[date]=p.boundary_eligibility(local)
            save(prefix+'boundary-eligibility',boundaries[date])
        publish(prefix+'results.json',{'day':day,'block':block,'cells':list(local.values()),'scope':'source only; oracle is not an executable price'})
        print(json.dumps({'date':date,'requests':source.http_requests,'unavailable':sum(r['status']=='unavailable' for r in local.values()),'endpoint_stopped':source.stopped}),flush=True)
    for date in cfg['boundary_dates']:
        collect_day(date)
    eligible=p.cohort_eligibility(design['cohorts'],boundaries)
    publish('boundaries.json', {'boundaries':boundaries,'cohorts':eligible,'selection':'source observability only; positive price magnitude never used'})
    for day in days:
        if day['date'] not in cfg['boundary_dates']:
            collect_day(day['date'],p.day_eligible(day['date'],design['cohorts'],eligible))
    for year,cohort in design['cohorts'].items():
        save('cohort-'+year+'-boundary-eligibility',eligible[year])
        dates=[d['date'] for d in days if cohort['start']<=d['date']<=cohort['end']]
        required=['base-'+date+'-'+key for date in dates for key in ('canonical-bracket','oracle-wsteth-price','oracle-wsteth-source')]
        absent=[k for k in required if rows[k]['status']!='complete']
        addresses=[rows['base-'+date+'-oracle-wsteth-source'].get('value',{}).get('words',[None])[0] for date in dates]
        changes=[date for date,a,b in zip(dates[1:],addresses,addresses[1:]) if a is not None and b is not None and a!=b]
        row=unavailable('Missing '+str(len(absent))+' required daily source cells') if absent else {'status':'complete','scope':'daily oracle observations only'}
        save('cohort-'+year+'-daily-source',{**row,'missing_cells':absent,'source_address_change_dates':changes})
        save('cohort-'+year+'-semantic-qualification',unavailable('Four code snapshots do not establish uninterrupted oracle/proxy/version semantics'))
        save('cohort-'+year+'-executable-route',unavailable('Two-way wrapper prices, full gas, funding/bridge/redemption and terminal USD exit unavailable'))
    save('native-historical-conversions',unavailable('Ethereum single qualified finalized anchor is not a historical conversion panel'))
    save('historical-queue-waits',unavailable('Aggregate queue views do not determine counterfactual request finalization/claim cash or waiting time'))
    ids,_=manifests(design,days)
    if set(rows)!=set(ids):
        raise ValueError('source cell denominator differs')
    return {'cells':[rows[k] for k in ids], 'http_requests':source.http_requests,'rpc_subcalls':source.rpc_subcalls,'raw_bytes':source.raw_bytes,
            'endpoint_stops':source.stopped,'financial_outcomes_computed':False,'elapsed_time_kill':False,'implementation_admitted':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        gate=json.loads((ROOT/REGISTRATION).read_text())['experiments'][EXPERIMENT]
        inputs={name:old.q1.helpers.strict_json(run.read_input(name)) for name in gate['inputs'] if not name.endswith('_text')}
        for name in gate['inputs']:
            if name.endswith('_text'):run.read_input(name)
        design=inputs['design'];days=inputs['calendar']['days']
        if inputs['phase']['slots']['Q3']!={'kind':'source','experiment':EXPERIMENT} or inputs['phase']['elapsed_time_kill'] is not False:
            raise ValueError('phase source slot differs')
        inputs['r1_boundary_receipts']=[inputs['r1_boundary_'+str(i)] for i in range(3)]
        context=retained_context(design,days,inputs)
        result=capture(design,days,context,run.write_json)
        run.write_json('summary.json',result)
        run.finish([{k:r[k] for k in ('id','status','reason') if k in r} for r in result['cells']])


if __name__=='__main__':main()

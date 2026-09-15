"""F2 indivisible acquisition and conditional financial attempt; no CLI until admitted."""
import argparse
from datetime import datetime
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research import ResearchRun
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=module('f2_retained_q3','q3_source.py');p=q.p
book=module('f2_wallet_book','wrapper_book.py')
EXPERIMENT='defi-depth-f2-20260915';REGISTRATION='research/defi-depth-2026-09-15/gates-f2.json'
TOKENS={'ETH':'0x4200000000000000000000000000000000000006','USDC':book.ASSETS['USDC'][1],'WST':book.ASSETS['WST'][1]}
ORACLE='0x2cc0fc26ed4563a5ce5e8bdcfe1a2878676ae156'
RETAINED=('2025-09-01','2026-09-01')

def encode_prices(assets):
    if not assets or len(set(assets))!=len(assets) or any(a not in TOKENS for a in assets):raise ValueError('fixed unique asset vector required')
    return '0x9d23d9f2'+format(32,'064x')+format(len(assets),'064x')+''.join(TOKENS[a][2:].rjust(64,'0') for a in assets)

def parse_prices(value,assets):
    raw=p.old.q1.helpers.hexdata(value)
    if len(raw)!=2+64*(len(assets)+2):raise ValueError('price vector ABI length mismatch')
    words=[int(raw[i:i+64],16) for i in range(2,len(raw),64)]
    if words[:2]!=[32,len(assets)] or any(v<=0 for v in words[2:]):raise ValueError('invalid dynamic ABI or nonpositive price')
    return dict(zip(assets,words[2:]))

def manifests(design):
    cells=['retained-history','source-annual-panel'];outputs=['history.json','source-summary.json','financial-summary.json'];requests=[]
    for day in design['days']:
        prefix=day['date']+'-'
        cells += [prefix+k for k in ('header-left','header-right','canonical-bracket','oracle-prices')]
        if day['date'] not in RETAINED:requests += [prefix+'header-left',prefix+'header-right']
        requests.append(prefix+'oracle-prices');outputs.append(prefix+'source.json')
    for year in ('2024','2025','2026'):
        for policy in book.POLICIES:
            for scenario in book.SCENARIOS:
                cid=year+'-'+policy.lower()+'-'+scenario;cells.append(cid);outputs.append(cid+'.json')
    for scenario in book.SCENARIOS:
        for baseline in ['B'+str(i) for i in range(10)]+['wallet-ETH25','wallet-cash']:
            cells.append('D-'+scenario+'-'+baseline)
    cells+=['primary-decision','implementation','confirmation']
    outputs += [rid+'-'+kind+'.json' for rid in requests for kind in ('attempt','receipt')]
    assert len(requests)==design['max_rpc_subcalls']
    assert len(set(cells))==len(cells) and len(set(outputs))==len(outputs)
    return cells,outputs

def retained(inputs,design):
    context={};prior=set(inputs['attempt_history']['base_header_keys'])
    if len(prior)!=182:raise ValueError('expected 182 attempted historical Base header keys')
    if design['prior_base_request_keys']!=inputs['attempt_history']['all_base_request_keys']:raise ValueError('prior request exclusion inventory mismatch')
    for day in design['days']:
        date=day['date']
        if date not in RETAINED:
            for off in (0,1):
                key=p.request_key('eth_getBlockByNumber',[hex(day['candidate_block']+off),False])
                if key in prior:raise ValueError('new planned header was already attempted')
            continue
        headers=[]
        for off,side in enumerate(('left','right')):
            receipt=inputs[date+'-header-'+side]
            expected=q.member('base-'+date+'-header-'+side,'eth_getBlockByNumber',[hex(day['candidate_block']+off),False])
            if receipt['request']!=expected:raise ValueError('retained header identity differs')
            value=p._raw_envelopes(receipt)[expected['id']]['result']
            headers.append(p.old.parse_header(value,day['candidate_block']+off,datetime.fromisoformat(receipt['retrieval_utc']).timestamp()))
        block=p.old.bracket(*headers,day['timestamp'])
        published=inputs[date+'-source'];cells={r['id'].removeprefix('base-'+date+'-'):r for r in published['cells']}
        if p.boundary_eligibility(cells)['status']!='complete' or published['block']!=block:raise ValueError('retained boundary unqualified')
        action=next(a for a in inputs['q3_design']['chains']['base']['daily_actions'] if a['key']=='oracle-wsteth-price')
        receipt=inputs[date+'-wst-receipt'];expected=q.action_member('base-'+date+'-oracle-wsteth-price',action,block)
        if receipt['request']!=expected:raise ValueError('retained wrapper price identity mismatch')
        price=p.old.parse_action(p._raw_envelopes(receipt)[expected['id']]['result'],action)['words'][0]
        if cells['oracle-wsteth-price']['value']['words']!=[price]:raise ValueError('retained raw/parsed wrapper mismatch')
        context[date]={'headers':headers,'block':block,'wst_price':price}
    return context

def capture(design,context,publish,fetch=q.public_post,**clocks):
    source=p.PacedSource(design,publish,fetch,**clocks);rows=[];cells=[];stop=None
    days={d['date']:d for d in design['days']}
    seen=set(design['prior_base_request_keys'])
    def request(chain,member,parser,dependency=None):
        key=p.request_key(member['method'],member['params'])
        if dependency is None and chain not in source.stopped:
            if key in seen:raise ValueError('prior or same-run request key would be retried')
            seen.add(key)
        return source.request(chain,member,parser,dependency=dependency)
    for date in design['acquisition_order']:
        day=days[date]
        date=day['date'];local=[];headers=[]
        for off,side in enumerate(('left','right')):
            rid=date+'-header-'+side
            if date in context:row={'id':rid,'status':'complete','value':context[date]['headers'][off],'source_role':'retained Q3 raw'}
            else:row=request('base',q.member(rid,'eth_getBlockByNumber',[hex(day['candidate_block']+off),False]),lambda v,t,off=off:p.old.parse_header(v,day['candidate_block']+off,t),dependency=stop)
            headers.append(row);local.append(row)
        try:
            if any(r['status']!='complete' for r in headers):raise ValueError('canonical header unavailable')
            block=p.old.bracket(*(r['value'] for r in headers),day['timestamp'])
            bracket={'id':date+'-canonical-bracket','status':'complete','value':block}
        except (ValueError,TypeError,KeyError) as exc:
            block=None;bracket={'id':date+'-canonical-bracket','status':'unavailable','reason':str(exc)}
        local.append(bracket)
        assets=['ETH','USDC'] if date in context else ['WST','ETH','USDC']
        member=q.member(date+'-oracle-prices','eth_call',[{'to':ORACLE,'data':encode_prices(assets)},{'blockHash':block['hash'],'requireCanonical':True} if block else None])
        row=request('base',member,lambda v,t:parse_prices(v,assets),dependency=stop or (None if block else 'canonical bracket unavailable'))
        local.append(row)
        if row['status']=='complete':
            prices=dict(row['value'])
            if date in context:prices['WST']=context[date]['wst_price']
            rows.append({'date':date,'prices_atoms_1e8':prices,'block':block})
        else:
            stop=stop or 'First missing indispensable daily mark; financial panel unavailable, no later acquisition or replacement'
        if bracket['status']!='complete':stop=stop or 'First missing indispensable canonical bracket'
        publish(date+'-source.json',{'day':day,'cells':local,'complete_price_vector':rows[-1] if rows and rows[-1]['date']==date else None,'stop':stop})
        cells+=local
        print(json.dumps({'date':date,'http_requests':source.http_requests,'raw_bytes':source.raw_bytes,'stop':stop,'endpoint_stopped':source.stopped}),flush=True)
    complete=len(rows)==366
    summary={'status':'complete' if complete else 'unavailable','reason':None if complete else stop,'price_rows':sorted(rows,key=lambda r:r['date']),'rpc_requests':source.rpc_subcalls,'raw_bytes':source.raw_bytes,'stopped':source.stopped,
      'scope':'conditional oracle valuation vectors, no executable price or continuous freshness guarantee'}
    publish('source-summary.json',summary)
    cells.append({'id':'source-annual-panel','status':summary['status'],**({'reason':stop} if not complete else {})})
    return summary,cells

def unavailable(reason):return {'status':'unavailable','reason':reason,'implementation_admitted':False,'promotion_admitted':False}

def financial(summary,benchmarks,publish):
    cells=[];results={};comparisons={};defect=None
    panel=[{'date':r['date'],'prices':{a:F(v,10**8) for a,v in r['prices_atoms_1e8'].items()}} for r in summary['price_rows']] if summary['status']=='complete' else None
    for year in ('2024','2025','2026'):
        for policy in book.POLICIES:
            for scenario in book.SCENARIOS:
                cid=year+'-'+policy.lower()+'-'+scenario
                if year!='2026':out=unavailable('Earlier frozen cohort lacks complete retained prerequisites; no backfill in F2')
                elif panel is None:out=unavailable('Indivisible F2 daily source prerequisite unavailable')
                elif defect:out=unavailable('Not attempted after financial measurement defect: '+defect)
                else:
                    progress={}
                    try:out={**book.run_book(panel,policy,scenario,progress=progress),'status':'complete'}
                    except (ValueError,ArithmeticError) as exc:
                        defect=type(exc).__name__+': '+str(exc)
                        out={**unavailable('Financial measurement failure: '+defect),'partial':book.partial_snapshot(progress)}
                publish(cid+'.json',out);cells.append({'id':cid,'status':out['status'],**({'reason':out['reason']} if out['status']!='complete' else {})})
                if year=='2026':results[(policy,scenario)]=out
    for scenario in book.SCENARIOS:
        contrasts={};candidate=results[('F2',scenario)]
        for name in ['B'+str(i) for i in range(10)]+['wallet-ETH25','wallet-cash']:
            other=results[(name,scenario)] if name.startswith('wallet-') else benchmarks[name][scenario]
            if candidate['status']!=other['status'] or candidate['status']!='complete':row=unavailable('Candidate or fixed comparator unavailable')
            else:
                difference=F(candidate['net_cash_profit_usd'])-F(other['net_cash_profit_usd'])
                row={'status':'complete','difference_usd':book.render(difference),'incremental_floor_pass_conditional':difference>=200,
                     'benchmark_numeric_risk_pass':other.get('numerical_risk_pass_conditional',other.get('conditional_numeric_risk_pass')),
                     'basis':'same-block same-oracle wallet control' if name.startswith('wallet-') else 'retained CEX book; oracle/bar/route basis differs, not clean mechanism attribution'}
            contrasts[name]=row;cells.append({'id':'D-'+scenario+'-'+name,'status':row['status'],**({'reason':row['reason']} if row['status']!='complete' else {})})
        comparisons[scenario]=contrasts
    primary=results[('F2','primary')]
    known=[r for r in comparisons['primary'].values() if r['status']=='complete' and r['benchmark_numeric_risk_pass'] is True]
    numeric=primary['status']=='complete' and primary['absolute_floor_pass_conditional'] and primary['numerical_risk_pass_conditional'] and all(r['incremental_floor_pass_conditional'] for r in known)
    decision={'status':'unavailable','reason':'Actual B1, executable routes, lock/horizon cash and independent fresh confirmation unavailable',
      'known_comparator_numerical_pass_only':numeric,'primary_scenario':'primary','absolute_target_usd':1000,'incremental_target_usd':200,
      'all_comparators_retained':True,'no_metric_substitution':True,'promotion_admitted':False}
    cells += [{'id':k,**unavailable(decision['reason'])} for k in ('primary-decision','implementation','confirmation')]
    publish('financial-summary.json',{'cells':cells,'comparisons':comparisons,'primary_decision':decision,'scope':'one exposed development recipe, no validation or selection'})
    return cells

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);a=parser.parse_args()
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=a.source) as run:
        inputs={name:json.loads(run.read_input(name)) for name in run.admission.experiment['inputs'] if not name.endswith('_text')}
        design=inputs['design'];context=retained(inputs,design)
        run.write_json('history.json',{'base_header_keys':inputs['attempt_history']['base_header_keys'],'source_failures_preserved':True,'no_prior_key_retry':True})
        summary,cells=capture(design,context,run.write_json)
        cells.append({'id':'retained-history','status':'complete'})
        cells+=financial(summary,inputs['benchmarks'],run.write_json)
        run.finish(cells)
if __name__=='__main__':main()

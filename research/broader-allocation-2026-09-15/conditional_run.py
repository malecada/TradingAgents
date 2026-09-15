"""Registered fixed conditional books; no network or discretionary parameter search."""
import argparse
from datetime import datetime,timezone
from decimal import Decimal as D
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from tradingagents.research import ResearchRun
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('registered_conditional_book',HERE/'conditional_book.py');engine=importlib.util.module_from_spec(s);s.loader.exec_module(engine)
SCENARIOS=('primary','doubled','frictionless')
RECIPES=('H2','H3','H4','H5')
SPEC_HASH='b9db53367e4b4a3e8d59e444b0019e32bb65dc9093a398c8c92c76a1c427b908'


def compact(result):
    return {k:v for k,v in result.items() if k not in ('states','events','decisions')}


def known_unavailable(reason,partial=None):
    return {'status':'unavailable','reason':reason,'partial':partial,'implementation_admitted':False,'promotion_admitted':False}


def partial_snapshot(progress):
    partial={k:v for k,v in progress.items() if k!='book'}
    if 'book' in progress:
        book=progress['book']
        partial['balances']={a:str(v) for a,v in engine.balances(book).items()}
        partial['literal_ledger_events']=[{'id':e['id'],'kind':e['kind'],'deltas':[{'location':k[0],'asset':k[1],'quantity_delta':str(v)} for k,v in e['deltas'].items()]} for e in book.events]
        rebuilt={a:D(v) for a,v in partial['initial_balances'].items()}
        for event in partial['literal_ledger_events']:
            for delta in event['deltas']:rebuilt[delta['asset']]=rebuilt.get(delta['asset'],D(0))+D(delta['quantity_delta'])
        partial['literal_balances_reconciled']=rebuilt=={a:D(v) for a,v in partial['balances'].items()}
        if not partial['literal_balances_reconciled']:raise ValueError('partial literal ledger/balances do not reconcile')
    return partial


def execute(panel,recipe,publish,benchmarks=None,deadline=None):
    if recipe not in RECIPES:raise ValueError('unregistered recipe')
    policies=(recipe,*('B'+str(i) for i in range(10))) if recipe=='H2' else (recipe,)
    baseline={} if benchmarks is None else benchmarks
    cells=[];own={};diagnostics={};defect=False
    def calculate(policy,scenario,lagged=None):
        nonlocal defect
        tag=policy.lower()+'-'+scenario+('-placebo' if lagged is not None else '')
        attempted=not defect and (deadline is None or time.monotonic()<=deadline)
        publish(tag+'-attempt.json',{'attempted':attempted,'policy':policy,'scenario':scenario,'diagnostic':lagged is not None,'started_utc':datetime.now(timezone.utc).isoformat(),'capital_usd':'10000','scope':'conditional historical bar/USD proxies'})
        if defect or (deadline is not None and time.monotonic()>deadline):
            return known_unavailable('not attempted after measurement defect/cooperative deadline')
        progress={}
        try:
            out=engine.run_book(panel,policy,scenario,lagged_instructions=lagged,with_stress=lagged is None,progress=progress,deadline=deadline)
            out['status']='complete'
            out['conditional_numeric_risk_pass']=(D(out['observed_discrete_max_drawdown'])<=D('.30') and all(D(v['loss_fraction'])<=D('.50') for k,v in out['stress'].items() if k!='total-binance-loss')) if lagged is None else None
            return out
        except (ValueError,ArithmeticError,TimeoutError) as exc:
            reason=type(exc).__name__+': '+str(exc)
            missing='zero or unavailable realized volatility' in str(exc) or 'insufficient trend warmup' in str(exc) or 'insufficient volatility warmup' in str(exc)
            if not missing:defect=True
            partial=partial_snapshot(progress)
            return {**known_unavailable(reason,partial),'classification':'undefined registered signal' if missing else 'measurement defect or resource failure'}
    for policy in policies:
        baseline.setdefault(policy,{}) if policy.startswith('B') else None
        for scenario in SCENARIOS:
            tag=policy.lower()+'-'+scenario
            if policy=='B1':
                publish(tag+'-attempt.json',{'policy':policy,'scenario':scenario,'attempted':False,'reason':'actual cash vehicle unestablished; not replaced by B0'})
                out=known_unavailable('Actual accessible cash vehicle B1 and its costs/valuation/access are unestablished.')
            else:out=calculate(policy,scenario)
            publish(tag+'.json',out)
            cells.append({'id':tag,'status':out['status'],**({'reason':out['reason']} if out['status']=='unavailable' else {})})
            if policy.startswith('B'):baseline[policy][scenario]=compact(out)
            else:own[scenario]=out
    for scenario,out in own.items():
        tag=recipe.lower()+'-'+scenario+'-placebo'
        if out['status']=='complete':result=calculate(recipe,scenario,lagged=out['decisions'])
        else:
            publish(tag+'-attempt.json',{'attempted':False,'reason':'parent candidate unavailable'})
            result=known_unavailable('parent candidate unavailable; no substitute placebo')
        publish(tag+'.json',result);diagnostics[scenario]=compact(result)
    comparisons={}
    for scenario,out in own.items():
        contrasts={}
        for name in ('B'+str(i) for i in range(10)):
            other=baseline[name][scenario]
            contrasts[name]=({'status':'complete','difference_usd':str(D(out['net_cash_profit_usd'])-D(other['net_cash_profit_usd'])),
                'positive_difference_conditional':D(out['net_cash_profit_usd'])-D(other['net_cash_profit_usd'])>0,
                'incremental_floor_pass_conditional':D(out['net_cash_profit_usd'])-D(other['net_cash_profit_usd'])>=D('200'),
                'benchmark_conditional_numeric_risk_pass':other['conditional_numeric_risk_pass'],'actual_benchmark_feasibility':'unavailable'}
                if out['status']==other['status']=='complete' else {'status':'unavailable','reason':'candidate or benchmark book unavailable'})
        comparisons[scenario]={'candidate':compact(out),'benchmark_differences':contrasts,'placebo':diagnostics[scenario],
                               'positive_cash_profit_conditional':D(out['net_cash_profit_usd'])>0 if out['status']=='complete' else None,
                               'full_promotion':'unavailable: actual B1 and implementation/confirmation evidence missing'}
    summary={'recipe':recipe,'capital_usd':'10000','cohort_start':'2025-09-01T00:00:00Z','cohort_end':'2026-09-01T00:00:00Z','scope':'Conditional development; no validated or selected strategy','cells':cells,'comparisons':comparisons,'measurement_defect':defect,'promotion_admitted':False,'confirmation_admitted':False,'source_acquisitions':0}
    if recipe=='H2':publish('benchmarks.json',baseline)
    publish('summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True);p.add_argument('--recipe',choices=RECIPES,required=True);a=p.parse_args()
    experiment='allocation-conditional-'+a.recipe.lower()+'-20260915'
    registration='research/broader-allocation-2026-09-15/gates-conditional-'+a.recipe.lower()+'.json'
    with ResearchRun.start(root=HERE.parents[1],registration=registration,experiment=experiment,source=a.source) as run:
        raw=run.read_input('spec')
        if hashlib.sha256(raw).hexdigest()!=SPEC_HASH:raise ValueError('wrong frozen scenario spec')
        run.read_input('ancestry');run.read_input('cash_terms')
        panel=json.loads(run.read_input('panel'))
        if panel.get('status')!='complete':raise ValueError('source panel was not qualified')
        benchmarks=json.loads(run.read_input('benchmarks')) if a.recipe!='H2' else None
        used=0
        def publish(name,value):
            nonlocal used
            used+=len((json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
            if used>32*1024*1024:raise ValueError('output resource bound exceeded')
            run.write_json(name,value)
        result=execute(panel,a.recipe,publish,benchmarks,time.monotonic()+480)
        run.finish(result['cells'])

if __name__=='__main__':main()

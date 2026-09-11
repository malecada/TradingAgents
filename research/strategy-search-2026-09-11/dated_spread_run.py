"""One registered offline eight-case dated/perpetual book, no parameter search."""
import argparse
import json
from pathlib import Path
from dated_spread_book import book
from dated_spread_sources import readmit
from dated_spread_statistics import exposure

EXPERIMENT='dated-spread-book-20260911'
REGISTRATION='research/strategy-search-2026-09-11/gates-dated-spread.json'
MAX_OUTPUT_BYTES=8*1024**2
INPUTS=('carry_capture','carry_admission','archive_capture','archive_admission','mark_capture','mark_admission','btc_dated_mark_receipt','eth_dated_mark_receipt')
CASES=[(a,c,s) for a in ('BTC','ETH') for c in (1000,10000) for s in ('base','stress')]


def case_id(asset,capital,scenario):return f'{asset.lower()}-{capital}-{scenario}'
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def unavailable(reason):
    return {'status':'unavailable','reason':reason,
        'scalar_diagnostics':{name:{'status':'unavailable','reason':reason} for name in ('zero_funding','frictionless')},
        'stress_states':[{'id':f'{m:g}x-{b}bp','status':'unavailable','reason':reason} for m in (.5,1.,2.) for b in (0,10,50)]}


def evaluate(inputs):
    data,audit=readmit(inputs);books={};cells=[]
    for asset,capital,scenario in CASES:
        key=case_id(asset,capital,scenario)
        try:
            if asset in audit['errors']:result=unavailable(audit['errors'][asset])
            else:
                d=data[asset]
                result=book(d['dated'],d['perp'],d['dated_mark'],d['mark'],d['funding'],d['spot'],asset=asset,capital=capital,cost_scenario=scenario)
                if result['status']=='unavailable':result={**result,**unavailable(result['reason'])}
        except MemoryError:raise
        except Exception as exc:result=unavailable(type(exc).__name__+': '+str(exc))
        books[key]=result
        cells.append({'id':key,'status':'complete' if result['status']=='conditional' else 'unavailable',
            **({'reason':result['reason']} if result['status']=='unavailable' else {})})
    summaries=[]
    for asset,capital,scenario in CASES:
        key=case_id(asset,capital,scenario);result=books[key]
        if result['status']=='conditional' and all(a in data['benchmarks'] for a in ('BTC','ETH')):
            beta=exposure([r['nav'] for r in result['daily_trace']],capital,data['benchmarks']['BTC'],data['benchmarks']['ETH'])
        else:beta={'status':'unavailable','reason':'cash book or joint benchmark input unavailable'}
        pair=[books[case_id(asset,capital,s)] for s in ('base','stress')]
        observed=[r['metrics']['cash_profit']>0 and r['metrics']['annualized_simple_return_365']>=.03 for r in pair if r['status']=='conditional']
        relevance=False if False in observed else (True if len(observed)==2 else None)
        beta_pass=all(abs(beta[a+'_beta'])<=.1 and beta[a+'_interval'][0]>=-.2 and beta[a+'_interval'][1]<=.2 for a in ('btc','eth')) if beta['status']=='complete' else None
        metrics=result.get('metrics')
        item={'id':key,'asset':asset,'capital':capital,'cost_scenario':scenario,'status':result['status'],
            'cash_benchmarks':{str(r):capital*r*56/365 for r in (0,.03,.05)},
            'statistics':{'market_exposure':beta,'expected_profit_confidence':{'status':'unavailable','reason':'One spent episode per asset; not a repeated independent profit sample.'},
                          'power':{'status':'unavailable','reason':'No valid expected-profit test or independent episode sample.'}},
            'conditional_screens':{'positive_cash_and_3pct_annual_base_and_stress':relevance,'beta_point_and_interval':beta_pass,
                'drawdown_at_most_10pct':metrics['max_drawdown']<=.1 if metrics else None,
                'modeled_net_base_at_most_1pct_nav':metrics['modeled_net_base_fraction_nav']<=.01 if metrics and metrics['modeled_net_base_fraction_nav'] is not None else None,
                'no_separate_path_wallet_deficit':not metrics['path_wallet_deficit'] if metrics else None,
                'no_separate_stress_wallet_deficit':not metrics['stress_wallet_deficit'] if metrics else None},
            'actual_margin':{'status':'unavailable','reason':'Daily mark extrema and assumed1%maintenance do not establish tiers, intraday liquidation, ADL or transferable collateral.'},
            'execution':{'status':'unavailable','reason':'Historical/current lots, fees, personal access and simultaneous fills unverified.'},
            'graduation':False,'validated_strategy':False}
        if metrics:item.update(metrics=metrics,final_ledger=result['final_ledger'],scalar_diagnostics=result['scalar_diagnostics'])
        else:item['reason']=result['reason']
        summaries.append(item)
    summary={'cases':summaries,'primary_count':8,'scalar_diagnostic_count':16,'stress_state_count':72,'source_count':20,
        'complete_primary':sum(c['status']=='complete' for c in cells),'unavailable_primary':sum(c['status']=='unavailable' for c in cells),
        'complete_scalars':sum(x['status']=='complete' for b in books.values() for x in b['scalar_diagnostics'].values()),
        'unavailable_scalars':sum(x['status']=='unavailable' for b in books.values() for x in b['scalar_diagnostics'].values()),
        'complete_stresses':sum(x['status']=='complete' for b in books.values() for x in b['stress_states']),
        'unavailable_stresses':sum(x['status']=='unavailable' for b in books.values() for x in b['stress_states']),
        'graduation':False,'validated_strategies':0,'interpretation':'Eight correlated exploratory alternatives on one56-day spent episode; no pooled portfolio, independent discoveries or confirmation.'}
    return {'cases':books},summary,audit,cells


def main():
    from tradingagents.research_spread import ResearchRun
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        inputs={name:run.read_input(name) for name in INPUTS}
        books,summary,audit,cells=evaluate(inputs)
        outputs={'books.json':books,'summary.json':summary,'source-audit.json':audit}
        if sum(len(encoded(value)) for value in outputs.values())>MAX_OUTPUT_BYTES:raise ValueError('combined actual encoded8MiB output bound exceeded')
        for name,value in outputs.items():run.write_json(name,value)
        run.finish(cells)


if __name__=='__main__':main()

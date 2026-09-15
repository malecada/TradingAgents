"""Bind one already-frozen recipe registration; never reads financial values."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from tradingagents.research import runtime_hashes
P=Path('research/broader-allocation-2026-09-15')
RECIPES=('H2','H3','H4','H5');SCENARIOS=('primary','doubled','frictionless')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make(recipe):
    i=RECIPES.index(recipe)
    prior=P/('gates-input-readiness.json' if i==0 else 'gates-conditional-'+RECIPES[i-1].lower()+'.json')
    g=json.loads(prior.read_text());dataset='allocation-usdc-daily-proxy'
    if dataset not in g['datasets']:
        g['datasets'][dataset]={'identity':'binance-btcusdc-ethusdc-kraken-usdcusd-daily-proxy-20250213-20260915','history_reference':'readiness-charter.md and allocation-input-readiness-20260915; all raw received fields and normalized panel exposed. Prior178core/44DeFi ancestors and spent historical windows remain; no fresh confirmation.','exposures':[{'start':'2025-02-13T00:00:00Z','end':'2026-09-16T00:00:00Z','state':'exposed'}]}
    inputs={'spec':P/'conditional-spec.json','ancestry':P/'ancestry-crosswalk.json','cash_terms':Path('research_runs/allocation-cash-terms-20260915/outputs/cash-terms.json'),'panel':Path('research_runs/allocation-input-readiness-20260915/outputs/panel.json')}
    if i:inputs['benchmarks']=Path('research_runs/allocation-conditional-h2-20260915/outputs/benchmarks.json')
    policies=(recipe,*('B'+str(n) for n in range(10))) if i==0 else (recipe,)
    cells=[policy.lower()+'-'+scenario for policy in policies for scenario in SCENARIOS]
    outputs=[name+suffix for name in cells for suffix in ('-attempt.json','.json')]
    outputs += [recipe.lower()+'-'+scenario+'-placebo'+suffix for scenario in SCENARIOS for suffix in ('-attempt.json','.json')]
    outputs += ['summary.json']+(['benchmarks.json'] if i==0 else [])
    source=[P/n for n in ('conditional_book.py','conditional_run.py','conditional_launcher.py','register_conditional.py','spot_book.py')]+[Path('research/strategy-search-2026-09-11/resource_guard_v2.py'),Path('uv.lock')]
    e={'family':'allocation-decision','parent':'allocation-input-readiness-20260915' if i==0 else 'allocation-conditional-'+RECIPES[i-1].lower()+'-20260915','question':'What are the fixed '+recipe+' conditional full-capital cash, benchmark, stress and diagnostic outcomes without a real-account promotion claim?','charter':{'path':str(P/'conditional-charter.md'),'sha256':sha(P/'conditional-charter.md')},'stage':'development','reuse':'exploratory','selection':None,'source_files':{str(p):sha(p) for p in source},'runtime_hashes':runtime_hashes(),'windows':[{'dataset':dataset,'start':'2025-02-13T00:00:00Z','end':'2026-09-02T00:00:00Z','availability':'existing'}],'inputs':{k:{'path':str(p),'sha256':sha(p),'dataset':dataset} for k,p in inputs.items()},'cells':cells,'outputs':outputs}
    if i:
        frozen=g['experiments']['allocation-conditional-h2-20260915']
        for key in ('charter','source_files','runtime_hashes','windows'):
            if e[key]!=frozen[key]:raise ValueError('frozen financial contract changed: '+key)
        if e['inputs']['spec']!=frozen['inputs']['spec']:raise ValueError('frozen financial specification changed')
        from tradingagents.research.verify import verify_run
        verify_run(Path('research_runs/allocation-conditional-h2-20260915'))
    g['experiments']['allocation-conditional-'+recipe.lower()+'-20260915']=e
    path=P/('gates-conditional-'+recipe.lower()+'.json')
    with path.open('x') as f:json.dump(g,f,indent=2);f.write('\n')
    return str(path)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--recipe',choices=RECIPES,required=True);a=p.parse_args();print(make(a.recipe))

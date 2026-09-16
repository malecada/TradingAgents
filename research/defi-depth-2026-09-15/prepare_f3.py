"""Terminal-only F3 registration preparation; no financial arithmetic or requests."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research import runtime_hashes
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE='research/defi-depth-2026-09-15/'
spec=importlib.util.spec_from_file_location('f3_registration_runner',HERE/'f3_source.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


def ref(path):return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def actions():
    base=next(c for c in json.loads((HERE/'q1-spec.json').read_bytes())['chains'] if c['name']=='base')
    indexed={a['key']:{'method':'eth_call',**a} for a in base['actions']}
    indexed['lp-max-liquidity']={'key':'lp-max-liquidity','method':'eth_call','to':base['pool'],
        'data':'0x70cf754a','signature':'maxLiquidityPerTick()','types':['uint128'],'expected':[M.S.LP.MAX_TICK_LIQUIDITY]}
    for key,address in [('lp-code',base['pool']),('weth-code',base['weth']),('usdc-code',base['usdc'])]:
        indexed[key]={'key':key,'method':'eth_getCode','to':address}
    return [indexed[k] for k in M.S.DAILY['F3']],[indexed[k] for k in M.S.BOUNDARY_KEYS['F3']]


def prepare():
    daily,boundary=actions()
    packet,context,owners,prior,old=M.C.prepare(ROOT,daily,boundary)
    count=packet['f1_audit']['counts']
    design={**old,'experiment':M.EXPERIMENT,'recipe':'F3','daily_actions':daily,'boundary_actions':boundary,
        'ownership':owners,'prior_request_keys':prior,'price_field_history':M.S.O.price_fields(prior),
        'inherited_phase_claims':8,'inherited_financial_claims':2,
        'prior_phase_actual_rpc':old['prior_phase_actual_rpc']+count['actual_physical_requests'],
        'prior_known_raw_bytes':old['prior_known_raw_bytes']+count['retained_raw_bytes'],
        'economic_policy':'50 percent initial investable USDC budget; fixed full usable range; primary P/D/risk in charter'}
    inv=M.S.request_inventory(design)
    for k in ('max_physical_requests','worst_case_raw_bytes'):design[k]=inv[k]
    design['remaining_rpc_after_full_reservation']=25000-design['prior_phase_actual_rpc']-design['max_physical_requests']
    if design['remaining_rpc_after_full_reservation']<0:raise ValueError('phase RPC envelope exceeded')
    if design['prior_known_raw_bytes']+design['q2_uncertain_body_reservation']+design['prior_existing_metadata_read_charge']+design['worst_case_raw_bytes']>design['phase_raw_cap']:
        raise ValueError('phase raw-byte envelope exceeded')
    M.C.verify_packet(packet,design,(ROOT/M.C.PREFIX/'claim.json').read_bytes(),(ROOT/M.C.PREFIX/'complete.json').read_bytes())
    M.S.validate_design(design,context)
    generated={BASE+'f3-source-context.json':(json.dumps(packet,indent=2)+'\n').encode(),
               BASE+'f3-design.json':(json.dumps(design,indent=2)+'\n').encode()}
    def registered_ref(path):
        return {'path':path,'sha256':hashlib.sha256(generated[path]).hexdigest()} if path in generated else ref(path)
    paths={'design':BASE+'f3-design.json','source_context':BASE+'f3-source-context.json','phase':BASE+'phase-grant.json',
        'benchmarks':'research_runs/allocation-conditional-h2-20260915/outputs/benchmarks.json',
        'benchmark_claim':'research_runs/allocation-conditional-h2-20260915/claim.json',
        'benchmark_terminal':'research_runs/allocation-conditional-h2-20260915/complete.json',
        'q1_spec':BASE+'q1-spec.json','f1_design':BASE+'f1-design.json','f1_closure_audit':BASE+'f1-closure-audit.json',
        'core_ancestry':'research/broader-allocation-2026-09-15/ancestry-crosswalk.json',
        'defi_ancestry':'research/broader-allocation-2026-09-15/defi-ancestry-crosswalk.json',
        'closure_text':'research/broader-allocation-2026-09-15/RESULTS.md'}
    for label,eid,terminal in [('dex','allocation-dex-source-20260915','complete'),('q1','defi-depth-q1-20260915','complete'),
        ('q2','defi-depth-q2-20260915','failed'),('r1','defi-depth-r1-20260915','failed'),('q3','defi-depth-q3-20260915','failed'),
        ('f2','defi-depth-f2-20260915','complete'),('f1','defi-depth-f1-20260915','complete')]:
        paths[label+'_claim']='research_runs/'+eid+'/claim.json';paths[label+'_terminal']='research_runs/'+eid+'/'+terminal+'.json'
    for name in ('f3-charter-review','lending-book-review','financial-source-policy-review','protocol-financial-source-review',
                 'protocol-financial-results-review','protocol-closure-audit-review','f1-closure-review','f3-context-review'):
        paths[name+'_text']=BASE+'reviews/'+name+'.md'
    previous=json.loads((HERE/'gates-f1.json').read_bytes())
    sources=dict(previous['experiments']['defi-depth-f1-20260915']['source_files'])
    for name in ('f3_source.py','f3_context.py','prepare_f3.py','protocol_closure_audit.py','f3-design.json'):
        sources[BASE+name]=registered_ref(BASE+name)['sha256']
    for path,expected in sources.items():
        if registered_ref(path)['sha256']!=expected:raise ValueError('inherited source differs; exact successor review required')
    family='full-range-lp-cash-financial';dataset='lp-exposed-financial';end=datetime.now(timezone.utc).isoformat()
    cells,outputs=M.manifests(design)
    gate={'schema_version':1,'program_id':'defi-depth-2026-09-15',
        'families':{family:{'mechanism_id':'base-native-usdc-weth-full-range-fixed-cash-v1','prior_attempts':7,'attempt_budget':8,
            'history_reference':BASE+'f3-charter.md; seven direct imported claims; original188/189 and44relatedDeFi overlap'}},
        'datasets':{dataset:{'identity':'base-lp-exposed-20230902-20260901-and-prior-source-history',
            'history_reference':BASE+'f3-charter.md; all prior source and financial exposure retained',
            'exposures':[{'start':'2023-09-02T00:00:00Z','end':end,'state':'exposed'}]}},
        'experiments':{M.EXPERIMENT:{'family':family,'parent':None,
            'question':'Does the fixed50percent full-usable-range LP/cash recipe meet absolute and incremental annual net targets after funded costs and inventory changes within fixed risk limits?',
            'charter':ref(BASE+'f3-charter.md'),'stage':'development','reuse':'exploratory','selection':None,
            'source_files':sources,'runtime_hashes':runtime_hashes(),
            'inputs':{name:{**registered_ref(path),'dataset':dataset} for name,path in paths.items()},
            'windows':[{'dataset':dataset,'start':'2023-09-02T00:00:00Z','end':end,'availability':'existing'}],
            'cells':cells,'outputs':outputs}}}
    generated[BASE+'gates-f3.json']=(json.dumps(gate,indent=2)+'\n').encode()
    if any((ROOT/path).exists() for path in generated):raise FileExistsError('F3 preparation outputs already exist')
    for path,raw in generated.items():
        with (ROOT/path).open('xb') as f:f.write(raw)
    print(json.dumps({'cells':len(cells),'outputs':len(outputs),'inputs':len(paths),'source_files':len(sources),
        'physical_request_reservation':design['max_physical_requests'],'retained_byte_reservation':design['worst_case_raw_bytes'],
        'remaining_rpc_after_full_reservation':design['remaining_rpc_after_full_reservation']}))


if __name__=='__main__':prepare()

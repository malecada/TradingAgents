"""Terminal-only F1 registration builder; no network or financial arithmetic."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research import runtime_hashes
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE='research/defi-depth-2026-09-15/'

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

M=module('f1_registration_runner','f1_source.py')

def ref(path):return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
def write(name,value):
    with (HERE/name).open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n')


def prepare():
    # Guard and full terminal audit precede any output creation.
    q1=json.loads((HERE/'q1-spec.json').read_text());q2=json.loads((HERE/'q2-spec.json').read_text())
    days=[d for d in q2['days'] if '2025-09-01'<=d['date']<='2026-09-01']
    if len(days)!=366:raise ValueError('fixed calendar missing')
    packet,owners=M.C.prepare(ROOT,days)
    if packet['inherited_endpoint_stop']:raise ValueError('inherited provider stop cannot be bypassed')
    base=next(c for c in q1['chains'] if c['name']=='base')
    actions={a['key']:{'method':'eth_call',**a} for a in base['actions']}
    daily=[actions[k] for k in M.S.DAILY['F1']]
    boundary=[actions[k] for k in ('usdc-decimals','aave-pool-identity','aave-underlying')]
    for key,to in [('usdc-code',base['usdc']),('aave-pool-code',base['aave_pool']),('atoken-code',base['atoken'])]:
        boundary.append({'key':key,'to':to,'method':'eth_getCode'})
    for day in days:
        d=day['date'];owners[d]['fields']={a['key']:'new' for a in daily+(boundary if d in M.S.BOUNDARIES else [])}
    counts=packet['f2_audit']['counts'];prior_rpc=1841+counts['actual_source_requests']
    known_raw=754936+counts['retained_raw_bytes']
    order=[days[i]['date'] for i in (0,1,365)]+[d['date'] for d in days[2:-1]]
    policy=M.S.P
    design={'experiment':M.EXPERIMENT,'recipe':'F1','days':days,'ownership':owners,'daily_actions':daily,'boundary_actions':boundary,
      'acquisition_order':order,'url':'https://mainnet.base.org','chain_id':8453,'attempt_delays_seconds':[0,15,60],
      'minimum_response_pause_seconds':5,'inherited_endpoint_stop':None,'prior_request_keys':packet['prior_request_keys'],
      'price_field_history':M.C.O.price_fields(packet['prior_request_keys']),
      'denials_stop_endpoint':sorted(policy.DENIALS),
      'recognized_rpc_throttling':{'codes':sorted(policy.THROTTLE_CODES),'message_fragments_casefold':sorted(policy.THROTTLE_FRAGMENTS)},
      'per_request_wall_seconds':30,'provider_retry_after_max_seconds':300,'elapsed_time_kill':False,
      'response_retained_prefix_caps':policy.CAPS,'inherited_phase_claims':7,'phase_claim_cap':11,
      'inherited_financial_claims':1,'phase_financial_cap':4,'repair_claims_spent':1,'repair_cap':1,
      'prior_phase_actual_rpc':prior_rpc,'phase_rpc_cap':25000,'prior_known_raw_bytes':known_raw,
      'q2_uncertain_body_reservation':262144,'prior_existing_metadata_read_charge':1140942,
      'phase_raw_cap':2147483648,'documentary_operations_used':60,'documentary_operations_cap':60,
      'economic_policy':'70 percent initial investable USDC; fixed primary net P/D/risk rules in charter',
      'capital_usd':10000,'annual_profit_target_usd':1000,'incremental_hurdle_usd':200,
      'source_model':'actual canonical clock within one second before date target; no nearest/bracket or counterfactual execution claim'}
    inventory=M.S.request_inventory(design)
    for key in ('max_physical_requests','worst_case_raw_bytes'):design[key]=inventory[key]
    if prior_rpc+design['max_physical_requests']>25000:raise ValueError('phase physical request cap exceeded')
    if known_raw+262144+1140942+design['worst_case_raw_bytes']>2147483648:raise ValueError('phase retained raw cap exceeded')
    design['remaining_rpc_after_full_reservation']=25000-prior_rpc-design['max_physical_requests']
    context=M.C.verify_packet(packet,design);M.S.validate_design(design,context)
    # No financial function is called by this builder.
    generated={BASE+'f1-source-context.json':(json.dumps(packet,indent=2)+'\n').encode(),
               BASE+'f1-design.json':(json.dumps(design,indent=2)+'\n').encode()}
    def registered_ref(path):
        return {'path':path,'sha256':hashlib.sha256(generated[path]).hexdigest()} if path in generated else ref(path)
    dataset='lending-exposed-financial';family='native-usdc-lending-cash-financial'
    exposure_end=datetime.now(timezone.utc).isoformat()
    gate={'schema_version':1,'program_id':'defi-depth-2026-09-15',
      'families':{family:{'mechanism_id':'base-native-usdc-lending-fixed-cash-index-model-v1','prior_attempts':6,'attempt_budget':7,
        'history_reference':BASE+'f1-charter.md; six direct imported source claims; original188/189 and44relatedDeFi records overlap, no reset'}},
      'datasets':{dataset:{'identity':'base-lending-exposed-20230902-20260901-and-prior-source-history',
        'history_reference':BASE+'f1-charter.md; all direct source/financial exposure and broader search retained',
        'exposures':[{'start':'2023-09-02T00:00:00Z','end':exposure_end,'state':'exposed'}]}},'experiments':{}}
    paths={'design':BASE+'f1-design.json','source_context':BASE+'f1-source-context.json','phase':BASE+'phase-grant.json',
      'benchmarks':'research_runs/allocation-conditional-h2-20260915/outputs/benchmarks.json',
      'benchmark_claim':'research_runs/allocation-conditional-h2-20260915/claim.json',
      'benchmark_terminal':'research_runs/allocation-conditional-h2-20260915/complete.json',
      'q1_spec':BASE+'q1-spec.json','q2_spec':BASE+'q2-spec.json','f2_design':BASE+'f2-design.json',
      'prior_attempt_history':BASE+'f2-attempt-history.json',
      'f2_closure_audit':BASE+'f2-closure-audit.json',
      'f2_closure_review':BASE+'reviews/f2-closure-review.md',
      'core_ancestry':'research/broader-allocation-2026-09-15/ancestry-crosswalk.json',
      'defi_ancestry':'research/broader-allocation-2026-09-15/defi-ancestry-crosswalk.json',
      'closure_text':'research/broader-allocation-2026-09-15/RESULTS.md'}
    for label,eid,terminal in [('dex','allocation-dex-source-20260915','complete'),('q1','defi-depth-q1-20260915','complete'),
       ('q2','defi-depth-q2-20260915','failed'),('r1','defi-depth-r1-20260915','failed'),('q3','defi-depth-q3-20260915','failed'),
       ('f2','defi-depth-f2-20260915','complete')]:
        paths[label+'_claim']='research_runs/'+eid+'/claim.json';paths[label+'_terminal']='research_runs/'+eid+'/'+terminal+'.json'
    for name in ('f1-design-review','f1-source-preparation-review','lending-book-review','financial-source-policy-review',
                 'protocol-financial-source-review','protocol-financial-results-review','f1-context-review'):
        paths[name+'_text']=BASE+'reviews/'+name+'.md'
    for i,evidence in enumerate(packet['evidence_refs']):
        if ref(evidence['path'])!=evidence:raise ValueError('ownership evidence changed during preparation')
        paths[f'ownership_evidence_{i:04d}']=evidence['path']
    previous=json.loads((HERE/'gates-f2.json').read_text())
    sources=dict(previous['experiments']['defi-depth-f2-20260915']['source_files'])
    for name in ('f1_source.py','prepare_f1.py','f1_context.py','f2_closure_audit.py','source_ownership.py',
                 'financial_transport.py','financial_source_policy.py','protocol_financial_source.py','protocol_financial_results.py',
                 'lending_book.py','lending_math.py','lp_book.py','v3_ticks.py','protocol_stress.py','literal_receipts.py','wallet_controls.py','f1-design.json'):
        sources[BASE+name]=registered_ref(BASE+name)['sha256']
    cells,outputs=M.manifests(design)
    gate['experiments'][M.EXPERIMENT]={'family':family,'parent':None,
      'question':'Does the fixed70 percent native-USDC lending/cash recipe meet the absolute and incremental annual net targets within the fixed risk limits; if not, is the failure economic, unavailable or under-evidenced?',
      'charter':ref(BASE+'f1-charter.md'),'stage':'development','reuse':'exploratory','selection':None,
      'source_files':sources,'runtime_hashes':runtime_hashes(),
      'inputs':{name:{**registered_ref(path),'dataset':dataset} for name,path in paths.items()},
      'windows':[{'dataset':dataset,'start':'2023-09-02T00:00:00Z','end':exposure_end,'availability':'existing'}],
      'cells':cells,'outputs':outputs}
    # All input/source references resolve before creating any output. Never replace
    # an earlier registration, including a partially published preparation.
    targets=[HERE/'f1-source-context.json',HERE/'f1-design.json',HERE/'gates-f1.json']
    if any(path.exists() for path in targets):raise FileExistsError('F1 preparation outputs already exist')
    for path,raw in generated.items():
        with (ROOT/path).open('xb') as handle:handle.write(raw)
    write('gates-f1.json',gate)
    print(json.dumps({'cells':len(cells),'outputs':len(outputs),'inputs':len(paths),'source_files':len(sources),
                      'physical_request_reservation':design['max_physical_requests'],'retained_byte_reservation':design['worst_case_raw_bytes'],
                      'remaining_rpc_after_full_reservation':design['remaining_rpc_after_full_reservation']}))


if __name__=='__main__':prepare()

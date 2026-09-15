"""Prepare metadata/configuration only. Does not acquire or calculate outcomes."""
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research import runtime_hashes
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE='research/defi-depth-2026-09-15/'
def ref(path):return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
def write(name,value):(HERE/name).write_text(json.dumps(value,indent=2)+'\n')
s=importlib.util.spec_from_file_location('f2_registration_code',HERE/'f2_source.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
q3=json.loads((HERE/'q3-design-v2.json').read_text());calendar=json.loads((HERE/'q2-spec.json').read_text())
history=[];headers=set();all_keys=set()
for name in ('q1','q2','r1','q3'):
 for path in sorted((ROOT/('research_runs/defi-depth-'+name+'-20260915/outputs')).glob('*attempt.json')):
  obj=json.loads(path.read_text())
  if not obj.get('attempted') or obj['url']!='https://mainnet.base.org':continue
  requests=obj['request'] if isinstance(obj['request'],list) else [obj['request']]
  keys=[]
  for request in requests:
   key=m.p.request_key(request['method'],request['params']);keys.append(key);all_keys.add(key)
   if name in ('r1','q3') and request['method']=='eth_getBlockByNumber':headers.add(key)
  history.append({**ref(str(path.relative_to(ROOT))),'request_keys':keys})
assert len(headers)==182
write('f2-attempt-history.json',{'scope':'Prior intent metadata only, including unknown Q2 response; no economic values','base_header_keys':sorted(headers),'all_base_request_keys':sorted(all_keys),'attempt_files':history})
days=[d for d in calendar['days'] if '2025-09-01'<=d['date']<='2026-09-01'];assert len(days)==366
requests=3*366-4
for day in days:
 if day['date'] in m.RETAINED:continue
 for off in (0,1):assert m.p.request_key('eth_getBlockByNumber',[hex(day['candidate_block']+off),False]) not in all_keys
order=['2025-09-01','2025-09-02','2026-09-01']+[d['date'] for d in days if d['date'] not in ('2025-09-01','2025-09-02','2026-09-01')]
design={k:q3[k] for k in ('pacing','recognized_rpc_throttling','max_response_bytes','denials_stop_endpoint')}
design.update(prior_base_request_keys=sorted(all_keys),experiment=m.EXPERIMENT,recipe='One25%-of-initial-investable-USDC wrapped staking oracle/cash screen',days=days,acquisition_order=order,
 chains={'base':{'url':'https://mainnet.base.org','chain_id':8453}},max_rpc_subcalls=requests,max_http_requests=requests,worst_case_raw_bytes=requests*262144,
 prior_phase_rpc=1841,phase_rpc_cap=25000,post_reservation_rpc_remaining=25000-1841-requests,documentary_used=55,
 raw_known=754936,unknown_q2_reservation=262144,prior_existing_metadata_reads=1140942,phase_raw_cap=2147483648,
 prior_claims=6,phase_claim_cap=11,financial_slot='F2',financial_prior_used=0,shared_repair_used=1,
 primary_cohort='2026',other_cohorts=['2024','2025'],capital_usd=10000,annual_target_usd=1000,incremental_target_usd=200,
 controls=list(m.book.POLICIES[1:])+['B'+str(i) for i in range(10)],scenarios=list(m.book.SCENARIOS),
 request_policy='Boundary/entry first then chronological; one attempt per new key, one owner per header. First missing indispensable source stops later acquisition; all cells retained.',
 source_model='AaveOracle.getAssetsPrices(address[]), scalar WST retained at two boundaries; USD unit1e8 qualified at both boundaries. Oracle source/code/staleness/market basis not proven continuous.',
 source_url='https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/misc/AaveOracle.sol')
write('f2-design.json',design)
gate=json.loads((HERE/'gates-q3.json').read_text());family='unhedged-wrapper-cash-financial';dataset='wrapper-cash-exposed-financial'
gate['families'][family]={'mechanism_id':'base-wsteth-unhedged-fixed-cash-oracle-price-increment-v1','prior_attempts':7,'attempt_budget':8,'history_reference':BASE+'f2-charter.md; seven direct imported predecessor claims,188original/44related records overlap; no source/repair budget reset'}
gate['datasets'][dataset]={'identity':'base-wrapper-eth-usdc-exposed-20230902-20260901-plus-prior-source-history','history_reference':BASE+'f2-charter.md; Q1/Q2/R1/Q3 and original allocation/WBETH spent exposure inherited','exposures':[{'start':'2023-09-02T00:00:00Z','end':'2026-09-16T00:00:00Z','state':'exposed'}]}
paths={'design':BASE+'f2-design.json','attempt_history':BASE+'f2-attempt-history.json','q3_design':BASE+'q3-design-v2.json','phase':BASE+'phase-grant.json',
 'core_ancestry':'research/broader-allocation-2026-09-15/ancestry-crosswalk.json','defi_ancestry':'research/broader-allocation-2026-09-15/defi-ancestry-crosswalk.json',
 'benchmarks':'research_runs/allocation-conditional-h2-20260915/outputs/benchmarks.json',
 'original_panel':'research_runs/allocation-input-readiness-20260915/outputs/panel.json',
 'q3_review_text':BASE+'reviews/q3-postexecution-review.md','continuation_review_text':BASE+'reviews/financial-continuation-review.md',
 'closure_text':'research/broader-allocation-2026-09-15/RESULTS.md'}
for label,eid,terminal in [('dex','allocation-dex-source-20260915','complete'),('q1','defi-depth-q1-20260915','complete'),('q2','defi-depth-q2-20260915','failed'),('r1','defi-depth-r1-20260915','failed'),('q3','defi-depth-q3-20260915','failed'),('wbeth_inputs','wbeth-inputs-20260911','complete'),('wbeth_book','wbeth-book-20260911','complete')]:
 for suffix,file in [('claim','claim'),('terminal',terminal)]:paths[label+'_'+suffix]='research_runs/'+eid+'/'+file+'.json'
for date in m.RETAINED:
 for side in ('left','right'):paths[date+'-header-'+side]='research_runs/defi-depth-q3-20260915/outputs/base-'+date+'-header-'+side+'-receipt.json'
 paths[date+'-source']='research_runs/defi-depth-q3-20260915/outputs/base-'+date+'-results.json'
 paths[date+'-wst-receipt']='research_runs/defi-depth-q3-20260915/outputs/base-'+date+'-oracle-wsteth-price-receipt.json'
sources={**gate['experiments']['defi-depth-q3-20260915']['source_files']}
for path in [BASE+'f2_source.py',BASE+'wrapper_book.py',BASE+'protocol_math.py','research/broader-allocation-2026-09-15/spot_book.py',BASE+'f2-design.json']:
 sources[path]=ref(path)['sha256']
cells,outputs=m.manifests(design)
gate['experiments'][m.EXPERIMENT]={'family':family,'parent':None,'question':'Does one fixed25% wrapper/cash allocation deliver at least$1000 annual conditional net profit and$200 incremental value against eligible fixed controls within numerical risk limits?',
 'charter':ref(BASE+'f2-charter.md'),'stage':'development','reuse':'exploratory','selection':None,'source_files':sources,'runtime_hashes':runtime_hashes(),
 'inputs':{name:{**ref(path),'dataset':dataset} for name,path in paths.items()},
 'windows':[{'dataset':dataset,'start':'2023-09-02T00:00:00Z','end':'2026-09-16T00:00:00Z','availability':'existing'}],
 'cells':cells,'outputs':outputs}
write('gates-f2.json',gate)
print({'cells':len(cells),'outputs':len(outputs),'inputs':len(paths),'requests':requests,'raw_reservation':requests*262144})

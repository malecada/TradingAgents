"""Build source registration from retained metadata; never acquire source."""
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research import runtime_hashes
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];base='research/defi-depth-2026-09-15/'
loader=importlib.util.spec_from_file_location('q3_registration',HERE/'q3_source.py');q=importlib.util.module_from_spec(loader);loader.loader.exec_module(q)
def ref(path):return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
gate=json.loads((HERE/'gates-q2.json').read_text())
design=json.loads((HERE/'q3-design-v2.json').read_text());calendar=json.loads((HERE/'q2-spec.json').read_text())
family='staking-conversion-source';dataset='staking-wrapper-source-history'
gate['families'][family]={'mechanism_id':design['family_proposal']['mechanism_id'],'prior_attempts':6,'attempt_budget':7,'history_reference':base+'q3-charter.md; exact six claim/terminal inputs, original188/189 closure and44related records remain; no global double count or family reset'}
gate['datasets'][dataset]={'identity':'eth-native-staking-and-base-wsteth-oracle-fixed-calendar-20230902-20260901','history_reference':base+'q3-charter.md; retained Q1 and R1 exposed source plus old WBETH and full core/DeFi crosswalks; no fresh confirmation','exposures':[{'start':'2023-09-02T00:00:00Z','end':'2026-09-15T18:01:00Z','state':'exposed'}]}
paths={'design':base+'q3-design-v2.json','calendar':base+'q2-spec.json','phase':base+'phase-grant.json','q1_spec':base+'q1-spec.json',
'core_ancestry':'research/broader-allocation-2026-09-15/ancestry-crosswalk.json','defi_ancestry':'research/broader-allocation-2026-09-15/defi-ancestry-crosswalk.json',
'closure_text':'research/broader-allocation-2026-09-15/RESULTS.md','r1_review_text':base+'reviews/r1-provider-limit-review.md',
'q3_review_text':base+'reviews/q3-design-review.md','aave_base':base+'documents/aave-base.json',
'ethereum_header_receipt':'research_runs/defi-depth-q1-20260915/outputs/ethereum-finalized-header-receipt.json',
'ethereum_header_result':'research_runs/defi-depth-q1-20260915/outputs/ethereum-finalized-header-result.json'}
for name,experiment,terminal in [('dex','allocation-dex-source-20260915','complete'),('q1','defi-depth-q1-20260915','complete'),('q2','defi-depth-q2-20260915','failed'),('r1','defi-depth-r1-20260915','failed'),('wbeth_inputs','wbeth-inputs-20260911','complete'),('wbeth_book','wbeth-book-20260911','complete')]:
 for key,file in [('claim','claim'),('terminal',terminal)]:paths[name+'_'+key]='research_runs/'+experiment+'/'+file+'.json'
for day in calendar['days']:
 if day['date']<='2023-11-28':paths['r1-header-'+day['date']]='research_runs/defi-depth-r1-20260915/outputs/'+day['date']+'-headers-receipt.json'
for i in range(3):paths['r1_boundary_'+str(i)]='research_runs/defi-depth-r1-20260915/outputs/2023-09-02-state-'+str(i)+'-receipt.json'
sources=[base+x for x in ['q3_source.py','q3_protocol.py','q1_source.py','r1_source_v2.py','q2_transport.py']]+['research/broader-allocation-2026-09-15/dex_source.py','research/broader-allocation-2026-09-15/dex_transport.py','uv.lock']
# Frozen helper imports include the historical repair runtime; it grants no Q3 authority.
sources += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'tradingagents/research_defi_repair').glob('*.py'))]
cells,outputs=q.manifests(design,calendar['days'])
gate['experiments'][q.EXPERIMENT]={'family':family,'parent':None,'question':design['source_question'],'charter':ref(base+'q3-charter.md'),'stage':'discovery','reuse':'exploratory','selection':None,
'source_files':{path:ref(path)['sha256'] for path in sources},'runtime_hashes':runtime_hashes(),
'inputs':{name:{**ref(path),'dataset':dataset} for name,path in paths.items()},
'windows':[{'dataset':dataset,'start':'2023-09-02T00:00:00Z','end':'2026-09-15T18:01:00Z','availability':'existing'}],
'cells':cells,'outputs':outputs}
(HERE/'gates-q3.json').write_text(json.dumps(gate,indent=2)+'\n')
print({'cells':len(cells),'outputs':len(outputs),'inputs':len(paths),'max_requests':design['max_rpc_subcalls']})

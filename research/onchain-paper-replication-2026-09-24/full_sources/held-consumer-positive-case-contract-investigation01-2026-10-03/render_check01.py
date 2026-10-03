from pathlib import Path
import ast,json,hashlib,copy
H=Path(__file__).resolve().parent;F=H.parent;S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source');P=S/'tradingagents/research/onchain_replication';OLD=F/'original-import-native-successor-preparation06-2026-10-03/capsule04/fixture_inputs/success'
def read(p):assert p.stat().st_size<=4*1024**2;return p.read_bytes()
def doc(p):return json.loads(read(p))
def write(n,x):(H/n).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def extract(path,names,ns):
 t=ast.parse(read(path));nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names or isinstance(n,ast.Assign) and any(isinstance(z,ast.Name) and z.id in names for z in n.targets)]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
job=doc(OLD/'execution_job.json');plan=doc(OLD/'producer_plan.json');base=copy.deepcopy(job);selection=job['payload']['representation_jobs']['original32'];graphs=selection['descriptor']['required_graphs'];assert sorted(selection['descriptor']['resource_fixture']['target_nodes'].values())==[2,3]
selection['held_score_consumer_input']='held_score_policy';plan['producers']['original32']['held_score_consumer_input']='held_score_policy';job['resources']['disk_paths']=[str(S)];job['resources']['storage_budget']['root']=str(S)
policy={'schema_version':1,'kind':'original-import-held-score-readback-v1','targets':{g:{'output':'held-target-%02d.json'%(i+1)} for i,g in enumerate(graphs)},'part_bytes':1048576,'max_read_bytes':768,'max_members':32767}
outputs=['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json']+[r['output'] for r in policy['targets'].values()]
ns={'Path':Path};extract(P/'resource_fixture.py',{'require','KEYS','selection'},ns);assert ns['selection'](base)[0]=='original32'
try:ns['selection'](job)
except ValueError as e:assert str(e)=='fixture selected fields differ';key_refusal=str(e)
else:raise AssertionError('old selection unexpectedly admitted held selector')
ns2={'Path':Path};extract(P/'held_score_consumer.py',{'require','KIND','_policy'},ns2);assert ns2['_policy'](policy,graphs,outputs)==policy
# Exact existing preflight output expression, executed with qualified metadata-only objects.
t=ast.parse(read(P/'resource_fixture.py'));fun=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='preflight');check=next(n for n in fun.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='exact resource-only outputs required' for a in n.value.args))
from types import SimpleNamespace
fake=SimpleNamespace(admission=SimpleNamespace(experiment={'outputs':outputs}));scope={'run':fake,'outputs':set(outputs[:4]),'require':ns['require']}
try:exec(compile(ast.Module(body=[check],type_ignores=[]),'actual-preflight-output-check','exec'),scope)
except ValueError as e:output_refusal=str(e)
else:raise AssertionError('old four-output condition accepted six')
case={'schema_version':1,'kind':'root-selected-imported-held-resource-v1','program_id':None,'experiment_id':None,'job_input':'execution_job','plan_input':'producer_plan','representation':'original32','producer':'original32','held_policy_input':'held_score_policy','readback_outputs':{g:r['output'] for g,r in policy['targets'].items()},'additional_inputs':None}
roles=['runtime','software_environment','native_environment','native_policy','original_import_index','original_evidence','matching','target_catalog','case_contract','registration','budget_extension','budget_review','charter']
write('JOB_TEMPLATE01.json',job);write('PLAN_TEMPLATE01.json',plan);write('HELD_POLICY01.json',policy);write('CASE_TEMPLATE01.json',case);write('ROLE_REQUIREMENTS01.json',{'roles':{k:None for k in roles},'known_runtime_body':'fixture_inputs/held/runtime-role01.json','root_authority':None,'outputs':outputs,'status':'refused-unregistered-source-route-needs-correction','denominators':{'positive_targets':2,'positive_motifs_each':32,'positive_cells':[64,96],'positive_score_bytes':[512,768],'full_refusal_variants':27,'full_refusal_classes':16,'preclaim_refusals':4,'maximum_refusal_claims':23,'maximum_refusal_owners':17,'maximum_refusal_journals':19},'original_samples':512,'resampling':False})
refs=[]
for path,names in [(P/'job.py',['_command','worker']),(P/'resource_fixture.py',['selection','preflight','execute']),(P/'resource_binding.py',['open_first']),(P/'matching_owner.py',['_guard','bind']),(P/'original_import_stage.py',['attach']),(P/'compact_mcm.py',['produce_imported','_produce_locked']),(P/'held_score_consumer.py',['_policy','_route','preflight','consume'])]:
 raw=read(path);t=ast.parse(raw);refs.append({'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'definitions':{n.name:n.lineno for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names}})
write('SOURCE_READBACK01.json',{'sources':refs,'refusals':[key_refusal,output_refusal],'positive_policy_schema_passed':True,'genuine_authority_executed':False,'additional_module_required':False,'existing_dispatch_source_correction_required':True});print('PASS legacy selection; held policy schema; actual source03 key and output refusals reproduced; no authority')

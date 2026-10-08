import ast,copy,hashlib,json,stat
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final20-2026-10-08';H=Path(__file__).resolve().parent;NAME='eth-paper-real-data-end-to-end-resource-20261008-20'
prior=json.loads((F/'real-data-pilot-retry20-entry-review01-2026-10-08/RELEASE_REVIEW01.json').read_bytes());ev=dict(prior['evidence']);checks=[]
oldbinding=json.loads((N/'BINDING01.json').read_bytes());ev.pop(oldbinding['transport']['path'])
def read(p):
 b=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
def check(n,v):
 assert v,n
 checks.append(n)
def need(v,msg):
 if not v:raise ValueError(msg)
review=load(H/'SOURCE_REVIEW01.json');check('reviewed_helper',review['decision']=='accepted-source-only')
oldpolicy=load(F/'real-data-pilot-capacity-selection03-2026-10-08/mcm_policy.json');newpolicy=load(F/'real-data-pilot-capacity-selection04-2026-10-08/mcm_policy.json');selection=load(F/'real-data-pilot-capacity-selection04-2026-10-08/SELECTION01.json')
expected=copy.deepcopy(oldpolicy)
for key in ('max_buffer_bytes','max_numeric_bytes'):expected['numeric'][key]+=3346688
check('selection_only_two_increases',newpolicy==expected and selection['after']==newpolicy['numeric'] and selection['before']==oldpolicy['numeric'])
check('selected_minima',all(newpolicy['numeric'][k]==review['required_selection'][k] for k in ('max_buffer_bytes','max_numeric_bytes','max_output_bytes')))
draft=load(N/'INPUT_DRAFT03.json');old=load(N/'INPUT_DRAFT02.json');expected=copy.deepcopy(old);expected['protocol']['references']['mcm_policy']=draft['protocol']['references']['mcm_policy'];check('draft_only_mcm_ref',expected==draft)
prepared=load(N/'PREPARATION_RESULT06.json');priorprepared=load(N/'PREPARATION_RESULT05.json');check('entire_prepared_inventory_identical',prepared['inventory']==priorprepared['inventory'])
check('prepared_documents_identical',prepared['builder03_result']['inputs']==priorprepared['builder03_result']['inputs'])
binding=load(N/'BINDING_DRAFT03.json');gate=load(N/'gate03.json');oldgate=load(N/'gate02.json');exp=gate['experiments'][NAME];oldexp=oldgate['experiments'][NAME]
check('gate_only_inputs_sources',{k for k in exp if exp[k]!=oldexp[k]}=={'inputs','source_files'})
expected=copy.deepcopy(oldgate);expected['experiments'][NAME]=exp;check('history_family_unchanged',expected==gate)
text=read(N/'preflight03.py').decode();oldtext=read(N/'preflight02.py').decode()
def const(text,name):return ast.literal_eval(next(n.value for n in ast.parse(text).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
helper=const(text,'INDEX_CAPACITY');oldhelper=const(oldtext,'INDEX_CAPACITY');body=read(R/helper['path']);check('reviewed_helper_hash',ev[helper['path']]==helper['sha256']==review['evidence'][helper['path']])
inverse=text.replace(repr(helper),repr(oldhelper)).replace("HERE/'gate03.json'","HERE/'gate02.json'").replace("HERE/'BINDING02.json'","HERE/'BINDING01.json'").replace("HERE/'RELEASE_REVIEW02.json'","HERE/'RELEASE_REVIEW01.json'")
check('preflight_literal_inverse',inverse==oldtext)
root=read(N/'root_io03.py').decode();check('rootio_literal_inverse',root.replace('from preflight03 import check','from preflight02 import check')==read(N/'root_io02.py').decode())
check('check_before_launch',root.index('args, preflight = check()')<root.index('result = launch_checked(args,preflight'))
refusal=load(N/'PRECLAIM_REFUSAL01.json');check('preclaim_only_refusal',refusal['status']=='READ_ONLY_ENTRY_REFUSAL_NO_RESERVATION' and refusal['actual_root_cli_exit']==1 and not refusal['claim_present'] and not refusal['launch_reservation_present'])
check('no_claim',not (R/'research_runs'/NAME/'claim.json').exists());check('no_reservation',not (N/'launch-attempt01.json').exists())
# Inspect exactly changed public materialization and its inverse; opaque body hash only.
bound=load(N/'TRANSPORT_BINDING06.json');refs=load(N/'INPUT_REFS06.json');check('private_fresh',binding['transport']['path']!=oldbinding['transport']['path'])
for role,v in refs.items():
 check('input_ref_join_'+role,all(exp['inputs'][role][k]==v[k] for k in ('path','sha256')))
 data=read(R/v['path']);check('input_hash_'+role,hashlib.sha256(data).hexdigest()==v['sha256'])
 if role!='archive_transport':check('public_bound_body_'+role,json.loads(data)==bound['inputs'][role])
for role,v in exp['inputs'].items():
 if role not in refs:
  expected=draft['protocol']['references'].get(role)
  if expected is not None:check('remaining_selected_join_'+role,all(v[k]==expected[k] for k in ('path','sha256')))
  else:check('inherited_input_'+role,v==oldexp['inputs'][role])
check('mcm_runtime_policy',exp['inputs']['mcm_policy']['sha256']==selection['policy']['sha256'])
fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');env={'copy':copy,'Path':Path,'need':need,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<binder inverse>','exec'),env)
archive=load(R/draft['protocol']['references']['archive_policy']['path'])
env['inverse_binding'](prepared,archive,bound,binding['transport'],lambda x:(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode(),lambda x:hashlib.sha256(x).hexdigest());checks.append('actual_inverse_binding06')
for p,h in exp['source_files'].items():
 if ev.get(p)!=h:check('new_source_pin_'+p,hashlib.sha256(read(R/p)).hexdigest()==h)
for v in exp['inputs'].values():
 if ev.get(v['path'])!=v['sha256']:check('new_input_pin_'+v['path'],hashlib.sha256(read(R/v['path'])).hexdigest()==v['sha256'])
for role,v in binding.items():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():check('binding_join_'+role,hashlib.sha256(read(R/v['path'])).hexdigest()==v['sha256'])
check('sole_private_evidence',[p for p in ev if p.startswith('research_artifacts/real_pilot_runtime/pilot-transport-')]==[binding['transport']['path']])
result={'schema_version':1,'decision':'accepted','identity':NAME,'evidence':ev,'checks':checks,'accepted_gate':binding['gate'],'scope':'Narrow additive gate03/draft03/preparation06/binder06 seam review after preclaim-only refusal. Exact two memory fields increase3346688 bytes; inventory/resources/science/diagnostic/history/91 extension unchanged. New helper reviewed separately; old suites/admission not repeated. Sole new opaque dispatch hash-only; superseded opaque reference excluded from release evidence. Ready for BINDING02 and focused release seal; no native authorization or capacity/RSS guarantee.'}
(H/'BINDING_REVIEW02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':'accepted','checks':len(checks),'sha256':hashlib.sha256((H/'BINDING_REVIEW02.json').read_bytes()).hexdigest()}))

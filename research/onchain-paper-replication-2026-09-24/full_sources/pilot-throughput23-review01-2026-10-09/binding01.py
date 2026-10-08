import ast,copy,hashlib,json,os,resource,signal,stat
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(60)
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;N=F/'real-data-pilot-final23-2026-10-09';O=F/'real-data-pilot-final22-2026-10-08';evidence={};checks=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(65536),b''):h.update(b)
 return h.hexdigest()
def read(p):evidence[str(p.relative_to(R))]=sha(p);return json.loads(p.read_bytes())
def ck(n,v):
 assert v,n
 checks.append(n)
name='eth-paper-real-data-end-to-end-resource-20261009-23';binding=read(N/'BINDING_DRAFT02.json');gate=read(N/'gate02.json');oldgate=read(O/'gate01.json');ex=gate['experiments'][name];private=binding['transport']
ck('identity_draft',binding['identity']==name and binding['binding_review'] is None)
for k in oldgate: 
 if k!='experiments':ck('unchanged_gate_'+k,gate[k]==oldgate[k])
ck('all_history_unchanged',set(gate['experiments'])-set(oldgate['experiments'])=={name} and all(gate['experiments'][k]==v for k,v in oldgate['experiments'].items()))
ck('349_sources_64_inputs',len(ex['source_files'])==349 and len(ex['inputs'])==64)
for p,h in ex['source_files'].items():ck('source_'+p,p!=private['path'] and sha(R/p)==h);evidence[p]=h
for role,ref in ex['inputs'].items():
 ck('input_'+role,sha(R/ref['path'])==ref['sha256']);evidence[ref['path']]=ref['sha256']
 if ref['path']==private['path']:ck('sole_opaque_role',role=='archive_transport')
for role,ref in binding.items():
 if isinstance(ref,dict) and {'path','sha256'}<=ref.keys():
  p=R/ref['path'];ck('binding_'+role,sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes']);evidence[ref['path']]=ref['sha256']
# Execute ONLY isolated unchanged metadata validators extracted from AST; no imports/admission/scans.
tree=ast.parse((N/'preflight01.py').read_text());ns={'Path':Path,'ROOT':R,'copy':copy,'OPAQUE_ROLE':'archive_transport','stat':stat,'os':os,'hashlib':hashlib}
for namefn in ['need','reference','validate_opaque','inverse_binding']:
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==namefn);exec(compile(ast.Module(body=[node],type_ignores=[]),'<reviewed_metadata_only>','exec'),ns)
ns['validate_opaque'](private);checks.append('private_hash_only_stable_descriptor')
prep=read(N/'PREPARATION_RESULT02.json');bound=read(N/'TRANSPORT_BINDING02.json');req=read(N/'TRANSPORT_REQUEST02.json');draft=read(N/'INPUT_DRAFT02.json');archive=read(R/draft['protocol']['references']['archive_policy']['path'])
ck('actual_binder_request_join',req==bound['source_request'] and req['prepared']==binding['preparation'] and req['archive_policy']==draft['protocol']['references']['archive_policy'])
raw=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();ns['inverse_binding'](prep,archive,bound,private,raw,lambda b:hashlib.sha256(b).hexdigest());checks.append('actual_binder_inverse')
refs=read(N/'INPUT_REFS01.json');ck('eight_public_bound_roles',set(refs)==set(bound['inputs']) and len(refs)==8)
for role,ref in refs.items():
 ck('bound_public_'+role,read(R/ref['path'])==bound['inputs'][role] and all(ex['inputs'][role][k]==ref[k] for k in ['path','sha256']))
for role,ref in draft['protocol']['references'].items():
 if role not in refs and role!='archive_transport':ck('inherited_input_'+role,all(ex['inputs'][role][k]==ref[k] for k in ['path','sha256']))
s=(N/'preflight01.py').read_text().replace('eth-paper-real-data-end-to-end-resource-20261009-23','eth-paper-real-data-end-to-end-resource-20261008-22').replace('ethpilot-20261009-23','ethpilot-20261008-22').replace("HERE/'gate02.json'","HERE/'gate01.json'").replace('effective_attempt_budget!=94','effective_attempt_budget!=93')
ck('preflight_literal_inverse',s==(O/'preflight01.py').read_text());ck('root_io_identical',(N/'root_io.py').read_bytes()==(O/'root_io.py').read_bytes())
for fn in ['preflight01.py','root_io.py']:
 p=str((N/fn).relative_to(R));ck('entry_in_source_closure_'+fn,ex['source_files'][p]==sha(N/fn))
scratch=read(N/'MATCHING_SCRATCH_RESERVATION01.json');ck('scratch_exact',scratch['experiment']==name and scratch['incremental_explicit_numeric_scratch_bytes']==262144 and scratch['installed_source']['sha256']=='1d1377bd1faab3b563ff6d07c2e55908c556b71fb5add4126d5860d481a099fe' and scratch['independent_source_review']['sha256']=='8e8efc359efaede583f7d418da68fe6826757aa33c2787e63f149a817de54c3c')
ck('extension94_join',ex['cumulative_budget_extension']['review']['sha256']=='fdcccb350c8dd3f31157faa320c723eb21fa2731291313c741e0d87b96e16db7')
ck('prior22_recovery_join',binding['prior_recovery_review']['sha256']=='3a852cf45f8c6ed2043dc273e30befb31a2c5f5b2d0ff20db2b4138176c92ee0')
ck('accepted_draft_review',sha(H/'METADATA_REVIEW02.json')=='aa8c2615afa45e4a247dbd37f53a8a883fe32e2fd3fe3ee5fa7962ef22da08d9')
ck('no_claim_or_attempt',not (R/'research_runs'/name).exists() and not (N/'launch-attempt01.json').exists())
x={'schema_version':1,'decision':'accepted','identity':name,'evidence':evidence,'source_count':349,'input_count':64,'opaque_evidence_count':1,'checks':checks,'scope':'Exact changed final23 binding/caller/source/input joins only. Original22 family/history preserved. Private dispatch hash-only; actual public binder inverse verified. Reuses source8e8e, budgetfdcc, metadataaa8c acceptance. No runtime/current-capacity/admission/commit/remote-recovery/launch claim. Final BINDING01 and release exact hash sealing still required.'}
(H/'BINDING_REVIEW01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'checks':len(checks),'evidence':len(evidence),'sha256':sha(H/'BINDING_REVIEW01.json')}))

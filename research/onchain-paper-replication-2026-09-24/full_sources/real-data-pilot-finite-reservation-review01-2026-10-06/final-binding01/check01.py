from pathlib import Path
import ast,copy,hashlib,json,os,stat,subprocess,sys,types
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[4];FS=HERE.parent.parent
D=FS/'real-data-pilot-final03-2026-10-06';O=FS/'real-data-pilot-final02-2026-10-06';N='eth-paper-real-data-end-to-end-resource-20261006-03';OLD=N[:-2]+'02'
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
previous=json.loads((FS/'real-data-pilot-compact-policy-correction-review01-2026-10-06/successor03/RELEASE_REVIEW01.json').read_bytes());evidence=previous['evidence'].copy()
private_old=[p for p in evidence if 'real_pilot_runtime' in p];assert len(private_old)==1
for p in private_old:del evidence[p]
def body(p):
 assert p.stat().st_size<4*1024**2 and 'real_pilot_runtime' not in p.parts and p.name!='connection.json';b=p.read_bytes();evidence[str(p.relative_to(ROOT))]=sha(b);return b
def read(p):return json.loads(body(p))
def auth(r):
 b=body(ROOT/r['path']);assert sha(b)==r['sha256'];assert 'bytes' not in r or len(b)==r['bytes'];return json.loads(b)
def need(v,m):
 if not v:raise ValueError(m)
review=read(HERE.parent/'SOURCE_REVIEW01.json');assert review['decision']=='accepted'
gate=read(D/'gate01.json');oldgate=read(O/'gate01.json');x=oldgate['experiments'][OLD];y=gate['experiments'][N]
assert len(y['source_files'])==202 and len(y['inputs'])==59 and y['parent'] is None
changes={i['target']:i['candidate_sha256'] for i in review['source_changes']}
assert {p for p in set(y['source_files'])-set(x['source_files']) if p.startswith('tradingagents/')}=={'tradingagents/research/onchain_replication/real_pilot_reservations.py'}
for p,h in y['source_files'].items():
 if p in changes:assert sha(body(ROOT/p))==h==changes[p]
 elif p in x['source_files']:assert x['source_files'][p]==h==previous['evidence'][p]
 else:assert sha(body(ROOT/p))==h
 evidence[p]=h
r=read(D/'NUMERICAL_CONTEXT_REANCHOR01.json');oldpair=auth(r['old_pair_policy']);pair=auth(r['new_pair_policy']);expected=copy.deepcopy(oldpair);expected['numerical_source']['commit']=r['source_commit'];expected['numerical_source']['files'].update(changes);assert expected==pair and len(pair['numerical_source']['files'])==179
assert set(subprocess.check_output(['git','diff','--name-only',oldpair['numerical_source']['commit'],r['source_commit'],'--','tradingagents'],cwd=ROOT,text=True).splitlines())==set(changes)
for p,h in changes.items():assert sha(subprocess.check_output(['git','show',r['source_commit']+':'+p],cwd=ROOT))==h
binding=read(D/'BINDING_DRAFT01.json');draft=auth(binding['draft']);saved=auth(binding['preparation']);bound=auth(binding['transport_binding']);auth(binding['baseline'])
for k in ('prior_outcome_review','prior_preservation_complete','prior_recovery_review'):auth(binding[k])
assert binding['prior_recovery_review']['sha256']=='84c5717876b7d643405e0c3b4178b3a91ffcba4f3f6e88c152a7ed14981c6049'
assert bound['source_request']['prepared']==binding['preparation']
su=FS/'real-data-pilot-packed-feature-successor04-2026-10-06';oldsu=FS/'real-data-pilot-packed-feature-successor03-2026-10-06'
assert body(su/'successor02.py')==body(oldsu/'successor02.py')
inv=read(su/'IDENTITY_INVERSE01.json')
for v in inv.values():
 a=body(ROOT/v['before']['path']);b=body(ROOT/v['after']['path']);assert sha(a)==v['before']['sha256'] and sha(b)==v['after']['sha256'] and a.count(OLD.encode())==1 and b.replace(N.encode(),OLD.encode())==a
olddeps=read(oldsu/'DEPENDENCIES02.json');deps=read(su/'DEPENDENCIES02.json')
assert json.loads(json.dumps(olddeps).replace(str(oldsu.relative_to(ROOT)),str(su.relative_to(ROOT))).replace(inv['builder']['before']['sha256'],inv['builder']['after']['sha256']).replace(inv['controls']['before']['sha256'],inv['controls']['after']['sha256']))==deps
m=types.ModuleType('finite_prepare');m.__file__=str(su/'successor02.py');exec(compile(body(su/'successor02.py'),m.__file__,'exec'),vars(m));assert m.prepare(ROOT,draft)==saved
preflight=body(D/'preflight01.py');oldpre=body(O/'preflight01.py');assert preflight==oldpre.replace(OLD.encode(),N.encode()).replace(b'packed-feature-successor03-',b'packed-feature-successor04-').replace(b'!=73',b'!=74').replace(b"'effective_attempt_budget':73",b"'effective_attempt_budget':74")
assert body(D/'root_io.py')==body(O/'root_io.py').replace(OLD.encode(),N.encode())
fn=next(n for n in ast.parse(preflight).body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');env={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'pure inverse','exec'),env)
archive=auth(saved['builder03_spec']['references'][saved['builder03_spec']['template_roles']['archive']]);env['inverse_binding'](saved,archive,bound,binding['transport'],raw,sha)
oldbound=read(O/'TRANSPORT_BINDING02.json');expected=json.loads(json.dumps(oldbound['inputs']).replace(OLD,N).replace('ethpilot-20261006-02','ethpilot-20261006-03'))
for desc in (expected['execution_job']['payload']['representation_jobs']['original32']['descriptor'],expected['producer_plan']['producers']['original32']['descriptor']):
 for k,role in [('pair_execution','pair_policy'),('compact_execution','compact_policy'),('compact_archive_execution','archive_policy')]:desc[k]['policy_sha256']=y['inputs'][role]['sha256']
assert expected==bound['inputs']
for role,value in bound['inputs'].items():assert body(ROOT/y['inputs'][role]['path'])==raw(value) and sha(raw(value))==y['inputs'][role]['sha256']
private=binding['transport'];assert private==bound['private_input']['archive_transport'] and all(y['inputs']['archive_transport'][k]==private[k] for k in ('path','sha256'))
p=ROOT/private['path'];s=p.lstat();parent=p.parent.lstat();assert s.st_size==928==private['bytes'] and stat.S_IMODE(s.st_mode)==0o600 and stat.S_IMODE(parent.st_mode)==0o700 and s.st_uid==parent.st_uid==os.getuid() and s.st_nlink==1 and p.resolve()==p
assert private['sha256']==oldbound['private_input']['archive_transport']['sha256'];evidence[private['path']]=private['sha256']
C=FS/'real-data-pilot-finite-reservation-correction01-2026-10-06'
for role,ref in y['inputs'].items():
 if role in bound['inputs'] or role=='archive_transport':continue
 if role=='pair_policy':assert sha(body(ROOT/ref['path']))==ref['sha256'];continue
 if role in ('compact_policy','mcm_policy'):assert body(ROOT/ref['path'])==body(C/'metadata01'/str(role+'.json')) and sha(body(ROOT/ref['path']))==ref['sha256'];continue
 assert ref==x['inputs'][role] and previous['evidence'][ref['path']]==ref['sha256'];evidence[ref['path']]=ref['sha256']
s=bound['inputs']['execution_job']['payload']['representation_jobs']['original32'];p=bound['inputs']['producer_plan']['producers']['original32'];assert all(p.get(k)==v for k,v in s.items())
for field,key,hkey in [('compact_policy_input','compact_execution','policy_sha256'),('compact_archive_input','compact_archive_execution','policy_sha256'),('pair_checkpoint_input','pair_execution','policy_sha256'),('original_dictionary_input','original_dictionary_import','sha256'),('original_dictionary_stage_input','original_dictionary_stage','sha256')]:assert s['descriptor'][key][hkey]==y['inputs'][s[field]]['sha256']
# Admission authenticates amendment/registration semantics; independent budget review remains explicit.
read(HERE.parent/'EXTENSION_REVIEW01.json');read(HERE.parent/'ALLOCATION_REVIEW01.json');read(HERE.parent/'ALLOCATION_CHECK01.json')
admission=read(D/'ACTUAL_READONLY_ADMISSION01.json');assert admission['ready'] and admission['effective_attempt_budget']==74 and admission['source_pins']==202 and admission['input_roles']==59
assert sha(subprocess.check_output(['git','show',admission['source']+':'+str((D/'gate01.json').relative_to(ROOT))],cwd=ROOT))==sha(body(D/'gate01.json'))
assert all(evidence[p]==h for p,h in y['source_files'].items()) and all(evidence[v['path']]==v['sha256'] for v in y['inputs'].values())
assert not (ROOT/'research_runs'/N).exists() and not any(k in sys.modules for k in ('numpy','torch','scipy','tradingagents'))
checks={'package_pins':179,'source_pins':202,'input_roles':59,'pure_prepare_equal':True,'binder_inverse_equal':True,'all_descriptor_joins':True,'exact_canonical_generated_bytes':True,'finite_reservations_exact_accepted':True,'genuine_committed_admission':admission}
result={'schema_version':1,'status':'PASS','identity':N,'checks':checks,'findings':[],'evidence':evidence,'private_body_read':False,'preflight_sha256':sha(preflight)}
(HERE/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
review={'schema_version':1,'decision':'accepted','identity':N,'reviewer':'independent pilot_correction_review','scope':'Exact six-reference final03 composition; accepted finite source correction, 179-pin control reanchor, unchanged scientific/resource constraints, cumulative74 and actual committed admission. Final binding and release still required.','evidence':{binding[k]['path']:binding[k]['sha256'] for k in ('gate','draft','preparation','baseline','transport','transport_binding')},'checks':checks,'findings':[],'private_input_qualification':'Exactly one fresh protected path; public binder digest and stat only, body never opened. Opaque entry hash mandatory.'}
(HERE/'BINDING_REVIEW01.json').write_text(json.dumps(review,indent=2,sort_keys=True)+'\n');print('BINDING_REVIEW01',sha((HERE/'BINDING_REVIEW01.json').read_bytes()))

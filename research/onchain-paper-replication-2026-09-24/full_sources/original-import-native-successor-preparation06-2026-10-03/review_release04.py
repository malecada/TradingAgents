"""Independent exact preparation read-only checks; no job/claim/numerical imports."""
import ast,hashlib,importlib.util,json,os,stat,subprocess,sys,tarfile
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];C=P/'capsule04';F=P.parent
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='protocol.allow',GIT_CONFIG_VALUE_0='never')
os.environ.update({k:env[k] for k in ['GIT_NO_LAZY_FETCH','GIT_TERMINAL_PROMPT','GIT_OPTIONAL_LOCKS','GIT_CONFIG_COUNT','GIT_CONFIG_KEY_0','GIT_CONFIG_VALUE_0']})
def git(root,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stderr=subprocess.PIPE)
def fn(tree,name):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
m=read(P/'PREPARATION_MANIFEST04.json');assert sha((P/'PREPARATION_MANIFEST04.json').read_bytes())=='e6c39d32bf5ebc93f504e17b96176717354c39d5f4453e12733dbecbf37b801e'
for row in m['files']:
 b=(P/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
d=read(P/'release-draft01.json');inv=read(P/'source_inventory04.json');assert sha((P/'source_inventory04.json').read_bytes())==d['source_inventory_sha256']=='53313918e21ca67a1f898c0463cc1e05a85519c5b2beb08c23fcb4427b917509'
assert d['status']=='prospective-NOT-released' and d['effective_attempt_budget']==5 and d['historical_closed_attempts']==3
assert git(C,'rev-parse','HEAD').decode().strip()==d['capsule_commit']=='ce0e37f8eaaca258c46944a4cbdb9ae30e40fa26'
assert not (C/'.git/objects/info/alternates').exists()
rows={r['target']:r for r in inv['source_inventory']};assert len(rows)==153 and len(d['source_files'])==162 and sum(n.startswith('tradingagents/') for n in rows)==142
for name,pin in d['source_files'].items():
 b=(C/name).read_bytes();assert sha(b)==pin and git(C,'show',d['capsule_commit']+':'+name)==b and git(C,'show',d['source_anchor']+':'+name)==b
 if name in rows:
  r=rows[name];assert len(b)==r['bytes'] and sha(b)==r['sha256'] and b==(R/r['origin']).read_bytes()
assert sha((C/d['registration']).read_bytes())==d['registration_sha256']=='97ff80aaac2ce79875a95be44ca8adce0205d89752e55e1715a352df42c89149'
# Exact handler-only composition and generator/lineage parity.
pkg=C/'tradingagents/research/onchain_replication';base=ast.parse((F/'imported-source-metadata-correction02-2026-10-03/compact_mcm.py').read_bytes());selected=ast.parse((pkg/'compact_mcm.py').read_bytes())
def primary_handler(t):return next(n for n in ast.walk(fn(t,'_produce_locked')) if isinstance(n,ast.ExceptHandler) and n.name=='primary')
a=primary_handler(base);b=primary_handler(selected);b.body=a.body
assert ast.dump(selected)==ast.dump(base)
assert sha((pkg/'compact_mcm.py').read_bytes())=='6673fa484f37c0c3556c3d158035bb0c7f1db8f4a9f834ca50374c57c1e21b81'
base=ast.parse((P/'resource_fixture.baseline05.py').read_bytes());selected=ast.parse((P/'resource_fixture.py').read_bytes());parent=fn(selected,'_engineering_parent');parent.body=[n for n in parent.body if not(isinstance(n,ast.If) and any(isinstance(v,ast.Constant) and v.value=='original-import-native-success-20261003-04' for v in ast.walk(n)))];selected.body=[n for n in selected.body if not(isinstance(n,ast.FunctionDef) and n.name=='_engineering_parent04')];assert ast.dump(base)==ast.dump(selected)
base=ast.parse((P/'generate_inputs.baseline05.py').read_bytes());selected=ast.parse((P/'generate_inputs01.py').read_bytes());base.body=[n for n in base.body if not(isinstance(n,ast.FunctionDef) and n.name=='registration')];selected.body=[n for n in selected.body if not(isinstance(n,ast.FunctionDef) and n.name=='registration')];assert ast.dump(base)==ast.dump(selected)
# Canonicalization is the only changed original-dictionary function.
canonical=F/'original-dictionary-canonical-validation-candidate01-2026-10-03'
assert sha((pkg/'original_dictionary.py').read_bytes())=='93c0cd1ae882d51df185458ce7304a46dfb66dc7ca337285039541fa70176e88'
assert sha((canonical/'REVIEW_CANONICAL_VALIDATION01.md').read_bytes())==d['source_reviews']['canonical']
old_original=ast.parse((F/'original-import-native-successor-preparation05-2026-10-03/capsule03/tradingagents/research/onchain_replication/original_dictionary.py').read_bytes())
new_original=ast.parse((pkg/'original_dictionary.py').read_bytes())
old_original.body=[n for n in old_original.body if not(isinstance(n,ast.FunctionDef) and n.name=='validate')]
new_original.body=[n for n in new_original.body if not(isinstance(n,ast.FunctionDef) and n.name=='validate')]
assert ast.dump(old_original)==ast.dump(new_original)
prev_inventory=read(F/'original-import-native-successor-preparation05-2026-10-03/source_inventory03.json')
prior={r['target']:r for r in prev_inventory['source_inventory']}
assert set(prior)==set(rows)
assert {n for n in rows if rows[n]['sha256']!=prior[n]['sha256']}=={'fixture_tools/generate_inputs01.py','tradingagents/research/onchain_replication/resource_fixture.py','tradingagents/research/onchain_replication/original_dictionary.py'}
# Resolve relative modules and absolute tradingagents imports without executing them.
edges=0;missing=[]
for name in rows:
 if not name.endswith('.py'):continue
 for n in ast.walk(ast.parse((C/name).read_bytes())):
  parts=[]
  if isinstance(n,ast.ImportFrom) and n.level:
   root=Path(name).parent
   for _ in range(n.level-1):root=root.parent
   parts=[str(root.joinpath(*s.split('.'))) for s in ([n.module] if n.module else [a.name for a in n.names])]
  elif isinstance(n,ast.ImportFrom) and n.module and (n.module=='tradingagents' or n.module.startswith('tradingagents.')):parts=[n.module.replace('.','/')]
  elif isinstance(n,ast.Import):parts=[a.name.replace('.','/') for a in n.names if a.name=='tradingagents' or a.name.startswith('tradingagents.')]
  for target in parts:
   edges+=1
   if not any(v in rows for v in [target+'.py',target+'/__init__.py']):missing.append((name,n.lineno,target))
assert missing==[],missing
# Actual imported dynamic route needs only imported_kernel and its workload.
for name in ['research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py','research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-2026-09-30/workload.py']:assert name in rows
assert 'resource_refusal' not in (pkg/'compact_mcm.py').read_text()
old=F/'original-import-native-successor-preparation05-2026-10-03/capsule03'
for identity in ['original-import-native-success-20261003-01','original-import-native-success-20261003-02','original-import-native-success-20261003-03']:
 for q in (old/'research_runs'/identity).rglob('*'):
  if q.is_file():assert q.read_bytes()==(C/q.relative_to(old)).read_bytes()
for n in ['cumulative-extension01.json','cumulative-extension-review01.json','successor-allocation01.json']:assert (C/'fixture_budget'/n).read_bytes()==(old/'fixture_budget'/n).read_bytes()
# Complete existing preparation archive and original lstat baseline.
ret=read(P/'CAPSULE_PREPARATION01.json');archive=P/'capsule-source-input-gate01.tar.gz';assert sha(archive.read_bytes())==ret['archive_sha256']
rr={r['path']:r for r in ret['members']};assert len(rr)==990
assert {str(q.relative_to(C)) for q in [C,*C.rglob('*')]}==set(rr)
for name,row in rr.items():
 q=C/name;s=q.lstat();assert stat.S_IMODE(s.st_mode)==row['mode'] and s.st_blocks*512==row['allocated_bytes']
 if row['kind']=='file':assert s.st_nlink==1 and stat.S_ISREG(s.st_mode) and len(q.read_bytes())==row['bytes'] and sha(q.read_bytes())==row['sha256'] and s.st_size<=4194304
 else:assert stat.S_ISDIR(s.st_mode)
seen=set()
with tarfile.open(archive,'r|gz') as stream:
 for mem in stream:
  name='.' if mem.name=='capsule04' else mem.name.removeprefix('capsule04/');assert name in rr and name not in seen;seen.add(name);row=rr[name];assert mem.mode==row['mode']
  if row['kind']=='directory':assert mem.isdir()
  else:
   assert mem.isfile() and mem.size==row['bytes'];f=stream.extractfile(mem)
   with f:raw=f.read(mem.size+1)
   assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
assert seen==set(rr) and sum(r['bytes'] for r in rr.values())==6943394 and sum(r['allocated_bytes'] for r in rr.values())==9969664
orig=read(F/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json')
for row in orig['inputs']:assert sha((C/row['capsule_path']).read_bytes())==row['sha256']
for name,pin in orig['original_source_files'].items():assert sha(git(C,'show',orig['original_source']+':'+name))==pin['claim_sha256']
# Public genuine metadata admission only; no ResearchRun or numerical API.
os.chdir(C);sys.path.insert(0,str(C))
from tradingagents.research.admission import admit,claims
from tradingagents.research.onchain_replication import resource_fixture
ad=admit(root=C,registration=d['registration'],experiment=d['cases']['success']['identity'],source=d['capsule_commit']);j=read(C/ad.inputs['execution_job']['path']);resource_fixture.admitted(ad,j)
assert ad.ready and ad.effective_attempt_budget==5 and len(ad.inputs)==32 and len(claims(C))==3
try:admit(root=C,registration=d['registration'],experiment=d['cases']['second_target_publication_failure']['identity'],source=d['capsule_commit'])
except ValueError as e:assert str(e)=='budget extension first-adopter snapshot is stale or incomplete';dependent=str(e)
else:raise AssertionError('dependent admitted too soon')
for entry in d['cases'].values():
 assert not(C/'research_runs'/entry['identity']).exists() and not(C/'fixture_outer'/entry['identity']).exists()
 for name,info in entry['experiment']['inputs'].items():assert sha((C/info['path']).read_bytes())==info['sha256']
 assert read(C/entry['experiment']['inputs']['execution_job']['path'])['resources']==entry['job_resources']
# Selected runtime checker and StorageWatch are read-only, stdlib-only functions.
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
runtime=module('review_runtime',C/'fixture_tools/runtime_gate01.py').check(C,d['runtime'])
storage=module('review_storage',pkg/'workflow_storage.py');obs=storage.StorageWatch(C,j['resources']['storage_budget']['limits']).check()
print('OBSERVATION',json.dumps(obs,sort_keys=True))
assert obs['allocated_bytes']==9969664 and obs['logical_file_bytes']==6943394
assert not {'numpy','torch','scipy'}&set(sys.modules)
print(json.dumps({'manifest_bodies':len(m['files']),'sources':len(d['source_files']),'package':142,'source_and_anchor_joins':162,'local_static_import_edges':edges,'unresolved_static_modules':missing,'handler_only_MCM_parity':True,'resource_fixture_other_AST_parity':True,'generator_outside_registration_parity':True,'original26_Git_and11_JSON':True,'historical_failed_claims_preserved':3,'new_claims':0,'read_only_admission_ready':ad.ready,'effective_budget':ad.effective_attempt_budget,'inputs':len(ad.inputs),'dependent_refusal':dependent,'runtime_records':len(d['runtime']['distribution_records']),'module_origins':len(runtime['module_origins']),'archive_members':len(rr),'files':ret['files'],'directories':ret['directories'],'logical_bytes':6943394,'allocated_bytes':9969664,'storage_observation':obs,'numerical_imports':False},indent=2))

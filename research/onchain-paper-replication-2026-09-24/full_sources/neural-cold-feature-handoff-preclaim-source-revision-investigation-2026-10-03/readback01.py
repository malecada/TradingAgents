"""Explicit source/metadata-only investigation. No research package imports."""
import ast,copy,hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
BASE=HERE.parent
CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-01/source')
CSC=BASE/'neural-cold-feature-handoff-proof-source-composition03-2026-10-03'
GEN=BASE/'neural-cold-feature-handoff-engineering-registration-preparation03-2026-10-03'
BUILDER=BASE/'neural-cold-feature-handoff-root-capsule-builder-preparation01-2026-10-03'
OUTER=BASE/'neural-cold-feature-handoff-proof-outer-preparation03-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
def js(p):return json.loads(p.read_bytes())
def git(*a):return subprocess.check_output(['git',*a],cwd=CAP,env={**os.environ,'GIT_NO_LAZY_FETCH':'1'},timeout=15)
refs={}
def pin(p):
 b=p.read_bytes();refs[str(p)]={'bytes':len(b),'sha256':sha(b)};return b
for p in [CSC/'MANIFEST03.json',CSC/'source_inventory03.json',CSC/'prepare_metadata_composed03.py',CSC/'REPORT03.md',GEN/'MANIFEST03.json',GEN/'generate03.py',BUILDER/'MANIFEST01.json',BUILDER/'builder01.py',OUTER/'proof_release01.py',BASE/'neural-cold-feature-handoff-root-integration01-2026-10-03/PROPOSED_MATERIALIZATION_RELEASE01.json']:
 pin(p)
for name in ['tradingagents/research/verify.py','tradingagents/research/onchain_replication/matching_owner.py','tradingagents/research/onchain_replication/job.py','tradingagents/research/onchain_replication/compact_cold_proof_inputs.py','cold_prep/anchor.json','cold-registration.json','cold_prep/runtime.json','cold_prep/native_environment.json']:
 pin(CAP/name)
inv=js(CSC/'source_inventory03.json');rows=inv['source_inventory'];assert len(rows)==195
source={r['target']:r['sha256'] for r in rows};assert len(source)==195
for r in rows:
 b=(CAP/r['target']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
head=git('rev-parse','HEAD').decode().strip();assert head=='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e'
anchor=js(CAP/'cold_prep/anchor.json');package={p:h for p,h in source.items() if p.startswith('tradingagents/')};assert len(package)==147 and anchor['files']==package
assert anchor['commit']=='c65287a2c70fdc38fd6335a994dfd29fe97e26b4'
target='tradingagents/research/verify.py';assert target in package
assert sha(git('show',anchor['commit']+':'+target))==package[target]
reg=js(CAP/'cold-registration.json');ids=['compact-cold-inputs-20261003-01','compact-cold-comparison-20261003-01'];assert list(reg['experiments'])==ids[:1]
exp=reg['experiments'][ids[0]];assert exp['source_files']==source and len(exp['inputs'])==9
assert next(iter(reg['families'].values()))['attempt_budget']==2 and next(iter(reg['families'].values()))['prior_attempts']==0
absent=[]
for identity in ids:
 for base in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
  p=CAP/base/identity;assert not p.exists() and not p.is_symlink();absent.append(str(p))
config={}
for name in ('recipe','configs','model','training','environment'):
 r=exp['inputs'][name];b=pin(CAP/r['path']);assert sha(b)==r['sha256'];config[name]=r
for name in ('CHARTER_MATERIALIZE02.md','CHARTER_COMPARE02.md','HISTORY02.md'):
 assert pin(CAP/'cold_prep'/name)==pin(GEN/name)
# Execute ONLY actual stdlib source_mapping and its three tiny dependencies.
tree=ast.parse((CSC/'prepare_metadata_composed03.py').read_bytes())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'digest','raw','source_mapping'}]
ns={'hashlib':hashlib,'json':json,'Path':Path};exec(compile(ast.Module(body=nodes,type_ignores=[]),'extracted-source-mapping','exec'),ns)
assert ns['source_mapping'](CAP,inv)==source
checks=['actual195-source-mapping','exact147-current-anchor','actualA-registration-nine-inputs','ten-unclaimed-namespaces']
for label,mutate in [('hash',lambda d:d['source_inventory'][0].__setitem__('sha256','1'*64)),('status',lambda d:d.__setitem__('status','accepted')),('membership',lambda d:d['source_inventory'].pop())]:
 changed=copy.deepcopy(inv);mutate(changed)
 try:ns['source_mapping'](CAP,changed)
 except ValueError as e:assert str(e)=='frozen exact composition inventory differs'
 else:raise AssertionError('changed inventory accepted')
 checks.append('actual-helper-refuses-'+label)
# Literal source-pin extraction, no preparation/research module import.
constants={}
for label,p,names in [('metadata',CSC/'prepare_metadata_composed03.py',[]),('generator',GEN/'generate03.py',['PINNED_INVENTORY','RELEASE_SHA','CONFIG_PINS']),('builder',BUILDER/'builder01.py',['INV'])]:
 t=ast.parse(p.read_bytes());constants[label]={}
 for n in t.body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in names:constants[label][n.targets[0].id]=ast.literal_eval(n.value)
 assert not any(isinstance(n,ast.Import) and any(a.name.split('.')[0] in {'numpy','torch'} for a in n.names) for n in t.body)
assert constants['generator']['PINNED_INVENTORY']==constants['builder']['INV']==sha((CSC/'source_inventory03.json').read_bytes())
result={'status':'source-metadata-readback-only','current_head':head,'anchor':anchor['commit'],'sources':195,'package':147,'verify_sha256':source[target],'checks':checks,'input_names':sorted(exp['inputs']),'unchanged_config_refs':config,'constants':constants,'unclaimed_paths_observed':absent,'qualification':'No candidate source read or accepted; no source activation, registration, numerical imports, authority or jobs.'}
(HERE/'readback01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(HERE/'source_refs01.json').write_text(json.dumps(refs,indent=2,sort_keys=True)+'\n')
print(json.dumps({'checks':checks,'sources':195,'package':147,'status':'PASS'},sort_keys=True))

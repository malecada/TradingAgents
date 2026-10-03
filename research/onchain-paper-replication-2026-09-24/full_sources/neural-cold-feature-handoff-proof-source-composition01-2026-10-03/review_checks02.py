"""Independent read-only bytes/AST checks; no package or numerical imports."""
from pathlib import Path
import ast,hashlib,json,os,subprocess,sys
P=Path(__file__).resolve().parent; R=P.parents[3]
def digest(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def checked(p,row):
 b=p.read_bytes();assert digest(b)==row['sha256'] and len(b)==row['bytes'],str(p);return b
m=load(P/'MANIFEST01.json');assert digest((P/'MANIFEST01.json').read_bytes())=='d1d5d3f60de896b14edfc254d3ca31a7d32dae7ed490a3f5db18c06e10094216'
for row in m['files']:checked(P/row['path'],row)
assert len(m['files'])==179 and sum(x['bytes'] for x in m['files'])==3147795
inv=load(P/'source_inventory01.json');rows={r['target']:r for r in inv['source_inventory']};assert len(rows)==164
assert sum(n.startswith('tradingagents/') for n in rows)==147
assert sum(r['bytes'] for r in rows.values())==2963908
ENV=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
gitjoins=0
for name,row in rows.items():
 b=checked(R/row['snapshot'],row);assert b==checked(R/row['origin'],row)
 if row['git_commit']:
  old=subprocess.check_output(['git','-c','protocol.allow=never','show',row['git_commit']+':'+row['git_path']],cwd=R,env=ENV)
  assert old==b,name;gitjoins+=1
base=load(R/inv['base']['path']);assert digest((R/inv['base']['path']).read_bytes())==inv['base']['sha256']
bm={r['target']:r for r in base['source_inventory']};unchanged=sum(rows[n]['sha256']==r['sha256'] for n,r in bm.items());assert unchanged==147
for folder,filename,key in [('neural-cold-feature-handoff-proof-preparation01-2026-10-03','install-map01.json','source'),('neural-cold-feature-handoff-proof-outer-preparation02-2026-10-03','install-map02.json','origin')]:
 for r in load(P.parent/folder/filename)['files']:assert (R/r[key]).read_bytes()==(R/rows[r['target']]['snapshot']).read_bytes()
dep=load(P/'DEPENDENCY_READBACK01.json')
for row in dep['dependencies']:checked(R/row['path'],row)
for row in dep['original_preservation']['original_input_references']:checked(R/row['origin'],row)
assert len(dep['original_preservation']['original_source_path_pins'])==26
rt=load(R/'research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-native-preparation-2026-10-03/runtime01.json')
for row in rt['distribution_records']:assert digest(Path(row['record']).read_bytes())==row['record_sha256']
assert len(rt['distribution_records'])==251
for n in ['configs01.json','recipe01.json','model01.json','training01.json']:assert (P/n).read_bytes()==(P.parent/'neural-cold-feature-handoff-proof-preparation01-2026-10-03'/n).read_bytes()
missing=[]
for target,row in rows.items():
 if not target.endswith('.py'):continue
 for n in ast.walk(ast.parse((R/row['snapshot']).read_bytes())):
  if isinstance(n,ast.ImportFrom) and n.level:
   parent=Path(target).parent
   for _ in range(n.level-1):parent=parent.parent
   modules=[n.module] if n.module else [a.name for a in n.names]
   for mod in modules:
    basepath=parent.joinpath(*mod.split('.'));choices=[str(basepath)+'.py',str(basepath/'__init__.py')]
    if not any(c in rows for c in choices):missing.append({'file':target,'line':n.lineno,'module':mod})
assert missing==[{'file':'tradingagents/research/onchain_replication/compact_mcm.py','line':282,'module':'resource_refusal'}]
# Extract only the two actual source-selection functions. Substitute a read-only
# hash namespace/proof boundary; this is NOT genuine Binding/Owner admission.
pkg=P/'source-bodies/tradingagents/research/onchain_replication'
def literal(path,name):
 for n in ast.parse(path.read_text()).body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets):return ast.literal_eval(n.value)
from types import SimpleNamespace as NS
k=literal(pkg/'compact_dictionary.py','KERNEL'); reader=literal(pkg/'compact_samples.py','READER');mk=literal(pkg/'compact_mcm.py','KERNEL')
sm={name:r['sha256'] for name,r in rows.items()};root=P/'source-bodies'
proof=NS(owner=NS(bound=NS(_run=NS(admission=NS(root=root,experiment={'source_files':sm})))))
def require(v,m):
 if not v:raise ValueError(m)
def extracted(path,fn,env):
 n=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==fn);exec(compile(ast.Module(body=[n],type_ignores=[]),str(path),'exec'),env);return env[fn]
dict_env={'KERNEL':k,'compact_samples':NS(READER=reader),'ROOT':root,'file_hash':lambda p:digest(p.read_bytes()),'require':require}

refused=None
try:extracted(pkg/'compact_dictionary.py','_sources',dict_env)(proof)
except ValueError as e:refused=str(e)
assert refused=='compact dictionary numerical source not admitted or changed'
# Fixed-width valid-looking pins quantify source-map extent only; no gate/input
# is changed and no metadata start or authority is fabricated.
ds={name:'0'*64 for name in (k,reader)};ms=ds|{mk:'0'*64}
size=lambda x:len((json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode())
externals=[]
for filename,name in [('compact_samples.py','READER'),('compact_mcm.py','KERNEL'),('compact_sampler.py','CORE'),('compact_features.py','BOUNDARY'),('compact_denominator.py','VALIDATOR'),('compact_native_features.py','NATIVE')]:
 value=literal(pkg/filename,name)
 assert value not in rows
 externals.append({'declared_in':filename,'constant':name,'missing_target':value})
assert not {'numpy','torch','scipy','tradingagents'}&set(sys.modules)
print(json.dumps({'manifest':len(m['files']),'manifest_bytes':m['total_bytes'],'sources':len(rows),'package':147,'source_bytes':inv['logical_bytes'],'git_source_joins':gitjoins,'base_unchanged_sources':unchanged,'overlay_bodies':17,'dependencies':12,'original_JSON':11,'original_reference_paths':26,'original_Git_reverified':False,'runtime_RECORDS':251,'missing_relative_modules':missing,'missing_direct_dynamic_sources':externals,'actual_extracted_dictionary_sources_refusal':refused,'scientific_dictionary_source_count':len(ds),'scientific_dictionary_source_map_bytes_fixed64pin':size(ds),'scientific_MCM_source_count':len(ms),'scientific_MCM_source_map_bytes_fixed64pin':size(ms),'whole_registered_source_map_bytes':size(sm),'numerical_imports':False,'actual_authority':False},indent=2))

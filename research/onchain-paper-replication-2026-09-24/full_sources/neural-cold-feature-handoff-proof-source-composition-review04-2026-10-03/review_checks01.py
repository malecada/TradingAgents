"""Independent frozen-source/metadata checks only; never invokes a builder stage."""
import ast,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; BASE=HERE.parent;ROOT=HERE.parents[3]
C=BASE/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03'
C3=C.with_name('neural-cold-feature-handoff-proof-source-composition03-2026-10-03')
G=BASE/'neural-cold-feature-handoff-engineering-registration-preparation04-2026-10-03'
G3=G.with_name('neural-cold-feature-handoff-engineering-registration-preparation03-2026-10-03')
B=BASE/'neural-cold-feature-handoff-root-capsule-builder-preparation02-2026-10-03'
B1=B.with_name('neural-cold-feature-handoff-root-capsule-builder-preparation01-2026-10-03')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def check_manifest(p,h):
 assert sha(p.read_bytes())==h
 m=read(p);assert len(m['files'])==m['file_count']==len({r['path'] for r in m['files']})
 for r in m['files']:
  b=(p.parent/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'],r['path']
 return m['file_count']
counts=[check_manifest(C/'MANIFEST04.json','10fba546b2ebcf39e33fb80da710be56c7fa518ba3447ba87bdc40aa6b6bcc99'),check_manifest(G/'MANIFEST04.json','ccd6a09d1022e7fce0d685cbfc53e74c5437fb0a0dffab91a9879adfdbfd0884'),check_manifest(B/'MANIFEST02.json','8feb177726f5df8ce5a2875aa3a7d13fca861270bb329cedbb0f476ac6b2ce9a')]
inv=read(C/'source_inventory04.json');old=read(C3/'source_inventory03.json');rows={r['target']:r for r in inv['source_inventory']};oldrows={r['target']:r for r in old['source_inventory']}
assert len(rows)==195 and set(rows)==set(oldrows) and sum(t.startswith('tradingagents/') for t in rows)==147
assert [t for t in rows if rows[t]['sha256']!=oldrows[t]['sha256']]==['tradingagents/research/verify.py']
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0');gitjoins=0
for target,r in rows.items():
 b=(C/'source-bodies'/target).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
 assert b==(ROOT/r['origin']).read_bytes()==(ROOT/r['snapshot']).read_bytes()
 if r.get('git_commit'):
  assert subprocess.check_output(['git','-c','protocol.allow=never','show',r['git_commit']+':'+r['git_path']],cwd=ROOT,env=env)==b;gitjoins+=1
 if target!='tradingagents/research/verify.py':assert r==oldrows[target] and b==(C3/'source-bodies'/target).read_bytes()
assert rows['tradingagents/research/verify.py']['git_commit'] is None
assert rows['tradingagents/research/verify.py']['sha256']=='3a45746a388307d1b375c885bb2fd7a22c2a60f139df714d2bbe98906d57d7eb'
assert sum(r['bytes'] for r in rows.values())==inv['logical_bytes']==3278877
rawsha=sha((C/'source_inventory04.json').read_bytes());canonicalsha=sha((json.dumps(inv,sort_keys=True,separators=(',',':'))+'\n').encode())
assert rawsha=='e8d8594d1c7aabe4076bf2b4bab7454cb0fad48ec8f46b754e06fc3f3ddb6773' and canonicalsha=='3fc6a3afc3d50a9df1c24533c8343b8cd769a7d513a3bd8d0c27be298808bcc8'
# Inverse full AST, not only selected functions.
def inverse(new,old,replacements):
 s=new.read_text()
 for a,b in replacements.items():s=s.replace(b,a)
 assert ast.dump(ast.parse(s))==ast.dump(ast.parse(old.read_bytes()))
inverse(C/'prepare_metadata_composed04.py',C3/'prepare_metadata_composed03.py',{'aff7a877446e94a10c75d73f093c643e3e1f90296d86337352cd0f8dfac69379':canonicalsha,'source-only-outer03-unreviewed':'source-only-verify-batch04-unreviewed'})
inverse(G/'generate04.py',G3/'generate03.py',{'8576e2baba60576818ee4def16fcfad32cc69bd197c4ff1b727808d9695786d2':rawsha})
inverse(B/'builder02.py',B1/'builder01.py',read(B/'replacements02.json'))
for n in ('recipe01.json','configs01.json','model01.json','training01.json'):assert (C/n).read_bytes()==(C3/n).read_bytes()
for n in ('CHARTER_MATERIALIZE02.md','CHARTER_COMPARE02.md','HISTORY02.md','request-compare02.json','request-materialize03.json'):assert (G/n).read_bytes()==(G3/n).read_bytes()
for n in ('request-export01.json','request-inputs01.json','request-materialize01.json','request-compare01.json'):assert (B/n).read_bytes()==(B1/n).read_bytes()
def extract(p,names,ns):
 tree=ast.parse(p.read_bytes());body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 exec(compile(ast.Module(body=body,type_ignores=[]),str(p),'exec'),ns);return ns
ns=extract(C/'prepare_metadata_composed04.py',{'digest','raw','source_mapping'},{'Path':Path,'hashlib':hashlib,'json':json})
f=ns['source_mapping'];assert f(C/'source-bodies',inv)=={t:r['sha256'] for t,r in rows.items()}
oldns=extract(C3/'prepare_metadata_composed03.py',{'digest','raw','source_mapping'},{'Path':Path,'hashlib':hashlib,'json':json})
def refuse(call):
 try:call()
 except (ValueError,KeyError,FileNotFoundError):return
 raise AssertionError('expected refusal')
refuse(lambda:oldns['source_mapping'](C/'source-bodies',inv))
for k in range(6):
 v=copy.deepcopy(inv)
 if k==0:v['status']='accepted'
 if k==1:v['execution_admitted']=True
 if k==2:v['source_inventory'][0]['target']='../escape'
 if k==3:v['source_inventory'].reverse()
 if k==4:v['source_inventory'][0]['sha256']='0'*64
 if k==5:v['source_inventory'].pop()
 refuse(lambda:f(C/'source-bodies',v))
# Concrete namespace, native/resource and runtime-denominator refusal functions,
# executed only with synthetic scalar metadata; never validate/render/execute.
import re,stat
bn=extract(B/'builder02.py',{'require','relative','reference_shape','ordered_rows','runtime_shape','request_shape'},{'Path':Path,'re':re,'MAX':4194304})
for p in ('../x','/tmp/x','x//y','.env','keys/x'):refuse(lambda:bn['relative'](p))
assert bn['ordered_rows'](inv['source_inventory'])==inv['source_inventory']
rr={'distribution_records':[{'name':str(i),'record':'/synthetic/'+str(i),'record_sha256':'ab'*32} for i in range(251)]};bn['runtime_shape'](rr)
refuse(lambda:bn['runtime_shape']({'distribution_records':rr['distribution_records'][:-1]}));refuse(lambda:bn['runtime_shape']({'distribution_records':rr['distribution_records'][:-1]+rr['distribution_records'][:1]}))
root=Path('/synthetic-review-not-created');gb=1073741824
p={'memory_max_bytes':3*gb,'memory_high_bytes':3*gb,'reserve_bytes':3*gb,'start_reserve_bytes':6*gb,'wall_seconds':1800,'disk_floor_bytes':10*gb,'disk_paths':[str(root)],'native_unit_limits':{'file_size_bytes':4194304},'storage_budget':{'root':str(root),'limits':{'max_allocated_bytes':gb,'max_logical_bytes':gb,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}}
gn=extract(G/'generate04.py',{'require','resources'},{'GIB':gb,'MAX':4194304});assert gn['resources'](root,p)==p
for key in ('memory_max_bytes','memory_high_bytes','reserve_bytes','start_reserve_bytes','wall_seconds','disk_floor_bytes'):refuse(lambda:gn['resources'](root,dict(p,**{key:True})))
refuse(lambda:gn['resources'](root,dict(p,physical_policy={})))
# Reuse independently authored finite static declaration analyzer, never imported implementations.
analyzer=BASE/'neural-cold-feature-handoff-proof-source-composition02-2026-10-03/source_symbols01.py'
st=ast.parse(analyzer.read_bytes());st.body=[n for n in st.body if not(isinstance(n,ast.ImportFrom) and n.module=='discover_source01')]
an={'ROOT':ROOT};exec(compile(st,'<bounded-source-expression-analyzer>','exec'),an)
analysisrows={t:dict(r,origin=str((C/'source-bodies'/t).relative_to(ROOT))) for t,r in rows.items()};w=an['Symbols'](analysisrows)
required=w.module('tradingagents/research/onchain_replication/compact_native_producer.py').required_sources();assert len(required)==47 and required<=set(rows);declarations=len(w.modules)
edges=0;loaders=[]
for target,r in rows.items():
 if not target.endswith('.py'):continue
 mod=w.module(target);mod.cache['root']=ROOT
 for n in ast.walk(mod.tree):
  names=[]
  if isinstance(n,ast.ImportFrom) and n.level:
   base=Path(target).parent
   for _ in range(n.level-1):base=base.parent
   names=[str(base.joinpath(*s.split('.'))) for s in ([n.module] if n.module else [a.name for a in n.names])]
  elif isinstance(n,ast.ImportFrom) and n.module and n.module.startswith('tradingagents'):
   base=n.module.replace('.','/');names=[base]
   if base+'/__init__.py' in rows:names += [base+'/'+a.name for a in n.names if base+'/'+a.name+'.py' in rows]
  elif isinstance(n,ast.Import):names=[a.name.replace('.','/') for a in n.names if a.name.startswith('tradingagents')]
  for name in names:edges+=1;assert name+'.py' in rows or name+'/__init__.py' in rows,(target,n.lineno,name)
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('load','_load','module') and len(n.args)>=2:
   if n.func.id in ('load','_load'):
    declared=next((f for f in mod.tree.body if isinstance(f,ast.FunctionDef) and f.name==n.func.id),None)
    if declared is None or not any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='spec_from_file_location' for c in ast.walk(declared)):continue
   path=mod.evaluate(n.args[1]);name=str(Path(path).relative_to(ROOT));assert name in rows;loaders.append([target,n.lineno,name])
assert 'resource_refusal' not in (C/'source-bodies/tradingagents/research/onchain_replication/compact_mcm.py').read_text()
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'status':'passed-source-and-metadata-only','manifest_counts':counts,'sources':195,'package':147,'logical_source_bytes':3278877,'historical_git_joins':gitjoins,'changed_target':'tradingagents/research/verify.py','all_three_inverse_AST':True,'raw_inventory':rawsha,'canonical_inventory':canonicalsha,'mutations_refused':6,'source_mapping':195,'static_edges':edges,'declaration_modules':declarations,'required_pins':sorted(required),'generic_loader_callers':loaders,'source_analyzer_sha256':sha(analyzer.read_bytes()),'genuine_authority_or_capsule_or_registration_created':False,'numerical_imports':False},indent=2))

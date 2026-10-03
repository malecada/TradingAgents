import ast,copy,hashlib,importlib.util,json,os,stat,subprocess,sys,types
from pathlib import Path
O=Path(__file__).resolve().parent
P=O.parent/'batch-output-full-source-helper-preparation01-2026-10-03'
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
sha=lambda b:hashlib.sha256(b).hexdigest()
checks=[];inventory=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def body(p):
 s=p.lstat();check(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'regular singleton '+str(p));raw=p.read_bytes();inventory.append({'path':str(p),'type':'regular','mode':oct(stat.S_IMODE(s.st_mode)),'bytes':len(raw),'sha256':sha(raw)});return raw
def load(name):
 spec=importlib.util.spec_from_file_location(name,P/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=json.loads(body(P/'MANIFEST01.json'));check(sha((P/'MANIFEST01.json').read_bytes())=='238949db2c9f635a0de7e521a1874b1f5b70e1b110a781716d343cc8d368ddd3','exact frozen manifest')
check({p.name for p in P.iterdir()}=={'MANIFEST01.json'}|{x['path'] for x in m['members']},'complete no extras')
for row in m['members']:
 raw=body(P/row['path']);check(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'manifest '+row['path'])
b=load('capsule_builder01');g=load('generate_inputs01');pkg=types.ModuleType('fixture_tools');pkg.capsule_builder01=b;sys.modules['fixture_tools']=pkg
q=json.loads((P/'ROOT_TEMPLATE01.json').read_bytes());mode=q['closure_mode'];rows=q['rows'];orig=json.loads((P/'SOURCE_INVENTORY01.json').read_bytes())
source,package=b.full_rows(rows,mode)
check(len(source)==202 and len(package)==151,'exact full closure')
reg=json.loads((C/'held-fixture-registration01.json').read_bytes());pins=reg['experiments']['original-import-held-success-20261003-01']['source_files'];initial=json.loads((P/'ORIGIN_ROWS_INITIAL01.json').read_bytes());base={n:h for n,h in pins.items() if n not in initial['baseline_auxiliary_paths']}
check(len(base)==199,'actual199 baseline')
for row in orig['entries']:
 raw=body(Path(row['origin']));check(sha(raw)==row['sha256']==source[row['target']] and len(raw)==row['bytes'],'origin '+row['target'])
check(set(source)-set(base)=={'tradingagents/research/onchain_replication/'+n+'.py' for n in ('archive_non_tail','selected_non_tail_transport','completed_f32')},'exact three new package paths')
reader=b.Reader(C)
base_rows=[]
for name,h in sorted(base.items()):
 raw=reader.body(name);check(sha(raw)==h,'genuine baseline body '+name);base_rows.append({'path':name,'sha256':h,'bytes':len(raw)})
b.full_git_bodies(reader,'d443208795f59292c156c5b81b687594efacea4d',base_rows);reader.recheck();check(True,'genuine current199 Git joins')
for name,target in [('capsule_builder01','fixture_tools/capsule_builder01.py'),('generate_inputs01','fixture_tools/generate_inputs01.py'),('build_release_draft01','proof_tools/build_release_draft01.py')]:
 old=(P/(name+'.py.baseline.txt')).read_bytes();new=(P/(name+'.py')).read_bytes();check(new.startswith(old) and old==(C/target).read_bytes(),'full original prefix and actual origin '+name)
 check(mode['helper_source_files'][target]==sha(new),'external helper final hash '+name)
 check(sha(new).encode() not in new,'no direct selfhash '+name)
# Independently inverse every cloned generator metadata function, exact AST.
names={'render_held_auxiliary_declaration','held_auxiliary_metadata','held_input_plan'}
class Undo(ast.NodeTransformer):
 def visit_FunctionDef(self,n):
  if n.name in {'full_'+s for s in names}:n.name=n.name[5:]
  return self.generic_visit(n)
 def visit_Name(self,n):
  if n.id in {'full_'+s for s in names}:n.id=n.id[5:]
  return n
 def visit_Constant(self,n):
  if type(n.value)==int:n.value={202:199,151:148,207:204}.get(n.value,n.value)
  if type(n.value)==str:
   n.value=n.value.replace('202','199').replace('151','148').replace('207','204')
  return n
old=ast.parse((P/'generate_inputs01.py.baseline.txt').read_text());new=ast.parse((P/'generate_inputs01.py').read_text());defs={x.name:x for x in new.body if isinstance(x,ast.FunctionDef)}
for n in old.body:
 if isinstance(n,ast.FunctionDef) and n.name in names:check(ast.dump(n)==ast.dump(Undo().visit(copy.deepcopy(defs['full_'+n.name]))),'count-name-only full inverse '+n.name)
refusals=[]
def refuse(label,fn):
 try:fn()
 except (ValueError,TypeError,KeyError) as e:refusals.append({'case':label,'type':type(e).__name__,'message':str(e)})
 else:raise AssertionError('ACCEPTED '+label)
for v in [None,{},True,dict(mode,schema_version=True),dict(mode,kind='future'),dict(mode,unknown=1),dict(mode,helper_source_files={}),dict(mode,helper_source_files=dict(mode['helper_source_files'],unknown='a'*64))]:refuse('unsupported mode '+repr(v)[:90],lambda v=v:b.full_mode(v))
for what in ('extra','missing','reverse','extent0','extentbool','hash','duplicate','extra_field'):
 r=copy.deepcopy(rows)
 if what=='extra':r.append(dict(r[-1],path='unknown.py'))
 if what=='missing':r.pop()
 if what=='reverse':r.reverse()
 if what=='extent0':r[0]['bytes']=0
 if what=='extentbool':r[0]['bytes']=True
 if what=='hash':r[0]['sha256']='0'*64
 if what=='duplicate':r[-1]=r[0]
 if what=='extra_field':r[0]['approval']=True
 refuse(what,lambda r=r:b.full_rows(r,mode))
refuse('actual199 current is no future151 installed origin',lambda:b.held_source_plan(C,'d443208795f59292c156c5b81b687594efacea4d','0cfc2c03200880534b7c91c2f16ac659a265a35b',rows,closure_mode=mode,design_source='d443208795f59292c156c5b81b687594efacea4d'))
p={'kind':'full202-resource-source-metadata-v1','closure_mode':mode,'source_count':202,'package_count':151,'source_files':source,'package_files':package,'source':None,'anchor':None,'root':None,'execution_admitted':False}
out=g.held_input_plan({},p,closure_mode=mode);check(out['remaining_roles']==list(g.HELD_ROLES) and not out['execution_admitted'],'no missing authority promoted')
refuse('None mode retains199',lambda:g.held_input_plan({},p))
for key in ('source_files','package_files','closure_mode'):
 v=copy.deepcopy(p);v[key]={};refuse('selected strict '+key,lambda v=v:g.held_input_plan({},v,closure_mode=mode))
# Existing legacy defaults are actual-source metadata, not invented authority.
legacy={'source_count':199,'package_count':148,'source_files':base,'package_files':{n:h for n,h in base.items() if b.full_package(n)},'source':initial['baseline_source'],'anchor':None,'root':str(C),'execution_admitted':False}
check(g.held_input_plan({},legacy)==g._legacy_held_input_plan({},legacy),'legacy wrapper same result')
check(not any(k.split('.')[0] in {'numpy','torch','scipy'} for k in sys.modules),'no numerical imports')
(O/'MEMBERS_READ01.json').write_text(json.dumps(inventory,indent=2)+'\n')
(O/'REFUSALS01.json').write_text(json.dumps(refusals,indent=2)+'\n')
(O/'RESULT01.json').write_text(json.dumps({'checks':checks,'refusal_count':len(refusals),'source_count':202,'package_count':151,'admission_count':207,'execution_admitted':False},indent=2)+'\n')
print('PASS',len(checks),'checks;',len(refusals),'refusals; source-only, no future anchor or admission')

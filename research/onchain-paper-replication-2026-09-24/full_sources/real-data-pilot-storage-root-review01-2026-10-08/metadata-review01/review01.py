import ast,hashlib,json,re
from pathlib import Path
from types import SimpleNamespace as N
H=Path(__file__).resolve().parent;F=H.parent.parent;C=F/'real-data-pilot-storage-metadata-binding01-2026-10-08';R=F.parents[2]
checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def need(x,m):
 if not x:raise ValueError(m)
def refuse(n,f):
 try:f()
 except ValueError:checks.append(n);return
 raise AssertionError(n)
def ex(nodes,ns):exec(compile(ast.fix_missing_locations(ast.Module(nodes,type_ignores=[])),'isolated_metadata','exec'),ns)
man=C/'MANIFEST.json';ck('manifest_pin',hashlib.sha256(man.read_bytes()).hexdigest()=='649dbd868cb832f551862896acf3f88f437a71d71fc3b2d521ffc11e9159bf43')
m=json.loads(man.read_text())
for name,pin in m['files'].items():ck('file_'+name,hashlib.sha256((C/name).read_bytes()).hexdigest()==pin)
D=json.loads((C/'DEPENDENCIES04.json').read_text());oldD=json.loads((F/'real-data-pilot-fixed21-metadata-successor01-2026-10-08/DEPENDENCIES04.json').read_text())
ck('only_three_dependency_changes',{k for k in D if D[k]!=oldD[k]}=={'builder','controls','handoff'})
for n,v in D.items():ck('dependency_'+n,hashlib.sha256((R/v['path']).read_bytes()).hexdigest()==v['sha256'])
accepted=ast.parse((F/'real-data-pilot-storage-identity01-2026-10-08/real_pilot_storage.py').read_text());validator=next(n for n in accepted.body if isinstance(n,ast.FunctionDef) and n.name=='experiment_name')
old='eth-paper-real-data-end-to-end-resource-20261008-21';new='eth-paper-real-data-end-to-end-resource-20261009-22'
for name,fun in [('controls02.py','calculate'),('build_inputs04.py','build'),('prepare_builder04.py','prepare'),('successor04.py','prepare')]:
 p=C/name if name=='successor04.py' else C/'candidate'/name
 text=p.read_text();original=(C/('baseline_'+name)).read_text();tree=ast.parse(text)
 helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='experiment_name');ck('same_grammar_'+name,ast.dump(helper)==ast.dump(validator))
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==fun)
 ns={'re':re};ex([helper],ns)
 validation=next(n for n in fn.body if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='experiment')
 for value in [old,new]:ns['experiment']=value;ex([validation],ns);ck('valid_'+name+value,ns['experiment']==value)
 for value in [None,False,22,'../x',new+'/x',new+'\n',new.replace('-22','-022')]:
  ns['experiment']=value;refuse('invalid_'+name+repr(value),lambda:ex([validation],ns))
 # Full byte inverse, only explicitly identified changed seams.
 lines=text.splitlines(True);del lines[helper.lineno-1:helper.end_lineno+1];inverse=''.join(lines).replace('import re\n','',1).replace('    experiment=experiment_name(experiment)\n','',1)
 if name=='controls02.py':inverse=inverse.replace('def calculate(s,*,experiment=EXPERIMENT):','def calculate(s):',1).replace("budget['experiment']==experiment","budget['experiment']==EXPERIMENT").replace("root+'/research_runs/'+experiment","root+'/research_runs/'+EXPERIMENT")
 elif name=='build_inputs04.py':inverse=inverse.replace(f'def build(root,spec,*,experiment={old!r}):','def build(root,spec):',1).replace("budget=resource['storage_budget'];limits=budget['limits']","budget=resource['storage_budget'];limits=budget['limits'];experiment="+repr(old),1)
 else:
  inverse=inverse.replace(f'def prepare(root,draft,*,experiment={old!r}):','def prepare(root,draft):',1)
  for call in ['c.calculate(inventory','b.build(root,spec','m.prepare(root,draft']:inverse=inverse.replace(call+',experiment=experiment)',call+')',1)
  if name=='prepare_builder04.py':
   a=inverse.index('PINS=');z=inverse.index('\n\ndef need',a);aa=original.index('PINS=');zz=original.index('\n\ndef need',aa);inverse=inverse[:a]+original[aa:zz]+inverse[z:]
 ck('full_inverse_'+name,inverse==original)
 if name=='prepare_builder04.py':
  pins=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='PINS'))
  for role,(rel,pin) in pins.items():ck('handoff_pin_'+role,hashlib.sha256((p.parent.parent/rel).read_bytes()).hexdigest()==pin)
 for target in (['c.calculate','b.build'] if name=='prepare_builder04.py' else ['m.prepare'] if name=='successor04.py' else []):
  call=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and ast.unparse(n.func)==target);seen=[]
  capture=lambda *a,**k:seen.append(k)
  ex([ast.Expr(call)],dict(c=N(calculate=capture),b=N(build=capture),m=N(prepare=capture),inventory={},root=Path('/toy'),spec={},draft={},experiment=new))
  ck('forward_'+target,seen==[{'experiment':new}])
 if name in ('controls02.py','build_inputs04.py'):
  join=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need' and any(isinstance(a,ast.Constant) and a.value in ('exact original/shared writable scope required','exact common writable union required') for a in n.args))
  budget={'schema_version':2,'kind':'real-pilot-writable-union','authority_root':'/toy','experiment':new,'roots':['/toy/research_artifacts','/toy/research_runs/'+new],'shared_files':['/toy/research_runs/.lock']}
  ns=dict(need=need,budget=budget,root='/toy' if name=='controls02.py' else Path('/toy'),experiment=new)
  ex([ast.Expr(join)],ns);checks.append('valid_budget_'+name)
  for field,value in [('experiment',old),('roots',['/wrong']),('shared_files',['/wrong'])]:
   ns['budget']={**budget,field:value};refuse('mismatch_'+name+field,lambda:ex([ast.Expr(join)],ns))
result={'decision':'accepted-source-only-not-whole-pipeline','manifest_sha256':hashlib.sha256(man.read_bytes()).hexdigest(),'source_hashes':{k:v for k,v in m['files'].items() if k in ('successor04.py','candidate/controls02.py','candidate/build_inputs04.py','candidate/prepare_builder04.py','DEPENDENCIES04.json')},'checks':checks,'limitations':['Exact full inverses preserve original numeric/reservation/schema logic; no repeated capacity matrices.','Actual validator/prefix/join/call AST tested on metadata doubles. No genuine seven-graph handoff, empirical input, scientific import, Admission/Owner/job/claim or integration executed.','Dependencies rebind only builder/controls/handoff; all exact local pins verified.','Worker failed512-byte toy tail fixture remains preserved; corrected560 fixture was not treated as scientific validation.','Legacy default21 retained; fresh metadata outputs and entry release remain pending.']}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))

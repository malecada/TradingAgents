import ast,copy,difflib,hashlib,json,os,resource,signal,traceback,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-two-attribute-qualification02-2026-10-11';C=F/'matching-compiled-two-attribute-agreement01-2026-10-11';refs={};checks=[]
def read(p):
 assert p.suffix!='.so';b=p.read_bytes();refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):checks.append({'name':n,'pass':bool(v)});assert v,n
m=json.loads(read(D/'MANIFEST02.json'));ck(refs[str((D/'MANIFEST02.json').relative_to(R))]['sha256']=='d712c03de3815c63419bde120d2492828280feb358a532b1d41d493779b37a3b','exact successor manifest')
for name,row in m['files'].items():read(D/name);ck(refs[str((D/name).relative_to(R))]==row,'frozen member '+name)
new=read(D/'fixture02.py');old=read(C/'fixture01.py');tree=ast.parse(new)
for a,b,suffix,first,last in [(old,new,'FORWARD.patch','fixture01.py','fixture02.py'),(new,old,'INVERSE.patch','fixture02.py','fixture01.py')]:
 ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=first,tofile=last))==read(D/suffix),'exact '+suffix)
start='    filler=make_filler(native,np,agreement)';end="    checks.append({'function_and_global_mutation_refused':True})"
ck(new[new.index(start):new.index(end)+len(end)]==old[old.index(start):old.index(end)+len(end)],'unchanged numerical cases and criteria')
literal=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REFERENCES' for t in n.targets));reference=ast.literal_eval(literal.value);candidate=json.loads(read(C/'MANIFEST01.json'))
ck(all(row==candidate['files'][name] for name,row in reference.items() if name!='MANIFEST01.json'),'references match immutable candidate manifest; binary not read')
ck(new.index('ATTEMPT=reserve_attempt')<new.index('os.dup2')<new.index('spec.loader.exec_module')<new.index('import numpy'),'reservation and raw descriptor setup precede load')
ns={'json':json};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('reserve_attempt','write_result')];exec(compile(ast.Module(body=nodes,type_ignores=[]),'reservation-only','exec'),ns)
synthetic=P/'synthetic-spent01';ns['reserve_attempt'](synthetic);ns['write_result'](synthetic,{'status':'FAILED_SYNTHETIC'})
before=(synthetic/'NUMERIC_RESULT01.json').read_bytes()
for name,call in [('reserve',lambda:ns['reserve_attempt'](synthetic)),('result',lambda:ns['write_result'](synthetic,{'status':'PASS'}))]:
 try:call()
 except FileExistsError:ck(True,'repeated '+name+' refused')
 else:ck(False,'repeat must refuse')
ck((synthetic/'NUMERIC_RESULT01.json').read_bytes()==before,'spent synthetic failure retained')
# Actual new except/finally AST; replace numerical try body with one synthetic failure.
outer=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.Try)));outer.body=[ast.Raise(exc=ast.Name(id='original_error',ctx=ast.Load()),cause=None)]
original=ValueError('synthetic numerical failure');reporting=OSError('synthetic traceback storage failure');record=[]
class BrokenAttempt:
 def __truediv__(self,name):return self
 def open(self,*args,**kwargs):raise reporting
env={'original_error':original,'ATTEMPT':BrokenAttempt(),'traceback':traceback,'failure':None,'checks':[],'start':0,'time':types.SimpleNamespace(monotonic=lambda:0),'write_result':lambda path,value:record.append(value)}
try:exec(compile(ast.fix_missing_locations(ast.Module(body=[outer],type_ignores=[])),'actual-exception-reporting-seam','exec'),env)
except BaseException as error:
 ck(error is reporting,'reporting failure replaces primary raised error')
 ck(error.__context__ is original,'original error survives only as exception context')
else:ck(False,'expected reporting error')
ck(record[0]['status']=='PASS_FINITE_SYNTHETIC' and record[0]['failure'] is None,'confirmed false PASS result after original failure and traceback storage failure')
out={'decision':'REFUSED_FAILURE_REPORTING_REPAIR_REQUIRED','checks':checks,'references':refs,'counterexample':{'original_error':type(original).__name__,'escaping_error':type(reporting).__name__,'written_result':record[0]},'native_science_fixture_executed':False}
with (P/'RESULT01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks)}))

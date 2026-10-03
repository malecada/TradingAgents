"""Independent stdlib source and opaque extracted-loop controls. No authority."""
import ast,copy,hashlib,itertools,json,pathlib,stat,subprocess
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
PREP=BASE/'held-consumer-canonical-successor-preparation01-2026-10-03'
OUT=pathlib.Path(__file__).resolve().parent
CAP=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
checks=[];evidence={};H=lambda b:hashlib.sha256(b).hexdigest()
def raw(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2 and p.resolve()==p
 b=p.read_bytes();assert len(b)==s.st_size;return b
def check(name,yes):assert yes,name;checks.append(name)
def dump(name,v):
 with (OUT/name).open('x') as f:json.dump(v,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
check('frozen subject manifest',H(raw(PREP/'MANIFEST01.json'))=='5a66675c7ee9c48181ad899ce1be84f41456afff9fb574d9bc0a0af159155546')
for row in json.loads(raw(PREP/'MANIFEST01.json'))['members']:
 p=PREP/row['path'];b=raw(p);check('subject body '+row['path'],len(b)==row['bytes'] and H(b)==row['sha256'] and stat.S_IMODE(p.stat().st_mode)==row['mode'])
for row in json.loads(raw(PREP/'ORIGINS01.json'))['references']:
 b=raw(pathlib.Path(row['path']));check('origin '+row['path'],H(b)==row['sha256'] and len(b)==row['bytes'])
old=raw(PREP/'baseline.py');new=raw(PREP/'original_dictionary.py')
target='tradingagents/research/onchain_replication/original_dictionary.py'
check('actual held baseline bytes',old==raw(CAP/target))
r=subprocess.run(['git','--no-optional-locks','-C',str(CAP),'ls-tree','-z','d443208795f59292c156c5b81b687594efacea4d','--',target],capture_output=True,check=True,timeout=10)
check('actual held committed blob',not r.stderr and len(r.stdout)<1024 and r.stdout.split(b'\t')[0].split()[-1].decode()==hashlib.sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest())
evidence['held_selected_ls_tree']=r.stdout.decode().rstrip('\0')
prior=BASE/'original-dictionary-canonical-validation-candidate01-2026-10-03'
check('exact prior93c candidate',new==raw(prior/'candidate01.py') and H(new)=='93c0cd1ae882d51df185458ce7304a46dfb66dc7ca337285039541fa70176e88')
orig=json.loads(raw(prior/'origins01.json'))
for row in orig['references']:
 b=raw(ROOT/row['path']);check('prior provenance '+row['path'],len(b)==row['bytes'] and H(b)==row['sha256'])
def parts(b):
 tree=ast.parse(b);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
 lo=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='indices' for t in n.targets))
 hi=next(i for i,n in enumerate(fn.body) if i>lo and isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='repeated representative' for a in n.value.args))
 return tree,fn,lo,hi
ot,of,ol,oh=parts(old);nt,nf,nl,nh=parts(new)
rest=copy.deepcopy(nt);rf=next(n for n in rest.body if isinstance(n,ast.FunctionDef) and n.name=='validate');rf.body[nl:nh+1]=copy.deepcopy(of.body[ol:oh+1])
check('full other AST inverse',ast.dump(rest,include_attributes=False)==ast.dump(ot,include_attributes=False))
lines=new.decode().splitlines(keepends=True);oldlines=old.decode().splitlines(keepends=True);lines[nf.body[nl].lineno-1:nf.body[nh].end_lineno]=oldlines[of.body[ol].lineno-1:of.body[oh].end_lineno]
check('complete byte inverse',''.join(lines).encode()==old)
env={'json':json};small=[n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name in ('canonical','require')]
exec(compile(ast.Module(body=small,type_ignores=[]),'<actual-pure-definitions>','exec'),env)
canonical=env['canonical'];require=env['require']
codes=[compile(ast.Module(body=copy.deepcopy(f.body[l:h+1]),type_ignores=[]),'<exact-loop>','exec') for f,l,h in [(of,ol,oh),(nf,nl,nh)]]
def execute(which,samples,reps,groups,serializer=canonical):
 e={'s':{'graphs':samples},'reps':reps,'groups':groups,'canonical':serializer,'require':require}
 try:exec(codes[which],e);return {'status':'return','indices':e['indices']}
 except BaseException as error:return {'status':'error','type':type(error).__name__,'message':str(error),'error':error}
def result(r):return {k:v for k,v in r.items() if k!='error'}
# Opaque dictionaries only. Exhaustive small token multiplicities, reps and groups.
cases=0
for size in range(1,4):
 for tokens in itertools.product(range(2),repeat=size):
  samples=[{'opaque':x} for x in tokens]
  for count in range(1,3):
   for rt in itertools.product(range(3),repeat=count):
    reps=[{'opaque':x} for x in rt]
    for omit in (False,True):
     groups=[list(range(size-(1 if omit else 0))) for _ in reps]
     a=execute(0,samples,reps,groups);b=execute(1,samples,reps,groups)
     check('opaque multiplicity/refusal case '+str(cases),result(a)==result(b));cases+=1
samples=[{'opaque':str(i),'unicode':'節😀'} for i in range(512)];ids=list(range(511,479,-1));reps=[copy.deepcopy(samples[i]) for i in ids];groups=[[i] for i in ids];groups[0]+=list(range(480));counts=[];traces=[]
for which in (0,1):
 counter={'serialization':0,'comparison':0};trace=[]
 class Traced(bytes):
  def __eq__(self,other):counter['comparison']+=1;trace.append((bytes(self).decode(),bytes(other).decode()));return bytes.__eq__(self,other)
 def observe(x):counter['serialization']+=1;return Traced(canonical(x))
 r=execute(which,samples,reps,groups,observe);check('512/32 exact indices '+str(which),r=={'status':'return','indices':ids});counts.append(counter);traces.append(trace)
check('full ordered comparison trace',traces[0]==traces[1] and len(traces[0])==16384)
check('exact serialization counts',counts==[{'serialization':32768,'comparison':16384},{'serialization':544,'comparison':16384}]);evidence['operation_counts']=counts
evidence['comparison_trace_sha256']=H(json.dumps(traces[0],ensure_ascii=False,separators=(',',':')).encode())
# Exact first-use exceptions may remove redundant prior trace entries, never change selected exception.
first=[]
for kind in (ValueError,MemoryError,SystemExit,KeyboardInterrupt):
 for role in ('s0','s1','s2','r0','r1','r2'):
  for which in (0,1):
   gs=[{'token':str(i)} for i in range(3)];rs=copy.deepcopy(gs);names={id(x):'s'+str(i) for i,x in enumerate(gs)}|{id(x):'r'+str(i) for i,x in enumerate(rs)};error=kind('first-use');trace=[]
   def observe(x):
    label=names[id(x)];trace.append(label)
    if label==role:raise error
    return canonical(x)
   r=execute(which,gs,rs,[[0],[1],[2]],observe);check('first-use identity '+kind.__name__+role+str(which),r.get('error') is error)
   first.append({'exception':kind.__name__,'role':role,'implementation':which,'trace':trace,'same_object':r.get('error') is error})
evidence['first_use_witnesses']=first
# Outside equivalence domain: deliberate failure on removed redundant serializer call.
limitations=[]
for kind in (MemoryError,SystemExit):
 rows=[]
 for which in (0,1):
  s=[{'token':'0'},{'token':'1'}];rep={'token':'0'};calls=0;failure=kind('second representative serialization')
  def stateful(x):
   global calls
   if x is rep:
    calls+=1
    if calls==2:raise failure
   return canonical(x)
  r=execute(which,s,[rep],[[0,1]],stateful);rows.append({'implementation':which,'disposition':result(r),'same_error':r.get('error') is failure,'representative_calls':calls})
 check('removed redundant call qualification '+kind.__name__,rows[0]['same_error'] and rows[1]['disposition']['status']=='return');limitations.append({'kind':'removed_redundant_call_not_exception_equivalent','exception':kind.__name__,'rows':rows})
# Inherited diagnostic reducer only: no ImportedOriginal/Run/Owner/Binding constructed.
owner_tree=ast.parse(raw(CAP/'tradingagents/research/onchain_replication/owned_io.py'))
fataldefs=[n for n in owner_tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('CleanupFailure','_fatal')];fenv={};exec(compile(ast.Module(body=fataldefs,type_ignores=[]),'<actual-fatal-predicate>','exec'),fenv)
cls=next(n for n in nt.body if isinstance(n,ast.ClassDef) and n.name=='ImportedOriginal');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='with_evidence')
node=next(n for n in ast.walk(method) if isinstance(n,ast.If) and ast.unparse(n.test)=='primary is None')
class NoteFatal(MemoryError):
 def add_note(self,note):raise RuntimeError('diagnostic attachment failed')
primary=NoteFatal('original callback fatal');later=ValueError('later recheck');env2={'primary':primary,'error':later,'fatal':fenv['_fatal']}
try:exec(compile(ast.Module(body=[copy.deepcopy(node)],type_ignores=[]),'<unchanged-exact-callback-reducer>','exec'),env2)
except BaseException as escaped:
 check('inherited diagnostic limitation witnessed',type(escaped)is RuntimeError and escaped is not primary)
 limitations.append({'kind':'unchanged_with_evidence_add_note_can_replace_first_fatal','source_line':node.lineno,'primary_type':'MemoryError subclass with failing add_note','secondary_type':'ValueError','escaped_type':type(escaped).__name__,'introduced_by_successor':False,'authority_objects_constructed':False})
else:raise AssertionError('diagnostic witness absent')
dump('LIMITATIONS01.json',limitations)
# Re-run author's exact47check body after only replacing its output directory constant.
author=ast.parse(raw(PREP/'check01.py'));author_env={'__file__':str(PREP/'check01.py')}
author.body=[n for n in author.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='write_text')]
exec(compile(author,'<author-check-body-no-source-write>','exec'),author_env)
check('author47 controls',author_env['report']['count']==47);dump('AUTHOR_RESULTS01.json',author_env['report'])
for row in json.loads(raw(PREP/'MANIFEST01.json'))['members']:check('final subject unchanged '+row['path'],H(raw(PREP/row['path']))==row['sha256'])
evidence.update(checks=checks,assertion_count=len(checks),opaque_enumerated_cases=cases,numerical_imports=False,authority_constructed=False,original_samples_read=False,source_only=True)
dump('RESULTS01.json',evidence)
print(json.dumps({'independent_assertions':len(checks),'opaque_cases':cases,'author_checks':47,'limitation_witnesses':len(limitations)}))

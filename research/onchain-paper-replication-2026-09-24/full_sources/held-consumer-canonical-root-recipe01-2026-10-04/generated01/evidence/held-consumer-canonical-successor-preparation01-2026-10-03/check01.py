"""Exact extracted membership slice, synthetic opaque JSON only; no imports of source."""
import ast,copy,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
checks=[]
def require(v,m):
 if not v:raise ValueError(m)
def check(n,v):
 assert v,n;checks.append(n)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def slice_module(path):
 tree=ast.parse(path.read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate')
 a=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='indices')
 z=next(i for i,n in enumerate(f.body) if i>a and isinstance(n,ast.Expr) and 'repeated representative' in ast.unparse(n))
 return tree,f,a,z
old,fo,a,z=slice_module(H/'baseline.py');new,fn,b,w=slice_module(H/'original_dictionary.py')
restored=copy.deepcopy(new);f=next(n for n in restored.body if isinstance(n,ast.FunctionDef) and n.name=='validate');f.body[b:w+1]=copy.deepcopy(fo.body[a:z+1])
check('whole other AST identical',ast.dump(old)==ast.dump(restored))
oldbytes=(H/'baseline.py').read_bytes();newbytes=(H/'original_dictionary.py').read_bytes()
check('exact cbe baseline',hashlib.sha256(oldbytes).hexdigest()=='cbe571a3758695b2ff63a45031c90840a7358538f9a2c0bad31077db8439a6d9')
check('exact previously reviewed93c body',hashlib.sha256(newbytes).hexdigest()=='93c0cd1ae882d51df185458ce7304a46dfb66dc7ca337285039541fa70176e88')
oldtext=oldbytes.decode();newtext=newbytes.decode();oldlines=oldtext.splitlines(keepends=True);newlines=newtext.splitlines(keepends=True)
start=fn.body[b].lineno-1;end=fn.body[w].end_lineno
newlines[start:end]=oldlines[fo.body[a].lineno-1:fo.body[z].end_lineno]
check('complete byte inverse of membership slice',''.join(newlines)==oldtext)

def run(fn,a,z,graphs,reps,groups,serializer=canonical):
 env={'s':{'graphs':graphs},'reps':reps,'groups':groups,'canonical':serializer,'require':require}
 fragment=ast.Module(body=copy.deepcopy(fn.body[a:z+1]),type_ignores=[])
 exec(compile(ast.fix_missing_locations(fragment),'<exact-membership-slice>','exec'),env)
 return env['indices']
def outcome(fn,a,z,graphs,reps,groups,serializer=canonical):
 try:return ('return',run(fn,a,z,graphs,reps,groups,serializer))
 except ValueError as e:return ('refused',str(e))

graphs=[{'opaque':str(i)} for i in range(512)]
indices=list(range(511,479,-1));reps=[copy.deepcopy(graphs[i]) for i in indices];groups=[[i] for i in indices];groups[0]+=list(range(480))
counts=[]
for label,fn,lo,hi in [('old',fo,a,z),('new',fn,b,w)]:
 counter={'serializations':0,'comparisons':0}
 class Counted(bytes):
  def __eq__(self,other):counter['comparisons']+=1;return bytes.__eq__(self,other)
 def observed(x):counter['serializations']+=1;return Counted(canonical(x))
 check(label+' ordered indices',run(fn,lo,hi,graphs,reps,groups,observed)==indices)
 counts.append(counter)
check('old32768 serializations',counts[0]['serializations']==32768)
check('new544 serializations',counts[1]['serializations']==544)
check('both16384 ordered comparisons',counts[0]['comparisons']==counts[1]['comparisons']==16384)
# Reacquire fn after the explicit counter loop above.
_,fn,b,w=slice_module(H/'original_dictionary.py')
for label,gs,rs,gp in [
 ('duplicate sample',[{'x':1},{'x':1}],[{'x':1}],[[0,1]]),
 ('nonmember',[{'x':1},{'x':2}],[{'x':3}],[[0,1]]),
 ('wrong group',[{'x':1},{'x':2}],[{'x':2}],[[0]]),
 ('repeated representative',[{'x':1},{'x':2}],[{'x':1},{'x':1}],[[0],[0,1]]),
 ('unicode/signedzero',[{'x':'節😀','y':-0.0},{'x':'é','y':2.0}],[{'x':'é','y':2.0}],[[0,1]]),
 ('integer float inequivalence',[{'x':1},{'x':1.0}],[{'x':1.0}],[[0,1]]),
 ('first sample malformed',[{'x':float('nan')},{'x':1}],[{'x':float('nan')}],[[0,1]]),
 ('first representative malformed',[{'x':1},{'x':float('nan')}],[{'x':float('nan')}],[[0,1]]),
 ('later representative not visited',[{'x':1}],[{'x':2},{'x':float('nan')}],[[0],[]]),
]:
 check(label+' equal disposition/order',outcome(fo,a,z,gs,rs,gp)==outcome(fn,b,w,gs,rs,gp))
# First-use ordering and actual exception object identity, without authority stubs.
for exc_type in (ValueError,MemoryError,SystemExit):
 for fail_role in ('sample0','representative0','sample1'):
  traces=[]
  for func,lo,hi in ((fo,a,z),(fn,b,w)):
   gs=[{'role':'sample0'},{'role':'sample1'}];rs=[{'role':'representative0'}];gp=[[0,1]];trace=[];error=exc_type('synthetic first-use failure')
   def observe(x):
    trace.append(x['role'])
    if x['role']==fail_role:raise error
    return canonical(x)
   try:run(func,lo,hi,gs,rs,gp,observe)
   except BaseException as actual:check(exc_type.__name__+' '+fail_role+' identity '+str(lo),actual is error)
   else:raise AssertionError('failure lost')
   traces.append(trace)
  check(exc_type.__name__+' '+fail_role+' first-use prefix',traces[0]==traces[1])
# No module/global cache: changed data is reserialized on a new invocation.
check('fresh invocation original',run(fn,b,w,[{'x':1}],[{'x':1}],[[0]])==[0])
check('fresh changed invocation refusal',outcome(fn,b,w,[{'x':2}],[{'x':1}],[[0]])[0]=='refused')
report={'checks':checks,'count':len(checks),'counts':counts,'per_matcher_eight_validations':{'before_serializations':32768*8,'after_serializations':544*8,'comparisons_unchanged':16384*8},'actual_scientific_inputs_read':False,'numerical_imports':False,'authority_objects':False,'wall_share_or_RAM_saving_claim':False}
(H/'CHECKS01.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps({'passed':len(checks),'counts':counts}))

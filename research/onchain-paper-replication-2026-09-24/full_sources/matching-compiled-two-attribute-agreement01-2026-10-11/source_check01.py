import ast,hashlib,json,os,resource,signal,difflib
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(9,9));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(10)
p=Path(__file__).resolve().parent;f=p.parent
checks=[]
for name in ('edge_chunk_adapter.py','build01.py','fixture01.py','source_check01.py'):
 ast.parse((p/name).read_text());checks.append('syntax '+name)
c=(p/'edge_chunk.c').read_text();a=(p/'edge_chunk_adapter.py').read_text()
ops=['fx=PyNumber_Float(x)','fy=PyNumber_Float(y)','delta=PyNumber_Subtract(fx,fy)','square=PyNumber_Power(delta,two,Py_None)','total=PyObject_CallOneArg(sum,terms)','negative=PyNumber_Negative(total)','scaled=PyNumber_TrueDivide(negative,two)','out=PyObject_CallOneArg(exp,scaled)']
assert [c.index(x) for x in ops]==sorted(c.index(x) for x in ops);checks.append('exact primitive order')
assert 'Py_BEGIN_ALLOW_THREADS' not in c and 'pow(' not in c and 'exp(' not in c;checks.append('no GIL release or native approximation')
assert c.index('PyList_SetItem(progress')<c.index('li=PyObject_GetItem')<c.index('value=two_agreement');checks.append('prefix marker precedes row and arithmetic')
assert 'else value=PyObject_CallFunctionObjArgs(agreement,av,bv,NULL)' in c;checks.append('row refusal retains original callback')
assert all(t in a for t in ('agreement.__code__ is not code','math_module.fsum is not fsum','math_module.exp is not exp','globals_.get(name,value) is not value','x.shape[1]!=2','not x.flags.c_contiguous','x.flags.writeable'));checks.append('code global math and readonly shape guards')
assert 'frombuffer' in (p/'fixture01.py').read_text() and 'is True' in (p/'fixture01.py').read_text();checks.append('queued fixture eligible immutable native success assertion')
for name,old in [('edge_chunk.c',f/'matching-compiled-uncached-edge-chunk01-2026-10-11/edge_chunk.c'),('edge_chunk_adapter.py',f/'matching-compiled-uncached-edge-caller-candidate03-2026-10-11/edge_chunk_adapter.py')]:
 before=old.read_text();after=(p/name).read_text()
 for x,y,suffix in ((before,after,'.patch'),(after,before,'.inverse.patch')):
  (p/(name+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=name,tofile=name)))
 checks.append('literal inverse '+name)
build=json.loads((p/'BUILD01.json').read_text());assert build['returncode']==0 and build['native_loaded'] is False;checks.append('actual compile only exit0')
(p/'SOURCE_RESULT01.json').write_text(json.dumps({'status':'PASS_SOURCE_AND_COMPILE_ONLY','checks':checks,'native_loaded':False,'numeric_fixture_executed':False},indent=2)+'\n');print(len(checks),'checks')

import ast,difflib,hashlib,json,os,resource,signal
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(15)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'matching-compiled-two-attribute-agreement01-2026-10-11';refs={};checks=[]
def read(p):
 assert p.suffix!='.so';body=p.read_bytes();assert len(body)<2*1024**2;refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body)};return body.decode()
def ck(value,name):checks.append({'name':name,'pass':bool(value)});assert value,name
manifest=json.loads(read(D/'MANIFEST01.json'));ck(refs[str((D/'MANIFEST01.json').relative_to(R))]['sha256']=='445cb2fb0d266a5c17243ad1d1fc9f29cc8a8b5e3fbe1b8472cc98513aa58152','exact candidate manifest')
for name,row in manifest['files'].items():
 if name.endswith('.so'):continue
 read(D/name);ck(refs[str((D/name).relative_to(R))]==row,'textual evidence '+name)
for name,old in [('edge_chunk.c',F/'matching-compiled-uncached-edge-chunk01-2026-10-11/edge_chunk.c'),('edge_chunk_adapter.py',F/'matching-compiled-uncached-edge-caller-candidate03-2026-10-11/edge_chunk_adapter.py')]:
 before=read(old);after=read(D/name)
 for a,b,suffix in [(before,after,'.patch'),(after,before,'.inverse.patch')]:ck(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=name,tofile=name))==read(D/(name+suffix)),'exact changed inverse '+name+suffix)
original=read(R/'tradingagents/research/onchain_replication/matching_reference.py');node=next(n for n in ast.parse(original).body if isinstance(n,ast.FunctionDef) and n.name=='agreement');agreement=ast.get_source_segment(original,node)
ck('math.exp(-math.fsum((float(x)-float(y))**2 for x,y in zip(a,b,strict=True))/len(a))' in agreement,'retained exact original expression')
c=read(D/'edge_chunk.c');adapter=read(D/'edge_chunk_adapter.py');ast.parse(adapter)
ops=['x=PyObject_GetItem(a,index)','y=PyObject_GetItem(b,index)','fx=PyNumber_Float(x)','fy=PyNumber_Float(y)','delta=PyNumber_Subtract(fx,fy)','square=PyNumber_Power(delta,two,Py_None)','total=PyObject_CallOneArg(sum,terms)','negative=PyNumber_Negative(total)','scaled=PyNumber_TrueDivide(negative,two)','out=PyObject_CallOneArg(exp,scaled)']
ck([c.index(op) for op in ops]==sorted(c.index(op) for op in ops),'scalar reads conversions and Python numeric operator order')
ck(c.index('PyList_SetItem(progress')<c.index('li=PyObject_GetItem')<c.index('value=two_agreement')<c.index('weight=PyNumber_Multiply')<c.index('PyObject_SetItem(w,index,weight)'),'prefix marker before potentially failing row arithmetic and write')
ck('else value=PyObject_CallFunctionObjArgs(agreement,av,bv,NULL)' in c and 'if (ar<0) goto fail' in c and 'if (br<0) goto fail' in c,'unsupported rows callback fallback; buffer errors not erased')
ck('Py_BEGIN_ALLOW_THREADS' not in c and 'pow(' not in c and 'exp(' not in c,'no new native arithmetic or explicit GIL release')
apply=next(n for n in ast.walk(ast.parse(adapter)) if isinstance(n,ast.FunctionDef) and n.name=='apply')
ck(isinstance(apply.body[0],ast.If) and isinstance(apply.body[0].body[0],ast.Raise),'capability refusal occurs before eligibility/write path')
ck(all(x in adapter for x in ['agreement.__code__ is not code','original_module.agreement is not agreement','math_module.fsum is not fsum','math_module.exp is not exp','globals_.get(name,value) is not value','x.shape[1]!=2','x.flags.writeable','not x.flags.c_contiguous']),'explicit currentness and two-attribute readonly contiguous domain')
fixture=read(D/'fixture01.py');ast.parse(fixture)
ck("(P/'NUMERIC_RESULT01.json').write_text" in fixture and "open('x" not in fixture and 'exist_ok=False' not in fixture,'confirmed fixture overwrites output without exclusive attempt guard')
owner=read(F/'matching-compiled-uncached-edge-caller-candidate03-2026-10-11/compiled_edge_owner.py')
ck('e93bc309b1e7a38dff37ba63fd12bb0a3dce3a6766f829d6583cb008361c4dc6' not in owner and '7218b75e9d2b1f4f832418e1057a7085eeeaa20120a3dfbdcc57e303542ce9f6' not in owner,'old owner cannot select new source/adapter')
out={'decision':'ACCEPTED_C_ADAPTER_SOURCE_ONLY_FIXTURE_EXECUTION_WITHHELD','checks':checks,'references':refs,'native_library_read_or_loaded':False,'scientific_imports_or_numerical_execution':False,'findings':[{'severity':'P2','file':'fixture01.py','line':54,'issue':'Overwrite of prior numeric result; no exclusive attempt refusal before native load.','repair':'Create exclusive attempt directory before imports/load and write result exclusively; retain raw parent exit including absent result after fatal termination.'}]}
with (P/'RESULT01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':out['decision'],'checks':len(checks),'result_sha256':hashlib.sha256((P/'RESULT01.json').read_bytes()).hexdigest()}))

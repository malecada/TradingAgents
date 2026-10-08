import ast,contextlib,hashlib,json,sys,time,types,statistics
from pathlib import Path
P=Path(__file__).resolve().parent

def require(ok,why):
    if not ok:raise ValueError(why)
def load(name):
    tree=ast.parse((P/name).read_text());tree.body=[x for x in tree.body if isinstance(x,(ast.Import,ast.FunctionDef)) and (not isinstance(x,ast.FunctionDef) or x.name in ('_loaded','_authenticate_loaded'))]
    ns={'require':require,'AUTHORITY_CLASSES':{'Owner'},'Path':Path};exec(compile(tree,str(P/name),'exec'),ns);return ns
B=load('baseline.py');C=load('imported_authority_lease.py')
root=P/'synthetic';root.mkdir(exist_ok=False)
source='import contextlib\n'+''.join(f'def f{i}(x):\n    return x+{i}\n' for i in range(400))+'\nclass Owner:\n    def same(self):\n        def nested(x): return x+3\n        return nested(1)\n    @property\n    def prop(self): return 1\n\n@contextlib.contextmanager\ndef held():\n    yield 1\n'
path=root/'fixture.py';path.write_text(source)
module=types.ModuleType('synthetic_lease_exact');module.__file__=str(path);exec(compile(source,str(path),'exec'),vars(module));sys.modules[module.__name__]=module
sources={'fixture.py':hashlib.sha256(path.read_bytes()).hexdigest()};loaded=B['_loaded'](root,sources);assert loaded==C['_loaded'](root,sources)
results=[]
def compare(name,values=loaded,pins=sources):
    errors=[]
    for mod in [B,C]:
        try:mod['_authenticate_loaded'](values,pins,root);errors.append(None)
        except Exception as error:errors.append((type(error).__name__,str(error)))
    assert errors[0]==errors[1],(name,errors);results.append({'case':name,'result':errors[0] or 'accepted'})
compare('authored-method-property-contextmanager')
compare('source-hash-mismatch',pins={'fixture.py':'0'*64})
def altered(code):
    m,p,functions=loaded[module.__name__];functions=list(functions);label,fn,_=functions[0];functions[0]=(label,fn,code);return {module.__name__:(m,p,tuple(functions))}
original=loaded[module.__name__][2][0][2]
compare('wrong-co-name',altered(original.replace(co_name='wrong')))
compare('wrong-filename',altered(original.replace(co_filename='wrong.py')))
compare('wrong-constant',altered(original.replace(co_consts=(None,999))))
# Duplicate nested names retain ordered equal-name candidates and exact equality.
assert original!=original.replace(co_name=original.co_name+'different')
for functions in [[module.Owner.same.__code__], [module.Owner.same.__code__.co_consts[1]]]:
    code=functions[0];compare('nested-code-same-name', {module.__name__:(module,path,(('nested',module.Owner.same,code),))})
# Source read counts remain one per module on every full invocation.
original_read=Path.read_bytes;counts={}
for label,mod in [('baseline',B),('candidate',C)]:
    seen=[]
    def read(path):seen.append(str(path));return original_read(path)
    Path.read_bytes=read
    try:mod['_authenticate_loaded'](loaded,sources,root)
    finally:Path.read_bytes=original_read
    counts[label]=seen
assert counts['baseline']==counts['candidate']==[str(path)]
times={}
for label,mod in [('baseline',B),('candidate',C)]:
    samples=[]
    for _ in range(7):
        t=time.perf_counter();mod['_authenticate_loaded'](loaded,sources,root);samples.append(time.perf_counter()-t)
    times[label]=samples
receipt={'status':'PASS','cases':results,'source_reads':counts,'synthetic_functions':len(loaded[module.__name__][2]),'seconds':times,'median_synthetic_authentication_speedup':statistics.median(times['baseline'])/statistics.median(times['candidate']),'imports_numerical_packages':any(name in sys.modules for name in ['numpy','scipy','torch'])}
assert receipt['imports_numerical_packages'] is False
(P/'RESULT01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

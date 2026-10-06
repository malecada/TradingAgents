"""Import/source-only checks; no class instances or empirical inputs."""
import hashlib,importlib.util,json,types
from pathlib import Path
from tradingagents.research.onchain_replication import typed_tail_binding as tail,matching_owner,owned_io
D=Path(__file__).resolve().parent;root=Path.cwd()
spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.wrapper_candidate',D/'candidate/imported_authority_lease.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
modules=(tail,matching_owner,owned_io)
sources={str(Path(x.__file__).relative_to(root)):hashlib.sha256(Path(x.__file__).read_bytes()).hexdigest() for x in modules}
cases=[]
def capture():return m._loaded(root,sources)
def authenticate():m._authenticate_loaded(capture(),sources,root)
def reject(name,action):
 try:action()
 except ValueError:cases.append(name)
 else:raise AssertionError(name+' accepted')
authenticate();cases.append('real metadata dataclass and genuine authority source accepted')
for name,fn in [('authored metadata identity',tail.Binding.identity.fget),('genuine capability Binding',matching_owner.Binding._guard)]:
 code=fn.__code__
 try:
  replacement=compile('def changed(self):\n return 12471\n',fn.__code__.co_filename,'exec').co_consts[0]
  fn.__code__=replacement;reject(name+' corruption refused',authenticate)
 finally:fn.__code__=code
wrapped=owned_io._opened.__wrapped__
try:
 owned_io._opened.__wrapped__=lambda:None
 reject('contextmanager wrapper corruption refused',authenticate)
finally:owned_io._opened.__wrapped__=wrapped
unknown=types.FunctionType(tail.Binding.__repr__.__code__,tail.Binding.__repr__.__globals__,closure=tail.Binding.__repr__.__closure__)
unknown.__module__=tail.__name__;unknown.__wrapped__=tail.Binding.__repr__.__wrapped__
try:
 tail.Binding.unknown_foreign=unknown
 reject('unknown metadata foreign wrapper refused',authenticate)
finally:del tail.Binding.unknown_foreign
before=capture();original=tail.Binding.__init__
try:
 tail.Binding.__init__=lambda self:None
 assert capture()!=before
 cases.append('generated metadata method replacement detected by snapshot')
finally:tail.Binding.__init__=original
# A source-path override on an otherwise generated name is still authenticated.
try:
 ns=vars(tail).copy();exec(compile('def __init__(self):\n return None\n',tail.__file__,'exec'),ns)
 override=types.FunctionType(ns['__init__'].__code__,vars(tail));override.__module__=tail.__name__
 tail.Binding.__init__=override
 reject('source-path override cannot bypass authentication',authenticate)
finally:tail.Binding.__init__=original
bad=dict(sources);bad[str(Path(tail.__file__).relative_to(root))]='0'*64
reject('metadata source hash substitution refused',lambda:m._authenticate_loaded(capture(),bad,root))
# Arbitrary labels must not acquire the narrow generated-method exemption.
try:
 evil=types.FunctionType(compile('def evil():\n return 3\n',tail.__file__,'exec').co_consts[0],vars(tail))
 evil.__module__=tail.__name__
 setattr(tail,'evil.metadata_generated',evil)
 reject('forged generated suffix refused',authenticate)
finally:delattr(tail,'evil.metadata_generated')
authenticate();cases.append('restored source and functions accepted')
print(json.dumps({'status':'GREEN','count':len(cases),'checks':cases,'scope':'source/import only; no arrays, instances, lease activation or claims'},indent=2))

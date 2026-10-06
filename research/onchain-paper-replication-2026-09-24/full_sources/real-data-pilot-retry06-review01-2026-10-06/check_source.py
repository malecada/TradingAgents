"""Independent real metadata import RED/GREEN and exact source review; no instances or arrays."""
import ast,contextlib,hashlib,json,sys,types
from pathlib import Path
ROOT=Path.cwd();FS=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';HERE=Path(__file__).resolve().parent;W=FS/'real-data-pilot-wrapper-fix01-2026-10-06';D6=FS/'real-data-pilot-final06-2026-10-06';PKG=ROOT/'tradingagents/research/onchain_replication'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
manifest=json.loads((W/'MANIFEST01.json').read_bytes())
for p,h in manifest.items():assert sha(W/p)==h,p
assert (W/'baseline/imported_authority_lease.py').read_bytes()==(PKG/'imported_authority_lease.py').read_bytes()
source=(W/'candidate/imported_authority_lease.py').read_text();tree=ast.parse(source)
old=(W/'baseline/imported_authority_lease.py').read_text();oldtree=ast.parse(old)
oldfunc={n.name:ast.dump(n) for n in oldtree.body if isinstance(n,ast.FunctionDef)}
newfunc={n.name:ast.dump(n) for n in tree.body if isinstance(n,ast.FunctionDef)}
assert {k for k in newfunc if newfunc[k]!=oldfunc[k]}=={'_loaded','_authenticate_loaded'}
assert [ast.dump(n) for n in oldtree.body if not isinstance(n,ast.FunctionDef)]==[ast.dump(n) for n in tree.body if not isinstance(n,ast.FunctionDef)]
store=(PKG/'real_pilot_storage.py').read_bytes();candidate=(D6/'candidate/real_pilot_storage.py').read_bytes()
assert candidate.count(b'eth-paper-real-data-end-to-end-resource-20261006-06')==1 and candidate.replace(b'eth-paper-real-data-end-to-end-resource-20261006-06',b'eth-paper-real-data-end-to-end-resource-20261006-05')==store
# Actual non-authority metadata dataclass, no construction or numeric input.
from tradingagents.research.onchain_replication import typed_tail_binding as tail
scope={'contextlib':contextlib,'hashlib':hashlib,'json':json,'sys':sys,'types':types,'Path':Path,'AUTHORITY_CLASSES':{'Binding'}}
def require(v,m):
 if not v:raise ValueError(m)
scope['require']=require
p=Path(tail.__file__);sources={str(p.relative_to(ROOT)):sha(p)}
def project(t):
 s=dict(scope);nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in {'_loaded','_authenticate_loaded'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'review-helper','exec'),s);return s
baseline=project(oldtree);current=project(tree)
try:baseline['_loaded'](ROOT,sources)
except ValueError as e:assert str(e)=='contextmanager wrapper differs';red=str(e)
else:raise AssertionError('actual dataclass baseline unexpectedly passed')
loaded=current['_loaded'](ROOT,sources);current['_authenticate_loaded'](loaded,sources,ROOT)
functions=loaded[tail.__name__][2]
assert len([x for x in functions if x[0].endswith('.metadata_generated')])==7
assert any(x[0]=='Binding.identity.fget' for x in functions)
original=tail.Binding.__init__
try:
 tail.Binding.__init__=lambda self:None
 assert current['_loaded'](ROOT,sources)!=loaded
finally:tail.Binding.__init__=original
getter=tail.Binding.identity.fget;code=getter.__code__
try:
 getter.__code__=compile('def identity(self):\n return 999\n',str(p),'exec').co_consts[0]
 try:current['_authenticate_loaded'](current['_loaded'](ROOT,sources),sources,ROOT)
 except ValueError:pass
 else:raise AssertionError('authored property corruption accepted')
finally:getter.__code__=code
current['_authenticate_loaded'](current['_loaded'](ROOT,sources),sources,ROOT)
report={'schema_version':1,'decision':'accepted','reviewer':'namespace_review05 independent retry06 reviewer','candidates':[ref(W/'candidate/imported_authority_lease.py'),ref(D6/'candidate/real_pilot_storage.py')],'worker_manifest':ref(W/'MANIFEST01.json'),'independent_checks':['actual imported metadata dataclass baseline reproduces contextmanager refusal','exact candidate authenticates source plus seven captured generated methods','authored identity getter remains captured and modified code refuses','generated init replacement changes loaded snapshot','foreign generated-label spoof independently refused','all nonchecker functions/classes/imports unchanged','storage exact05-to06 one-literal inverse'],'findings':[],'control_boundary':'Exactly typed_tail_binding.Binding seven generated metadata methods are snapshot-checked but their runtime-generated bodies are not source-compilation authenticated before capture. Explicit D6 charter states boundary. Authored properties/overrides, genuine capability classes, original contextmanager code/globals/closure checks and source-body hashes remain required. No generic foreign-wrapper exemption.','not_tested':['No real authority lease/Owner instance or lifecycle claim, graph/model/array execution.','No financial timing/cashflow/fees/funding or economic validation.','No before-capture authenticity of generated metadata method bodies; intentionally outside claimed capability scope.','Final D6 binding/source reanchor/recovery/runtime/headroom release remains separate.']}
(HERE/'SOURCE_REVIEW01.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'source_review':ref(HERE/'SOURCE_REVIEW01.json'),'actual_red':red,'candidate':report['candidates'][0]},indent=2))

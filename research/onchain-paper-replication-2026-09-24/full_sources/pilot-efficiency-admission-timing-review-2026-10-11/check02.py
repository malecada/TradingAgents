"""Changed-seam AST and scalar publication checks only; no scientific imports."""
import ast,copy,json,types,sys
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];S=R/'tradingagents/research/onchain_replication';C=D.parent/'authority-expected-code-cache-candidate02-2026-10-11';checks=[]
def ck(ok,name):
    assert ok,name
    checks.append(name)
def timing_call(n):return isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='phase_timing'
class RemoveTiming(ast.NodeTransformer):
    def visit_With(self,n):
        self.generic_visit(n)
        if len(n.items)==1 and timing_call(n.items[0].context_expr):return n.body
        return n
    def visit_Expr(self,n):
        if timing_call(n.value) and n.value.func.attr=='add_bytes':return None
        return self.generic_visit(n)
def parse(p):return ast.parse(p.read_text())
def named(t,name):return next(n for n in ast.walk(t) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
old=parse(C/'imported_authority_lease.py');new=RemoveTiming().visit(parse(S/'imported_authority_lease.py'))
for name in ('_authenticate_loaded','_authenticate_expected','_finger','_full','_live','_identity','_expected_current','_expected_context','activate'):
    ck(ast.dump(named(old,name))==ast.dump(named(new,name)),'inline-only lease '+name)
oldcaller=parse(C/'real_pilot_import_caller.py');newcaller=RemoveTiming().visit(parse(S/'real_pilot_import_caller.py'))
oldbody=named(oldcaller,'execute').body
start=next(i for i,n in enumerate(oldbody) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='budget' for t in n.targets))
newbody=named(newcaller,'operation').body
start2=next(i for i,n in enumerate(newbody) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='budget' for t in n.targets))
ck(ast.dump(ast.Module(body=oldbody[start:],type_ignores=[]))==ast.dump(ast.Module(body=newbody[start2:],type_ignores=[])),'entire admitted execution body unchanged after inline scopes removed')
# Load only stdlib timing/reporting modules under a disposable package name.
pkg=types.ModuleType('_review_scalar');pkg.__path__=[];sys.modules[pkg.__name__]=pkg
for name in ('failure_reporting','phase_timing'):
    mod=types.ModuleType(pkg.__name__+'.'+name);mod.__package__=pkg.__name__;sys.modules[mod.__name__]=mod
    exec(compile((S/(name+'.py')).read_text(),str(S/(name+'.py')),'exec'),vars(mod));setattr(pkg,name,mod)
t=pkg.phase_timing;primary=KeyboardInterrupt('primary');seen=[]
def operation():
    with t.measure('entry'):raise primary
def publish(value):seen.append(value);raise OSError('disk')
try:t.run_profiled(operation,publish)
except KeyboardInterrupt as found:ck(found is primary,'run_profiled preserves original fatal on publication failure')
else:raise AssertionError('missing fatal')
ck(seen[0]['phases']['entry']['failures']==1 and t._ACTIVE.get() is None,'complete failure snapshot and activation restored')
sentinel=object();seen=[]
ck(t.run_profiled(lambda:sentinel,seen.append) is sentinel and len(seen)==1,'success publishes exactly once and returns original result')
# Authenticate exact actual timing definitions using genuine extracted loaded
# collector/authenticator, without any actual Lease or research-module imports.
ns=dict(contextlib=__import__('contextlib'),hashlib=__import__('hashlib'),sys=sys,types=types,Path=Path,phase_timing=t,
    require=lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg)))
nodes=[n for n in parse(S/'imported_authority_lease.py').body if isinstance(n,ast.FunctionDef) and n.name in ('_loaded','_authenticate_loaded') or isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='AUTHORITY_CLASSES' for x in n.targets)]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'extracted-loaded-controls','exec'),ns)
t.__file__=str((S/'phase_timing.py').resolve());sources={'phase_timing.py':__import__('hashlib').sha256((S/'phase_timing.py').read_bytes()).hexdigest()}
loaded=ns['_loaded'](S.resolve(),sources);ns['_authenticate_loaded'](loaded,sources,S.resolve())
ck(len(loaded)==1 and any(label.startswith('PhaseTotals.') for label,_,_ in next(iter(loaded.values()))[2]),'actual PhaseTotals methods/contextmanager authenticate through original loaded-code rules')
(D/'CHECK02.json').write_text(json.dumps({'status':'PASS','checks':checks,'science_imported':False,'actual_authority_created':False},indent=2)+'\n');print(len(checks),'checks passed')

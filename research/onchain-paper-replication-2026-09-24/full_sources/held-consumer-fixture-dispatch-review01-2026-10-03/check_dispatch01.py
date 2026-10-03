import ast,copy,hashlib,json
from pathlib import Path
from types import SimpleNamespace as NS
H=Path(__file__).resolve().parent;F=H.parent
C=F/'held-consumer-fixture-dispatch-preparation01-2026-10-03'
T=F/'held-consumer-positive-case-contract-investigation01-2026-10-03'
S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source/tradingagents/research/onchain_replication')
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((C/'MANIFEST01.json').read_bytes())=='f7209b4555872c05480b1fa4d9405e733213ef1969da54a489f51e8e74cc2a44'
for row in json.loads((C/'MANIFEST01.json').read_bytes())['files']:
 raw=(C/row['path']).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
assert (C/'baseline-source03.txt').read_bytes()==(S/'resource_fixture.py').read_bytes()
def extract(path,names,ns):
 tree=ast.parse(path.read_bytes());nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names or isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in x.targets)]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
class DropImports(ast.NodeTransformer):
 def visit_ImportFrom(self,n):return ast.copy_location(ast.Pass(),n)
policy_ns={'Path':Path};extract(S/'held_score_consumer.py',{'KIND','require','_policy','FIELD'},policy_ns)
def functions(path):
 ns={'Path':Path};extract(path,{'KEYS','require','selection'},ns)
 pre=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='preflight')
 start=next(i for i,n in enumerate(pre.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='item' for t in n.targets))
 end=next(i for i,n in enumerate(pre.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='control' for t in n.targets))
 ns['fragment']=compile(ast.fix_missing_locations(DropImports().visit(ast.Module(body=pre.body[start:end],type_ignores=[]))),str(path),'exec');return ns
NEW=functions(C/'resource_fixture.py');OLD=functions(C/'baseline-source03.txt')
def data():
 job=json.loads((T/'JOB_TEMPLATE01.json').read_bytes());plan=json.loads((T/'PLAN_TEMPLATE01.json').read_bytes());p=json.loads((T/'HELD_POLICY01.json').read_bytes())
 outputs=['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json']+[v['output'] for v in p['targets'].values()]
 return job,plan,p,outputs
def seam(ns,job,plan,p,outputs,read_error=None,registered=True):
 _,s,_=ns['selection'](job)
 def read(r,n):
  if read_error is not None:raise read_error
  return json.dumps(p).encode()
 run=NS(admission=NS(experiment={'outputs':outputs},inputs={'held_score_policy':{}} if registered else {}))
 env=dict(ns,run=run,s=s,plan=plan,original=NS(parse=json.loads,_read_registered=read),held_score_consumer=NS(_policy=policy_ns['_policy']))
 exec(ns['fragment'],env)
def refusal(fn):
 try:fn()
 except (ValueError,KeyError,TypeError):return
 raise AssertionError('unexpected acceptance')
j,pl,p,o=data();refusal(lambda:seam(OLD,j,pl,p,o));seam(NEW,j,pl,p,o);print('PASS actual baseline RED / candidate selected metadata GREEN')
for mutate in [lambda j,pl,p,o:p['targets'].pop(next(iter(p['targets']))),lambda j,pl,p,o:o.append('extra.json'),lambda j,pl,p,o:o.pop(),lambda j,pl,p,o:pl['producers']['original32'].pop('held_score_consumer_input'),lambda j,pl,p,o:p.update(part_bytes=True),lambda j,pl,p,o:p.update(extra='x'*8192),lambda j,pl,p,o:p['targets'][next(iter(p['targets']))].update(output='resource-binding.json'),lambda j,pl,p,o:p['targets'][next(iter(p['targets']))].update(output='../bad.json')]:
 j,pl,p,o=data();mutate(j,pl,p,o);refusal(lambda:seam(NEW,j,pl,p,o))
for error in [MemoryError('read'),KeyboardInterrupt('read'),SystemExit('read')]:
 j,pl,p,o=data()
 try:seam(NEW,j,pl,p,o,read_error=error)
 except BaseException as actual:assert actual is error
 else:raise AssertionError('fatal lost')
print('PASS 8 malformed/output refusals and 3 exact first-fatal read sentinels; metadata stand-ins only')
# Execute actual _route prefix with exact local stand-in classes: proves predicate
# ordering only. These are deliberately not represented as real Target/Owner.
class Target:
 def check(self):pass
class Owner:pass
route_ns=dict(policy_ns,imported_mcm_identity=NS(Target=Target),compact_owner=NS(Owner=Owner))
route=next(n for n in ast.parse((S/'held_score_consumer.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_route')
exec(compile(ast.fix_missing_locations(DropImports().visit(ast.Module(body=[route],type_ignores=[]))),str(S/'held_score_consumer.py'),'exec'),route_ns)
findings=[]
for name,change in [('plan_only_selector',lambda s,item:s.pop('held_score_consumer_input')),('plan_only_unknown_selector',lambda s,item:item.update(held_score_typo='invalid'))]:
 j,pl,p,o=data();s=j['payload']['representation_jobs']['original32'];item=pl['producers']['original32'];change(s,item)
 if name=='plan_only_selector':o=o[:4]
 seam(NEW,j,pl,p,o)
 target=Target();target.owner=Owner();target.execution=NS(_stage=NS(prepared=NS(_selection_now=lambda:{'selected':s,'producer':item})))
 try:route_ns['_route'](target)
 except ValueError as e:reason=str(e)
 else:raise AssertionError('expected actual later route refusal')
 findings.append({'case':name,'fixture_preflight_output_fragment':'accepted','later_actual_route_predicate':'refused','reason':reason,'authority':'stand-in classes; no Owner created'})
 print('REPRODUCED',name,reason)
# Whole-module inverse byte equality, using the exact declared diff reversal.
import subprocess
# Do not apply a patch to any source; reverse changed source spans in memory.
a=(C/'baseline-source03.txt').read_text();b=(C/'resource_fixture.py').read_text();ta=ast.parse(a);tb=ast.parse(b)
assert len(ta.body)==len(tb.body)
for x,y in zip(ta.body,tb.body):
 if isinstance(x,ast.FunctionDef) and x.name in {'selection','preflight'}:continue
 assert ast.dump(x)==ast.dump(y)
 assert ast.get_source_segment(a,x)==ast.get_source_segment(b,y)
aa=a.splitlines(True);bb=b.splitlines(True)
for x,y in reversed(list(zip(ta.body,tb.body))):
 if isinstance(x,ast.FunctionDef) and x.name in {'selection','preflight'}:bb[y.lineno-1:y.end_lineno]=aa[x.lineno-1:x.end_lineno]
assert ''.join(bb)==a
(H/'COUNTEREXAMPLES01.json').write_text(json.dumps({'scope':'actual-source AST seams with synthetic metadata; no genuine authority','findings':findings},indent=2)+'\n')
print('PASS exact inverse whole bytes outside selection/preflight; all candidate manifest bodies matched')

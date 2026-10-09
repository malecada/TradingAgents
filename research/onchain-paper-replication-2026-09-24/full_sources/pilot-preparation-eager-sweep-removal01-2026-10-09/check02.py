"""Exact caller branch AST; inert call tracing, no authority or numerical execution."""
import ast,json,hashlib,types,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30)
H=Path(__file__).resolve().parent;ROOT=H.parents[3];S=ROOT/'tradingagents/research/onchain_replication';old=(S/'real_pilot_import_caller.py').read_text();new=(H/'real_pilot_import_caller.py').read_text()
a='            checked = [Target(execution,g,k) for k,g in graphs.items()]';b="            checked = [] if p.get('imported_authority_lease_input') is not None and selected_mcm.get('schema_version') == 6 else [Target(execution,g,k) for k,g in graphs.items()]"
assert new.replace(b,a)==old and new.count(b)==1
# Select exact existing sweep and production entry statements, excluding post-production retention/training.
def excerpt(text):
 tree=ast.parse(text);nodes=list(ast.walk(tree));branch=next(n for n in nodes if isinstance(n,ast.If) and ast.unparse(n.test)=='diagnostic is None' and 'checked' in ast.unparse(n))
 prep=next(n for n in nodes if isinstance(n,ast.For) and ast.unparse(n.iter)=='enumerate(checked)')
 prod=next(n for n in nodes if isinstance(n,ast.For) and ast.unparse(n.iter)=='enumerate(graphs.items())')
 stop=next(i for i,n in enumerate(prod.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets))
 prod=ast.For(target=prod.target,iter=prod.iter,body=prod.body[:stop+1],orelse=[])
 return compile(ast.fix_missing_locations(ast.Module(body=[branch,prep,prod],type_ignores=[])),'<actual caller controlflow>','exec')
# Fresh production calls themselves are extracted from the actual installed functions.
t=ast.parse((S/'compact_mcm.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='produce_imported');target=next(n for n in f.body if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='target' for v in n.targets))
t=ast.parse((S/'compact_mcm_batched.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='produce');prepare=next(n for n in ast.walk(f) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='producer._prepare')
fresh=compile(ast.Module(body=[target,prepare],type_ignores=[]),'<actual fresh production Target and prepare>','exec')
def run(text,lease=True,schema=6,diag=False,bad=None):
 events=[];phase=['eager']
 def Target(execution,g,k):events.append((phase[0],'target',k));return types.SimpleNamespace(key=k)
 def prepare(target,key,i,o):
  events.append((phase[0],'prepare',key))
  if key==bad:raise ValueError('synthetic later graph refusal')
  return None,None,None,None
 def produce(execution,g,*,graph_hash,input_name,output_input,**kw):
  phase[0]='production';ns=dict(Target=Target,execution=execution,graph=g,graph_hash=graph_hash,input_name=input_name,output_input=output_input,producer=types.SimpleNamespace(_prepare=prepare));exec(fresh,ns);events.append(('production','completed',graph_hash))
 nop=lambda *a,**k:None
 diagnostic=types.SimpleNamespace(startup_enter=nop,startup_complete=nop) if diag else None
 ns=dict(diagnostic=diagnostic,p={'imported_authority_lease_input':'selected'} if lease else {},graphs={str(i):None for i in range(7)},Target=Target,execution=None,s={'compact_mcm_input':'mcm','compact_mcm_output_input':'out'},compact_mcm=types.SimpleNamespace(_prepare=prepare,produce_imported=produce),watch=types.SimpleNamespace(check=nop),measurements=types.SimpleNamespace(begin=nop),progress=None)
 if lease:ns['selected_mcm']={'schema_version':schema}
 error=None
 try:exec(excerpt(text),ns)
 except ValueError as e:error=str(e)
 return events,error
base=run(old);candidate=run(new);assert sum(x[:2]==('eager','target') for x in base[0])==7 and sum(x[:2]==('eager','prepare') for x in base[0])==7
assert all(x[0]=='production' for x in candidate[0]) and [x[2] for x in candidate[0] if x[1]=='completed']==list(map(str,range(7)))
assert [x for x in base[0] if x[0]=='production']==candidate[0]
for lease,schema,diag in [(False,6,False),(True,5,False),(True,1,False),(True,6,True),(False,6,True)]:assert run(old,lease,schema,diag)==run(new,lease,schema,diag)
red=run(old,bad='3');changed=run(new,bad='3');assert red[1]==changed[1] and not any(x[1]=='completed' for x in red[0]) and [x[2] for x in changed[0] if x[1]=='completed']==['0','1','2']
r=dict(status='PASS_CONTROLFLOW_ONLY',literal_inverse=True,baseline_trace=base,candidate_trace=candidate,legacy_diagnostic_no_lease_equal=True,later_refusal_baseline=red,later_refusal_candidate=changed,qualification='Inert traced callbacks execute exact branch statements; no genuine Owner/Run, graph data, validation bypass or scientific result. Unreached graphs remain unexecuted; existing lifecycle disposition is not simulated.')
(H/'CHECK02.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS exact sweep/production entry controlflow; five preserved routes; later refusal timing differs')

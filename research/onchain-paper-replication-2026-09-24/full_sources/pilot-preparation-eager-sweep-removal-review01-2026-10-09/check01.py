import ast,json,hashlib,types,os,resource,signal,copy
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=Path(__file__).resolve().parent;C=R.parent/'pilot-preparation-eager-sweep-removal01-2026-10-09';ROOT=R.parents[3];S=ROOT/'tradingagents/research/onchain_replication';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=json.loads((C/'MANIFEST01.json').read_bytes())
assert sha(C/'real_pilot_import_caller.py')==m['candidate_sha256'] and sha(S/'real_pilot_import_caller.py')==m['baseline_sha256']
for n,h in m['evidence'].items():assert sha(C/n)==h
old=(S/'real_pilot_import_caller.py').read_text();new=(C/'real_pilot_import_caller.py').read_text();before='checked = [Target(execution,g,k) for k,g in graphs.items()]';after="checked = [] if p.get('imported_authority_lease_input') is not None and selected_mcm.get('schema_version') == 6 else [Target(execution,g,k) for k,g in graphs.items()]";assert new.count(after)==1 and new.replace(after,before)==old
assert ast.dump(ast.parse(new.replace(after,before)),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
def snippet(text):
 ns=list(ast.walk(ast.parse(text)));branch=next(x for x in ns if isinstance(x,ast.If) and ast.unparse(x.test)=='diagnostic is None' and any(isinstance(y,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='checked' for z in y.targets) for y in x.body));prep=next(x for x in ns if isinstance(x,ast.For) and ast.unparse(x.iter)=='enumerate(checked)');prod=copy.deepcopy(next(x for x in ns if isinstance(x,ast.For) and ast.unparse(x.iter)=='enumerate(graphs.items())'));idx=next(i for i,x in enumerate(prod.body) if isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='result' for z in x.targets));prod.body=prod.body[:idx+1];return compile(ast.fix_missing_locations(ast.Module([branch,prep,prod],[])),'<actual changed branch>','exec')
def getfn(name,fn):return next(x for x in ast.parse((S/name).read_bytes()).body if isinstance(x,ast.FunctionDef) and x.name==fn)
f=getfn('compact_mcm.py','produce_imported');target=next(x for x in f.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='target' for y in x.targets));f=getfn('compact_mcm_batched.py','produce');prep=next(x for x in ast.walk(f) if isinstance(x,ast.Assign) and isinstance(x.value,ast.Call) and ast.unparse(x.value.func)=='producer._prepare');fresh=compile(ast.Module([target,prep],[]),'<actual production statements>','exec')
def run(text,p,schema=None,diagnostic=False,bad=None):
 events=[];phase=['eager'];failure=ValueError('synthetic refusal');nop=lambda *a,**k:None
 def target(execution,g,key):events.append((phase[0],'target',key));return types.SimpleNamespace(key=key)
 def prepare(t,key,*args):
  events.append((phase[0],'prepare',key))
  if key==bad:raise failure
  return (None,)*4
 def produce(execution,graph,graph_hash,input_name,output_input,**kwargs):
  phase[0]='production';ns=dict(Target=target,execution=execution,graph=graph,graph_hash=graph_hash,input_name=input_name,output_input=output_input,producer=types.SimpleNamespace(_prepare=prepare));exec(fresh,ns);events.append(('production','returned',graph_hash))
 ns=dict(p=p,diagnostic=types.SimpleNamespace(startup_enter=nop,startup_complete=nop) if diagnostic else None,Target=target,graphs={str(i):object() for i in range(7)},execution=None,compact_mcm=types.SimpleNamespace(_prepare=prepare,produce_imported=produce),s={'compact_mcm_input':'in','compact_mcm_output_input':'out'},watch=types.SimpleNamespace(check=nop),measurements=types.SimpleNamespace(begin=nop),progress=None)
 if schema is not None:ns['selected_mcm']={'schema_version':schema}
 error=None
 try:exec(snippet(text),ns)
 except ValueError as e:assert e is failure;error=str(e)
 return events,error
base=run(old,{'imported_authority_lease_input':'lease'},6);newcase=run(new,{'imported_authority_lease_input':'lease'},6);assert len(base[0])==35 and len(newcase[0])==21;assert [e for e in base[0] if e[0]=='production']==newcase[0]
for p,sv,d in [({},None,False),({'imported_authority_lease_input':None},None,False),({'imported_authority_lease_input':'lease'},5,False),({'imported_authority_lease_input':'lease'},6,True),({},None,True)]:assert run(old,p,sv,d)==run(new,p,sv,d)
a=run(old,{'imported_authority_lease_input':'lease'},6,bad='2');b=run(new,{'imported_authority_lease_input':'lease'},6,bad='2');assert not [x for x in a[0] if x[1]=='returned'] and [x[2] for x in b[0] if x[1]=='returned']==['0','1'];assert b[0][-1]==('production','prepare','2') and a[1]==b[1]
# Production authority/source bracket remains actual source, not simulated authority.
pf=getfn('compact_mcm.py','_prepare');assert ast.unparse(pf.body[0])=='dictionary.check()';assert 'dictionary.check()' in ast.unparse(pf.body[-4:]) or ast.unparse(pf).count('dictionary.check()')>=2
assert 'held.check(owner)' in ast.unparse(getfn('compact_mcm_batched.py','produce'))
assert "target=Target(execution,graph,graph_hash)" in (S/'compact_mcm.py').read_text()
evidence={str((C/n).relative_to(ROOT)):sha(C/n) for n in ('MANIFEST01.json','real_pilot_import_caller.py','CHECK01.log','CHECK02.json','check02.py')}
for n in ('real_pilot_import_caller.py','compact_mcm.py','compact_mcm_batched.py','imported_mcm_identity.py'):evidence[str((S/n).relative_to(ROOT))]=sha(S/n)
r={'decision':'accepted_source_only','candidate_sha256':m['candidate_sha256'],'baseline_sha256':m['baseline_sha256'],'evidence':evidence,'checks':{'single_assignment_literal_AST_inverse':True,'healthy_eager_target_and_prepare_removed':[7,7],'same_seven_ordered_production_entries':True,'preserved_branch_cases':5,'no_lease_selected_mcm_undefined_safe':True,'later_failure_original_completed':0,'later_failure_candidate_completed':2,'original_exception_object_preserved':True},'operational_deviation':'Selected nondiagnostic schema6 imported-lease route drops eager all-graph validation. Later graph refusal may follow earlier graph production; no prevalidation or unchanged complete failure-trace claim.','qualification':'Exact extracted branch and production statements exercised with inert metadata doubles only; genuine Target/Owner/lease/source checks remain in unchanged production source but were not instantiated. Existing early admitted schema validation is relied upon; no broader hostile runtime type guarantee. No numerical import, real graph, authority, launch, speedup, capacity or scientific completion claim.'};(R/'SOURCE_REVIEW01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['checks']))

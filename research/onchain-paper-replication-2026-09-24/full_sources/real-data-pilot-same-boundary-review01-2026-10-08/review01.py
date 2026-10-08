import ast,builtins,contextlib,copy,hashlib,json,sys,types
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'real-data-pilot-same-boundary-reuse01-2026-10-08';H=Path(__file__).resolve().parent;M=R/'tradingagents/research/onchain_replication';evidence={};checks=[]
def read(p):
 b=p.read_bytes();evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b.decode()
def check(n,v):
 assert v,n
 checks.append(n)
lease=read(C/'imported_authority_lease.py');target=read(C/'imported_mcm_identity.py');oldlease=read(C/'baseline_imported_authority_lease.py');oldtarget=read(C/'baseline_imported_mcm_identity.py')
check('exact_lease_sha',hashlib.sha256(lease.encode()).hexdigest()=='f94f181dfa02d92eb58f96d99bfc70f8353d0945564013733ac5b2d2432cf8b4');check('exact_target_sha',hashlib.sha256(target.encode()).hexdigest()=='39304277c2a0c6278a7524102f15bcfb0f8f9d73f691b51e0cd7a554a65bd7eb')
check('frozen_main_lease',read(M/'imported_authority_lease.py')==oldlease);check('frozen_main_target',read(M/'imported_mcm_identity.py')==oldtarget)
def functions(src):
 tree=ast.parse(src);out={}
 for n in tree.body:
  if isinstance(n,ast.FunctionDef):out[n.name]=n
  if isinstance(n,ast.ClassDef):
   for f in n.body:
    if isinstance(f,ast.FunctionDef):out[n.name+'.'+f.name]=f
 return out
oldf=functions(oldlease);newf=functions(lease)
check('only_lease_expected_functions',{k for k in oldf.keys()|newf.keys() if ast.dump(oldf[k])!=ast.dump(newf[k])} if False else set(newf)-set(oldf)=={'_checked_value'})
for k in oldf:
 if k not in ('Lease._full','Lease.check','check'):check('unchanged_lease_'+k,ast.dump(oldf[k])==ast.dump(newf[k]))
ot=functions(oldtarget);nt=functions(target)
for k in ot:
 if k not in ('_checkpoint','Target.__init__'):check('unchanged_target_'+k,ast.dump(ot[k])==ast.dump(nt[k]))
for funcs in (ot,nt):
 calls=[n for n in ast.walk(funcs['Target.__init__']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_checkpoint'];check('four_constructor_boundaries_'+str(funcs is nt),len(calls)==4)
check('two_adjacent_execution_checks_removed',sum(isinstance(n,ast.Call) and ast.unparse(n.func)=='execution.check' for n in ast.walk(ot['Target.__init__']))==2 and sum(isinstance(n,ast.Call) and ast.unparse(n.func)=='execution.check' for n in ast.walk(nt['Target.__init__']))==0)
# Real stdlib Interval and provenance functions; exact Lease methods are run
# unbound on metadata holders, never constructing a Lease/Owner/Run capability.
interval={};exec(compile(read(M/'imported_authority_interval.py'),'interval','exec'),interval)
prov={};tree=ast.parse(read(M/'provenance.py'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('canonical_bytes','thaw')];prov['json']=json;exec(compile(ast.Module(body=nodes,type_ignores=[]),'provenance-pure','exec'),prov);canonical=prov['canonical_bytes']
compact=types.SimpleNamespace()
def importer(name,globals=None,locals=None,fromlist=(),level=0):
 if level==1 and name=='provenance':return types.SimpleNamespace(**prov)
 if level==1 and name=='':return types.SimpleNamespace(compact_owner=compact)
 raise AssertionError(('unexpected import',name,level))
ns={'json':json,'types':types,'sys':sys,'Path':Path,'contextlib':contextlib,'hashlib':hashlib,'fingerprint':interval['fingerprint'],'require':interval['require'],'__builtins__':dict(vars(builtins),__import__=importer)}
for name in ('_loaded','_authenticate_loaded','_checked_value'):
 exec(compile(ast.Module(body=[newf[name]],type_ignores=[]),'<exact '+name+'>','exec'),ns)
ns['AUTHORITY_CLASSES']=set()
methods={}
for name in ('_identity','_finger','_full','check'):
 node=copy.deepcopy(newf['Lease.'+name]);exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact Lease.'+name+'>','exec'),ns);methods[name]=ns[name]
policy={'schema_version':1,'kind':interval['KIND'],'live_interval_ms':1,'fingerprint_interval_ms':2,'full_interval_ms':10,'max_stale_ms':100,'max_calls_between_full':100,'assumption':interval['ASSUMPTION']}
sourcepath=H/'synthetic-source.txt';sourcepath.write_text('before')
def scenario(mode=None,return_value=True,boundary=True):
 sourcepath.write_text('before');current={'identity':'current'};original={'identity':'original'};ticks=[0.0];clock_calls=[0];events=[];holder=types.SimpleNamespace();cap=types.SimpleNamespace(_closed=False);prepared=types.SimpleNamespace(_closed=False,_cap=cap,_configuration=lambda:b'configuration');owner=types.SimpleNamespace(closed=False,poisoned=False);run=types.SimpleNamespace(_claim_sha256='claim',admission=types.SimpleNamespace(source='source',registration_sha256='registration',inputs={},experiment={'source_files':{}},root=H));bound=types.SimpleNamespace(_run=run,context={});stage=types.SimpleNamespace(prepared=prepared,closed=True);material=types.SimpleNamespace(_integrity=lambda:copy.deepcopy(original));execution=types.SimpleNamespace(_owner=owner,_stage=stage,_bound=bound,_materialized=material,_execution=current,_execution_pin=canonical(current))
 def actual_check():events.append('full');return {'current':copy.deepcopy(current),'original':copy.deepcopy(original)}
 execution.check=actual_check
 def clock():
  clock_calls[0]+=1
  if clock_calls[0]==7:
   events.append('last_clock')
   if mode=='current':current['identity']='changed'
   if mode=='original':original['identity']='changed'
   if mode=='object':execution._owner=types.SimpleNamespace()
   if mode=='configuration':run.admission.source='changed'
   if mode=='source':sourcepath.write_text('after')
   if mode=='revocation':owner.closed=True
   if mode=='baseline':holder.value=b'{}'
   if mode=='stale':ticks[0]=1.0
  return ticks[0]
 scheduler=interval['Interval'](policy,clock=clock)
 holder.__dict__.update(execution=execution,owner=owner,stage=stage,prepared=prepared,bound=bound,run=run,objects=(execution,owner,stage,prepared,bound,run,material,cap),scheduler=scheduler,_scheduler_pin=scheduler,_policy_pin=scheduler.policy,_clock_pin=scheduler.clock,closed=False,target=None,paths=(sourcepath,),fingerprints=(interval['fingerprint'](sourcepath),),sources={},loaded={},value=canonical(actual_check()))
 holder.configuration=canonical({'prepared':prepared._configuration().hex(),'execution':execution._execution_pin.hex(),'claim':run._claim_sha256,'source':run.admission.source,'registration':run.admission.registration_sha256,'inputs':{},'sources':{},'runtime':{}})
 for name in ('_identity','_finger','_full'):setattr(holder,name,types.MethodType(methods[name],holder))
 def live():events.append('live');holder._identity()
 holder._live=live
 def verify(_):
  events.append('final_rejoin')
  if mode=='fatal':raise MemoryError('final rejoin fatal')
  interval['require'](not owner.closed,'revoked')
 compact.verify_current=verify
 stage.integrity=lambda:events.append('stage_integrity')
 events.clear()
 try:
  value=methods['check'](holder,boundary=boundary,_return_value=return_value);return value,holder,events,None
 except BaseException as error:return None,holder,events,error
v,h,events,error=scenario();check('actual_method_return',error is None and v=={'current':{'identity':'current'},'original':{'identity':'original'}} and events.count('full')==1);check('clock_precedes_final_rejoin',events.index('last_clock')<events.index('final_rejoin'))
v['current']['identity']='caller-mutation';check('returned_metadata_detached',h.execution._execution=={'identity':'current'})
for mode in ('current','original','object','configuration','source','revocation','baseline','stale','fatal'):
 v,h,events,error=scenario(mode);check('late_refusal_'+mode,isinstance(error,MemoryError if mode=='fatal' else ValueError) and h.closed and h.scheduler.closed)
v,h,events,error=scenario(return_value=False);check('default_return_none',error is None and v is None and 'final_rejoin' not in events and events.count('full')==1)
v,h,events,error=scenario(boundary=False);check('no_sampled_value_export',isinstance(error,ValueError) and h.closed and h.scheduler.closed)
# No-lease constructor checkpoint keeps exactly the legacy two execution checks.
checkpoint_env={'__builtins__':dict(vars(builtins),__import__=lambda *a,**k:(_ for _ in ()).throw(AssertionError('unexpected lease import')))};exec(compile(ast.Module(body=[nt['_checkpoint']],type_ignores=[]),'<checkpoint>','exec'),checkpoint_env);calls=[];e=types.SimpleNamespace(check=lambda:calls.append(1) or {'v':1})
for value in (True,False,True,False):checkpoint_env['_checkpoint'](e,value=value)
check('default_two_full_checks_preserved',len(calls)==2)
# Inspect real callback-free chain rather than instantiate it.
for name in ('compact_owner.py','original_import_stage.py'):read(M/name)
result={'decision':'accepted-source-only','evidence':evidence,'checks':checks,'candidate_hashes':{str((C/n).relative_to(R)):evidence[str((C/n).relative_to(R))] for n in ('imported_authority_lease.py','imported_mcm_identity.py')},'scope':'Future candidate only; active21 source/Git untouched. Actual isolated Lease.check/_identity/_finger/_full methods and real Interval exercised on non-authoritative metadata holders with callback stubs. No Lease/Owner/Run instantiated. Four constructor boundaries retained; two adjacent execution checks reused only from that invocation. Late clock current/original/object/config/source/revocation/baseline/staleness mutations and fatal rejoin poison lease+scheduler. Final clock precedes callback-free rejoin. Legacy no-lease route retains two checks. No persistent result cache/token, numerical/neural/graph reads, authority admission, measured saving or integration claim. Final rejoin is still sampled and non-atomic; no proof of wall-clock age after uninstrumented final rejoin or writer exclusion.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted-source-only','checks':len(checks),'sha256':hashlib.sha256((H/'SOURCE_REVIEW01.json').read_bytes()).hexdigest()}))

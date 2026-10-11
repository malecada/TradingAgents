"""Independent selected preload seam review; stdlib-only, isolated module registry."""
import ast,builtins,contextlib,copy,hashlib,json,resource,signal,sys,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(15,15));signal.alarm(30)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];C=F/'pilot31-loaded-identity-correction01-2026-10-11';S=R/'tradingagents/research/onchain_replication';checks={};refs={}
def rb(p):
 assert not ({'.git','.venv','keys','apis','research_artifacts','research_runs'}&set(p.parts));b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def ck(v,name):
 checks[name]=bool(v)
 if not v:raise AssertionError(name)
def require(v,m):
 if not v:raise ValueError(m)
def funcs(body,names):return ast.Module(body=[n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
try:
 manifest=json.loads(rb(C/'MANIFEST01.json'))
 for name,row in manifest['files'].items():
  b=rb(C/name);ck(len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256'],'frozen candidate '+name)
 original=rb(S/'real_pilot_import_caller.py').decode();candidate=rb(C/'real_pilot_import_caller.py').decode()
 ck(hashlib.sha256(original.encode()).hexdigest()=='06b60d5e0741fe5a8734e8f1f71f9cc3079644075e0a27d03f678bb74ca52ca0' and hashlib.sha256(candidate.encode()).hexdigest()=='f65ff353315bfb9e4db80d326170e02e5b2ebc6da1e5d59e5a8e9243b4afd11a','exact original and candidate hashes')
 addition="        if compiled:\n            # Freeze selected helper identities before genuine Lease activation.\n            # Importing these definitions does not open a native backend.\n            from . import compiled_normalization_policy, compiled_small_lse\n"
 keyword=",compiled=selected_mcm.get('schema_version') in (5,6) and 'compiled_normalization_policy' in selected_mcm['batched']['execution']"
 ck(candidate.count(addition)==candidate.count(keyword)==1,'single bounded helper block and caller keyword')
 inverse=candidate.replace('def _prepare_lease_modules(*, batched=False, grouped=False, compiled=False):','def _prepare_lease_modules(*, batched=False, grouped=False):').replace(addition,'').replace(keyword,'')
 ck(inverse==original,'whole source literal inverse; all surrounding callbacks guards caps unchanged')
 ct=ast.parse(candidate);caller=next(n for n in ct.body if isinstance(n,ast.FunctionDef) and n.name=='execute');call=next(n for n in ast.walk(caller) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_prepare_lease_modules');activate=next(n for n in ast.walk(caller) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='activate')
 ck(call.lineno<activate.lineno and candidate.splitlines()[call.lineno-2].strip()=="selected_mcm=_read(run.admission,s['compact_mcm_input'])",'exact genuine admitted MCM read then preload then activation')
 expression=next(k.value for k in call.keywords if k.arg=='compiled')
 choice=lambda m:eval(compile(ast.Expression(expression),'selected-call-expression','eval'),{'selected_mcm':m})
 ck(choice({'schema_version':6,'batched':{'execution':{'compiled_normalization_policy':{}}}}) is True and choice({'schema_version':5,'batched':{'execution':{'compiled_normalization_policy':{}}}}) is True,'both selected batched schemas preload')
 ck(choice({'schema_version':6,'batched':{'execution':{}}}) is False and choice({'schema_version':1}) is False,'unselected and nonbatched caller short-circuit')
 lease=rb(S/'imported_authority_lease.py');tree=ast.parse(lease);table={};ns={'sys':types.SimpleNamespace(modules=table,flags=sys.flags),'types':types,'Path':Path,'contextlib':contextlib,'hashlib':hashlib,'require':require}
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_loaded','_authenticate_loaded'} or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='AUTHORITY_CLASSES' for t in n.targets)]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(S/'imported_authority_lease.py'),'exec'),ns)
 prefix='tradingagents.research.onchain_replication.';helpers=('compiled_normalization_policy','compiled_small_lse');bodies={short:rb(S/(short+'.py')) for short in helpers};pins={str((S/(short+'.py')).relative_to(R)):hashlib.sha256(b).hexdigest() for short,b in bodies.items()};events=[];definition_imports=[]
 def safe_import(name,g=None,l=None,fromlist=(),level=0):
  require(level==0 and name in {'types','hashlib','json','os','stat','pathlib'},'unexpected definition import '+name);definition_imports.append(name);return builtins.__import__(name,g,l,fromlist,level)
 def get_module(short):
  key=prefix+short
  if key not in table:
   m=types.ModuleType(key);m.__file__=str(S/(short+'.py'));m.__dict__['__builtins__']=dict(vars(builtins),__import__=safe_import)
   exec(compile(bodies[short],m.__file__,'exec',dont_inherit=True,optimize=sys.flags.optimize),vars(m));table[key]=m
  return table[key]
 def import_selected(name,g=None,l=None,fromlist=(),level=0):
  require(name=='' and level==1,'unexpected preloader import');events.append(tuple(fromlist));result=types.SimpleNamespace()
  for short in fromlist:setattr(result,short,get_module(short) if short in helpers else None)
  return result
 def preload(body,hook=import_selected):
  scope={'__builtins__':dict(vars(builtins),__import__=hook)};exec(compile(funcs(body,{'_prepare_lease_modules'}),'actual-preloader','exec'),scope);return scope['_prepare_lease_modules']
 old=preload(original);new=preload(candidate);loaded=lambda:ns['_loaded'](R,pins);auth=lambda value:ns['_authenticate_loaded'](value,pins,R)
 get_module('compiled_normalization_policy');old(batched=True,grouped=True);initial=loaded();auth(initial);get_module('compiled_small_lse');late=loaded();auth(late)
 ck(set(late)-set(initial)=={prefix+'compiled_small_lse'} and late!=initial,'original omission independently reproduces genuine loaded roster change')
 table.clear();events.clear();new(batched=True,grouped=True,compiled=True);baseline=loaded();auth(baseline);get_module('compiled_small_lse');get_module('compiled_normalization_policy');ck(loaded()==baseline and len(baseline)==2,'selected preload fixes both helper identities before synthetic baseline')
 ck(set(definition_imports)=={'types','hashlib','json','os','stat','pathlib'},'actual helper definitions import only finite stdlib; no backend invoked')
 module=table[prefix+'compiled_small_lse'];fn=module.open_backend
 replacement=types.FunctionType(fn.__code__,vars(module),fn.__name__,fn.__defaults__,fn.__closure__);replacement.__module__=module.__name__;module.open_backend=replacement
 ck(loaded()!=baseline,'same-code different-function identity still detected');module.open_backend=fn
 changed_code=fn.__code__.replace(co_consts=fn.__code__.co_consts+('independent mutation',));saved_code=fn.__code__;fn.__code__=changed_code
 ck(loaded()!=baseline,'changed function code still detected')
 try:auth(loaded())
 except ValueError as e:ck('loaded code not bound' in str(e),'actual source authenticator refuses changed code')
 else:raise AssertionError('mutated code accepted')
 fn.__code__=saved_code
 alternate=types.ModuleType(module.__name__);alternate.__file__=module.__file__;table[module.__name__]=alternate;ck(loaded()!=baseline,'module substitution still detected');table[module.__name__]=module
 del table[module.__name__];ck(loaded()!=baseline,'module removal still detected');table[module.__name__]=module
 ck(loaded()==baseline,'restored exact immutable snapshot')
 for a,b in ((False,False),(True,False),(True,True)):
  events.clear();old(batched=a,grouped=b);oldseq=tuple(events);events.clear();new(batched=a,grouped=b);ck(tuple(events)==oldseq,'unselected import order unchanged '+str((a,b)))
 failure=ImportError('independent preload refused')
 def reject(name,g=None,l=None,fromlist=(),level=0):
  if 'compiled_small_lse' in fromlist:raise failure
  return import_selected(name,g,l,fromlist,level)
 try:preload(candidate,reject)(batched=True,grouped=True,compiled=True)
 except ImportError as e:ck(e is failure,'original import exception propagates before activation')
 else:raise AssertionError('preloader suppressed import failure')
 # Authenticate unchanged guard and caller source only; do not run Lease or scheduler.
 lease_class=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Lease');finger=next(n for n in lease_class.body if isinstance(n,ast.FunctionDef) and n.name=='_finger')
 ck("require(current == self.loaded, 'loaded module/function identity changed')" in ast.unparse(finger),'exact loaded equality refusal retained')
 interval=rb(S/'imported_authority_interval.py');ck(hashlib.sha256(interval).hexdigest()=='e61ef97f883ed9d27107f6316b774697b8949d83c313928150a0ae717b283f6f' and hashlib.sha256(lease).hexdigest()=='edd14622f3b5948a057e38bcce937c4080b9acc985c9a419fa0ac038aa158119','actual unchanged interval and lease source pins')
 batched=rb(S/'compact_mcm_batched.py');ck(hashlib.sha256(batched).hexdigest()=='e93d3b7073c8de5d1c3e7f5f30b55ba613b47a014f8fe449a0fe7e8a746941dd','all three actual full boundaries remain unchanged')
 correction=rb(F/'pilot31-terminal-locator-correction01-2026-10-11/CORRECTION01.json');ck(hashlib.sha256(correction).hexdigest()=='6b230b1a18667d06b01682ec50a19293d011ccb0ddae689eef5c8b5edc00911a','accepted separate actual locator correction')
 result={'schema_version':1,'decision':'ACCEPT_EXACT_PREACTIVATION_HELPER_PRELOAD_SOURCE','reviewer':'independent outcome16_release_review','candidate':refs[str((C/'real_pilot_import_caller.py').relative_to(R))]|{'path':str((C/'real_pilot_import_caller.py').relative_to(R))},'candidate_manifest':refs[str((C/'MANIFEST01.json').relative_to(R))]|{'path':str((C/'MANIFEST01.json').relative_to(R))},'checks':checks,'evidence':refs,'scope':'Exact one-file source and genuine selected caller preload before existing immutable Lease activation. Actual pure loaded/source authentication functions with isolated helper registry; no actual authority/Owner/backend constructed.','findings':[],'limits':['Original actual second-boundary traceback does not record the specific module delta. This source omission is independently reproducible, but is not a complete historical module census or universal architecture proof.','Only the two selected helper definitions are executed under restricted stdlib imports; other preloader imports are inert events. This is not full real-worker import closure execution.','No actual Lease/scheduler, native backend, arrays, data, scientific tests, claims, Git/network or private body inspected/executed.','No assurance about other late imports, indivisible-phase expiry, real timings, full capacity or scientific performance.','No Main installation or current entry/launch release. Root must first accept actual failed31 preservation, then install exact reviewed candidate and regenerate genuine complete numerical/source/registration bindings for a fresh authorized identity.']}
 with (P/'REVIEW01.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps({'decision':result['decision'],'checks':len(checks),'review_sha256':hashlib.sha256((P/'REVIEW01.json').read_bytes()).hexdigest(),'candidate_sha256':result['candidate']['sha256']},sort_keys=True))
except BaseException as e:
 with (P/'FAILED_CHECK01.json').open('x') as f:json.dump({'error':repr(e),'checks':checks,'evidence':refs},f,indent=2,sort_keys=True);f.write('\n')
 raise

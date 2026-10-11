import ast,builtins,hashlib,json,os,resource,signal,types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'pilot34-authority-fresh-serialization-candidate01-2026-10-11';S=R/'tradingagents/research/onchain_replication';refs={};checks=[]
def read(p):
 assert not ({'.git','.venv','research_artifacts','research_runs','keys','apis'}&set(p.parts))
 b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(v,n):
 checks.append({'name':n,'pass':bool(v)})
 if not v:raise AssertionError(n)
m=json.loads(read(D/'MANIFEST01.json'));ck(refs[str((D/'MANIFEST01.json').relative_to(R))]['sha256']=='96b7bb803d326d0abb623af9b278facd5925668cf638c66e4cf7051b2b8536ad','exact frozen candidate manifest')
for name,row in m['files'].items():b=read(D/name).encode();ck(hashlib.sha256(b).hexdigest()==row['sha256'] and len(b)==row['bytes'],'frozen textual member '+name)
old={n:read(S/n) for n in ('imported_authority_lease.py','original_import_preparation.py')};new={n:read(D/n) for n in old}
for name in new:
 if name=='imported_authority_lease.py':inverse=new[name].replace('from .provenance import current_canonical_bytes,thaw','from .provenance import canonical_bytes,thaw',1).replace('current=current_canonical_bytes(', 'current=canonical_bytes(',1)
 else:inverse=new[name].replace(',current_canonical_bytes\n','\n',1).replace('return current_canonical_bytes(', 'return canonical_bytes(',1)
 ck(inverse==old[name] and ast.dump(ast.parse(inverse),include_attributes=False)==ast.dump(ast.parse(old[name]),include_attributes=False),'full literal and AST inverse '+name)
 ck(new[name].count('current_canonical_bytes(')==1,'exact one changed serialization call '+name)
shared=read(F/'pilot34-shared-serialization-integration01-2026-10-11/provenance.py');ck(hashlib.sha256(shared.encode()).hexdigest()=='3bb5cf4a64126521ece009890b9f53c68bbd7db6e125c0401d885469188fa31e','unchanged shared helper prerequisite')
accepted=read(F/'pilot34-acceleration-candidates-source-review02-2026-10-11/SHARED_SOURCE_REVIEW01.json');ck(hashlib.sha256(accepted.encode()).hexdigest()=='ad5ffa1297a878d0b1848f7e04900ac11f005f9932ca025760485b12a1236ff5','accepted shared-helper domain review reused')
ns={'json':json};nodes=[n for n in ast.parse(shared).body if isinstance(n,ast.FunctionDef) and n.name in ('canonical_bytes','current_canonical_bytes','thaw')];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared-pure-stdlib','exec'),ns)
def method(text,name,env):
 node=next(n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name==name)
 out=dict(env);exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-extracted-callsite','exec'),out);return out[name]
def require(v,msg):
 if not v:raise ValueError(msg)
def outcome(f,obj):
 try:return ('ok',f(obj))
 except BaseException as e:return (type(e).__name__,str(e))
n=types.SimpleNamespace
# One actual _configuration payload with frozen nested data, fresh mutation,
# fallback refusal and restoration. No genuine Prepared object construction.
mapping={'nested':[1,2]};trace=[]
bound=n(record=types.MappingProxyType({'id':[1]}),context={'mode':'synthetic'},limits={'cap':3},_snapshots={Path('/synthetic/input'):(1,2)})
obj=n(_bound=bound,_run=n(directory=Path('/synthetic/run'),_claim_sha256='claim'),_job_input='job',_input='input',_selection=types.MappingProxyType(mapping),_source={'file':'sha'})
def thaw(v):trace.append(id(v));return ns['thaw'](v)
env={**ns,'thaw':thaw};fns=[method(v['original_import_preparation.py'],'_configuration',env) for v in (old,new)]
saved=None
for mode in ('initial','mutated','unsupported','restored'):
 if mode=='mutated':mapping['nested'].append(3)
 if mode=='unsupported':mapping['nested'].append(object())
 if mode=='restored':mapping['nested'][:]=[1,2]
 rows=[]
 for fn in fns:trace.clear();rows.append((outcome(fn,obj),list(trace)))
 ck(rows[0]==rows[1] and rows[0][1]==[id(bound.record),id(bound.context),id(bound.limits)],'configuration exact bytes/refusal and thaw order '+mode)
 if mode=='initial':saved=rows[0][0]
 if mode=='mutated':ck(rows[0][0]!=saved,'current nested mutation changes configuration bytes')
 if mode=='restored':ck(rows[0][0]==saved,'configuration restoration exact')
# Local import resolved only to extracted stdlib functions. The three stubs
# observe ordering; they confer no path/source/module/Lease authority.
def finger(text,mode):
 events=[];context=types.MappingProxyType({'nested':[1]});admission=n(source='source',registration_sha256='registration',inputs={'one':{'path':'input','sha256':'sha'}},experiment={'source_files':{'file':'sha'}},root=Path('/synthetic'))
 p=n(_configuration=lambda:(events.append('configuration') or b'prepared'));run=n(_claim_sha256='claim',admission=admission);o=n(prepared=p,execution=n(_execution_pin=b'execution'),run=run,bound=n(context=context),paths=('p',),fingerprints=('fp',),sources={'file':'sha'},loaded=('loaded',),_identity=lambda:events.append('identity'))
 o.configuration=ns['canonical_bytes']({'prepared':b'prepared'.hex(),'execution':b'execution'.hex(),'claim':'claim','source':'source','registration':'registration','inputs':admission.inputs,'sources':admission.experiment['source_files'],'runtime':context})
 if mode=='mutation':context['nested'].append(2)
 def fingerprint(path):events.append('fingerprint');return 'bad' if mode=='path' else 'fp'
 def loaded(root,sources):events.append('loaded');return ('bad',) if mode=='module' else ('loaded',)
 def importer(name,globals=None,locals=None,fromlist=(),level=0):
  assert name=='provenance' and level==1;return n(**ns)
 fn=method(text,'_finger',{'__builtins__':dict(vars(builtins),__import__=importer),'require':require,'fingerprint':fingerprint,'_loaded':loaded})
 return outcome(fn,o),events
for mode in ('plain','mutation','path','module'):
 a=finger(old['imported_authority_lease.py'],mode);b=finger(new['imported_authority_lease.py'],mode);ck(a==b,'finger exact fallback/refusal/observation order '+mode)
 ck(b[1]==({'plain':['configuration','identity','fingerprint','loaded'],'mutation':['configuration'],'path':['configuration','identity','fingerprint'],'module':['configuration','identity','fingerprint','loaded']}[mode]),'finger explicit refusal prefix '+mode)
result={'decision':'ACCEPT_EXACT_TWO_FRESH_SERIALIZATION_CALLS_SOURCE_ONLY','checks':checks,'references':refs,'candidate_sources':{name:m['files'][name]['sha256'] for name in old},'shared_provenance_sha256':hashlib.sha256(shared.encode()).hexdigest(),'findings':[],'scope':'Only Lease._finger current encoding and Prepared._configuration return encoding plus shared-helper imports. Construction baseline, existing thaws, source/body/module checks, scheduler60s, callback order and all other source are literal-inverse unchanged.','limits':['Shared provenance3bb5 is required but uninstalled; installed original module does not expose this helper.','No genuine Prepared/Lease/Target/Owner, actual paths/fingerprints/module compilation, graph/array/native/scientific import, live job or numerical execution.','Extracted methods with scalar inert metadata and observation stubs prove only the selected serialization/order seam.','Actual performance/memory/capacity, real loaded-source/caller/authority admission and installation remain unproved.','Inherited concurrent mutation, encoder instrumentation and allocation timing exceptions are not universally equivalent.','Financial timing leakage, return/cashflows, fees/funding and empirical validity were not tested.']}
with (P/'REVIEW01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((P/'REVIEW01.json').read_bytes()).hexdigest()},sort_keys=True))

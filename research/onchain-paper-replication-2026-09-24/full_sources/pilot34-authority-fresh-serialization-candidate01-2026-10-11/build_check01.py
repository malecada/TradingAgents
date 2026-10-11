import ast,builtins,copy,difflib,hashlib,json,resource,signal,types
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));signal.alarm(20)
R=Path.cwd();P=Path(__file__).resolve().parent;F=P.parent;S=R/'tradingagents/research/onchain_replication';G=F/'pilot34-shared-serialization-integration01-2026-10-11';checks=[];refs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes();assert len(b)<2097152;refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b.decode()
def ck(v,n):assert v,n;checks.append(n)
m=json.loads(read(G/'MANIFEST01.json'));prov=read(G/'provenance.py');ck(sha(prov.encode())==m['files']['provenance.py']['sha256']=='3bb5cf4a64126521ece009890b9f53c68bbd7db6e125c0401d885469188fa31e','exact shared provenance prerequisite')
read(F/'authority-current-pins-serialization-review02-2026-10-11/REPORT.md')
old={n:read(S/n) for n in ['imported_authority_lease.py','original_import_preparation.py']};new=dict(old)
a="    def _finger(self):\n        from .provenance import canonical_bytes,thaw\n";b="    def _finger(self):\n        from .provenance import current_canonical_bytes,thaw\n";ck(new['imported_authority_lease.py'].count(a)==1,'unique finger import');new['imported_authority_lease.py']=new['imported_authority_lease.py'].replace(a,b,1).replace('        current=canonical_bytes({\'prepared\':','        current=current_canonical_bytes({\'prepared\':',1)
new['original_import_preparation.py']=new['original_import_preparation.py'].replace('from .provenance import canonical_bytes,thaw,file_hash','from .provenance import canonical_bytes,thaw,file_hash,current_canonical_bytes',1).replace("        return canonical_bytes({'binding':thaw(bound.record)","        return current_canonical_bytes({'binding':thaw(bound.record)",1)
for n in new:
 (P/n).write_text(new[n])
 for suffix,x,y,px,py in [('patch',old[n],new[n],S/n,P/n),('inverse.patch',new[n],old[n],P/n,S/n)]:
  (P/(n+'.'+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=str(px.relative_to(R)),tofile=str(py.relative_to(R)))))
 if n=='imported_authority_lease.py':back=new[n].replace('from .provenance import current_canonical_bytes,thaw','from .provenance import canonical_bytes,thaw',1).replace('current=current_canonical_bytes(', 'current=canonical_bytes(',1)
 else:back=new[n].replace(',current_canonical_bytes\n','\n',1).replace('return current_canonical_bytes(', 'return canonical_bytes(',1)
 ck(back==old[n] and ast.dump(ast.parse(back))==ast.dump(ast.parse(old[n])),'exact literal/full AST inverse '+n)
ck(new['imported_authority_lease.py'].count('current_canonical_bytes(')==1 and new['original_import_preparation.py'].count('current_canonical_bytes(')==1,'exact two fresh callsite changes only')
ns={'json':json};nodes=[n for n in ast.parse(prov).body if isinstance(n,ast.FunctionDef) and n.name in ['canonical_bytes','thaw','current_canonical_bytes']];exec(compile(ast.Module(body=nodes,type_ignores=[]),'shared-provenance-functions','exec'),ns)
def require(v,msg):
 if not v:raise ValueError(msg)
def method(text,classname,name,env):
 klass=next(n for n in ast.parse(text).body if isinstance(n,ast.ClassDef) and n.name==classname);fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name==name);scope=dict(env);exec(compile(ast.Module(body=[fn],type_ignores=[]),'extracted-exact-method','exec'),scope);return scope[name]
# Confirm actual class name from source without importing it.
cls=next(n.name for n in ast.parse(old['original_import_preparation.py']).body if isinstance(n,ast.ClassDef) and any(isinstance(f,ast.FunctionDef) and f.name=='_configuration' for f in n.body))
def config_run(text,mutation=None):
 events=[];n=types.SimpleNamespace;bound=n(record={'a':[1]},context={'b':[2]},limits={'c':3},_snapshots={Path('/synthetic/file'):[1,2]});run=n(directory=Path('/synthetic/run'),_claim_sha256='claim');obj=n(_bound=bound,_run=run,_job_input='job',_input='input',_selection={'v':[4]},_source={'s':'hash'})
 if mutation:mutation(obj)
 def thaw(v):events.append('thaw');return ns['thaw'](v)
 f=method(text,cls,'_configuration',{**ns,'thaw':thaw})
 try:return ('bytes',f(obj),events)
 except Exception as e:return (type(e).__name__,str(e),events)
for label,mutation in [('plain',None),('fresh',lambda t:t._selection['v'].append(5)),('unsupported',lambda t:setattr(t,'_source',{'s':object()})),('frozen',lambda t:setattr(t,'_selection',types.MappingProxyType({'x':[1]}))),('nonfinite',lambda t:setattr(t,'_source',{'s':float('nan')}))]:
 ck(config_run(old['original_import_preparation.py'],mutation)==config_run(new['original_import_preparation.py'],mutation),'configuration bytes/refusal/thaw order '+label)
ck(config_run(new['original_import_preparation.py'])[1]!=config_run(new['original_import_preparation.py'],lambda t:t._selection['v'].append(5))[1],'fresh configuration mutation changes bytes')
def finger_run(text,mode):
 events=[];n=types.SimpleNamespace;run=n(_claim_sha256='claim',admission=n(source='commit',registration_sha256='registration',inputs={'a':{'path':'p','sha256':'h'}},experiment={'source_files':{'s':'h'}},root=Path('/synthetic')));prepared=n(_configuration=lambda:(events.append('configuration') or b'prepared'));e=n(_execution_pin=b'execution');context={'r':[1]};obj=n(execution=e,prepared=prepared,run=run,bound=n(context=context),paths=('p',),fingerprints=('finger',),sources={'s':'h'},loaded={'loaded':1},_identity=lambda:events.append('identity'))
 value={'prepared':b'prepared'.hex(),'execution':b'execution'.hex(),'claim':'claim','source':'commit','registration':'registration','inputs':run.admission.inputs,'sources':run.admission.experiment['source_files'],'runtime':context};obj.configuration=ns['canonical_bytes'](value)
 if mode=='mutation':context['r'].append(2)
 if mode=='unsupported':context['r'].append(object())
 if mode=='frozen':obj.bound.context=types.MappingProxyType(context)
 def fingerprint(p):events.append('fingerprint');return 'changed' if mode=='path' else 'finger'
 def loaded(root,sources):events.append('loaded');return {} if mode=='module' else {'loaded':1}
 def importer(name,globals=None,locals=None,fromlist=(),level=0):
  assert name=='provenance' and level==1
  return n(**ns)
 env={'__builtins__':dict(vars(builtins),__import__=importer),'require':require,'fingerprint':fingerprint,'_loaded':loaded}
 f=method(text,'Lease','_finger',env)
 try:return ('ok',f(obj),events)
 except Exception as error:return (type(error).__name__,str(error),events)
for mode in ['plain','mutation','unsupported','frozen','path','module']:
 ck(finger_run(old['imported_authority_lease.py'],mode)==finger_run(new['imported_authority_lease.py'],mode),'finger bytes/guard order/refusal '+mode)
ck(finger_run(new['imported_authority_lease.py'],'plain')[2]==['configuration','identity','fingerprint','loaded'],'all original guard observations retained in order')
result={'status':'PASS_EXACT_TWO_FRESH_SERIALIZATION_SEAMS','checks':checks,'references':refs,'candidate_sources':{n:sha(v.encode()) for n,v in new.items()},'prerequisite':{'path':str((G/'provenance.py').relative_to(R)),'sha256':sha(prov.encode())},'construction_baseline_changed':False,'genuine_authority_or_graph_execution':False,'performance_or_capacity_claim':None}
(P/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(checks),'candidate_sources':result['candidate_sources']}))

"""Independent finite source/expression review; no authority imports."""
import ast,copy,hashlib,json,resource,signal
from pathlib import Path
from types import SimpleNamespace,MappingProxyType
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
signal.alarm(20)
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
C=HERE.parent/'authority-serialization-single-pass01-2026-10-11'
refs={}
def read(p):
 raw=p.read_bytes();assert len(raw)<262144
 refs[str(p.relative_to(ROOT))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 return raw
m=json.loads(read(C/'MANIFEST.json'))
for name,entry in m['files'].items():
 raw=read(C/name);assert len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256']
for name,digest in m['current_source_sha256'].items():assert hashlib.sha256(read(ROOT/name)).hexdigest()==digest
old=read(C/'baseline.py');new=read(C/'candidate.py')
assert old==read(ROOT/'tradingagents/research/onchain_replication/imported_authority_lease.py')
expected=old
for s in [b'self.run.admission.inputs',b"self.run.admission.experiment['source_files']",b'self.bound.context']:
 assert expected.count(b'thaw('+s+b')')==2
 expected=expected.replace(b'thaw('+s+b')',s)
assert expected==new
compile(new,'<source-only>','exec')
prov=ast.parse(read(C/'provenance-baseline.py'))
defs=[n for n in prov.body if isinstance(n,ast.FunctionDef) and n.name in ('thaw','canonical_bytes','freeze')]
env={'json':json};exec(compile(ast.Module(body=defs,type_ignores=[]),'<extracted-stdlib-only>','exec'),env)
def expr(raw,method):
 cls=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='Lease')
 fn=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)
 node=next(n.value for n in fn.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='canonical_bytes' and isinstance(n.value.args[0],ast.Dict))
 return compile(ast.Expression(body=node),'<genuine-expression-synthetic-objects>','eval')
def make():
 admission=SimpleNamespace(inputs=json.loads('{"graph":{"path":"public/α","sha256":"abc"}}'),experiment=json.loads('{"source_files":{"source.py":"def"}}'),source='source',registration_sha256='registration')
 return SimpleNamespace(prepared=SimpleNamespace(_configuration=lambda:b'prepared'),run=SimpleNamespace(admission=admission,_claim_sha256='claim'),bound=SimpleNamespace(context=env['freeze']({'namespace':'scope','source_commit':'commit','runtime_hash':'hash'})))
def value(code,obj):
 try:return ('bytes',eval(code,env,{'self':obj,'execution':SimpleNamespace(_execution_pin=b'exec'),'e':SimpleNamespace(_execution_pin=b'exec')}))
 except (ValueError,TypeError) as error:return (type(error).__name__,str(error))
checks=0;counterexamples=[]
for method in ['__init__','_finger']:
 a,b=expr(old,method),expr(new,method);x=make();before=value(a,x);assert before==value(b,x);checks+=1
 for field,update in [('inputs',lambda x:x.run.admission.inputs['graph'].__setitem__('path','public/changed')),('sources',lambda x:x.run.admission.experiment['source_files'].__setitem__('source.py','new-hash')),('runtime',lambda x:setattr(x.bound,'context',env['freeze']({'namespace':'changed','source_commit':'commit','runtime_hash':'hash'})))]:
  x=make();before=value(a,x);update(x);assert value(a,x)==value(b,x)!=before;checks+=1
 for bad in [float('nan'),b'unsupported']:
  x=make();x.run.admission.inputs['graph']['path']=bad;assert value(a,x)==value(b,x) and value(a,x)[0]!='bytes';checks+=1
 backing={'namespace':'before'};x=make();x.bound.context=MappingProxyType(backing);before=value(a,x);backing['namespace']='after';assert value(a,x)==value(b,x)!=before;checks+=1
 # Out-of-domain custom dict changes earlier inputs while resolving a later field.
 class Effects(dict):
  def __getitem__(self,key):
   self.inputs['graph']['path']='changed-by-custom-getitem'
   return super().__getitem__(key)
 def exotic():
  x=make();m=Effects(x.run.admission.experiment);m.inputs=x.run.admission.inputs;x.run.admission.experiment=m;return x
 left=value(a,exotic());right=value(b,exotic());assert left!=right;checks+=1
 counterexamples.append({'method':method,'custom_dict_getitem_mutates_earlier_field':'old snapshots inputs before later getitem; new gets reference before getitem then traverses changed inputs','difference_confirmed':True})
author=json.loads(read(C/'RESULT.json'));assert author['status']=='PASS' and author['equivalence_checks']==104
result={'status':'PASS_FOCUSED_ADMITTED_DOMAIN_AND_CONFIRMED_LIMIT','checks':checks,'exact_literal_six_removals':True,'author_104_checks_reused_not_reexecuted':True,'expression_sites':['Lease.__init__','Lease._finger'],'custom_evaluation_order_counterexamples':counterexamples,'references':refs,'authority_objects_instantiated':False,'native_scientific_imports':False,'timing_measured':False}
(HERE/'RESULT01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print('PASS',checks,'focused checks; custom-type non-equivalence explicitly confirmed')

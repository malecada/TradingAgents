import ast,builtins,hashlib,json,os,pathlib,shutil,subprocess,sys,threading,types
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent;C=P.parent/'held-consumer-selected-transfer-worker-preparation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((C/'MANIFEST01.json').read_bytes());assert sha((C/'MANIFEST01.json').read_bytes())=='b03d11fb657ebcc8a9de36db25383f9d1e88bcc803128701c66124e0df205a70'
for r in m['members']:
 b=(C/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
v=json.loads((C/'SOURCE_INVENTORY01.json').read_bytes());rows=v['entries'];assert len(rows)==201 and len({r['target'] for r in rows})==201
for r in rows:
 b=pathlib.Path(r['origin']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
assert sum(r['package_source'] for r in rows)==150 and sum(r['bytes'] for r in rows)==3428116
rep=P/'owned-source-replica';rep.mkdir()
for name in ['held_score_consumer.py','resource_fixture.py','held_score_consumer.py.baseline04.txt','resource_fixture.py.baseline04.txt','check01.py','check02.py','check03.py']:shutil.copyfile(C/name,rep/name)
for name in ['check01.py','check02.py','check03.py']:
 p=subprocess.run([sys.executable,'-B',str(rep/name)],capture_output=True,timeout=30)
 (P/(name+'.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0,name
# Actual selected canonical reducer, not the author's simplified reducer.
io={};q=P.parent/'batch-output-exact-member-reader-candidate02-2026-10-03/owned_io.py';exec(compile(q.read_bytes(),str(q),'exec'),io)
doc=(P.parent/'batch-output-selected-transfer-preparation01-2026-10-03/archive_non_tail.py').read_text();ns={'CleanupFailure':io['CleanupFailure']}
exec(compile(ast.Module([n for n in ast.parse(doc).body if isinstance(n,ast.FunctionDef) and n.name in ('fatal','select','close_all')],[]),'actual-durable-reducer','exec'),ns)
consumer=ast.parse((C/'held_score_consumer.py').read_text())
checks=[]
for first,later in [(io['CleanupFailure']('uncertain'),MemoryError('later first fatal')),(MemoryError('original fatal'),KeyboardInterrupt('later fatal')),(ValueError('ordinary body'),io['CleanupFailure']('close uncertain'))]:
 calls=[]
 class Context:
  def close(self,primary):calls.append(primary);raise later
 context=Context();pkg=types.SimpleNamespace(archive_non_tail=types.SimpleNamespace(**ns,Context=Context))
 def imports(name,*args,**kwargs):
  if name=='':return pkg
  return builtins.__import__(name,*args,**kwargs)
 env={'threading':threading,'_LOCK':threading.RLock(),'__builtins__':{**vars(builtins),'__import__':imports}}
 exec(compile(ast.Module([n for n in consumer.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('require','_TransferWorker')],[]),'actual-worker-exit','exec'),env)
 worker=env['_TransferWorker'](None,{},'execution_job');worker.context=context;env['_WORKER']=worker
 try:worker.__exit__(type(first),first,None)
 except BaseException as e:assert e is ns['select'](first,later)
 else:raise AssertionError('failure suppressed')
 assert calls==[first] and env['_WORKER'] is None
 checks.append({'primary':type(first).__name__,'cleanup':type(later).__name__,'selected':type(ns['select'](first,later)).__name__,'closes':1})
# No output publication or transfer occurs from merely validating policies/source closure.
fns={n.name:n for n in consumer.body if isinstance(n,ast.FunctionDef)}
for name in ['_policy','_transfer_scope','_transfer_outputs','_transfer_closure']:
 text=ast.unparse(fns[name]);assert not any(x in text for x in ['Popen(','.dispatch(','.write_json(','.start('])
fixture=ast.parse((C/'resource_fixture.py').read_text());functions={n.name:n for n in fixture.body if isinstance(n,ast.FunctionDef)}
original=next(n for n in ast.parse((C/'resource_fixture.py.baseline04.txt').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='execute');candidate=functions['_execute_original'];candidate.name='execute';assert ast.dump(original)==ast.dump(candidate)
result={'status':'accepted-source-checks-only','candidate_manifest':sha((C/'MANIFEST01.json').read_bytes()),'source_count':201,'package_count':150,'implementation_bytes':3428116,'admission_pins':206,'registered_outputs':10,'author_tests':16,'additional_canonical_reducer_cases':checks,'numerical_execute_AST_unchanged':True,'actual_authority_or_network':False,'future_source_commit':None}
(P/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))

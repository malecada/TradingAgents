"""Actual extracted lifecycle/metadata seams with explicitly synthetic stand-ins."""
import ast,builtins,hashlib,json,os,threading,unittest,types
from pathlib import Path
P=Path(__file__).parent
SOURCE=P/'held_score_consumer.py'
def defs(names):
 t=ast.parse(SOURCE.read_text());return ast.Module([n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names],type_ignores=[])
def namespace(names,pkg=None):
 ns=dict(Path=Path,json=json,hashlib=hashlib,os=os,threading=threading,_WORKER=None,_LOCK=threading.RLock())
 if pkg:
  def imports(name,*args,**kw):
   if name=='':return pkg
   return builtins.__import__(name,*args,**kw)
  ns['__builtins__']={**vars(builtins),'__import__':imports}
 exec(compile(defs(names),str(SOURCE),'exec'),ns);return ns
class Checks(unittest.TestCase):
 def test_closure(self):
  ns=namespace({'require','_transfer_closure'});code={f'code/{i}.py':'0'*64 for i in range(201)};pkg=dict(list(code.items())[:150]);aux={f'meta/{i}.json':'1'*64 for i in range(5)}
  value=dict(schema_version=1,kind='selected-held-transfer-source-closure-v1',implementation_source_count=201,package_count=150,source_files=code,package_files=pkg,auxiliary_source_files=aux)
  self.assertIs(ns['_transfer_closure'](value,code|aux,set(pkg)),code)
  for change in ({'implementation_source_count':199},{'package_count':148},{'schema_version':True},{'auxiliary_source_files':dict(list(aux.items())[:-1])},{'extra':True}):
   with self.assertRaises(ValueError):ns['_transfer_closure'](value|change,code|aux,set(pkg))
  for registered in (code,code|aux|{'extra.py':'0'*64}):
   with self.assertRaises(ValueError):ns['_transfer_closure'](value,registered,set(pkg))
 def test_lifecycle_firstfatal(self):
  for body_error,close_error in [(None,None),(ValueError('body'),None),(MemoryError('first'),OSError('close')),(ValueError('body'),MemoryError('close'))]:
   calls=[]
   class Context:
    def __init__(self,run):self.run=run;self.closed=False
    def check(self):calls.append('check')
    def close(self,primary):
     calls.append(('close',primary));self.closed=True
     if close_error:raise close_error
     if primary:raise primary
   def select(a,b):
    if a is None:return b
    if isinstance(a,MemoryError):return a
    if isinstance(b,MemoryError):return b
    return a
   pkg=types.SimpleNamespace(archive_non_tail=types.SimpleNamespace(Context=Context,select=select),archive_dispatch=types.SimpleNamespace(non_tail_context=lambda run,**kw:Context(run)))
   ns=namespace({'require','_TransferWorker'},pkg)
   run=types.SimpleNamespace(directory=P/'never-created',_published_outputs={})
   ns['transfer_preflight']=lambda *a,**kw:({'population_input':'population'}, {'never.json'})
   worker=ns['_TransferWorker'](run,{},'execution_job');self.assertIs(worker.__enter__(),worker);self.assertIs(ns['_WORKER'],worker)
   expected=body_error if isinstance(body_error,MemoryError) else close_error or body_error
   if expected:
    with self.assertRaises(type(expected)) as caught:worker.__exit__(type(body_error),body_error,None)
    self.assertIs(caught.exception,expected)
   else:self.assertFalse(worker.__exit__(None,None,None))
   self.assertIsNone(ns['_WORKER']);self.assertEqual(len([c for c in calls if isinstance(c,tuple)]),1)
 def test_publication_before_birth(self):
  calls=[];pkg=types.SimpleNamespace(archive_non_tail=object(),archive_dispatch=types.SimpleNamespace(non_tail_context=lambda *a,**kw:calls.append('BIRTH')))
  ns=namespace({'require','_TransferWorker'},pkg);run=types.SimpleNamespace(directory=P/'never-created',_published_outputs={'used.json':'0'*64})
  ns['transfer_preflight']=lambda *a,**kw:({'population_input':'population'},{'used.json'})
  with self.assertRaisesRegex(ValueError,'already reserved'):ns['_TransferWorker'](run,{},'execution_job').__enter__()
  self.assertEqual(calls,[]);self.assertIsNone(ns['_WORKER'])
 def test_concurrent_scope(self):
  pkg=types.SimpleNamespace(archive_non_tail=object(),archive_dispatch=object());ns=namespace({'require','_TransferWorker'},pkg);ns['_WORKER']=object()
  with self.assertRaisesRegex(ValueError,'another'):ns['_TransferWorker'](None,{},'execution_job').__enter__()
 def test_dependency_and_order(self):
  tree=ast.parse(SOURCE.read_text());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='transfer_preflight')
  imports=[n.module for n in ast.walk(f) if isinstance(n,ast.ImportFrom)];self.assertIn('lifecycle',imports);self.assertNotIn('runner',imports)
  source=ast.unparse(f);self.assertIn('type(run) is ResearchRun',source);self.assertIn('matching_owner._source',source);self.assertIn('matching_owner._guard',source)
  self.assertLess(source.index('_transfer_closure('),source.index('release==expected') if 'release==expected' in source else source.index('release == expected'))
  fixture=ast.parse((P/'resource_fixture.py').read_text());wrap=next(n for n in fixture.body if isinstance(n,ast.FunctionDef) and n.name=='execute');body=ast.unparse(wrap)
  self.assertLess(body.index('preflight('),body.index('transfer_worker('));self.assertNotIn('start(',body)
 def test_full_baseline_math_and_unaffected_ast(self):
  for name,changed in [('held_score_consumer.py',{'_policy','preflight','consume'}),('resource_fixture.py',{'selection','preflight','execute'})]:
   old=ast.parse((P/(name+'.baseline04.txt')).read_text());new=ast.parse((P/name).read_text());olddefs={n.name:n for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newdefs={n.name:n for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
   for key,node in olddefs.items():
    if key not in changed:self.assertEqual(ast.dump(node),ast.dump(newdefs[key]),name+':'+key)
   if name=='resource_fixture.py':
    original=newdefs['_execute_original'];original.name='execute';self.assertEqual(ast.dump(original),ast.dump(olddefs['execute']))
   else:
    policy=newdefs['_policy'];policy.body.pop(0);self.assertEqual(ast.dump(policy),ast.dump(olddefs['_policy']))
    pre=newdefs['preflight'];pre.body=[n for n in pre.body if not (isinstance(n,ast.If) and '_worker_current' in ast.unparse(n))];self.assertEqual(ast.dump(pre),ast.dump(olddefs['preflight']))
    consume=newdefs['consume']
    for n in consume.body:
     if isinstance(n,ast.With):n.body=[x for x in n.body if not isinstance(x,ast.If)]
    self.assertEqual(ast.dump(consume),ast.dump(olddefs['consume']))
if __name__=='__main__':unittest.main()

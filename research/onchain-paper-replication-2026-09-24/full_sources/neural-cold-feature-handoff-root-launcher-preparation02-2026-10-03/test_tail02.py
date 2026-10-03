import ast,copy,importlib.util,json,pathlib,sys,tempfile,unittest
P=pathlib.Path(__file__).parent;path=pathlib.Path(sys.argv.pop(1));s=importlib.util.spec_from_file_location('candidate',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def terminal(ns):
 fn=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='execute');outer=next(n for n in fn.body if isinstance(n,ast.Try));tail=outer.finalbody
 if hasattr(m,'finish_tail'):
  start=next(i for i,n in enumerate(tail) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='finish_tail' for x in ast.walk(n)))
 else:start=next(i for i,n in enumerate(tail) if isinstance(n,ast.Try) and any(isinstance(c,ast.Name) and c.id=='disposition' for c in ast.walk(n)))
 exec(compile(ast.Module(body=copy.deepcopy(tail[start:]),type_ignores=[]),'actual-terminal-tail','exec'),ns)
class Tests(unittest.TestCase):
 def case(self,late=None,write_fail=(),primary=None):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'source';root.mkdir();out=pathlib.Path(d)/'out';out.mkdir();calls=[];writes=[]
   def watch(*args,**kw):
    calls.append(kw)
    if len(calls)==2 and late is not None:raise late
    return {'files':0,'allocated_bytes':0}
   original=m.write
   def write(directory,name,data):
    writes.append(name)
    if name in write_fail:raise OSError('synthetic marker unavailable')
    return original(directory,name,data)
   ns=dict(m.__dict__);ns.update(directory=out,root=root,identity='synthetic-tail-only',q={'phase':'materialize','source':'b'*40},request_reference={'synthetic':True},process=None,observed={},primary=primary,result={'synthetic_success_observation':True},root_watch=watch,write=write,cleanup_types=[])
   def retain(e):ns['primary']=m.select(ns['primary'],e)
   ns['retain']=retain
   # Actual new function globals must use explicitly qualified test operations.
   saved={k:m.__dict__[k] for k in ('root_watch','write')};m.root_watch=watch;m.write=write
   try:terminal(ns)
   finally:m.__dict__.update(saved)
   files={p.name:p.read_bytes() for p in out.iterdir()};return ns['primary'],files,writes,calls
 def test_exact_old_final_watch_counterexample(self):
  error=ValueError('synthetic final-tail floor refusal');selected,files,_,_=self.case(late=error)
  self.assertIs(selected,error);self.assertIn('observation.json',files)
  self.assertTrue(any(n in files for n in ('failure.json','late-failure.json','tail-write-failure.json')),'success observation left without additive revocation')
 def test_final_fatal_exact_identity(self):
  for f in (MemoryError('first'),KeyboardInterrupt(),SystemExit(7)):
   selected,files,_,_=self.case(late=f);self.assertIs(selected,f);self.assertIn('failure.json',files)
 def test_failed_marker_fallback(self):
  f=MemoryError('first');selected,files,writes,_=self.case(late=f,write_fail={'failure.json'})
  self.assertIs(selected,f);self.assertIn('late-failure.json',files);self.assertIn('failure.json',writes)
 def test_all_marker_failures_stay_pending_nonzero(self):
  f=MemoryError('first');selected,files,writes,_=self.case(late=f,write_fail={'failure.json','late-failure.json','tail-write-failure.json'})
  self.assertIs(selected,f);self.assertIn('tail-intent.json',files);self.assertNotIn('tail-complete.json',files)
 def test_success_requires_last_seal(self):
  selected,files,_,_=self.case();self.assertIsNone(selected);self.assertIn('tail-complete.json',files);self.assertTrue(json.loads(files['observation.json'])['requires_root_tail_complete'])
 def test_already_fatal_survives_later_tail_failure(self):
  f=SystemExit(9);selected,files,_,_=self.case(late=MemoryError('later'),primary=f);self.assertIs(selected,f);self.assertIn('failure.json',files)
if __name__=='__main__':unittest.main(verbosity=2)

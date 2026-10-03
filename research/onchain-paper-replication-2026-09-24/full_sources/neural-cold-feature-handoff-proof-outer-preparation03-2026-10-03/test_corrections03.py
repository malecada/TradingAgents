"""Source-boundary tests only; fixture records never confer authority."""
import ast,importlib.util,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;S=Path(os.environ.get('SOURCE_DIR',P));sys.path.insert(0,str(S))
import proof_raw01 as raw
import proof_release01 as release
owned=P.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py'
node=next(n for n in ast.parse(owned.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='CleanupFailure');env={};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-CleanupFailure','exec'),env);Cleanup=env['CleanupFailure']
class Corrections(unittest.TestCase):
 def test_cleanup_then_first_memory_fatal(self):
  first=Cleanup('uncertain');later=MemoryError('fatal')
  reducer=getattr(raw,'preserve_owned',lambda a,b,c:raw.preserve(a,b))
  self.assertIs(reducer(first,later,Cleanup),later)
 def test_all_mixed_fatal_orders(self):
  reducer=getattr(raw,'preserve_owned',lambda a,b,c:raw.preserve(a,b))
  for fatal in (MemoryError(),RecursionError(),KeyboardInterrupt(),SystemExit()):
   with self.subTest(kind=type(fatal).__name__):
    self.assertIs(reducer(Cleanup(),fatal,Cleanup),fatal)
    self.assertIs(reducer(fatal,Cleanup(),Cleanup),fatal)
    self.assertIs(reducer(fatal,MemoryError(),Cleanup),fatal)
 def test_owned_parent_fsync_close(self):
  fn=getattr(raw,'sync_owned_directory',None);self.assertIsNotNone(fn)
  first=MemoryError('sync');later=OSError('close');calls=[]
  def op(path,flags):calls.append('open');return 123
  def sync(fd):calls.append('sync');raise first
  def close(fd):calls.append('close');raise later
  original=raw.os;raw.os=SimpleNamespace(open=op,fsync=sync,close=close,O_RDONLY=0,O_DIRECTORY=0,O_NOFOLLOW=0)
  try:
   with self.assertRaises(MemoryError) as caught:fn(Path('/pure-fixture'),Cleanup)
   self.assertIs(caught.exception,first);self.assertEqual(calls,['open','sync','close'])
  finally:raw.os=original
 def test_supervisor_uses_authenticated_cleanup_type(self):
  text=(S/'proof_supervise01.py').read_text()
  self.assertIn("owned=canonical_cleanup(root,sources['tradingagents/research/onchain_replication/owned_io.py'])",text)
  self.assertIn('primary=preserve_owned(primary,error,owned.CleanupFailure)',text)
  self.assertIn('sync_owned_directory(directory.parent,owned.CleanupFailure)',text)
  self.assertNotIn('finally:os.close(fd)',text)
 def test_original_prior_fragment_refuses_forgery(self):
  # Exact source branch, same counterexample as independent reviewer. No earlier
  # actual source/Git/runtime gate is replaced or claimed to have run.
  tree=ast.parse((S/'proof_release01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_release_context','check_release') and any(isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='prior' for x in n.body))
  start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='prior');code=compile(ast.Module(body=fn.body[start:start+2],type_ignores=[]),'actual-prior-branch','exec')
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)
   def put(path,value,kind='metadata'):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw.canonical(value));return raw.ref(root,path,kind=kind)
   population=put('fake/population.json',{'fake':True},'document');material=put('fake/future.json',{'inputs':{'population':{'path':population['path'],'sha256':population['sha256']}}},'document');auth=put('fake/auth.json',{'proof':{'kind':'materialized-inputs-only','scientific_completion':False,'future_inputs':material}})
   accepted=put(raw.OUTER+raw.IDENTITIES['materialize']+'/accepted.json',{'status':'accepted','phase':'materialize','source':'b'*40,'release':{'unverified':True},'authentication':auth})
   wait=put('proof_supervise/'+raw.IDENTITIES['materialize']+'/exit.json',{'status':'accepted','controller_exit_code':0,'controller_pid_absent':True,'accepted_receipt':accepted,'release':{'unverified':True},'source':'c'*40,'controller_pid':2147483646,'supervisor_pid':2147483647})
   env=dict(vars(release));env.update(root=root,phase='compare',release={'source':'a'*40,'prior_materialization':{'accepted':accepted,'wait':wait}},job={'payload':{'representation_jobs':{'cold-proof':{}}}},experiment={'inputs':{'population':{'path':population['path'],'sha256':population['sha256']}}})
   with self.assertRaises((ValueError,KeyError,FileNotFoundError)):exec(code,env)
 def test_reduced_materialization_membership(self):
  names=getattr(raw,'MATERIAL_INPUTS',None);self.assertIsNotNone(names)
  self.assertEqual(len(names),43);self.assertTrue({'population','cold_proof','plan','future_execution_job'}<=names);self.assertEqual(len([n for n in names if n.startswith('graph-')]),19)
 def test_authentication_chain_is_recomputed(self):
  tree=ast.parse((S/'proof_release01.py').read_text());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
  historical=functions['authenticated_materialization'];current=functions['authenticate_prior']
  calls={ast.unparse(n.func) for n in ast.walk(historical) if isinstance(n,ast.Call)}
  self.assertTrue({'_release_context','authenticate','closure','runtime_gate.check'}<=calls)
  self.assertIn('authenticated_materialization',ast.unparse(current));self.assertIn('_evolution_tree',ast.unparse(current));self.assertIn("'retained-materialization'",ast.unparse(historical))
  self.assertIn("set(new['inputs'])",ast.unparse(functions['_registration_evolution']))
if __name__=='__main__':unittest.main(verbosity=2)

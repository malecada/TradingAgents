import ast,hashlib,json,os,stat,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).resolve().parent
# Extract actual pure functions; no research/numerical import, no fake authority.
def load():
 t=ast.parse((H/'archive_non_tail.py').read_bytes());names={'require','encode','validate_policy','project','select','fatal','close_all','read_file','write_file'}
 ns=dict(json=json,hashlib=hashlib,os=os,stat=stat,sys=sys,Path=Path,META=131072,BLOCK=32768)
 class CleanupFailure(BaseException):pass
 ns['CleanupFailure']=CleanupFailure
 exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'actual-candidate-extract','exec'),ns);return ns
class Tests(unittest.TestCase):
 def setUp(self):self.m=load()
 def policy(self):return dict(schema_version=1,kind='non-tail-durable-population-v1',category='non-tail-original-members',namespace='new-only',deadline_seconds=60,max_rounded_bytes=1000000,max_commands=64,max_parts=32,max_control_bytes=33554432,part_bytes=128,receipt_output='receipt.json',terminal_output='terminal.json',slots=[dict(graph='ab'*32,role='score-batches',max_bytes=10000,max_members=32)])
 def test_policy(self):self.assertEqual(self.m['validate_policy'](self.policy()),self.policy())
 def test_all_roles_finite(self):
  for role in ('score-batches','mcm-output','graph-artifact'):
   p=self.policy();p['slots'][0]['role']=role;self.m['validate_policy'](p)
 def test_no_events_or_bool(self):
  for key,val in [('kind','archive-dispatch-v1'),('category','events'),('max_parts',True),('namespace','.')]:
   p=self.policy();p[key]=val
   with self.assertRaises(ValueError):self.m['validate_policy'](p)
 def test_duplicate_slot(self):
  p=self.policy();p['slots']*=2
  with self.assertRaises(ValueError):self.m['validate_policy'](p)
 def test_no_refund_project(self):
  p=self.policy();old=dict(rounded_bytes=32768,commands=1,parts=1)
  got=self.m['project'](old,1,p);self.assertEqual(got,dict(rounded_bytes=65536,commands=2,parts=2));self.assertEqual(old['rounded_bytes'],32768)
  p['max_commands']=1
  with self.assertRaises(ValueError):self.m['project'](old,1,p)
 def test_actual_fd_write_read(self):
  with tempfile.TemporaryDirectory() as d:
   fd=os.open(d,os.O_DIRECTORY);self.addCleanup(os.close,fd);self.m['write_file'](fd,'intent.json',b'{}\n');self.assertEqual(self.m['read_file'](fd,'intent.json'),b'{}\n')
   with self.assertRaises(FileExistsError):self.m['write_file'](fd,'intent.json',b'{}\n')
   with self.assertRaises(ValueError):self.m['write_file'](fd,'.',b'{}\n')
 def test_fatal_write_close_once(self):
  with tempfile.TemporaryDirectory() as d:
   fd=os.open(d,os.O_DIRECTORY);self.addCleanup(os.close,fd);a=MemoryError('first');real=os.close;seen=[]
   def close(x):seen.append(x);real(x);raise OSError('close')
   with patch.object(os,'write',side_effect=a),patch.object(os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as got:self.m['write_file'](fd,'failed.json',b'{}')
   self.assertIs(got.exception,a);self.assertEqual(len(seen),1);self.assertTrue((Path(d)/'failed.json').exists())
 def test_cleanup_firstfatal(self):
  first=SystemExit('first');seen=[]
  def bad():seen.append(1);raise MemoryError('second')
  with self.assertRaises(SystemExit) as got:self.m['close_all']([bad,lambda:seen.append(2)],first)
  self.assertIs(got.exception,first);self.assertEqual(seen,[1,2])
 def test_inverse_sources(self):
  root=H.parents[3]
  for n in ('archive_dispatch.py','archive_transport.py'):
   original=(root/'tradingagents/research/onchain_replication'/n).read_bytes();candidate=(H/n).read_bytes();self.assertTrue(candidate.startswith(original))
   self.assertEqual(ast.dump(ast.parse(original)),ast.dump(ast.parse(candidate[:len(original)])))
if __name__=='__main__':unittest.main()

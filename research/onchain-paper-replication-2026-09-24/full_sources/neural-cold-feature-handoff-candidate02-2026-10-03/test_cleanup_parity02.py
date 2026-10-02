"""Narrow actual source cleanup composition, file controls and AST parity."""
import ast,copy,json,os,sys,tempfile,types,unittest
from pathlib import Path
from test_review_boundaries01 import module,function,invoke_fragment,caller_case
HERE=Path(__file__).resolve().parent
class Cleanup(unittest.TestCase):
 def case(self,primary,marker_error,close_error):
  f=function('compact_cold_features.py','prepare');block=copy.deepcopy(next(n for n in f.body if isinstance(n,ast.Try) and n.handlers));block.body=[ast.Raise(exc=ast.Name(id='injected',ctx=ast.Load()),cause=None)]
  wrapper=ast.FunctionDef(name='invoke',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[block],decorator_list=[])
  cold=module('cold_files');seen=[]
  def marker(*args):seen.append('marker');raise marker_error
  def close():seen.append('close');raise close_error
  ns=dict(injected=primary,owner=types.SimpleNamespace(poisoned=False,_transition=types.SimpleNamespace(release=close)),claimed=True,
   cold_files=types.SimpleNamespace(write_once=marker,preserve=cold.preserve),directory=Path('/synthetic-not-accessed'),inode=(1,1),
   canonical_bytes=lambda x:b'{}',KIND='synthetic',policy={'max_metadata_bytes':100},sys=sys)
  invoke_fragment([wrapper],ns)
  caught=None
  try:ns['invoke']()
  except BaseException as e:caught=e
  return caught,seen,ns['owner']
 def test_original_fatal_survives_marker_and_release_failure(self):
  first=MemoryError('first');caught,seen,owner=self.case(first,OSError('marker'),KeyboardInterrupt('release'))
  self.assertIs(caught,first);self.assertEqual(seen,['marker','close']);self.assertTrue(owner.poisoned)
  received,trace,_=caller_case(caught);self.assertIs(received,first);self.assertEqual(trace,[])
 def test_first_marker_fatal_survives_later_release_fatal(self):
  first=MemoryError('marker');caught,seen,owner=self.case(ValueError('primary'),first,SystemExit('release'))
  self.assertIs(caught,first);self.assertEqual(seen,['marker','close'])
 def test_ordinary_cleanup_error_remains_fail_stop(self):
  caught,seen,owner=self.case(ValueError('primary'),OSError('marker'),OSError('release'))
  received,trace,kind=caller_case(caught);self.assertIsInstance(received,kind);self.assertEqual(trace,[])
 def test_parent_fsync_fatal_survives_parent_close_fatal(self):
  cold=module('cold_files')
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'child';original_sync=cold.os.fsync;original_close=cold.os.close;first=MemoryError('sync');seen=[]
   def sync(fd):seen.append('sync');raise first
   def close(fd):seen.append('close');original_close(fd);raise KeyboardInterrupt('close')
   cold.os.fsync=sync;cold.os.close=close
   try:
    with self.assertRaises(MemoryError) as caught:cold.durable_birth(path)
    self.assertIs(caught.exception,first);self.assertEqual(seen,['sync','close']);self.assertEqual(list(path.iterdir()),[])
   finally:cold.os.fsync=original_sync;cold.os.close=original_close
 def test_valid_birth_and_extension_preserve_original_pins(self):
  cold=module('cold_files')
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);old=root/'old';old.mkdir();(old/'one').write_bytes(b'original')
   bounds=dict(max_files=10,max_directories=10,max_total_bytes=10000,max_file_bytes=10000,max_depth=4,chunk_bytes=32)
   original=cold.capture(root,('old',),bounds);path=root/'new';inode=cold.durable_birth(path)
   bodies={'start.json':b'start','complete.json':b'complete'}
   for name,raw in bodies.items():cold.write_once(path,inode,name,raw,100)
   expanded=cold.extend(original,path,inode,bodies)
   self.assertEqual(cold.original_subset(expanded,original.roots),(original.directories,original.files));expanded.check(full=True)
   with self.assertRaises(FileExistsError):cold.durable_birth(path)
class Parity(unittest.TestCase):
 def test_unchanged_archive_and_native_numeric_composition(self):
  old=ast.parse((HERE/'compact_cold_features.py.baseline01').read_text());new=ast.parse((HERE/'compact_cold_features.py').read_text())
  def calls(t,name):return [ast.dump(n,include_attributes=False) for n in ast.walk(t) if isinstance(n,ast.Call) and ast.unparse(n.func)==name]
  for name in ('archive_owner_seal.check_content','compact_stage.verify','m._NativeMap','PreparedFeatures'):
   with self.subTest(call=name):self.assertEqual(calls(old,name),calls(new,name))
 def test_unmodified_cold_feature_numeric_methods(self):
  old=ast.parse((HERE/'compact_cold_features.py.baseline01').read_text());new=ast.parse((HERE/'compact_cold_features.py').read_text())
  a=next(n for n in old.body if isinstance(n,ast.ClassDef) and n.name=='_Features');b=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='_Features')
  self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
 def test_payload_diff_is_only_selected_cold_failstop(self):
  old=ast.parse((HERE/'job_payload.py.baseline01').read_text());new=ast.parse((HERE/'job_payload.py').read_text())
  class Remove(ast.NodeTransformer):
   def visit_If(self,n):
    if "job.get('compact_cold_handoff_input') is not None"==ast.unparse(n.test):return None
    return self.generic_visit(n)
  self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(Remove().visit(new),include_attributes=False))
if __name__=='__main__':unittest.main(verbosity=2)

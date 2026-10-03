import ast,importlib.util,pathlib,stat,tempfile,types,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent;s=importlib.util.spec_from_file_location('candidate',P/'launcher02.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_canonical_actual_class_priority(self):
  src=P.parent/'neural-cold-feature-handoff-proof-source-composition04-2026-10-03/source-bodies/tradingagents/research/onchain_replication/owned_io.py'
  node=next(n for n in ast.parse(src.read_bytes()).body if isinstance(n,ast.ClassDef) and n.name=='CleanupFailure');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-canonical-class-only','exec'),ns);cls=ns['CleanupFailure'];uncertain=cls();fatal=MemoryError('real')
  self.assertIs(m.select(uncertain,fatal,(cls,)),fatal);self.assertIs(m.select(fatal,uncertain,(cls,)),fatal)
  # Identical spelling without authenticated type identity gains no exemption.
  other=type('CleanupFailure',(BaseException,),{});foreign=other();self.assertIs(m.select(foreign,fatal,(cls,)),foreign)
 def test_active_entry_headroom(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   with patch.object(m.shutil,'disk_usage',return_value=types.SimpleNamespace(free=100*m.GIB)):
    for i in range(24):(p/str(i)).write_bytes(b'')
    self.assertEqual(m.root_watch(p)['files'],24);(p/'25').write_bytes(b'')
    with self.assertRaises(ValueError):m.root_watch(p)
    self.assertEqual(m.root_watch(p,reserve_bytes=3*65536,reserve_entries=3)['files'],25)
 def test_active_allocated_headroom(self):
  class Entry:
   def lstat(self):return types.SimpleNamespace(st_mode=stat.S_IFREG|0o600,st_nlink=1,st_size=1,st_blocks=24*1024**2//512)
  directory=types.SimpleNamespace(iterdir=lambda:iter([Entry()]))
  with patch.object(m.shutil,'disk_usage',return_value=types.SimpleNamespace(free=100*m.GIB)):
   with self.assertRaises(ValueError):m.root_watch(directory)
   self.assertEqual(m.root_watch(directory,reserve_bytes=3*65536,reserve_entries=3)['allocated_bytes'],24*1024**2)
 def test_marker_bound(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)
   with self.assertRaises(ValueError):m.tail_write(p,'too-large.json',{'text':'x'*8192})
   self.assertFalse((p/'too-large.json').exists())
 def test_partial_success_seal_is_revoked(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'source';root.mkdir();out=pathlib.Path(d)/'out';out.mkdir();first=MemoryError('seal-fsync');real=m.write
   def write(directory,name,data):
    real(directory,name,data)
    if name=='tail-complete.json':raise first
   with patch.object(m,'write',side_effect=write),patch.object(m,'root_watch',return_value={'files':0,'allocated_bytes':0}):
    got=m.finish_tail(out,root,'test-only',{'phase':'materialize','source':'a'*40},{},None,{},None,{'synthetic':True},())
   self.assertIs(got,first);self.assertTrue((out/'tail-complete.json').exists());self.assertTrue((out/'failure.json').exists())
 def test_multiple_errors_preserve_first_fatal(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'source';root.mkdir();out=pathlib.Path(d)/'out';out.mkdir();first=MemoryError('first');second=KeyboardInterrupt('later');real=m.write
   def write(directory,name,data):
    if name=='error.txt':raise second
    return real(directory,name,data)
   with patch.object(m,'write',side_effect=write),patch.object(m,'root_watch',return_value={'files':0,'allocated_bytes':0}):got=m.finish_tail(out,root,'test-only',{'phase':'materialize','source':'a'*40},{},None,{},first,None,())
   self.assertIs(got,first);self.assertTrue((out/'failure.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)

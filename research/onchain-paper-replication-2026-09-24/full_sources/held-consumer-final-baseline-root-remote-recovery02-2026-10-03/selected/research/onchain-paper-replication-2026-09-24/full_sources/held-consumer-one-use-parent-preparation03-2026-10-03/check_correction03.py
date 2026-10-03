import ast,importlib.util,json,os,stat,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('parent03',R/'launch_success01.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class Correct(unittest.TestCase):
 def test_actual_launch_log_loop_rejects_original_redirect(self):
  source=ast.parse((R/'launch_success01.py').read_bytes());launch=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='launch');loop=next(n for n in ast.walk(launch) if isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple) and [x.value for x in n.iter.elts if isinstance(x,ast.Constant)]==['stdout.log','stderr.log'])
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);original=root/'owned';original.mkdir();pin=p.directory_identity(original);foreign=root/'foreign';foreign.mkdir();original.rename(root/'retained');original.symlink_to(foreign,target_is_directory=True)
   ns={'open_log':p.open_log,'directory':original,'directory_pin':pin,'fds':[]}
   with self.assertRaises(ValueError):exec(compile(ast.Module([loop],[]),'actual-log-loop','exec'),ns)
   assert ns['fds']==[] and list(foreign.iterdir())==[]
 def test_actual_reservation_parent_entry_synced(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);attempt=root/'attempt';attempt.mkdir();osfsync=os.fsync;seen=[]
   def sync(fd):s=os.fstat(fd);seen.append((s.st_ino,stat.S_ISDIR(s.st_mode)));osfsync(fd)
   with patch.object(p.os,'fsync',side_effect=sync):
    p.directory_identity(attempt);reserved=attempt/'fixed-qualified-identity';reserved.mkdir();p.directory_identity(reserved)
   assert seen==[(attempt.stat().st_ino,True),(root.stat().st_ino,True),(reserved.stat().st_ino,True),(attempt.stat().st_ino,True)],seen
 def test_atomic_logs_real_fd_join_and_final_bytes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);pin=p.directory_identity(root);fd=p.open_log(root,'stdout.log',pin)
   try:
    os.write(fd,b'qualified utility log');os.fsync(fd);row=p.log_join(root,'stdout.log',fd,pin,final=True);assert row['bytes']==21 and row['inode']==(root/'stdout.log').stat().st_ino
    with self.assertRaises(FileExistsError):p.open_log(root,'stdout.log',pin)
   finally:os.close(fd)
 def test_replaced_logs_never_receive_fd_writes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);pin=p.directory_identity(root);fd=p.open_log(root,'stdout.log',pin);(root/'stdout.log').rename(root/'retained-original');(root/'stdout.log').write_bytes(b'foreign')
   try:
    os.write(fd,b'owned');assert (root/'stdout.log').read_bytes()==b'foreign' and (root/'retained-original').read_bytes()==b'owned'
    with self.assertRaises(ValueError):p.log_join(root,'stdout.log',fd,pin)
   finally:os.close(fd)
 def test_real_three_fd_cleanup_on_original_log_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);pin=p.directory_identity(root);first=MemoryError('first fsync');close=os.close;closed=[]
   def close_later(fd):close(fd);closed.append(fd);raise SystemExit('later closed')
   with patch.object(p.os,'fsync',side_effect=first),patch.object(p.os,'close',side_effect=close_later):
    with self.assertRaises(MemoryError) as caught:p.open_log(root,'stderr.log',pin)
   assert caught.exception is first and len(closed)==len(set(closed))==3
 def test_reservation_sync_fatal_still_closes_both(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);first=MemoryError('first fsync');close=os.close;closed=[]
   def close_later(fd):close(fd);closed.append(fd);raise OSError('later close')
   with patch.object(p.os,'fsync',side_effect=first),patch.object(p.os,'close',side_effect=close_later):
    with self.assertRaises(MemoryError) as caught:p.directory_identity(root)
   assert caught.exception is first and len(closed)==len(set(closed))==2
 def test_nonfinite_name_and_source_default_refuse(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);pin=p.directory_identity(root)
   with self.assertRaises(ValueError):p.open_log(root,'../outside',pin)
  with self.assertRaises(ValueError):p.prepared(R/'REQUEST_TEMPLATE03.json','0'*64)
  assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
if __name__=='__main__':unittest.main()

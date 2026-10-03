import ast,hashlib,importlib.util,json,os,signal,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
p=load(R/'launch_success01.py','parent02');semantic=load(R/'held_outcome02.py','semantic02');assert H((R/'held_outcome02.py').read_bytes())==p.PARSER_SHA
class Correction(unittest.TestCase):
 def test_exact_post_tail_original_globals(self):
  release=json.loads((R/'release-unreleased01.json').read_bytes());raw=(p.CAP/'fixture_tools/raw_receipts01.py').read_bytes();assert H(raw)==release['source_files']['fixture_tools/raw_receipts01.py']
  function=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='authenticate_post_tail')
  candidate=ast.parse((R/'launch_success01.py').read_bytes());f=next(n for n in candidate.body if isinstance(n,ast.FunctionDef) and n.name=='finish_check');assignment=next(n for n in f.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ns' for t in n.targets))
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);tree=root/'fixture_outer'/'qualified-post-tail';tree.mkdir(parents=True);info=root.stat();limits={'disk_floor_bytes':10*p.GIB,'storage_budget':{'limits':{'max_allocated_bytes':100,'max_logical_bytes':100,'max_entries':10}}}
   value={'disk_floor_bytes':10*p.GIB,'disk_free_bytes':11*p.GIB,'excludes_own_file':True,'remaining_final_file_allowance':65536,'observation':{'root':str(root),'root_device':info.st_dev,'root_inode':info.st_ino,'allocated_bytes':0,'logical_file_bytes':0,'entries':0}}
   body=json.dumps(value,sort_keys=True).encode();(tree/'post-tail-storage.json').write_bytes(body);reader=semantic.Reader(root)
   context={'Path':Path,'GIB':p.GIB,'require':p.require,'sha':p.sha,'reader':reader};exec(compile(ast.Module([assignment],[]),'actual-parent-ns','exec'),context);ns=context['ns'];exec(compile(ast.Module([function],[]),'actual-original-posttail','exec'),ns)
   out=ns['authenticate_post_tail'](root,'qualified-post-tail',limits);assert out['sha256']==H(body);reader.recheck()
 def test_unexpected_wait_fatal_does_not_skip_kill_reap(self):
  first=MemoryError('wait60 fatal');calls=[]
  class Process:
   pid=12345
   def poll(self):calls.append('poll');return None
   def wait(self,timeout):
    calls.append('wait'+str(timeout))
    if timeout==60:raise first
    return -9
  with patch.object(p,'ticks',return_value='known'),patch.object(p.os,'killpg',side_effect=lambda pid,sig:calls.append('signal'+str(sig))):
   with self.assertRaises(MemoryError) as caught:p.reap_controller(Process(),'known')
  assert caught.exception is first and calls==['poll','signal15','wait60','signal9','wait5'],calls
 def test_every_reap_independent_and_original_fatal(self):
  first=MemoryError('poll fatal');calls=[]
  class Process:
   pid=12345
   def poll(self):calls.append('poll');raise first
   def wait(self,timeout):calls.append('wait'+str(timeout));raise SystemExit('later wait')
  with patch.object(p,'ticks',side_effect=OSError('missing pid')):
   with self.assertRaises(MemoryError) as caught:p.reap_controller(Process(),'known')
  assert caught.exception is first and calls==['poll','wait60','wait5'],calls
 def test_anchor_refuses_symlink_and_same_mode_replacement(self):
  for symbolic in (False,True):
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);original=root/'attempt';original.mkdir();foreign=root/'foreign';foreign.mkdir();anchor=p.directory_identity(original);original.rename(root/'retained')
    if symbolic:original.symlink_to(foreign,target_is_directory=True)
    else:foreign.rename(original)
    with self.assertRaises((ValueError,OSError)):p.write(original,'receipt.json',{'qualified':True},anchor)
    assert not (original/'receipt.json').exists() and not (root/'retained'/'receipt.json').exists()
 def test_atomic_file_parent_sync_and_no_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);anchor=p.directory_identity(root);fsync=os.fsync;seen=[]
   def sync(fd):seen.append(os.fstat(fd).st_mode);fsync(fd)
   with patch.object(p.os,'fsync',side_effect=sync):p.write(root,'receipt.json',{'qualified':True},anchor)
   assert len(seen)==2 and json.loads((root/'receipt.json').read_bytes())=={'qualified':True}
   with self.assertRaises(FileExistsError):p.write(root,'receipt.json',{'qualified':False},anchor)
 def test_atomic_write_firstfatal_three_actual_closes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);anchor=p.directory_identity(root);first=MemoryError('write first');realclose=os.close;closed=[]
   def close(fd):realclose(fd);closed.append(fd);raise OSError('closed later')
   with patch.object(p.os,'write',side_effect=first),patch.object(p.os,'close',close):
    with self.assertRaises(MemoryError) as caught:p.write(root,'receipt.json',{},anchor)
   assert caught.exception is first and len(closed)==len(set(closed))==3
 def test_selected_real_cleanup_type_does_not_mask_fatal(self):
  # Qualified pure reducer control binds the exact accepted parser class.
  p.SELECTED_CLEANUP_TYPES=(semantic.CleanupFailure,)
  uncertain=semantic.CleanupFailure('owned close uncertain');fatal=MemoryError('first fatal');assert p.select(uncertain,fatal) is fatal
  with self.assertRaises(MemoryError) as caught:p.cleanup([lambda:(_ for _ in ()).throw(fatal)],uncertain)
  assert caught.exception is fatal
 def test_uninstalled_still_refuses(self):
  with self.assertRaises(ValueError):p.prepared(R/'REQUEST_TEMPLATE02.json',H((R/'REQUEST_TEMPLATE02.json').read_bytes()))
  assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
if __name__=='__main__':unittest.main()

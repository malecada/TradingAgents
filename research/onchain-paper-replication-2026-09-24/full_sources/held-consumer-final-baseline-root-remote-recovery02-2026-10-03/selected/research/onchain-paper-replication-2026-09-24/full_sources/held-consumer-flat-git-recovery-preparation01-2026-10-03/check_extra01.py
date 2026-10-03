"""Additional real-child, cleanup, namespace and storage qualification."""
import hashlib,json,os,stat,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
import check_git01 as base
import git_recovery01 as m
import bounded_git_fd01 as b
class Extra(unittest.TestCase):
 setUp=base.Checks.setUp
 joined=base.Checks.joined
 def test_real_child_timeout_killed_and_reaped(self):
  v,s,_=self.joined();real=subprocess.Popen;children=[]
  def child(*args,**kwargs):
   p=real([sys.executable,'-B','-c','import time;time.sleep(30)'],**kwargs);children.append(p);return p
  with patch.object(b.subprocess,'Popen',child),patch.object(b.time,'monotonic',side_effect=[0,20]),self.assertRaises(ValueError):b.git(s.check(),['cat-file','--batch'])
  self.assertEqual(len(children),1);p=children[0];self.assertIsNotNone(p.poll());self.assertTrue(all(stream.closed for stream in (p.stdin,p.stdout,p.stderr)))
 def test_original_fatal_survives_poll_free_cleanup(self):
  v,s,_=self.joined();m.populate(s,v);realclose=b.selectors.DefaultSelector.close;first=MemoryError('read first');calls=[];realread=b.os.read
  def later(obj):calls.append('selector.close');realclose(obj);raise SystemExit('later close')
  # Popen performs an internal errpipe read; allow it, then fail selector stdout.
  realpopen=b.subprocess.Popen;children=[];started=[]
  def popen(*args,**kwargs):p=realpopen(*args,**kwargs);children.append(p);started.append(1);return p
  def read(fd,n):
   if started:raise first
   return realread(fd,n)
  with patch.object(b.subprocess,'Popen',popen),patch.object(b.os,'read',read),patch.object(b.selectors.DefaultSelector,'close',later),self.assertRaises(MemoryError) as found:b.git(s.check(),['--git-dir=.','cat-file','--batch'],(self.commit+'\n').encode())
  self.assertIs(found.exception,first);self.assertEqual(calls,['selector.close']);self.assertTrue(all(p.poll() is not None and all(t.closed for t in (p.stdin,p.stdout,p.stderr)) for p in children))
 def test_request_and_stdout_and_stderr_bounds(self):
  v,s,_=self.joined();m.populate(s,v)
  with self.assertRaises(ValueError):b.git(s.check(),['cat-file','--batch'],b'x'*65537)
  with self.assertRaises(ValueError):b.git(s.check(),['--git-dir=.','cat-file','--batch'],(self.commit+'\n').encode(),cap=16)
  real=subprocess.Popen;children=[]
  def child(*args,**kwargs):
   p=real([sys.executable,'-B','-c',"import os;os.write(2,b'x'*70000)"],**kwargs);children.append(p);return p
  with patch.object(b.subprocess,'Popen',child),self.assertRaises(ValueError):b.git(s.check(),['cat-file','--batch'])
  self.assertTrue(all(p.poll() is not None for p in children))
 def test_selected_child_environment_and_held_fd(self):
  v,s,_=self.joined();m.populate(s,v);real=subprocess.Popen;seen=[]
  def popen(*args,**kwargs):seen.append((args,kwargs));return real(*args,**kwargs)
  with patch.object(b.subprocess,'Popen',popen):s.object(self.commit,'commit')
  args,k=seen[0];self.assertEqual(k['cwd'],'/proc/self/fd/'+str(s.check()));self.assertEqual(k['pass_fds'],(s.check(),));self.assertEqual(set(k['env']),{'PATH','LC_ALL','GIT_CONFIG_NOSYSTEM','GIT_CONFIG_GLOBAL','GIT_NO_LAZY_FETCH','GIT_NO_REPLACE_OBJECTS','GIT_TERMINAL_PROMPT'});self.assertEqual(k['env']['GIT_CONFIG_GLOBAL'],'/dev/null');self.assertIn('protocol.allow=never',args[0]);self.assertIn('--no-replace-objects',args[0])
 def test_symlink_recovered_object_refused(self):
  v,s,_=self.joined();name=next(k for k in v.maps['capsule'] if k.startswith('.git/objects/'));p=self.flat/v.maps['capsule'][name];retained=self.root/'retained-body';p.rename(retained);p.symlink_to(retained)
  with self.assertRaises(ValueError):m.populate(s,v)
 def test_fd_created_object_replacement_keeps_foreign_bytes(self):
  v,s,_=self.joined();real=os.open;foreign=self.root/'foreign';foreign.write_bytes(b'keep');once=[]
  def race(path,flags,*args,**kwargs):
   fd=real(path,flags,*args,**kwargs)
   if flags&os.O_CREAT and len(str(path))==38 and not once:
    once.append(1);os.rename(path,self.root/'owned-created-retained',src_dir_fd=kwargs['dir_fd']);os.link(foreign,path,dst_dir_fd=kwargs['dir_fd'])
   return fd
  with patch.object(m.os,'open',race),self.assertRaises(ValueError):m.populate(s,v)
  self.assertEqual(foreign.read_bytes(),b'keep');self.assertGreater((self.root/'owned-created-retained').stat().st_size,0)
 def test_logical_and_allocated_store_bound(self):
  v,s,_=self.joined();m.populate(s,v);allocated=s.storage();self.assertGreaterEqual(allocated,s.bytes)
  with patch.object(m,'TOTAL',allocated-1),self.assertRaises(ValueError):s.storage()
 def test_wrong_object_type_and_missing_blob(self):
  v,s,_=self.joined();m.populate(s,v)
  with self.assertRaises(ValueError):s.object(self.tree,'commit')
  with self.assertRaises(ValueError):s.object(self.commit+':absent','blob')
 def test_budget_deadline_and_aggregate_outputs(self):
  v,s,_=self.joined();s.deadline=0
  with self.assertRaises(ValueError):s.query(['cat-file','--batch'],b'')
  s.deadline=float('inf');s.returned=m.TOTAL+1
  with self.assertRaises(ValueError):s.budget()
if __name__=='__main__':unittest.main(verbosity=2)

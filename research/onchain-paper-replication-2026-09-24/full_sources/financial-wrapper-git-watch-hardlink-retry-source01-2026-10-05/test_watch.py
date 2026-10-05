"""Five focused owned-metadata tests; no Git operation, network or claim."""
import ast,difflib,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
P=Path(__file__).parent
BASE=P.parent/'financial-wrapper-serialized-storage-source-remote01-2026-10-05'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
OLD=load('original_watch',BASE/'watch01.py');NEW=load('candidate_watch',P/'watch01.py')
def require(ok,why):
 if not ok:raise ValueError(why)
class Watch(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.parent=Path(self.tmp.name);self.root=self.parent/'owned';self.root.mkdir();self.objects=self.root/'fresh.git'/'objects';self.objects.mkdir(parents=True);self.file=self.objects/'body';self.file.write_bytes(b'1234')
 def timing(self,callback):return patch.object(NEW,'time',SimpleNamespace(monotonic=time.monotonic,sleep=callback))
 def test_exact_inverse_caps_and_owned_active_caller(self):
  for name in ('watch01.py','recover01.py'):
   lines=(P/(name+'.ndiff')).read_text().splitlines(True)
   self.assertEqual(''.join(difflib.restore(lines,1)),(BASE/name).read_text());self.assertEqual(''.join(difflib.restore(lines,2)),(P/name).read_text())
  self.assertEqual(OLD.POLICY,NEW.POLICY)
  old=next(n for n in ast.parse((BASE/'watch01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='census')
  new=next(n for n in ast.parse((P/'watch01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='census')
  # Undo only new flag validation/forwarding: retry algorithm must be exact.
  new.args=old.args
  for n in ast.walk(new):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_sample':n.keywords=[]
  self.assertEqual(ast.dump(new,include_attributes=False),ast.dump(old,include_attributes=False))
  tree=ast.parse((P/'recover01.py').read_text());git=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='git')
  calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='watch'];active=[n for n in calls if n.keywords]
  self.assertEqual(len(active),1);self.assertEqual(ast.unparse(active[0]),"watch(owned_fetch_objects=Path(cwd) / 'objects' if args and args[0] == 'fetch' and (Path(cwd) == HERE / 'fresh-serialized-storage-source01.git') and (child.poll() is None) else None)")
  loop=next(n for n in ast.walk(git) if isinstance(n,ast.While) and ast.unparse(n.test)=='poller.get_map()');self.assertIn(active[0],list(ast.walk(loop)))
  readback=next(n for n in ast.walk(git) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='genuine child OS limit readback')
  self.assertLess(readback.lineno,active[0].lineno)
  for flag in (False,0,1,'active',self.parent):
   with self.subTest(flag=flag),self.assertRaises(ValueError):NEW.census(self.root,owned_fetch_objects=flag)
 def test_transient_actual_links_initial_and_rejoin_red_green(self):
  # Initial internal alias: original refuses immediately; new active context discards it.
  alias=self.objects/'alias';os.link(self.file,alias)
  with self.assertRaises(ValueError) as caught:OLD.census(self.root)
  self.assertNotIsInstance(caught.exception,OLD.ChangingTree)
  delays=[]
  def retire(delay):delays.append(delay);alias.unlink()
  with self.timing(retire):result=NEW.census(self.root,owned_fetch_objects=self.objects)
  self.assertEqual(delays,[.1]);self.assertEqual(result['complete_attempts'],2);self.assertEqual(result['logical_bytes'],4);self.assertEqual(result['members'],4);self.assertEqual(self.file.stat().st_nlink,1)
  # Rejoin alias created outside owned root: no directory fingerprint masks file check.
  for module,active in ((OLD,False),(NEW,True)):
   outside=self.parent/'outside';created=False;real_disk=module.shutil.disk_usage;delays=[]
   def disk(path):
    nonlocal created
    if not created:os.link(self.file,outside);created=True
    return real_disk(path)
   def retire_rejoin(delay):delays.append(delay);outside.unlink()
   with patch.object(module,'shutil',SimpleNamespace(disk_usage=disk)),patch.object(module,'time',SimpleNamespace(monotonic=time.monotonic,sleep=retire_rejoin)):
    if active:
     result=module.census(self.root,owned_fetch_objects=self.objects);self.assertEqual(result['complete_attempts'],2);self.assertEqual(result['logical_bytes'],4);self.assertEqual(delays,[.1])
    else:
     with self.assertRaises(ValueError) as caught:module.census(self.root)
     self.assertNotIsInstance(caught.exception,module.ChangingTree);self.assertEqual(delays,[])
   if outside.exists():outside.unlink()
 def test_persistent_links_strict_default_and_three_active_attempts(self):
  for external in (False,True):
   alias=(self.parent if external else self.objects)/'alias';os.link(self.file,alias)
   try:
    waits=[]
    with self.timing(waits.append):
     for label in ('pre-call','post-drain'):
      with self.subTest(label=label,external=external),self.assertRaises(ValueError) as caught:NEW.census(self.root)
      self.assertNotIsInstance(caught.exception,NEW.ChangingTree)
    self.assertEqual(waits,[])
    attempts=[];sample=NEW._sample
    def counted(*args,**kwargs):attempts.append(1);return sample(*args,**kwargs)
    with self.timing(waits.append),patch.object(NEW,'_sample',counted),self.assertRaisesRegex(ValueError,'three bounded attempts') as caught:NEW.census(self.root,owned_fetch_objects=self.objects)
    self.assertIsInstance(caught.exception.__cause__,NEW.ChangingTree);self.assertEqual(len(attempts),3);self.assertEqual(waits,[.1,.1])
   finally:alias.unlink()
 def test_oversize_and_zero_link_immediate_fatal(self):
  with self.file.open('r+b') as f:f.truncate(NEW.POLICY['file']+1)
  alias=self.objects/'alias';os.link(self.file,alias);waits=[]
  with self.timing(waits.append),self.assertRaises(ValueError) as caught:NEW.census(self.root,owned_fetch_objects=self.objects)
  self.assertNotIsInstance(caught.exception,NEW.ChangingTree);self.assertEqual(waits,[]);alias.unlink();self.file.write_bytes(b'1234')
  # Rejoin size remains fatal before any hardlink retry classification.
  real_disk=NEW.shutil.disk_usage;grown=False
  def disk(path):
   nonlocal grown
   if not grown:
    with self.file.open('r+b') as f:f.truncate(NEW.POLICY['file']+1)
    grown=True
   return real_disk(path)
  with self.timing(waits.append),patch.object(NEW,'shutil',SimpleNamespace(disk_usage=disk)),self.assertRaises(ValueError) as caught:NEW.census(self.root,owned_fetch_objects=self.objects)
  self.assertNotIsInstance(caught.exception,NEW.ChangingTree);self.assertEqual(waits,[]);self.file.write_bytes(b'1234')
  original_lstat=Path.lstat
  def zero(path,*args,**kwargs):
   s=original_lstat(path,*args,**kwargs)
   if path==self.file:
    values={name:getattr(s,name) for name in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks')};values['st_nlink']=0;return SimpleNamespace(**values)
   return s
  with self.timing(waits.append),patch.object(Path,'lstat',zero),self.assertRaises(ValueError) as caught:NEW.census(self.root,owned_fetch_objects=self.objects)
  self.assertNotIsInstance(caught.exception,NEW.ChangingTree);self.assertEqual(waits,[])
 def test_outside_objects_hardlink_remains_strict(self):
  outside=self.root/'selected-file';outside.write_bytes(b'1234');alias=self.root/'selected-alias';os.link(outside,alias);waits=[]
  with self.timing(waits.append),self.assertRaises(ValueError) as caught:NEW.census(self.root,owned_fetch_objects=self.objects)
  self.assertNotIsInstance(caught.exception,NEW.ChangingTree);self.assertEqual(waits,[])
 def test_actual_original_child_four_mib_limit(self):
  # Execute only the exact source-defined limits function in a disposable Python child.
  tree=ast.parse((P/'recover01.py').read_text());limits=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='limits')
  body=ast.unparse(limits)
  code="import os,sys,resource,json\nFILE=4*1024**2\nready_write=int(sys.argv[1])\nencode=lambda value:json.dumps(value).encode()\ndef require(ok,why):\n if not ok:raise ValueError(why)\n"+body+"\nlimits()\ntry:\n with open(sys.argv[2],'wb',buffering=0) as f:\n  f.write(b'x'*(FILE+1));f.write(b'x')\nexcept OSError as error:\n print(json.dumps({'errno':error.errno,'size':os.stat(sys.argv[2]).st_size,'limits':list(resource.getrlimit(resource.RLIMIT_FSIZE))}))\nelse:raise AssertionError('oversize write unexpectedly succeeded')\n"
  rd,wr=os.pipe()
  try:
   child=subprocess.Popen([sys.executable,'-B','-c',code,str(wr),str(self.parent/'bounded-child')],pass_fds=(wr,),stdout=subprocess.PIPE,stderr=subprocess.PIPE);os.close(wr);wr=None
   ready=json.loads(os.read(rd,512));out,err=child.communicate(timeout=10);self.assertEqual(child.returncode,0,err.decode());result=json.loads(out)
   self.assertEqual(ready,{'pid':child.pid,'fsize':[4*1024**2]*2});self.assertEqual(result,{'errno':27,'size':4*1024**2,'limits':[4*1024**2]*2})
  finally:
   os.close(rd)
   if wr is not None:os.close(wr)
  self.assertFalse({'torch','numpy','scipy','pandas'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)

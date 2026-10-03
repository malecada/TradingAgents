"""Independent assertions using labelled author's tiny real-Git fixture setup only."""
import copy,hashlib,json,os,stat,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-flat-git-recovery-preparation01-2026-10-03';sys.path.insert(0,str(P));raw=(P/'check_git01.py').read_text();old="dir=P));observations=[]";assert raw.count(old)==1;adapted=raw.replace(old,"dir=REVIEW_OUTPUT));observations=[]");(O/'fixture_setup03.location-only.txt').write_text(adapted);ns={'__name__':'source_fixture_only','__file__':str(P/'check_git01.py'),'REVIEW_OUTPUT':O};exec(compile(adapted,str(P/'check_git01.py'),'exec'),ns);m=ns['m'];base=ns['Checks'];import bounded_git_fd01 as g
observations={}
class Independent(unittest.TestCase):
 setUp=base.setUp
 joined=base.joined
 def test_exact_actual_known_source_worksheets(self):
  e=json.loads((P/'EXPECTED_ORIGINAL_TEMPLATE01.json').read_bytes());h=json.loads((O.parent/'held-consumer-historical-admission-closure-investigation01-2026-10-03/COPY_PLAN01.json').read_bytes());c=json.loads((O.parent/'held-consumer-original-git-runtime-root-binding01-2026-10-03/ORIGINAL_GIT_RUNTIME_BINDING01.json').read_bytes());self.assertEqual(e['historical']['lookups'],h['logical_committed_lookups']);self.assertEqual(e['historical']['claims'],h['claims']);self.assertEqual(e['selected_c6']['rows'],c['source_paths']);self.assertIsNone(e['current'])
 def test_real_Git_from_recovered_bytes_and_no_live_donor(self):
  real=m.a.read
  def read(root,name,*a,**k):
   self.assertFalse(Path(root).is_relative_to(self.cap));self.assertFalse(Path(root).is_relative_to(self.donor));return real(root,name,*a,**k)
  with patch.object(m.a,'read',read):
   v,s,q=self.joined();objects=m.populate(s,v);got=m.verify_lookups(s,self.commit,self.expected,v,True);self.assertEqual(got,self.expected);self.assertEqual(len(objects),4)
   with self.assertRaises(ValueError):s.object(self.parent,'commit')
  observations['real_joins']={'files':len(got),'object_files':len(objects),'missing_real_parent_refused':True,'donor_reads':False}
 def test_only_archival_original_modes_metadata(self):
  with patch.object(m.os,'chmod',side_effect=AssertionError('chmod forbidden')),patch.object(m.os,'fchmod',side_effect=AssertionError('fchmod forbidden')):
   v,s,_=self.joined();m.populate(s,v);m.verify_lookups(s,self.commit,self.expected,v,True)
  self.assertTrue(all(stat.S_IMODE((s.path/n).stat().st_mode)==0o600 for n in s.files));self.assertEqual(stat.S_IMODE(self.output.stat().st_mode),0o700)
 def test_complete_current_roster_and_literal_paths_refuse(self):
  v,s,_=self.joined();m.populate(s,v)
  for rows in (self.expected[:1],self.expected+[self.expected[0]],list(reversed(self.expected))):
   if len(rows)==2:self.assertEqual(len(m.verify_lookups(s,self.commit,rows,v,True)),2)
   else:
    with self.assertRaises(ValueError):m.verify_lookups(s,self.commit,rows,v,True)
  for name in ('*','alpha\n'+self.commit,'../alpha'):
   rows=copy.deepcopy(self.expected);rows[0]['path']=name
   with self.assertRaises((ValueError,KeyError)):m.verify_lookups(s,self.commit,rows,v,True)
 def test_recovered_external_is_not_ignored(self):
  meta=json.loads((self.flat/'external-metadata.json').read_bytes());flat=next(iter(meta['flat_members'].values()));(self.flat/flat).write_bytes(b'changed external');v=m.FlatView(self.flat);v.begin();self.addCleanup(v.close)
  try:m.chain(v,self.bundle,self.request,self.qsha,self.csha,self.rsha)
  except BaseException as e:self.assertIn(type(e).__name__,('ValueError','CleanupFailure'))
  else:self.fail('external role ignored')
  self.assertEqual(list(self.output.iterdir()),[])
 def test_hash_type_oid_and_current_mode_refusal(self):
  v,s,_=self.joined();m.populate(s,v)
  for field,value in [('object','1'*40),('bytes',0),('sha256','e'*64),('git_mode','100755')]:
   rows=copy.deepcopy(self.expected);rows[0][field]=value
   with self.assertRaises(ValueError):m.verify_lookups(s,self.commit,rows,v,True)
  with self.assertRaises(ValueError):s.object(self.tree,'commit')
  with self.assertRaises(ValueError):s.object(self.commit+':missing','blob')
 def test_exact_heldFD_child_and_inert_environment(self):
  v,s,_=self.joined();m.populate(s,v);real=g.subprocess.Popen;seen=[]
  def popen(*a,**k):seen.append((a,k));return real(*a,**k)
  with patch.object(g.subprocess,'Popen',popen):s.object(self.commit,'commit')
  args,k=seen[0];self.assertEqual(k['cwd'],'/proc/self/fd/'+str(s.check()));self.assertEqual(k['pass_fds'],(s.check(),));self.assertEqual(k['env'],{'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'});self.assertEqual(args[0][:7],['git','-c','protocol.allow=never','--no-replace-objects','--literal-pathspecs','--git-dir=.','cat-file'])
 def test_actual_timeout_child_reaped_closed(self):
  v,s,_=self.joined();real=g.subprocess.Popen;children=[]
  def popen(*a,**k):p=real([sys.executable,'-B','-c','import time;time.sleep(30)'],**k);children.append(p);return p
  with patch.object(g.subprocess,'Popen',popen),patch.object(g.time,'monotonic',side_effect=[0,20]),self.assertRaises(ValueError):g.git(s.check(),['cat-file','--batch'])
  self.assertEqual(len(children),1);self.assertIsNotNone(children[0].poll());self.assertTrue(all(x.closed for x in (children[0].stdin,children[0].stdout,children[0].stderr)))
 def test_firstfatal_original_over_later_SystemExit(self):
  v,s,_=self.joined();m.populate(s,v);realpop=g.subprocess.Popen;realread=g.os.read;realclose=g.selectors.DefaultSelector.close;children=[];first=MemoryError('original read')
  def pop(*a,**k):p=realpop(*a,**k);children.append(p);return p
  def read(fd,n):
   if children:raise first
   return realread(fd,n)
  def close(selector):realclose(selector);raise SystemExit('later cleanup')
  with patch.object(g.subprocess,'Popen',pop),patch.object(g.os,'read',read),patch.object(g.selectors.DefaultSelector,'close',close),self.assertRaises(MemoryError) as e:g.git(s.check(),['--git-dir=.','cat-file','--batch'],(self.commit+'\n').encode())
  self.assertIs(e.exception,first);self.assertTrue(all(p.poll() is not None and all(x.closed for x in (p.stdin,p.stdout,p.stderr)) for p in children))
 def test_resource_refusals_and_no_unsupported_git_commands(self):
  v,s,_=self.joined();m.populate(s,v)
  with self.assertRaises(ValueError):s.query(['fetch','irrelevant'])
  with self.assertRaises(ValueError):s.query(['cat-file','--batch'],b'x'*65537)
  with self.assertRaises(ValueError):g.git(s.check(),['--git-dir=.','cat-file','--batch'],(self.commit+'\n').encode(),cap=8)
  allocated=s.storage()
  with patch.object(m,'TOTAL',allocated-1),self.assertRaises(ValueError):s.storage()
  s.returned=m.TOTAL+1
  with self.assertRaises(ValueError):s.budget()
  s.returned=0;s.deadline=0
  with self.assertRaises(ValueError):s.budget()
 def test_originalFD_regularfile_replacement(self):
  v,s,_=self.joined();real=os.open;foreign=self.root/'foreign';foreign.write_bytes(b'keep');once=[]
  def replace(name,flags,*a,**k):
   fd=real(name,flags,*a,**k)
   if flags&os.O_CREAT and len(str(name))==38 and not once:once.append(fd);os.rename(name,self.root/'retained-created',src_dir_fd=k['dir_fd']);os.link(foreign,name,dst_dir_fd=k['dir_fd'])
   return fd
  with patch.object(m.os,'open',replace),self.assertRaises(ValueError):m.populate(s,v)
  self.assertEqual(foreign.read_bytes(),b'keep');self.assertTrue((self.root/'retained-created').stat().st_size>0)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Independent));(O/'INDEPENDENT03.json').write_text(json.dumps({'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'observations':observations,'fixture_root':str(ns['RUN']),'qualification':'tiny real objects only; synthetic constant substitutions retained, not actual source authority'},indent=2)+'\n');sys.exit(not result.wasSuccessful())

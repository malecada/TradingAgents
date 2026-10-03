"""Qualified tiny metadata-chain tests, not genuine source/capture or authority."""
import copy,hashlib,importlib.util,json,os,sys,unittest
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-final-recovery-preparation03-2026-10-03';sys.path.insert(0,str(P));s=importlib.util.spec_from_file_location('flat04',P/'recovery03.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);H=lambda b:hashlib.sha256(b).hexdigest();counter=0;observations={}
class Tests(unittest.TestCase):
 def setUp(self):
  global counter
  counter+=1;self.d=O/('chain-%02d'%counter);self.d.mkdir();self.bundle=self.d/'bundle';self.bundle.mkdir();self.cap=self.d/'tiny-capsule-fixture';self.ext=self.d/'tiny-external-fixture';self.cap.mkdir(mode=0o750);self.ext.mkdir(mode=0o710);(self.cap/'opaque').write_bytes(b'fixture-capsule-opaque');(self.ext/'helper').write_bytes(b'fixture-external-opaque');self.dest=self.d/'flat';self.dest.mkdir(mode=0o700);self.man={role:m.scan(root) for role,root in [('capsule',self.cap),('external',self.ext)]};self.archives={role:m.pack(root,self.man[role],self.bundle/(role+'.tar.gz')) for role,root in [('capsule',self.cap),('external',self.ext)]}
  self.q={'schema_version':1,'capsule_root':m.CAP,'source':m.SOURCE,'external_root':str(self.ext),'output_root':str(self.d/'uninvoked-capture-scope'),'external_members':{r['path']:r['sha256'] for r in self.man['external']['members'] if r['kind']=='file'},'registration':'fixture-only-not-authenticated.json','registration_sha256':'0'*64}
  for role in ('capsule','external'):
   self.q[role+'_manifest']=self.man[role];self.q[role+'_manifest_sha256']=H(m.encode(self.man[role]));(self.bundle/(role+'-manifest.json')).write_bytes(m.encode(self.man[role]))
  self.qhash=H(m.encode(self.q));self.receipt={'schema_version':1,'source':m.SOURCE,'request_sha256':self.qhash,'archives':self.archives,'scope':'SYNTHETIC UNREGISTERED METADATA FIXTURE ONLY; actual capture/source/Git authentication NOT RUN'};self.write_receipt()
 def write_receipt(self):
  b=m.encode(self.receipt);(self.bundle/'capture.json').write_bytes(b);self.chash=H(b)
 def recover(self,**kw):return m.recover(kw.get('bundle',self.bundle),kw.get('chash',self.chash),kw.get('q',self.q),kw.get('qhash',self.qhash),kw.get('dest',self.dest))
 def test_qualified_full_two_role_chain_and_files(self):
  with patch.object(m,'authenticate_source',side_effect=AssertionError('fresh Git prohibited in flat protocol')):r=self.recover()
  for role in ('capsule','external'):
   meta=json.loads((self.dest/(role+'-metadata.json')).read_bytes());self.assertEqual(meta['manifest'],self.man[role]);self.assertEqual(meta['archive'],self.archives[role])
   for row in self.man[role]['members']:
    if row['kind']=='file':self.assertEqual(H((self.dest/meta['flat_members'][row['path']]).read_bytes()),row['sha256'])
  self.assertEqual(json.loads((self.dest/'recovery.json').read_bytes()),r);self.assertIs(r['recovered_tree_git_join'],False);self.assertIs(r['research_authority'],False);observations['qualified_chain']=r;observations['qualification']='Fixture-only request/capture dictionaries; no actual capture/source/Git, native or research authority'
 def test_request_capture_hash_refuse_before_decompression(self):
  for kwargs in ({'qhash':'0'*64},{'chash':'0'*64}):
   with patch.object(m,'framed_members',side_effect=AssertionError('decode before authentication')),patch.object(m.FlatOutput,'create',side_effect=AssertionError('write before authentication')),self.assertRaises(ValueError):self.recover(**kwargs)
  self.assertEqual(list(self.dest.iterdir()),[])
 def test_capture_wrong_source_or_request_join(self):
  for field in ('source','request_sha256'):
   original=self.receipt[field];self.receipt[field]='f'*len(original);self.write_receipt()
   with patch.object(m,'framed_members',side_effect=AssertionError('decode')),self.assertRaises(ValueError):self.recover()
   self.receipt[field]=original
  self.assertEqual(list(self.dest.iterdir()),[])
 def test_unknown_capture_archive_role(self):
  self.receipt['archives']['unknown']=copy.deepcopy(self.archives['capsule']);self.write_receipt()
  with patch.object(m,'framed_members',side_effect=AssertionError('decode')),self.assertRaises(ValueError):self.recover()
 def test_first_role_manifest_pin_before_decompression(self):
  (self.bundle/'capsule-manifest.json').write_bytes(b'{}\n')
  with patch.object(m,'framed_members',side_effect=AssertionError('decode')),patch.object(m.FlatOutput,'create',side_effect=AssertionError('write')),self.assertRaises(ValueError):self.recover()
 def test_second_role_failure_retains_unaccepted_first_partials(self):
  (self.bundle/'external-manifest.json').write_bytes(b'{}\n')
  with self.assertRaises(ValueError):self.recover()
  self.assertTrue((self.dest/'capsule-metadata.json').exists());self.assertFalse((self.dest/'recovery.json').exists());observations['partial_on_late_role_failure']='first-role partials retained; no final recovery.json or successful return'
 def test_destination_nonrecursive(self):
  for dest in (self.bundle,self.ext,Path(m.CAP),self.bundle/'nested'):
   with self.subTest(dest=dest),self.assertRaises(ValueError):self.recover(dest=dest)
 def test_wrong_second_role_body_hash_retained_no_success(self):
  raw=(self.bundle/'external.tar.gz').read_bytes();(self.bundle/'external.tar.gz').write_bytes(raw[:-1]+bytes([raw[-1]^1]))
  with self.assertRaises(ValueError):self.recover()
  self.assertFalse((self.dest/'recovery.json').exists())
 def test_exact_readback_cleanup_failure_chain(self):
  real=m.read
  def wrong(root,name,*a,**k):
   b=real(root,name,*a,**k)
   return b'wrong recovered bytes' if Path(root)==self.dest else b
  with patch.object(m,'read',wrong):
   try:m.restore(self.bundle/'capsule.tar.gz',self.archives['capsule'],self.man['capsule'],self.dest)
   except BaseException as e:
    self.assertEqual(type(e).__name__,'CleanupFailure');self.assertIsInstance(e.__cause__,ExceptionGroup);messages=[str(x) for x in e.__cause__.exceptions];self.assertIn('recovered flat body differs',messages);self.assertIn('noncanonical exact compressed bytes',messages);observations['reviewer_error_correction']={'type':type(e).__name__,'aggregate':messages,'source_change':False}
   else:self.fail('accepted changed body')
  self.assertFalse((self.dest/'body-metadata.json').exists());self.assertFalse((self.dest/'recovery.json').exists())
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests));(O/'CHECK04.json').write_text(json.dumps({'tests':r.testsRun,'errors':len(r.errors),'failures':len(r.failures),'observations':observations},indent=2)+'\n');sys.exit(not r.wasSuccessful())

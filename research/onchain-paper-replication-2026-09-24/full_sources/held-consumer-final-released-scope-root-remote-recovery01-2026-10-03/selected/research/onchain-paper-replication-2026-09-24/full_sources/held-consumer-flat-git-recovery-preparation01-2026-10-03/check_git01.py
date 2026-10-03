"""Retained tiny real Git utility qualification, not a capsule/claim/source receipt."""
import copy,gzip,hashlib,importlib.util,json,os,stat,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import git_recovery01 as m
from bounded_git01 import git as utility
P=Path(__file__).resolve().parent;RUN=Path(tempfile.mkdtemp(prefix='tiny-git-',dir=P));observations=[]
class Checks(unittest.TestCase):
 def setUp(self):
  self.root=RUN/self._testMethodName;self.root.mkdir(mode=0o700);self.donor=self.root/'tiny-donor.git';self.donor.mkdir(mode=0o700);utility(self.donor,['init','--bare','.'])
  self.bodies={'alpha':b'opaque-alpha\0','exec':b'opaque-exec\n'};self.oids={}
  for name,body in self.bodies.items():self.oids[name]=utility(self.donor,['hash-object','-w','--stdin'],body).decode().strip()
  self.tree=utility(self.donor,['mktree'],('100644 blob '+self.oids['alpha']+'\talpha\n100755 blob '+self.oids['exec']+'\texec\n').encode()).decode().strip()
  self.parent=utility(self.donor,['-c','user.name=synthetic','-c','user.email=synthetic@invalid','commit-tree',self.tree,'-m','tiny utility parent']).decode().strip();self.commit=utility(self.donor,['-c','user.name=synthetic','-c','user.email=synthetic@invalid','commit-tree',self.tree,'-p',self.parent,'-m','tiny utility child']).decode().strip()
  self.cap=self.root/'capsule';self.cap.mkdir(mode=0o700);(self.cap/'.git').mkdir(mode=0o700);(self.cap/'.git/objects').mkdir(mode=0o700)
  for f in (self.donor/'objects').glob('??/*'):
   if f.parent.name+f.name==self.parent:continue
   target=self.cap/'.git/objects'/f.parent.name/f.name;target.parent.mkdir(mode=0o700,exist_ok=True);target.write_bytes(f.read_bytes())
  for name,body in self.bodies.items():(self.cap/name).write_bytes(body)
  os.chmod(self.cap/'exec',0o750);self.expected=[{'path':n,'git_mode':'100755' if n=='exec' else '100644','object':self.oids[n],'bytes':len(b),'sha256':m.a.digest(b)} for n,b in self.bodies.items()]
  self.external=self.root/'external';self.external.mkdir(mode=0o700);(self.external/'note').write_bytes(b'opaque external utility evidence')
  self.bundle=self.root/'bundle';self.bundle.mkdir(mode=0o700);self.flat=self.root/'flat';self.flat.mkdir(mode=0o700);self.output=self.root/'proof-store';self.output.mkdir(mode=0o700)
  self.q={'schema_version':1,'capsule_root':str(self.cap),'source':self.commit,'external_root':str(self.external),'external_members':{'note':m.a.digest((self.external/'note').read_bytes())},'output_root':str(self.root/'capture-output-uninvoked'),'registration':'unavailable-synthetic-registration.json','registration_sha256':'0'*64}
  self.archive_info={}
  for role,root in [('capsule',self.cap),('external',self.external)]:
   man=m.a.scan(root);self.q[role+'_manifest']=man;self.q[role+'_manifest_sha256']=m.a.digest(m.a.encode(man));self.archive_info[role]=m.a.pack(root,man,self.bundle/(role+'.tar.gz'));m.a.put(self.bundle/(role+'-manifest.json'),man)
  self.request=self.root/'request.json';m.a.put(self.request,self.q);self.qsha=m.a.digest(self.request.read_bytes());c={'schema_version':1,'source':self.commit,'request_sha256':self.qsha,'archives':self.archive_info,'scope':'SYNTHETIC TINY UTILITY CHAIN; original capture/source authentication not invoked'};m.a.put(self.bundle/'capture.json',c);self.csha=m.a.digest((self.bundle/'capture.json').read_bytes())
  for target,name,value in [(m.a,'SOURCE',self.commit),(m.a,'CAP',str(self.cap)),(m,'SOURCE',self.commit)]:
   patched=patch.object(target,name,value);patched.start();self.addCleanup(patched.stop)
  m.a.recover(self.bundle,self.csha,self.q,self.qsha,self.flat);self.rsha=m.a.digest((self.flat/'recovery.json').read_bytes())
 def joined(self):
  v=m.FlatView(self.flat);v.begin();self.addCleanup(v.close);q=m.chain(v,self.bundle,self.request,self.qsha,self.csha,self.rsha);s=m.ObjectStore(self.output);s.begin();self.addCleanup(s.close);return v,s,q
 def test_red_archival_without_git_namespace(self):
  with self.assertRaises(ValueError):utility(self.flat,['cat-file','-t',self.commit])
  observations.append({'case':'RED_ARCHIVAL_ONLY','tiny_commit':self.commit,'result':'real Git cannot read commit from flat archival directory; no actual source proof'})
 def test_green_loose_objects_all_bodies_modes_missing_parent(self):
  v,s,_=self.joined();files=m.populate(s,v);result=m.verify_lookups(s,self.commit,self.expected,v,True);s.verify_files();self.assertEqual(len(result),2);self.assertEqual(len(files),4)
  with self.assertRaises(ValueError):s.object(self.parent,'commit')
  observations.append({'case':'GREEN_TINY_LOOSE','tiny_commit':self.commit,'lookups':len(result),'missing_parent':self.parent,'full_ancestry':False,'git_operations':s.calls})
 def test_green_pack_pair_only(self):
  # Real Git packs only the exact selected objects; no revision traversal.
  selected=[self.commit,self.tree,*self.oids.values()];raw=utility(self.donor,['pack-objects','--stdout'],('\n'.join(selected)+'\n').encode());packed=self.root/'packed.git';packed.mkdir(mode=0o700);utility(packed,['init','--bare','.']);utility(packed,['index-pack','--stdin'],raw)
  capsule=self.root/'packed-capsule';capsule.mkdir(mode=0o700);(capsule/'.git').mkdir(mode=0o700);(capsule/'.git/objects').mkdir(mode=0o700);(capsule/'.git/objects/pack').mkdir(mode=0o700)
  for f in (packed/'objects/pack').iterdir():(capsule/'.git/objects/pack'/f.name).write_bytes(f.read_bytes())
  for name,body in self.bodies.items():(capsule/name).write_bytes(body)
  os.chmod(capsule/'exec',0o750);man=m.a.scan(capsule);archive=self.root/'packed.gz';info=m.a.pack(capsule,man,archive);flat=self.root/'packed-flat';flat.mkdir(mode=0o700);m.a.restore(archive,info,man,flat,prefix='capsule');meta=json.loads((flat/'capsule-metadata.json').read_bytes());v=m.FlatView(flat);v.begin();self.addCleanup(v.close);v.manifests={'capsule':man};v.maps={'capsule':meta['flat_members']};s=m.ObjectStore(self.output);s.begin();self.addCleanup(s.close);rows=m.populate(s,v);self.assertEqual(len(rows),2);self.assertEqual(len(m.verify_lookups(s,self.commit,self.expected,v,True)),2)
 def test_all_current_membership_refusal(self):
  v,s,_=self.joined();m.populate(s,v)
  with self.assertRaises(ValueError):m.verify_lookups(s,self.commit,self.expected[:1],v,True)
 def test_git_hash_mode_body_inverse_controls(self):
  v,s,_=self.joined();m.populate(s,v)
  for field,value in [('object','0'*40),('sha256','0'*64),('bytes',1),('git_mode','100755')]:
   rows=copy.deepcopy(self.expected);rows[0][field]=value
   with self.assertRaises(ValueError):m.verify_lookups(s,self.commit,rows,v,True)
 def test_changed_recovered_body_refused(self):
  v,s,_=self.joined();m.populate(s,v);(self.flat/v.maps['capsule']['alpha']).write_bytes(b'wrong')
  with self.assertRaises(ValueError):m.verify_lookups(s,self.commit,self.expected,v,True)
 def test_changed_object_before_population_refused(self):
  v,s,_=self.joined();name=next(n for n in v.maps['capsule'] if n.startswith('.git/objects/'));(self.flat/v.maps['capsule'][name]).write_bytes(b'wrong')
  with self.assertRaises(ValueError):m.populate(s,v)
 def test_wrong_chain_pins_before_store_population(self):
  v=m.FlatView(self.flat);v.begin();self.addCleanup(v.close)
  for pins in [('0'*64,self.csha,self.rsha),(self.qsha,'0'*64,self.rsha),(self.qsha,self.csha,'0'*64)]:
   with self.assertRaises(ValueError):m.chain(v,self.bundle,self.request,*pins)
  self.assertEqual(list(self.output.iterdir()),[])
 def test_wrong_body_map_even_count_preserved(self):
  meta=json.loads((self.flat/'capsule-metadata.json').read_bytes());keys=list(meta['flat_members']);meta['flat_members'][keys[0]],meta['flat_members'][keys[1]]=meta['flat_members'][keys[1]],meta['flat_members'][keys[0]];(self.flat/'capsule-metadata.json').write_bytes(m.a.encode(meta));rec=json.loads((self.flat/'recovery.json').read_bytes());rec['results']['capsule']['metadata_sha256']=m.a.digest(m.a.encode(meta));(self.flat/'recovery.json').write_bytes(m.a.encode(rec));v=m.FlatView(self.flat);v.begin();self.addCleanup(v.close)
  with self.assertRaises(ValueError):m.chain(v,self.bundle,self.request,self.qsha,self.csha,m.a.digest(m.a.encode(rec)))
 def test_fresh_empty_private_output(self):
  (self.output/'foreign').write_bytes(b'keep');v,s,q=None,m.ObjectStore(self.output),None;self.addCleanup(s.close)
  with self.assertRaises(ValueError):s.begin()
  self.assertEqual((self.output/'foreign').read_bytes(),b'keep')
 def test_namespace_modes_never_changed(self):
  with patch.object(m.os,'chmod',side_effect=AssertionError('chmod')),patch.object(m.os,'fchmod',side_effect=AssertionError('fchmod')):
   v,s,_=self.joined();m.populate(s,v);m.verify_lookups(s,self.commit,self.expected,v,True)
 def test_acquired_directory_birth_substitution_explicit_contract(self):
  foreign=self.root/'empty-current-namespace';foreign.mkdir(mode=0o700);ino=foreign.stat().st_ino;real=os.mkdir;events=[]
  def swap(path,mode=0o777,*,dir_fd=None):
   r=real(path,mode,dir_fd=dir_fd)
   if str(path)=='objects' and not events:(self.output/'objects').rename(self.root/'created-retained');foreign.rename(self.output/'objects');events.append(1)
   return r
  with patch.object(m.os,'mkdir',swap):v,s,_=self.joined();m.populate(s,v)
  self.assertEqual((self.output/'objects').stat().st_ino,ino);self.assertEqual(stat.S_IMODE((self.output/'objects').stat().st_mode),0o700);self.assertEqual(events,[1])
 def test_preexisting_object_file_not_overwritten(self):
  v,s,_=self.joined();real=os.open;foreign=self.root/'foreign';foreign.write_bytes(b'keep');once=[]
  def race(path,flags,*args,**kwargs):
   if flags&os.O_CREAT and len(str(path))==38 and not once:once.append(1);os.link(foreign,path,dst_dir_fd=kwargs['dir_fd'])
   return real(path,flags,*args,**kwargs)
  with patch.object(m.os,'open',race),self.assertRaises(FileExistsError):m.populate(s,v)
  self.assertEqual(foreign.read_bytes(),b'keep')
 def test_fd_firstfatal_cleanup_independent(self):
  s=m.ObjectStore(self.output);s.begin();owned=list(s.fds);first=MemoryError('original write');real=os.close;closed=[]
  def close(fd):closed.append(fd);real(fd);raise OSError('later uncertain close')
  with patch.object(m.os,'write',side_effect=first),patch.object(m.os,'close',close),self.assertRaises(MemoryError) as found:
   try:s.create('failure',b'x')
   finally:s.close()
  self.assertIs(found.exception,first);self.assertEqual(closed[1:],list(reversed(owned)));self.assertEqual(len(closed),4);self.assertEqual(len(closed),len(set(closed)))
 def test_unselected_object_metadata_not_installed(self):
  v,s,_=self.joined();v.manifests['capsule']['members'].append({'path':'.git/objects/info/alternates','kind':'file','mode':0o600,'bytes':0,'sha256':m.a.digest(b'')});m.populate(s,v);self.assertFalse((self.output/'objects/info/alternates').exists())
 def test_per_operation_and_total_bounds(self):
  v,s,_=self.joined();m.populate(s,v)
  with self.assertRaises(ValueError):s.query(['cat-file','--batch'],b'x'*65537)
  with self.assertRaises(ValueError):s.create('oversize',b'x'*(m.a.FILE+1))
  s.calls=m.MAX_CALLS
  with self.assertRaises(ValueError):s.object(self.commit,'commit')
  self.assertEqual((m.WALL,m.TOTAL,m.MAX_CALLS),(300,134217728,4096))
 def test_unselected_git_command_refused(self):
  v,s,_=self.joined()
  with self.assertRaises(ValueError):s.query(['fetch','anything'])
 def test_null_public_spec_refuses(self):
  with self.assertRaises((ValueError,TypeError)):m.prove(json.loads((P/'ROOT_SPEC_TEMPLATE01.json').read_bytes()))
 def test_fd_wrapper_exact_inverse(self):
  original=(P/'bounded_git01.py').read_text();candidate=(P/'bounded_git_fd01.py').read_text();self.assertEqual(candidate.replace("cwd='/proc/self/fd/'+str(root),pass_fds=(root,),env=env,stdin=","cwd=root,env=env,stdin="),original)
if __name__=='__main__':
 result=unittest.main(verbosity=2,exit=False);(RUN/'observations.json').write_text(json.dumps(observations,sort_keys=True,indent=2)+'\n');raise SystemExit(not result.result.wasSuccessful())

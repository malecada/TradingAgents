import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile,unittest
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-final-recovery-preparation02-2026-10-03';A=O.parent/'held-consumer-final-recovery-preparation01-2026-10-03';sys.path.insert(0,str(P));H=lambda b:hashlib.sha256(b).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('candidate02',P/'recovery01.py');old=load('frozen01',A/'recovery01.py');observations={};counter=0
class Checks(unittest.TestCase):
 def setUp(self):
  global counter
  counter+=1;self.d=O/('tiny-case-%02d'%counter);self.d.mkdir();self.src=self.d/'source';self.src.mkdir(mode=0o750);(self.src/'empty').mkdir(mode=0o750);(self.src/'opaque').write_bytes(b'opaque\x00bytes');os.chmod(self.src/'opaque',0o640);self.manifest=m.scan(self.src);self.arc=self.d/'tiny.gz';self.info=m.pack(self.src,self.manifest,self.arc)
 def header(self,type,size,name='entry'):
  t=tarfile.TarInfo(name);t.type=type;t.size=size;t.mode=0o600;return t.tobuf(format=tarfile.USTAR_FORMAT)
 def frame(self,raw):return list(m.framed_members(gzip.compress(raw,mtime=0)))
 def test_frozen_manifest_all_types_modes(self):
  raw=(P/'MANIFEST02.json').read_bytes();self.assertEqual(H(raw),'9362c240c71fc17268da69f983fe0b7a1007cb2770cac5be519d1d82ec03be39');manifest=json.loads(raw);seen=[]
  for r in manifest['members']:
   p=P/r['path'];s=p.lstat();self.assertEqual(stat.S_IMODE(s.st_mode),r['mode']);seen.append(r['path'])
   if r['type']=='file':self.assertTrue(stat.S_ISREG(s.st_mode));self.assertEqual(s.st_nlink,r['links']);b=p.read_bytes();self.assertEqual((len(b),H(b)),(r['bytes'],r['sha256']))
   elif r['type']=='directory':self.assertTrue(stat.S_ISDIR(s.st_mode))
   elif r['type']=='symlink':self.assertTrue(stat.S_ISLNK(s.st_mode));self.assertEqual(os.readlink(p),r['target'])
   else:self.fail('unexpected typed member')
  self.assertEqual(set(seen),{str(p.relative_to(P)) for p in P.rglob('*') if p.name!='MANIFEST02.json'});observations['manifest_members']=len(seen)
 def test_complete_inverse_and_dependencies(self):
  a=(A/'recovery01.py').read_bytes();b=(P/'recovery01.py').read_bytes();self.assertEqual(H(b),'5c3794be17ee4e5797a0714125bb0f7b151377568d909a33b892cff664b7b5a2');self.assertEqual((P/'recovery01.py.baseline').read_bytes(),a)
  first=a.index(b'def restore(');last=a.index(b'def put(');start=b.index(b'INFLATED=BASE+64*1024**2');end=b.index(b'def put(');self.assertEqual(a[:first],b[:start]);self.assertEqual(a[last:],b[end:]);self.assertEqual(ast.dump(ast.parse(a[:first]+a[last:])),ast.dump(ast.parse(b[:start]+b[end:])))
  for name in ('owned_io.py','bounded_git01.py','REQUEST_TEMPLATE01.json'):self.assertEqual((P/name).read_bytes(),(A/name).read_bytes())
  observations['inverse']='exact complete bytes and AST outside restored block; source/Git/request/capture/recover unchanged'
 def test_exact_HFR1_red_green(self):
  raw=gzip.compress(self.header(tarfile.XHDTYPE,64*1024**2,'extended'),mtime=0);self.assertEqual(len(raw),67);archive=self.d/'67-byte.gz';archive.write_bytes(raw);empty={'schema_version':1,'root_mode':0o700,'members':[]};info={'bytes':67,'sha256':H(raw),'manifest_sha256':H(m.encode(empty))};real=gzip.GzipFile.read;seen=[]
  class Intercept(Exception):pass
  def guard(g,n=-1):
   seen.append(n)
   if n>65536:raise Intercept('large read safely intercepted')
   return real(g,n)
  with patch.object(gzip.GzipFile,'read',guard),self.assertRaises(Intercept):old.restore(archive,info,empty,self.d/'old-partial')
  self.assertEqual(max(seen),64*1024**2);red=list(seen);seen.clear()
  with patch.object(gzip.GzipFile,'read',guard),self.assertRaises(ValueError):m.restore(archive,info,empty,self.d/'new-partial')
  self.assertEqual(seen,[512]);observations['HFR1']={'red_read_requests':red,'green_read_requests':seen,'compressed_bytes':67}
 def test_exact_HFR2_original_chmod_red_green(self):
  original=os.chmod;results={}
  for name,mod in [('old',old),('new',m)]:
   outside=self.d/(name+'-outside');outside.mkdir(mode=0o700);dest=self.d/(name+'-restore');events=[]
   def hook(path,mode,*a,**k):
    if Path(path)==dest/'empty' and not events:
     (dest/'empty').rename(dest/'retained-empty');(dest/'empty').symlink_to(outside,target_is_directory=True);events.append('path chmod reached')
    return original(path,mode,*a,**k)
   with patch.object(mod.os,'chmod',hook):
    if name=='old':
     with self.assertRaises(ValueError):mod.restore(self.arc,self.info,self.manifest,dest)
    else:self.assertEqual(mod.restore(self.arc,self.info,self.manifest,dest)['status'],'byte-restored-no-authority')
   results[name]={'events':events,'outside_mode':stat.S_IMODE(outside.stat().st_mode)}
  self.assertEqual(results['old']['outside_mode'],0o750);self.assertEqual(results['new']['outside_mode'],0o700);self.assertEqual(results['new']['events'],[]);observations['HFR2-original']=results
 def test_declared_resource_bounds(self):self.assertEqual((m.FILE,m.PAX,m.INFLATED),(4*1024**2,8192,192*1024**2))
 def test_unsupported_headers_before_payload(self):
  for kind,size in [(tarfile.XHDTYPE,8193),(tarfile.REGTYPE,m.FILE+1),(tarfile.DIRTYPE,1),(tarfile.GNUTYPE_LONGNAME,1),(tarfile.GNUTYPE_LONGLINK,1),(tarfile.GNUTYPE_SPARSE,1),(tarfile.XGLTYPE,1),(tarfile.SYMTYPE,1),(tarfile.LNKTYPE,1),(b'Z',1)]:
   with self.subTest(kind=kind,size=size),self.assertRaises(ValueError):self.frame(self.header(kind,size,'././@PaxHeader' if kind==tarfile.XHDTYPE else 'entry'))
 def test_pax_duplicate_unknown_invalid_length(self):
  for body in [b'12 path=one\n12 path=two\n',b'13 size=1234\n',b'99 path=x\n',b'0 path=x\n',b'junk',b'']:
   with self.subTest(body=body),self.assertRaises(ValueError):self.frame(self.header(tarfile.XHDTYPE,len(body),'././@PaxHeader')+body+bytes((-len(body))%512)+bytes(1024))
 def test_padding_truncation_and_termination(self):
  for raw in [b'a'*511,self.header(tarfile.REGTYPE,1)+b'x',self.header(tarfile.REGTYPE,1)+b'x'+b'1'*511,bytes(512),bytes(1024)+b'nonzero']:
   with self.subTest(n=len(raw)),self.assertRaises((ValueError,tarfile.HeaderError,EOFError)):self.frame(raw)
 def test_inflated_ceiling_before_unbounded_read(self):
  calls=[];real=gzip.GzipFile.read
  def guard(g,n=-1):calls.append(n);self.assertGreaterEqual(n,0);self.assertLessEqual(n,65536);return real(g,n)
  with patch.object(m,'INFLATED',1024),patch.object(gzip.GzipFile,'read',guard),self.assertRaises(ValueError):self.frame(bytes(2048))
  self.assertTrue(calls)
 def test_long_utf8_canonical_complete(self):
  (self.src/('é'*70)).write_bytes(b'opaque long name');manifest=m.scan(self.src);archive=self.d/'long.gz';info=m.pack(self.src,manifest,archive);dest=self.d/'restored';result=m.restore(archive,info,manifest,dest);self.assertEqual(m.scan(dest),manifest);self.assertEqual(result['members'],len(manifest['members']))
 def test_deterministic_roundtrip(self):
  second=self.d/'second.gz';self.assertEqual(m.pack(self.src,self.manifest,second),self.info);self.assertEqual(self.arc.read_bytes(),second.read_bytes());dest=self.d/'dest';m.restore(self.arc,self.info,self.manifest,dest);self.assertEqual(m.scan(dest),self.manifest)
 def test_archive_binding_and_member_refusals(self):
  for i,key in enumerate(self.info):
   info=dict(self.info);info[key]=0 if key=='bytes' else '0'*64
   with self.subTest(key=key),self.assertRaises(ValueError):m.restore(self.arc,info,self.manifest,self.d/('bad-'+str(i)))
  for i,what in enumerate(('hash','mode','extra','missing')):
   manifest=copy.deepcopy(self.manifest)
   if what=='hash':next(r for r in manifest['members'] if r['kind']=='file')['sha256']='a'*64
   if what=='mode':manifest['members'][0]['mode']=0o700
   if what=='extra':manifest['members'].append({'path':'zz','kind':'directory','mode':0o700})
   if what=='missing':manifest['members'].pop()
   info=dict(self.info,manifest_sha256=H(m.encode(manifest)))
   with self.subTest(what=what),self.assertRaises(ValueError):m.restore(self.arc,info,manifest,self.d/('member-'+str(i)))
 def test_manifest_types_paths_and_counts(self):
  for row in [{'path':'../x','kind':'directory','mode':0o700},{'path':'keys/a','kind':'directory','mode':0o700},{'path':'x','kind':'directory','mode':True},{'path':'x','kind':'file','mode':0o600,'bytes':m.FILE+1,'sha256':'a'*64},{'path':'x','kind':'directory','mode':0o700,'sha256':'a'*64}]:
   manifest={'schema_version':1,'root_mode':0o700,'members':[row]}
   with self.subTest(row=row),self.assertRaises(ValueError):m.validate(manifest)
 def test_null_request_no_authority(self):
  with self.assertRaises((ValueError,TypeError)):m.request(json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes()))
 def test_post_open_directory_root_swaps_refuse(self):
  for i,(root,symlink) in enumerate(((False,True),(True,True),(False,False),(True,False))):
   outside=self.d/('outside'+str(i));outside.mkdir(mode=0o700);dest=self.d/('dest'+str(i));target=dest if root else dest/'empty';real=os.fchmod;events=[]
   def swap(fd,mode):
    s=os.fstat(fd)
    if stat.S_ISDIR(s.st_mode) and target.exists() and target.stat().st_ino==s.st_ino and not events:
     target.rename(self.d/('retained'+str(i)))
     if symlink:target.symlink_to(outside,target_is_directory=True)
     else:target.mkdir(mode=0o700)
     events.append(1)
    return real(fd,mode)
   with patch.object(m.os,'fchmod',swap),self.assertRaises(ValueError):m.restore(self.arc,self.info,self.manifest,dest)
   self.assertEqual(events,[1]);self.assertEqual(stat.S_IMODE(outside.stat().st_mode),0o700)
   if not symlink:self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o700)
 def test_owned_directory_firstfatal_close_once(self):
  dirs=m.RestoreDirectories(self.d/'owned');dirs.begin();dirs.create('child');fds=list(dirs.fds);real=os.close;closed=[];fatal=MemoryError('original')
  def close(fd):closed.append(fd);real(fd);raise OSError('after real close')
  with patch.object(m.os,'fchmod',side_effect=fatal),patch.object(m.os,'close',close):
   try:
    try:dirs.mode('child',0o750)
    finally:dirs.close()
   except BaseException as e:self.assertIs(e,fatal)
   else:self.fail('lost firstfatal')
  self.assertEqual(closed,list(reversed(fds)));self.assertEqual(len(closed),len(set(closed)))
 def test_no_numerical_imports(self):self.assertFalse(any(n.split('.')[0] in {'numpy','torch','scipy'} for n in sys.modules))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));(O/'CHECK02.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'observations':observations,'actual_capsule_capture_restore':False,'external_recovery':False},indent=2)+'\n');sys.exit(not result.wasSuccessful())

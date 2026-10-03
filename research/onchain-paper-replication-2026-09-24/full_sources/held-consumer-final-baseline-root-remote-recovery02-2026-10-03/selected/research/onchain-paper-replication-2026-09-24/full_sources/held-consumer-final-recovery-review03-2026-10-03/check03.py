import ast,copy,gzip,hashlib,importlib.util,json,os,stat,sys,tarfile,unittest
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-final-recovery-preparation03-2026-10-03';A=O.parent/'held-consumer-final-recovery-preparation02-2026-10-03';sys.path.insert(0,str(P));H=lambda b:hashlib.sha256(b).hexdigest();s=importlib.util.spec_from_file_location('candidate03',P/'recovery03.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);observed={};counter=0
class Checks(unittest.TestCase):
 def setUp(self):
  global counter
  counter+=1;self.d=O/('case-%02d'%counter);self.d.mkdir();self.src=self.d/'source';self.src.mkdir(mode=0o750);(self.src/'empty').mkdir(mode=0o710);(self.src/'nested').mkdir(mode=0o750);(self.src/'nested/a').write_bytes(b'opaque-a\0');(self.src/'z').write_bytes(b'opaque-z');os.chmod(self.src/'z',0o640);self.man=m.scan(self.src);self.arc=self.d/'archive.gz';self.info=m.pack(self.src,self.man,self.arc);self.dest=self.d/'flat';self.dest.mkdir(mode=0o700)
 def restore(self):return m.restore(self.arc,self.info,self.man,self.dest)
 def test_all851_frozen_types_no_special_reads(self):
  raw=(P/'MANIFEST03.json').read_bytes();self.assertEqual(H(raw),'8043f8265a743c1ff5141d7452768554bfa6d3d76e171badc5667250301dcda2');v=json.loads(raw);types={}
  for r in v['members']:
   p=P/r['path'];s=p.lstat();self.assertEqual(stat.S_IMODE(s.st_mode),r['mode']);kind=r['kind'];types[kind]=types.get(kind,0)+1
   if kind=='file':self.assertTrue(stat.S_ISREG(s.st_mode));self.assertEqual(s.st_nlink,r['nlink']);b=p.read_bytes();self.assertEqual((len(b),H(b)),(r['bytes'],r['sha256']))
   elif kind=='directory':self.assertTrue(stat.S_ISDIR(s.st_mode))
   elif kind=='symlink':self.assertTrue(stat.S_ISLNK(s.st_mode));self.assertEqual(os.readlink(p),r['target'])
   elif kind=='fifo':self.assertTrue(stat.S_ISFIFO(s.st_mode))
   else:self.fail('unknown kind '+kind)
  self.assertEqual(len(v['members']),851);self.assertEqual({r['path'] for r in v['members']},{str(x.relative_to(P)) for x in P.rglob('*') if x.name!='MANIFEST03.json'});observed['manifest_types']=types
 def test_whole_inverse(self):
  a=(A/'recovery01.py').read_text();b=(P/'recovery03.py').read_text();self.assertEqual(H(b.encode()),'785b957f93e22b18b1d3c00a73cacc75b6028bab9566d737b40903dcffc4964e');self.assertEqual(a[:a.index('class RestoreDirectories:')],b[:b.index('class FlatOutput:')]);self.assertEqual(a[a.index('def put('):a.index('def recover(')],b[b.index('def put('):b.index('def recover(')]);self.assertEqual(a[a.index("if __name__"):],b[b.index("if __name__"):])
  for name in ('owned_io.py','bounded_git01.py','REQUEST_TEMPLATE01.json'):self.assertEqual((A/name).read_bytes(),(P/name).read_bytes())
  for name in ('request','capture','authenticate_source','read','scan','validate','pack','tar_stream','framed_members','new_file','put'):
   get=lambda t:next(n for n in ast.parse(t).body if isinstance(n,ast.FunctionDef) and n.name==name)
   self.assertEqual(ast.dump(get(a)),ast.dump(get(b)))
 def test_all_body_names_modes_and_reencoding(self):
  seen=[];real=m.read
  def trace(root,name,*a,**k):
   if Path(root)==self.dest:seen.append(name)
   return real(root,name,*a,**k)
  with patch.object(m,'read',trace):result=self.restore()
  metadata=json.loads((self.dest/'body-metadata.json').read_bytes());self.assertEqual(metadata['manifest'],self.man);self.assertEqual(metadata['archive'],self.info);mapping=metadata['flat_members'];self.assertEqual(set(mapping),{r['path'] for r in self.man['members'] if r['kind']=='file'});self.assertEqual(seen,list(mapping.values()))
  for name,flat in mapping.items():self.assertEqual((self.src/name).read_bytes(),(self.dest/flat).read_bytes())
  for k in ('instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority'):self.assertIs(result[k],False)
  self.assertTrue(all(p.is_file() for p in self.dest.iterdir()));observed['complete_roundtrip']=result
 def test_no_birth_or_metadata_operations(self):
  with patch.object(m.os,'mkdir',side_effect=AssertionError('mkdir')),patch.object(m.os,'chmod',side_effect=AssertionError('chmod')),patch.object(m.os,'fchmod',side_effect=AssertionError('fchmod')):self.restore()
  self.assertEqual(stat.S_IMODE(self.dest.stat().st_mode),0o700)
 def test_output_contract_refusals(self):
  absent=self.d/'absent';alias=self.d/'alias';alias.symlink_to(self.dest,target_is_directory=True);nonprivate=self.d/'public';nonprivate.mkdir(mode=0o750);nonempty=self.d/'nonempty';nonempty.mkdir(mode=0o700);(nonempty/'foreign').write_bytes(b'keep')
  for dest in (absent,alias,nonprivate,nonempty):
   with self.subTest(dest=dest),self.assertRaises((ValueError,FileNotFoundError)):m.restore(self.arc,self.info,self.man,dest)
  self.assertEqual((nonempty/'foreign').read_bytes(),b'keep')
 def test_atomic_created_file_ownership(self):
  real=os.open;once=[];foreign=self.d/'foreign';foreign.write_bytes(b'unchanged')
  def swap(name,flags,*a,**k):
   fd=real(name,flags,*a,**k)
   if name=='body-00000.body' and flags&os.O_CREAT and not once:
    once.append(fd);(self.dest/name).rename(self.d/'original-created');os.link(foreign,self.dest/name)
   return fd
  with patch.object(m.os,'open',swap),self.assertRaises(ValueError):self.restore()
  self.assertEqual(foreign.read_bytes(),b'unchanged');self.assertEqual((self.d/'original-created').read_bytes(),b'opaque-a\0')
 def test_existing_file_cannot_receive_writes(self):
  real=os.open;foreign=self.d/'foreign';foreign.write_bytes(b'keep');once=[]
  def race(name,flags,*a,**k):
   if name=='body-00000.body' and flags&os.O_CREAT and not once:once.append(1);os.link(foreign,self.dest/name)
   return real(name,flags,*a,**k)
  with patch.object(m.os,'open',race),self.assertRaises(FileExistsError):self.restore()
  self.assertEqual(foreign.read_bytes(),b'keep')
 def test_namespace_replacement_no_foreign_mutation(self):
  real=os.write;once=[]
  def race(fd,b):
   if not once:once.append(1);self.dest.rename(self.d/'retained');self.dest.mkdir(mode=0o700)
   return real(fd,b)
  with patch.object(m.os,'write',race),self.assertRaises((ValueError,FileNotFoundError)):self.restore()
  self.assertEqual(list(self.dest.iterdir()),[])
 def test_actual_readback_and_late_body_change(self):
  real=m.read
  def change(root,name,*a,**k):
   raw=real(root,name,*a,**k)
   return b'wrong' if Path(root)==self.dest else raw
  with patch.object(m,'read',change),self.assertRaises(ValueError):self.restore()
 def test_firstfatal_each_fd_close(self):
  realopen=os.open;realclose=os.close;active=[];closed=[];first=MemoryError('original write');out=m.FlatOutput(self.dest)
  def op(*a,**k):fd=realopen(*a,**k);active.append(fd);return fd
  def close(fd):active.remove(fd);closed.append(fd);realclose(fd);raise OSError('after real close')
  with patch.object(m.os,'open',op),patch.object(m.os,'close',close),patch.object(m.os,'write',side_effect=first):
   try:
    try:out.begin();out.create('tiny',b'x')
    finally:out.close()
   except BaseException as e:self.assertIs(e,first)
   else:self.fail('lost fatal')
  self.assertEqual(active,[]);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_archive_pin_refused_before_read_or_write(self):
  for field in ('sha256','manifest_sha256','bytes'):
   info=dict(self.info);info[field]=0 if field=='bytes' else '0'*64
   with patch.object(m,'framed_members',side_effect=AssertionError('decompression started')),patch.object(m.FlatOutput,'create',side_effect=AssertionError('write started')),self.assertRaises(ValueError):m.restore(self.arc,info,self.man,self.dest)
  self.assertEqual(list(self.dest.iterdir()),[])
 def test_every_manifest_type_hash_mode(self):
  for i,field in enumerate(('sha256','bytes','mode','kind')):
   man=copy.deepcopy(self.man);r=next(r for r in man['members'] if r['kind']=='file')
   if field=='sha256':r[field]='a'*64
   elif field=='bytes':r[field]+=1
   elif field=='mode':r[field]=0o600
   else:r.clear();r.update(path='nested/a',kind='directory',mode=0o700)
   dest=self.d/('bad'+str(i));dest.mkdir(mode=0o700);info=dict(self.info,manifest_sha256=H(m.encode(man)))
   with self.assertRaises(ValueError):m.restore(self.arc,info,man,dest)
 def test_noncanonical_and_trailing_compression(self):
  raw=self.arc.read_bytes();changed=bytearray(raw);changed[4:8]=b'\x01\x00\x00\x00'
  for i,b in enumerate((bytes(changed),raw+gzip.compress(bytes(512),mtime=0))):
   p=self.d/('bad'+str(i)+'.gz');p.write_bytes(b);info=dict(self.info,bytes=len(b),sha256=H(b));dest=self.d/('flat'+str(i));dest.mkdir(mode=0o700)
   with self.assertRaises(ValueError):m.restore(p,info,self.man,dest)
 def test_67byte_original_parser_bound(self):
  t=tarfile.TarInfo('extended');t.type=tarfile.XHDTYPE;t.size=64*1024**2;t.mode=0o600;raw=gzip.compress(t.tobuf(format=tarfile.USTAR_FORMAT),mtime=0);self.assertEqual(len(raw),67);real=gzip.GzipFile.read;calls=[]
  def read(g,n=-1):calls.append(n);self.assertTrue(0<=n<=65536);return real(g,n)
  with patch.object(gzip.GzipFile,'read',read),self.assertRaises(ValueError):list(m.framed_members(raw))
  self.assertEqual(calls,[512]);observed['67B_read_requests']=calls
 def test_fixed_and_tiny_scaled_bounds(self):
  self.assertEqual((m.FILE,m.BASE,m.INFLATED,m.PAX,m.FLOOR),(4194304,134217728,201326592,8192,10737418240))
  with patch.object(m,'INFLATED',1024),self.assertRaises(ValueError):list(m.framed_members(gzip.compress(bytes(2048),mtime=0)))
 def test_long_utf8_full_reencoding(self):
  (self.src/('é'*70)).write_bytes(b'long');man=m.scan(self.src);p=self.d/'long.gz';info=m.pack(self.src,man,p);self.assertEqual(m.restore(p,info,man,self.dest)['regular_bodies'],3)
 def test_null_template_and_numerical_absence(self):
  with self.assertRaises((ValueError,TypeError)):m.request(json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes()))
  self.assertFalse(any(n.split('.')[0] in {'numpy','torch','scipy'} for n in sys.modules))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));(O/'CHECK03.json').write_text(json.dumps({'tests':result.testsRun,'errors':len(result.errors),'failures':len(result.failures),'observations':observed,'actual_capsule_or_external_recovery':False},indent=2)+'\n');sys.exit(not result.wasSuccessful())

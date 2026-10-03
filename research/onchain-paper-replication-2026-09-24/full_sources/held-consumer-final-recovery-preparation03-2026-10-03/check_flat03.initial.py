"""Stdlib only, tiny owned opaque fixtures retained; no actual capsule or capture."""
import ast,copy,gzip,importlib.util,json,os,stat,tarfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('flat_recovery',P/'recovery03.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Checks(unittest.TestCase):
 def setUp(self):
  self.root=P/('fixture-'+self._testMethodName);self.root.mkdir(mode=0o700);self.src=self.root/'src';self.src.mkdir(mode=0o750);(self.src/'empty').mkdir(mode=0o750);(self.src/'dir').mkdir(mode=0o710);(self.src/'body').write_bytes(b'opaque\0one');(self.src/'dir'/'body').write_bytes(b'opaque-two');os.chmod(self.src/'body',0o640);self.manifest=m.scan(self.src);self.archive=self.root/'good.gz';self.info=m.pack(self.src,self.manifest,self.archive);self.dest=self.root/'flat';self.dest.mkdir(mode=0o700)
 def restore(self,manifest=None,info=None,archive=None):return m.restore(archive or self.archive,info or self.info,manifest or self.manifest,self.dest)
 def arbitrary(self,raw,manifest=None,label='bad'):
  a=self.root/(label+'.gz');a.write_bytes(raw);man=self.manifest if manifest is None else manifest;info={'bytes':len(raw),'sha256':m.digest(raw),'manifest_sha256':m.digest(m.encode(man))};return a,info,man
 def header(self,kind,size):
  t=tarfile.TarInfo('././@PaxHeader' if kind==tarfile.XHDTYPE else 'entry');t.type=kind;t.size=size;return t.tobuf(format=tarfile.USTAR_FORMAT)
 def test_roundtrip_all_bodies_and_metadata(self):
  result=self.restore();self.assertEqual(result['status'],'fresh-flat-archival-recovery-not-origin-proof');meta=json.loads((self.dest/'body-metadata.json').read_bytes());self.assertEqual(meta['manifest'],self.manifest);self.assertEqual(meta['archive'],self.info)
  for r in self.manifest['members']:
   if r['kind']=='file':self.assertEqual((self.dest/meta['flat_members'][r['path']]).read_bytes(),(self.src/r['path']).read_bytes())
  self.assertFalse(any(p.is_dir() for p in self.dest.iterdir()));self.assertEqual(stat.S_IMODE(self.dest.stat().st_mode),0o700)
  for k in ('instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority'):self.assertIs(result[k],False)
 def test_long_utf8_pax(self):
  (self.src/('é'*70)).write_bytes(b'long opaque');man=m.scan(self.src);a=self.root/'long.gz';info=m.pack(self.src,man,a);result=self.restore(man,info,a);self.assertEqual(result['regular_bodies'],3)
 def test_no_directory_birth_or_metadata_mutation(self):
  with patch.object(m.os,'mkdir',side_effect=AssertionError('directory birth forbidden')),patch.object(m.os,'chmod',side_effect=AssertionError('chmod forbidden')),patch.object(m.os,'fchmod',side_effect=AssertionError('fchmod forbidden')):self.restore()
 def test_exact_birth_attack_has_no_boundary(self):
  outside=self.root/'unrelated-original';outside.mkdir(mode=0o700);ino=outside.stat().st_ino;real=os.mkdir;events=[]
  def swap(path,mode=0o777,*,dir_fd=None):
   result=real(path,mode,dir_fd=dir_fd)
   if str(path)=='empty' and dir_fd is not None:
    target=self.dest/'empty';target.rename(self.root/'created-original');outside.rename(target);events.append('swap')
   return result
  with patch.object(m.os,'mkdir',swap):self.restore()
  self.assertEqual(events,[]);self.assertEqual(outside.stat().st_ino,ino);self.assertEqual(stat.S_IMODE(outside.stat().st_mode),0o700)
 def test_missing_existing_output(self):
  with self.assertRaises(FileNotFoundError):m.restore(self.archive,self.info,self.manifest,self.root/'absent')
 def test_nonempty_output(self):
  (self.dest/'foreign').write_bytes(b'keep')
  with self.assertRaises(ValueError):self.restore()
  self.assertEqual((self.dest/'foreign').read_bytes(),b'keep')
 def test_nonprivate_output(self):
  os.chmod(self.dest,0o750)
  with self.assertRaises(ValueError):self.restore()
 def test_symlink_output(self):
  alias=self.root/'alias';alias.symlink_to(self.dest,target_is_directory=True)
  with self.assertRaises(ValueError):m.restore(self.archive,self.info,self.manifest,alias)
 def test_exclusive_raced_file_no_foreign_write(self):
  real=os.open;once=[];foreign=self.root/'foreign';foreign.write_bytes(b'keep')
  def race(path,flags,*args,**kw):
   if path=='body-00000.body' and flags & os.O_CREAT and not once:once.append(1);os.link(foreign,self.dest/path)
   return real(path,flags,*args,**kw)
  with patch.object(m.os,'open',race),self.assertRaises(FileExistsError):self.restore()
  self.assertEqual(foreign.read_bytes(),b'keep')
 def test_created_file_replaced_write_owned_fd(self):
  real=os.open;once=[];foreign=self.root/'foreign';foreign.write_bytes(b'foreign')
  def race(path,flags,*args,**kw):
   fd=real(path,flags,*args,**kw)
   if path=='body-00000.body' and flags & os.O_CREAT and not once:
    once.append(1);(self.dest/path).rename(self.root/'created-retained');os.link(foreign,self.dest/path)
   return fd
  with patch.object(m.os,'open',race),self.assertRaises(ValueError):self.restore()
  self.assertEqual(foreign.read_bytes(),b'foreign');self.assertEqual((self.root/'created-retained').read_bytes(),b'opaque\0one')
 def test_output_namespace_replaced(self):
  real=os.write;once=[]
  def race(fd,b):
   if not once:once.append(1);self.dest.rename(self.root/'retained');self.dest.mkdir(mode=0o700)
   return real(fd,b)
  with patch.object(m.os,'write',race),self.assertRaises((ValueError,FileNotFoundError)):self.restore()
  self.assertEqual(list(self.dest.iterdir()),[])
 def test_foreign_namespace_injected(self):
  real=os.write;once=[]
  def race(fd,b):
   if not once:once.append(1);(self.dest/'foreign').write_bytes(b'keep')
   return real(fd,b)
  with patch.object(m.os,'write',race),self.assertRaises(ValueError):self.restore()
  self.assertEqual((self.dest/'foreign').read_bytes(),b'keep')
 def test_actual_readback_required(self):
  real=os.read
  def wrong(fd,n):
   s=os.fstat(fd)
   if stat.S_IMODE(s.st_mode)==0o600 and s.st_size==len(b'opaque\0one'):return b'x'*(n or 1)
   return real(fd,n)
  with patch.object(m.os,'read',wrong),self.assertRaises(ValueError):self.restore()
 def test_firstfatal_every_owned_fd_close(self):
  first=MemoryError('write first');realclose=os.close;realopen=os.open;active=[];closed=[]
  def opening(*a,**k):fd=realopen(*a,**k);active.append(fd);return fd
  def closing(fd):closed.append(fd);active.remove(fd);realclose(fd);raise OSError('close later')
  output=m.FlatOutput(self.dest)
  with patch.object(m.os,'open',opening),patch.object(m.os,'close',closing),patch.object(m.os,'write',side_effect=first),self.assertRaises(MemoryError) as found:
   try:output.begin();output.create('opaque',b'x')
   finally:output.close()
  self.assertIs(found.exception,first);self.assertEqual(active,[]);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_firstfatal_generator_and_output_cleanup(self):
  first=SystemExit('body first');events=[];real=m.FlatOutput.close
  def members(raw):
   try:raise first;yield
   finally:events.append('generator');raise first
  def close(output):events.append('output');real(output);raise OSError('later')
  with patch.object(m,'framed_members',members),patch.object(m.FlatOutput,'close',close),self.assertRaises(SystemExit) as found:self.restore()
  self.assertIs(found.exception,first);self.assertEqual(events,['generator','output'])
 def test_archive_hash_and_manifest_hash(self):
  for field in ('sha256','manifest_sha256','bytes'):
   info=dict(self.info);info[field]=0 if field=='bytes' else '0'*64
   with self.assertRaises(ValueError):self.restore(info=info)
  self.assertEqual(list(self.dest.iterdir()),[])
 def test_membership_hash_type_mode(self):
  for i,change in enumerate(('hash','type','mode','missing','extra')):
   man=copy.deepcopy(self.manifest)
   if change=='hash':man['members'][0]['sha256']='0'*64
   elif change=='type':man['members'][0]={'path':'body','kind':'directory','mode':0o640}
   elif change=='mode':man['members'][0]['mode']=0o600
   elif change=='missing':man['members']=man['members'][1:]
   else:man['members'].append({'path':'zzz','kind':'directory','mode':0o700})
   dest=self.root/('bad'+str(i));dest.mkdir(mode=0o700);info=dict(self.info,manifest_sha256=m.digest(m.encode(man)))
   with self.assertRaises(ValueError):m.restore(self.archive,info,man,dest)
 def test_exact_compressed_canonical_reencoding(self):
  raw=bytearray(self.archive.read_bytes());raw[4:8]=b'\x01\x00\x00\x00';a,info,man=self.arbitrary(bytes(raw))
  with self.assertRaises(ValueError):self.restore(man,info,a)
 def test_extra_gzip_member_trailing_zeros(self):
  a,info,man=self.arbitrary(self.archive.read_bytes()+gzip.compress(bytes(512),mtime=0))
  with self.assertRaises(ValueError):self.restore(man,info,a)
 def test_truncation_and_bad_termination(self):
  for raw in (self.archive.read_bytes()[:-5],gzip.compress(bytes(512),mtime=0),gzip.compress(bytes(1024)+b'x',mtime=0)):
   with self.assertRaises((ValueError,EOFError,OSError)):list(m.framed_members(raw))
 def test_exact_67byte_bound_before_payload(self):
  t=tarfile.TarInfo('extended');t.type=tarfile.XHDTYPE;t.size=64*1024**2;t.mode=0o600;raw=gzip.compress(t.tobuf(format=tarfile.USTAR_FORMAT),mtime=0);self.assertEqual(len(raw),67);original=gzip.GzipFile.read;calls=[]
  def read(obj,n=-1):calls.append(n);self.assertTrue(0<=n<=65536);return original(obj,n)
  with patch.object(gzip.GzipFile,'read',read),self.assertRaises(ValueError):list(m.framed_members(raw))
  self.assertEqual(calls,[512])
 def test_extension_link_and_extent_before_payload(self):
  for kind,size in ((tarfile.XHDTYPE,8193),(tarfile.GNUTYPE_LONGNAME,8),(tarfile.GNUTYPE_SPARSE,1),(tarfile.XGLTYPE,8),(tarfile.LNKTYPE,0),(tarfile.SYMTYPE,0),(b'Z',1),(tarfile.REGTYPE,m.FILE+1),(tarfile.DIRTYPE,1)):
   with self.subTest(kind=kind,size=size),self.assertRaises(ValueError):list(m.framed_members(gzip.compress(self.header(kind,size),mtime=0)))
 def test_malformed_pax_and_padding(self):
  for raw in (self.header(tarfile.XHDTYPE,4)+b'junk'+bytes(508),self.header(tarfile.XHDTYPE,10),self.header(tarfile.REGTYPE,1)+b'x'+b'x'*511):
   with self.assertRaises(ValueError):list(m.framed_members(gzip.compress(raw,mtime=0)))
 def test_inflated_bound_fixed_and_scaled(self):
  self.assertEqual((m.FILE,m.BASE,m.INFLATED,m.PAX,m.FLOOR),(4194304,134217728,201326592,8192,10737418240))
  with patch.object(m,'INFLATED',1024),self.assertRaises(ValueError):list(m.framed_members(gzip.compress(bytes(2048),mtime=0)))
 def test_source_inverse(self):
  old=(P.parent/'held-consumer-final-recovery-preparation02-2026-10-03'/'recovery01.py').read_text();new=(P/'recovery03.py').read_text();oldtree=ast.parse(old);newtree=ast.parse(new)
  names=['request','capture','authenticate_source','read','scan','validate','pack','tar_stream','framed_members','new_file','put']
  for name in names:
   a=next(n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name);b=next(n for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name);self.assertEqual(ast.get_source_segment(old,a),ast.get_source_segment(new,b));self.assertEqual(ast.dump(a),ast.dump(b))
  self.assertEqual(old[:old.index('class RestoreDirectories:')],new[:new.index('class FlatOutput:')]);self.assertEqual(old[old.index('def put('):old.index('def recover(')],new[new.index('def put('):new.index('def recover(')]);self.assertEqual(old[old.index("if __name__"):],new[new.index("if __name__"):])
 def test_template_refused(self):
  with self.assertRaises((ValueError,TypeError)):m.request(json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes()))
 def test_complete_reencoding_reads_each_recovered_body(self):
  real=m.read;seen=[]
  def traced(root,name,*a,**k):
   if Path(root)==self.dest:seen.append(name)
   return real(root,name,*a,**k)
  with patch.object(m,'read',traced):self.restore()
  self.assertEqual(seen,['body-00000.body','body-00001.body'])
if __name__=='__main__':unittest.main(verbosity=2)

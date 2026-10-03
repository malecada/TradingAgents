import gzip,hashlib,importlib.util,os,stat,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent;s=importlib.util.spec_from_file_location('r',P/'recovery01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=P);self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.src=self.root/'src';self.src.mkdir(mode=0o750);(self.src/'empty').mkdir(mode=0o750);(self.src/'body').write_bytes(b'tiny');self.manifest=m.scan(self.src);self.archive=self.root/'good.gz';self.info=m.pack(self.src,self.manifest,self.archive)
 def header(self,kind,size):
  t=tarfile.TarInfo('././@PaxHeader' if kind==tarfile.XHDTYPE else 'entry');t.type=kind;t.size=size;return t.tobuf(format=tarfile.USTAR_FORMAT)
 def test_exact_67byte_bomb_before_read(self):
  t=tarfile.TarInfo('extended');t.type=tarfile.XHDTYPE;t.size=64*1024**2;t.mode=0o600;raw=gzip.compress(t.tobuf(format=tarfile.USTAR_FORMAT),mtime=0);self.assertEqual(len(raw),67)
  archive=self.root/'bomb.gz';archive.write_bytes(raw);empty={'schema_version':1,'root_mode':0o700,'members':[]};info={'bytes':len(raw),'sha256':m.digest(raw),'manifest_sha256':m.digest(m.encode(empty))};original=gzip.GzipFile.read;calls=[]
  def read(obj,n=-1):calls.append(n);self.assertLessEqual(n,65536);self.assertGreaterEqual(n,0);return original(obj,n)
  with patch.object(gzip.GzipFile,'read',read),self.assertRaises(ValueError):m.restore(archive,info,empty,self.root/'partial')
  self.assertEqual(calls,[512])
 def test_other_extensions_and_oversize_before_payload(self):
  for kind,size in [(tarfile.XHDTYPE,8193),(tarfile.GNUTYPE_LONGNAME,8),(tarfile.GNUTYPE_SPARSE,1),(tarfile.XGLTYPE,8),(tarfile.REGTYPE,m.FILE+1)]:
   with self.subTest(kind=kind,size=size),self.assertRaises(ValueError):list(m.framed_members(gzip.compress(self.header(kind,size),mtime=0)))
 def test_truncated_and_malformed_pax(self):
  for raw in [self.header(tarfile.XHDTYPE,10),self.header(tarfile.XHDTYPE,4)+b'junk'+bytes(508),self.header(tarfile.REGTYPE,1)+b'x']:
   with self.assertRaises(ValueError):list(m.framed_members(gzip.compress(raw,mtime=0)))
 def test_inflated_total(self):
  with patch.object(m,'INFLATED',1024),self.assertRaises(ValueError):list(m.framed_members(gzip.compress(bytes(2048),mtime=0)))
 def test_long_pax_roundtrip(self):
  (self.src/('é'*70)).write_bytes(b'utf8name');manifest=m.scan(self.src);archive=self.root/'long.gz';info=m.pack(self.src,manifest,archive);dest=self.root/'long';m.restore(archive,info,manifest,dest);self.assertEqual(m.scan(dest),manifest)
 def test_original_path_chmod_witness_unreachable(self):
  with patch.object(m.os,'chmod',side_effect=AssertionError('pathname chmod forbidden')):m.restore(self.archive,self.info,self.manifest,self.root/'no-path-chmod')
 def race(self,root=False,symlink=True):
  outside=self.root/'outside';outside.mkdir(mode=0o700);dest=self.root/'restored';target=dest if root else dest/'empty';real=os.fchmod;once=[]
  def swapped(fd,mode):
   st=os.fstat(fd)
   if stat.S_ISDIR(st.st_mode) and target.exists() and st.st_ino==target.stat().st_ino and not once:
    once.append(1);target.rename(target.with_name(target.name+'-original'))
    if symlink:target.symlink_to(outside,target_is_directory=True)
    else:target.mkdir(mode=0o700)
   return real(fd,mode)
  with patch.object(m.os,'fchmod',swapped),self.assertRaises(ValueError):m.restore(self.archive,self.info,self.manifest,dest)
  self.assertEqual(once,[1]);self.assertEqual(stat.S_IMODE(outside.stat().st_mode),0o700)
  if not symlink:self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o700)
 def test_child_symlink_race(self):self.race()
 def test_root_symlink_race(self):self.race(root=True)
 def test_regular_directory_replacement(self):self.race(symlink=False)
 def test_held_directory_cleanup_firstfatal(self):
  dirs=m.RestoreDirectories(self.root/'held');dirs.begin();dirs.create('empty');owned=list(dirs.fds);first=MemoryError('fchmod');real=os.close;closed=[]
  def close(fd):closed.append(fd);real(fd);raise OSError('uncertain after actual close')
  with patch.object(m.os,'fchmod',side_effect=first),patch.object(m.os,'close',close),self.assertRaises(MemoryError) as e:
   try:dirs.mode('empty',0o750)
   finally:dirs.close()
  self.assertIs(e.exception,first);self.assertEqual(closed,list(reversed(owned)));self.assertEqual(len(closed),len(set(closed)))
if __name__=='__main__':unittest.main()

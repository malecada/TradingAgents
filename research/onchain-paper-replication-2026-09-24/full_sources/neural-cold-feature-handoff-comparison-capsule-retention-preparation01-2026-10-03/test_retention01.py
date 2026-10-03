"""Tiny opaque files only. No Git command, network, real CAP or authority."""
import io,json,os,pathlib,tarfile,tempfile,time,unittest
from unittest.mock import patch
import retention01 as m
class Cases(unittest.TestCase):
 def fixture(self,root):
  source=root/'source';source.mkdir();(source/'d').mkdir();(source/'d/a').write_bytes(b'\0opaque\xff');(source/'d/a').chmod(0o440)
  rows=m.archive.snapshot(source,root/'copy',limit=65536)
  return source,[{'path':'.','kind':'directory','mode':source.stat().st_mode&0o777,'bytes':0}]+rows
 def test_complete_opaque_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src,rows=self.fixture(root);m.pack(src,root/'a.gz',rows);m.unpack(root/'a.gz',root/'restored',rows);self.assertEqual((root/'restored/d/a').read_bytes(),b'\0opaque\xff')
   with self.assertRaises(FileExistsError):m.unpack(root/'a.gz',root/'restored',rows)
 def test_missing_extra_hash_mode_refuse(self):
  for kind in ('missing','extra','hash','mode'):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d);src,rows=self.fixture(root);m.pack(src,root/'a.gz',rows);changed=json.loads(json.dumps(rows))
    if kind=='missing':changed=changed[:-1]
    if kind=='extra':changed.append({'path':'new','kind':'directory','mode':0o700})
    if kind=='hash':changed[-1]['sha256']='1'*64
    if kind=='mode':changed[-1]['mode']=0o777
    with self.assertRaises(ValueError):m.unpack(root/'a.gz',root/'restored',changed)
 def test_link_and_traversal_refuse(self):
  for name,typ in [('source/a',tarfile.SYMTYPE),('source/../escape',tarfile.REGTYPE),('source/keys/x',tarfile.REGTYPE)]:
   with self.subTest(name=name),tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d);a=root/'a.gz'
    with tarfile.open(a,'w:gz') as f:
     top=tarfile.TarInfo('source');top.type=tarfile.DIRTYPE;top.mode=0o700;f.addfile(top);item=tarfile.TarInfo(name);item.mode=0o600;item.type=typ;item.linkname='/bad';f.addfile(item)
    rows=[{'path':'.','kind':'directory','mode':0o700,'bytes':0},{'path':name[7:],'kind':'file','mode':0o600,'bytes':0,'sha256':m.digest(b'')}]
    with self.assertRaises(ValueError):m.unpack(a,root/'out',rows)
 def test_duplicate_tar_member_refused(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);a=root/'a.gz'
   with tarfile.open(a,'w:gz') as f:
    for _ in range(2):top=tarfile.TarInfo('source');top.type=tarfile.DIRTYPE;top.mode=0o700;f.addfile(top)
   with self.assertRaises(ValueError):m.unpack(a,root/'out',[{'path':'.','kind':'directory','mode':0o700,'bytes':0}])
 def test_trailing_archive_bytes_refused(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src,rows=self.fixture(root);m.pack(src,root/'a.gz',rows)
   with (root/'a.gz').open('ab') as f:f.write(b'unexpected-after-complete-archive')
   with self.assertRaises(ValueError):m.unpack(root/'a.gz',root/'restored',rows)
 def test_compressed_bound_and_no_overwrite(self):
  stream=io.BytesIO();limited=m.Limited(stream);limited.count=m.MAX
  with self.assertRaises(ValueError):limited.write(b'x')
  self.assertEqual(stream.getvalue(),b'')
 def test_batch_framing_refusals(self):
  good=b'1'*40+b' blob 1\na\n'
  for value in (b'',good+b'extra',good.replace(b'blob',b'tree'),good[:-1],good.replace(b' 1\n',b' 99999999\n')):
   with self.subTest(value=value),self.assertRaises(ValueError):m.blobs(lambda *_a,**_k:value,pathlib.Path('/never-used'),'a'*40,['a'])
  self.assertEqual(m.blobs(lambda *_a,**_k:good,pathlib.Path('/never-used'),'a'*40,['a']),{'a':b'a'})
 def test_original_A_and_wrong_B_parent_refused_before_body_reads(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   with self.assertRaises(ValueError):m.validate(root,m.A,{},lambda *_a:(_ for _ in ()).throw(AssertionError('Git must not run')), {})
   B='b'*40
   def synthetic_wrong_parent(_root,*args,**kwargs):return (B if args[0]=='rev-parse' else B+' '+'c'*40).encode()
   with self.assertRaisesRegex(ValueError,'sole direct A'):m.validate(root,B,{},synthetic_wrong_parent,{})
 def test_protected_archive_member_rejected_before_source_read(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/'source';src.mkdir();rows=[{'path':'keys/data','kind':'file','mode':0o600,'bytes':0,'sha256':m.digest(b'')}]
   with self.assertRaises(ValueError):m.pack(src,root/'a.gz',rows)
 def test_decompressed_header_request_is_bounded_before_read(self):
  reader=m.TarReader(io.BytesIO(b'data'),time.monotonic()+10)
  with self.assertRaises(ValueError):reader.read(m.MAX+8193)
  self.assertEqual(reader.tell(),0)
 def test_git_firstfatal_cleanup_reap_and_fds_once_without_child(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);runner=m.Git(root/'logs');fatal=MemoryError('initial wait');events=[];closed=[];realclose=os.close
   class Stub:
    pid=2147483640
    def poll(self):return None
    def wait(self,timeout):
     events.append(('wait',timeout))
     if timeout==60:raise fatal
     return -9
   def close(fd):closed.append(fd);realclose(fd);raise OSError('cleanup')
   with patch.object(m.subprocess,'Popen',return_value=Stub()),patch.object(m.os,'killpg',side_effect=lambda *x:events.append(('kill',x))),patch.object(m.os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as got:runner(root,'synthetic-not-run')
   self.assertIs(got.exception,fatal);self.assertEqual([x[0] for x in events],['wait','kill','wait']);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_pack_firstfatal_survives_tar_close(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src,rows=self.fixture(root);fatal=MemoryError('original');count=[]
   class FakeTar:
    def addfile(self,*args):raise fatal
    def close(self):count.append('close');raise OSError('close')
   with patch.object(m.tarfile,'open',return_value=FakeTar()):
    with self.assertRaises(MemoryError) as got:m.pack(src,root/'a.gz',rows)
   self.assertIs(got.exception,fatal);self.assertEqual(count,['close'])
if __name__=='__main__':unittest.main(verbosity=2)

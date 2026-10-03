"""Tiny retained opaque archives; no capture or original source recovery."""
import ast,gzip,importlib.util,io,json,os,tarfile,tempfile,traceback,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
RUN=Path(tempfile.mkdtemp(prefix='paths-',dir=P))
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load(P/'recovery04.py','new')
old=load(P.parent/'held-consumer-final-recovery-preparation03-2026-10-03'/'recovery03.py','old')
def archive(name,kind=tarfile.DIRTYPE,pax=True,raw_name='entry',raw_type=None):
 chunks=[]
 if pax:
  value=('path='+name+'\n').encode();n=len(value)+2
  while len(str(n))+1+len(value)!=n:n=len(str(n))+1+len(value)
  body=str(n).encode()+b' '+value;t=tarfile.TarInfo('././@PaxHeader');t.type=tarfile.XHDTYPE;t.size=len(body);chunks.extend([t.tobuf(format=tarfile.USTAR_FORMAT),body,bytes((-len(body))%512)])
 t=tarfile.TarInfo(raw_name if pax else name);t.type=kind;t.size=0
 h=bytearray(t.tobuf(format=tarfile.USTAR_FORMAT))
 if raw_type is not None:h[156:157]=raw_type
 # Preserve deliberately malformed trailing syntax rather than TarInfo normalization.
 if not pax:
  b=name.encode();h[:100]=b+bytes(100-len(b))
 h[148:156]=b'        ';h[148:156]=('%06o\0 ' % sum(h)).encode()
 chunks.extend([bytes(h),bytes(1024)]);return gzip.compress(b''.join(chunks),mtime=0)
class Paths(unittest.TestCase):
 def test_actual_old_source_red_and_new_full_roundtrip(self):
  root=RUN/'roundtrip';root.mkdir();src=root/'src';src.mkdir();long='d'*110;(src/long).mkdir(mode=0o710);(src/long/'body').write_bytes(b'opaque\0payload');(src/'empty').mkdir();man=m.scan(src);a=root/'canonical.gz';info=m.pack(src,man,a)
  raw=a.read_bytes();self.assertIn(('path='+long+'/\n').encode(),gzip.decompress(raw))
  red=root/'old-flat';red.mkdir(mode=0o700)
  try:old.restore(a,info,man,red)
  except ValueError as e:
   self.assertEqual(str(e),'unsafe member path');(root/'RED04.log').write_text(traceback.format_exc())
  else:self.fail('old source did not reproduce')
  dest=root/'new-flat';dest.mkdir(mode=0o700)
  with patch.object(m.os,'mkdir',side_effect=AssertionError('mkdir')),patch.object(m.os,'chmod',side_effect=AssertionError('chmod')),patch.object(m.os,'fchmod',side_effect=AssertionError('fchmod')):result=m.restore(a,info,man,dest)
  meta=json.loads((dest/'body-metadata.json').read_bytes());self.assertEqual(meta['manifest'],man);self.assertEqual(meta['archive'],info);self.assertEqual((dest/meta['flat_members'][long+'/body']).read_bytes(),b'opaque\0payload');self.assertFalse(result['research_authority']);self.assertFalse(any(q.is_dir() for q in dest.iterdir()))
 def test_pax_paths_and_raw_slash_refusals(self):
  bad=['','/','//','./','../','a//','a/../','a/./','a//b/','/a/','a\\b/','a\0b/','.env/','keys/a/','a/'+'b'*2048+'/']
  for path in bad:
   with self.subTest(path=repr(path)),self.assertRaises(ValueError):list(m.framed_members(archive(path)))
  for kind in (tarfile.REGTYPE,tarfile.AREGTYPE):
   with self.subTest(kind=kind),self.assertRaises(ValueError):list(m.framed_members(archive('long/',kind)))
  for path,kind in [('a//',tarfile.DIRTYPE),('a/',tarfile.REGTYPE),('a/',tarfile.AREGTYPE),('/',tarfile.DIRTYPE),('a/../',tarfile.DIRTYPE)]:
   with self.subTest(raw=path,kind=kind),self.assertRaises(ValueError):list(m.framed_members(archive(path,kind,pax=False)))
 def test_alternate_encoding_rejected_by_exact_reencoding(self):
  # A PAX record for a short path is semantically understandable but noncanonical.
  raw=archive('short/');man={'schema_version':1,'root_mode':448,'members':[{'path':'short','kind':'directory','mode':420}]};root=RUN/'alternate';root.mkdir();a=root/'archive.gz';a.write_bytes(raw);dest=root/'flat';dest.mkdir(mode=0o700);info={'bytes':len(raw),'sha256':m.digest(raw),'manifest_sha256':m.digest(m.encode(man))}
  from owned_io import CleanupFailure
  with self.assertRaises(CleanupFailure) as raised:m.restore(a,info,man,dest)
  self.assertIsInstance(raised.exception.__cause__,ValueError)
  self.assertEqual(str(raised.exception.__cause__),'noncanonical exact compressed bytes')
  self.assertFalse((dest/'body-metadata.json').exists())
 def test_single_dir_slash_only_after_real_type(self):
  for name in ('abc/','é'*70+'/'):
   self.assertEqual(list(m.framed_members(archive(name)))[0][0],name[:-1])
  with self.assertRaises(ValueError):list(m.framed_members(archive('abc/',tarfile.DIRTYPE,raw_type=tarfile.AREGTYPE)))
 def test_pax_extent_bound_precedes_payload(self):
  t=tarfile.TarInfo('././@PaxHeader');t.type=tarfile.XHDTYPE;t.size=m.PAX+1;raw=gzip.compress(t.tobuf(format=tarfile.USTAR_FORMAT),mtime=0);real=gzip.GzipFile.read;calls=[]
  def read(o,n):calls.append(n);return real(o,n)
  with patch.object(gzip.GzipFile,'read',read),self.assertRaises(ValueError):list(m.framed_members(raw))
  self.assertEqual(calls,[512])
if __name__=='__main__':unittest.main(verbosity=2)

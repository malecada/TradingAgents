import copy,io,json,os,unittest
from pathlib import Path
import codec01 as C
from local_store01 import LocalStore
from owned_io import _cleanup
ROOT=Path(__file__).resolve().parent
class Checks(unittest.TestCase):
 def spec(self,role='score-batches'):
  return dict(schema_version=1,kind='mcm-batch-output-bytes',role=role,dtype='<f8' if role=='score-batches' else '<f4',shape=[33,32],order='C',scope={k:'a'*64 for k in C.SCOPE},motifs=32,spent_samples=512)
 def fixture(self,role='score-batches'):
  d=self.spec(role);raw=bytes((i%251 for i in range(C.descriptor(d))));files={};pin=C.encode_stream(io.BytesIO(raw),d,lambda n,b:files.setdefault(n,b),chunk_bytes=64);return d,raw,files,pin
 def test_both_exact_formats(self):
  for role in ('score-batches','mcm-output'):
   d,raw,files,pin=self.fixture(role);out=[];result=C.verify_stream(files.__getitem__,pin,d,out.append)
   self.assertEqual(raw,b''.join(out));self.assertEqual(sorted(files),result['members']);self.assertFalse(result['representation_complete'])
 def test_each_body_corruption_or_absence(self):
  d,raw,files,pin=self.fixture()
  for n in files:
   for missing in (False,True):
    f=dict(files)
    if missing:del f[n]
    else:f[n]=f[n][:-1]+bytes([f[n][-1]^1])
    with self.subTest(n=n,missing=missing),self.assertRaises((KeyError,ValueError)):C.verify_stream(f.__getitem__,pin,d)
 def test_descriptor_mutations(self):
  d,raw,f,p=self.fixture()
  for k,v in [('dtype','<f4'),('order','F'),('shape',[34,32]),('motifs',31),('spent_samples',513),('schema_version',True),('role','mcm-output')]:
   bad=copy.deepcopy(d);bad[k]=v
   with self.subTest(k=k),self.assertRaises(ValueError):C.verify_stream(f.__getitem__,p,bad)
  for k in C.SCOPE:
   bad=copy.deepcopy(d);bad['scope'][k]='b'*64
   with self.assertRaises(ValueError):C.verify_stream(f.__getitem__,p,bad)
 def test_rehashed_footer_mutations(self):
  d,raw,f,p=self.fixture()
  for k,v in [('logical_bytes',1),('chunks',1),('head','b'*64),('raw_sha256','b'*64),('pages',[])]:
   files=dict(f);t=json.loads(files['terminal.json']);t[k]=v;files['terminal.json']=C.canonical(t)
   with self.assertRaises(ValueError):C.verify_stream(files.__getitem__,C.sha(files['terminal.json']),d)
 def test_extra_source_and_partial_sink(self):
  d,raw,f,p=self.fixture();out={}
  with self.assertRaises(ValueError):C.encode_stream(io.BytesIO(raw+b'!'),d,lambda n,b:out.setdefault(n,b),chunk_bytes=64)
  self.assertNotIn('terminal.json',out)
  out={};fatal=KeyboardInterrupt('actual opaque sink failure')
  def sink(n,b):
   if n=='chunk-00001.bin':raise fatal
   out[n]=b
  with self.assertRaises(KeyboardInterrupt) as caught:C.encode_stream(io.BytesIO(raw),d,sink,chunk_bytes=64)
  self.assertIs(caught.exception,fatal);self.assertIn('chunk-00000.bin',out);self.assertNotIn('terminal.json',out)
  (ROOT/'PARTIAL01.json').write_text(json.dumps({n:C.sha(b) for n,b in out.items()},sort_keys=True))
 def test_real_local(self):
  root=ROOT/'opaque-local01';root.mkdir(mode=0o700)
  d,raw,files,p=self.fixture();out=[]
  with LocalStore(root) as s:
   actual=C.encode_stream(io.BytesIO(raw),d,s.put,chunk_bytes=64)
   self.assertEqual(actual,p);s.verify(p,d,out.append)
   self.assertEqual(raw,b''.join(out))
   with self.assertRaises(ValueError):s.put('start.json',b'!')
   self.assertTrue(s.poisoned)
  self.assertTrue((root/'terminal.json').is_file())
 def test_cleanup_matrix(self):
  for primary in (KeyboardInterrupt('primary'),MemoryError('primary'),ValueError('primary')):
   for secondary in (OSError('close'),MemoryError('close'),KeyboardInterrupt('close')):
    seen=[]
    def fail():seen.append(1);raise secondary
    try:
     try:raise primary
     finally:_cleanup((fail,lambda:seen.append(2)))
    except BaseException as e:
     self.assertEqual(seen,[1,2]);self.assertIs(e,primary if isinstance(primary,(KeyboardInterrupt,MemoryError)) else secondary if isinstance(secondary,(KeyboardInterrupt,MemoryError)) else e)
 def test_deadline_and_caps(self):
  d=self.spec();d['shape']=[C.MAX_BYTES,32]
  with self.assertRaises(ValueError):C.descriptor(d)
  for n in (True,0,3,C.CHUNK+8):
   with self.assertRaises(ValueError):C.encode_stream(io.BytesIO(b''),self.spec(),lambda n,b:None,chunk_bytes=n)
  with self.assertRaises(ValueError):C.deadline(-1000000000)
if __name__=='__main__':unittest.main()

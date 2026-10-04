import copy,hashlib,io,json,unittest
from pathlib import Path
import codec01 as C
from local_store01 import LocalStore
ROOT=Path(__file__).resolve().parent
D=dict(schema_version=1,kind='mcm-batch-output-bytes',role='mcm-output',dtype='<f4',shape=[2,32],order='C',scope={k:'c'*64 for k in C.SCOPE},motifs=32,spent_samples=512)
def fixture():
 f={};p=C.encode_stream(io.BytesIO(bytes(range(256))),D,lambda n,b:f.setdefault(n,b),chunk_bytes=64);return f,p
def seal(f,p):
 raw=C.canonical(p);f['page-0000.json']=raw;t=json.loads(f['terminal.json']);t['pages'][0]['sha256']=C.sha(raw);f['terminal.json']=C.canonical(t);return C.sha(f['terminal.json'])
class Checks(unittest.TestCase):
 def test_validly_rehashed_bad_rows(self):
  for field,value in [('index',1),('offset',1),('bytes',63),('name','../out'),('raw_sha256','0'*64)]:
   f,pin=fixture();p=json.loads(f['page-0000.json']);p['rows'][0][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):C.verify_stream(f.__getitem__,seal(f,p),D)
  for how in ('reverse','duplicate','missing','extra'):
   f,pin=fixture();p=json.loads(f['page-0000.json']);r=p['rows']
   if how=='reverse':r.reverse()
   if how=='duplicate':r[1]=r[0]
   if how=='missing':r.pop()
   if how=='extra':r.append(r[0])
   with self.subTest(how=how),self.assertRaises(ValueError):C.verify_stream(f.__getitem__,seal(f,p),D)
 def test_semantic_header_footer(self):
  for offset in (0,8,16,24,32,64,-1):
   f,pin=fixture();b=bytearray(f['chunk-00000.bin']);b[offset]^=1
   if offset!=-1:b[-32:]=hashlib.sha256(b[:-32]).digest()
   f['chunk-00000.bin']=bytes(b);p=json.loads(f['page-0000.json']);p['rows'][0]['frame_sha256']=C.sha(bytes(b))
   with self.subTest(offset=offset),self.assertRaises(ValueError):C.verify_stream(f.__getitem__,seal(f,p),D)
 def test_full_membership(self):
  root=ROOT/'opaque-extra01';root.mkdir(mode=0o700)
  with LocalStore(root) as store:
   p=C.encode_stream(io.BytesIO(bytes(range(256))),D,store.put,chunk_bytes=64)
   (root/'unexpected').write_bytes(b'extra retained')
   with self.assertRaises(ValueError):store.verify(p,D)
 def test_callback_prefix_uncommitted(self):
  f,p=fixture();f['chunk-00002.bin']=b'bad';prefix=[]
  with self.assertRaises(ValueError):C.verify_stream(f.__getitem__,p,D,prefix.append)
  self.assertEqual(len(prefix),2)
 def test_large_extent_no_allocation(self):
  d=copy.deepcopy(D);d['shape']=[C.MAX_BYTES//128,32]
  self.assertEqual(C.descriptor(d),C.MAX_BYTES)
  calls=[]
  class Refused:
   def read(self,n):calls.append(n);raise OSError('opaque source unavailable')
  with self.assertRaises(OSError):C.encode_stream(Refused(),d,lambda n,b:None)
  self.assertEqual(calls,[C.CHUNK])
if __name__=='__main__':unittest.main()

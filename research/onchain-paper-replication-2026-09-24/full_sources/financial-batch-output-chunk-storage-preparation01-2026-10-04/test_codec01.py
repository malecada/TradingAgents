import io,json,unittest
from pathlib import Path
import codec01 as C
class CodecTests(unittest.TestCase):
 def spec(self):return dict(schema_version=1,kind='mcm-batch-output-bytes',role='score-batches',dtype='<f8',shape=[9,32],order='C',scope={k:'a'*64 for k in C.SCOPE},motifs=32,spent_samples=512)
 def test_roundtrip(self):
  raw=bytes(range(256))*9;store={}
  end=C.encode_stream(io.BytesIO(raw),self.spec(),lambda n,b:store.setdefault(n,b),chunk_bytes=128)
  out=[];got=C.verify_stream(lambda n:store[n],end,self.spec(),out.append)
  self.assertEqual(b''.join(out),raw);self.assertEqual(got['status'],'complete-byte-proof-only')
 def test_short(self):
  store={}
  with self.assertRaises(ValueError):C.encode_stream(io.BytesIO(b'x'),self.spec(),lambda n,b:store.setdefault(n,b),chunk_bytes=128)
  self.assertNotIn('terminal.json',store)
 def test_live_refused(self):
  with self.assertRaises(ValueError):C.publish_live(None,None,None)
if __name__=='__main__':unittest.main()

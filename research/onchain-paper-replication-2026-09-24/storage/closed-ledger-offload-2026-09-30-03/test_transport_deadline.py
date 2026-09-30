import importlib.util
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('candidate_transport',HERE/'transport.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_upload_deadline_and_reserved_payload(self):
  t=m.Transport({'public_key_path':'/synthetic/key.pub','user':'test','host':'example.invalid','port':23},rate=262144,maximum_payload_bytes=100000)
  with tempfile.TemporaryDirectory() as d,patch.object(m.base.subprocess,'run') as run:
   p=Path(d)/'file';p.write_bytes(b'123');t.put(p,'new/object')
   self.assertEqual(run.call_args.kwargs['timeout'],5400);self.assertEqual(t.remaining,99997)
 def test_download_deadline_and_reserved_payload(self):
  t=m.Transport({'public_key_path':'/synthetic/key.pub','user':'test','host':'example.invalid','port':23},rate=262144,maximum_payload_bytes=100000);t.sizes['new/object']=3
  with tempfile.TemporaryDirectory() as d,patch.object(m.base,'receive_diagnostic') as receive:
   t.get('new/object',Path(d)/'file');self.assertEqual(receive.call_args.kwargs['max_seconds'],5400);self.assertEqual(t.remaining,100000-32768)
if __name__=='__main__':unittest.main(verbosity=2)

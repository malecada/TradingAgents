import io,os,unittest
from pathlib import Path
import codec01 as C
from local_store01 import LocalStore
from check03 import D
ROOT=Path(__file__).resolve().parent
class Final(unittest.TestCase):
 def test_final_local(self):
  root=ROOT/'opaque-final04';root.mkdir(mode=0o700)
  with LocalStore(root) as s:
   p=C.encode_stream(io.BytesIO(bytes(range(256))),D,s.put,chunk_bytes=64)
   self.assertEqual(s.verify(p,D)['logical_bytes'],256)
   os.chmod(root/'chunk-00000.bin',0o644)
   with self.assertRaises(ValueError):s.verify(p,D)
 def test_partial_fd_retention(self):
  root=ROOT/'opaque-partial04';root.mkdir(mode=0o700)
  with LocalStore(root) as s:
   s.put('start.json',b'opaque')
   (root/'chunk-00000.bin').symlink_to('absent')
   with self.assertRaises(ValueError):s.put('chunk-00000.bin',b'never written')
   self.assertTrue(s.poisoned);self.assertTrue((root/'chunk-00000.bin').is_symlink())
if __name__=='__main__':unittest.main()

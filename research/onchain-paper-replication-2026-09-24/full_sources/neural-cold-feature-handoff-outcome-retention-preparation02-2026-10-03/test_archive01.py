import importlib.util,pathlib,tempfile,types,unittest
P=pathlib.Path(__file__).parent
if (P/'archive01.py').exists():
 s=importlib.util.spec_from_file_location('a',P/'archive01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
else:m=types.SimpleNamespace()
class Tests(unittest.TestCase):
 def test_copy_and_recovery_exact_bytes_modes_membership(self):
  self.assertTrue(hasattr(m,'snapshot'),'complete finite snapshot seam absent')
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);source=root/'source';source.mkdir();(source/'d').mkdir();(source/'d/a').write_bytes(b'\x00\xffraw');(source/'d/a').chmod(0o440)
   copy=root/'archive';rows=m.snapshot(source,copy,limit=65536);m.verify_tree(copy,rows,limit=65536)
   self.assertEqual((copy/'d/a').read_bytes(),b'\x00\xffraw');self.assertEqual((copy/'d/a').stat().st_mode&0o777,0o440)
   (copy/'d/a').chmod(0o640);(copy/'d/a').write_bytes(b'bad')
   with self.assertRaises(ValueError):m.verify_tree(copy,rows,limit=65536)
 def test_no_reuse_and_symlink_refusal(self):
  self.assertTrue(hasattr(m,'snapshot'),'snapshot seam absent')
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);src=root/'source';src.mkdir();(src/'a').write_bytes(b'a');out=root/'out';m.snapshot(src,out,limit=65536)
   with self.assertRaises(FileExistsError):m.snapshot(src,out,limit=65536)
   (src/'link').symlink_to(src/'a')
   with self.assertRaises(ValueError):m.snapshot(src,root/'bad',limit=65536)
 def test_missing_extra_hardlink(self):
  self.assertTrue(hasattr(m,'verify_tree'),'full recovery verifier absent')
  with tempfile.TemporaryDirectory() as d:
   import os
   root=pathlib.Path(d);src=root/'source';src.mkdir();(src/'a').write_bytes(b'a');out=root/'out';rows=m.snapshot(src,out,limit=65536)
   (out/'extra').write_bytes(b'x')
   with self.assertRaises(ValueError):m.verify_tree(out,rows,limit=65536)
   (out/'extra').unlink();os.link(out/'a',out/'link')
   with self.assertRaises(ValueError):m.verify_tree(out,rows,limit=65536)
if __name__=='__main__':unittest.main(verbosity=2)

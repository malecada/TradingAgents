import importlib.util,unittest,tempfile,os,copy,json
from pathlib import Path
P=Path(__file__).parent
s=importlib.util.spec_from_file_location('recovery',P/'recovery01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Checks(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=P);self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.src=self.root/'src';self.src.mkdir();(self.src/'empty').mkdir();(self.src/'body').write_bytes(b'opaque\x00bytes');os.chmod(self.src,0o750);os.chmod(self.src/'body',0o640)
 def test_roundtrip_typed_directories_root(self):
  manifest=m.scan(self.src);a=self.root/'archive.gz';info=m.pack(self.src,manifest,a);dest=self.root/'fresh';m.restore(a,info,manifest,dest)
  self.assertEqual(m.scan(dest),manifest);self.assertEqual(set(manifest['members'][0]),{'path','kind','mode','bytes','sha256'});self.assertEqual([r for r in manifest['members'] if r['kind']=='directory'][0],{'path':'empty','kind':'directory','mode':0o755})
 def test_symlink_hardlink_protected(self):
  for name,make in [('link',lambda p:p.symlink_to('body')),('hard',lambda p:os.link(self.src/'body',p)),('.env',lambda p:p.write_bytes(b'no secrets synthetic'))]:
   p=self.src/name;make(p)
   with self.assertRaises(ValueError):m.scan(self.src)
   p.unlink()
 def test_missing_extra_hash_mode(self):
  original=m.scan(self.src)
  for change in ('missing','extra','hash','mode'):
   bad=copy.deepcopy(original)
   if change=='missing':bad['members']=bad['members'][1:]
   elif change=='extra':bad['members'].append({'path':'absent','kind':'directory','mode':0o755})
   elif change=='hash':bad['members'][0]['sha256']='0'*64
   else:bad['members'][0]['mode']=0o600
   with self.assertRaises(ValueError):m.same(self.src,bad)
 def test_archive_hash_and_new_destination(self):
  manifest=m.scan(self.src);a=self.root/'a.gz';info=m.pack(self.src,manifest,a)
  with self.assertRaises(ValueError):m.restore(a,dict(info,sha256='0'*64),manifest,self.root/'bad')
  with self.assertRaises((ValueError,FileExistsError)):m.restore(a,info,manifest,self.src)
 def test_typed_rows_traversal(self):
  manifest=m.scan(self.src)
  for row in [{'path':'../evil','kind':'directory','mode':0o700},{'path':'.','kind':'directory','mode':0o700},{'path':'empty','kind':'directory','mode':0o700,'bytes':0}]:
   bad=copy.deepcopy(manifest);bad['members']=[row]
   with self.assertRaises(ValueError):m.validate(bad)
 def test_changed_source_refused(self):
  original=m.scan(self.src);(self.src/'body').write_bytes(b'changed')
  with self.assertRaises(ValueError):m.pack(self.src,original,self.root/'bad.gz')
if __name__=='__main__':unittest.main()

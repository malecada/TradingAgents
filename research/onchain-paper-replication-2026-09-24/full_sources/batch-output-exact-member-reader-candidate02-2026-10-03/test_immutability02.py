"""Actual local reader surface; tiny bytes, no numerical or authority imports."""
import hashlib,importlib.util,json,os,tempfile,unittest
from pathlib import Path
from types import MappingProxyType
P=Path(__file__).resolve().parent
source=Path(os.environ.get('READER_SOURCE',str(P/'exact_members02.py')))
s=importlib.util.spec_from_file_location('selected_reader',source);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def fixture(root):
 data=bytes(128);(root/'matrix.f32').write_bytes(data)
 v={'schema_version':1,'kind':'compact-mcm-output','stage_sha256':'ab'*32,'contract_sha256':'cd'*32,'stage_directory':'/original/stage','scope':{k:'12'*32 for k in m.SCOPES},'owner':'ef'*32,'rows':1,'motifs':32,'dtype':'<f4','order':'row-major','array_bytes':128,'array_sha256':hashlib.sha256(data).hexdigest(),'execution_admitted':False}
 raw=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode();(root/'manifest.json').write_bytes(raw);return hashlib.sha256(raw).hexdigest(),data
class Tests(unittest.TestCase):
 def test_actual_same_content_replacement_rebase(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha,data=fixture(root);bypassed=False
   try:
    with m.open_local(root,kind='mcm-output',document_sha256=sha) as r:
     original=r._files['matrix.f32'][0]
     (root/'replacement.tmp').write_bytes(data);os.replace(root/'replacement.tmp',root/'matrix.f32')
     with self.assertRaises(ValueError):r.check()
     try:del r._frozen
     except AttributeError:
      with self.assertRaises(AttributeError):r._pin=()
      # The original inode must remain refused even after attempted deletion.
      with self.assertRaises(ValueError):r.read_part('matrix.f32',0,8)
     else:
      files=dict(r._files);record,_=r._read('matrix.f32',128,expected=hashlib.sha256(data).hexdigest(),extent=128)
      self.assertNotEqual(record[0],original);files['matrix.f32']=record
      r._files=MappingProxyType(files);r._pin=tuple(sorted(files.items()));r._frozen=True
      self.assertEqual(r.read_part('matrix.f32',0,8),data[:8]);r.check();bypassed=True
   except ValueError:
    self.assertFalse(bypassed)
   self.assertFalse(bypassed,'normal del/setattr rebased the pinned original member inode')
 def test_all_slots_refuse_delete_and_reassign(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha,data=fixture(root)
   with m.open_local(root,kind='mcm-output',document_sha256=sha) as r:
    for name in r.__slots__:
     old=getattr(r,name)
     with self.subTest(name=name):
      with self.assertRaises(AttributeError):delattr(r,name)
      with self.assertRaises(AttributeError):setattr(r,name,old)
    with self.assertRaises(AttributeError):r.extra='x'
    self.assertFalse(hasattr(r,'__dict__'))
    with self.assertRaises(TypeError):r._files['matrix.f32']=()
    with self.assertRaises(TypeError):r._payload['matrix.f32']=()
    self.assertEqual(r.read_part('matrix.f32',0,8),data[:8])
   self.assertTrue(r.closed)
   with self.assertRaises(ValueError):r.read_part('matrix.f32',0,8)
if __name__=='__main__':unittest.main(verbosity=2)

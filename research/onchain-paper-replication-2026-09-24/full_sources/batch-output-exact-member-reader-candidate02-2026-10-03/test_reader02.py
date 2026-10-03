import hashlib,json,os,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import exact_members02 as m

def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def h(b):return hashlib.sha256(b).hexdigest()
def output(root):
 data=b'\x00'*128;(root/'matrix.f32').write_bytes(data)
 v={'schema_version':1,'kind':'compact-mcm-output','stage_sha256':'ab'*32,'contract_sha256':'cd'*32,'stage_directory':'/original/stage','scope':{k:'12'*32 for k in m.SCOPES},'owner':'ef'*32,'rows':1,'motifs':32,'dtype':'<f4','order':'row-major','array_bytes':128,'array_sha256':h(data),'execution_admitted':False}
 b=raw(v);(root/'manifest.json').write_bytes(b);return h(b),data
class Tests(unittest.TestCase):
 def test_dot_refused(self):
  for name in ('.','..','../a','a/b',''):
   with self.assertRaises(ValueError):m.member_name(name)
 def test_actual_raw_reader(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha,b=output(root)
   with m.open_local(root,kind='mcm-output',document_sha256=sha) as r:
    self.assertEqual(r.read_part('matrix.f32',4,16),b[4:20]);self.assertEqual(r.members,('matrix.f32',))
 def test_missing_extra_hash_swapped(self):
  for action in ('missing','extra','hash','swap','hardlink'):
   with self.subTest(action=action),tempfile.TemporaryDirectory() as d:
    root=Path(d);sha,b=output(root)
    if action=='missing':(root/'matrix.f32').unlink()
    elif action=='extra':(root/'extra').write_bytes(b'x')
    elif action=='hash':(root/'matrix.f32').write_bytes(b'x'*128)
    elif action=='hardlink':os.link(root/'matrix.f32',root/'extra')
    else:
     (root/'matrix.f32').rename(root/'moved');(root/'matrix.f32').symlink_to(root/'moved')
    with self.assertRaises((ValueError,OSError)):
     with m.open_local(root,kind='mcm-output',document_sha256=sha):pass
 def test_mutation_after_read_and_inode_swap(self):
  for same in (True,False):
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);sha,b=output(root)
    with self.assertRaises(ValueError):
     with m.open_local(root,kind='mcm-output',document_sha256=sha) as r:
      r.read_part('matrix.f32',0,8)
      if same:(root/'matrix.f32').write_bytes(b'x'*128)
      else:
       (root/'new').write_bytes(b);os.replace(root/'new',root/'matrix.f32')
 def test_body_fatal_close_uncertainty(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha,b=output(root);fatal=MemoryError('first');real=m.os.close;seen=[]
   def close(fd):
    seen.append(fd);real(fd);raise OSError('close uncertainty')
   active=[False]
   def switched(fd):
    if active[0]:return close(fd)
    return real(fd)
   with patch.object(m.os,'close',side_effect=switched):
    with self.assertRaises(MemoryError) as got:
     with m.open_local(root,kind='mcm-output',document_sha256=sha):
      active[0]=True;raise fatal
   self.assertIs(got.exception,fatal);self.assertEqual(len(seen),1)
 def test_bad_manifest_before_payload(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha,b=output(root)
   with self.assertRaises(ValueError):
    with m.open_local(root,kind='mcm-output',document_sha256='ab'*32):pass
if __name__=='__main__':unittest.main(verbosity=2)

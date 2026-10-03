import importlib.util,hashlib,json,unittest
from pathlib import Path
p=Path(__file__).with_name('member_ranges01.py');s=importlib.util.spec_from_file_location('ranges',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def contract():
 raw=bytes(range(24))
 return {'schema_version':1,'kind':'non-tail-exact-member-plan-v1','role':'score-batch','owner':'ab'*32,'stage_sha256':'cd'*32,'container_sha256':'ef'*32,'scope':{k:'12'*32 for k in m.SCOPES},'path':'stream/batches/chunk-000000000000.bin','dtype':'<f8','order':'row-major','rows':1,'motifs':32,'start_cell':0,'cells':3,'header_bytes':0,'bytes':24,'sha256':hashlib.sha256(raw).hexdigest(),'chunk_bytes':8},raw
class Tests(unittest.TestCase):
 def test_binary_exact(self):
  v,b=contract();q=m.validate(v);self.assertEqual(list(m.ranges(q)),[(0,8),(8,8),(16,8)])
  r=m.verify_parts(q,[b[:8],b[8:16],b[16:]]);self.assertEqual(r['sha256'],v['sha256']);self.assertFalse(r['execution_admitted'])
 def test_refuse_algebra_types(self):
  v,b=contract()
  for k,x in [('bytes',True),('motifs',31),('dtype','<f4'),('order','column-major'),('start_cell',31),('header_bytes',128),('path','../x'),('chunk_bytes',1048577),('owner','x')]:
   with self.assertRaises(ValueError):m.validate(dict(v,**{k:x}))
 def test_exact_complete_stream(self):
  v,b=contract();q=m.validate(v)
  for parts in ([b[:8]], [b[:8],b[8:16],b[16:],b'x'],[b[:9],b[9:16],b[16:]],[b'x'*8,b[8:16],b[16:]]):
   with self.assertRaises(ValueError):m.verify_parts(q,parts)
 def test_output_roles_no_recast(self):
  v,b=contract()
  for role,header in [('mcm-output',0),('graph-artifact-mcm',128)]:
   u=dict(v,role=role,dtype='<f4',start_cell=0,cells=32,bytes=128+header,header_bytes=header)
   self.assertEqual(m.validate(u)['bytes'],128+header)
 def test_no_activation_or_authority(self):
  with self.assertRaisesRegex(RuntimeError,'genuine'):m.activate(None)
 def test_detach_and_unknown_fields(self):
  v,b=contract();q=m.validate(v);v['scope']['graph']='98'*32;self.assertNotEqual(q['scope'],v['scope'])
  with self.assertRaises(ValueError):m.validate(dict(v,authority=True))
if __name__=='__main__':unittest.main(verbosity=2)

import hashlib,importlib.util,json,struct,tempfile,unittest,sys,types
from pathlib import Path
D=Path(__file__).resolve().parent
P=D/'candidate/tradingagents/research/onchain_replication/mcm_raw_parts.py'
pkg=types.ModuleType('raw_parts_probe');pkg.__path__=[str(P.parent),str(D.parents[3]/'tradingagents/research/onchain_replication')];sys.modules[pkg.__name__]=pkg
s=importlib.util.spec_from_file_location('raw_parts_probe.mcm_raw_parts',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Bits(unittest.TestCase):
 def test_original_cast_bit_join_and_signed_zero(self):
  values=[0.,-0.,1.,0.5,2**-149,2**-150,1-2**-25,0.5+2**-25,2**-126]
  raw64=b''.join(struct.pack('<d',x) for x in values);raw32=b''.join(struct.pack('<f',x) for x in values)
  result=m.cast_equal(raw64,raw32);self.assertEqual(result['cells'],len(values));self.assertEqual(result['f32_sha256'],hashlib.sha256(raw32).hexdigest())
  changed=bytearray(raw32);changed[7]=0
  with self.assertRaisesRegex(ValueError,'bits differ'):m.cast_equal(raw64,bytes(changed))
 def test_chunk_order_extent_and_kind_are_distinct(self):
  raw=b'\x00'*16
  a=m.descriptor('score-batch-f64','a'*64,0,0,raw,cells=2,part_bytes=16)
  b=m.descriptor('mcm-output-f32','a'*64,0,0,raw,cells=4,part_bytes=16)
  self.assertEqual(a['dtype'],'<f8');self.assertEqual(b['dtype'],'<f4');self.assertNotEqual(a,b)
  for args in [(1,0,raw),(0,8,raw),(0,0,raw[:-1])]:
   with self.assertRaises(ValueError):m.descriptor('mcm-output-f32','a'*64,*args,cells=4,part_bytes=16)
  with self.assertRaises(ValueError):m.layout('mcm-output-f32',4,4194308)
 def test_nonfinite_or_substituted_values_refuse(self):
  for x in [float('inf'),float('nan')]:
   with self.assertRaises(ValueError):m.cast_equal(struct.pack('<d',x),struct.pack('<f',x))
  with self.assertRaisesRegex(ValueError,'bits differ'):m.cast_equal(struct.pack('<d',0.25),struct.pack('<f',0.5))
 def test_pinned_stream_full_eof_wrong_hash_and_final_mutation(self):
  with tempfile.TemporaryDirectory(dir=D) as directory:
   path=Path(directory)/'original.f32';raw=b''.join(struct.pack('<f',x) for x in [0.,-0.,0.5,1.]);path.write_bytes(raw)
   kw=dict(kind='mcm-output-f32',cells=4,part_bytes=8,expected_sha256=hashlib.sha256(raw).hexdigest())
   self.assertEqual(b''.join(x[2] for x in m.parts(path,**kw,lease=lambda:None)),raw)
   wrong=dict(kw,expected_sha256='f'*64)
   with self.assertRaisesRegex(ValueError,'EOF/hash'):list(m.parts(path,**wrong,lease=lambda:None))
   calls=[]
   def mutation():
    calls.append(1)
    if len(calls)==4:path.write_bytes(raw[:-4]+struct.pack('<f',0.25))
   with self.assertRaisesRegex(ValueError,'changed'):list(m.parts(path,**kw,lease=mutation))
   path.write_bytes(raw[:-1])
   with self.assertRaisesRegex(ValueError,'extent'):list(m.parts(path,**kw,lease=lambda:None))
if __name__=='__main__':unittest.main(verbosity=2)

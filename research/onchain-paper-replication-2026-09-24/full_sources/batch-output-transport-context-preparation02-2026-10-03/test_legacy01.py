import hashlib,importlib.util,json,os,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
import non_tail_context as m
# Reuse real accepted byte-format fixture generators, no numerical package imports.
D=HERE.parent/'batch-output-exact-member-reader-candidate02-2026-10-03'
spec=importlib.util.spec_from_file_location('format_fixtures',D/'test_formats02.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
def limits(**kw):return dict(max_rounded_bytes=1048576,max_commands=100,max_parts=100,part_bytes=128,deadline_seconds=10,**kw)
class Tests(unittest.TestCase):
 def setup(self,d,kind='score-batches'):
  root=Path(d)/'source';root.mkdir()
  if kind=='score-batches':ref=f.batches(root)
  elif kind=='graph-artifact':ref=f.graph(root)
  else:
   body=b'\0'*128;(root/'matrix.f32').write_bytes(body)
   v=dict(schema_version=1,kind='compact-mcm-output',stage_sha256='12'*32,contract_sha256='13'*32,stage_directory='/synthetic/stage',scope={k:'14'*32 for k in m.reader.SCOPES},owner='15'*32,rows=1,motifs=32,dtype='<f4',order='row-major',array_bytes=128,array_sha256=hashlib.sha256(body).hexdigest(),execution_admitted=False)
   ref=f.save(root,'manifest.json',v)
  return root,ref
 def test_complete_all_roles(self):
  for kind in ('score-batches','mcm-output','graph-artifact'):
   with tempfile.TemporaryDirectory() as d:
    root,ref=self.setup(d,kind);copy=Path(d)/'recovered';shutil.copytree(root,copy)
    with m.open_context(root,kind=kind,document_sha256=ref,limits=limits()) as c:
     for name in c.members:
      for offset,size in c.ranges(name):self.assertEqual(len(c.read_original(name,offset,size)),size)
     result=c.verify_recovery(copy);self.assertFalse(result['recovery_authority']);self.assertEqual(result['local_bytes_retired'],0)
     self.assertGreater(c.spent['rounded_bytes'],0);self.assertEqual(result['complete_original_members'],len(c.inventory))
     with self.assertRaises(NotImplementedError):c.activate_transport(object())
 def test_no_dict_authority(self):
  with self.assertRaises(TypeError):m.Context({},limits())
 def test_mutation_revoke_no_refund(self):
  with tempfile.TemporaryDirectory() as d:
   root,ref=self.setup(d)
   with self.assertRaises(ValueError):
    with m.open_context(root,kind='score-batches',document_sha256=ref,limits=limits()) as c:
     name=c.members[0];c.read_original(name,0,128);spent=dict(c.spent);(root/name).write_bytes(b'1'*256)
     try:c.read_original(name,128,128)
     finally:self.assertGreaterEqual(c.spent['rounded_bytes'],spent['rounded_bytes']);self.assertTrue(c.revoked)
 def test_missing_recovery_preserves_original(self):
  with tempfile.TemporaryDirectory() as d:
   root,ref=self.setup(d);copy=Path(d)/'recovered';shutil.copytree(root,copy);(copy/'chunk-000000000000.bin').unlink()
   with self.assertRaises((ValueError,FileNotFoundError)):
    with m.open_context(root,kind='score-batches',document_sha256=ref,limits=limits()) as c:c.verify_recovery(copy)
   self.assertTrue((root/'chunk-000000000000.bin').exists())
 def test_refusal_dot_order_and_mutable_limits(self):
  with tempfile.TemporaryDirectory() as d:
   root,ref=self.setup(d);lim=limits()
   with self.assertRaises(ValueError):
    with m.open_context(root,kind='score-batches',document_sha256=ref,limits=lim) as c:
     lim['max_commands']=999999
     self.assertEqual(c.policy['max_commands'],100)
     c.read_original('.',0,1)
 def test_order_refusal(self):
  with tempfile.TemporaryDirectory() as d:
   root,ref=self.setup(d)
   with self.assertRaises(ValueError):
    with m.open_context(root,kind='score-batches',document_sha256=ref,limits=limits()) as c:c.read_original(c.members[0],128,128)
 def test_budget_rounding_no_refund(self):
  b=m.Reservations(limits());b.reserve(1);self.assertEqual(b.spent['rounded_bytes'],32768);b.reserve(32769);self.assertEqual(b.spent['rounded_bytes'],98304)
  x=limits();x['max_commands']=1;b=m.Reservations(x);b.reserve(1)
  with self.assertRaises(ValueError):b.reserve(1)
  self.assertEqual(b.spent['commands'],1);self.assertTrue(b.revoked)
 def test_deadline(self):
  with patch.object(m.time,'monotonic',return_value=0):b=m.Reservations(limits())
  with patch.object(m.time,'monotonic',return_value=11):
   with self.assertRaises(TimeoutError):b.reserve(1)
  self.assertTrue(b.revoked)
 def test_first_fatal_all_cleanup(self):
  a=MemoryError('first');b=SystemExit('later');seen=[]
  def bad():seen.append(1);raise b
  with self.assertRaises(MemoryError) as got:m.finish([bad,lambda:seen.append(2)],a)
  self.assertIs(got.exception,a);self.assertEqual(seen,[1,2])
 def test_immutability(self):
  b=m.Reservations(limits())
  for name in b.__slots__:
   with self.assertRaises(AttributeError):delattr(b,name)
   with self.assertRaises(AttributeError):setattr(b,name,None)
 def test_bool_limits(self):
  x=limits();x['max_parts']=True
  with self.assertRaises(ValueError):m.Reservations(x)
 def test_shared_no_refund_across_containers(self):
  budget=m.Reservations(limits())
  with tempfile.TemporaryDirectory() as d:
   root,ref=self.setup(d)
   with m.open_context(root,kind='score-batches',document_sha256=ref,limits=budget) as c:c.read_original(c.members[0],0,128)
   first=dict(budget.spent)
   with m.open_context(root,kind='score-batches',document_sha256=ref,limits=budget) as c:c.read_original(c.members[0],0,128)
   self.assertEqual(budget.spent['rounded_bytes'],2*first['rounded_bytes'])
 def test_actual_context_firstfatal_close_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root,ref=self.setup(d);fatal=MemoryError('actual first');real=m.reader.os.close;closed=[]
   def close(fd):closed.append(fd);real(fd);raise OSError('close uncertain')
   cm=m.open_context(root,kind='score-batches',document_sha256=ref,limits=limits());c=cm.__enter__()
   with patch.object(m.reader.os,'close',side_effect=close):
    self.assertFalse(cm.__exit__(type(fatal),fatal,None))
   self.assertEqual(len(closed),1);self.assertTrue(c.revoked)
 def test_recovery_swapped_hash(self):
  with tempfile.TemporaryDirectory() as d:
   root,ref=self.setup(d);copy=Path(d)/'recovered';shutil.copytree(root,copy)
   with self.assertRaises(ValueError):
    with m.open_context(root,kind='score-batches',document_sha256=ref,limits=limits()) as c:
     for name in c.members:
      for offset,count in c.ranges(name):c.read_original(name,offset,count)
     (copy/'chunk-000000000000.bin').write_bytes(b'1'*256);c.verify_recovery(copy)
if __name__=='__main__':unittest.main()

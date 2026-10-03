"""Pure policy/extracted byte-loop stand-ins, not study authority."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('candidate_consumer',P/'held_score_consumer.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
H='a'*64
class Policy(unittest.TestCase):
 def policy(self):return {'schema_version':1,'kind':m.KIND,'targets':{H:{'output':'held-a.json'}},'part_bytes':8,'max_read_bytes':1024,'max_members':10}
 def test_valid(self):self.assertEqual(m._policy(self.policy(),[H],['held-a.json']),self.policy())
 def test_refuse(self):
  for field,value in [('schema_version',True),('part_bytes',7),('max_read_bytes',True),('max_members',32768),('kind','scientific'),('extra',0),('targets',{})]:
   p=self.policy();p[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):m._policy(p,[H],['held-a.json'])
 def test_unregistered_output(self):
  with self.assertRaises(ValueError):m._policy(self.policy(),[H],[])
 def test_complete_byte_loop(self):
  class Reader:
   members=('chunk-000000000000.bin','chunk-000000000001.bin')
   def read_part(self,n,o,c):return (b'a'*16 if n.endswith('000.bin') else b'b'*8)[o:o+c]
  r=m._read_all(Reader(),3,2,8,24,2)
  self.assertEqual(r,{'members':2,'parts':3,'bytes':24,'sha256':hashlib.sha256(b'a'*16+b'b'*8).hexdigest()})
 def test_missing_extra_order_short(self):
  class Reader:
   members=()
   def read_part(self,n,o,c):return b'x'*(c-1)
  for names in [(),('wrong',),('chunk-000000000001.bin','chunk-000000000000.bin'),('chunk-000000000000.bin','chunk-000000000001.bin')]:
   r=Reader();r.members=names
   with self.subTest(names=names),self.assertRaises(ValueError):m._read_all(r,3,2,8,24,2)
 def test_fatal_identity(self):
  fatal=MemoryError('first')
  class Reader:
   members=('chunk-000000000000.bin',)
   def read_part(self,*a):raise fatal
  with self.assertRaises(MemoryError) as e:m._read_all(Reader(),1,1,8,8,1)
  self.assertIs(e.exception,fatal)
if __name__=='__main__':unittest.main(verbosity=2)

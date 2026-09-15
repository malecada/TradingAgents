import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import os
ROOT=Path(__file__).resolve().parents[2];HERE=ROOT/'research/defi-depth-2026-09-15'
s=importlib.util.spec_from_file_location('heritage',HERE/'heritage_source.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
class HeritageTests(unittest.TestCase):
 def test_metadata_no_values_and_hash(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'u.json';p.write_text('{"by_symbol":{"inventedtoken":{"circulating_supply":123.5}},"2024-01":["inventedtoken"]}')
   r=h.inspect_metadata(p,4096);self.assertEqual(r['status'],'complete')
   self.assertNotIn('inventedtoken',json.dumps(r));self.assertNotIn('123.5',json.dumps(r));self.assertIn('circulating_supply',r['structure']['field_types'])
   self.assertEqual(r['sha256'],h.digest(p.read_bytes()))
 def test_symlink_file_and_parent_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'real';p.mkdir();(p/'x.json').write_text('{}')
   (root/'dirlink').symlink_to(p);(root/'filelink').symlink_to(p/'x.json')
   for target in [root/'dirlink'/'x.json',root/'filelink']:self.assertEqual(h.inspect_metadata(target,100)['status'],'unavailable')
 def test_missing_oversize_invalid_duplicate(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';self.assertEqual(h.inspect_metadata(p,8)['status'],'unavailable')
   for body in ['x'*9,'notjson','{"a":1,"a":2}']:
    p.write_text(body);self.assertEqual(h.inspect_metadata(p,8 if len(body)==9 else 100)['status'],'unavailable')
 def test_partial_error_and_concurrent_change_bytes_charged(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'u.json';p.write_text('{"map": {"inventedtoken": 1}}')
   real_read=os.read;calls=0
   def partial(fd,size):
    nonlocal calls
    calls+=1
    if calls==1:return real_read(fd,5)
    raise OSError('invented mid-read failure')
   with patch.object(h.os,'read',partial):r=h.inspect_metadata(p,100)
   self.assertEqual(r['bytes'],5);self.assertEqual(r['sha256'],h.digest(p.read_bytes()[:5]));self.assertFalse(r['body_complete'])
   real_fstat=os.fstat;calls=0
   def changing(fd):
    nonlocal calls
    calls+=1
    if calls==2:p.write_text('{"map": {"inventedtoken": 2}}')
    return real_fstat(fd)
   with patch.object(h.os,'fstat',changing):r=h.inspect_metadata(p,100)
   self.assertEqual(r['status'],'unavailable');self.assertEqual(r['bytes'],len(b'{"map": {"inventedtoken": 1}}'));self.assertFalse(r['body_complete'])
   self.assertNotEqual(r['pre_identity'],r['post_identity'])
 def test_source_never_executes(self):
  r=h.inspect_code(b'raise RuntimeError("do not execute")\ndef f(): pass\n','fake.py')
  self.assertEqual(r['status'],'complete');self.assertEqual(r['function_count'],1)
 def test_denominators_and_no_q6_external_read(self):
  for question,count in [('q4',24),('q6',14)]:
   spec=json.loads((HERE/(question+'-design.json')).read_text());outputs={};calls=[]
   def fake(path,cap):calls.append(path);return h.missing('invented missing')
   result=h.inspect(spec,{path:b'x=1\n' for path in spec['source_code_inventory']},lambda k,v:outputs.update({k:v}),fake)
   outputs['summary.json']=result;ids,names=h.inventory(spec)
   self.assertEqual(len(result['cells']),count);self.assertEqual(set(outputs),set(names));self.assertEqual(len(calls),8 if question=='q4' else 0)
   self.assertFalse(result['financial_outcomes'])
if __name__=='__main__':unittest.main()

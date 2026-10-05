"""One actual lower-bound counterexample, an inverse, and six reused source checks."""
import ast,difflib,importlib.util,json,os,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
P=Path(__file__).parent
BEFORE=P.parent/'financial-wrapper-git-watch-hardlink-retry-source01-2026-10-05'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
OLD=load('withheld_watch01',BEFORE/'watch01.py');NEW=load('corrected_watch02',P/'watch01.py')
REUSED=load('accepted_unchanged_checks',BEFORE/'test_watch.py')
REUSED.NEW=NEW
class Precedence(unittest.TestCase):
 def exercise(self,module,stage,bound):
  with tempfile.TemporaryDirectory() as temporary:
   parent=Path(temporary);root=parent/'owned';objects=root/'fresh.git'/'objects';objects.mkdir(parents=True);body=objects/'body';alias=parent/'outside-alias'
   body.write_bytes(b'1234' if stage=='initial' else (b'12' if bound=='logical' else b''))
   policy=dict(module.POLICY)
   if bound=='logical':policy['logical']=3
   else:
    directories=sum(x.stat().st_blocks*512 for x in (root,root/'fresh.git',objects))
    # A real allocated block is larger than an empty file; refuse its observed charge.
    policy['allocated']=directories+4095
   waits=[];disk=module.shutil.disk_usage;created=False
   if stage=='initial':os.link(body,alias)
   def publish(path):
    nonlocal created
    if stage=='rejoin' and not created:os.link(body,alias);body.write_bytes(b'1234');created=True
    return disk(path)
   def shrink(delay):
    waits.append(delay);alias.unlink();body.write_bytes(b'12' if bound=='logical' else b'')
   with patch.object(module,'POLICY',policy),patch.object(module,'time',SimpleNamespace(monotonic=time.monotonic,sleep=shrink)),patch.object(module,'shutil',SimpleNamespace(disk_usage=publish)):
    if module is OLD:
     result=module.census(root,owned_fetch_objects=objects)
     self.assertEqual(result['complete_attempts'],2);self.assertEqual(waits,[.1])
     self.assertLessEqual(result['logical_bytes'],policy['logical']);self.assertLessEqual(result['allocated_bytes'],policy['allocated'])
     return {'withheld_accepted_after_observed_breach':True,'accepted':result}
    with self.assertRaisesRegex(ValueError,'whole .*logical/allocated cap') as caught:module.census(root,owned_fetch_objects=objects)
    self.assertNotIsInstance(caught.exception,module.ChangingTree);self.assertEqual(waits,[])
    self.assertEqual(body.stat().st_size,4);self.assertEqual(body.stat().st_nlink,2)
    return {'corrected_immediate_fatal':True,'retry_requests':0}
 def test_actual_observed_breach_cannot_shrink_into_success(self):
  rows=[]
  for stage in ('initial','rejoin'):
   for bound in ('logical','allocated'):
    with self.subTest(stage=stage,bound=bound):rows.append({'stage':stage,'bound':bound,'red':self.exercise(OLD,stage,bound),'green':self.exercise(NEW,stage,bound)})
  print('COUNTEREXAMPLE_ROWS '+json.dumps(rows,sort_keys=True))
 def test_exact_inverse_and_unchanged_retry_caller_context(self):
  lines=(P/'watch01.py.ndiff').read_text().splitlines(True)
  self.assertEqual(''.join(difflib.restore(lines,1)),(BEFORE/'watch01.py').read_text());self.assertEqual(''.join(difflib.restore(lines,2)),(P/'watch01.py').read_text())
  for name in ('recover01.py','utilities/owned_io.py'):self.assertEqual((P/name).read_bytes(),(BEFORE/name).read_bytes())
  def census(path):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='census')
  self.assertEqual(ast.dump(census(P/'watch01.py'),include_attributes=False),ast.dump(census(BEFORE/'watch01.py'),include_attributes=False));self.assertEqual(NEW.POLICY,OLD.POLICY)
if __name__=='__main__':
 suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(REUSED.Watch),unittest.defaultTestLoader.loadTestsFromTestCase(Precedence)])
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 raise SystemExit(not result.wasSuccessful())

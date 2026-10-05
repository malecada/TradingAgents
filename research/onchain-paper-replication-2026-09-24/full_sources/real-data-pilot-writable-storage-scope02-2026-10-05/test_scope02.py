import ast,difflib,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=Path('tradingagents/research/onchain_replication');T=D/'candidate'/P;A=D.parent/'real-data-pilot-writable-storage-scope01-2026-10-05'
pkg=types.ModuleType('scope02');pkg.__path__=[str(T),str(ROOT/P)];sys.modules['scope02']=pkg
import scope02.real_pilot_storage as m
L={'max_allocated_bytes':1000000,'max_logical_bytes':1000000,'max_entries':1000,'max_depth':16,'max_scan_seconds':5}
def setup(root):
 (root/'research_artifacts').mkdir();(root/'research_runs').mkdir();(root/'research_runs/.lock').write_bytes(b'lock')
 return {'schema_version':2,'kind':m.KIND,'authority_root':str(root),'experiment':m.EXPERIMENT,'roots':[str(root/'research_artifacts'),str(root/'research_runs'/m.EXPERIMENT)],'shared_files':[str(root/'research_runs/.lock')],'limits':dict(L)}
class Checks(unittest.TestCase):
 def test_absent_birth_and_disappearance_refusal(self):
  with tempfile.TemporaryDirectory(dir=D) as t:
   root=Path(t);b=setup(root);w=m.WritableUnion(b,root);first=w.check()
   self.assertIsNone(first['root_identities'][1]['inode']);self.assertEqual(first['logical_file_bytes'],4)
   w.target.mkdir();(w.target/'claim.json').write_text('metadata');second=w.check();self.assertIsNotNone(second['root_identities'][1]['inode']);self.assertEqual(second['logical_file_bytes'],12)
   w.target.rename(w.target.with_name('retained-old'))
   with self.assertRaisesRegex(ValueError,'disappeared'):w.check()
   w.target.mkdir()
   with self.assertRaisesRegex(ValueError,'rebirth'):w.check()
 def test_readonly_sibling_hardlink_but_shared_file_strict(self):
  with tempfile.TemporaryDirectory(dir=D) as t:
   root=Path(t);b=setup(root);old=root/'research_runs/historical';old.mkdir();(old/'claim.json').write_text('old');os.link(old/'claim.json',old/'copy.json')
   m.WritableUnion(b,root).check()
   os.link(root/'research_runs/.lock',old/'lock-alias')
   with self.assertRaisesRegex(ValueError,'lock type/link'):m.WritableUnion(b,root).check()
   (old/'lock-alias').unlink();(root/'research_runs/.lock').unlink();(root/'research_runs/.lock').symlink_to(old/'claim.json')
   with self.assertRaises(OSError):m.WritableUnion(b,root).check()
 def test_foreign_scope_parent_and_aggregate_refusal(self):
  with tempfile.TemporaryDirectory(dir=D) as t:
   root=Path(t);b=setup(root);bad={**b,'experiment':'foreign'}
   with self.assertRaisesRegex(ValueError,'experiment'):m.WritableUnion(bad,root)
   w=m.WritableUnion(b,root);(root/'research_runs').rename(root/'old-parent');(root/'research_runs').mkdir();(root/'research_runs/.lock').write_text('lock')
   with self.assertRaisesRegex(ValueError,'parent replaced'):w.check()
   (root/'research_artifacts/a').write_text('123456');target=root/'research_runs'/m.EXPERIMENT;target.mkdir();(target/'b').write_text('123456');b['limits']['max_logical_bytes']=15
   with self.assertRaises(m.StorageLimit) as error:m.WritableUnion(b,root).check()
   self.assertEqual(error.exception.observation['logical_file_bytes'],16)
 def test_exact_source01_inverse(self):
  delta=json.loads((D/'SOURCE_DELTA01.json').read_text())
  for name,row in delta.items():
   source=(T/name).read_text();lines=source.splitlines(True)
   for e in reversed(row['edits']):self.assertEqual(lines[e['new_start']:e['new_end']],e['new']);lines[e['new_start']:e['new_end']]=e['old']
   self.assertEqual(''.join(lines),(A/'candidate'/P/name).read_text());ast.parse(source)
  self.assertFalse({'torch','numpy','scipy','networkx'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)

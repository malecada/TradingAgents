"""Actual Source04 read-only Git/metadata checks; no admission or array decode."""
import ast,copy,json,pathlib,runpy,sys,types,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent
BASE=P.parent/'held-consumer-auxiliary-source-pins-preparation01-2026-10-03'
RECEIPT=json.loads((P.parent/'held-consumer-root-source-composition04-2026-10-03/SOURCE_COMPOSITION04.json').read_bytes())
ROOT=pathlib.Path(RECEIPT['source_root']);SOURCE=RECEIPT['actual_source_commit'];ANCHOR=RECEIPT['actual_148_package_anchor']
ROWS=[{'path':r['path'] if 'path' in r else r['target'],'sha256':r['sha256'],'bytes':r['bytes']} for r in RECEIPT['source_entries']]
ROWS.sort(key=lambda r:r['path'])
OLD='--baseline' in sys.argv;sys.argv=[v for v in sys.argv if v!='--baseline']
B=runpy.run_path(str(ROOT/'fixture_tools/capsule_builder01.py' if OLD else P/'capsule_builder01.py'))
G=runpy.run_path(str(BASE/'generate_inputs01.py' if OLD else P/'generate_inputs01.py'))
class Tests(unittest.TestCase):
 def test_actual_source04_full_source_then_null_roles(self):
  plan=B['held_source_plan'](ROOT,SOURCE,ANCHOR,ROWS)
  self.assertEqual((plan['source_count'],plan['package_count']),(199,148));self.assertEqual(len(plan['source_origins']),199)
  result=G['held_input_plan']({},plan)
  self.assertFalse(result['execution_admitted']);self.assertEqual(len(result['remaining_roles']),15);self.assertIsNone(result['auxiliary_metadata'])
  (P/('ACTUAL_BASELINE_PLAN.json' if OLD else 'ACTUAL_SOURCE04_READBACK.json')).write_text(json.dumps({'source_plan':plan,'null_role_input_plan':result,'qualification':'actual Source04 original bodies; candidate helper not installed or admitted'},sort_keys=True,indent=2)+'\n')
 def test_actual_source04_package_changed_only_selected_dispatch(self):
  self.assertEqual(B['HELD_SOURCE04_PACKAGE_CHANGES']['resource_fixture.py'],'3ea9902ec4067edc59bc897081c5ad5f6738350ccd3a339b0b423c863212a97e')
 def test_unknown_anchor_and_changed_lineage_refused(self):
  actual=B['_held_git'];fn=B['held_source_plan'];ns=fn.__globals__
  def git(root,*args):
   if args==('show','-s','--format=%P',ANCHOR):return (B['HELD_S2']+'\n').encode()
   return actual(root,*args)
  with patch.dict(ns,_held_git=git),self.assertRaisesRegex(ValueError,'accepted held Source04 lineage'):fn(ROOT,SOURCE,ANCHOR,ROWS)
 def test_unlisted_current_package_and_nondescendant_refused(self):
  actual=B['_held_git'];fn=B['held_source_plan'];ns=fn.__globals__
  for corruption in ['extra-package','not-descendant']:
   def git(root,*args):
    if corruption=='extra-package' and args==('ls-tree','-r','--name-only',SOURCE):return actual(root,*args)+b'tradingagents/research/unselected.py\n'
    if corruption=='not-descendant' and args==('merge-base','--is-ancestor',B['HELD_SOURCE04'],SOURCE):raise ValueError('synthetic non-descendant')
    return actual(root,*args)
   with self.subTest(corruption=corruption),patch.dict(ns,_held_git=git),self.assertRaises(ValueError):fn(ROOT,SOURCE,ANCHOR,ROWS)
 def test_package_hash_missing_and_extra_rows_refuse(self):
  for mode in ['hash','missing','extra']:
   rows=copy.deepcopy(ROWS)
   if mode=='hash':next(r for r in rows if r['path'].endswith('/resource_fixture.py'))['sha256']='0'*64
   elif mode=='missing':rows.pop()
   else:rows.append({'path':'unknown.py','sha256':'0'*64,'bytes':1})
   with self.subTest(mode=mode),self.assertRaises(ValueError):B['held_source_plan'](ROOT,SOURCE,ANCHOR,rows)
if __name__=='__main__':unittest.main(verbosity=2)

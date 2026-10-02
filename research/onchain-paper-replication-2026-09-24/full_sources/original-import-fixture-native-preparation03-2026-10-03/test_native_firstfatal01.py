"""Actual helper AST with stdlib-only owned IO; no guard or process execution."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'original-import-fixture-native-preparation02-2026-10-03/resources.py'
SOURCE=Path(sys.argv.pop(1)) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else HERE/'resources.py'
IO=HERE.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py'
def namespace():
 t=ast.parse(SOURCE.read_text());names={'_native_select','_native_reason','_native_finalize'};nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names]
 if len(nodes)!=3:raise AssertionError('selected-native fatal/finalization helpers are absent')
 spec=importlib.util.spec_from_file_location('actual_owned_io',IO);io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
 ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),ns);return ns,io
class SelectedNative(unittest.TestCase):
 def test_first_actual_fatal_identity_survives_later_fatal(self):
  ns,io=namespace();first=MemoryError('first');later=KeyboardInterrupt()
  self.assertIs(ns['_native_select'](first,later,io),first)
 def test_later_first_fatal_promotes_over_ordinary(self):
  ns,io=namespace();later=MemoryError('first');self.assertIs(ns['_native_select'](ValueError(),later,io),later)
 def test_cleanup_wrapper_embedded_fatal_is_preserved(self):
  ns,io=namespace();first=MemoryError('inside');wrapper=io.CleanupFailure();wrapper.failures=(ValueError(),first)
  self.assertIs(ns['_native_select'](wrapper,KeyboardInterrupt(),io),first)
 def test_genuine_cleanup_uncertainty_does_not_disappear(self):
  ns,io=namespace();wrapper=io.CleanupFailure();self.assertIs(ns['_native_select'](ValueError(),wrapper,io),wrapper)
 def test_diagnostic_fatal_cannot_replace_original_fatal(self):
  ns,io=namespace()
  class BadMemory(MemoryError):
   def __str__(self):raise KeyboardInterrupt('format')
  original=BadMemory();state={'limit_reason':None};selected=ns['_native_reason'](state,original,io)
  self.assertIs(selected,original);self.assertEqual(state['phase'],'failed');self.assertIsNotNone(state['limit_reason'])
 def test_all_independent_actions_run_after_fatal(self):
  ns,io=namespace();seen=[];first=MemoryError('stop');later=KeyboardInterrupt('storage');state={'phase':'running','limit_reason':None}
  def action(name,error=None):
   def invoke():
    seen.append(name)
    if error is not None:raise error
   return invoke
  actions=[(n,action(n,e)) for n,e in [('ignore-term',None),('ignore-int',None),('stop',first),('readback',None),('storage',later),('publish',None),('final',None),('sync',None),('restore-term',None),('restore-int',None)]]
  primary,failed=ns['_native_finalize'](state,None,actions,io)
  self.assertIs(primary,first);self.assertTrue(failed);self.assertEqual(seen,[n for n,_ in actions]);self.assertEqual(state['phase'],'failed')
 def test_each_cleanup_position_fails_without_skipping_other_actions(self):
  names=('ignore-term','ignore-int','stop','readback','storage','publish','final','sync','restore-term','restore-int')
  for fail_at in names:
   with self.subTest(fail_at=fail_at):
    ns,io=namespace();seen=[];first=MemoryError(fail_at);state={'phase':'running','limit_reason':None}
    def callback(name):
     def run():
      seen.append(name)
      if name==fail_at:raise first
     return run
    selected,failed=ns['_native_finalize'](state,None,[(n,callback(n)) for n in names],io)
    self.assertIs(selected,first);self.assertTrue(failed);self.assertEqual(seen,list(names));self.assertEqual(state['phase'],'failed')
 def test_body_ordinary_retained_without_cleanup_failure(self):
  ns,io=namespace();first=ValueError('body');state={'phase':'failed','limit_reason':'body'}
  primary,failed=ns['_native_finalize'](state,first,[('storage',lambda:None)],io)
  self.assertIs(primary,first);self.assertFalse(failed);self.assertEqual(state['phase'],'failed')
 def test_success_actions_observe_no_invented_failure(self):
  ns,io=namespace();state={'phase':'running','limit_reason':None};seen=[]
  primary,failed=ns['_native_finalize'](state,None,[('final',lambda:seen.append(state['phase']))],io)
  self.assertIsNone(primary);self.assertFalse(failed);self.assertEqual(seen,['complete'])
if __name__=='__main__':unittest.main(verbosity=2)

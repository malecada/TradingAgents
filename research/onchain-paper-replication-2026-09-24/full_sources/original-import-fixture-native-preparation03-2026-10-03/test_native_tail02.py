"""Actual monitor handler/finally AST; startup replaced, OS calls injected.
No native unit, process, cgroup or claim is created. Receipt writes are real tiny
files in TemporaryDirectory. This does not prove native stop behavior.
"""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import types
import unittest
HERE=Path(__file__).resolve().parent
SOURCE=Path(sys.argv.pop(1)) if len(sys.argv)>1 and not sys.argv[1].startswith('-') else HERE/'resources.py'
IO=HERE.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py'
def actual_tail(body_error,stop_error):
 tree=ast.parse(SOURCE.read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='guarded_run')
 index=next(i for i,n in enumerate(run.body) if isinstance(n,ast.Try) and n.finalbody and any(isinstance(h,ast.ExceptHandler) and h.name=='exc' for h in n.handlers))
 tail=copy.deepcopy(run.body[index:]);tail[0].body=[ast.Raise(exc=ast.Name(id='body_error',ctx=ast.Load()),cause=None)]
 wrapper=ast.FunctionDef(name='invoke',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=tail,decorator_list=[])
 # These original local variables must stay local, as in guarded_run.
 names=('selected_primary','selected_body_error','selected_finalization_failed')
 wrapper.body=[ast.Assign(targets=[ast.Name(id=n,ctx=ast.Store())],value=ast.Constant(value=False if n.endswith('failed') else None)) for n in names]+wrapper.body
 helpers=[copy.deepcopy(n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_native_select','_native_reason','_native_finalize','_native_write','_native_sync'}]
 spec=importlib.util.spec_from_file_location('actual_owned_io_tail',IO);io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
 temporary=tempfile.TemporaryDirectory();root=Path(temporary.name);trace=[];state={'phase':'running','limit_reason':None}
 def stop(*args,**kwargs):
  trace.append('stop')
  if stop_error is not None:raise stop_error
  return types.SimpleNamespace(returncode=0)
 def properties(unit):trace.append('readback');return {'ActiveState':'inactive','Result':'success'}
 def signals(sig,previous):trace.append(('signal',int(sig),previous));return previous
 def storage():trace.append('storage')
 def publish():trace.append(('publish',state['phase']))
 ns=dict(json=json,os=os,sys=sys,Path=Path,native_io=io,physical_policy=None,native_unit_limits={'file_size_bytes':4194304},
  body_error=body_error,state=state,launched=True,cgroup=None,unit='synthetic-not-launched',receipt=root,
  signal=types.SimpleNamespace(signal=signals,SIGTERM=signal.SIGTERM,SIGINT=signal.SIGINT,SIG_IGN=signal.SIG_IGN),
  prior_signals={signal.SIGTERM:'oldterm',signal.SIGINT:'oldint'},_systemctl=stop,_properties=properties,
  observe_storage=storage,publish=publish,disk_paths=(),disk_floor_bytes=0,shutil=types.SimpleNamespace())
 module=ast.fix_missing_locations(ast.Module(body=helpers+[wrapper],type_ignores=[]));exec(compile(module,str(SOURCE),'exec'),ns)
 caught=None
 try:ns['invoke']()
 except BaseException as error:caught=error
 files={p.name:json.loads(p.read_text()) for p in root.iterdir() if p.name.endswith('.json')}
 temporary.cleanup();return caught,state,trace,files
class Tail(unittest.TestCase):
 def test_original_body_fatal_survives_stop_fatal_with_later_actions(self):
  first=MemoryError('body');later=KeyboardInterrupt('stop');caught,state,trace,files=actual_tail(first,later)
  self.assertIs(caught,first);self.assertIn('readback',trace);self.assertIn('storage',trace)
  self.assertEqual(state['phase'],'failed');self.assertFalse(state['cleanup_verified'])
  self.assertEqual(files['final.json']['phase'],'failed');self.assertEqual(files['native-finalization-failed.json']['phase'],'failed')
  self.assertIn(('signal',int(signal.SIGTERM),'oldterm'),trace);self.assertIn(('signal',int(signal.SIGINT),'oldint'),trace)
 def test_first_cleanup_fatal_promotes_over_ordinary_body(self):
  first=ValueError('body');later=MemoryError('stop');caught,state,trace,files=actual_tail(first,later)
  self.assertIs(caught,later);self.assertIn('readback',trace);self.assertIn('storage',trace);self.assertEqual(state['phase'],'failed')
if __name__=='__main__':unittest.main(verbosity=2)

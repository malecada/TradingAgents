"""Actual PairLog terminal methods plus actual producer handler; fake IO/lease only."""
import ast,hashlib,os,sys,unittest,json
from pathlib import Path
from types import SimpleNamespace
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from test_cleanup03 import handler
class ActualTerminal(unittest.TestCase):
 def test_selected_producer_reaches_actual_matching_terminal_before_revoke(self):
  path=D.parent/'original-import-fixture-io-candidate02-2026-10-02/compact_pair_log.py';tree=ast.parse(path.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PairLog');methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('_terminal','fail','_check')]
  owner=SimpleNamespace(poisoned=False,identity='a'*64);calls=[];writes={}
  def require(v,m):
   if not v:raise ValueError(m)
  def lease():require(not owner.poisoned,'actual owner lease rejected')
  def cleanup(actions,primary):
   failures=[]
   for a in actions:
    try:a()
    except BaseException as e:failures.append(e)
   if failures:raise failures[0]
  def write(fd,name,raw):writes[name]=raw;return hashlib.sha256(raw).hexdigest()
  io=SimpleNamespace(_root=lambda *a:None,_json=lambda v:json.dumps(v).encode(),_write=write,_cleanup=cleanup,_close_after_failure=lambda action,primary:action())
  env={'io':io,'hashlib':hashlib,'require':require,'verify':lambda *a,**k:None}
  logclass=ast.ClassDef(name='SelectedLog',bases=[],keywords=[],body=methods,decorator_list=[]);exec(compile(ast.fix_missing_locations(ast.Module(body=[logclass],type_ignores=[])),str(path),'exec'),env)
  log=env['SelectedLog']();log.closed=log.poisoned=False;log.lease=lease;log.root=Path('/fake/metadata');log.fd=1;log.start_sha=log.head='b'*64;log.chunks=0;log.start={'owner':owner.identity,'scope':{}};log.state={'pending':None}
  def close():
   if not log.closed:log.closed=True;calls.append('descriptor-close')
  log.close=close;sentinel=ValueError('expected purpose refusal');env.update(owner=owner,log=log,stream=None,claimed=True,fd=1,sentinel=sentinel)
  exec(handler(),env)
  with self.assertRaises(ValueError) as got:env['selected']()
  self.assertIs(got.exception,sentinel);self.assertEqual(calls,['descriptor-close']);self.assertTrue(owner.poisoned)
  self.assertEqual(json.loads(writes['terminal.json'])['status'],'failed');self.assertIn('failed.json',writes)
 def test_only_selected_cleanup_handler_changes_in_entire_module(self):
  old=ast.parse((D.parent/'original-import-native-refusal-candidate02-2026-10-03/compact_mcm.py').read_text());new=ast.parse((D/'compact_mcm.py').read_text())
  def selected(tree):
   f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
   return next(n for n in ast.walk(f) if isinstance(n,ast.ExceptHandler) and n.name=='primary' and any(isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='actions' for t in x.targets) for x in n.body))
  selected(new).body=selected(old).body;self.assertEqual(ast.dump(old,include_attributes=False),ast.dump(new,include_attributes=False))
if __name__=='__main__':unittest.main()

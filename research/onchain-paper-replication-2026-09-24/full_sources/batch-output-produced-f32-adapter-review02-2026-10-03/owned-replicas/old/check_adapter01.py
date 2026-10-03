"""Extracted metadata/lifecycle tests. Stand-ins are not genuine authority."""
import ast,json,types,unittest,builtins
from pathlib import Path
P=Path(__file__).parent
def functions(path,names,ns):
 t=ast.parse(path.read_text());exec(compile(ast.Module([n for n in t.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names],[]),str(path),'exec'),ns);return ns
class Checks(unittest.TestCase):
 def test_transport_policy_separation(self):
  durable=functions(P/'archive_non_tail.py',{'require','encode'},{'json':json,'META':8192})
  ns=functions(P/'selected_non_tail_transport.py',{'require','encoded','policy'},dict(Path=Path,json=json,re=__import__('re'),META=8192,durable=types.SimpleNamespace(**durable)))
  context=dict(schema_version=3,slots=[dict(graph='a'*64,role='mcm-output')],part_bytes=8192,deadline_seconds=600,max_control_bytes=2**24,max_commands=32)
  p=dict(schema_version=2,kind='selected-produced-f32-ssh-plaintext-channel-v1',connection=dict(host='example.invalid',user='fixture',port=23,identity_file='/unopened/synthetic-key',known_hosts_file='/unopened/synthetic-hosts'),remote_namespace='test',part_bytes=8192,command_seconds=1,cleanup_seconds=1,stderr_bytes=1024,max_commands=32,max_parts=32,max_rounded_bytes=2**24,max_channel_bytes=2**24,max_local_bytes=2**24,max_files=128,outputs={'a'*64:'raw.json'})
  self.assertEqual(ns['policy'](p,context),p)
  with self.assertRaises(ValueError):ns['policy'](p,context|{'schema_version':2})
  with self.assertRaises(ValueError):ns['policy'](p|{'schema_version':1,'kind':'selected-non-tail-ssh-plaintext-channel-v1'},context)
  with self.assertRaises(ValueError):ns['policy'](p,context|{'slots':[dict(graph='a'*64,role='graph-artifact')]})
 def adapter_ns(self):
  class CleanupFailure(BaseException):pass
  d=functions(P/'archive_non_tail.py',{'fatal','select'},dict(CleanupFailure=CleanupFailure))
  d['require']=lambda v,m:None if v else (_ for _ in ()).throw(ValueError(m))
  return functions(P/'completed_f32.py',{'CompletedF32'},dict(durable=types.SimpleNamespace(**d),require=d['require'],compact_mcm=types.SimpleNamespace(Produced=type('OnlyGenuineProducedPlaceholder',(),{})))),CleanupFailure
 def test_dictionary_and_fake_capability_refused(self):
  ns,_=self.adapter_ns()
  for wrong in ({'hash':'0'*64},object(),types.SimpleNamespace(record={})):
   with self.assertRaisesRegex(ValueError,'genuine completed'):ns['CompletedF32'](wrong,None)
 def test_close_firstfatal_and_close_once(self):
  ns,CleanupFailure=self.adapter_ns();cls=ns['CompletedF32']
  for primary,later in [(MemoryError('first'),OSError('close')),(ValueError('body'),MemoryError('cleanup')),(None,CleanupFailure('uncertain'))]:
   owner=types.SimpleNamespace(poisoned=False);calls=[]
   class CM:
    def __exit__(self,*args):calls.append('close');raise later
   obj=object.__new__(cls)
   for k,v in dict(_reader=None,_closed=False,_failed=False,_cm=CM(),_objects=(None,None,None,None,owner,None,None),_frozen=True).items():object.__setattr__(obj,k,v)
   # Preserve actual close reducer; no fake authority check is called successful.
   # Real _authority refuses the synthetic incomplete ancestry after close.
   expected=primary if isinstance(primary,MemoryError) else later
   with self.assertRaises(type(expected)) as caught:obj._close(primary)
   self.assertIs(caught.exception,expected);self.assertEqual(calls,['close']);self.assertTrue(owner.poisoned);self.assertTrue(obj._closed)
   obj._close();self.assertEqual(calls,['close'])
 def test_source_type_and_closed_stage_contract(self):
  t=ast.parse((P/'completed_f32.py').read_text());cls=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='CompletedF32');body=ast.unparse(cls)
  for clause in ['type(produced) is compact_mcm.Produced','type(target) is imported_mcm_identity.Target','stage.closed','owner.active is None','held.check(owner)','produced._check()']:
   self.assertIn(clause,body)
  self.assertNotIn('produced.check()',body);self.assertNotIn('np.',body)
 def test_numerical_original_inverse(self):
  original=(P/'compact_mcm.py.baseline.txt').read_text();new=(P/'compact_mcm.py').read_text();start=new.index('        result._check()\n        if _imported(dictionary):',new.index('def _produce_locked'))
  end=new.index('        return result',start)+len('        return result')
  inverse=new[:start]+'        result._check(); return result'+new[end:]
  self.assertEqual(inverse,original);self.assertEqual(ast.dump(ast.parse(inverse)),ast.dump(ast.parse(original)))
 def test_complete_recovery_kind_selected(self):
  text=(P/'archive_non_tail.py').read_text();self.assertIn("kind=self.ledger.record['role']",text)
  self.assertIn("type(source) is CompletedF32",text);self.assertIn("role='mcm-output'",text)
  engine=(P/'selected_non_tail_transport.py').read_text();self.assertIn("operation.ledger.record['role']=='mcm-output'",engine);self.assertIn('selected-produced-f32-remote-roundtrip',engine)
if __name__=='__main__':unittest.main()

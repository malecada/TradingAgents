"""Actual extracted Authority private-state boundary; no scientific minting."""
import ast
import hashlib
import importlib.util
from pathlib import Path
import threading
import types
import unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def extracted():
 spec=importlib.util.spec_from_file_location('provenance_pure',ROOT/'tradingagents/research/onchain_replication/provenance.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
 tree=ast.parse((HERE/'compact_cold_features.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Authority']
 def require(value,message):
  if not value:raise ValueError(message)
 key=object();ns=dict(_KEY=key,require=require,hashlib=hashlib,threading=threading,freeze=p.freeze,thaw=p.thaw,canonical_bytes=p.canonical_bytes)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual Authority source','exec'),ns);return ns['Authority'],key,ns
class PrivateState(unittest.TestCase):
 def test_constructor_without_factory_token_refused(self):
  A,key,ns=extracted()
  with self.assertRaises(ValueError):A(object(),None,{},None,{},[],{})
 def test_concurrent_operation_refused_without_unlocking_other_owner(self):
  A,key,ns=extracted();a=A(key,None,{},None,{},[],{});a._lock.acquire()
  with self.assertRaisesRegex(ValueError,'concurrent'):a.check()
  self.assertTrue(a._lock.locked());a._lock.release()
 def test_poisoned_authority_stays_closed_and_unlocks(self):
  A,key,ns=extracted();a=A(key,None,{},None,{},[],{});a._state['failed']=True
  with self.assertRaisesRegex(ValueError,'poisoned'):a.check()
  self.assertFalse(a._lock.locked());self.assertTrue(a._state['failed'])
 def test_authority_record_cannot_be_replaced(self):
  A,key,ns=extracted();a=A(key,None,{},None,{},[],{})
  with self.assertRaises(AttributeError):a._record={}
 def test_corrupted_record_is_rejected_before_run_callbacks(self):
  A,key,ns=extracted();a=A(key,None,{},None,{},[],{});object.__setattr__(a,'_pin','0'*64)
  with self.assertRaisesRegex(ValueError,'record changed'):a.check()
  self.assertTrue(a._state['failed']);self.assertFalse(a._lock.locked())
if __name__=='__main__':unittest.main(verbosity=2)

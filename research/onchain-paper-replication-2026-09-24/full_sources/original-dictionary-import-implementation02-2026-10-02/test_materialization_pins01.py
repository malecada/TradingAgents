"""Exact new metadata reducer AST with invented nonnumerical record objects."""
import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
HERE=Path(__file__).resolve().parent

def load():
 t=ast.parse((HERE/'original_import_preparation.py').read_text());names={'require','_evidence_pin','_check_materialized_metadata'}
 nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names]
 if len(nodes)!=3:raise AssertionError('complete materialization provenance pin absent')
 ns={'hashlib':hashlib};exec(compile(ast.Module(body=nodes,type_ignores=[]),'pins','exec'),ns);return ns

class Pins(unittest.TestCase):
 def test_every_emitted_provenance_field_and_identity_pinned(self):
  ns=load();e=SimpleNamespace(dictionary_identity='d',sample_identity='s',representative_indices=(2,1),original_terminal='failed',original_claim='old',_dictionary_bytes=b'body',bundle_sha256='bundle')
  value=SimpleNamespace(_evidence=e,_evidence_object=e,_evidence_value=ns['_evidence_pin'](e),_dictionary=SimpleNamespace(identity='d'),numeric_bytes=96,_numeric_bytes=96)
  ns['_check_materialized_metadata'](value)
  for key,replacement in [('representative_indices',(1,2)),('bundle_sha256','bad'),('sample_identity','bad'),('original_claim','bad'),('original_terminal','complete'),('_dictionary_bytes',b'bad')]:
   old=getattr(e,key);setattr(e,key,replacement)
   with self.subTest(key=key),self.assertRaises(ValueError):ns['_check_materialized_metadata'](value)
   setattr(e,key,old)
  value._evidence=SimpleNamespace(**vars(e))
  with self.assertRaises(ValueError):ns['_check_materialized_metadata'](value)
  value._evidence=e;value.numeric_bytes=0
  with self.assertRaises(ValueError):ns['_check_materialized_metadata'](value)
  value.numeric_bytes=96;value._dictionary.identity='changed'
  with self.assertRaises(ValueError):ns['_check_materialized_metadata'](value)

if __name__=='__main__':unittest.main()

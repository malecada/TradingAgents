"""Stdlib-only exact AST tests, no real Binding or numerical import."""
import ast
import errno
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def selection():
 tree=ast.parse((HERE/'resource_binding.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','assert_selected')]
 if len(nodes)!=2:raise AssertionError('exact job binding join absent')
 ns={};exec(compile(ast.Module(body=nodes,type_ignores=[]),'selection','exec'),ns);return ns['assert_selected']

def metadata():
 file=HERE/'import_metadata.py'
 if not file.exists():raise AssertionError('owned descriptor metadata boundary absent')
 tree=ast.parse(file.read_text());nodes=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
 original=ast.parse((HERE/'original_dictionary.py').read_text());close=next(n for n in original.body if isinstance(n,ast.FunctionDef) and n.name=='_close_owned')
 class CleanupFailure(BaseException):pass
 io=SimpleNamespace(CleanupFailure=CleanupFailure)
 ns={'os':os,'stat':__import__('stat'),'hashlib':__import__('hashlib'),'Path':Path,'io':io,'LIMIT':65536}
 exec(compile(ast.Module(body=[close],type_ignores=[]),'close','exec'),ns)
 ns['original']=SimpleNamespace(_close_owned=ns['_close_owned'])
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(file),'exec'),ns)
 return ns

class Corrections(unittest.TestCase):
 def test_actual_job_reference_required(self):
  f=selection();ad=SimpleNamespace(inputs={'a':{'sha256':'1'},'b':{'sha256':'2'}})
  bound=SimpleNamespace(record={'resource_only':True,'job_input':'a','job_sha256':'1'},_run=SimpleNamespace(admission=ad))
  f(bound,'a')
  with self.assertRaises(ValueError):f(bound,'b')
  for key,value in [('resource_only',1),('job_sha256','bad')]:
   old=bound.record[key];bound.record[key]=value
   with self.assertRaises(ValueError):f(bound,'a')
   bound.record[key]=old
 def test_fatal_write_then_close_preserves_identity_and_closes_all(self):
  ns=metadata();fatal=MemoryError('write fatal');closed=[];realclose=os.close
  def close(fd):
   closed.append(fd);realclose(fd)
   if len(closed)==1:raise OSError('uncertain close')
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'write',side_effect=fatal),patch.object(os,'close',side_effect=close):
   with self.assertRaises(MemoryError) as caught:ns['write'](Path(tmp),'x',b'data')
   self.assertIs(caught.exception,fatal);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_fatal_read_then_close_preserves_identity_and_closes_all(self):
  ns=metadata();fatal=SystemExit('read fatal');closed=[];realclose=os.close
  def close(fd):
   closed.append(fd);realclose(fd)
   if len(closed)==1:raise OSError('uncertain close')
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'x').write_bytes(b'body')
   with patch.object(os,'read',side_effect=fatal),patch.object(os,'close',side_effect=close):
    with self.assertRaises(SystemExit) as caught:ns['read'](root,'x')
    self.assertIs(caught.exception,fatal);self.assertEqual(len(closed),2)
 def test_ordinary_body_then_first_fatal_close(self):
  ns=metadata();body=ValueError('ordinary write');fatal=MemoryError('first fatal close');closed=[];realclose=os.close
  def close(fd):
   closed.append(fd);realclose(fd)
   if len(closed)==1:raise fatal
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'write',side_effect=body),patch.object(os,'close',side_effect=close):
   with self.assertRaises(MemoryError) as caught:ns['write'](Path(tmp),'x',b'data')
   self.assertIs(caught.exception,fatal);self.assertIs(fatal.__cause__,body);self.assertEqual(len(closed),2)
 def test_ordinary_child_close_then_parent_fatal(self):
  ns=metadata();fatal=SystemExit('parent fatal');ordinary=OSError('child uncertain');closed=[];realclose=os.close
  def close(fd):
   closed.append(fd);realclose(fd)
   raise ordinary if len(closed)==1 else fatal
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'close',side_effect=close):
   with self.assertRaises(SystemExit) as caught:ns['write'](Path(tmp),'x',b'data')
   self.assertIs(caught.exception,fatal);self.assertIs(fatal.__cause__,ordinary);self.assertEqual(len(closed),2)
 def test_failed_child_open_closes_parent_once(self):
  ns=metadata();fatal=MemoryError('child open');opened=[];closed=[];realopen=os.open;realclose=os.close
  def opening(*a,**k):
   if opened:raise fatal
   fd=realopen(*a,**k);opened.append(fd);return fd
  def close(fd):closed.append(fd);realclose(fd)
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'open',side_effect=opening),patch.object(os,'close',side_effect=close):
   with self.assertRaises(MemoryError) as caught:ns['write'](Path(tmp),'x',b'data')
   self.assertIs(caught.exception,fatal);self.assertEqual(closed,opened)
 def test_durable_roundtrip_exclusive_and_no_fdopen(self):
  ns=metadata()
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'fdopen',side_effect=AssertionError('stream forbidden')):
   root=Path(tmp);ns['write'](root,'x',b'body');self.assertEqual(ns['read'](root,'x'),b'body')
   with self.assertRaises(FileExistsError):ns['write'](root,'x',b'replace')

class JournalCorrections(unittest.TestCase):
 def journal(self):
  file=HERE/'feature_journal.py'
  if not file.exists():raise AssertionError('genuine checked journal seam absent')
  tree=ast.parse(file.read_text());nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.Assign)) and (not isinstance(n,ast.FunctionDef) or n.name=='required_set')]
  import json
  ns={'Path':Path,'json':json,'canonical_bytes':lambda x:json.dumps(x,sort_keys=True).encode(),'require_hash':lambda x:None,'checked_io':SimpleNamespace(**metadata())}
  ns['durable_mkdir']=lambda p:(_ for _ in ()).throw(AssertionError('legacy birth'))
  ns['_immutable']=lambda *a:(_ for _ in ()).throw(AssertionError('legacy writer'))
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(file),'exec'),ns)
  return ns
 def test_genuine_checked_birth_and_failure_seal(self):
  ns=self.journal();owner={'experiment':'x','source_commit':'a'*40,'producer':'p','workflow_identity':'b'*64}
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp)/'namespace'/'journal'
   journal=ns['FeatureJournal'](directory,owner,required_graphs=['c'*64],_metadata_role=ns['_RESOURCE_METADATA'])
   self.assertTrue((directory/'owner.json').exists());journal.seal('failed',reason='synthetic')
   self.assertTrue((directory/'failed.json').exists())
   with self.assertRaises(ValueError):journal.seal('failed')
 def test_checked_constructor_primary_retained(self):
  ns=self.journal();fatal=MemoryError('owner publication');owner={'experiment':'x','source_commit':'a'*40,'producer':'p','workflow_identity':'b'*64}
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'write',side_effect=fatal):
   directory=Path(tmp)/'namespace'/'journal'
   with self.assertRaises(MemoryError) as caught:ns['FeatureJournal'](directory,owner,required_graphs=['c'*64],_metadata_role=ns['_RESOURCE_METADATA'])
   self.assertIs(caught.exception,fatal);self.assertTrue(directory.exists())
 def test_untrusted_role_refused_before_birth(self):
  ns=self.journal()
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp)/'namespace'/'journal'
   with self.assertRaises(ValueError):ns['FeatureJournal'](directory,{},required_graphs=['c'*64],_metadata_role=object())
   self.assertFalse(directory.exists())

if __name__=='__main__':unittest.main()

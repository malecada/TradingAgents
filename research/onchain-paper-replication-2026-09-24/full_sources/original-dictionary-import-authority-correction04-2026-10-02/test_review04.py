import ast,os,sys,tempfile,unittest,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import contextmanager
from threading import get_ident
import test_corrections01 as prior
HERE=Path(__file__).resolve().parent

def owners():
 ns={'os':os,'sys':sys,'contextmanager':contextmanager,'get_ident':get_ident,'require':lambda b,m:None if b else (_ for _ in ()).throw(ValueError(m))}
 class Owner:pass
 class CleanupFailure(BaseException):pass
 io=SimpleNamespace(CleanupFailure=CleanupFailure)
 def opening(root):return root,os.open(root,os.O_RDONLY|os.O_DIRECTORY)
 io._open=opening;io._root=lambda *a:None
 t=ast.parse((HERE.parents[3]/'tradingagents/research/onchain_replication/score_batches.py').read_text())
 deps=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_release','_cleanup','_close_after_failure')]
 tmp={'sys':sys,'CleanupFailure':CleanupFailure};exec(compile(ast.Module(body=deps,type_ignores=[]),'actual_score_cleanup','exec'),tmp);io._release=tmp['_release']
 ns.update(io=io,Owner=Owner,import_io=SimpleNamespace(**prior.metadata()))
 t=ast.parse((HERE/'compact_owner.py').read_text());nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_HeldTransition','_held','_held_import','entries')]
 # Only local import of exact candidate helper is replaced, not its operations.
 class Imports(ast.NodeTransformer):
  def visit_ImportFrom(self,node):return ast.Pass() if node.module in ('import_metadata',None) else node
  def visit_Import(self,node):return node
 nodes=[Imports().visit(n) for n in nodes];tree=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]));exec(compile(tree,'exact_owner_boundaries','exec'),ns)
 return ns

class ReviewChecks(unittest.TestCase):
 def test_inventory_body_fatal_iterator_and_fd_close_once(self):
  ns=owners();fatal=MemoryError('traversal');calls=[];realclose=os.close
  class Iterator:
   def __iter__(self):return self
   def __next__(self):raise fatal
   def close(self):calls.append('iterator');raise OSError('iterator close')
   def __enter__(self):return self
   def __exit__(self,*a):self.close()
  def close(fd):calls.append('fd');realclose(fd);raise OSError('fd close')
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'scandir',return_value=Iterator()),patch.object(os,'close',side_effect=close):
   with self.assertRaises(MemoryError) as got:ns['entries'](Path(tmp),{'x'},required=set(),_imported=True)
   self.assertIs(got.exception,fatal);self.assertEqual(calls,['iterator','fd'])
 def test_inventory_ordinary_iterator_then_first_fd_fatal(self):
  ns=owners();fatal=SystemExit('fd fatal');calls=[];realclose=os.close
  class Iterator:
   def __iter__(self):return iter(())
   def close(self):calls.append('iterator');raise OSError('iterator close')
  def close(fd):calls.append('fd');realclose(fd);raise fatal
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'scandir',return_value=Iterator()),patch.object(os,'close',side_effect=close):
   with self.assertRaises(SystemExit) as got:ns['entries'](Path(tmp),set(),required=set(),_imported=True)
   self.assertIs(got.exception,fatal);self.assertIsInstance(fatal.__cause__,OSError);self.assertEqual(calls,['iterator','fd'])
 def test_inventory_success_and_refusal(self):
  ns=owners()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'ok').write_bytes(b'')
   ns['entries'](root,{'ok'},required={'ok'},_imported=True)
   with self.assertRaises(ValueError):ns['entries'](root,set(),required=set(),_imported=True)
 def test_journal_pin_cannot_be_deleted(self):
  ns=prior.JournalCorrections().journal();owner={'experiment':'x','source_commit':'a'*40,'producer':'p','workflow_identity':'b'*64}
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'n'/'j';journal=ns['FeatureJournal'](root,owner,required_graphs=['c'*64],_metadata_role=ns['_RESOURCE_METADATA'])
   for name in ('_resource_pin','_metadata_role','directory'):
    with self.assertRaises(AttributeError):delattr(journal,name)
   journal.seal('failed');self.assertTrue((root/'failed.json').exists())
 def test_held_body_and_release_mixed_errors(self):
  for primary,later in [(MemoryError('body'),OSError('release')),(ValueError('body'),SystemExit('release'))]:
   ns=owners();calls=[]
   class Lock:
    def acquire(self,**kw):return True
    def locked(self):return True
    def release(self):calls.append('release');raise later
   owner=ns['Owner']();owner._transition=Lock();owner.required=('dictionary-import',);owner.poisoned=False
   selected=primary if isinstance(primary,MemoryError) else later
   with self.assertRaises(type(selected)) as got:
    with ns['_held'](owner):raise primary
   self.assertIs(got.exception,selected);self.assertEqual(calls,['release']);self.assertTrue(owner.poisoned);self.assertFalse(hasattr(owner,'_held_transition'))
 def test_journal_replaced_root_refused(self):
  ns=prior.JournalCorrections().journal();owner={'experiment':'x','source_commit':'a'*40,'producer':'p','workflow_identity':'b'*64}
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'n'/'j';journal=ns['FeatureJournal'](root,owner,required_graphs=['c'*64],_metadata_role=ns['_RESOURCE_METADATA'])
   root.rename(root.with_name('retained'));root.mkdir()
   with self.assertRaises(ValueError):journal.seal('failed')
   self.assertFalse((root/'failed.json').exists())
 def test_journal_role_path_and_configuration_refused(self):
  for name,value in [('_metadata_role',None),('directory',Path('/tmp/other')),('owner',{}),('required',[]),('parent',{}),('identity','changed')]:
   ns=prior.JournalCorrections().journal();owner={'experiment':'x','source_commit':'a'*40,'producer':'p','workflow_identity':'b'*64}
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'n'/'j';journal=ns['FeatureJournal'](root,owner,required_graphs=['c'*64],_metadata_role=ns['_RESOURCE_METADATA'])
    try:setattr(journal,name,value)
    except (AttributeError,ValueError):pass
    else:
     with self.assertRaises(ValueError):journal.seal('failed')
    self.assertFalse((root/'failed.json').exists())
 def test_journal_nested_owner_and_start_bytes_refused(self):
  for mutation in ('nested','start'):
   ns=prior.JournalCorrections().journal();owner={'experiment':'x','source_commit':'a'*40,'producer':'p','workflow_identity':'b'*64}
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)/'n'/'j';journal=ns['FeatureJournal'](root,owner,required_graphs=['c'*64],_metadata_role=ns['_RESOURCE_METADATA'])
    if mutation=='nested':journal.owner['producer']='changed'
    else:(root/'start.json').write_bytes(b'{}')
    with self.assertRaises(ValueError):journal.seal('failed')
    self.assertFalse((root/'failed.json').exists())

if __name__=='__main__':unittest.main()

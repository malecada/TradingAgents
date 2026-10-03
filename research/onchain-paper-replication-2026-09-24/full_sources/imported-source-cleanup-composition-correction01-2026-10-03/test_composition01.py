"""Exact source-composition regression; no imports, arrays or authority."""
import ast,hashlib,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;FULL=HERE.parent
SOURCE=HERE/'compact_mcm.py'
if len(sys.argv)>1 and sys.argv[1]=='--source':SOURCE=Path(sys.argv.pop(2));sys.argv.pop(1)
def parse(path):
 tree=ast.parse(path.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked');block=next(n for n in fn.body if isinstance(n,ast.Try));return tree,fn,block
class Composition(unittest.TestCase):
 def test_only_exact_accepted_cleanup_exception_is_composed(self):
  baseline,bfn,bblock=parse(FULL/'imported-source-metadata-correction02-2026-10-03/compact_mcm.py')
  cleanup,cfn,cblock=parse(FULL/'original-import-native-refusal-candidate03-2026-10-03/compact_mcm.py')
  candidate,fn,block=parse(SOURCE)
  self.assertEqual(ast.dump(block.handlers[0]),ast.dump(cblock.handlers[0]))
  block.handlers[0]=bblock.handlers[0]
  self.assertEqual(ast.dump(candidate),ast.dump(baseline))
 def test_actual_producer_has_no_unregistered_refusal_seam(self):
  tree,fn,block=parse(SOURCE)
  self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.level==1 and n.module is None and any(a.name=='resource_refusal' for a in n.names) for n in ast.walk(fn)))
  self.assertFalse(any(isinstance(n,ast.Name) and n.id=='resource_refusal' for n in ast.walk(fn)))
if __name__=='__main__':unittest.main(verbosity=2)

import ast,os,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import test_review04 as checks
class OldInventory(unittest.TestCase):
 def test_first_fatal_must_survive_old_iterator_cleanup(self):
  ns=checks.owners()
  old=checks.HERE.parent/'original-dictionary-import-authority-correction03-2026-10-02/compact_owner.py'
  node=next(n for n in ast.parse(old.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='entries')
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(old),'exec'),ns)
  fatal=MemoryError('traversal primary');closed=[];realclose=os.close
  class Iterator:
   def __iter__(self):return self
   def __next__(self):raise fatal
   def __enter__(self):return self
   def __exit__(self,*args):closed.append('iterator');raise OSError('iterator cleanup')
  def close(fd):closed.append('fd');realclose(fd)
  with tempfile.TemporaryDirectory() as tmp,patch.object(os,'scandir',return_value=Iterator()),patch.object(os,'close',side_effect=close):
   with self.assertRaises(MemoryError) as got:ns['entries'](Path(tmp),{'x'},required=set())
   self.assertIs(got.exception,fatal);self.assertEqual(closed,['iterator','fd'])
if __name__=='__main__':unittest.main()

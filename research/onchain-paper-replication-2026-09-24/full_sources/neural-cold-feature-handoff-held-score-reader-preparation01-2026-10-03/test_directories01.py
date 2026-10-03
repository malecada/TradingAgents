import ast,os,stat,tempfile,types,unittest
from pathlib import Path
from test_completion01 import HERE,require
class DirectoryTests(unittest.TestCase):
 def test_real_live_directories_then_same_name_replacement_refuses(self):
  tree=ast.parse((HERE/'mcm_score_stream.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_directory_identity','_directory_rejoin')]
  ns={'os':os,'stat':stat,'Path':Path,'require':require};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-directory-joins>','exec'),ns)
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'stream';root.mkdir();b=root/'batches';b.mkdir();fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY);bf=os.open(b,os.O_RDONLY|os.O_DIRECTORY)
   try:
    stream=types.SimpleNamespace(root=root,fd=fd,batches=types.SimpleNamespace(root=b,fd=bf));pins=ns['_directory_identity'](stream);ns['_directory_rejoin'](stream,pins)
    b.rename(root/'old-batches');b.mkdir()
    with self.assertRaises(ValueError):ns['_directory_rejoin'](stream,pins)
   finally:os.close(bf);os.close(fd)
 def test_bool_completion_count_rejected(self):
  from test_completion01 import load
  s,ns=load();s.finish();s.n=True
  with self.assertRaises(ValueError):ns['completed_evidence'](s)
if __name__=='__main__':unittest.main()

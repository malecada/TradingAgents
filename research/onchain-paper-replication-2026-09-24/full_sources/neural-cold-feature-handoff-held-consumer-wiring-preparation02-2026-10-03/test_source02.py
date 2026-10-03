"""Actual extracted _body; tiny stdlib files and injected read/close faults."""
import ast,os,runpy,stat,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
IO=P.parent/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/owned_io.py'
import types
io=types.SimpleNamespace(**runpy.run_path(str(IO)))
def load(name):
 t=ast.parse((P/name).read_bytes());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('require','_body')]
 for n in nodes:n.body=[x for x in n.body if not isinstance(x,ast.ImportFrom)]
 ns={'os':os,'stat':stat,'source_io':io};exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'actual-source-body','exec'),ns);return ns['_body']
class Source(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=P);self.root=Path(self.tmp.name);self.file=self.root/'source.py';self.file.write_bytes(b'hello');self.read=load('held_score_consumer.py')
 def tearDown(self):self.tmp.cleanup()
 def test_real_read_and_fd_cleanup(self):
  before=set(os.listdir('/proc/self/fd'));self.assertEqual(self.read(self.file),b'hello');self.assertEqual(before,set(os.listdir('/proc/self/fd')))
 def test_fatal_read_then_close_error(self):
  fatal=MemoryError('read');closes=[];real=os.close
  def close(fd):closes.append(fd);real(fd);raise OSError('close')
  with patch.object(os,'read',side_effect=fatal),patch.object(os,'close',side_effect=close):
   with self.assertRaises(MemoryError) as e:self.read(self.file)
  self.assertIs(e.exception,fatal);self.assertEqual(len(closes),2);self.assertEqual(len(set(closes)),2)
 def test_ordinary_read_then_fatal_close(self):
  fatal=SystemExit('close');real=os.close;closed=[]
  def close(fd):real(fd);closed.append(fd);raise fatal
  with patch.object(os,'read',side_effect=OSError('read')),patch.object(os,'close',side_effect=close):
   with self.assertRaises(SystemExit) as e:self.read(self.file)
  self.assertIs(e.exception,fatal);self.assertEqual(len(closed),2)
 def test_uncertain_close_refuses(self):
  real=os.close
  def close(fd):real(fd);raise OSError('uncertain')
  with patch.object(os,'close',side_effect=close):
   with self.assertRaises(io.CleanupFailure):self.read(self.file)
 def test_growth_bounded(self):
  real=os.read;sizes=[]
  def read(fd,n):
   sizes.append(n)
   if len(sizes)==1:
    with self.file.open('ab') as f:f.write(b'xxxxxxxx')
   return real(fd,n)
  with patch.object(os,'read',side_effect=read):
   with self.assertRaisesRegex(ValueError,'grew'):self.read(self.file)
  self.assertEqual(sizes,[6])
 def test_short_replacement_link_oversize(self):
  real=os.read
  def read(fd,n):
   b=real(fd,n)
   if b:self.file.unlink();self.file.write_bytes(b'hello')
   return b
  with patch.object(os,'read',side_effect=read):
   with self.assertRaises(ValueError):self.read(self.file)
  self.file.unlink();self.file.symlink_to('missing')
  with self.assertRaises(ValueError):self.read(self.file)
  self.file.unlink();self.file.write_bytes(b'x'*(1048577))
  with self.assertRaises(ValueError):self.read(self.file)
 def test_inverse_whole_ast_bytes(self):
  b=(P/'held_score_consumer.baseline01.py').read_text();c=(P/'held_score_consumer.py').read_text();a=b[b.index('def _body('):b.index('\ndef _sources(')];z=c[c.index('def _body('):c.index('\ndef _sources(')];self.assertEqual(c.replace(z,a),b)
if __name__=='__main__':unittest.main(verbosity=2)

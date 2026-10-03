"""Independent real-file failure edges, exact candidate; synthetic source only."""
import ast,hashlib,importlib.util,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).parent;P=H.parent/'batch-output-transport-context-preparation03-2026-10-03'
spec=importlib.util.spec_from_file_location('review_local03_edges',P/'non_tail_context.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_inverse_wholebytes_AST_and_dependencies(self):
  old=(P.parent/'batch-output-transport-context-preparation02-2026-10-03/non_tail_context.py').read_text();new=(P/'non_tail_context.py').read_text();fn=lambda text:next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='bootstrap_read');a=fn(old);b=fn(new);lines=new.splitlines(keepends=True);lines[b.lineno-1:b.end_lineno]=old.splitlines(keepends=True)[a.lineno-1:a.end_lineno];self.assertEqual(''.join(lines),old);self.assertEqual(ast.dump(ast.parse(''.join(lines))),ast.dump(ast.parse(old)))
  for name,pin in m.PINS.items():self.assertEqual(hashlib.sha256((m.D/(name+'.py')).read_bytes()).hexdigest(),pin)
 def test_parent_subdirectory_file_replacements(self):
  for mode in ('parent','ancestor','file'):
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(dir=H) as d:
    root=Path(d).resolve();ancestor=root/'ancestor';parent=ancestor/'parent';parent.mkdir(parents=True);source=parent/'source.py';source.write_bytes(b'abc');real=os.read;done=[];closed=[];rc=os.close
    def read(fd,count):
     if not done:
      if mode=='file':source.rename(parent/'old');source.write_bytes(b'abc')
      elif mode=='parent':parent.rename(ancestor/'old');parent.mkdir();source.write_bytes(b'abc')
      else:ancestor.rename(root/'old');parent.mkdir(parents=True);source.write_bytes(b'abc')
      done.append(True)
     return real(fd,count)
    def close(fd):closed.append(fd);return rc(fd)
    with patch.object(m.os,'read',side_effect=read),patch.object(m.os,'close',side_effect=close),self.assertRaises(ValueError):m.bootstrap_read(source)
    self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_close_fatal_selection_and_independent_attempts(self):
  for mode in ('ordinary_then_fatal','fatal_then_fatal','ordinary_both'):
   with self.subTest(mode=mode),tempfile.TemporaryDirectory(dir=H) as d:
    p=Path(d).resolve()/'source.py';p.write_bytes(b'abc');rc=os.close;closed=[];first=SystemExit('first actual fatal');second=MemoryError('second actual fatal')
    def close(fd):
     closed.append(fd);rc(fd)
     if mode=='ordinary_both' or mode=='ordinary_then_fatal' and len(closed)==1:raise OSError('ordinary')
     if len(closed)==1 or mode=='ordinary_then_fatal':raise first
     raise second
    with patch.object(m.os,'close',side_effect=close):
     try:m.bootstrap_read(p)
     except BaseException as e:
      if mode=='ordinary_both':self.assertIs(type(e),m.BootstrapCleanupFailure)
      else:self.assertIs(e,first)
     else:self.fail('close failure accepted')
    self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_before_read_link_oversize_and_child_missing(self):
  with tempfile.TemporaryDirectory(dir=H) as d:
   root=Path(d).resolve();p=root/'source.py';p.write_bytes(b'abc');q=root/'link';q.symlink_to(p)
   with self.assertRaises(ValueError):m.bootstrap_read(q)
   q.unlink();os.link(p,q)
   with self.assertRaises(ValueError):m.bootstrap_read(p)
   q.unlink();p.write_bytes(b'x'*(1048576+1))
   with patch.object(m.os,'read',side_effect=AssertionError('must refuse before read')),self.assertRaises(ValueError):m.bootstrap_read(p)
   rc=os.close;closed=[]
   def close(fd):closed.append(fd);return rc(fd)
   with patch.object(m.os,'close',side_effect=close),self.assertRaises(FileNotFoundError):m.bootstrap_read(root/'missing')
   self.assertEqual(len(closed),1)
if __name__=='__main__':unittest.main(verbosity=2)

"""Extracted actual source, stdlib fake process/frames only; no Git or job launch."""
import ast,hashlib,os,subprocess,types,unittest
from pathlib import Path
HERE=Path(__file__).parent;SOURCE=Path(os.environ.get('BATCH_SOURCE',HERE/'candidate01.py'))
def require(v,m):
 if not v:raise ValueError(m)
def extract(name,env):
 tree=ast.parse(SOURCE.read_bytes());fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),None)
 if fn is None:raise AssertionError('selected source missing '+name)
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual '+name,'exec'),env);return env[name]
class Tests(unittest.TestCase):
 def test_exact26_frames_order_hash_and_binary_newlines(self):
  rows=[('p'+str(i).zfill(2),hashlib.sha256((str(i)+'\nblob\x00').encode()).hexdigest()) for i in range(26)];parts=[(str(i)+'\nblob\x00').encode() for i in range(26)]
  wire=b''.join(b'a'*40+b' blob '+str(len(raw)).encode()+b'\n'+raw+b'\n' for raw in parts)
  fn=extract('_original_batch_rows',{'require':require,'hashlib':hashlib});out=fn(wire,rows)
  self.assertEqual(out,[{'path':n,'sha256':h,'bytes':len(raw)} for (n,h),raw in zip(rows,parts)])
 def test_bad_frames_missing_wrongtype_extent_hash_and_trailing(self):
  h=hashlib.sha256(b'x').hexdigest();rows=[('p',h)];frame=b'a'*40+b' blob 1\nx\n'
  fn=extract('_original_batch_rows',{'require':require,'hashlib':hashlib})
  bad=[b'p missing\n',frame.replace(b'blob',b'tree'),frame[:-1],frame+b'extra',frame.replace(b' 1\n',b' 2\n'),frame.replace(b'\nx\n',b'\ny\n'),b'a'*40+b' blob 2097153\n',b'a'*40+b' blob 0\n\n',b'a'*40+b' blob 01\nx\n']
  for raw in bad:
   with self.subTest(raw=raw[:70]),self.assertRaises(ValueError):fn(raw,rows)
 def test_request_batch_single_invocation_no_reuse(self):
  # The exact selected function must call only one batch reader for all26.
  tree=ast.parse(SOURCE.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='original_source_blobs');calls=[ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)]
  self.assertEqual(calls.count('_original_git_batch'),1);self.assertNotIn('subprocess.check_output',calls)
if __name__=='__main__':unittest.main(verbosity=2)

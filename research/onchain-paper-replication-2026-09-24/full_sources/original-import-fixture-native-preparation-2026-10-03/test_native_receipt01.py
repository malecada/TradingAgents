"""Actual receipt writer with pure cleanup dependency; no package imports."""
import ast,json,os,sys,tempfile,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent

def function():
    helper=D.parent/'original-import-fixture-io-candidate04-2026-10-02/owned_io.py'
    ns={'sys':sys};tree=ast.parse(helper.read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('CleanupFailure','_require','_fatal','_flatten','_cleanup')]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-accepted-cleanup','exec'),ns)
    tree=ast.parse((D/'resources.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_native_receipt')
    node.body=[n for n in node.body if not isinstance(n,ast.ImportFrom)]
    ns.update(Path=Path,os=types.SimpleNamespace(**{name:getattr(os,name) for name in ('open','close','write','fsync','fstat','stat','O_RDONLY','O_DIRECTORY','O_NOFOLLOW','O_WRONLY','O_CREAT','O_EXCL')}),json=json)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-native-receipt','exec'),ns)
    return ns

class Receipt(unittest.TestCase):
    def test_exclusive_durable_small_metadata(self):
        ns=function()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);ns['_native_receipt'](path,'worker.json',{'before_claim':True})
            self.assertEqual(json.loads((path/'worker.json').read_bytes()),{'before_claim':True})
            with self.assertRaises(FileExistsError):ns['_native_receipt'](path,'worker.json',{'before_claim':False})
            self.assertTrue(json.loads((path/'worker.json').read_bytes())['before_claim'])
    def test_primary_fatal_and_close_once(self):
        ns=function();first=MemoryError('write fatal');closed=[];actual_close=ns['os'].close
        def failwrite(*a):raise first
        def close(fd):closed.append(fd);actual_close(fd);raise OSError('uncertain')
        ns['os'].write=failwrite;ns['os'].close=close
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(MemoryError) as caught:ns['_native_receipt'](Path(tmp),'partial.json',{'before_claim':True})
            self.assertIs(caught.exception,first);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2);self.assertTrue((Path(tmp)/'partial.json').exists())
    def test_size_and_parent_redirect_refused(self):
        ns=function()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            with self.assertRaises(ValueError):ns['_native_receipt'](path,'large.json',{'x':'x'*65536})
            self.assertFalse((path/'large.json').exists());(path/'redirect').symlink_to(path,target_is_directory=True)
            with self.assertRaises(ValueError):ns['_native_receipt'](path/'redirect','x.json',{})

if __name__=='__main__':unittest.main()

import importlib.util,unittest,tempfile,hashlib,copy
from pathlib import Path
D=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('builder',D/'capsule_builder01.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
s=importlib.util.spec_from_file_location('controller',D/'controller01.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
class Capsule(unittest.TestCase):
    def test_real_tiny_export_validates_before_population(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'a.py').write_bytes(b'x=1\n');row={'origin':'a.py','target':'tradingagents/a.py','bytes':4,'sha256':hashlib.sha256(b'x=1\n').hexdigest(),'git_commit':None,'git_path':None}
            spec={'status':'reviewed-source-export-only','source_inventory':[row],'required_package_sources':['tradingagents/a.py']}
            wrong=copy.deepcopy(spec);wrong['source_inventory'][0]['sha256']='0'*64
            with self.assertRaises(ValueError):b.export_sources(wrong,root,root/'bad')
            self.assertFalse((root/'bad').exists())
            result=b.export_sources(spec,root,root/'fresh');self.assertEqual(result['files'],1);self.assertEqual((root/'fresh/tradingagents/a.py').read_bytes(),b'x=1\n')
            with self.assertRaises(ValueError):b.export_sources(spec,root,root/'fresh')
    def test_unsafe_or_duplicate_sources_refused(self):
        for name in ('../x','.env','keys/a','/tmp/a','.git/a','.venv/a','a/../b'):
            with self.assertRaises(ValueError):b.relative(name)
    def test_prospective_controller_cannot_launch(self):
        with self.assertRaises(ValueError):c.command({'status':'prospective-not-released'},'success')
    def test_cleanup_first_fatal_and_ordinary_uncertainty(self):
        original=b.os.close;first=MemoryError('first');seen=[]
        def fail(fd):seen.append(fd);raise OSError('uncertain')
        b.os.close=fail
        try:
            b.close_owned(5,first);self.assertEqual(seen,[5])
            with self.assertRaises(b.SourceCleanupFailure):b.close_owned(6,ValueError('body'))
        finally:b.os.close=original
if __name__=='__main__':unittest.main()

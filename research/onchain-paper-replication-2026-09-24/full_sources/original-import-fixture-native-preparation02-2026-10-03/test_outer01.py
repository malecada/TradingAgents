import unittest,tempfile,hashlib,ast
from pathlib import Path
import outer_controller01 as outer
class Outer(unittest.TestCase):
    def test_unreleased_stops_before_any_subprocess(self):
        original=outer.subprocess.check_output;calls=[]
        def forbidden(*a,**k):calls.append(a);raise AssertionError('subprocess forbidden')
        outer.subprocess.check_output=forbidden
        try:
            with self.assertRaises(ValueError):outer.check_release(Path('/unused'),{'status':'prospective'},'success')
            self.assertEqual(calls,[])
        finally:outer.subprocess.check_output=original
    def test_actual_source_envelope_git_join_and_missing_helper(self):
        names=['fixture_tools/outer_controller01.py','fixture_tools/raw_receipts01.py','fixture_tools/runtime_gate01.py']+['tradingagents/research/onchain_replication/'+n+'.py' for n in ('job','resources','owned_io','workflow_storage')]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pins={}
            for name in names:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'selected source');pins[name]=hashlib.sha256(path.read_bytes()).hexdigest()
            release={'source_files':pins,'capsule_commit':'a'*40};old=outer.subprocess.check_output
            try:
                outer.subprocess.check_output=lambda *a,**k:b'selected source'
                outer.source_envelope(root,release)
                outer.subprocess.check_output=lambda *a,**k:b'changed committed source'
                with self.assertRaises(ValueError):outer.source_envelope(root,release)
                release['source_files']={k:v for k,v in pins.items() if 'raw_receipts' not in k}
                with self.assertRaises(ValueError):outer.source_envelope(root,release)
            finally:outer.subprocess.check_output=old
    def test_signal_and_tail_actions_present_in_actual_run(self):
        tree=ast.parse(Path(outer.__file__).read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');text=ast.unparse(run)
        self.assertIn('signal.SIGINT, signal.SIGTERM',text);self.assertIn('signal.signal(number, handler)',text);self.assertIn('post-tail-storage.json',text);self.assertIn('excludes_own_file',text)
    def test_first_actual_fatal_outranks_synthetic_cleanup(self):
        class Cleanup(BaseException):pass
        first=MemoryError('first');second=SystemExit(8);ordinary=ValueError('ordinary');wrapper=Cleanup()
        self.assertIs(outer.select(first,second,Cleanup),first);self.assertIs(outer.select(wrapper,first,Cleanup),first);self.assertIs(outer.select(ordinary,wrapper,Cleanup),wrapper)
    def test_final_index_includes_partial_files_and_refuses_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'partial').write_bytes(b'failed attempt retained');index=outer.inventory(root);self.assertEqual(index['members'][0]['path'],'partial');self.assertEqual(index['members'][0]['bytes'],23)
            (root/'linked').symlink_to(root/'partial')
            with self.assertRaises(ValueError):outer.inventory(root)
if __name__=='__main__':unittest.main()

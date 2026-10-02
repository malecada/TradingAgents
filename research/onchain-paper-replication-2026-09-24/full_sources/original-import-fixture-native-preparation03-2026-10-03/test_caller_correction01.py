"""Actual source/helper counterexamples; synthetic records confer no authority."""
import ast
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

D = Path(__file__).resolve().parent
OLD = D.parent / 'original-import-fixture-native-preparation02-2026-10-03'
IMPL = Path(os.environ.get('NATIVE03_CALLER_SOURCE', str(D)))
sys.path.insert(0, str(OLD))
from test_raw01 import fixture

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

raw = load('actual_raw_under_test', IMPL / 'raw_receipts01.py')
sys.modules['raw_receipts01'] = raw
outer = load('actual_caller_under_test', IMPL / 'outer_controller01.py')

class CallerCorrection(unittest.TestCase):
    def test_receipt_cleanup_class_cannot_mask_later_actual_fatal(self):
        # Evaluate the actual run's IO assignment, then use the real receipt writer.
        tree = ast.parse((IMPL / 'outer_controller01.py').read_bytes())
        run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
        assignment = next(n for n in run.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'io' for t in n.targets))
        source = json.loads((OLD / 'source_inventory02.json').read_bytes())
        row = next(r for r in source['source_inventory'] if r['target'].endswith('/owned_io.py'))
        original = D.parents[3] / row['origin']
        # D.parents[3] is repository root; minimal package isolates class identity.
        existing = {k: v for k, v in sys.modules.items() if k == 'tradingagents' or k.startswith('tradingagents.')}
        for k in existing: del sys.modules[k]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                target = root / row['target']; target.parent.mkdir(parents=True)
                for parent in (root/'tradingagents', root/'tradingagents/research', target.parent):
                    (parent/'__init__.py').write_bytes(b'')
                target.write_bytes(original.read_bytes())
                sys.path.insert(0, str(root))
                try:
                    namespace = dict(vars(outer), root=root, release={'source_files': {row['target']: row['sha256']}})
                    exec(compile(ast.Module(body=[assignment], type_ignores=[]), 'actual_io_assignment', 'exec'), namespace)
                    chosen = namespace['io']
                    import tradingagents.research.onchain_replication.owned_io as canonical
                    resources = load('actual_native_receipt_writer', OLD/'resources.py')
                    real_close = os.close
                    def close_then_report_uncertainty(fd):
                        real_close(fd)
                        raise OSError('injected uncertain close after actual close')
                    os.close = close_then_report_uncertainty
                    try:
                        with self.assertRaises(canonical.CleanupFailure) as failure:
                            resources._native_receipt(root, 'receipt.json', {'synthetic': True})
                    finally:
                        os.close = real_close
                    for later in (MemoryError('actual fatal'), SystemExit(9)):
                        self.assertIs(outer.select(failure.exception, later, chosen.CleanupFailure), later)
                finally:
                    sys.path.remove(str(root))
        finally:
            for k in list(sys.modules):
                if k == 'tradingagents' or k.startswith('tradingagents.'): del sys.modules[k]
            sys.modules.update(existing)

    def test_missing_positive_native_observations_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); release,*_=fixture(root,'success')
            with self.assertRaises((ValueError, KeyError)):
                raw.authenticate(root,'success',release)

    def test_partial_stop_observations_survive_first_inspection_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); release,base,_,write=fixture(root,'success')
            live=raw.metadata(root,base+'/guard/final.json'); write(base+'/guard/live.json',live)
            original=outer.subprocess.run; observations=[]; calls=[]
            def command(args, **kwargs):
                calls.append(args)
                if len(calls)==1: raise OSError('first inspection failed')
                if args[2]=='stop':
                    return outer.subprocess.CompletedProcess(args,0,b'stop stdout',b'stop stderr')
                return outer.subprocess.CompletedProcess(args,0,'ActiveState=inactive\nSubState=dead\nResult=success\nControlGroup=\n','')
            outer.subprocess.run=command
            try:
                options={}
                if 'retain_observation' in inspect.signature(outer.stop_native).parameters:
                    options['retain_observation']=observations.append
                with self.assertRaises(OSError): outer.stop_native(root,base,2000000101,**options)
                self.assertEqual(len(calls),3)
                self.assertTrue(observations, 'original attempted stop evidence was discarded')
                self.assertEqual(observations[-1]['stop']['returncode'],0)
                self.assertEqual(observations[-1]['stop']['stdout'],'stop stdout')
                self.assertEqual(observations[-1]['after']['properties']['ActiveState'],'inactive')
            finally:
                outer.subprocess.run=original

    def test_actual_post_tail_check_enforces_disk_floor(self):
        helper=getattr(outer,'publish_post_tail',None)
        self.assertIsNotNone(helper,'actual caller has no final disk-floor boundary')
        class Watch:
            def check(self): return {'allocated_bytes':1,'logical_file_bytes':1}
        class Usage:
            free=10*1024**3-1
        original=outer.shutil.disk_usage; saved=[]
        outer.shutil.disk_usage=lambda path:Usage()
        try:
            with self.assertRaises(ValueError): helper(Path('/synthetic-root'),Watch(),lambda name,value:saved.append((name,value)))
            self.assertFalse(saved)
        finally:
            outer.shutil.disk_usage=original

    def test_disk_floor_is_checked_after_readback_publication(self):
        class Watch:
            def check(self): return {'allocated_bytes':1,'logical_file_bytes':1}
        class Usage:
            def __init__(self,free): self.free=free
        values=iter([10*1024**3+1024,10*1024**3-1]);saved=[]
        original=outer.shutil.disk_usage
        outer.shutil.disk_usage=lambda path:Usage(next(values))
        try:
            with self.assertRaises(ValueError): outer.publish_post_tail(Path('/synthetic-root'),Watch(),lambda name,value:saved.append((name,value)))
            self.assertEqual(saved[0][0],'post-tail-storage.json')
            self.assertEqual(saved[0][1]['disk_free_bytes'],10*1024**3+1024)
        finally:
            outer.shutil.disk_usage=original

    def test_final_tail_parser_refuses_below_floor_evidence(self):
        self.assertIsNotNone(getattr(raw,'authenticate_post_tail',None),'post-tail evidence is not authenticated')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/'fixture_outer/synthetic';d.mkdir(parents=True)
            (d/'post-tail-storage.json').write_text(json.dumps({'disk_free_bytes':10*1024**3-1,'disk_floor_bytes':10*1024**3}))
            with self.assertRaises((ValueError,KeyError)):raw.authenticate_post_tail(root,'synthetic',{'disk_floor_bytes':10*1024**3})

if __name__=='__main__': unittest.main()

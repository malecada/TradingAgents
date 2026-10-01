"""Selected production failure closes available owners; no numerical producer run."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication import native_producer as native
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_failure_fixture',HERE/'test_dispatch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class Tests(unittest.TestCase):
    fixture=base.Tests.fixture
    def test_sampler_failure_preserves_pair_and_feature_failure(self):
        f=self.fixture();m=native.api();sampler=m.seal.saved.artifacts.publication.producer
        with patch.object(sampler,'produce',side_effect=RuntimeError('injected sampler stop')):
            with self.assertRaisesRegex(RuntimeError,'injected sampler stop'):
                native.produce(f.run,'r',f.execution['payload']['representation_jobs']['r'],f.graphs,f.examples)
        failures=list((f.root/'research_artifacts/onchain_representations').glob('*/example-a/failed.json'))
        self.assertEqual(len(failures),1)
        directory=failures[0].parent
        pair_failures=list((f.root/'research_artifacts/onchain_pair_workflows').glob('*/example-a/failed.json'))
        self.assertEqual(len(pair_failures),1)
        note=json.loads((directory/'attempt-failed.json').read_bytes())
        self.assertEqual(note['cleanup_errors'],[])
        self.assertIn('injected sampler stop',note['reason'])
        print('PRESERVED_FAILURE',str(directory),flush=True)
    def test_pair_construction_failures_are_fatal_and_preserved(self):
        for stage in ('start.json','binding.json','final-lease'):
            with self.subTest(stage=stage):
                f=self.fixture();m=native.api();ownership=m.seal.ownership
                original=ownership.journal.write
                def fail(path,value):
                    if Path(path).name==stage:raise OSError('injected pair construction stop')
                    return original(path,value)
                from contextlib import ExitStack
                with ExitStack() as stack:
                    stack.enter_context(patch.object(ownership.journal,'write',side_effect=fail))
                    if stage=='final-lease':stack.enter_context(patch.object(ownership.OwnedJournal,'lease',side_effect=ValueError('injected pair construction stop')))
                    stack.enter_context(patch.object(m.seal.saved.artifacts.publication.producer,'produce',side_effect=AssertionError('sampler reached')))
                    with self.assertRaises(native.NativeProducerCleanupError):
                        native.produce(f.run,'r',f.execution['payload']['representation_jobs']['r'],f.graphs,f.examples)
                pair_root=f.root/'research_artifacts/onchain_pair_workflows'
                self.assertTrue(pair_root.is_dir())
                self.assertEqual(len(list(pair_root.glob('*/example-a'))),1)
                self.assertEqual(list(pair_root.glob('*/example-a/failed.json')),[])

if __name__=='__main__':unittest.main(verbosity=2)

"""Synthetic full-cardinality proof metadata; no 512-draw empirical execution."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('larger_proof_fixture',HERE.parent/'sampler-producer-2026-10-01/test_producer.py')
def api():return load('larger_proof_producer',HERE/'producer.py')

class Tests(unittest.TestCase):
    def test_512_absolute_references_fit_registered_bound_and_repeated_lease(self):
        m=api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'proof.json'
            fixed=ROOT/'research_artifacts/onchain_sampler_workflows'/('a'*64)/'example-research-attempt'
            value={'draws':[{'path':str(fixed/f'draw-{i:06d}.json'),'sha256':'b'*64} for i in range(512)],
                'source_owner_placeholder':'x'*65536}
            path.write_bytes(canonical_bytes(value));self.assertGreater(path.stat().st_size,65536)
            self.assertLess(path.stat().st_size,262144)
            metadata=m.Metadata(root)
            self.assertEqual(metadata.read(path,file_hash(path),cap=262144),value)
            metadata.lease()
            path.write_bytes(canonical_bytes(value|{'extra':True}))
            with self.assertRaises(ValueError):metadata.lease()
    def test_unregistered_size_and_overall_ceiling_refuse(self):
        m=api()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'proof.json';path.write_bytes(canonical_bytes({'v':'x'*70000}))
            for cap in (65536,True,0,2**21+1):
                with self.subTest(cap=cap),self.assertRaises(ValueError):m.Metadata(root).read(path,cap=cap)
    def test_registered_larger_policy_produces_actual_small_sample_artifact(self):
        m=api();f=base.Tests('test_actual_production_publishes_typed_samples_and_exact_completion_proof')
        self.addCleanup(f.doCleanups)
        owner=base.base.first.OwnershipTests;original=owner.input
        def configured(instance,name,value):
            if name=='sampler_execution':value=value|{'max_metadata_bytes':262144,'max_attempt_bytes':20_000_000}
            return original(instance,name,value)
        with patch.object(base,'api',return_value=m),patch.object(owner,'input',new=configured):f.fixture()
        result=f.produce();proof=json.loads(Path(result['proof']['path']).read_bytes())
        start=json.loads(Path(proof['start']['path']).read_bytes())
        self.assertEqual(start['reserved_encoded_bytes'],7*262144+10485760)
        self.assertEqual(result['admitted'].samples.identity,proof['sample_identity'])
        result['admitted'].lease()

if __name__=='__main__':unittest.main(verbosity=2)

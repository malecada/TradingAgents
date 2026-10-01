"""Current dictionary artifact admission/reuse without numerical fitting APIs."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tradingagents.research.onchain_replication.provenance import file_hash,canonical_bytes

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('dictionary_artifact_fixture',HERE.parent/'dictionary-publication-2026-10-01/test_publication.py')
def api():
    assert (HERE/'route.py').is_file(),'dictionary artifact admission missing'
    return load('dictionary_artifact_route',HERE/'route.py')

class Tests(unittest.TestCase):
    def fixture(self):
        self.m=api();m=self.m
        f=base.Tests('test_actual_dictionary_publication_has_exact_provenance_sizes_and_scalar_parity');self.addCleanup(f.doCleanups)
        with patch.object(base,'api',return_value=m.publication),patch.object(m.publication,'SOURCES',m.SOURCES):f.fixture()
        self.f=f;self.receipt=f.run_publication();self.proof=Path(self.receipt['path']);return f.f.f.f.f
    def admit(self):
        f=self.f.f.f.f.f
        return self.m.admit(f.owned,f.journal,sampler_input='sampler_execution',artifact_input='artifact_read',
            output_input='dictionary_output',proof_sha256=file_hash(self.proof))
    def forbidden_arrays(self):return patch.object(self.m.publication.reader,'read_component',side_effect=AssertionError('allocation before dictionary metadata admission'))
    def test_current_dictionary_reuse_does_not_enter_numerical_workload(self):
        f=self.fixture();before=f.owned.journal.reservations;pub=self.m.publication;pair=pub.driver.artifacts.consumer.serial.pair
        with patch.object(pub.driver,'fit',side_effect=AssertionError('dictionary refit')),patch.object(pub.driver.workload,'fit',side_effect=AssertionError('workload replay')),patch.object(pub.driver.artifacts.consumer.serial,'Serial',side_effect=AssertionError('serial execution')),patch.object(pair.PairSession,'create',side_effect=AssertionError('pair create')),patch.object(pair.PairSession,'resume',side_effect=AssertionError('pair resume')):
            result=self.admit();result.lease();again=self.admit()
        proof=json.loads(self.proof.read_bytes())
        self.assertEqual(result.dictionary.identity,proof['dictionary_identity'])
        self.assertEqual(again.dictionary.identity,result.dictionary.identity)
        self.assertEqual(result.record['dictionary_proof'],self.receipt)
        self.assertEqual(before,f.owned.journal.reservations)
    def test_conflicting_marker_refuses_before_array_loading(self):
        self.fixture();(self.proof.parent/'failed.json').write_text('{}')
        with self.forbidden_arrays(),self.assertRaises(ValueError):self.admit()
    def test_foreign_owner_refuses_even_with_new_expected_hash(self):
        self.fixture();proof=json.loads(self.proof.read_bytes());proof['owner']['experiment']='foreign';self.proof.write_bytes(canonical_bytes(proof))
        with self.forbidden_arrays(),self.assertRaises(ValueError):self.admit()
    def test_rehashed_false_matrix_byte_claim_is_refused(self):
        self.fixture();proof=json.loads(self.proof.read_bytes());proof['matrix_array_bytes']+=8
        self.proof.write_bytes(canonical_bytes(proof))
        with self.assertRaises(ValueError):self.admit()
    def test_corrupt_dictionary_member_refuses_before_array_loading(self):
        f=self.fixture();path=f.directory/'checkpoint-000001/array-000000.npy'
        raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
        with self.forbidden_arrays(),self.assertRaises(ValueError):self.admit()
    def test_later_dictionary_drift_invalidates_receipt(self):
        f=self.fixture();result=self.admit();path=f.directory/'checkpoint-000001/array-000000.npy'
        raw=bytearray(path.read_bytes());raw[-1]^=1;path.write_bytes(raw)
        with self.assertRaises(ValueError):result.lease()
    def test_proof_drift_during_dictionary_loading_refuses_return(self):
        f=self.fixture();reader=self.m.publication.reader;original=reader.read_component;hit=[]
        def changed(path,*args,**kwargs):
            result=original(path,*args,**kwargs)
            if Path(path).parent==f.directory/'checkpoint-000001':
                hit.append(True);(self.proof.parent/'failed.json').write_text('{}')
            return result
        with patch.object(reader,'read_component',side_effect=changed),self.assertRaises(ValueError):self.admit()
        self.assertEqual(hit,[True])

if __name__=='__main__':unittest.main(verbosity=2)

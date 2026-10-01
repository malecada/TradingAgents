"""Actual registered saved-MCM to graph tensors; synthetic guard observations."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from contextlib import ExitStack
import numpy as np
from tests.research.onchain_replication import test_matching_owner as owner_fixture
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.evaluation import feature_hash
from tradingagents.research.onchain_replication.neighborhoods import NeighborhoodIndex
from tradingagents.research.onchain_replication.array_neighborhoods import ArrayNeighborhoodIndex

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('graph_feature_fixture',HERE.parent/'mcm-artifact-route-2026-10-01/test_route.py')
def api():
    assert (HERE/'route.py').exists(),'registered graph feature route missing'
    return load('graph_feature_route',HERE/'route.py')

class Tests(unittest.TestCase):
    def fixture(self,mode=None):
        self.m=api();m=self.m
        f=base.Tests('test_saved_reuse_and_lease_forbid_all_numerical_and_fresh_dictionary_apis');self.addCleanup(f.doCleanups)
        original=owner_fixture.OwnershipTests.input
        policy={'schema_version':1,'max_numeric_bytes':1000,'chunk_entries':2}
        if mode=='cap':policy['max_numeric_bytes']=1
        def configured(instance,name,value):
            if name=='plan':
                original(instance,'feature_tensor',policy);value['producers']['p']['feature_tensor_input']='feature_tensor'
            if name=='execution_job':value['payload']['representation_jobs']['r']['feature_tensor_input']='wrong' if mode=='route' else 'feature_tensor'
            return original(instance,name,value)
        with patch.object(base,'api',return_value=m.saved),patch.object(m.saved,'SOURCES',m.SOURCES),patch.object(owner_fixture.OwnershipTests,'input',new=configured):
            owner=f.fixture()
        self.f=f;self.owner=owner;return owner

    def prepare(self,**changes):
        kw=dict(dictionary_ticket=self.f.ticket,graph_hash=self.f.f.f.graph_hash,
            mcm_input='mcm_execution',output_input='mcm_output',read_input='mcm_read',
            proof_sha256=file_hash(self.f.proof_path),feature_input='feature_tensor')
        kw.update(changes)
        return self.m.prepare(self.owner.owned,self.owner.journal,**kw)

    def test_real_saved_mcm_to_exact_tensors_without_numerical_recomputation(self):
        f=self.fixture();m=self.m;before=f.owned.journal.reservations
        expected=np.load(f.directory/'checkpoint-000002/array-000000.npy',allow_pickle=False)
        graph=f.workload._graphs[self.f.f.f.graph_hash]
        with ExitStack() as stack:
            for obj,name in ((m.saved.artifacts,'admit'),(m.saved.publication.driver,'compute'),
                (m.saved.publication.driver.serial,'Serial'),(NeighborhoodIndex,'neighborhood'),(ArrayNeighborhoodIndex,'neighborhood')):
                stack.enter_context(patch.object(obj,name,side_effect=AssertionError('numerical recomputation')))
            result=self.prepare();result.lease()
        np.testing.assert_array_equal(result.feature['mcm'].numpy(),expected)
        np.testing.assert_array_equal(result.feature['edge_index'].numpy(),graph.edge_index)
        self.assertEqual(result.record['feature_hash'],feature_hash(dict(result.feature)))
        self.assertEqual(result.record['mcm_provenance']['mcm_proof'],self.f.proof)
        self.assertEqual(before,f.owned.journal.reservations)
        with self.assertRaises(TypeError):result.feature['mcm']=result.feature['edge_index']
        with self.assertRaises(AttributeError):result.record={}
        result.feature['mcm'][0,0]=.125
        with self.assertRaises(ValueError):result.lease()

    def test_selected_route_and_numeric_cap_refuse_before_saved_matrix_load(self):
        for mode in ('route','cap'):
            with self.subTest(mode=mode):
                self.fixture(mode)
                with patch.object(self.m.saved,'admit',side_effect=AssertionError('MCM loaded before policy refusal')):
                    with self.assertRaises(ValueError):self.prepare()

    def test_unknown_graph_unissued_dictionary_and_corrupt_matrix_refuse(self):
        f=self.fixture();m=self.m
        with patch.object(m.boundary,'materialize',side_effect=AssertionError('tensors before admission')):
            for changes in ({'graph_hash':'f'*64},{'dictionary_ticket':m.saved.DictionaryTicket()}):
                with self.subTest(changes=next(iter(changes))),self.assertRaises(ValueError):self.prepare(**changes)
            p=f.directory/'checkpoint-000002/array-000000.npy';raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
            with self.assertRaises(ValueError):self.prepare()

    def test_registered_policy_drift_after_conversion_refuses_return(self):
        self.fixture();m=self.m;original=m.boundary.materialize
        def changed(*args,**kwargs):
            result=original(*args,**kwargs)
            ad=self.owner.owned.workload.bound._run.admission
            (ad.root/ad.inputs['feature_tensor']['path']).write_text('{}')
            return result
        with patch.object(m.boundary,'materialize',side_effect=changed),self.assertRaises(ValueError):self.prepare()

if __name__=='__main__':unittest.main(verbosity=2)

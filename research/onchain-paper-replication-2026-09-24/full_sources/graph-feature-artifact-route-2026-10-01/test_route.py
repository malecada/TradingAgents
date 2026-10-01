"""Registered native graph checkpoint reuse; actual tiny predecessor fixtures."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from contextlib import ExitStack
import numpy as np
from tests.research.onchain_replication import test_matching_owner as owner_fixture
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash
from tradingagents.research.onchain_replication.evaluation import feature_hash
from tradingagents.research.onchain_replication.neighborhoods import NeighborhoodIndex
from tradingagents.research.onchain_replication.array_neighborhoods import ArrayNeighborhoodIndex

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('graph_reuse_fixture',HERE.parent/'graph-feature-publication-2026-10-01/test_publication.py')
def api():
    assert (HERE/'route.py').exists(),'saved graph feature route missing'
    return load('graph_reuse_route',HERE/'route.py')

class Tests(unittest.TestCase):
    def fixture(self,mode=None):
        self.m=api();m=self.m
        f=base.Tests('test_actual_graph_completion_strictly_roundtrips_and_refuses_relaunch');self.addCleanup(f.doCleanups)
        original=owner_fixture.OwnershipTests.input
        policy={'schema_version':1,'max_array_bytes':1024,'max_numeric_bytes':1000,'chunk_entries':2}
        if mode=='cap':policy['max_numeric_bytes']=1
        def configured(instance,name,value):
            if name=='plan':
                original(instance,'graph_read',policy);value['producers']['p']['graph_read_input']='graph_read'
            if name=='execution_job':value['payload']['representation_jobs']['r']['graph_read_input']='graph_read'
            return original(instance,name,value)
        with patch.object(base,'api',return_value=m.publication),patch.object(m.publication,'SOURCES',m.SOURCES),patch.object(owner_fixture.OwnershipTests,'input',new=configured):
            owner=f.fixture()
        self.f=f;self.owner=owner;self.proof=f.produce();self.path=Path(self.proof['path']);return owner

    def admit(self,**changes):
        kw=dict(dictionary_ticket=self.f.f.f.ticket,graph_hash=self.f.graph_hash,mcm_input='mcm_execution',
            mcm_output_input='mcm_output',mcm_read_input='mcm_read',feature_input='feature_tensor',
            output_input='graph_output',read_input='graph_read',proof_sha256=file_hash(self.path))
        kw.update(changes)
        return self.m.admit(self.owner.owned,self.owner.journal,**kw)

    def test_exact_saved_reuse_and_output_lease_without_numeric_reentry(self):
        f=self.fixture();m=self.m;before=f.owned.journal.reservations
        expected=np.load(f.directory/'checkpoint-000003/array-000000.npy',allow_pickle=False)
        with ExitStack() as stack:
            for obj,name in ((m.publication.route,'prepare'),(m.saved.artifacts,'admit'),
                (m.saved.publication.driver,'compute'),(m.saved.publication.driver.serial,'Serial'),
                (NeighborhoodIndex,'neighborhood'),(ArrayNeighborhoodIndex,'neighborhood')):
                stack.enter_context(patch.object(obj,name,side_effect=AssertionError('numerical reentry')))
            result=self.admit();result.lease()
        np.testing.assert_array_equal(result.feature['mcm'].numpy(),expected)
        np.testing.assert_array_equal(result.feature['edge_index'].numpy(),f.workload._graphs[self.f.graph_hash].edge_index)
        self.assertEqual(result.record['feature_hash'],feature_hash(dict(result.feature)))
        self.assertEqual(result.record['graph_proof'],self.proof);self.assertEqual(before,f.owned.journal.reservations)
        result.feature['mcm'][0,0]=.125
        with self.assertRaises(ValueError):result.lease()

    def test_false_proof_duplicate_conflict_and_corruption_refuse_before_arrays(self):
        f=self.fixture();m=self.m;raw=self.path.read_bytes();original=json.loads(raw)
        with patch.object(m.reader,'read_component',side_effect=AssertionError('array before metadata refusal')):
            for change in ({'graph_hash':'f'*64},{'array_bytes':True},{'encoded_artifact_bytes':1},{'event_index':False}):
                with self.subTest(change=next(iter(change))):
                    self.path.write_bytes(canonical_bytes(original|change))
                    with self.assertRaises(ValueError):self.admit()
            self.path.write_bytes(raw)
            f.journal.records.append(f.journal.records[3])
            with self.assertRaises(ValueError):self.admit()
            f.journal.records.pop()
            conflict=self.path.parent/'failed.json';conflict.write_text('{}')
            with self.assertRaises(ValueError):self.admit()
            conflict.unlink()
            p=f.directory/'checkpoint-000003/array-000000.npy';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
            with self.assertRaises(ValueError):self.admit()

    def test_copy_allowance_refuses_before_upstream_or_graph_array_loading(self):
        self.fixture('cap')
        with patch.object(self.m.reader,'read_component',side_effect=AssertionError('array before budget refusal')):
            with self.assertRaises(ValueError):self.admit()

    def test_post_read_component_drift_refuses_return(self):
        f=self.fixture();m=self.m;original=m.reader.read_component
        def changed(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if Path(path).parent.name=='checkpoint-000003':
                target=Path(path).parent/'array-000000.npy';raw=bytearray(target.read_bytes());raw[-1]^=1;target.write_bytes(raw)
            return value
        with patch.object(m.reader,'read_component',side_effect=changed),self.assertRaises(ValueError):self.admit()

if __name__=='__main__':unittest.main(verbosity=2)

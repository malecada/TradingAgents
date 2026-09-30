"""Actual registered owner/route to one tiny durable numerical pair.

Kernel guard observations are mocked. Samples are actual synthetic draws, but
are not published sampler artifacts; this is not empirical admission.
"""
from dataclasses import replace
import importlib.util
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.provenance import file_hash

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fixture=load('consumer_owner_fixture',HERE.parent/'pair-owner-route-2026-09-30/test_ownership.py')
workload=load('consumer_workload',HERE.parent/'pair-workload-2026-09-30/workload.py')
def api():
    assert (HERE/'route.py').is_file(),'admitted consumer constructor missing'
    return load('consumer_route_candidate',HERE/'route.py')

class Tests(unittest.TestCase):
    def fixture(self,omit=False):
        self.m=api();module=self.m
        class Selected(fixture.Parent):
            bridge=module.ownership;close_pair=False
            def prepare(self):
                for name in module.SOURCES:
                    if omit and name==str((HERE/'route.py').relative_to(ROOT)):continue
                    path=ROOT/name;target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(path,target);self.exp['source_files'][name]=file_hash(target)
                    fixture.first.git(self.root,'add','--',name)
                super().prepare()
        f=Selected('test_actual_claim_owner_and_old_numerical_anchor_are_distinct')
        self.addCleanup(f.doCleanups);f.setUp();self.f=f
        settings=f.configs['dictionary']|{'train_start':f.fold.train_start,'train_end':f.fold.train_end}
        self.samples=sample_neighborhoods(f.graphs,settings,11)
        return f
    def first_pair(self):
        f=self.f;seen=[]
        class Stop(Exception):pass
        def capture(p,a,b):seen.append((p,a,b));raise Stop
        with self.assertRaises(Stop):
            workload.fit(self.samples,f.configs['matching'],dict(f.workload.settings),
                workflow=f.identity,backend=self.m.serial.pair.BACKEND,
                max_entries=f.control['max_entries'],score_pair=capture)
        return seen[0]
    def test_admitted_pair_matches_scalar_and_completed_replay_does_not_allocate(self):
        f=self.fixture();consumer=self.m.dictionary_consumer(f.owned,self.samples);p,a,b=self.first_pair()
        value=consumer(p,a,b)
        self.assertEqual(value['score'],match_reference(a,b,f.configs['matching']).score)
        completed_reservations=f.owned.journal.reservations
        self.assertGreater(completed_reservations,0)
        self.assertLessEqual(completed_reservations,f.control['max_checkpoints'])
        self.assertEqual(f.owned.journal.state['pending'],None)
        with patch.object(self.m.serial.pair.PairSession,'create',side_effect=AssertionError('completed create')),\
             patch.object(self.m.serial.pair.PairSession,'resume',side_effect=AssertionError('completed resume')):
            self.assertEqual(consumer(p,a,b),value)
        self.assertEqual(f.owned.journal.reservations,completed_reservations)
    def test_altered_samples_refuse_before_any_pair_reservation(self):
        f=self.fixture()
        with self.assertRaises(ValueError):self.m.dictionary_consumer(f.owned,replace(self.samples,seed=12))
        self.assertEqual(f.owned.journal.reservations,0)
        self.assertEqual(list((f.owned.journal.root/'pairs').iterdir()),[])
    def test_changed_registered_control_stops_existing_consumer_before_allocation(self):
        f=self.fixture();consumer=self.m.dictionary_consumer(f.owned,self.samples);args=self.first_pair()
        (f.root/'pair_workload.json').write_text('{}')
        with self.assertRaises(ValueError):consumer(*args)
        self.assertEqual(f.owned.journal.reservations,0)
        self.assertEqual(list((f.owned.journal.root/'pairs').iterdir()),[])
    def test_unregistered_constructor_refuses_before_reservation(self):
        f=self.fixture(omit=True)
        with self.assertRaises(ValueError):self.m.dictionary_consumer(f.owned,self.samples)
        self.assertEqual(f.owned.journal.reservations,0)
    def test_plain_object_cannot_supply_an_owner(self):
        m=api()
        with self.assertRaises(ValueError):m.dictionary_consumer(object(),None)

def load_tests(loader,tests,pattern):return loader.loadTestsFromTestCase(Tests)
if __name__=='__main__':unittest.main(verbosity=2)

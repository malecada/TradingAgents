"""Tiny real pair/journal composition; no admitted empirical execution."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import numpy as np
from unittest.mock import patch
from tradingagents.research.onchain_replication import matching_pair as pair
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.cache import cache_key
from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY, CONTEXT
from tests.research.onchain_replication.test_matching_reference import graph, config
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class Tests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((HERE/'serial.py').exists(),'serial composition missing')
        self.m=load('serial_candidate',HERE/'serial.py')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        (self.root/'pairs').mkdir()
        self.jm=load('journal_candidate',HERE.parent/'pair-journal-2026-09-30/journal.py')
        self.limits={'max_reserved_bytes':100000000,'max_reservations':100,'max_events':200}
        self.j=self.jm.Journal(self.root,'first','d'*64,CONTEXT['namespace'],self.limits)
        self.a=graph([[0.],[.3]],[(0,1,.2)]);self.b=graph([[0.],[.1]],[(0,1,.3)])
        self.c=config()|{'max_iterations':1};self.scope='e'*64
        self.purpose={'schema_version':1,'kind':'dictionary','workload_sha256':self.scope,
                      'block_sha256':'f'*64,'sample_indices':[1,0],
                      'typed_graphs':[graph_identity(self.a),graph_identity(self.b)]}
        self.leases=0
    def lease(self):self.leases+=1
    def consumer(self,j=None,**kw):
        args=dict(context=CONTEXT,policy=POLICY,config=self.c,workload_sha256=self.scope,
                  lease=self.lease,operations_per_checkpoint=10000,max_checkpoints=10)
        args.update(kw);return self.m.Serial(j or self.j,**args)
    def test_actual_pair_score_matches_scalar_and_publication_is_durable(self):
        value=self.consumer()(self.purpose,self.a,self.b)
        self.assertEqual(value,{'purpose_sha256':cache_key(self.purpose),'score':match_reference(self.a,self.b,self.c).score})
        self.assertIsNone(self.j.state['pending']);self.assertGreater(self.leases,0)
        self.assertEqual(self.j.state['pairs'][self.jm.digest(self.purpose)]['kind'],'complete')
    def test_completed_pair_reuse_forbids_every_solver_entry(self):
        c=self.consumer();expected=c(self.purpose,self.a,self.b);before=self.j.reservations
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('create repeated')),patch.object(pair.PairSession,'resume',side_effect=AssertionError('resume repeated')):
            self.assertEqual(c(self.purpose,self.a,self.b),expected)
        self.assertEqual(self.j.reservations,before)
    def test_partial_checkpoint_new_owner_resumes_and_preserves_parent(self):
        c=self.consumer(operations_per_checkpoint=1,max_checkpoints=1)
        with self.assertRaises(self.m.CheckpointStop):c(self.purpose,self.a,self.b)
        self.assertIsNone(self.j.state['pending'])
        parent=self.j.seal('failed');raw=Path(parent['path']).read_bytes();spent=self.j.reserved_bytes
        child=self.jm.Journal(self.root,'child','a'*64,CONTEXT['namespace'],self.limits,parent=parent)
        with patch.object(pair.engine,'create',side_effect=AssertionError('restarted')):
            value=self.consumer(child)(self.purpose,self.a,self.b)
        self.assertEqual(value['score'],match_reference(self.a,self.b,self.c).score)
        self.assertGreater(child.reserved_bytes,spent);self.assertEqual(Path(parent['path']).read_bytes(),raw)
    def test_pending_publication_refuses_without_solver(self):
        identity=pair.identity(self.a,self.b,self.c,CONTEXT)
        self.m.extent.reserve_pair(self.j,self.purpose,identity,POLICY)
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('allocated')):
            with self.assertRaisesRegex(ValueError,'reconciliation'):self.consumer()(self.purpose,self.a,self.b)
    def test_wrong_workload_or_orientation_refused_before_reservation(self):
        for purpose in (self.purpose|{'workload_sha256':'0'*64},self.purpose|{'typed_graphs':list(reversed(self.purpose['typed_graphs']))}):
            with self.assertRaises(ValueError):self.consumer()(purpose,self.a,self.b)
        self.assertEqual(self.j.reservations,0)
    def test_cumulative_quota_refuses_before_pair_allocation(self):
        self.j.policy['max_reserved_bytes']=self.j.reserved_bytes
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('allocated')):
            with self.assertRaisesRegex(ValueError,'quota'):self.consumer()(self.purpose,self.a,self.b)
    def test_publication_gap_stays_pending_and_is_not_rerun(self):
        c=self.consumer()
        with patch.object(self.j,'publish',side_effect=OSError('event lost')):
            with self.assertRaises(OSError):c(self.purpose,self.a,self.b)
        self.assertIsNotNone(self.j.state['pending'])
        self.assertTrue(Path(self.j.state['pending']['path']).exists())
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('rerun')):
            with self.assertRaises(ValueError):self.consumer()(self.purpose,self.a,self.b)
    def test_adapter_cleanup_note_is_fatal_even_without_returned_handle(self):
        c=self.consumer();error=OSError('construction failed')
        error.add_note('Pair cleanup also failed: OSError')
        with patch.object(pair.PairSession,'create',side_effect=error):
            with self.assertRaises(self.m.CleanupFailure):c(self.purpose,self.a,self.b)
        with self.assertRaisesRegex(ValueError,'poisoned'):c(self.purpose,self.a,self.b)
    def test_actual_dictionary_and_mcm_workloads_use_durable_scores(self):
        workload=load('serial_workload',HERE.parent/'pair-workload-2026-09-30/workload.py')
        g=graph([[0.],[.2],[.5]],[(0,1,.3),(1,2,.7)])
        settings=cfg()|dict(sample_count=3,size=2,partition_threshold=4,partition_size=4)
        samples=sample_neighborhoods([g],settings,11)
        kw=dict(workflow=CONTEXT['namespace'],backend=pair.BACKEND,max_entries=100)
        purposes=[]
        def oracle(p,a,b):
            purposes.append(p)
            return {'purpose_sha256':cache_key(p),'score':float(match_reference(a,b,self.c).score)}
        expected=workload.fit(samples,self.c,settings,score_pair=oracle,**kw)
        c=self.consumer(workload_sha256=expected['workload_sha256'])
        actual=workload.fit(samples,self.c,settings,score_pair=c,**kw)
        self.assertEqual(actual['dictionary'].identity,expected['dictionary'].identity)
        for a,b in zip(actual['matrices'],expected['matrices'],strict=True):
            np.testing.assert_array_equal(a['matrix'],b['matrix'])
        purposes.clear()
        want=workload.mcm(g,actual['dictionary'],self.c,score_pair=oracle,**kw)
        mc=self.consumer(workload_sha256=purposes[0]['workload_sha256'])
        got=workload.mcm(g,actual['dictionary'],self.c,score_pair=mc,**kw)
        np.testing.assert_array_equal(got,want)
        count=self.j.reservations
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('complete pair recomputed')),patch.object(pair.PairSession,'resume',side_effect=AssertionError('complete pair reopened')):
            replay=workload.mcm(g,actual['dictionary'],self.c,score_pair=mc,**kw)
        np.testing.assert_array_equal(replay,got);self.assertEqual(self.j.reservations,count)
    def test_cleanup_failure_is_fatal_and_poisoned(self):
        c=self.consumer();close=pair.PairSession.close
        def bad_close(obj):close(obj);raise OSError('cleanup failed')
        with patch.object(pair.PairSession,'close',bad_close):
            with self.assertRaises(self.m.CleanupFailure):c(self.purpose,self.a,self.b)
        with self.assertRaisesRegex(ValueError,'poisoned'):c(self.purpose,self.a,self.b)


if __name__=='__main__':unittest.main(verbosity=2)

"""Tiny numerical/workload tests; in-memory callback is NOT journal admission."""
import importlib.util
from pathlib import Path
from dataclasses import replace
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods,NeighborhoodIndex
from tradingagents.research.onchain_replication.dictionary import fit_dictionary,reorder_dictionary
from tradingagents.research.onchain_replication.matching_reference import match_reference
from tradingagents.research.onchain_replication.matching_pair import BACKEND
from tradingagents.research.onchain_replication.cache import cache_key

HERE=Path(__file__).resolve().parent

def api():
    assert (HERE/'workload.py').is_file(),'pair workload implementation missing'
    spec=importlib.util.spec_from_file_location('workload_candidate',HERE/'workload.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class Scores:
    """Explicit test-only completed score store; missing and zero stay distinct."""
    def __init__(self,matching,fail=None,zero=False):
        self.matching=matching;self.saved={};self.computed=[];self.asked=[]
        self.fail=fail;self.zero=zero
    def __call__(self,purpose,a,b):
        key=cache_key(purpose);self.asked.append(purpose)
        if key not in self.saved:
            if self.fail is not None and len(self.computed)==self.fail:
                raise RuntimeError('synthetic interruption')
            score=0. if self.zero else float(match_reference(a,b,self.matching).score)
            self.computed.append(key);self.saved[key]={'purpose_sha256':key,'score':score}
        return dict(self.saved[key])


class Tests(unittest.TestCase):
    def setUp(self):
        self.m=api();self.match=config()|{'beta_final':1.}
        self.g=graph([[i*.2] for i in range(7)],[(0,1,1),(2,1,.7),(3,4,.4),(5,6,.2)])
        self.settings=cfg()|dict(sample_count=7,size=2,partition_threshold=4,partition_size=4)
        self.samples=sample_neighborhoods([self.g],self.settings,11)
        self.kw=dict(workflow='a'*64,backend=BACKEND,max_entries=10000)

    def fit(self,scores,**changes):
        return self.m.fit(self.samples,self.match,self.settings,score_pair=scores,**(self.kw|changes))

    def test_full_distances_hierarchy_and_medoids_match_scalar_oracle(self):
        matrices=[]
        from tradingagents.research.onchain_replication import dictionary as original
        real=original.cluster_medoids
        def capture(matrix,k):
            matrices.append(matrix.copy());return real(matrix,k)
        with patch.object(original,'cluster_medoids',capture):
            oracle=fit_dictionary(self.samples,self.match,self.settings)
        result=self.fit(Scores(self.match))
        self.assertEqual(len(result['matrices']),len(matrices))
        for got,want in zip(result['matrices'],matrices,strict=True):
            np.testing.assert_array_equal(got['matrix'],want)
        d=result['dictionary']
        self.assertEqual(d.memberships,oracle.memberships);self.assertEqual(d.hierarchy,oracle.hierarchy)
        self.assertEqual([g.center_id for g in d.representatives],[g.center_id for g in oracle.representatives])
        self.assertNotEqual(d.identity,oracle.identity)
        self.assertEqual(d.config['pair_execution']['name'],BACKEND['name'])

    def test_interruption_after_first_direction_reuses_without_changing_rng_or_partition(self):
        baseline=Scores(self.match);expected=self.fit(baseline)
        interrupted=Scores(self.match,fail=1)
        with self.assertRaisesRegex(RuntimeError,'interruption'):self.fit(interrupted)
        first=interrupted.computed[0];interrupted.fail=None;interrupted.asked=[]
        actual=self.fit(interrupted)
        self.assertEqual(interrupted.asked,baseline.asked)
        self.assertEqual(interrupted.computed,baseline.computed)
        self.assertEqual(interrupted.computed.count(first),1)
        self.assertEqual(actual['dictionary'].identity,expected['dictionary'].identity)
        for a,b in zip(actual['matrices'],expected['matrices'],strict=True):np.testing.assert_array_equal(a['matrix'],b['matrix'])

    def test_every_direction_and_partition_has_explicit_distinct_purpose(self):
        scores=Scores(self.match);self.fit(scores)
        self.assertEqual(len(scores.asked)%2,0)
        for a,b in zip(scores.asked[::2],scores.asked[1::2],strict=True):
            self.assertEqual(a['kind'],'dictionary');self.assertEqual(a['block_sha256'],b['block_sha256'])
            self.assertEqual(a['sample_indices'],list(reversed(b['sample_indices'])))
            self.assertEqual(a['typed_graphs'],list(reversed(b['typed_graphs'])))
            self.assertNotEqual(cache_key(a),cache_key(b))
        self.assertEqual(len(scores.asked),len({cache_key(x) for x in scores.asked}))

    def test_mcm_partial_row_and_valid_zero_replay(self):
        d=self.fit(Scores(self.match))['dictionary']
        saved=Scores(self.match,fail=1,zero=True)
        with self.assertRaisesRegex(RuntimeError,'interruption'):
            self.m.mcm(self.g,d,self.match,score_pair=saved,**self.kw)
        self.assertEqual(len(saved.saved),1);first=saved.computed[0]
        saved.fail=None;saved.asked=[]
        values=self.m.mcm(self.g,d,self.match,score_pair=saved,**self.kw)
        self.assertEqual(values.dtype,np.float32);self.assertEqual(values.shape,(7,2))
        np.testing.assert_array_equal(values,np.zeros((7,2),dtype=np.float32))
        self.assertEqual(len(saved.computed),14);self.assertEqual(saved.computed.count(first),1)
        self.assertEqual([(p['center_index'],p['motif_index']) for p in saved.asked],[(i,j) for i in range(7) for j in range(2)])

    def test_mcm_values_match_scalar_oracle_and_bind_representative_order(self):
        d=self.fit(Scores(self.match))['dictionary'];scores=Scores(self.match)
        values=self.m.mcm(self.g,d,self.match,score_pair=scores,**self.kw)
        idx=NeighborhoodIndex(self.g)
        want=np.asarray([[match_reference(idx.neighborhood(i,d.config),motif,self.match).score for motif in d.representatives] for i in range(7)],dtype=np.float32)
        np.testing.assert_array_equal(values,want)
        rev=reorder_dictionary(d,[1,0]);other=Scores(self.match)
        out=self.m.mcm(self.g,rev,self.match,score_pair=other,**self.kw)
        np.testing.assert_array_equal(out,values[:,::-1])
        self.assertTrue(set(scores.saved).isdisjoint(other.saved))
        self.assertTrue(all(p['center_id']==self.g.node_ids[p['center_index']] for p in scores.asked))

    def test_foreign_callback_reference_rejected(self):
        def bad(p,a,b):return {'purpose_sha256':'f'*64,'score':.5}
        with self.assertRaisesRegex(ValueError,'purpose'):self.fit(bad)

    def test_invalid_scores_not_published_as_distance(self):
        for score in (float('nan'),float('inf'),True,'0.5'):
            with self.subTest(score=score):
                with self.assertRaises(ValueError):self.fit(lambda p,a,b:{'purpose_sha256':cache_key(p),'score':score})

    def test_backend_and_capacity_refused_before_pair_call(self):
        def forbidden(*a):self.fail('numerical callback must not run')
        with self.assertRaises(ValueError):self.fit(forbidden,backend=BACKEND|{'version':1})
        with self.assertRaisesRegex(ValueError,'capacity'):self.fit(forbidden,max_entries=1)
        d=self.fit(Scores(self.match))['dictionary']
        with self.assertRaisesRegex(ValueError,'capacity'):
            self.m.mcm(self.g,d,self.match,score_pair=forbidden,**(self.kw|{'max_entries':1}))

    def test_changed_sample_identity_or_graph_record_refused(self):
        def forbidden(*a):self.fail('numerical callback must not run')
        for samples in (replace(self.samples,identity='f'*64),replace(self.samples,graphs=tuple(reversed(self.samples.graphs)))):
            with self.assertRaises(ValueError):self.m.fit(samples,self.match,self.settings,score_pair=forbidden,**self.kw)

    def test_foreign_dictionary_backend_or_matching_refused_before_callback(self):
        d=fit_dictionary(self.samples,self.match,self.settings)
        def forbidden(*a):self.fail('numerical callback must not run')
        with self.assertRaises(ValueError):self.m.mcm(self.g,d,self.match,score_pair=forbidden,**self.kw)
        d=self.fit(Scores(self.match))['dictionary']
        with self.assertRaises(ValueError):self.m.mcm(self.g,d,self.match|{'beta_final':2.},score_pair=forbidden,**self.kw)

    def test_workflow_and_matching_changes_do_not_hit_old_scores(self):
        old=Scores(self.match);self.fit(old)
        new=Scores(self.match);self.fit(new,workflow='b'*64)
        self.assertTrue(set(old.saved).isdisjoint(new.saved))
        changed=Scores(self.match|{'beta_final':2.})
        self.m.fit(self.samples,changed.matching,self.settings,score_pair=changed,**self.kw)
        self.assertTrue(set(old.saved).isdisjoint(changed.saved))

if __name__=='__main__':unittest.main(verbosity=2)

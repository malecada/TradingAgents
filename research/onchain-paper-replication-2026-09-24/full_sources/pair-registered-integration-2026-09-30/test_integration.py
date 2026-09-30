"""Synthetic actual ResearchRun/Binding integration, not an empirical launcher.

Kernel guard/death observations are mocked. Pair routing below is fixture wiring,
not a production admission layer or proof of physical whole-workflow accounting.
"""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from tests.research.onchain_replication import test_matching_successor as successor
from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY
from tests.research.onchain_replication.test_matching_reference import graph, config
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication import matching_pair as pair
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.dictionary import fit_dictionary
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.provenance import file_hash, thaw

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

serial=load('registered_serial',HERE.parent/'pair-serial-composition-2026-09-30/serial.py')
workload=load('registered_workload',HERE.parent/'pair-workload-2026-09-30/workload.py')
journals=load('registered_journal',HERE.parent/'pair-journal-2026-09-30/journal.py')
LIMITS={'max_reserved_bytes':100_000_000,'max_reservations':180,'max_events':360}

def snapshot(path):
    return {str(p.relative_to(path)):file_hash(p) for p in path.rglob('*') if p.is_file()}

def consumer(bound,journal,scope,matching,**kw):
    options=dict(operations_per_checkpoint=10000,max_checkpoints=10)
    options.update(kw)
    return serial.Serial(journal,context=thaw(bound.context),policy=thaw(bound.limits),
        config=matching,workload_sha256=scope,lease=bound.lease,**options)


class First(successor._FirstOwner):
    __test__=False
    mode='dictionary'
    def prepare(self):
        self.policy['limits']=copy.deepcopy(POLICY)
        self.input('pair_policy',self.policy)
        self.descriptor['pair_execution']['policy_sha256']=self.exp['inputs']['pair_policy']['sha256']
        self.matching=config()|{'max_iterations':1,'beta_final':1.}
        self.settings=cfg()|dict(sample_count=7,size=2,partition_threshold=4,partition_size=4)
        self.input('synthetic_pair_contract',{'matching':self.matching,'dictionary':self.settings,
            'journal_limits':LIMITS,'seed':11,'max_entries':10000,
            'fixture_schedule':{'normal_operations':10000,'interruption_operations':1,'max_checkpoints':10}})
        super().prepare()
        self.bound=self.bind();self.bound.check()
        # Separate workflow root: a sibling under representation owners would
        # violate Binding's exact first-owner inventory.
        self.pair_root=self.root/'research_artifacts/synthetic_pair_workflows'/self.identity
        self.pair_root.mkdir(parents=True);(self.pair_root/'pairs').mkdir()
        self.pairs=journals.Journal(self.pair_root,'example-a',cache_key(thaw(self.bound.record)),self.identity,LIMITS)
        self.graph=graph([[i*.2] for i in range(7)],[(0,1,1),(2,1,.7),(3,4,.4),(5,6,.2)])
        self.samples=sample_neighborhoods([self.graph],self.settings,11)
        self.kw=dict(workflow=self.identity,backend=pair.BACKEND,max_entries=10000)
        self.asked=[];self.complete_keys=[];self.partial_key=None
        def score(p,a,b):
            self.asked.append(copy.deepcopy(p));key=cache_key(p)
            normal=consumer(self.bound,self.pairs,p['workload_sha256'],self.matching)
            phase=p['kind']
            interrupt=(phase==self.mode and len([q for q in self.asked if q['kind']==phase])==2)
            if interrupt:
                self.partial_key=key
                return consumer(self.bound,self.pairs,p['workload_sha256'],self.matching,
                    operations_per_checkpoint=1,max_checkpoints=1)(p,a,b)
            value=normal(p,a,b);self.complete_keys.append(key);return value
        try:
            self.dictionary=workload.fit(self.samples,self.matching,self.settings,score_pair=score,**self.kw)
            if self.mode in ('mcm','complete'):
                self.mcm=workload.mcm(self.graph,self.dictionary['dictionary'],self.matching,score_pair=score,**self.kw)
        except serial.CheckpointStop:
            if self.mode=='complete':raise
        else:
            if self.mode!='complete':raise AssertionError('interruption was not exercised')
        self.pair_terminal=self.pairs.seal('failed')
        self.pair_snapshot=snapshot(self.pair_root)


class Fixture(successor.SuccessorTests):
    __test__=False
    def input(self,name,value):
        # Pin the precise failed pair journal into the child registration before
        # ResearchRun.start. This is a real registered input; binding the route
        # to arbitrary journal owners remains production work, not fixture proof.
        terminal=self.parent.pair_terminal
        self.exp['inputs']['failed_pair_journal']={
            'path':str(Path(terminal['path']).relative_to(self.root)),
            'sha256':terminal['sha256'],'dataset':'sample'}
        super().input(name,value)


class Tests(unittest.TestCase):
    def setup_fixture(self,mode):
        class Selected(First):pass
        Selected.mode=mode
        fixture=Fixture('test_actual_successor_binds_new_claim_and_original_numerical_context')
        self.addCleanup(fixture.doCleanups)
        with patch.object(successor,'_FirstOwner',Selected):fixture.setUp()
        self.f=fixture;self.p=fixture.parent
        self.before=snapshot(self.p.directory)
        return fixture

    def open_pairs(self):
        f=self.f;p=self.p
        feature,bound=f.open();bound.check()
        self.assertNotEqual(bound.record['source_commit'],p.bound.record['source_commit'])
        self.assertEqual(thaw(bound.context),thaw(p.bound.context))
        info=f.run.admission.inputs['failed_pair_journal']
        ref={'path':str(f.root/info['path']),'sha256':info['sha256']}
        f.run.read_input('failed_pair_journal')
        child=journals.Journal(p.pair_root,'example-b',cache_key(thaw(bound.record)),p.identity,LIMITS,parent=ref)
        self.assertGreater(child.reserved_bytes,p.pairs.reserved_bytes)
        self.assertEqual(child.reservations,p.pairs.reservations)
        return feature,bound,child

    def oracle(self):
        from tradingagents.research.onchain_replication import dictionary as original
        matrices=[];real=original.cluster_medoids
        def capture(matrix,k):matrices.append(matrix.copy());return real(matrix,k)
        with patch.object(original,'cluster_medoids',capture):
            d=fit_dictionary(self.p.samples,self.p.matching,self.p.settings)
        return d,matrices

    def replay(self,bound,child,*,all_complete=False):
        p=self.p;asked=[];computed=[];resumed=[]
        def callback(purpose,a,b):
            key=cache_key(purpose);asked.append(copy.deepcopy(purpose))
            c=consumer(bound,child,purpose['workload_sha256'],p.matching)
            if key in p.complete_keys:
                old=child.reservations
                with (patch.object(pair.PairSession,'create',side_effect=AssertionError('completed create')),
                      patch.object(pair.PairSession,'resume',side_effect=AssertionError('completed resume'))):
                    value=c(purpose,a,b)
                self.assertEqual(child.reservations,old);return value
            self.assertFalse(all_complete,'completed replay requested an unpublished pair')
            if key==p.partial_key:
                with patch.object(pair.engine,'create',side_effect=AssertionError('progress restarted')):
                    value=c(purpose,a,b)
                resumed.append(key);return value
            computed.append(key);return c(purpose,a,b)
        d=workload.fit(p.samples,p.matching,p.settings,score_pair=callback,**p.kw)
        m=workload.mcm(p.graph,d['dictionary'],p.matching,score_pair=callback,**p.kw)
        return d,m,asked,computed,resumed

    def assert_preserved(self):
        self.assertEqual(self.before,snapshot(self.p.directory))
        for name,sha in self.p.pair_snapshot.items():
            self.assertEqual(file_hash(self.p.pair_root/name),sha)

    def test_partitioned_dictionary_failed_owner_resumes_exact_matrices_and_mcm(self):
        self.setup_fixture('dictionary');_,bound,child=self.open_pairs()
        d,m,asked,computed,resumed=self.replay(bound,child)
        oracle,matrices=self.oracle()
        self.assertTrue(d['dictionary'].hierarchy,'partitioned hierarchy was not exercised')
        self.assertEqual(d['dictionary'].hierarchy,oracle.hierarchy)
        self.assertEqual(d['dictionary'].memberships,oracle.memberships)
        self.assertEqual([g.center_id for g in d['dictionary'].representatives],[g.center_id for g in oracle.representatives])
        self.assertEqual(len(matrices),len(d['matrices']))
        for actual,expected in zip(d['matrices'],matrices,strict=True):np.testing.assert_array_equal(actual['matrix'],expected)
        self.assertEqual(asked[:2],self.p.asked)
        self.assertEqual(resumed,[self.p.partial_key])
        self.assertTrue(set(computed).isdisjoint(self.p.complete_keys))
        self.assertEqual(m.shape,(7,2));self.assertEqual(m.dtype,np.float32)
        self.assert_preserved()

    def test_mcm_partial_cell_resumes_with_exact_center_and_motif_order(self):
        self.setup_fixture('mcm');_,bound,child=self.open_pairs()
        d,m,asked,computed,resumed=self.replay(bound,child)
        self.assertEqual(d['dictionary'].identity,self.p.dictionary['dictionary'].identity)
        self.assertEqual(resumed,[self.p.partial_key])
        self.assertTrue(set(computed).isdisjoint(self.p.complete_keys))
        cells=[p for p in asked if p['kind']=='mcm']
        self.assertEqual([(p['center_index'],p['motif_index']) for p in cells],[(i,j) for i in range(7) for j in range(2)])
        from tradingagents.research.onchain_replication.neighborhoods import NeighborhoodIndex
        from tradingagents.research.onchain_replication.matching_reference import match_reference
        index=NeighborhoodIndex(self.p.graph)
        expected=np.asarray([[match_reference(index.neighborhood(i,self.p.settings),motif,self.p.matching).score
            for motif in d['dictionary'].representatives] for i in range(7)],dtype=np.float32)
        np.testing.assert_array_equal(m,expected);self.assert_preserved()

    def test_completed_dictionary_and_mcm_survive_failed_run_without_solver(self):
        self.setup_fixture('complete');_,bound,child=self.open_pairs();before=child.reservations
        d,m,asked,computed,resumed=self.replay(bound,child,all_complete=True)
        self.assertEqual(d['dictionary'].identity,self.p.dictionary['dictionary'].identity)
        self.assertEqual(asked,self.p.asked);self.assertFalse(computed);self.assertFalse(resumed)
        for a,b in zip(d['matrices'],self.p.dictionary['matrices'],strict=True):np.testing.assert_array_equal(a['matrix'],b['matrix'])
        np.testing.assert_array_equal(m,self.p.mcm)
        self.assertEqual(before,child.reservations);self.assert_preserved()

    def test_lost_current_guard_refuses_before_replay_or_reservation(self):
        self.setup_fixture('dictionary');_,bound,child=self.open_pairs()
        before=snapshot(self.p.pair_root)
        self.p.mock.side_effect=ValueError('synthetic expired current guard')
        with (patch.object(pair.PairSession,'create',side_effect=AssertionError('allocated')),
              patch.object(pair.PairSession,'resume',side_effect=AssertionError('resumed'))):
            with self.assertRaisesRegex(ValueError,'expired current guard'):self.replay(bound,child)
        self.assertEqual(before,snapshot(self.p.pair_root));self.assert_preserved()

    def test_parent_cgroup_becoming_live_refuses_before_replay_or_reservation(self):
        self.setup_fixture('dictionary');_,bound,child=self.open_pairs()
        before=snapshot(self.p.pair_root);self.f.mocks[3].return_value=True
        with (patch.object(pair.PairSession,'create',side_effect=AssertionError('allocated')),
              patch.object(pair.PairSession,'resume',side_effect=AssertionError('resumed'))):
            with self.assertRaises(ValueError):self.replay(bound,child)
        self.assertEqual(before,snapshot(self.p.pair_root));self.assert_preserved()

    def test_altered_registered_parent_reference_refused_before_pair_owner_creation(self):
        self.setup_fixture('dictionary')
        Path(self.p.pair_terminal['path']).write_text('{}')
        with self.assertRaises(ValueError):self.open_pairs()
        self.assertFalse((self.p.pair_root/'example-b').exists())


def load_tests(loader,tests,pattern):return loader.loadTestsFromTestCase(Tests)
if __name__=='__main__':unittest.main(verbosity=2)

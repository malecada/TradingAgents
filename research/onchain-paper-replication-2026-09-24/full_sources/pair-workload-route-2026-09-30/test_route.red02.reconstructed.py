"""Actual registered metadata/graph route; kernel guard alone is mocked."""
import copy
from dataclasses import replace, asdict
import importlib.util
import json
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from tests.research.onchain_replication import test_matching_owner as first
from tests.research.onchain_replication.test_feature_pipeline import population, configs
from tests.research.onchain_replication.test_matching_pair_checkpoints import POLICY
from tradingagents.research.onchain_replication import matching_pair as pair
from tradingagents.research.onchain_replication.neighborhoods import graph_hash, sample_neighborhoods
from tradingagents.research.onchain_replication.registered_features import representation_descriptor
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash, thaw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REL=str((HERE/'route.py').relative_to(ROOT))

def module():
    assert (HERE/'route.py').is_file(), 'registered workload route missing'
    spec=importlib.util.spec_from_file_location('candidate_route',HERE/'route.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result

class Fixture(first.OwnershipTests):
    __test__=False
    change=None
    def prepare(self):
        target=self.root/REL;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(HERE/'route.py',target);self.exp['source_files'][REL]=file_hash(target)
        first.git(self.root,'add','--',REL)
        self.graphs,self.fold,self.examples=population();self.configs=configs()
        self.configs['dictionary'].update(sample_count=3,size=2,partition_threshold=4,partition_size=4)
        self.policy['limits']=copy.deepcopy(POLICY);self.input('pair_policy',self.policy)
        self.control={'schema_version':1,'max_entries':10000,'operations_per_checkpoint':10000,
            'max_checkpoints':10,'journal_limits':{'max_reserved_bytes':100000000,'max_reservations':100,'max_events':200}}
        if self.change:self.change(self)
        self.input('pair_workload',self.control)
        self.descriptor=representation_descriptor(self.graphs,self.examples,self.fold,'proposed',11,self.configs)
        self.descriptor.update(pair_execution={'backend':pair.BACKEND,'policy_sha256':self.exp['inputs']['pair_policy']['sha256']},
            pair_workload={'input':'pair_workload','sha256':self.exp['inputs']['pair_workload']['sha256']})
        refs={}
        for i,g in enumerate(self.graphs):
            h=graph_hash(g);name='graph-'+str(i);self.input(name,{'graph_hash':h});refs[h]={'input':name}
        self.item.update(descriptor=self.descriptor,graphs=refs,pair_workload_input='pair_workload')
        self.execution['payload']['representation_jobs']['r'].update(descriptor=self.descriptor,pair_workload_input='pair_workload')
        self.input('plan',self.plan);self.input('execution_job',self.execution)
        super().prepare()

class Tests(unittest.TestCase):
    def fixture(self,change=None):
        self.m=module()
        class Selected(Fixture):pass
        Selected.change=staticmethod(change) if change else None
        f=Selected('test_actual_claim_owner_and_old_numerical_anchor_are_distinct')
        self.addCleanup(f.doCleanups);f.setUp();self.f=f
        return f
    def admit(self,**kw):
        f=self.f
        args=dict(representation='r',plan_input='plan',producer='p',policy_input='pair_policy',
            control_input='pair_workload',journal_directory=f.directory,
            graphs=f.graphs,examples=f.examples,fold=f.fold,seed=11,configs=f.configs)
        args.update(kw)
        return self.m.admit(f.run,**args)
    def test_real_graphs_and_registered_schedule_are_bound_without_pair_allocation(self):
        f=self.fixture()
        with patch.object(pair.PairSession,'create',side_effect=AssertionError('allocated')):
            route=self.admit()
        self.assertEqual(thaw(route.descriptor),f.descriptor)
        self.assertEqual(thaw(route.control),f.control)
        self.assertEqual(route.bound.record['source_commit'],f.source)
        self.assertEqual(route.record['control_sha256'],f.exp['inputs']['pair_workload']['sha256'])
        self.assertFalse((f.directory/'pairs').exists())
    def test_actual_graph_change_and_missing_population_refused(self):
        f=self.fixture()
        changed=replace(f.graphs[0],node_features=f.graphs[0].node_features+1)
        for graphs in ([changed,*f.graphs[1:]],f.graphs[1:]):
            with self.subTest(count=len(graphs)),self.assertRaises(ValueError):self.admit(graphs=graphs)
    def test_actual_seed_config_fold_and_train_rows_cannot_use_old_descriptor(self):
        f=self.fixture();config=copy.deepcopy(f.configs);config['matching']['max_iterations']+=1
        for changes in ({'seed':12},{'configs':config},{'fold':replace(f.fold,train_end='2023-12-01T00:00:00Z')},
            {'examples':replace(f.examples,train=f.examples.train[1:])}):
            with self.subTest(changes=list(changes)),self.assertRaises(ValueError):self.admit(**changes)
    def test_invalid_schedule_refuses_before_graph_iteration(self):
        for key,value in [('max_entries',True),('max_checkpoints',0),('operations_per_checkpoint',1.5),('schema_version',True)]:
            with self.subTest(key=key):
                f=self.fixture(lambda f:f.control.update({key:value}))
                def forbidden():raise AssertionError('graphs opened before metadata admission');yield
                with self.assertRaises(ValueError):self.admit(graphs=forbidden())
                f.doCleanups()
    def test_invalid_quota_refuses_before_graph_iteration(self):
        self.fixture(lambda f:f.control['journal_limits'].update(max_reserved_bytes=-1))
        def forbidden():raise AssertionError('graphs opened before metadata admission');yield
        with self.assertRaises(ValueError):self.admit(graphs=forbidden())
    def test_wrong_control_input_refused_before_graph_iteration(self):
        self.fixture()
        def forbidden():raise AssertionError('graphs opened before metadata admission');yield
        with self.assertRaises(ValueError):self.admit(control_input='sample',graphs=forbidden())
    def test_registered_control_drift_is_detected_by_route_lease(self):
        f=self.fixture();r=self.admit()
        (f.root/'pair_workload.json').write_text('{}')
        with self.assertRaises(ValueError):r.lease()
    def test_test_denominator_cannot_change_while_graph_union_stays_identical(self):
        f=self.fixture()
        for rows in (tuple(reversed(f.examples.test)),(*f.examples.test,f.examples.test[-1])):
            changed=replace(f.examples,test=rows,test_mask_hash=digest(canonical_bytes([r.decision_at for r in rows])))
            self.assertEqual({h for r in rows for h in r.graph_hashes},{h for r in f.examples.test for h in r.graph_hashes})
            with self.subTest(count=len(rows)),self.assertRaises(ValueError):self.admit(examples=changed)
    def test_hardlink_added_to_admitted_metadata_refuses_on_lease(self):
        f=self.fixture();r=self.admit()
        os.link(f.root/'pair_workload.json',f.root/'unadmitted-alias.json')
        with self.assertRaises(ValueError):r.lease()
    def test_route_source_must_be_an_exact_registered_source(self):
        f=self.fixture();(f.root/REL).write_text('# drift\n')
        with self.assertRaises(ValueError):self.admit()
    def test_sampling_scope_binds_training_membership_config_seed_and_order(self):
        f=self.fixture();r=self.admit()
        settings=f.configs['dictionary']|{'train_start':f.fold.train_start,'train_end':f.fold.train_end}
        samples=sample_neighborhoods(f.graphs,settings,11)
        result=r.sample_scope(samples)
        self.assertEqual(len(result),64)
        for bad in (replace(samples,seed=12),replace(samples,source_hashes=samples.source_hashes[:-1]),
                    replace(samples,graphs=tuple(reversed(samples.graphs))),replace(samples,identity='f'*64)):
            with self.subTest(identity=bad.identity),self.assertRaises(ValueError):r.sample_scope(bad)
        spec=importlib.util.spec_from_file_location('workload_route_oracle',HERE.parent/'pair-workload-2026-09-30/workload.py')
        w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
        seen=[]
        class Stop(Exception):pass
        def capture(p,a,b):seen.append(p);raise Stop
        with self.assertRaises(Stop):w.fit(samples,f.configs['matching'],settings,
            workflow=f.identity,backend=pair.BACKEND,max_entries=10000,score_pair=capture)
        self.assertEqual(result,seen[0]['workload_sha256'])
    def test_expired_guard_prevents_sample_acceptance(self):
        f=self.fixture();r=self.admit()
        settings=f.configs['dictionary']|{'train_start':f.fold.train_start,'train_end':f.fold.train_end}
        samples=sample_neighborhoods(f.graphs,settings,11)
        f.mock.side_effect=ValueError('expired guard')
        with self.assertRaises(ValueError):r.sample_scope(samples)
    def test_sample_feature_tamper_not_covered_by_sample_identity_is_refused(self):
        f=self.fixture();r=self.admit()
        settings=f.configs['dictionary']|{'train_start':f.fold.train_start,'train_end':f.fold.train_end}
        samples=sample_neighborhoods(f.graphs,settings,11)
        local=replace(samples.graphs[0],node_features=samples.graphs[0].node_features+123)
        changed=replace(samples,graphs=(local,*samples.graphs[1:]))
        self.assertEqual(changed.identity,samples.identity)
        with self.assertRaisesRegex(ValueError,'actual induced'):r.sample_scope(changed)

def load_tests(loader,tests,pattern):return loader.loadTestsFromTestCase(Tests)
if __name__=='__main__':unittest.main(verbosity=2)

"""Pure synthetic structural admission against scalar partitioned dictionaries."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from tests.research.onchain_replication.test_feature_pipeline import population,configs
from tradingagents.research.onchain_replication import dictionary as scalar
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.matching_pair import BACKEND
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.provenance import thaw

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dictionary_membership_candidate',HERE/'route.py')
route=importlib.util.module_from_spec(spec);spec.loader.exec_module(route)

class Tests(unittest.TestCase):
    def fixture(self,seed=11):
        graphs,fold,_=population();c=configs()
        settings=c['dictionary']|{'sample_count':13,'size':2,'partition_threshold':4,'partition_size':4,
            'train_start':fold.train_start,'train_end':fold.train_end}
        samples=sample_neighborhoods(graphs,settings,seed);matrices={};original=scalar.cluster_medoids
        def capture(matrix,k):matrices[id(matrix)]=matrix;return original(matrix,k)
        with patch.object(scalar,'cluster_medoids',side_effect=capture):d=scalar.fit_dictionary(samples,c['matching'],settings)
        d=replace(d,config=settings|{'pair_execution':BACKEND},matching_config_hash=cache_key({'config':c['matching'],'backend':BACKEND}))
        d=replace(d,identity=scalar.dictionary_hash(d))
        self.samples=samples;self.settings=settings;self.matching=c['matching'];self.d=d
        return sum(m.nbytes for m in matrices.values())
    def verify(self,d):return route.membership(d,self.samples,self.settings,self.matching,BACKEND)
    def test_partition_structure_and_exact_unique_matrix_bytes_across_five_seeds(self):
        for seed in (11,23,37,51,71):
            with self.subTest(seed=seed):
                expected=self.fixture(seed);self.assertEqual(len(self.d.hierarchy),6)
                with patch.object(scalar,'cluster_medoids',side_effect=AssertionError('clustering during admission')),patch.object(scalar,'match_reference',side_effect=AssertionError('matching during admission')):
                    self.assertEqual(self.verify(self.d),expected)
    def test_corrupt_partition_order_suffix_and_group_coverage_refuse(self):
        self.fixture();hierarchy=thaw(self.d.hierarchy)
        wrong_order=thaw(hierarchy);wrong_order[0]['samples']=list(reversed(wrong_order[0]['samples']))
        wrong_group=thaw(hierarchy);wrong_group[0]['original_memberships'][0].append(wrong_group[0]['original_memberships'][0][0])
        for changed in (wrong_order,wrong_group,hierarchy+[hierarchy[-1]],hierarchy[:-1]):
            with self.subTest(hierarchy=changed),self.assertRaises(ValueError):self.verify(replace(self.d,hierarchy=changed))
    def test_foreign_representative_and_reordered_final_owner_groups_refuse(self):
        self.fixture()
        foreign=replace(self.d.representatives[0],parent_hash='f'*64)
        for changed in (replace(self.d,representatives=(foreign,*self.d.representatives[1:])),
            replace(self.d,representatives=tuple(reversed(self.d.representatives))),
            replace(self.d,memberships=tuple(reversed(self.d.memberships))),replace(self.d,matching_config_hash='e'*64)):
            with self.subTest(identity=changed.matching_config_hash),self.assertRaises(ValueError):self.verify(changed)
    def test_final_groups_cannot_split_prior_owner_or_omit_samples(self):
        self.fixture();groups=thaw(self.d.memberships)
        typed=[route.graph_identity(g) for g in self.samples.graphs]
        centers={typed.index(route.graph_identity(g)) for g in self.d.representatives}
        candidates=[]
        for item in self.d.hierarchy[-2:]:
            for own in item['original_memberships']:
                if len(own)>1:
                    for value in own:
                        if value not in centers:candidates.append(value)
        self.assertTrue(candidates);value=candidates[0]
        source=next(i for i,g in enumerate(groups) if value in g);other=1-source
        omitted=thaw(groups);omitted[source].remove(value)
        split=thaw(omitted);split[other]=sorted([*split[other],value])
        duplicated=thaw(groups);duplicated[other]=sorted([*duplicated[other],value])
        for changed in (omitted,split,duplicated):
            with self.subTest(groups=changed),self.assertRaises(ValueError):self.verify(replace(self.d,memberships=changed))

if __name__=='__main__':unittest.main(verbosity=2)

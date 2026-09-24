from dataclasses import replace
import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.dictionary import fit_dictionary,reorder_dictionary
from tradingagents.research.onchain_replication.mcm import mcm_features


def test_mcm_reference_accelerated_and_dictionary_order():
    g=graph([[0],[1],[2],[3]],[(0,1,1),(2,1,2)])
    sample=sample_neighborhoods([g],cfg(),11)
    d=fit_dictionary(sample,config(),dict(size=2,partition_threshold=20,partition_size=10,hop_depth=1,maximum_neighborhood_nodes=20))
    a=mcm_features(g,d,config(),reference=True)
    fast=mcm_features(g,d,config())
    np.testing.assert_allclose(a,fast,atol=1e-5,rtol=1e-4)
    reordered=reorder_dictionary(d,list(reversed(range(len(d.representatives)))))
    np.testing.assert_allclose(mcm_features(g,reordered,config(),reference=True),a[:,::-1])

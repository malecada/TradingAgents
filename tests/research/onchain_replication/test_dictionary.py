import numpy as np
from tests.research.onchain_replication.test_matching_reference import graph,config
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods
from tradingagents.research.onchain_replication.dictionary import cluster_medoids,fit_dictionary


def test_average_linkage_and_medoid_ties():
    distance=np.array([[0,.1,.8,.9],[.1,0,.7,.8],[.8,.7,0,.2],[.9,.8,.2,0]])
    centers,members=cluster_medoids(distance,2)
    assert centers==[0,2] and members==[[0,1],[2,3]]

def test_dictionary_determinism():
    g=graph([[0],[1],[2],[3]],[(0,1,1),(2,1,2)])
    sample=sample_neighborhoods([g],cfg(),11)
    settings={'size':2,'partition_threshold':20,'partition_size':10,'hop_depth':1,'maximum_neighborhood_nodes':20}
    a=fit_dictionary(sample,config(),settings);b=fit_dictionary(sample,config(),settings)
    assert a.identity==b.identity and len(a.representatives)==2


def test_partition_ties_use_original_indices_and_expand_membership():
    from tradingagents.research.onchain_replication.neighborhoods import SampleManifest,neighborhood
    g=graph([[0]]*7,[])
    settings=cfg()|{'sample_count':7}
    samples=sample_neighborhoods([g],settings,11)
    d=fit_dictionary(samples,config(),dict(size=1,partition_threshold=3,partition_size=3,hop_depth=1,maximum_neighborhood_nodes=20))
    assert d.representatives[0].center_id==samples.graphs[0].center_id
    assert d.memberships==(tuple(range(7)),)


def test_dictionary_is_immutable_and_content_bound():
    import pytest
    from dataclasses import replace
    from tradingagents.research.onchain_replication.mcm import mcm_features
    g=graph([[0],[1],[2],[3]],[(0,1,1),(2,1,2)])
    sample=sample_neighborhoods([g],cfg(),11)
    d=fit_dictionary(sample,config(),dict(size=2,partition_threshold=20,partition_size=10,hop_depth=1,maximum_neighborhood_nodes=20))
    with pytest.raises(TypeError):d.config['hop_depth']=0
    with pytest.raises(TypeError):sample.records[0]['probability']=.9
    with pytest.raises(ValueError,match='dictionary identity'):mcm_features(g,replace(d,representatives=tuple(reversed(d.representatives))),config())

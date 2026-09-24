from dataclasses import replace
import numpy as np
import pytest
from tests.research.onchain_replication.test_matching_reference import graph
from tradingagents.research.onchain_replication.neighborhoods import neighborhood,sample_neighborhoods


def cfg():return dict(hop_depth=1,sample_count=3,maximum_neighborhood_nodes=20,train_start='2024-01-01T00:00:00Z',train_end='2024-02-01T00:00:00Z')

def test_weak_induced_neighborhood_and_hub_refusal():
    g=graph([[0],[1],[2],[3]],[(0,1,1),(2,1,2)])
    n=neighborhood(g,1,cfg())
    assert n.node_ids==('0','1','2') and n.edge_index.shape==(2,2)
    with pytest.raises(ValueError,match='capacity'):neighborhood(g,1,cfg()|{'maximum_neighborhood_nodes':2})

def test_overlap_probabilities_reproducible_and_future_invariant():
    g=graph([[0],[1],[2],[3]],[(0,1,1),(2,1,2)])
    future=replace(g,start_utc='2024-03-01T00:00:00Z',end_utc='2024-03-08T00:00:00Z',available_at='2024-03-09T00:00:00Z')
    a=sample_neighborhoods([g,future],cfg(),11)
    b=sample_neighborhoods([g,replace(future,node_features=np.full((4,1),99.))],cfg(),11)
    assert a.identity==b.identity
    selected=a.records[0]['center_index'];neighbors=set(a.graphs[0].node_ids)
    w=np.array([0 if i==selected else .5 if str(i) in neighbors else 1 for i in range(4)])
    assert a.records[0]['probability']==.25
    assert a.records[1]['probability']==pytest.approx(w[a.records[1]['center_index']]/w.sum())


def test_indexed_neighborhood_matches_original_directed_induction():
    from tradingagents.research.onchain_replication.neighborhoods import NeighborhoodIndex,neighborhood
    from tradingagents.research.onchain_replication.contracts import GraphSnapshot
    import numpy as np
    g=GraphSnapshot('ETH','2022-01-03T00:00:00Z','2022-01-10T00:00:00Z','2022-01-11T00:00:00Z',('a'*64,),'b'*64,('a','b','c','d'),np.arange(16).reshape(4,4),np.array([[2,0,1,3],[0,1,2,3]]),np.ones((4,2)),4,4,{})
    cfg={'hop_depth':1,'maximum_neighborhood_nodes':10}
    index=NeighborhoodIndex(g)
    for center in range(4):
        expected=neighborhood(g,center,cfg);actual=index.neighborhood(center,cfg)
        assert actual.node_ids==expected.node_ids
        np.testing.assert_array_equal(actual.edge_index,expected.edge_index)
        np.testing.assert_array_equal(actual.edge_features,expected.edge_features)

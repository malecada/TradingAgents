import numpy as np
import pytest
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.subsets import filter_graph


def fixture():
    # a->b100, c->d1; two giant wallets excluded, smaller independent edge survives.
    nodes=np.array([[0,1,0,100],[1,0,100,0],[0,1,0,1],[1,0,1,0.]])
    return GraphSnapshot('ETH','2024-01-01T00:00:00Z','2024-01-08T00:00:00Z','2024-01-09T00:00:00Z',('a'*64,),'b'*64,('a','b','c','d'),np.log1p(nodes),np.array([[0,2],[1,3]]),np.log1p([[1,100],[1,1]]),2,2,{},np.array([[1.,100.],[1.,1.]]))


def test_whales_removed_features_rebuilt_and_origin_counters_explicit():
    graph,receipt=filter_graph(fixture(),'whale')
    assert graph.node_ids==('c','d') and receipt['removed_edges']==1
    np.testing.assert_allclose(np.expm1(graph.node_features),[[0,1,0,1],[1,0,1,0]])
    assert graph.raw_count==2 and 'origin' in receipt['raw_event_counter_policy']


def test_fund_cohort_cannot_be_invented():
    with pytest.raises(ValueError,match='cohort'):filter_graph(fixture(),'fund')
    graph,receipt=filter_graph(fixture(),'fund',cohort={'c','d'},cohort_hash='c'*64)
    assert graph.node_ids==('c','d')


def test_whale_strict_boundary_uses_raw_aggregates():
    from dataclasses import replace
    g=fixture();raw=np.array([[1.,60.],[1.,54.]])
    nodes=np.array([[0,1,0,60],[1,0,60,0],[0,1,0,54],[1,0,54,0.]])
    g=replace(g,node_features=np.log1p(nodes),edge_features=np.log1p(raw),edge_aggregates=raw)
    result,_=filter_graph(g,'whale');assert result.node_ids==('c','d')


def test_induced_fund_graph_retains_isolated_selected_vertex():
    g,_=filter_graph(fixture(),'fund',cohort={'a'},cohort_hash='d'*64)
    assert g.node_ids==('a',) and g.edge_index.shape==(2,0)
    np.testing.assert_array_equal(g.node_features,np.zeros((1,4)))

from dataclasses import replace
import numpy as np
import pytest
from tradingagents.research.onchain_replication.contracts import GraphSnapshot, validate_graph, graph_from_dict


def graph(**changes):
    values = dict(asset='ETH',start_utc='2024-01-01T00:00:00Z',end_utc='2024-01-08T00:00:00Z',available_at='2024-01-09T00:00:00Z',source_hashes=('a'*64,),graph_config_hash='b'*64,node_ids=('a','b'),node_features=np.array([[1.,2.],[3.,4.]]),edge_index=np.array([[0],[1]]),edge_features=np.array([[1.,2.]]),raw_count=2,admitted_count=1,exclusion_counts={'zero':1})
    return GraphSnapshot(**(values|changes))


def test_valid_graph_and_no_mutable_alias():
    x=np.array([[1.,2.],[3.,4.]])
    g=graph(node_features=x)
    x[0,0]=90
    assert g.node_features[0,0]==1
    validate_graph(g)
    with pytest.raises(ValueError): g.node_features[0,0]=3


@pytest.mark.parametrize('changes',[
    {'node_ids':('a','a')}, {'node_features':np.array([[1.,2.]])},
    {'edge_index':np.array([[0],[2]])}, {'edge_index':np.array([[0.2],[1.]])},
    {'edge_features':np.array([[float('nan'),2.]])},
    {'edge_index':np.array([[0,0],[1,1]]),'edge_features':np.ones((2,2))},
    {'start_utc':'2024-01-01T00:00:00'}, {'available_at':'2024-01-02T00:00:00Z'},
    {'raw_count':3},{'admitted_count':-1},{'source_hashes':('bogus',)},
])
def test_invalid_graph_rejected(changes):
    with pytest.raises(ValueError): validate_graph(graph(**changes))


def test_unknown_fields_rejected():
    with pytest.raises(ValueError,match='unknown'):
        graph_from_dict({'unexpected':12})

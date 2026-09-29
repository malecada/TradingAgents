"""Complete induced neighborhoods under an explicit NumPy-buffer allowance."""
import importlib
import numpy as np
import pytest
from tests.research.onchain_replication.test_matching_reference import graph
from tradingagents.research.onchain_replication.neighborhoods import neighborhood


def index(g,**kw):
    module=importlib.import_module('tradingagents.research.onchain_replication.array_neighborhoods')
    return module.ArrayNeighborhoodIndex(g,max_buffer_bytes=kw.pop('max_buffer_bytes',16*1024**2),edge_chunk=kw.pop('edge_chunk',2),**kw)


def test_literal_directed_induction_preserves_source_order_and_isolate():
    g=graph([[0],[1],[2],[3],[4]],[(2,1,7),(0,1,8),(2,0,9),(3,3,10)])
    with index(g) as idx:
        local=idx.neighborhood(1,{'hop_depth':1,'maximum_neighborhood_nodes':5})
        assert local.node_ids==('0','1','2') and local.center_id=='1'
        np.testing.assert_array_equal(local.edge_index,[[2,0,2],[1,1,0]])
        np.testing.assert_array_equal(local.edge_features,[[7],[8],[9]])
        isolate=idx.neighborhood(4,{'hop_depth':2,'maximum_neighborhood_nodes':5})
        assert isolate.node_ids==('4',) and isolate.edge_index.shape==(2,0)
    np.testing.assert_array_equal(local.node_features,[[0],[1],[2]])
    assert not local.node_features.flags.writeable
    with pytest.raises(ValueError,match='closed'):idx.neighborhood(1,{'hop_depth':1,'maximum_neighborhood_nodes':5})


@pytest.mark.parametrize('hops',[0,1,2,3])
def test_all_centers_match_scalar_full_neighborhood(hops):
    g=graph(np.arange(18).reshape(6,3),[(4,1,2),(2,0,3),(1,2,4),(3,3,5),(0,4,6)])
    cfg={'hop_depth':hops,'maximum_neighborhood_nodes':6}
    with index(g,edge_chunk=1) as idx:
        for center in range(6):
            actual=idx.neighborhood(center,cfg);expected=neighborhood(g,center,cfg)
            assert actual.node_ids==expected.node_ids and actual.parent_hash==expected.parent_hash
            np.testing.assert_array_equal(actual.node_features,expected.node_features)
            np.testing.assert_array_equal(actual.edge_index,expected.edge_index)
            np.testing.assert_array_equal(actual.edge_features,expected.edge_features)


def test_complete_synthetic_hub_above_old_cap_and_refusal_without_truncation():
    n=10002;g=graph(np.zeros((n,1)),[(0,i,1) for i in range(1,n)])
    with index(g,edge_chunk=256) as idx:
        with pytest.raises(ValueError,match='capacity'):
            idx.neighborhood(0,{'hop_depth':1,'maximum_neighborhood_nodes':10000})
        full=idx.neighborhood(0,{'hop_depth':1,'maximum_neighborhood_nodes':n})
        assert full.node_ids==tuple(map(str,range(n)))
        np.testing.assert_array_equal(full.edge_index,g.edge_index)
        assert full.edge_features.shape==(n-1,1)


@pytest.mark.parametrize('budget',[True,0,-1,1.5,1])
def test_bad_or_insufficient_allowance_rejected_before_index_build(budget,monkeypatch):
    g=graph([[0],[1]],[(0,1,1)])
    monkeypatch.setattr(np,'argsort',lambda *a,**k:pytest.fail('allocated index before admission'))
    with pytest.raises(ValueError,match='buffer'):index(g,max_buffer_bytes=budget)


def test_output_admission_precedes_output_construction_and_failure_keeps_index_usable(monkeypatch):
    g=graph(np.zeros((12,40)),[(i,j,1) for i in range(12) for j in range(12) if i!=j])
    with index(g,edge_chunk=1) as idx:
        # The fixed allowance admits the index but not this complete output.
        limit=idx.buffer_allowance+2*g.node_features[0].nbytes
    with index(g,edge_chunk=1,max_buffer_bytes=limit) as idx:
        module=importlib.import_module('tradingagents.research.onchain_replication.array_neighborhoods')
        with monkeypatch.context() as patch:
            patch.setattr(module,'AttributedGraph',lambda *a:pytest.fail('over-budget output constructed'))
            with pytest.raises(ValueError,match='buffer'):
                idx.neighborhood(0,{'hop_depth':1,'maximum_neighborhood_nodes':12})
        single=idx.neighborhood(0,{'hop_depth':0,'maximum_neighborhood_nodes':1})
        assert single.node_ids==('0',) and single.edge_index.shape==(2,0)


@pytest.mark.parametrize('cfg',[{'hop_depth':True,'maximum_neighborhood_nodes':4},
    {'hop_depth':-1,'maximum_neighborhood_nodes':4},{'hop_depth':1,'maximum_neighborhood_nodes':False}])
def test_invalid_selection_contract_refused(cfg):
    with index(graph([[0],[1]],[(0,1,1)])) as idx:
        with pytest.raises(ValueError):idx.neighborhood(0,cfg)


def test_index_order_is_not_lexical_node_id_order():
    from dataclasses import replace
    g=replace(graph([[0],[1],[2]],[(2,0,4),(1,2,5),(0,0,6)]),node_ids=('z','a','m'))
    with index(g,edge_chunk=1) as idx:
        local=idx.neighborhood(0,{'hop_depth':2,'maximum_neighborhood_nodes':3})
        assert local.node_ids==('z','a','m') and local.center_id=='z'
        np.testing.assert_array_equal(local.edge_index,[[2,1,0],[0,2,0]])
        with pytest.raises(ValueError,match='capacity'):
            idx.neighborhood(0,{'hop_depth':2,'maximum_neighborhood_nodes':2})


def test_live_extraction_refuses_reentrant_use_or_close(monkeypatch):
    with index(graph([[0],[1]],[(0,1,1)])) as idx:
        original=idx._select
        def select(center,cfg):
            with pytest.raises(ValueError,match='busy'):idx.close()
            with pytest.raises(ValueError,match='busy'):idx.neighborhood(center,cfg)
            return original(center,cfg)
        monkeypatch.setattr(idx,'_select',select)
        local=idx.neighborhood(0,{'hop_depth':1,'maximum_neighborhood_nodes':2})
        assert local.node_ids==('0','1')


def test_mapped_input_returns_independent_output_after_both_owners_close(tmp_path):
    from tests.research.onchain_replication.test_mapped_graph import saved
    from tradingagents.research.onchain_replication.graph_store import open_mapped_graph
    from tradingagents.research.onchain_replication.provenance import file_hash
    g,path,size=saved(tmp_path);cfg={'hop_depth':1,'maximum_neighborhood_nodes':len(g.node_ids)}
    expected=neighborhood(g,0,cfg)
    with open_mapped_graph(path,file_hash(path),max_mapped_bytes=size) as mapped:
        with index(mapped) as idx:
            actual=idx.neighborhood(0,cfg)
        assert not mapped.node_features._mmap.closed
    assert actual.node_ids==expected.node_ids
    np.testing.assert_array_equal(actual.node_features,expected.node_features)
    np.testing.assert_array_equal(actual.edge_index,expected.edge_index)
    np.testing.assert_array_equal(actual.edge_features,expected.edge_features)


def test_selected_indices_survive_other_calls_and_close():
    with index(graph([[0],[1],[2]],[(0,2,1)])) as idx:
        selected=idx.selected(0,{'hop_depth':1,'maximum_neighborhood_nodes':3})
        np.testing.assert_array_equal(selected,[0,2])
        idx.neighborhood(1,{'hop_depth':1,'maximum_neighborhood_nodes':3})
    np.testing.assert_array_equal(selected,[0,2])


def test_partial_index_failure_drops_owned_arrays(monkeypatch):
    module=importlib.import_module('tradingagents.research.onchain_replication.array_neighborhoods')
    g=graph([[0],[1]],[(0,1,1)]);original=np.argsort;calls=0
    def broken(*a,**kw):
        nonlocal calls
        calls+=1
        if calls==2:raise RuntimeError('synthetic second direction failure')
        return original(*a,**kw)
    monkeypatch.setattr(np,'argsort',broken)
    obj=module.ArrayNeighborhoodIndex.__new__(module.ArrayNeighborhoodIndex)
    with pytest.raises(RuntimeError,match='second direction'):
        obj.__init__(g,max_buffer_bytes=1024**2,edge_chunk=1)
    assert obj.closed and obj.graph is None and obj.orders==[] and obj.offsets==[]

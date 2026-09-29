"""Exact duplicate validation without large Python identity/edge sets."""
from dataclasses import replace
import numpy as np
import pytest

from tests.research.onchain_replication.test_bounded_graph_hash import fixture
from tradingagents.research.onchain_replication.contracts import validate_graph


def test_valid_graph_does_not_allocate_python_identity_or_edge_sets(monkeypatch):
    from tradingagents.research.onchain_replication import contracts
    g=fixture(nodes=257,edges=66049)
    def forbidden(*args,**kwargs):
        raise AssertionError('whole graph Python set allocation')
    monkeypatch.setattr(contracts,'set',forbidden,raising=False)
    validate_graph(g)


@pytest.mark.parametrize('endpoint_dtype',[np.int32,np.int64,np.uint64])
@pytest.mark.parametrize('duplicate',[False,True])
def test_duplicate_check_matches_independent_pair_set(endpoint_dtype,duplicate):
    rng=np.random.Generator(np.random.PCG64(77))
    pairs=np.array([(a,b) for a in range(21) for b in range(21)],dtype=endpoint_dtype).T
    pairs=pairs[:,rng.permutation(pairs.shape[1])]
    if duplicate:pairs[:,17]=pairs[:,312]
    expected=len({(int(a),int(b)) for a,b in pairs.T})==pairs.shape[1]
    g=replace(fixture(nodes=21,edges=441),edge_index=pairs)
    if expected:validate_graph(g)
    else:
        with pytest.raises(ValueError,match='duplicate aggregated edges'):validate_graph(g)


def test_duplicate_at_large_sorted_comparison_boundary_is_not_missed():
    g=fixture(nodes=257,edges=66049)
    edges=g.edge_index.copy();edges[:,65536]=edges[:,65535]
    # Deliberately reverse the original order: equality must follow sorting.
    g=replace(g,edge_index=edges[:,::-1])
    with pytest.raises(ValueError,match='duplicate aggregated edges'):validate_graph(g)


def test_duplicate_unicode_node_identity_is_rejected():
    g=fixture(nodes=3,edges=2)
    g=replace(g,node_ids=('Č','quote"','Č'))
    with pytest.raises(ValueError,match='duplicate or invalid node identities'):validate_graph(g)

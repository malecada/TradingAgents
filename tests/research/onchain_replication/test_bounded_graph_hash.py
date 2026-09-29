"""Canonical graph identity parity and bounded serializer inputs, synthetic only."""
from dataclasses import replace
import hashlib
import numpy as np
import pytest

from tradingagents.research.onchain_replication.contracts import GraphSnapshot, graph_to_dict
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.provenance import canonical_bytes


def fixture(nodes=7,edges=12,width=4,asset='ETH'):
    indices=np.array([(i//nodes,i%nodes) for i in range(edges)],dtype=np.int64).reshape(-1,2).T
    features=np.resize(np.array([-0.,1e-300,-1e15,np.pi]),(nodes,width))
    aggregates=np.column_stack((np.ones(edges),np.arange(edges,dtype=float)/3))
    return GraphSnapshot(asset,'2024-01-01T00:00:00Z','2024-01-08T00:00:00Z',
        '2024-01-09T00:00:00Z',('a'*64,),'b'*64,
        tuple(f'node-Č-"-\\-\n-{i}' for i in range(nodes)),features,indices,
        np.log1p(aggregates),edges,edges,{},aggregates)


@pytest.mark.parametrize('asset',['ETH','BTC'])
@pytest.mark.parametrize('shape',[(0,0,4),(7,12,4),(4097,0,4),(100,3000,4),(2,1,4097)])
def test_hash_keeps_complete_legacy_canonical_identity(asset,shape):
    g=fixture(*shape,asset=asset)
    expected=hashlib.sha256(canonical_bytes(graph_to_dict(g))).hexdigest()
    assert graph_hash(g)==expected
    changed=replace(g,available_at='2024-01-10T00:00:00Z')
    assert graph_hash(changed)!=expected


@pytest.mark.parametrize('shape',[(4097,0,4),(100,3000,4),(2,1,4097)])
def test_serializer_never_receives_a_whole_large_row_or_identity_list(monkeypatch,shape):
    from tradingagents.research.onchain_replication import provenance
    g=fixture(*shape)
    expected=hashlib.sha256(canonical_bytes(graph_to_dict(g))).hexdigest()
    calls=[]
    def bounded(value):
        if isinstance(value,(list,tuple)):
            calls.append(len(value))
            assert len(value)<=1024, 'whole large graph row/list reached serializer'
        return canonical_bytes(value)
    monkeypatch.setattr(provenance,'canonical_bytes',bounded)
    assert graph_hash(g)==expected
    assert calls


def test_hash_still_rejects_duplicate_aggregated_edges():
    g=fixture(nodes=3,edges=2)
    g=replace(g,edge_index=np.array([[0,0],[1,1]],dtype=np.int64))
    with pytest.raises(ValueError,match='duplicate aggregated edges'):
        graph_hash(g)

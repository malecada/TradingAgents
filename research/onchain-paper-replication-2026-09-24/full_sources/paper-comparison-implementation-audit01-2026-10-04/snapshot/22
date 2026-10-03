from dataclasses import replace
from fractions import Fraction
import numpy as np
import pytest
from tests.research.onchain_replication.test_btc_weekly import event,CONFIG,COVERAGE
from tradingagents.research.onchain_replication.btc_weekly import build_btc_weekly
from tradingagents.research.onchain_replication.btc_subsets import filter_btc_graph
from tradingagents.research.onchain_replication.btc_store import save_btc_graph,load_btc_graph
from tradingagents.research.onchain_replication.provenance import file_hash


def test_whale_selection_uses_bound_exact_sidecar_and_preserves_isolates(tmp_path):
    value=list(build_btc_weekly([event()],CONFIG,coverage=COVERAGE,scratch=tmp_path))[0]
    result,receipt=filter_btc_graph(value,'whale')
    expected=tuple(n for n,v in zip(value.graph.node_ids,value.incident_satoshis) if v<=Fraction(9,10)*max(value.incident_satoshis))
    assert result.graph.node_ids==expected
    assert result.fee_satoshis==value.fee_satoshis and receipt['schema_version']==3
    path=save_btc_graph(tmp_path/'subset',result)
    assert load_btc_graph(path,file_hash(path)).incident_satoshis==result.incident_satoshis
    with pytest.raises(ValueError,match='incident'):
        filter_btc_graph(replace(value,incident_satoshis=(Fraction(0),)*len(value.graph.node_ids)),'whale')


def test_fund_rebuilds_exact_retained_edges_and_rejects_rounded_node_features(tmp_path):
    value=list(build_btc_weekly([event()],CONFIG,coverage=COVERAGE,scratch=tmp_path))[0]
    result,receipt=filter_btc_graph(value,'fund',cohort=value.graph.node_ids,cohort_hash='b'*64)
    assert result.edge_satoshis==value.edge_satoshis
    np.testing.assert_array_equal(result.graph.node_features,value.graph.node_features)
    assert receipt['exact_parent_hash']
    bad=replace(value,graph=replace(value.graph,node_features=value.graph.node_features+1e-10))
    with pytest.raises(ValueError,match='node features'):filter_btc_graph(bad,'fund',cohort=value.graph.node_ids,cohort_hash='b'*64)

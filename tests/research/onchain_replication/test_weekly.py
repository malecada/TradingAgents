from datetime import datetime,timezone
import numpy as np
import pytest
from tradingagents.research.onchain_replication.contracts import Transaction
from tradingagents.research.onchain_replication.weekly import build_weekly,week_start

A='0x'+'a'*40;B='0x'+'b'*40

def tx(i,s=A,t=B,value=1.,status=1,at='2024-01-02T00:00:00Z'):
    return Transaction('ETH',f'{i:064x}',at,s,t,value,status,'a'*64,'approximate_ETH')

def config():
    import json
    from pathlib import Path
    return json.loads((Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/graph.json').read_text())

def test_monday_utc_boundary():
    assert week_start('2024-01-07T23:59:59Z','MON')=='2024-01-01T00:00:00Z'
    assert week_start('2024-01-08T00:00:00Z','MON')=='2024-01-08T00:00:00Z'
    assert week_start('2023-01-01T00:00:00Z','MON')=='2022-12-26T00:00:00Z'

def test_conservation_and_attributes(tmp_path):
    events=[tx(1,value=3),tx(2,value=2),tx(3,t=A,value=1),tx(4,t=None),tx(5,status=0),tx(6,value=0)]
    graphs=list(build_weekly(events,config(),coverage=[('2024-01-01T00:00:00Z','2024-01-08T00:00:00Z')],scratch=tmp_path))
    assert len(graphs)==1
    g=graphs[0]
    assert (g.raw_count,g.admitted_count)==(6,3)
    assert dict(g.exclusion_counts)=={'failed':1,'null_recipient':1,'zero_value':1}
    assert g.node_ids==(A,B)
    np.testing.assert_allclose(np.expm1(g.edge_features),[[1,1],[2,5]])
    np.testing.assert_allclose(np.expm1(g.node_features),[[1,3,1,6],[2,0,5,0]])
    assert g.available_at=='2024-01-09T00:00:00Z'

def test_duplicates_even_excluded_fail(tmp_path):
    with pytest.raises(ValueError,match='duplicate'):
        list(build_weekly([tx(1,value=0),tx(1,value=0)],config(),coverage=[('2024-01-01T00:00:00Z','2024-01-08T00:00:00Z')],scratch=tmp_path))

def test_partial_week_requires_explicit_disposition(tmp_path):
    with pytest.raises(ValueError,match='complete week'):
        list(build_weekly([tx(1)],config(),coverage=[('2024-01-02T00:00:00Z','2024-01-08T00:00:00Z')],scratch=tmp_path))

"""Synthetic source boundaries and retained failure state; no historical inputs."""
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

from tests.research.onchain_replication.test_weekly import tx, config
from tests.research.onchain_replication.test_btc_weekly import event
from tradingagents.research.onchain_replication.weekly import build_weekly
from tradingagents.research.onchain_replication.btc_weekly import build_btc_weekly

COVERAGE=[('2024-01-01T00:00:00Z','2024-01-15T00:00:00Z')]


def api():
    assert importlib.util.find_spec('tradingagents.research.onchain_replication.aggregation'), 'durable aggregation missing'
    from tradingagents.research.onchain_replication.aggregation import SourceBoundary
    return SourceBoundary


@pytest.mark.parametrize('asset',['ETH','BTC'])
def test_failed_decoder_retains_only_committed_source_boundary_and_refuses_reopen(tmp_path,asset):
    Boundary=api();directory=tmp_path/'owned'
    first=tx(1) if asset=='ETH' else event()
    source=first.source_hash if asset=='ETH' else first['source_hash']
    def stream():
        yield first
        yield Boundary(source,1)
        yield tx(2) if asset=='ETH' else event('c',previous='d')
        raise ValueError('synthetic truncated member')
    builder=build_weekly if asset=='ETH' else build_btc_weekly
    with pytest.raises(ValueError,match='truncated member'):
        list(builder(stream(),config(),coverage=COVERAGE,scratch=tmp_path,workspace=directory))
    with sqlite3.connect(directory/'ledger.sqlite') as db:
        table='events' if asset=='ETH' else 'transactions'
        assert db.execute('SELECT count(*) FROM '+table).fetchone()[0]==1
        assert db.execute('SELECT count(*) FROM source_checkpoints').fetchone()[0]==1
    assert json.loads((directory/'failed.json').read_text())['status']=='failed'
    saved={p.name:p.read_bytes() for p in directory.iterdir() if p.is_file()}
    with pytest.raises(FileExistsError):
        list(builder([],config(),coverage=COVERAGE,scratch=tmp_path,workspace=directory))
    assert saved=={p.name:p.read_bytes() for p in directory.iterdir() if p.is_file()}


@pytest.mark.parametrize('asset',['ETH','BTC'])
def test_cross_week_duplicate_remains_rejected_after_committed_boundary(tmp_path,asset):
    Boundary=api()
    first=tx(1) if asset=='ETH' else event()
    second=tx(1,at='2024-01-08T00:00:00Z') if asset=='ETH' else event('c',day='08')
    source=first.source_hash if asset=='ETH' else first['source_hash']
    builder=build_weekly if asset=='ETH' else build_btc_weekly
    with pytest.raises(ValueError,match='duplicate'):
        list(builder([first,Boundary(source,1),second],config(),coverage=COVERAGE,scratch=tmp_path,workspace=tmp_path/'owned'))
    assert not (tmp_path/'owned/complete.json').exists()


def test_boundary_wrong_count_cannot_commit_and_success_preserves_graph_semantics(tmp_path):
    Boundary=api()
    with pytest.raises(ValueError,match='boundary'):
        list(build_weekly([tx(1),Boundary('a'*64,2)],config(),coverage=COVERAGE[:1],scratch=tmp_path,workspace=tmp_path/'bad'))
    coverage=[('2024-01-01T00:00:00Z','2024-01-08T00:00:00Z')]
    graph=list(build_weekly([tx(1,value=3),tx(2,value=2),Boundary('a'*64,2)],config(),coverage=coverage,scratch=tmp_path,workspace=tmp_path/'good'))[0]
    assert (graph.raw_count,graph.admitted_count)==(2,2)
    assert graph.edge_aggregates.tolist()==[[2.,5.]]
    receipt=json.loads((tmp_path/'good/complete.json').read_text())
    assert receipt['status']=='complete' and receipt['rows']==2 and receipt['source_boundaries']==1
    assert (tmp_path/'good/ledger.sqlite').exists()


def test_closed_generator_retains_scratch_but_does_not_claim_completion(tmp_path):
    api()
    graphs=build_weekly([tx(1)],config(),coverage=[('2024-01-01T00:00:00Z','2024-01-08T00:00:00Z')],scratch=tmp_path,workspace=tmp_path/'owned')
    next(graphs);graphs.close()
    assert (tmp_path/'owned/failed.json').exists()
    assert not (tmp_path/'owned/complete.json').exists()

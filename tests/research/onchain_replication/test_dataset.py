from datetime import datetime,timedelta,timezone
import numpy as np
import pytest
from tradingagents.research.onchain_replication.calendar import eligible,build_folds
from tradingagents.research.onchain_replication.dataset import build_examples,fit_scaler
from tradingagents.research.onchain_replication.contracts import GraphSnapshot,PricePanel

H='a'*64

def fixture():
    start=datetime(2022,1,1,tzinfo=timezone.utc)
    dates=tuple((start+timedelta(days=i)).date().isoformat() for i in range(820))
    prices=PricePanel('ETH-USD',dates,tuple(100.+i%31 for i in range(820)),(),H,'2026-01-01T00:00:00Z')
    graphs=[];week=datetime(2022,1,3,tzinfo=timezone.utc)
    while week<datetime(2024,4,1,tzinfo=timezone.utc):
        stamp=lambda d:d.isoformat()
        graphs.append(GraphSnapshot('ETH',stamp(week),stamp(week+timedelta(days=7)),stamp(week+timedelta(days=8)),(H,),H,('a','b'),np.ones((2,4)),np.array([[0],[1]]),np.ones((1,2)),1,1,{}))
        week+=timedelta(days=7)
    config={'lookback_days':28,'folds':[{'id':'2024','train_start':'2022-01-01T00:00:00Z','train_end':'2024-01-01T00:00:00Z','test_start':'2024-01-01T00:00:00Z','test_end':'2025-01-01T00:00:00Z','validation_start':None,'validation_end':None}]}
    fold=build_folds(config,{'source_hashes':[H]})[0]
    return graphs,prices,fold,config


def test_clocks_leap_purge_and_unique_scaler_population():
    assert not eligible('2024-01-08T00:00:00Z','2024-01-04T00:00:00Z')
    assert eligible('2024-01-08T00:00:00Z','2024-01-08T00:00:00Z')
    graphs,prices,fold,config=fixture();examples=build_examples(graphs,prices,fold,config)
    assert any(x.decision_at.startswith('2024-02-29') for x in examples.test)
    assert all(x.label_end<fold.test_start for x in examples.train)
    assert all(x.max_input_available_at<=x.decision_at for x in (*examples.train,*examples.test))
    assert any(x['reason']=='warmup_or_missing_price' for x in examples.exclusions)
    scaler=fit_scaler(examples,prices,fold)
    lookup=dict(zip(prices.dates,prices.closes))
    assert scaler.mean==np.mean([lookup[d] for d in scaler.dates])
    changed=PricePanel(prices.symbol,prices.dates,tuple(v if d<'2024-01-01' else v*99 for d,v in zip(prices.dates,prices.closes)),(),H,prices.retrieved_at)
    second=build_examples(graphs,changed,fold,config)
    assert examples.train_hash==second.train_hash
    assert scaler==fit_scaler(second,changed,fold)


def test_missing_week_never_fills_from_older_week():
    graphs,prices,fold,config=fixture();full=build_examples(graphs,prices,fold,config)
    cut=build_examples([g for g in graphs if not g.start_utc.startswith('2024-01-01')],prices,fold,config)
    assert len(cut.test)<len(full.test)
    assert any(x['reason']=='missing_expected_graph' for x in cut.exclusions)
    assert cut.test_mask_hash!=full.test_mask_hash
    with pytest.raises(ValueError,match='mask'):cut.require_test_mask(full.test_mask_hash)

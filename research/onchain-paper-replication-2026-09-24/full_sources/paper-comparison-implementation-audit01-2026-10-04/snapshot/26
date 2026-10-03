import numpy as np
import pytest
import torch
from tradingagents.research.onchain_replication.metrics import classification_metrics,regression_metrics,paired_block_interval
from tradingagents.research.onchain_replication.baselines import PriceRecurrent,HierarchicalLSTM,price_svm,training_controls


def test_metrics_hand_calculation_and_probability_limits():
    m=classification_metrics([1,1,0,0],[.9,.2,.8,.1])
    assert m['accuracy']==.5 and m['precision_up']==.5 and m['recall_up']==.5 and m['f1_up']==.5
    assert m['brier']==pytest.approx(.325)
    r=regression_metrics([10,20],[12,18]);assert r==pytest.approx({'MAE':2.,'MSE':4.,'RMSE':2.,'MAPE_percent':15.})
    with pytest.raises(ValueError):classification_metrics([1],[1.1])
    with pytest.raises(ValueError):regression_metrics([0],[1])


def test_interval_rejects_gaps_and_preserves_pairing():
    dates=np.arange('2024-01-01','2024-03-01',dtype='datetime64[D]').astype(str).tolist()
    assert paired_block_interval(dates,np.ones(len(dates)),np.zeros(len(dates)),replicates=20)==(1.,1.)
    with pytest.raises(ValueError,match='gap'):paired_block_interval(dates[::2],np.ones(30),np.zeros(30),replicates=20)


@pytest.mark.parametrize('kind',['lstm','gru','hlstm'])
def test_price_models_have_distinct_joint_trainable_structure(kind):
    model=HierarchicalLSTM('classification') if kind=='hlstm' else PriceRecurrent(kind,'classification')
    x=torch.linspace(0,1,56).reshape(2,28,1);out=model(x)
    assert out.shape==(2,2);out.square().sum().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    if kind=='hlstm':assert model.lower is not model.upper


def test_svm_contract_and_zero_fit_controls():
    estimator=price_svm('regression');assert estimator.C==1 and estimator.epsilon==.1 and estimator.kernel=='rbf'
    assert not price_svm('classification').probability
    result=training_controls([0,1,1],[[1,2],[2,2]])
    assert result['training_majority']==[2/3,2/3] and result['last_direction']==[1.,0.]

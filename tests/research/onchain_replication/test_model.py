import json
from pathlib import Path
import torch
from tradingagents.research.onchain_replication.model import ReplicationModel


def cfg():return json.loads((Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/model.json').read_text())

def test_joint_gradient_and_structure_time_learning():
    torch.set_num_threads(2);torch.manual_seed(314159)
    model=ReplicationModel(cfg(),'classification')
    mcm=torch.zeros(3,32);mcm[0,0]=1;mcm[1,1]=2;mcm[2,2]=3
    a={'mcm':mcm,'edge_index':torch.tensor([[0,0],[1,2]])}
    b={'mcm':mcm,'edge_index':torch.tensor([[1,2],[0,0]])}
    graphs=[[a,b],[b,a],[a,a],[b,b]]
    prices=torch.zeros(4,2,1);labels=torch.tensor([0,1,0,1])
    optimizer=torch.optim.Adam(model.parameters(),lr=.01)
    initial=float(torch.nn.functional.cross_entropy(model(graphs,prices),labels).detach())
    loss=torch.nn.functional.cross_entropy(model(graphs,prices),labels);loss.backward()
    for name,parameters in model.parameter_groups().items():
        grads=[p.grad for p in parameters if p.requires_grad]
        assert grads and all(g is not None and torch.isfinite(g).all() for g in grads),name
        assert sum(float(g.abs().sum()) for g in grads)>0,name
    for _ in range(500):
        optimizer.zero_grad();loss=torch.nn.functional.cross_entropy(model(graphs,prices),labels);loss.backward();optimizer.step()
        if float(loss.detach())<=.15*initial:break
    assert float(torch.nn.functional.cross_entropy(model(graphs,prices),labels).detach())<=.2*initial


def test_regression_head_is_distinct():
    model=ReplicationModel(cfg(),'regression')
    assert model.temporal.output.out_features==1


def test_masked_nan_padding_has_finite_gradients():
    from tradingagents.research.onchain_replication.model import GraphEncoder
    encoder=GraphEncoder(cfg())
    x=torch.randn(3,32);x[2]=float('nan')
    encoder(x,torch.tensor([[0],[1]]),torch.tensor([True,True,False])).sum().backward()
    assert all(torch.isfinite(p.grad).all() for p in encoder.parameters() if p.grad is not None)


def test_pool_rejects_wholly_masked_graph():
    import pytest
    from tradingagents.research.onchain_replication.pooling import mean_pool
    with pytest.raises(ValueError,match='empty'):
        mean_pool(torch.ones(4,2),torch.tensor([True,True,False,False]),torch.tensor([0,0,1,1]))

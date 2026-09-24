import json
from pathlib import Path
import numpy as np
import pytest
import torch
from scipy.linalg import expm
from tradingagents.research.onchain_replication.graph_baselines import graphwave,align_embeddings,walks,GINEncoder,watchyourstep_objective


def test_graphwave_against_dense_three_node_oracle():
    edges=np.array([[0,1],[1,2]]);cfg={'scales':[.1,1.,10.],'evaluation_points':[0.,.5,1.,1.5,2.]}
    got=graphwave(edges,3,cfg,max_entries=10000)
    lap=np.array([[1,-1,0],[-1,2,-1],[0,-1,1.]])
    expected=[]
    for node in range(3):
        values=[]
        for scale in cfg['scales']:
            heat=expm(-scale*lap)[:,node]
            for t in cfg['evaluation_points']:
                z=np.exp(1j*t*heat).mean();values.extend([z.real,z.imag])
        expected.append(values)
    np.testing.assert_allclose(got,expected,atol=1e-7)


def test_historical_alignment_and_walk_reproducibility():
    previous=np.eye(2);current=np.array([[0.,-1.],[1.,0.]])
    np.testing.assert_allclose(align_embeddings(('a','b'),current,('a','b'),previous),previous,atol=1e-8)
    with pytest.raises(ValueError,match='anchor'):align_embeddings(('c','d'),current,('a','b'),previous)
    kwargs=dict(walk_length=4,walks_per_node=2,seed=11)
    a=list(walks(np.array([[0],[1]]),3,**kwargs));assert a==list(walks(np.array([[0],[1]]),3,**kwargs))
    assert all(w==[2] for w in a if w[0]==2)


def test_watchyourstep_objective_matches_scalar_and_gin_gradients():
    left=torch.tensor([[.1,.2],[.3,.4]],requires_grad=True);right=torch.tensor([[.2,.1],[.4,.3]],requires_grad=True);q=torch.zeros(2,requires_grad=True)
    powers=torch.tensor([[[0.,1.],[1.,0.]],[[1.,0.],[0.,1.]]]);adj=torch.tensor([[0.,1.],[1.,0.]])
    loss=watchyourstep_objective(left,right,q,powers,adj,10.,.01)
    expected=0.
    scores=(left@right.T).detach().numpy()
    for i in range(2):
        for j in range(2):expected+=5*np.logaddexp(0,-scores[i,j])+(1-float(adj[i,j]))*np.logaddexp(0,scores[i,j])
    assert float(loss.detach())==pytest.approx(expected);loss.backward();assert q.grad is not None
    model=GINEncoder();out=model(torch.randn(3,4),torch.tensor([[0,1,2],[1,2,2]]));assert out.shape==(32,)
    out.sum().backward();assert all(p.grad is not None for p in model.parameters())


def test_node2vec_mid_epoch_recovery_matches_uninterrupted():
    from copy import deepcopy
    from tradingagents.research.onchain_replication.graph_baselines import node2vec
    root=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/baselines.json'
    cfg=json.loads(root.read_bytes())['graph']['node2vec'];cfg={**cfg,'epochs':2,'walks_per_node':2,'walk_length':5,'batch_size':8}
    edges=np.array([[0,1,2],[1,2,0]]);gold,logs=node2vec(edges,3,cfg,11,max_entries=10000)
    saved=[]
    def interrupt(epoch,state):
        saved.append(deepcopy(state));raise RuntimeError('synthetic stop')
    with pytest.raises(RuntimeError,match='synthetic stop'):node2vec(edges,3,cfg,11,max_entries=10000,checkpoint=interrupt,checkpoint_seconds=1e-9)
    result,replayed=node2vec(edges,3,cfg,11,max_entries=10000,resume_state=saved[0])
    np.testing.assert_array_equal(result,gold);assert replayed==logs


def test_wys_partial_gradient_checkpoint_and_graphwave_replay():
    from copy import deepcopy
    from tradingagents.research.onchain_replication.graph_baselines import watchyourstep
    root=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/baselines.json'
    cfg={**json.loads(root.read_bytes())['graph']['watchyourstep'],'epochs':2};edges=np.array([[0,1,2],[1,2,0]])
    # 4 nodes, limit160 =>4rowpowers; choose140 =>3rowblocks +1.
    gold,logs=watchyourstep(edges,4,cfg,11,max_entries=140)
    saved=[]
    def interrupt(cursor,state):saved.append(deepcopy(state));raise RuntimeError('synthetic stop')
    with pytest.raises(RuntimeError):watchyourstep(edges,4,cfg,11,max_entries=140,checkpoint=interrupt,checkpoint_seconds=1e-9)
    replay,relogs=watchyourstep(edges,4,cfg,11,max_entries=140,resume_state=saved[0]);np.testing.assert_array_equal(gold,replay);assert logs==relogs
    wave={'scales':[.1,1.,10.],'evaluation_points':[0.,.5,1.,1.5,2.]};saved.clear()
    expected=graphwave(edges,4,wave,max_entries=140)
    with pytest.raises(RuntimeError):graphwave(edges,4,wave,max_entries=140,checkpoint=interrupt,checkpoint_seconds=1e-9)
    np.testing.assert_array_equal(expected,graphwave(edges,4,wave,max_entries=140,resume_state=saved[0]))

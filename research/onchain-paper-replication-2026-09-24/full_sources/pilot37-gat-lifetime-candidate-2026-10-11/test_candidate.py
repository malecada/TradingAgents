"""Staged synthetic parity tests. NOT RUN during native36/source freeze.

Uses actual unchanged source as comparator; candidate loaded only from this
uninstalled evidence directory. No research lifecycle, labels or data reads.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import torch

from tradingagents.research.onchain_replication import streamed_gat as original
from tradingagents.research.onchain_replication.model import ReplicationModel

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PIN='e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f'


@pytest.fixture(scope='module')
def candidate():
    # Refuse silently comparing against another current implementation.
    assert hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest()==PIN
    record=json.loads((HERE/'PREPARATION01.json').read_text())
    path=HERE/'streamed_gat_candidate.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==record['candidate_sha256']
    spec=importlib.util.spec_from_file_location('staged_streamed_gat_lifetime',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def close(a,b,dtype):
    # Frozen criteria: C05 float64; C06 applicable float32. No widening.
    atol,rtol=(1e-8,1e-6) if dtype==torch.float64 else (1e-5,1e-4)
    torch.testing.assert_close(a,b,atol=atol,rtol=rtol)


def optimizer_state_equal(a,b,dtype):
    if isinstance(a,torch.Tensor):
        assert isinstance(b,torch.Tensor) and a.dtype==b.dtype and a.shape==b.shape
        close(a,b,dtype)
    elif isinstance(a,dict):
        assert a.keys()==b.keys()
        for key in a:optimizer_state_equal(a[key],b[key],dtype)
    elif isinstance(a,(tuple,list)):
        assert type(a) is type(b) and len(a)==len(b)
        for x,y in zip(a,b,strict=True):optimizer_state_equal(x,y,dtype)
    else:assert a==b


def edge_case(kind):
    if kind=='empty':return torch.empty((2,0),dtype=torch.long),None
    edge=torch.tensor([[0,1,2,3,3,4,6,7],[1,2,0,3,5,6,7,6]],dtype=torch.long)
    mask=torch.tensor([True,True,True,True,False,True,True,False]) if kind=='masked' else None
    return edge,mask


@pytest.mark.parametrize('dtype',[torch.float32,torch.float64])
@pytest.mark.parametrize('dropout',[0.,.25])
@pytest.mark.parametrize('kind',['empty','directed','masked'])
def test_layer_forward_first_gradients_adam_and_rng(candidate,dtype,dropout,kind):
    torch.manual_seed(17)
    left=original.GraphAttention(5,3,2,dropout=dropout,block_edges=3).to(dtype=dtype)
    right=candidate.GraphAttention(5,3,2,dropout=dropout,block_edges=3).to(dtype=dtype)
    right.load_state_dict(left.state_dict())
    x=torch.randn(8,5,dtype=dtype);edges,mask=edge_case(kind)
    results=[]
    for layer in (left,right):
        features=x.clone().requires_grad_(True)
        optimizer=torch.optim.Adam(layer.parameters(),lr=.001)
        torch.manual_seed(29);before=torch.get_rng_state().clone()
        output=layer(features,edges,mask)
        after_forward=torch.get_rng_state().clone()
        loss=output.square().mean()+.123*output.mean()
        loss.backward()
        grads={name:p.grad.detach().clone() for name,p in layer.named_parameters()}
        input_grad=features.grad.detach().clone()
        after_backward=torch.get_rng_state().clone()
        optimizer.step()
        results.append(dict(output=output.detach(),grad=grads,input_grad=input_grad,
            model={k:v.detach().clone() for k,v in layer.state_dict().items()},
            optimizer=optimizer.state_dict(),rng=(before,after_forward,after_backward)))
    a,b=results
    for name in ('output','input_grad'):close(a[name],b[name],dtype)
    for category in ('grad','model'):
        assert a[category].keys()==b[category].keys()
        for key in a[category]:close(a[category][key],b[category][key],dtype)
    optimizer_state_equal(a['optimizer'],b['optimizer'],dtype)
    for x,y in zip(a['rng'],b['rng'],strict=True):assert torch.equal(x,y)


@pytest.mark.parametrize('dtype',[torch.float32,torch.float64])
@pytest.mark.parametrize('checkpointed',[False,True])
def test_genuine_model_repeated_graph_joint_update(candidate,dtype,checkpointed):
    # Original scientific architecture/config, synthetic3-step two-example batch.
    config_path=ROOT/'research/onchain-paper-replication-2026-09-24/config/model.json'
    assert hashlib.sha256(config_path.read_bytes()).hexdigest()=='20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d'
    config=json.loads(config_path.read_text())
    execution=dict(schema_version=1,backend='streamed-gat-mulsum-v1',block_edges=3)
    if checkpointed:execution.update(schema_version=2,graph_activation_checkpointing=True)
    torch.manual_seed(11)
    left=ReplicationModel(config,'classification',execution=execution).to(dtype=dtype)
    # Constructor dispatch patch is bounded to candidate construction; actual
    # GraphEncoder/ReplicationModel/checkpoint/temporal source remains unchanged.
    with patch.object(original,'GraphAttention',candidate.GraphAttention):
        right=ReplicationModel(config,'classification',execution=execution).to(dtype=dtype)
    right.load_state_dict(left.state_dict())
    torch.manual_seed(73)
    e,_=edge_case('directed')
    g1={'mcm':torch.randn(8,32,dtype=dtype),'edge_index':e}
    g2={'mcm':torch.randn(5,32,dtype=dtype),'edge_index':torch.empty((2,0),dtype=torch.long)}
    graphs=[[g1,g2,g1],[g2,g1,g2]]
    prices=torch.randn(2,3,1,dtype=dtype)
    results=[]
    for model in (left,right):
        model.train();optimizer=torch.optim.Adam(model.parameters(),lr=.001,betas=(.9,.999),eps=1e-8,weight_decay=0.)
        torch.manual_seed(101);before=torch.get_rng_state().clone()
        output=model(graphs,prices)
        after_forward=torch.get_rng_state().clone()
        loss=torch.nn.functional.cross_entropy(output,torch.tensor([0,1]))
        loss.backward();after_backward=torch.get_rng_state().clone()
        grads={name:p.grad.detach().clone() for name,p in model.named_parameters()}
        assert all(torch.isfinite(x).all() for x in grads.values())
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
        optimizer.step()
        results.append(dict(output=output.detach(),grad=grads,
            model={k:v.detach().clone() for k,v in model.state_dict().items()},
            optimizer=optimizer.state_dict(),rng=(before,after_forward,after_backward)))
    a,b=results;close(a['output'],b['output'],dtype)
    for category in ('grad','model'):
        for key in a[category]:close(a[category][key],b[category][key],dtype)
    optimizer_state_equal(a['optimizer'],b['optimizer'],dtype)
    for x,y in zip(a['rng'],b['rng'],strict=True):assert torch.equal(x,y)

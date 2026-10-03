import json
from pathlib import Path
import pytest
import torch
from tradingagents.research.onchain_replication.model_registry import build_model


@pytest.mark.parametrize('arm',['lstm','gru','hlstm','node2vec','graphwave','watchyourstep','gin','constant_graph','mcm_without_gat','gat_without_mcm','training_label_permutation','proposed'])
def test_every_neural_arm_assembles_and_receives_gradients(arm):
    root=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/model.json';model=build_model(arm,'direction',json.loads(root.read_bytes()))
    if arm in ('lstm','gru','hlstm'):out=model(torch.randn(2,28,1))
    elif arm in ('node2vec','graphwave','watchyourstep'):out=model(torch.randn(2,28,1),torch.randn(2,28,30 if arm=='graphwave' else 32))
    elif arm=='constant_graph':out=model(torch.randn(2,28,1))
    else:
        graph={'mcm':torch.rand(3,4 if arm in ('gin','gat_without_mcm') else 32),'edge_index':torch.tensor([[0,1],[1,2]])}
        out=model([[graph]*2]*2,torch.randn(2,2,1))
    assert out.shape==(2,2);out.square().sum().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())

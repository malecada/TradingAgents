"""Synthetic full-model gradients through actual compact native production.

Two motifs/two time steps are explicit fixture dimensions; production settings
and financial-cell exposure are unchanged. The OS guard is mocked by the fixture.
"""
import gc
import json
from pathlib import Path
import torch
from tests.research.onchain_replication.test_compact_native_producer import admitted, api
from tradingagents.research.onchain_replication.model_registry import build_model


def test_actual_compact_inputs_train_full_model_without_mutating_fixed_features(admitted):
    t,job,graphs,examples=admitted;m=api()
    prepared,terminal=m.produce(t.run,'r',job,graphs,examples)
    config_path=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config/model.json'
    config=json.loads(config_path.read_bytes())|{'mcm_input':2,'lookback_days':2}
    torch.manual_seed(11);model=build_model('proposed','direction',config)
    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    rows=examples.train
    keys=[h for row in rows for h in row.graph_hashes]
    fixed_hashes=prepared.features.verified_hashes()
    weights={name:value.detach().clone() for name,value in model.named_parameters()}
    batch=prepared.features.load_batch(keys)
    sequences=[[batch[h] for h in row.graph_hashes] for row in rows]
    prices=torch.tensor([row.input_prices for row in rows],dtype=torch.float32).unsqueeze(-1)/100
    target=torch.tensor([row.up for row in rows],dtype=torch.long)
    output=model(sequences,prices)
    assert output.shape==(len(rows),2) and torch.isfinite(output).all()
    torch.nn.functional.cross_entropy(output,target).backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
    optimizer.step()
    changed={name for name,p in model.named_parameters() if not torch.equal(p.detach(),weights[name])}
    assert any(name.startswith('graph.') for name in changed)
    assert any(name.startswith('temporal.') for name in changed)
    assert all(not value.requires_grad and value.grad is None for item in batch.values() for value in item.values())
    del batch,sequences,output;gc.collect()
    assert prepared.features.live_tensor_bytes()==0
    assert prepared.features.verified_hashes()==fixed_hashes
    m.finalize(prepared)

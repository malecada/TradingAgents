import json
import numpy as np
import pytest
import torch
from tradingagents.research.onchain_replication.component_store import save_component,load_component
from tradingagents.research.onchain_replication.provenance import file_hash


def test_streamed_optimizer_rng_and_numpy_state_roundtrip(tmp_path):
    from tradingagents.research.onchain_replication.checkpoints import seed_all,capture_rng,restore_rng
    rng=seed_all(11);model=torch.nn.Linear(2,1);optimizer=torch.optim.Adam(model.parameters())
    model(torch.ones(1,2)).sum().backward();optimizer.step()
    state={'model':model.state_dict(),'optimizer':optimizer.state_dict(),'rng':capture_rng(rng),'numpy':np.arange(12.).reshape(3,4)}
    context={'graph':'a'*64,'phase':'embedding','cursor':1}
    path=save_component(tmp_path/'checkpoint',state,context)
    expected=(rng.random(),torch.rand(1));loaded=load_component(path,file_hash(path),context,max_array_bytes=1024**2)
    model.load_state_dict(loaded['model']);optimizer.load_state_dict(loaded['optimizer']);restore_rng(loaded['rng'],rng)
    assert rng.random()==expected[0] and torch.equal(torch.rand(1),expected[1])
    np.testing.assert_array_equal(loaded['numpy'],state['numpy'])
    with pytest.raises(FileExistsError):save_component(tmp_path/'checkpoint',state,context)


def test_component_refuses_corruption_drift_and_unbounded_allocation(tmp_path):
    path=save_component(tmp_path/'checkpoint',{'x':np.ones(1000)}, {'seed':11});sha=file_hash(path)
    with pytest.raises(ValueError,match='context'):load_component(path,sha,{'seed':12},max_array_bytes=10000)
    with pytest.raises(ValueError,match='size'):load_component(path,sha,{'seed':11},max_array_bytes=100)
    member=path.parent/'array-000000.npy';raw=bytearray(member.read_bytes());raw[-1]^=1;member.write_bytes(raw)
    with pytest.raises(ValueError,match='hash'):load_component(path,sha,{'seed':11},max_array_bytes=10000)


def test_multiple_arrays_cannot_bypass_aggregate_allocation_bound(tmp_path):
    path=save_component(tmp_path/'checkpoint',[np.ones(1000),np.ones(1000)],{})
    with pytest.raises(ValueError,match='total allocation'):load_component(path,file_hash(path),{},max_array_bytes=10000)

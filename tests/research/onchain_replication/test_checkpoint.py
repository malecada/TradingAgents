import numpy as np
import pytest
import torch
from tradingagents.research.onchain_replication.checkpoints import save_checkpoint,load_checkpoint,seed_all

P={'source_hashes':['a'*64],'config_hash':'b'*64,'input_hash':'c'*64,'dictionary_hash':'d'*64,'fold_id':'2024','cell_id':'synthetic','source_commit':'e'*40}


def step(model,opt,rng):
    x=torch.randn(4,2)+float(rng.random());y=torch.randn(4,1)
    opt.zero_grad();loss=(model(x)-y).square().mean();loss.backward();opt.step()


def test_resumed_parameters_optimizer_and_all_rng_match(tmp_path):
    rng=seed_all(11);model=torch.nn.Linear(2,1);opt=torch.optim.Adam(model.parameters())
    step(model,opt,rng)
    path=save_checkpoint(tmp_path,model,opt,rng,P,epoch=1,batch=0,logs=[{'epoch':0,'loss':1.}])
    step(model,opt,rng);expected={k:v.clone() for k,v in model.state_dict().items()}
    rng=seed_all(99);other=torch.nn.Linear(2,1);optimizer=torch.optim.Adam(other.parameters())
    meta=load_checkpoint(path,other,optimizer,rng,P)
    assert meta['epoch']==1 and meta['batch']==0
    step(other,optimizer,rng)
    assert all(torch.equal(v,expected[k]) for k,v in other.state_dict().items())
    with pytest.raises(ValueError,match='provenance'):load_checkpoint(path,other,optimizer,rng,{**P,'input_hash':'f'*64})
    (path.parent/'state.pt').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='hash'):load_checkpoint(path,other,optimizer,rng,P)


def test_missing_rng_rejected_before_model_mutation(tmp_path):
    import io
    from tradingagents.research.onchain_replication.cache import publish
    from tradingagents.research.onchain_replication.provenance import digest
    rng=seed_all(11);model=torch.nn.Linear(2,1);opt=torch.optim.Adam(model.parameters())
    initial=model.weight.clone();stream=io.BytesIO();torch.save({'model':model.state_dict()},stream)
    path=publish(tmp_path,digest(b'incomplete'),{'state.pt':stream.getvalue()},P)
    with pytest.raises(ValueError,match='state'):load_checkpoint(path,model,opt,rng,P)
    assert torch.equal(initial,model.weight)

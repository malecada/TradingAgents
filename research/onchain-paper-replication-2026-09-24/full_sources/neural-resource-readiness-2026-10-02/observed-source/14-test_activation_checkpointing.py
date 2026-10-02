"""Synthetic memory and gradient equivalence for graph activation checkpointing."""
import copy
import torch
import pytest

from tests.research.onchain_replication.test_model import cfg
from tradingagents.research.onchain_replication.model import ReplicationModel


def fixture(checkpoint,dropout=.2,arm="proposed"):
    torch.set_num_threads(2);torch.manual_seed(3141)
    config={**cfg(),'graph_activation_checkpointing':checkpoint,'gat_dropout':dropout}
    from tradingagents.research.onchain_replication.model_registry import build_model
    model=build_model(arm,'classification',config)
    graphs=[]
    for n in (19,23):
        edges=torch.tensor([(i,j) for i in range(n) for j in range(n) if i!=j and (i+j)%3],dtype=torch.long).T
        graphs.append({'mcm':torch.rand(n,4 if arm in ('gin','gat_without_mcm') else 32),'edge_index':edges})
    return model,[[graphs[0],graphs[1],graphs[0]],[graphs[1],graphs[0],graphs[1]]],torch.randn(2,3,1),torch.tensor([0,1])


def measured_step(checkpoint,arm="proposed"):
    model,graphs,prices,labels=fixture(checkpoint,arm=arm)
    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    saved=[]
    def pack(tensor):
        saved.append(tensor.numel()*tensor.element_size());return tensor
    with torch.autograd.graph.saved_tensors_hooks(pack,lambda x:x):
        output=model(graphs,prices)
        loss=torch.nn.functional.cross_entropy(output,labels)
    memory=sum(saved)
    loss.backward()
    gradients={k:p.grad.clone() for k,p in model.named_parameters()}
    optimizer.step()
    return output.detach(),loss.detach(),gradients,copy.deepcopy(model.state_dict()),memory,torch.get_rng_state()


def test_checkpointing_reduces_saved_tensors_without_changing_joint_update():
    ordinary=measured_step(False);bounded=measured_step(True)
    print(f'saved_tensor_reference_bytes: ordinary={ordinary[4]}, checkpointed={bounded[4]}')
    assert bounded[4]<ordinary[4], 'checkpoint flag did not reduce saved activation bytes'
    for a,b in zip(ordinary[:2],bounded[:2]):torch.testing.assert_close(a,b,rtol=1e-6,atol=1e-7)
    for name in ordinary[2]:
        torch.testing.assert_close(ordinary[2][name],bounded[2][name],rtol=1e-6,atol=1e-7)
        assert torch.isfinite(bounded[2][name]).all()
    for name in ordinary[3]:torch.testing.assert_close(ordinary[3][name],bounded[3][name],rtol=1e-6,atol=1e-7)
    assert torch.equal(ordinary[5],bounded[5]), 'checkpoint recomputation advanced dropout RNG'
    for prefix in ('graph.mlp','graph.gat','temporal.lstm','temporal.query','temporal.key','temporal.alignment','temporal.output'):
        assert sum(float(g.abs().sum()) for k,g in bounded[2].items() if k.startswith(prefix))>0


@pytest.mark.parametrize('value',[1,'true',None])
def test_invalid_checkpoint_policy_is_not_silently_enabled_or_ignored(value):
    with pytest.raises(ValueError,match='checkpoint'):
        ReplicationModel({**cfg(),'graph_activation_checkpointing':value},'classification')


def test_checkpointed_training_replays_optimizer_and_rng_from_saved_checkpoint(tmp_path):
    from tradingagents.research.onchain_replication.checkpoints import seed_all,save_checkpoint,load_checkpoint
    rng=seed_all(123)
    model,graphs,prices,labels=fixture(True)
    optimizer=torch.optim.Adam(model.parameters(),lr=.001)
    def step(m,o):
        o.zero_grad(set_to_none=True)
        loss=torch.nn.functional.cross_entropy(m(graphs,prices),labels)
        loss.backward();o.step();return loss.detach()
    step(model,optimizer)
    provenance={'source_hashes':['a'*64],'config_hash':'b'*64,'input_hash':'c'*64,'dictionary_hash':'d'*64,'fold_id':'synthetic','cell_id':'activation-equivalence','source_commit':'e'*40}
    path=save_checkpoint(tmp_path/'checkpoints',model,optimizer,rng,provenance,epoch=0,batch=1,logs=[],epoch_loss=0.,epoch_count=2)
    expected=step(model,optimizer);expected_rng=torch.get_rng_state()
    restored,_,_,_=fixture(True)
    restored_optimizer=torch.optim.Adam(restored.parameters(),lr=.001)
    load_checkpoint(path,restored,restored_optimizer,rng,provenance)
    actual=step(restored,restored_optimizer)
    torch.testing.assert_close(actual,expected,rtol=0,atol=0)
    assert torch.equal(torch.get_rng_state(),expected_rng)
    for name,param in model.state_dict().items():torch.testing.assert_close(param,restored.state_dict()[name],rtol=0,atol=0)


@pytest.mark.parametrize('evaluation,no_grad',[(True,False),(False,True)])
def test_checkpoint_option_preserves_inference_and_masked_steps(evaluation,no_grad):
    model,graphs,prices,_=fixture(True,dropout=0.)
    reference,_,_,_=fixture(False,dropout=0.)
    if evaluation:model.eval();reference.eval()
    mask=torch.tensor([[True,True,False],[True,True,False]])
    graphs[0][2]=None;graphs[1][2]=None
    with torch.set_grad_enabled(not no_grad):
        actual=model(graphs,prices,mask)
        expected=reference(graphs,prices,mask)
    torch.testing.assert_close(actual,expected,rtol=0,atol=0)


@pytest.mark.parametrize('arm',['gin','gat_without_mcm','mcm_without_gat'])
def test_inherited_graph_comparators_preserve_gradients_and_updates(arm):
    ordinary=measured_step(False,arm);bounded=measured_step(True,arm)
    assert bounded[4]<ordinary[4]
    torch.testing.assert_close(ordinary[0],bounded[0],rtol=1e-6,atol=1e-7)
    for section in (2,3):
        for name in ordinary[section]:
            torch.testing.assert_close(ordinary[section][name],bounded[section][name],rtol=1e-6,atol=1e-7)
    assert torch.equal(ordinary[5],bounded[5])


def test_checkpoint_exposes_tensor_devices_to_rng_discovery(monkeypatch):
    from tradingagents.research.onchain_replication import model as module
    original=module.checkpoint
    model,graphs,prices,_=fixture(True)
    seen=[]
    def checked(function,*args,**kwargs):
        assert len(args)>=2 and isinstance(args[0],torch.Tensor) and isinstance(args[1],torch.Tensor), 'tensor devices hidden from checkpoint RNG discovery'
        seen.append(id(args[0]))
        return original(function,*args,**kwargs)
    monkeypatch.setattr(module,'checkpoint',checked)
    model(graphs,prices).sum().backward()
    assert sorted(seen)==sorted({id(graph['mcm']) for row in graphs for graph in row})


@pytest.mark.skipif(not torch.cuda.is_available(),reason='CUDA hardware unavailable; no GPU parity claim')
def test_cuda_dropout_checkpoint_predictions_gradients_updates_and_rng():
    def step(enabled):
        model,graphs,prices,labels=fixture(enabled)
        model=model.cuda()
        unique={id(g):{k:v.cuda() for k,v in g.items()} for row in graphs for g in row}
        graphs=[[unique[id(g)] for g in row] for row in graphs]
        optimizer=torch.optim.Adam(model.parameters(),lr=.001)
        output=model(graphs,prices.cuda())
        torch.nn.functional.cross_entropy(output,labels.cuda()).backward()
        gradients={k:p.grad.detach().cpu() for k,p in model.named_parameters()}
        optimizer.step()
        return output.detach().cpu(),gradients,{k:v.detach().cpu() for k,v in model.state_dict().items()},torch.cuda.get_rng_state()
    ordinary=step(False);bounded=step(True)
    torch.testing.assert_close(ordinary[0],bounded[0],rtol=1e-4,atol=1e-5)
    for section in (1,2):
        for name in ordinary[section]:
            torch.testing.assert_close(ordinary[section][name],bounded[section][name],rtol=1e-4,atol=1e-5)
    assert torch.equal(ordinary[3],bounded[3])

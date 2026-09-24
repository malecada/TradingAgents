from dataclasses import dataclass
import pytest
import torch
from tests.research.test_lifecycle import registered,start
from tradingagents.research.onchain_replication.training import fit_cell,predict_cell
from tradingagents.research.onchain_replication.checkpoints import seed_all

P={'source_hashes':['a'*64],'config_hash':'b'*64,'input_hash':'c'*64,'dictionary_hash':'d'*64,'fold_id':'2024','cell_id':'sum','source_commit':'e'*40}
CFG={'epochs':3,'batch_size':2,'learning_rate':.001,'betas':[.9,.999],'epsilon':1e-8,'weight_decay':0.,'gradient_clip_norm':1.,'shuffle':False,'scheduler':'none'}


def batch(indices):
    return {'input':torch.tensor([[float(i),float(i+1)] for i in indices])},torch.tensor([[float(i%2)] for i in indices])


def test_finite_fit_rejects_duplicate_and_predicts(registered):
    with start(registered) as run:
        provenance={**P,'source_commit':run.admission.source}
        result=fit_cell(run,'sum',provenance,lambda:torch.nn.Linear(2,1),batch,4,'regression',11,CFG)
        assert len(result.logs)==3 and result.logs[-1]['epoch']==2
        assert torch.isfinite(predict_cell(result.model,batch,4,2)).all()
        with pytest.raises(FileExistsError):fit_cell(run,'sum',provenance,lambda:torch.nn.Linear(2,1),batch,4,'regression',11,CFG)


def test_unregistered_cell_cannot_fit(registered):
    with start(registered) as run:
        with pytest.raises(ValueError,match='unregistered'):fit_cell(run,'absent',P,lambda:torch.nn.Linear(2,1),batch,4,'regression',11,CFG)


@pytest.mark.parametrize('interrupt_epoch',[1,3])
def test_interrupted_fit_requires_new_registered_attempt_and_replays(registered,interrupt_epoch):
    import copy
    import json
    from pathlib import Path
    from tests.research.test_lifecycle import commit,api
    from tradingagents.research.onchain_replication.provenance import file_hash
    root,spec,source=registered
    checkpoint=[]
    def interrupt(epoch,batch_number,path):
        if epoch==interrupt_epoch and batch_number==0:
            checkpoint.append(path)
            raise RuntimeError('synthetic interrupt')
    with pytest.raises(RuntimeError,match='synthetic interrupt'):
        with start(registered) as run:
            golden=fit_cell(run,'count',{**P,'cell_id':'count','source_commit':source},lambda:torch.nn.Linear(2,1),batch,4,'regression',11,CFG)
            fit_cell(run,'sum',{**P,'source_commit':source},lambda:torch.nn.Linear(2,1),batch,4,'regression',11,CFG,after_batch=interrupt)
    Run,_,_=api()
    with pytest.raises((FileExistsError,ValueError)):
        start(registered)
    child=copy.deepcopy(spec['experiments']['example-a']);child['parent']='example-a'
    child['inputs']['checkpoint']={'path':str(checkpoint[0].relative_to(root)),'sha256':file_hash(checkpoint[0]),'dataset':'sample'}
    spec['experiments']['example-b']=child
    complete_checkpoint=golden.checkpoint
    child['inputs']['completed_checkpoint']={'path':str(complete_checkpoint.relative_to(root)),'sha256':file_hash(complete_checkpoint),'dataset':'sample'}
    new_source=commit(root,spec)
    with Run.start(root=root,registration='registration.json',experiment='example-b',source=new_source) as run:
        with pytest.raises(ValueError,match='parent fit is active or completed'):
            fit_cell(run,'count',{**P,'cell_id':'count','source_commit':new_source},lambda:torch.nn.Linear(2,1),batch,4,'regression',11,CFG,continuation={'checkpoint':complete_checkpoint,'provenance':{**P,'cell_id':'count','source_commit':source}})
        result=fit_cell(run,'sum',{**P,'source_commit':new_source},lambda:torch.nn.Linear(2,1),batch,4,'regression',11,CFG,continuation={'checkpoint':checkpoint[0],'provenance':{**P,'source_commit':source}})
        assert all(torch.equal(value,golden.model.state_dict()[key]) for key,value in result.model.state_dict().items())
        assert result.logs==golden.logs


def test_flat_regression_target_cannot_broadcast(registered):
    def flat(indices):
        inputs,targets=batch(indices);return inputs,targets[:,0]
    with start(registered) as run:
        with pytest.raises(ValueError,match='target shape'):
            fit_cell(run,'sum',{**P,'source_commit':run.admission.source},lambda:torch.nn.Linear(2,1),flat,4,'regression',11,CFG)


def test_predictions_cannot_drop_rows():
    class Drop(torch.nn.Module):
        def forward(self,input):return input[:1,:1]
    with pytest.raises(ValueError,match='population'):predict_cell(Drop(),batch,4,2)

"""Synthetic compact features through maintained scaling, fitting and checkpoints.

Both tasks use fresh registered synthetic cells; no market fit or OS guard claim.
Two motifs/two steps/two epochs are explicit fixture settings only.
"""
from dataclasses import asdict
import gc
import json
from pathlib import Path
import pytest
import torch
from tests.research.onchain_replication import test_compact_native_producer as upstream
from tradingagents.research.onchain_replication.contracts import Fold, PricePanel
from tradingagents.research.onchain_replication.dataset import fit_scaler, example_binding
from tradingagents.research.onchain_replication.evaluation import batch_factory
from tradingagents.research.onchain_replication.training import fit_cell, predict_cell
from tradingagents.research.onchain_replication.checkpoints import seed_all, load_checkpoint
from tradingagents.research.onchain_replication.model_registry import build_model
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash

CONFIG=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config'


@pytest.fixture
def admitted(monkeypatch,request):
    training=upstream.upstream.upstream.upstream.upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            model=json.loads((CONFIG/'model.json').read_bytes())|{'mcm_input':2,'lookback_days':2}
            schedule=json.loads((CONFIG/'training.json').read_bytes())|{'epochs':2,'batch_size':1}
            t.input('synthetic_model',model);t.input('synthetic_training',schedule)
            t.exp['cells']=['synthetic-classification','synthetic-regression']
            path=t.root/t.exp['charter']['path']
            path.write_text('Synthetic compact full model: two motifs, two time steps, two epochs; classification and regression; no market experiment.\n')
            t.exp['charter']['sha256']=file_hash(path)
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=upstream.admitted.__wrapped__(monkeypatch,request)
    try:yield next(gen)
    finally:
        try:next(gen)
        except StopIteration:pass


def test_both_tasks_fit_predict_reload_and_preserve_compact_features(admitted):
    t,job,graphs,examples=admitted;m=upstream.api()
    prepared,terminal=m.produce(t.run,'r',job,graphs,examples)
    model_config=json.loads(t.run.read_input('synthetic_model'))
    schedule=json.loads(t.run.read_input('synthetic_training'))
    # Reconstruct only the synthetic training input-price table; no test/target
    # values enter scaler fitting, and the maintained date-selection rule applies.
    table={d:p for row in examples.train for d,p in zip(row.input_dates,row.input_prices,strict=True)}
    dates=tuple(sorted(table));prices=PricePanel('ETH-USD',dates,tuple(table[d] for d in dates),(),
        'b'*64,'2026-01-01T00:00:00Z')
    scaler=fit_scaler(examples,prices,Fold(**job['descriptor']['fold']))
    assert scaler.train_hash==examples.train_hash and set(scaler.dates)<=set(table)
    fixed=prepared.features.verified_hashes()
    for task,cell in [('direction','synthetic-classification'),('regression','synthetic-regression')]:
        kind='classification' if task=='direction' else task
        provenance={'source_hashes':list(examples.source_hashes),
            'config_hash':digest(canonical_bytes({'model':model_config,'training':schedule,'task':task})),
            'input_hash':digest(canonical_bytes(example_binding(examples,scaler))),
            'dictionary_hash':prepared.binding['dictionary_hash'],'fold_id':job['descriptor']['fold']['id'],
            'cell_id':cell,'source_commit':t.run.admission.source}
        factory=lambda:build_model('proposed',task,model_config)
        train=batch_factory('proposed',task,examples.train,scaler,prepared.features)
        test=batch_factory('proposed',task,examples.test,scaler,prepared.features)
        result=fit_cell(t.run,cell,provenance,factory,train,len(examples.train),kind,11,schedule)
        assert len(result.logs)==2 and all(row['examples']==len(examples.train) for row in result.logs)
        assert result.checkpoint_hash==file_hash(result.checkpoint)
        prediction=predict_cell(result.model,test,len(examples.test),1)
        assert prediction.shape==(len(examples.test),2 if task=='direction' else 1)
        restored=factory();rng=seed_all(11)
        optimizer=torch.optim.Adam(restored.parameters(),lr=schedule['learning_rate'],
            betas=tuple(schedule['betas']),eps=schedule['epsilon'],weight_decay=schedule['weight_decay'])
        state=load_checkpoint(result.checkpoint,restored,optimizer,rng,provenance)
        assert state['epoch']==2 and state['batch']==0 and state['logs']==result.logs
        assert torch.equal(prediction,predict_cell(restored,test,len(examples.test),1))
        assert all(torch.equal(value,restored.state_dict()[name]) for name,value in result.model.state_dict().items())
        with pytest.raises(FileExistsError,match='already claimed'):
            fit_cell(t.run,cell,provenance,factory,train,len(examples.train),kind,11,schedule)
        del result,restored,optimizer,prediction,state;gc.collect()
        assert prepared.features.live_tensor_bytes()==0
        assert prepared.features.verified_hashes()==fixed
        m.finalize(prepared)

"""Small synthetic numerical checks only; no ResearchRun, guard or real data."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path

import pytest
import torch

from tradingagents.research.onchain_replication.model import ReplicationModel


def helper():
    name = 'tradingagents.research.onchain_replication.real_pilot_training'
    assert importlib.util.find_spec(name) is not None, 'one-update pilot helper not implemented'
    return importlib.import_module(name)


def example(tmp_path):
    torch.set_num_threads(2)
    root = Path(__file__).resolve().parents[3]
    config = json.loads((root/'research/onchain-paper-replication-2026-09-24/config/model.json').read_text())
    training = json.loads((root/'research/onchain-paper-replication-2026-09-24/config/training.json').read_text())
    features = {}
    contracts = {}
    sha = lambda t: hashlib.sha256(t.numpy().tobytes()).hexdigest()
    for i in range(7):
        key = hashlib.sha256(str(i).encode()).hexdigest()
        mcm = (torch.arange(96, dtype=torch.float32).reshape(3,32)+i+1)/100
        edges = torch.tensor([[0,1,2],[1,2,0]])
        features[key] = {'mcm':mcm, 'edge_index':edges}
        contracts[key] = {'nodes':3, 'edges':3, 'mcm_sha256':sha(mcm), 'edge_index_sha256':sha(edges)}
    keys = list(features)
    sequences = [[keys[(i+j)//7 % 7] for j in range(28)] for i in range(16)]
    prices = torch.linspace(-1,1,448).reshape(16,28,1)
    labels = torch.tensor([i % 2 for i in range(16)])
    def batch(indices):
        assert indices == list(range(16))
        return {'prices':prices, 'graph_sequences':[[features[h] for h in row] for row in sequences]},labels
    return dict(model_factory=lambda:ReplicationModel(config,'classification'),batch_factory=batch,
                indices=list(range(16)),graph_features=features,graph_contracts=contracts,
                graph_sequences=sequences,model_config=config,training_config=training,
                provenance={'scope':'synthetic test only'},directory=tmp_path/'attempt',
                authority_check=lambda:None,max_checkpoint_bytes=4*1024**2)


def test_real_model_one_update_and_exact_checkpoint(tmp_path):
    result=helper().run_one_update(**example(tmp_path))
    assert result['optimizer_steps']==1 and result['financial_fit_complete'] is False
    assert result['unique_graphs']==7 and result['graph_references']==448
    assert result['checkpoint_exact_readback'] is True
    assert all(result['gradients'][k]['nonzero_elements']>0 for k in ('gat','lstm','attention'))
    state=torch.load(tmp_path/'attempt/checkpoint.pt',weights_only=True)
    assert state['optimizer_steps']==1 and state['financial_fit_complete'] is False
    assert all(int(row['step'])==1 for row in state['optimizer']['state'].values())
    assert {'forward','backward','optimizer','checkpoint','readback'} <= set(result['seconds'])


def test_truncated_edges_refused_before_update(tmp_path):
    args=example(tmp_path);args['graph_features'][next(iter(args['graph_features']))]['edge_index']=torch.tensor([[0],[1]])
    with pytest.raises(ValueError,match='edge'):
        helper().run_one_update(**args)
    assert not (tmp_path/'attempt/checkpoint.pt').exists()


def test_graph_object_alias_across_hashes_refused(tmp_path):
    args=example(tmp_path);keys=list(args['graph_features']);args['graph_features'][keys[1]]=args['graph_features'][keys[0]]
    with pytest.raises(ValueError,match='distinct'):
        helper().run_one_update(**args)


def test_authority_refusal_precedes_output_birth(tmp_path):
    args=example(tmp_path)
    def refuse():raise RuntimeError('no current owner')
    args['authority_check']=refuse
    with pytest.raises(RuntimeError,match='no current owner'):helper().run_one_update(**args)
    assert not args['directory'].exists()


def test_disconnected_gat_gradient_is_failure_not_success(tmp_path):
    args=example(tmp_path);factory=args['model_factory']
    def disconnected():
        model=factory()
        for p in model.graph.gat.parameters():p.register_hook(lambda g:torch.zeros_like(g))
        return model
    args['model_factory']=disconnected
    with pytest.raises(ValueError,match='gat'):helper().run_one_update(**args)
    assert json.loads((args['directory']/'failed.json').read_text())['optimizer_steps']==0


def test_checkpoint_limit_preserves_partial_and_failure(tmp_path):
    args=example(tmp_path);args['max_checkpoint_bytes']=128
    with pytest.raises((ValueError,RuntimeError,OSError)):helper().run_one_update(**args)
    assert (args['directory']/'checkpoint.pt').exists()
    assert (args['directory']/'checkpoint.pt').stat().st_size<=128
    assert json.loads((args['directory']/'failed.json').read_text())['optimizer_steps']==1
    assert not (args['directory']/'complete.json').exists()


def test_existing_evaluation_batch_factory_keeps_actual_prices_and_labels(tmp_path):
    from tradingagents.research.onchain_replication.dataset import Example,Scaler
    from tradingagents.research.onchain_replication.evaluation import batch_factory
    args=example(tmp_path)
    examples=[Example('synthetic','synthetic','synthetic','synthetic',tuple(str(j) for j in range(28)),
                      tuple(100+i+j/10 for j in range(28)),tuple(row),tuple('synthetic' for _ in row),110.,i%2)
              for i,row in enumerate(args['graph_sequences'])]
    args['batch_factory']=batch_factory('proposed','direction',examples,Scaler(100.,10.,(),'synthetic'),args['graph_features'])
    result=helper().run_one_update(**args)
    assert result['optimizer_steps']==1 and result['checkpoint_exact_readback']


def test_changed_frozen_optimizer_refused_before_birth(tmp_path):
    args=example(tmp_path);args['training_config']['learning_rate']=0.5
    with pytest.raises(ValueError,match='frozen training'):helper().run_one_update(**args)
    assert not args['directory'].exists()


def test_wrong_labels_never_replaced(tmp_path):
    args=example(tmp_path);factory=args['batch_factory']
    def bad(indices):
        inputs,labels=factory(indices)
        return inputs,labels.float()
    args['batch_factory']=bad
    with pytest.raises(ValueError,match='labels'):helper().run_one_update(**args)
    assert not (args['directory']/'checkpoint.pt').exists()


def test_lost_owner_after_checkpoint_retains_checkpoint_and_failure(tmp_path):
    args=example(tmp_path)
    def boundary():
        if (args['directory']/'checkpoint.pt').exists():raise RuntimeError('owner lost after checkpoint')
    args['authority_check']=boundary
    with pytest.raises(RuntimeError,match='owner lost after checkpoint'):helper().run_one_update(**args)
    assert (args['directory']/'checkpoint.pt').stat().st_size>0
    assert json.loads((args['directory']/'failed.json').read_text())['optimizer_steps']==1
    assert not (args['directory']/'complete.json').exists()


def test_gapped_eligible_indices_refused_before_batch_or_birth(tmp_path):
    args=example(tmp_path);args['indices']=list(range(15))+[16]
    def forbidden(indices):raise AssertionError('batch must not be fetched')
    args['batch_factory']=forbidden
    with pytest.raises(ValueError,match='consecutive'):helper().run_one_update(**args)
    assert not args['directory'].exists()


def test_default_eager_refuses_implicit_streamed_factory(tmp_path):
    args=example(tmp_path)
    policy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}
    args['model_factory']=lambda:ReplicationModel(args['model_config'],'classification',execution=policy)
    with pytest.raises(ValueError,match='execution'):helper().run_one_update(**args)
    assert not (args['directory']/'checkpoint.pt').exists()


def test_explicit_streamed_execution_survives_exact_checkpoint(tmp_path):
    args=example(tmp_path)
    policy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}
    args['model_execution']=policy
    args['model_factory']=lambda:ReplicationModel(args['model_config'],'classification',execution=policy)
    result=helper().run_one_update(**args)
    state=torch.load(args['directory']/'checkpoint.pt',weights_only=True)
    assert result['model_execution']==policy==state['model_execution']
    assert result['checkpoint_exact_readback'] and result['optimizer_steps']==1

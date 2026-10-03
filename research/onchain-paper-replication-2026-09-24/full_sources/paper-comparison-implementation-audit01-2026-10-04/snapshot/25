from dataclasses import replace,asdict
from pathlib import Path
import json
import numpy as np
import pytest
import torch
from tests.research.onchain_replication.test_dataset import fixture
from tradingagents.research.onchain_replication.dataset import build_examples
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest
from tradingagents.research.onchain_replication.feature_pipeline import prepare_features

CONFIG=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/config'

def configs():
    return {k:json.loads((CONFIG/(v+'.json')).read_bytes()) for k,v in [('dictionary','dictionary'),('matching','matching-stable'),('baselines','baselines')]}

def population():
    graphs,prices,fold,config=fixture();examples=build_examples(graphs,prices,fold,config)
    examples=replace(examples,train=examples.train[:2],test=examples.test[:2],
        train_hash=digest(canonical_bytes([asdict(x) for x in examples.train[:2]])),
        test_mask_hash=digest(canonical_bytes([x.decision_at for x in examples.test[:2]])))
    return graphs,fold,examples


@pytest.mark.parametrize('arm',['gin','gat_without_mcm','graphwave'])
def test_graph_producer_binds_raw_topology_and_fixed_population(arm):
    graphs,fold,examples=population();prepared=prepare_features(graphs,examples,fold,arm,11,configs(),max_entries=100000,checkpoint=lambda *args:None)
    required={h for x in (*examples.train,*examples.test) for h in x.graph_hashes}
    assert set(prepared.features)==required==set(prepared.binding['lineage'])
    assert prepared.binding['train_hash']==examples.train_hash and prepared.binding['seed']==11
    for h,value in prepared.features.items():
        assert prepared.binding['lineage'][h]['input_graph_hash']==h
        if arm=='graphwave':assert value.shape==(30,)
        else:assert value['mcm'].shape[1]==4 and value['edge_index'].shape[0]==2


def test_proposed_runs_dictionary_then_mcm_then_full_trainable_model():
    graphs,fold,examples=population();config=configs()
    # Small synthetic sampling fixture; production frozen512 is not changed.
    config['dictionary']={**config['dictionary'],'sample_count':32,'size':32}
    checkpoints=[]
    prepared=prepare_features(graphs,examples,fold,'proposed',11,config,max_entries=100000,checkpoint=lambda *args:checkpoints.append(args[0]))
    assert prepared.dictionary is not None and len(prepared.dictionary.representatives)==32
    assert prepared.binding['dictionary_hash']==prepared.dictionary.identity
    assert all(value['mcm'].shape[1]==32 for value in prepared.features.values())
    from tradingagents.research.onchain_replication.model_registry import build_model
    model=build_model('proposed','direction',json.loads((CONFIG/'model.json').read_bytes()))
    sequences=[[prepared.features[h] for h in example.graph_hashes] for example in examples.test]
    result=model(sequences,torch.zeros((2,28,1)));loss=result.square().sum();loss.backward()
    assert result.shape==(2,2) and all(p.grad is not None for p in model.parameters())
    assert 'dictionary_complete' in checkpoints and 'graph_complete' in checkpoints


def test_missing_or_foreign_graph_never_becomes_empty_feature_vector():
    graphs,fold,examples=population()
    with pytest.raises(ValueError,match='membership'):prepare_features([],examples,fold,'gin',11,configs(),max_entries=10000,checkpoint=lambda *args:None)


@pytest.mark.parametrize('arm',['node2vec','watchyourstep'])
def test_delayed_intermediate_cannot_change_earlier_feature_and_all_ancestors_are_bound(monkeypatch,arm):
    from types import SimpleNamespace
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash
    import tradingagents.research.onchain_replication.feature_pipeline as pipeline
    graphs,fold,_=population()
    # Jan10 publication -> Jan24 scored graph -> delayed Jan30 publication ->
    # Jan31 intermediate -> Feb8 scored graph. Event order alone leaks Jan30.
    graphs=list(graphs[:5])
    publications=['2022-01-10','2022-01-30','2022-01-24','2022-01-31','2022-02-08']
    graphs=[replace(g,available_at=date+'T00:00:00Z') for g,date in zip(graphs,publications)]
    hashes=list(map(graph_hash,graphs))
    def row(i,decision):
        return SimpleNamespace(graph_hashes=(hashes[i],),graph_available_at=(graphs[i].available_at,),decision_at=decision+'T00:00:00Z')
    examples=SimpleNamespace(fold_hash=fold.member_hash,source_hashes=graphs[0].source_hashes,
        train=(row(0,'2022-01-11'),row(2,'2022-01-25')),test=(row(4,'2022-02-09'),),train_hash='a'*64)
    calls=[]
    def engine(edges,n,config,seed,**kwargs):
        calls.append(len(calls))
        return np.ones((n,32)),[]
    monkeypatch.setattr(pipeline,arm,engine)
    # Accumulation reveals any transitive influence without numerical ambiguity.
    monkeypatch.setattr(pipeline,'align_embeddings',lambda nodes,values,old_nodes,old_values:values+old_values)
    result=prepare_features(graphs,examples,fold,arm,11,configs(),max_entries=100000,checkpoint=lambda *args:None)
    np.testing.assert_array_equal(result.features[hashes[2]],np.full(32,2.))
    order=[hashes[i] for i in (0,2,1,3,4)]
    assert result.binding['alignment_order']==order
    assert set(result.binding['lineage'])==set(hashes)
    for i,h in enumerate(order):
        item=result.binding['lineage'][h]
        assert item['alignment_previous_graph_hash']==(order[i-1] if i else None)
        assert item['source_hashes']==list(graphs[0].source_hashes)
        assert item['max_basis_available_at']==item['available_at']
    # A changed future intermediate can affect later predictions, never Jan25.
    calls.clear()
    def future_engine(edges,n,config,seed,**kwargs):
        i=len(calls);calls.append(i)
        return np.full((n,32),10. if i==2 else 1.),[]
    monkeypatch.setattr(pipeline,arm,future_engine)
    changed=prepare_features(graphs,examples,fold,arm,11,configs(),max_entries=100000,checkpoint=lambda *args:None)
    np.testing.assert_array_equal(changed.features[hashes[2]],result.features[hashes[2]])
    assert np.all(changed.features[hashes[4]]!=result.features[hashes[4]])

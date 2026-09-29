"""Synthetic exact graph-level sampling and retained scratch lifecycle checks."""
from dataclasses import replace
import json
import numpy as np
import pytest

from tests.research.onchain_replication.test_matching_reference import graph
from tests.research.onchain_replication.test_neighborhoods import cfg
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods


def population():
    first = graph([[i] for i in range(37)], [(i,(i+1)%37,float(i+1)) for i in range(37)])
    second = replace(first, start_utc='2024-01-08T00:00:00Z',
                     end_utc='2024-01-15T00:00:00Z', available_at='2024-01-16T00:00:00Z')
    return [second,first]


@pytest.mark.parametrize('seed',[11,23,37,53,71])
def test_mapped_sampling_preserves_complete_graph_manifest(tmp_path,seed):
    graphs=population();config=cfg()|{'sample_count':50}
    eager=sample_neighborhoods(graphs,config,seed)
    out=tmp_path/'scratch'
    mapped=sample_neighborhoods(graphs,config,seed,weight_workspace=out,max_weight_bytes=100000)
    assert mapped.identity==eager.identity
    assert mapped.records==eager.records and mapped.rng_state==eager.rng_state
    assert mapped.source_hashes==eager.source_hashes
    for a,b in zip(mapped.graphs,eager.graphs,strict=True):
        assert a.node_ids==b.node_ids and a.parent_hash==b.parent_hash
        for name in ('node_features','edge_index','edge_features'):
            np.testing.assert_array_equal(getattr(a,name),getattr(b,name))
    receipt=json.loads((out/'complete.json').read_text())
    assert receipt['sample_identity']==eager.identity
    assert receipt['numeric_bytes']==3*74*8
    assert {p.name for p in out.iterdir()}=={'intent.json','complete.json','weights.bin','probability.bin','cdf.bin'}
    before={p.name:p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        sample_neighborhoods(graphs,config,seed,weight_workspace=out,max_weight_bytes=100000)
    assert before=={p.name:p.read_bytes() for p in out.iterdir()}


def test_weight_budget_refused_before_workspace_reservation(tmp_path):
    out=tmp_path/'small'
    with pytest.raises(ValueError,match='budget'):
        sample_neighborhoods(population(),cfg(),11,weight_workspace=out,max_weight_bytes=1)
    assert not out.exists()


def test_workspace_requires_explicit_budget_and_budget_requires_workspace(tmp_path):
    with pytest.raises(ValueError,match='budget'):
        sample_neighborhoods(population(),cfg(),11,weight_workspace=tmp_path/'missing')
    with pytest.raises(ValueError,match='workspace'):
        sample_neighborhoods(population(),cfg(),11,max_weight_bytes=100000)


def test_neighborhood_failure_preserves_reserved_arrays(tmp_path):
    out=tmp_path/'failed'
    with pytest.raises(ValueError,match='capacity'):
        sample_neighborhoods(population(),cfg()|{'maximum_neighborhood_nodes':1},11,
                             weight_workspace=out,max_weight_bytes=100000)
    receipt=json.loads((out/'failed.json').read_text())
    assert 'capacity' in receipt['reason'] and not (out/'complete.json').exists()
    assert (out/'weights.bin').stat().st_size==74*8


@pytest.mark.parametrize('bad',[0.,-1.,np.nan,np.inf])
def test_invalid_weight_mass_refused_before_random_draw(tmp_path,bad):
    from tradingagents.research.onchain_replication.sampling_weights import MappedWeights
    rng=np.random.Generator(np.random.PCG64(11));before=rng.bit_generator.state
    with pytest.raises(ValueError,match='weight'):
        with MappedWeights(tmp_path/'invalid',9,100000,{'test':'synthetic'}) as store:
            store.weights[:]=bad
            store.draw(rng)
    assert rng.bit_generator.state==before


def test_valid_zero_weights_match_numpy_choice_and_state(tmp_path):
    from tradingagents.research.onchain_replication.sampling_weights import MappedWeights
    expected_rng=np.random.Generator(np.random.PCG64(23));actual_rng=np.random.Generator(np.random.PCG64(23))
    weights=np.array([0.,2.,0.,.125,1e-50,7.,0.,.3,.7])
    with MappedWeights(tmp_path/'zeros',len(weights),100000,{'test':'synthetic'}) as store:
        for _ in range(7):
            store.weights[:]=weights
            p=weights/weights.sum();expected=int(expected_rng.choice(len(weights),p=p))
            chosen,probability=store.draw(actual_rng)
            assert chosen==expected and np.float64(probability).tobytes()==p[expected].tobytes()
            assert actual_rng.bit_generator.state==expected_rng.bit_generator.state
            weights[chosen]=0.
            if not weights.any():break


def test_low_disk_refusal_creates_no_workspace(tmp_path,monkeypatch):
    from tradingagents.research.onchain_replication import sampling_weights
    from collections import namedtuple
    Usage=namedtuple('Usage','total used free')
    monkeypatch.setattr(sampling_weights.shutil,'disk_usage',lambda _:Usage(100,99,1))
    with pytest.raises(ValueError,match='disk'):
        with sampling_weights.MappedWeights(tmp_path/'disk',9,100000,{}):pass
    assert not (tmp_path/'disk').exists()


def test_oversized_binding_refused_before_reservation(tmp_path):
    from tradingagents.research.onchain_replication.sampling_weights import MappedWeights
    with pytest.raises(ValueError,match='metadata budget'):
        MappedWeights(tmp_path/'metadata',9,100000,{'too_large':'x'*33000})
    assert not (tmp_path/'metadata').exists()


def test_unsupported_numpy_refused_without_changing_default_sampler(tmp_path,monkeypatch):
    from tradingagents.research.onchain_replication import sampling_weights
    monkeypatch.setattr(sampling_weights.np,'__version__','2.3.1')
    with pytest.raises(ValueError,match='NumPy'):
        sample_neighborhoods(population(),cfg(),11,weight_workspace=tmp_path/'version',max_weight_bytes=100000)
    assert not (tmp_path/'version').exists()
    assert len(sample_neighborhoods(population(),cfg(),11).graphs)==3


def test_partial_allocation_failure_closes_maps_and_preserves_attempt(tmp_path,monkeypatch):
    from tradingagents.research.onchain_replication import sampling_weights
    real=sampling_weights.os.posix_fallocate;calls=[]
    def fail_second(fd,offset,length):
        calls.append(length)
        if len(calls)==2:raise OSError('synthetic allocation refusal')
        return real(fd,offset,length)
    monkeypatch.setattr(sampling_weights.os,'posix_fallocate',fail_second)
    store=sampling_weights.MappedWeights(tmp_path/'allocation',9,100000,{})
    with pytest.raises(OSError,match='allocation refusal'):
        with store:pytest.fail('must fail before enter returns')
    assert all(a._mmap.closed for a in store.arrays)
    assert (store.directory/'failed.json').exists()
    assert not (store.directory/'complete.json').exists()
    assert (store.directory/'weights.bin').stat().st_size==72


def test_caught_interruption_is_terminal_and_not_resumable(tmp_path):
    from tradingagents.research.onchain_replication.sampling_weights import MappedWeights
    store=MappedWeights(tmp_path/'interrupted',9,100000,{})
    with pytest.raises(KeyboardInterrupt):
        with store:raise KeyboardInterrupt('synthetic interruption')
    result=json.loads((store.directory/'failed.json').read_text())
    assert result['resumable'] is False and 'KeyboardInterrupt' in result['reason']
    assert all(a._mmap.closed for a in store.arrays)


def test_flush_failure_still_closes_every_mapping(tmp_path,monkeypatch):
    from tradingagents.research.onchain_replication.sampling_weights import MappedWeights
    store=MappedWeights(tmp_path/'flush',9,100000,{})
    def fail():raise OSError('synthetic flush failure')
    with pytest.raises(OSError,match='flush failure'):
        with store:monkeypatch.setattr(store.arrays[0],'flush',fail)
    assert all(a._mmap.closed for a in store.arrays)
    assert (store.directory/'failed.json').exists()
    assert not (store.directory/'complete.json').exists()


def test_large_allocation_blocks_include_separate_metadata_blocks(tmp_path,monkeypatch):
    from tradingagents.research.onchain_replication import sampling_weights
    from types import SimpleNamespace
    monkeypatch.setattr(sampling_weights.os,'statvfs',lambda _:SimpleNamespace(f_frsize=65536))
    monkeypatch.setattr(sampling_weights.shutil,'disk_usage',lambda _:SimpleNamespace(free=100*2**30))
    with pytest.raises(ValueError,match='budget'):
        sampling_weights.MappedWeights(tmp_path/'large_blocks',9,300000,{})
    assert not (tmp_path/'large_blocks').exists()


@pytest.mark.parametrize('size',[257,4097,131071])
def test_skewed_large_weight_arrays_preserve_probability_bytes(tmp_path,size):
    from tradingagents.research.onchain_replication.sampling_weights import MappedWeights
    fixture_rng=np.random.Generator(np.random.PCG64(71))
    weights=np.exp(-fixture_rng.random(size)*400)
    weights[::7]=0
    eager=np.random.Generator(np.random.PCG64(53));mapped=np.random.Generator(np.random.PCG64(53))
    with MappedWeights(tmp_path/'skew',size,4*2**20,{'test':'synthetic'}) as store:
        store.weights[:]=weights
        for _ in range(32):
            probability=weights/weights.sum();expected=int(eager.choice(size,p=probability))
            chosen,p=store.draw(mapped)
            assert chosen==expected and np.float64(p).tobytes()==probability[expected].tobytes()
            assert mapped.bit_generator.state==eager.bit_generator.state
            neighbors=np.unique((chosen+np.arange(-17,18))%size)
            weights[chosen]=0;store.weights[chosen]=0
            weights[neighbors]*=.5;store.weights[neighbors]*=.5

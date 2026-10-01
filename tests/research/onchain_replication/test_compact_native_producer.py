"""Explicit compact selection and actual fresh producer integration, no fits."""
import json
from dataclasses import replace
import pytest
from tests.research.onchain_replication import test_compact_native_features as upstream
from tests.research.onchain_replication import test_compact_denominator as dates


def api():
    from tradingagents.research.onchain_replication import compact_native_producer
    return compact_native_producer


def test_actual_run_required():
    with pytest.raises(ValueError,match='actual'):api().selected(object(),'r',{})


@pytest.fixture
def admitted(monkeypatch,request):
    training=upstream.upstream.upstream.upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    option=getattr(request,'param','valid')
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item.update(pair_journal_parent_input=None,max_graph_payload_bytes=1048576)
            if option=='route':t.item['compact_terminal_input']='sample'
            if option=='backend':t.item['native_backend']=None
            if option=='capacity':
                t.input('compact_native_features',{'schema_version':1,'max_live_tensor_bytes':1,
                    'max_numeric_bytes':8192,'chunk_entries':64})
        return original(helper,prepare)
    class Captured(Exception):pass
    holder={}
    def capture(helper,t):
        holder.update(helper=helper,t=t);raise Captured()
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    monkeypatch.setattr(training.first.Tests,'open',capture)
    gen=upstream.admitted.__wrapped__(monkeypatch)
    try:
        with pytest.raises(Captured):next(gen)
        t=holder['t'];graphs,fold,examples=dates.population()
        job=json.loads(t.run.read_input('execution_job'))['payload']['representation_jobs']['r']
        yield t,job,graphs,examples
    finally:
        gen.close()
        if 'helper' in holder:holder['helper'].doCleanups()


@pytest.mark.parametrize('admitted',['route','backend'],indirect=True)
def test_conflicting_selection_refused_before_claim(admitted):
    t,job,graphs,examples=admitted
    with pytest.raises(ValueError):api().selected(t.run,'r',job)
    assert not t.directory.exists()


@pytest.mark.parametrize('admitted',['capacity'],indirect=True)
def test_single_graph_capacity_refuses_before_claim(admitted):
    t,job,graphs,examples=admitted
    with pytest.raises(ValueError,match='capacity'):api().produce(t.run,'r',job,graphs,examples)
    assert not t.directory.exists()


def test_postclaim_failure_is_fatal_and_cannot_restart(admitted,monkeypatch):
    t,job,graphs,examples=admitted;m=api()
    def fail(*args,**kw):raise RuntimeError('synthetic training failure')
    monkeypatch.setattr(m.compact_training,'admit',fail)
    with pytest.raises(m.CompactProducerError):m.produce(t.run,'r',job,graphs,examples)
    assert (t.directory/'failed.json').is_file()
    assert (t.directory/'attempt-failed.json').is_file()
    with pytest.raises(ValueError,match='reserved'):m.selected(t.run,'r',job)


def test_actual_fresh_producer_returns_native_features_and_final_evidence(admitted):
    t,job,graphs,examples=admitted;m=api()
    assert m.selected(t.run,'r',job)
    prepared,terminal=m.produce(t.run,'r',job,graphs,examples)
    assert terminal._owner.closed and set(prepared.features)==set(job['descriptor']['required_graphs'])
    assert prepared.features.verified_hashes()==prepared.binding['feature_hashes']
    m.finalize(prepared)
    with pytest.raises(ValueError,match='binding'):
        m.finalize(replace(prepared,binding=dict(prepared.binding)|{'seed':12}))
    with pytest.raises(ValueError,match='reserved'):m.selected(t.run,'r',job)

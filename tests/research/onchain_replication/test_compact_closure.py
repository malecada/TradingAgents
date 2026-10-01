"""All required compact graph artifacts plus the complete calendar denominator."""
from types import SimpleNamespace
import shutil
import pytest
from tests.research.test_lifecycle import git
from tests.research.onchain_replication import test_compact_graph_artifacts as artifacts
from tests.research.onchain_replication import test_compact_denominator as dates
from tradingagents.research.onchain_replication.provenance import file_hash


def api():
    from tradingagents.research.onchain_replication import compact_closure
    return compact_closure


def test_rejects_unowned_caller_objects():
    with pytest.raises(ValueError,match='actual'):api().admit(object(),object(),[],input_name='closure')


@pytest.fixture
def admitted(monkeypatch):
    training=artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    monkeypatch.setattr(training,'population',dates.population)
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            t.input('calendar',dates.CALENDAR);t.input('coverage',dates.COVERAGE)
            t.input('compact_denominator',{'schema_version':1,'calendar_input':'calendar',
                'coverage_input':'coverage','max_calendar_days':64})
            t.input('compact_closure',{'schema_version':1,'max_graphs':16,'max_record_bytes':1048576,
                'max_numeric_payload_bytes':1048576})
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item.update(compact_denominator_input='compact_denominator',compact_closure_input='compact_closure')
            path=t.root/dates.VALIDATOR;path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(dates.ROOT/dates.VALIDATOR,path);git(t.root,'add','--',dates.VALIDATOR)
            t.exp['source_files'][dates.VALIDATOR]=file_hash(path)
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=artifacts.admitted.__wrapped__(SimpleNamespace(param='valid'),monkeypatch)
    features,t=next(gen)
    try:
        from tradingagents.research.onchain_replication import compact_denominator,compact_mcm,compact_features
        dictionary=features._mcm._dictionary;route=compact_mcm._training(dictionary)
        denominator=compact_denominator.admit(route,input_name='compact_denominator')
        graphs=[artifacts.api().publish(features,input_name='compact_graph_output')]
        for key in route.descriptor['required_graphs']:
            if key==features.record['graph_hash']:continue
            mcm=compact_mcm.produce(dictionary,graph_hash=key,input_name='compact_mcm',output_input='compact_mcm_output')
            other=compact_features.prepare(mcm,input_name='compact_features')
            graphs.append(artifacts.api().publish(other,input_name='compact_graph_output'))
        yield dictionary,denominator,graphs,t
    finally:
        try:next(gen)
        except StopIteration:pass


def test_exact_complete_graph_calendar_union_and_final_owner_revocation(admitted,monkeypatch):
    dictionary,denominator,graphs,t=admitted;m=api()
    result=m.admit(dictionary,denominator,graphs,input_name='compact_closure');result.check()
    required=set(denominator.record['denominator']['required_graphs'])
    assert len(required)==2 and set(result.record['binding']['feature_hashes'])==required
    assert result.record['denominator']['denominator']['calendar_days']==20
    assert result.record['empirical_admission_verified'] is False
    owner=dictionary._proof.owner
    assert not owner.closed and set(owner.stages)=={'dictionary',*('mcm-'+h for h in required)}
    for changed in (graphs[:1],[*graphs,graphs[0]]):
        with pytest.raises(ValueError):m.admit(dictionary,denominator,changed,input_name='compact_closure')
    lease=type(result).lease;injected=[]
    def revoke(self):
        lease(self);owner.poisoned=True;injected.append(True)
    monkeypatch.setattr(type(result),'lease',revoke)
    with pytest.raises(ValueError,match='owner'):result.check()
    assert injected

"""Durable exact compact closure metadata, retaining failed publication identity."""
import json
import pytest
from tests.research.onchain_replication import test_compact_closure as upstream


def api():
    from tradingagents.research.onchain_replication import compact_publication
    return compact_publication


def test_requires_actual_compact_closure():
    with pytest.raises(ValueError,match='actual'):api().publish(object(),input_name='output')


@pytest.fixture
def admitted(monkeypatch):
    training=upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            t.input('compact_publication',{'schema_version':1,'max_metadata_bytes':1048576,
                'max_attempt_bytes':4194304})
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item['compact_publication_input']='compact_publication'
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=upstream.admitted.__wrapped__(monkeypatch)
    dictionary,denominator,graphs,t=next(gen)
    try:yield upstream.api().admit(dictionary,denominator,graphs,input_name='compact_closure'),t
    finally:
        try:next(gen)
        except StopIteration:pass


def test_persists_exact_binding_rejects_republication_and_detects_changed_saved_metadata(admitted):
    closure,t=admitted;m=api();published=m.publish(closure,input_name='compact_publication')
    published.check()
    path=published.directory/'binding.json'
    saved=json.loads(path.read_bytes())
    assert set(saved['feature_hashes'])==set(closure.record['binding']['feature_hashes'])
    assert path.read_bytes()==m.canonical_bytes(m.thaw(closure.record['binding']))
    assert len(saved['feature_hashes'])==2
    assert published.record['representation_sealed'] is False
    assert not closure._dictionary._proof.owner.closed
    with pytest.raises(ValueError):m.publish(closure,input_name='compact_publication')
    saved['seed']+=1;path.write_text(json.dumps(saved))
    with pytest.raises(ValueError):published.check()


def test_last_publication_callback_revocation_preserves_failed_identity(admitted,monkeypatch):
    closure,t=admitted;m=api();owner=closure._dictionary._proof.owner
    original=m.Published.lease;changed=[]
    def revoke(self):
        original(self);owner.poisoned=True;changed.append(True)
    monkeypatch.setattr(m.Published,'lease',revoke)
    with pytest.raises(ValueError,match='owner'):m.publish(closure,input_name='compact_publication')
    path=m.directory(closure)
    assert changed and (path/'failed.json').is_file() and (path/'complete.json').is_file()
    with pytest.raises(ValueError):m.publish(closure,input_name='compact_publication')

"""Actual compact representation seal and current-run terminal handoff."""
import json
from pathlib import Path
import pytest
from tests.research.onchain_replication import test_compact_publication as upstream


def api():
    from tradingagents.research.onchain_replication import compact_terminal
    return compact_terminal


def test_actual_publication_required():
    with pytest.raises(ValueError,match='actual'):api().finish(object(),input_name='terminal')


@pytest.fixture
def admitted(monkeypatch):
    training=upstream.upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original=training.first.Tests.fixture
    def fixture(helper,mutate):
        def prepare(t):
            mutate(t)
            t.input('compact_terminal',{'schema_version':1,'max_metadata_bytes':1048576,
                'max_attempt_bytes':8388608})
            t.exp['outputs']+=['later-a.json','later-b.json']
            for item in (t.item,t.execution['payload']['representation_jobs']['r']):
                item.update(compact_terminal_input='compact_terminal',binding_output='binding.json',journal_output='journal.json')
        return original(helper,prepare)
    monkeypatch.setattr(training.first.Tests,'fixture',fixture)
    gen=upstream.admitted.__wrapped__(monkeypatch);closure,t=next(gen)
    try:yield upstream.api().publish(closure,input_name='compact_publication'),t
    finally:
        try:next(gen)
        except StopIteration:pass


def test_actual_seal_keeps_old_leases_closed_accepts_registered_outputs_and_detects_corruption(admitted):
    published,t=admitted;m=api();owner=published._closure._dictionary._proof.owner
    terminal=m.finish(published,input_name='compact_terminal');terminal.check()
    assert owner.closed and terminal.record['schema_version']==2
    marker=json.loads((owner.root.parent/'complete.json').read_bytes())
    assert marker['format']=='compact-representation-v1' and 'events' not in marker
    assert set(t.run._published_outputs)=={'binding.json','journal.json'}
    for operation in (owner.lease,published.check,lambda:m.finish(published,input_name='compact_terminal')):
        with pytest.raises(ValueError):operation()
    for name in ('later-a.json','later-b.json'):
        t.run.write_json(name,{'synthetic':name});terminal.lease()
    terminal.check()
    target=t.run.directory/'outputs/binding.json';raw=target.read_bytes();target.write_bytes(raw.replace(b'"seed": 11',b'"seed": 12'))
    assert target.read_bytes()!=raw
    with pytest.raises(ValueError):terminal.lease()
    target.write_bytes(raw)
    graph=published._closure._graphs[0]
    member=graph.directory/'artifact/array-000000.npy';raw=member.read_bytes()
    member.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
    with pytest.raises(ValueError):terminal.check()


def test_last_terminal_callback_cannot_revoke_owner(admitted,monkeypatch):
    published,t=admitted;m=api();owner=published._closure._dictionary._proof.owner
    original=m.Receipt.lease;changed=[]
    def revoke(self):
        original(self);owner.poisoned=True;changed.append(True)
    monkeypatch.setattr(m.Receipt,'lease',revoke)
    with pytest.raises(ValueError,match='owner'):m.finish(published,input_name='compact_terminal')
    assert changed and owner.closed and (m.directory(published)/'failed.json').is_file()
    assert (owner.root.parent/'complete.json').is_file()


def test_output_failure_keeps_sealed_representation_and_prevents_retry(admitted,monkeypatch):
    published,t=admitted;m=api();owner=published._closure._dictionary._proof.owner
    write=t.run.write_json
    def fail(name,value):
        if name=='journal.json':raise RuntimeError('synthetic output failure')
        return write(name,value)
    monkeypatch.setattr(t.run,'write_json',fail)
    with pytest.raises(RuntimeError,match='output failure'):m.finish(published,input_name='compact_terminal')
    assert owner.closed and (owner.root/'complete.json').is_file()
    assert (owner.root.parent/'complete.json').is_file()
    assert (t.run.directory/'outputs/binding.json').is_file()
    assert not (t.run.directory/'outputs/journal.json').exists()
    assert (m.directory(published)/'failed.json').is_file()
    with pytest.raises(ValueError):m.finish(published,input_name='compact_terminal')

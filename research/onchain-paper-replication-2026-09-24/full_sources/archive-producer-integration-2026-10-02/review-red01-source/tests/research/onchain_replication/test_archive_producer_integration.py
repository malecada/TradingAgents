"""Actual registered synthetic producer-to-terminal archive route; local files only."""
import json
import hashlib
from dataclasses import replace
from types import SimpleNamespace

import pytest

from tests.research.onchain_replication import test_compact_native_producer as native
from tests.research.onchain_replication.test_archive_chunks import Transport


@pytest.fixture
def admitted(monkeypatch, tmp_path, request):
    training = native.upstream.upstream.upstream.upstream.artifacts.upstream.upstream.dictionary.samples.publication.sampling.training
    original = training.first.Tests.fixture
    transport = Transport(tmp_path / 'remote')
    option = getattr(request, 'param', 'archive')
    if option=='capacity':
        import numpy as np
        construct=native.dates.GraphSnapshot
        def isolated(*args,**kwargs):
            return replace(construct(*args,**kwargs),node_ids=('a','b','c'),node_features=np.ones((3,4)),
                edge_index=np.empty((2,0),dtype=np.int64),edge_features=np.empty((0,2)))
        monkeypatch.setattr(native.dates,'GraphSnapshot',isolated)
    def fixture(helper, mutate):
        def prepare(t):
            mutate(t)
            if option == 'local': return
            policy = dict(schema_version=1, backend='compact-archive-events-v1',
                transport_identity=transport.identity, remote_namespace='synthetic',
                local_free_floor_bytes=10*1024**3, max_stage_verifications=2,
                max_writer_metadata_bytes=1000000, max_read_metadata_bytes=500000,
                max_stage_bytes=600000, max_workflow_metadata_bytes=100000000,
                max_remote_payload_bytes=100000000, max_decoded_transfer_bytes=1000000000)
            t.input('archive_policy', policy)
            for item in (t.item, t.execution['payload']['representation_jobs']['r']):
                item['compact_archive_input'] = 'archive_policy'
                item['descriptor']['compact_archive_execution'] = dict(
                    backend=policy['backend'], policy_sha256=t.exp['inputs']['archive_policy']['sha256'])
                if option=='capacity':
                    item['descriptor']['seed']=12
                    item['descriptor']['configs']['dictionary'].update(
                        sample_count=5,size=2,partition_threshold=2,partition_size=3)
            if option == 'hash':
                t.item['descriptor']['compact_archive_execution']['policy_sha256'] = '0'*64
            if option=='capacity':
                sampler=json.loads((t.root/'compact_sampler.json').read_bytes())
                sampler['max_attempt_bytes']=(5+3)*sampler['max_metadata_bytes']
                t.input('compact_sampler',sampler)
        return original(helper, prepare)
    monkeypatch.setattr(training.first.Tests, 'fixture', fixture)
    gen = native.admitted.__wrapped__(monkeypatch, SimpleNamespace(param='valid'))
    values = next(gen)
    try: yield *values, transport
    finally: gen.close()


@pytest.mark.parametrize('admitted', ['capacity'], indirect=True)
def test_actual_archive_dictionary_mcm_publication_and_postclose_checks(admitted):
    t, job, graphs, examples, transport = admitted
    m = native.api()
    prepared, terminal = m.produce(t.run, 'r', job, graphs, examples, archive_transport=transport)
    owner = terminal._owner; ledger = owner._archive_operations
    assert owner.closed and ledger._closed and not ledger._poisoned
    assert set(ledger._writers) == set(owner.required)
    assert ledger._reads == {name: 1 for name in owner.required}
    assert owner.stages['dictionary'].count_policy is not None
    assert owner.stages['dictionary'].contract['pairs'] == 20 < owner.stages['dictionary'].pairs == 22
    for name, stage in owner.stages.items():
        assert stage.contract['archive']['backend'] == 'compact-archive-events-v1'
        if name != 'dictionary':
            assert stage.count_policy is None and stage.contract['pairs'] == stage.pairs
    def forbidden(*args, **kwargs): raise AssertionError('post-close check attempted remote transfer')
    transport.mkdir = transport.put = transport.get = forbidden
    terminal.check(); m.finalize(prepared)
    closed=ledger.root/'closed.json';original_closed=closed.read_bytes()
    altered_closed=json.loads(original_closed);altered_closed['reserved']['remote_payload_bytes']+=1
    modified=(json.dumps(altered_closed,sort_keys=True,separators=(',',':'))+'\n').encode()
    closed.write_bytes(modified);ledger._expected['closed.json']=modified
    with pytest.raises(ValueError):terminal.check()
    closed.write_bytes(original_closed);ledger._expected['closed.json']=original_closed
    retained={p:p.read_bytes() for p in ledger.root.rglob('*.json')};spent=dict(ledger.reserved)
    with pytest.raises(ValueError):m.produce(t.run,'r',job,graphs,examples,archive_transport=transport)
    assert dict(ledger.reserved)==spent and all(p.read_bytes()==raw for p,raw in retained.items())
    stage=owner.stages['dictionary'];marker=stage.root/'stage-complete.json'
    original=marker.read_bytes();reference=stage.reference
    altered=json.loads(original);altered['scientific_result']['completed_pairs']+=1
    marker.write_text(json.dumps(altered));stage.reference=hashlib.sha256(marker.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='stage authority'):terminal.check()
    # Harness restores only its injected mutation to isolate the foreign-entry check.
    marker.write_bytes(original);stage.reference=reference
    names = {'owner.json', 'start.json', 'claim.json', 'compact', 'complete.json', 'archive-operations'}
    from tradingagents.research.onchain_replication.archive_owner_stage import attempt_path
    names |= {attempt_path(ledger, op).name for op in ledger._operations.values() if op.record['kind'] == 'reader'}
    assert {p.name for p in owner.root.parent.iterdir()} == names
    # Every successful claim remains historical; unadmitted namespace is refused.
    before = {p: p.read_bytes() for p in ledger.root.rglob('*.json')}
    (owner.root.parent / 'archive-stage-read-foreign').mkdir()
    with pytest.raises(ValueError): terminal.check()
    assert all(p.read_bytes() == raw for p, raw in before.items())


@pytest.mark.parametrize('admitted', ['hash'], indirect=True)
def test_archive_descriptor_hash_refused_before_claim(admitted):
    t, job, graphs, examples, transport = admitted
    with pytest.raises(ValueError):
        native.api().produce(t.run, 'r', job, graphs, examples, archive_transport=transport)
    assert not t.directory.exists() and not list(transport.root.iterdir())


def test_late_archive_mcm_mutation_preserves_spent_claims(admitted, monkeypatch):
    t, job, graphs, examples, transport = admitted
    from tradingagents.research.onchain_replication import archive_owner_stage, compact_mcm
    original = archive_owner_stage._execute_locked
    holder = {}
    kernel = compact_mcm._kernel(); numerical = kernel.mcm
    def calculate(*args, **kwargs):
        result = numerical(*args, **kwargs); holder['matrix'] = result['mcm']; return result
    def seal(ledger, stage, **kwargs):
        value = original(ledger, stage, **kwargs)
        if stage.kind == 'mcm':
            holder['ledger'] = ledger; holder['stage'] = stage
            holder['spending']=dict(ledger.reserved)
            holder['claims']={p:p.read_bytes() for op in ledger._operations.values()
                if op._stage is stage for p in op.root.glob('*.json')}
            holder['matrix'][0, 0] += .125
        return value
    monkeypatch.setattr(kernel, 'mcm', calculate)
    monkeypatch.setattr(compact_mcm, '_kernel', lambda: kernel)
    monkeypatch.setattr(archive_owner_stage, '_execute_locked', seal)
    with pytest.raises(native.api().CompactProducerError):
        native.api().produce(t.run, 'r', job, graphs, examples, archive_transport=transport)
    ledger = holder['ledger']; stage = holder['stage']
    # Independent default fixture denominator: two nodes by two motifs.
    assert stage.pairs == stage.contract['pairs'] == 4
    assert holder['matrix'].shape == (2,2)
    assert ledger.owner.poisoned and stage.closed
    assert ledger._reads[stage.name] == 1 and set(ledger._writers[stage.name]._terminal) == {'complete.json'}
    assert (stage.root / 'stage-complete.json').exists()
    assert (t.directory / 'attempt-failed.json').exists()
    assert dict(ledger.reserved)==holder['spending']
    assert all(p.read_bytes()==raw for p,raw in holder['claims'].items())
    assert not (t.directory/'complete.json').exists()
    assert ledger._closed and ledger._poisoned
    closed=json.loads((ledger.root/'closed.json').read_bytes())
    assert closed['poisoned'] is True and closed['reserved']==holder['spending']


def test_writer_completion_cannot_bless_changed_dictionary_matrix(admitted, monkeypatch):
    t,job,graphs,examples,transport=admitted
    from tradingagents.research.onchain_replication import archive_owner_writer,compact_dictionary
    original=archive_owner_writer._run_locked;holder={}
    def changed(ledger,stage,produce,**kwargs):
        value,receipt=original(ledger,stage,produce,**kwargs)
        if stage.kind=='dictionary':
            holder['ledger']=ledger;holder['stage']=stage
            value[0]['matrices'][0]['matrix'][0,0]+=.125
        return value,receipt
    monkeypatch.setattr(archive_owner_writer,'_run_locked',changed)
    with pytest.raises(native.api().CompactProducerError) as caught:
        native.api().produce(t.run,'r',job,graphs,examples,archive_transport=transport)
    assert 'writer completion' in str(caught.value.__cause__)
    ledger=holder['ledger'];stage=holder['stage']
    assert ledger.owner.poisoned and not stage.closed and not ledger._reads
    assert set(ledger._writers['dictionary']._terminal)=={'complete.json'}
    assert not (stage.root/'stage-complete.json').exists()


@pytest.mark.parametrize('admitted', ['local'], indirect=True)
def test_existing_local_route_has_no_archive_ledger(admitted):
    t, job, graphs, examples, transport = admitted
    prepared, terminal = native.api().produce(t.run, 'r', job, graphs, examples)
    assert not hasattr(terminal._owner, '_archive_operations')
    terminal.check(); native.api().finalize(prepared)
    assert not list(transport.root.iterdir())


def test_captured_transition_expires_and_cannot_cross_thread():
    from threading import Lock, Thread
    from tradingagents.research.onchain_replication import compact_owner as m
    owner=m.Owner.__new__(m.Owner);owner._transition=Lock();owner.poisoned=False
    failures=[]
    with m._held(owner) as held:
        def crossed():
            try:held.check(owner)
            except BaseException as error:failures.append(error)
        thread=Thread(target=crossed);thread.start();thread.join()
        assert len(failures)==1 and isinstance(failures[0],ValueError)
        held.check(owner)
    with pytest.raises(ValueError):held.check(owner)
    assert not held.lock.locked()


def test_invalidated_transition_cannot_mask_fatal_primary():
    from threading import Lock
    from tradingagents.research.onchain_replication import compact_owner as m
    owner=m.Owner.__new__(m.Owner);original=owner._transition=Lock();owner.poisoned=False
    primary=m.io.CleanupFailure('synthetic original close uncertainty')
    with pytest.raises(m.io.CleanupFailure) as caught:
        with m._held(owner):
            owner._transition=Lock()
            raise primary
    assert caught.value is primary and not original.locked()


def test_native_failure_preserves_primary_fatal_despite_ledger_close_error(admitted,monkeypatch):
    t,job,graphs,examples,transport=admitted
    from tradingagents.research.onchain_replication import compact_owner,archive_owner_operations
    primary=compact_owner.io.CleanupFailure('original training cleanup uncertainty')
    original=archive_owner_operations.Ledger._close;holder={}
    def uncertain(ledger):
        original(ledger);holder['ledger']=ledger
        raise OSError('uncertain after real poisoned ledger close')
    def training(*args,**kwargs):raise primary
    monkeypatch.setattr(archive_owner_operations.Ledger,'_close',uncertain)
    monkeypatch.setattr(native.api().compact_training,'admit',training)
    with pytest.raises(compact_owner.io.CleanupFailure) as caught:
        native.api().produce(t.run,'r',job,graphs,examples,archive_transport=transport)
    assert caught.value is primary
    ledger=holder['ledger']
    assert ledger._closed and ledger._poisoned and not ledger._operations
    assert json.loads((ledger.root/'closed.json').read_bytes())['poisoned'] is True
    assert (t.directory/'attempt-failed.json').exists()
    assert any('cleanup' in note for note in primary.__notes__)

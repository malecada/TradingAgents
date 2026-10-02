"""Actual registered owner selection, with the fixture's mocked OS guard."""
import json
import pytest

from tests.research.onchain_replication import test_first_owner as first
from tests.research.onchain_replication.test_compact_policy import candidate
from tests.research.onchain_replication.test_archive_chunks import Transport
from tradingagents.research.onchain_replication import compact_owner
from tradingagents.research.onchain_replication.provenance import thaw


@pytest.fixture
def admitted(tmp_path,request):
    f = first.Tests(); transport = Transport(tmp_path/'remote')
    option = getattr(request,'param',None)
    def prepare(t):
        p = candidate();t.policy['limits'] = p['pair'];t.input('pair_policy',t.policy)
        t.descriptor['pair_execution']['policy_sha256'] = t.exp['inputs']['pair_policy']['sha256']
        t.input('compact_policy',{'schema_version':1,'backend':p['backend'],'stage_policy':p,
            'max_workflow_retained_logical_bytes':30000000})
        t.descriptor['compact_execution'] = {'backend':p['backend'],
            'policy_sha256':t.exp['inputs']['compact_policy']['sha256']}
        t.descriptor['configs'] = {'matching':{'max_iterations':10}}
        if option == 'writer_matching':
            from tests.research.onchain_replication.test_matching_reference import config
            t.descriptor['configs']['matching'] = config() | {'beta_final':1.}
        policy = {'schema_version':1,'backend':'compact-archive-events-v1',
            'transport_identity':transport.identity,'remote_namespace':'synthetic',
            'local_free_floor_bytes':10*1024**3,'max_stage_verifications':4,
            'max_writer_metadata_bytes':1000000,'max_read_metadata_bytes':500000,
            'max_stage_bytes':600000,'max_workflow_metadata_bytes':10000000,
            'max_remote_payload_bytes':1000000,'max_decoded_transfer_bytes':1000000}
        if option in policy:policy[option] = 1
        t.input('archive_policy',policy)
        t.descriptor['compact_archive_execution'] = {'backend':policy['backend'],
            'policy_sha256':t.exp['inputs']['archive_policy']['sha256']}
        for item in (t.item,t.execution['payload']['representation_jobs']['r']):
            item.update(native_backend=p['backend'],compact_policy_input='compact_policy',
                compact_archive_input='archive_policy')
        if option == 'selection':t.item['compact_archive_input'] = 'sample'
        if option == 'descriptor':t.descriptor['compact_archive_execution']['policy_sha256'] = '0'*64
    try:
        result = f.fixture(prepare);journal,bound = f.open(result)
        owner = compact_owner.attach(bound,policy_input='compact_policy')
        yield result,owner,transport
    finally:f.doCleanups()


def select(admitted):
    from tradingagents.research.onchain_replication.archive_owner_policy import select
    return select(admitted[1],input_name='archive_policy',transport=admitted[2])


def test_registered_policy_binds_actual_owner_and_full_required_stage_population(admitted):
    selection = select(admitted);selection.check()
    value = thaw(selection.record)
    assert value['owner'] == admitted[1].identity and value['required_stages'] == list(admitted[1].required)
    assert value['capacity']['stage_count'] == 2
    assert value['capacity']['remote_payload_bytes'] == 2*200*168
    assert value['capacity']['decoded_transfer_bytes'] == 2*200*168*(3+4)
    assert value['execution_admitted'] is False
    assert not list(admitted[2].root.iterdir())
    assert set(p.name for p in admitted[1].root.iterdir()) == {'owner.json'}
    dictionary = selection.writer_policy('dictionary')
    mcm = selection.writer_policy(admitted[1].required[1])
    assert dictionary['remote_prefix'] != mcm['remote_prefix']
    assert dictionary['max_chunks'] == 13 and dictionary['local_free_floor_bytes'] == 10*1024**3
    dictionary['max_chunks'] = 1
    assert selection.writer_policy('dictionary')['max_chunks'] == 13
    with pytest.raises(ValueError):selection.writer_policy('foreign')


@pytest.mark.parametrize('admitted',['selection','descriptor','max_writer_metadata_bytes',
    'max_read_metadata_bytes','max_stage_bytes','max_workflow_metadata_bytes',
    'max_remote_payload_bytes','max_decoded_transfer_bytes','local_free_floor_bytes'],indirect=True)
def test_wrong_registration_or_underreserved_envelope_refuses(admitted):
    with pytest.raises(ValueError):select(admitted)
    assert set(p.name for p in admitted[1].root.iterdir()) == {'owner.json'}


@pytest.mark.parametrize('reason',['input','terminal'])
def test_saved_input_change_or_terminal_owner_revokes_selection(admitted,reason):
    selection = select(admitted)
    if reason == 'terminal':admitted[0].run.fail('synthetic owner policy test closure')
    else:(admitted[0].root/'archive_policy.json').write_bytes(b'{}')
    with pytest.raises(ValueError):selection.check()


def test_transport_endpoint_change_revokes_selection(admitted):
    selection = select(admitted);admitted[2].identity = '0'*64
    with pytest.raises(ValueError):selection.check()


def test_selection_requires_exact_current_owner_and_registered_input(admitted):
    from tradingagents.research.onchain_replication.archive_owner_policy import select
    with pytest.raises(ValueError):select(object(),input_name='archive_policy',transport=admitted[2])
    with pytest.raises(ValueError):select(admitted[1],input_name='sample',transport=admitted[2])


def test_already_started_owner_cannot_select_storage_retroactively(admitted):
    owner = admitted[1]
    owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    with pytest.raises(ValueError,match='fresh'):select(admitted)


def test_late_valid_stage_creation_refuses_selection(admitted,monkeypatch):
    owner = admitted[1];original = owner.boundary;calls = 0
    def boundary():
        nonlocal calls
        calls += 1;original()
        if calls == 2:
            owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    monkeypatch.setattr(owner,'boundary',boundary)
    with pytest.raises(ValueError,match='fresh'):select(admitted)
    assert 'dictionary' in owner.stages
    assert owner.active is owner.stages['dictionary']

"""Fresh ResearchRun compact owner tests; kernel guard boundary is synthetic."""
import json
from pathlib import Path
import pytest
from tests.research.onchain_replication import test_first_owner as first
from tests.research.onchain_replication.test_compact_policy import candidate
from tradingagents.research.onchain_replication import matching_owner
from tradingagents.research.onchain_replication.provenance import thaw


@pytest.fixture
def admitted(request):
    f = first.Tests()
    def prepare(t):
        p = candidate()
        t.policy['limits'] = p['pair']; t.input('pair_policy', t.policy)
        t.descriptor['pair_execution']['policy_sha256'] = t.exp['inputs']['pair_policy']['sha256']
        t.input('compact_policy', {'schema_version': 1, 'backend': p['backend'],
            'stage_policy': p, 'max_workflow_retained_logical_bytes': getattr(request, 'param', 30000000)})
        t.descriptor['compact_execution'] = {'backend': p['backend'],
            'policy_sha256': t.exp['inputs']['compact_policy']['sha256']}
        t.descriptor['configs'] = {'matching': {'max_iterations': 10}}
        for item in (t.item, t.execution['payload']['representation_jobs']['r']):
            item.update(native_backend=p['backend'], compact_policy_input='compact_policy')
    result = f.fixture(prepare)
    journal, bound = f.open(result)
    try: yield result, journal, bound
    finally: f.doCleanups()


def attach(admitted):
    from tradingagents.research.onchain_replication.compact_owner import attach
    return attach(admitted[2], policy_input='compact_policy')


def finish_zero_dictionary(owner):
    from tradingagents.research.onchain_replication.compact_pair_log import PairLog
    stage = owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    policy = thaw(owner.policy)
    log = PairLog(stage.root / 'matching', owner=owner.identity, scope=thaw(stage.scope),
        limits=policy['log'], max_iterations=10, lease=stage.lease)
    (stage.root / 'checkpoints').mkdir()
    return stage, owner.finish_stage(stage, log_terminal_sha256=log.finish(), stream_terminal_sha256=None)


def test_actual_admission_creates_exclusive_owner_and_binds_stage_policy(admitted):
    owner = attach(admitted); owner.lease()
    assert owner.root == admitted[1].directory / 'compact'
    assert owner.required == ('dictionary', 'mcm-' + 'a' * 64)
    with pytest.raises((ValueError, FileExistsError)): attach(admitted)
    start = json.loads((owner.root / 'owner.json').read_bytes())
    assert start['binding']['claim_sha256'] == admitted[0].run._claim_sha256
    assert start['policy_sha256'] == admitted[0].exp['inputs']['compact_policy']['sha256']
    assert not list(owner.root.glob('*/matching'))


def test_stage_completion_is_bound_to_current_owner_and_cannot_reopen(admitted):
    owner = attach(admitted); stage, ref = finish_zero_dictionary(owner)
    assert stage.closed and len(ref) == 64
    assert (stage.root / 'stage-complete.json').is_file()
    with pytest.raises(ValueError): owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    # No complete representation claim follows while its required MCM is missing.
    with pytest.raises(ValueError): owner.finish()
    assert not (owner.root / 'complete.json').exists()


@pytest.mark.parametrize('reason', ['mcm_first', 'foreign', 'duplicate', 'terminal_run', 'root_extra'])
def test_invalid_or_conflicting_owner_stage_refuses(admitted, reason):
    owner = attach(admitted)
    if reason == 'terminal_run': admitted[0].run.fail('synthetic terminal owner')
    if reason == 'root_extra': (owner.root / 'unadmitted').mkdir()
    if reason == 'duplicate': owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    name = 'mcm-' + 'a' * 64 if reason == 'mcm_first' else ('foreign' if reason == 'foreign' else 'dictionary')
    with pytest.raises(ValueError): owner.begin(name, workload_sha256='d' * 64, pairs=0)


def test_stage_foreign_files_are_refused_and_retained(admitted):
    owner = attach(admitted); stage = owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    bad = stage.root / 'foreign'; bad.write_bytes(b'preserve')
    with pytest.raises(ValueError): stage.lease()
    assert bad.read_bytes() == b'preserve'


@pytest.mark.parametrize('admitted', [6207456], indirect=True)
def test_workflow_logical_budget_applies_cumulatively_before_new_stage(admitted):
    owner = attach(admitted); finish_zero_dictionary(owner)
    assert owner.maximum == owner.reserved
    with pytest.raises(ValueError, match='workflow'):
        owner.begin('mcm-' + 'a' * 64, workload_sha256='b' * 64, pairs=1)
    assert not (owner.root / ('mcm-' + 'a' * 64)).exists()


def test_non_binding_and_unregistered_policy_refused(admitted):
    from tradingagents.research.onchain_replication.compact_owner import attach
    with pytest.raises(ValueError): attach(object(), policy_input='compact_policy')
    with pytest.raises(ValueError): attach(admitted[2], policy_input='sample')
    assert not (admitted[1].directory / 'compact').exists()


def test_runtime_drift_cannot_override_registered_owner_or_stage_contract(admitted):
    owner = attach(admitted)
    for name, value in [('maximum', 10**12), ('reserved', 0), ('required', ('dictionary',))]:
        original = getattr(owner, name); setattr(owner, name, value)
        try:
            with pytest.raises(ValueError): owner.lease()
        finally: setattr(owner, name, original)
    stage = owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    original = stage.pairs; stage.pairs = 1
    try:
        with pytest.raises(ValueError): stage.lease()
    finally: stage.pairs = original


def test_dangling_terminal_markers_revoke_active_compact_lease(admitted):
    owner = attach(admitted)
    for root in (owner.root, admitted[1].directory):
        marker = root / 'failed.json'; marker.symlink_to(root / 'absent')
        try:
            with pytest.raises(ValueError): owner.lease()
        finally: marker.unlink()  # Synthetic injected symlink, never a run artifact.


def test_wrapper_metadata_is_reserved_before_owner_and_stage_creation(admitted):
    owner = attach(admitted)
    assert owner.reserved == 2 * 65536
    stage = owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    assert stage.reservation == 6060000 + 2 * 8192
    assert owner.reserved == 6207456


def test_owner_loss_during_scope_hashing_refuses_before_stage_directory(admitted, monkeypatch):
    from tradingagents.research.onchain_replication import compact_matcher
    owner = attach(admitted); original = compact_matcher.scope
    def scope(*args, **kwargs):
        result = original(*args, **kwargs)
        admitted[0].run.fail('synthetic owner loss during scope hashing')
        return result
    monkeypatch.setattr(compact_matcher, 'scope', scope)
    with pytest.raises(ValueError): owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    assert not (owner.root / 'dictionary').exists()

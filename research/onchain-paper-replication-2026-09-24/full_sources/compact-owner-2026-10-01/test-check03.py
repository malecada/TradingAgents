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
        option = getattr(request, 'param', 30000000)
        full = isinstance(option, dict)
        if full: p['pair']['normalization_chunk_entries'] = 64
        t.policy['limits'] = p['pair']; t.input('pair_policy', t.policy)
        t.descriptor['pair_execution']['policy_sha256'] = t.exp['inputs']['pair_policy']['sha256']
        t.input('compact_policy', {'schema_version': 1, 'backend': p['backend'],
            'stage_policy': p, 'max_workflow_retained_logical_bytes': 30000000 if full else option})
        t.descriptor['compact_execution'] = {'backend': p['backend'],
            'policy_sha256': t.exp['inputs']['compact_policy']['sha256']}
        t.descriptor['configs'] = {'matching': {'max_iterations': 10}}
        if full:
            from tests.research.onchain_replication.test_mcm_score_stream import fixture
            from tradingagents.research.onchain_replication.neighborhoods import graph_hash
            _, numerical, _, _ = fixture()
            t.descriptor['configs']['matching'] = numerical.match
            if not option.get('wrong_graph'): t.descriptor['required_graphs'] = [graph_hash(numerical.g)]
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
        limits=policy['log'], max_iterations=owner.matching['max_iterations'], lease=stage.lease)
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


def completed_mcm(owner):
    from tests.research.onchain_replication.test_mcm_score_stream import fixture, POLICY as MCM_POLICY
    from tradingagents.research.onchain_replication.compact_pair_log import PairLog
    from tradingagents.research.onchain_replication.compact_matcher import CompactMatcher
    from tradingagents.research.onchain_replication.mcm_score_stream import MCMScoreStream
    from tradingagents.research.onchain_replication.neighborhoods import graph_hash, node_order_hash
    from tradingagents.research.onchain_replication.matching_identity import graph_identity
    from tradingagents.research.onchain_replication.cache import cache_key
    _, f, d, kernel = fixture(); p = thaw(owner.policy)
    workflow = owner.bound.record['workflow_identity']
    scope = cache_key({'schema_version': 1, 'kind': 'mcm', 'workflow': workflow,
        'backend': f.kw['backend'], 'graph': graph_hash(f.g), 'node_order': node_order_hash(f.g.node_ids),
        'dictionary': d.identity, 'ordered_motifs': [graph_identity(m) for m in d.representatives],
        'matching': f.match, 'dtype': 'float32'})
    stage = owner.begin(owner.required[1], workload_sha256=scope, pairs=14)
    log = PairLog(stage.root / 'matching', owner=owner.identity, scope=thaw(stage.scope),
        limits=p['log'], max_iterations=f.match['max_iterations'], lease=stage.lease)
    matcher = CompactMatcher(log, config=f.match, context=thaw(owner.bound.context), policy=p['pair'],
        workload_sha256=scope, schedule=p['schedule'], lease=stage.lease)
    stream = MCMScoreStream(stage.root / 'stream', graph=f.g, dictionary=d, matching_config=f.match,
        workflow=workflow, backend=f.kw['backend'], owner=owner.identity, chunk_cells=p['score_chunk_cells'],
        compute=matcher, lease=stage.lease)
    kernel.mcm(f.g, d, f.match, **(f.kw | {'workflow': workflow}), score_pair=stream,
        policy=MCM_POLICY, lease=stage.lease)
    return stage, log.finish(), stream.finish()['terminal_sha256']


@pytest.mark.parametrize('admitted', [{}], indirect=True)
def test_all_required_stage_closure_with_real_mcm_engine(admitted):
    owner = attach(admitted); finish_zero_dictionary(owner)
    stage, log_ref, stream_ref = completed_mcm(owner)
    owner.finish_stage(stage, log_terminal_sha256=log_ref, stream_terminal_sha256=stream_ref)
    ref = owner.finish()
    record = json.loads((owner.root / 'complete.json').read_bytes())
    assert len(ref) == 64 and record['stages'] == 2 and record['pairs'] == 14
    assert record['representation_admitted'] is False and not admitted[1].sealed
    assert owner.closed
    with pytest.raises(ValueError): owner.lease()
    with pytest.raises(ValueError): owner.finish()


@pytest.mark.parametrize('admitted', [{'wrong_graph': True}], indirect=True)
def test_valid_mcm_stream_for_foreign_required_graph_is_refused(admitted):
    owner = attach(admitted); finish_zero_dictionary(owner)
    stage, log_ref, stream_ref = completed_mcm(owner)
    with pytest.raises(ValueError, match='required graph'):
        owner.finish_stage(stage, log_terminal_sha256=log_ref, stream_terminal_sha256=stream_ref)
    assert not (stage.root / 'stage-complete.json').exists()


def test_log_iteration_limit_must_match_registered_matching_config(admitted):
    from tradingagents.research.onchain_replication.compact_pair_log import PairLog
    owner = attach(admitted); stage = owner.begin('dictionary', workload_sha256='d' * 64, pairs=0)
    log = PairLog(stage.root / 'matching', owner=owner.identity, scope=thaw(stage.scope),
        limits=thaw(owner.policy['log']), max_iterations=11, lease=stage.lease)
    (stage.root / 'checkpoints').mkdir()
    with pytest.raises(ValueError, match='iteration'):
        owner.finish_stage(stage, log_terminal_sha256=log.finish(), stream_terminal_sha256=None)
    assert not (stage.root / 'stage-complete.json').exists()

"""Prospective dictionary capacity and exact completion, never fit admission."""
import json
import pytest
from tests.research.onchain_replication import test_first_owner as first
from tests.research.onchain_replication.test_compact_policy import candidate
from tests.research.onchain_replication.test_mcm_score_stream import fixture
from tests.research.onchain_replication.test_compact_workload_integration import dictionary_scope
from tradingagents.research.onchain_replication import compact_owner, compact_policy
from tradingagents.research.onchain_replication.provenance import thaw

MODE = 'capacity-with-exact-completion-v1'


@pytest.fixture
def admitted(request):
    helper = first.Tests(); option = getattr(request, 'param', 'valid')
    base, f, _, _ = fixture()
    def prepare(t):
        p = candidate(); p['pair']['normalization_chunk_entries'] = 64
        t.policy['limits'] = p['pair']; t.input('pair_policy', t.policy)
        t.descriptor['pair_execution']['policy_sha256'] = t.exp['inputs']['pair_policy']['sha256']
        t.input('compact_policy', {'schema_version': 1, 'backend': p['backend'],
            'stage_policy': p, 'max_workflow_retained_logical_bytes': 30000000})
        t.descriptor['compact_execution'] = {'backend': p['backend'],
            'policy_sha256': t.exp['inputs']['compact_policy']['sha256']}
        t.descriptor['configs'] = {'matching': f.match, 'dictionary': f.settings}
        for item in (t.item, t.execution['payload']['representation_jobs']['r']):
            item.update(native_backend=p['backend'], compact_policy_input='compact_policy',
                        compact_dictionary_count_policy=MODE)
        if option == 'route': t.item.pop('compact_dictionary_count_policy')
    t = helper.fixture(prepare); journal, bound = helper.open(t)
    owner = compact_owner.attach(bound, policy_input='compact_policy')
    f.kw['workflow'] = bound.record['workflow_identity']
    try: yield owner, f, base
    finally: helper.doCleanups()


def dictionary_log(owner, f, *, bounded=True):
    from tradingagents.research.onchain_replication.compact_pair_log import PairLog
    from tradingagents.research.onchain_replication.compact_matcher import CompactMatcher
    scope = dictionary_scope(f)
    stage = owner.begin_dictionary(workload_sha256=scope) if bounded else owner.begin(
        'dictionary', workload_sha256=scope, pairs=30)
    p = thaw(owner.policy)
    log = PairLog(stage.root / 'matching', owner=owner.identity, scope=thaw(stage.scope),
        limits=p['log'], max_iterations=f.match['max_iterations'], lease=stage.lease)
    matcher = CompactMatcher(log, config=f.match, context=thaw(owner.bound.context), policy=p['pair'],
        workload_sha256=scope, schedule=p['schedule'], lease=stage.lease)
    return stage, log, matcher


def test_actual_dictionary_completes_with_separate_reserved_and_observed_counts(admitted):
    owner, f, base = admitted
    stage, log, matcher = dictionary_log(owner, f)
    before = owner.reserved
    actual = f.fit(matcher); count = log.state['completed_pairs']
    owner.finish_stage(stage, log_terminal_sha256=log.finish(), stream_terminal_sha256=None,
                       completed_pairs=count)
    intent = json.loads((stage.root / 'intent.json').read_bytes())
    receipt = json.loads((stage.root / 'stage-complete.json').read_bytes())
    assert intent['pair_count_policy']['name'] == MODE and intent['pairs'] == 30
    assert intent['pair_count_policy']['capacity']['max_matrix_entries'] == 41
    assert receipt['completed_pairs'] == count <= intent['pairs']
    assert stage.closed and owner.reserved == before
    assert actual['dictionary'].identity == f.fit(base.Scores(f.match))['dictionary'].identity
    assert receipt['execution_admitted'] is False


@pytest.mark.parametrize('admitted', ['route'], indirect=True)
def test_unselected_dictionary_count_policy_refuses_before_namespace(admitted):
    owner, f, _ = admitted
    with pytest.raises(ValueError): owner.begin_dictionary(workload_sha256=dictionary_scope(f))
    assert not (owner.root / 'dictionary').exists()


@pytest.mark.parametrize('count', [None, True, -1, 31])
def test_dictionary_capacity_is_not_an_implicit_completion_count(admitted, count):
    owner, f, _ = admitted
    stage, log, matcher = dictionary_log(owner, f)
    ref = log.finish()  # Empty synthetic log is not scientific dictionary completion.
    with pytest.raises(ValueError):
        owner.finish_stage(stage, log_terminal_sha256=ref, stream_terminal_sha256=None,
                           completed_pairs=count)
    assert not (stage.root / 'stage-complete.json').exists()


def test_exact_stage_cannot_opt_into_a_smaller_denominator_at_seal(admitted):
    owner, f, _ = admitted
    stage, log, matcher = dictionary_log(owner, f, bounded=False)
    with pytest.raises(ValueError):
        owner.finish_stage(stage, log_terminal_sha256=log.finish(), stream_terminal_sha256=None,
                           completed_pairs=0)
    assert not (stage.root / 'stage-complete.json').exists()

"""Prospective dictionary capacity and exact completion, never fit admission."""
import json
import pytest
from tests.research.onchain_replication import test_first_owner as first
from tests.research.onchain_replication.test_compact_policy import candidate
from tests.research.onchain_replication.test_mcm_score_stream import fixture
from tests.research.onchain_replication.test_compact_workload_integration import dictionary_scope
from tradingagents.research.onchain_replication import compact_owner
from tradingagents.research.onchain_replication.neighborhoods import sample_neighborhoods, graph_hash, node_order_hash
from tests.research.onchain_replication.test_matching_reference import graph
from tradingagents.research.onchain_replication.provenance import thaw

MODE = 'capacity-with-exact-completion-v1'


@pytest.fixture
def admitted(request):
    helper = first.Tests(); option = getattr(request, 'param', 'valid')
    base, f, _, _ = fixture()
    # Constant-feature isolated neighborhoods make actual scalar scores equal.
    # Seed12 causes the final [0,4] subset to reuse an earlier complete matrix.
    f.g = graph([[1.]] * 5, [])
    f.settings = f.settings | dict(sample_count=5, size=2, partition_threshold=2, partition_size=3)
    f.samples = sample_neighborhoods([f.g], f.settings, 12)
    def prepare(t):
        p = candidate(); p['pair']['normalization_chunk_entries'] = 64
        t.policy['limits'] = p['pair']; t.input('pair_policy', t.policy)
        t.descriptor['pair_execution']['policy_sha256'] = t.exp['inputs']['pair_policy']['sha256']
        t.input('compact_policy', {'schema_version': 1, 'backend': p['backend'],
            'stage_policy': p, 'max_workflow_retained_logical_bytes': 30000000})
        t.descriptor['compact_execution'] = {'backend': p['backend'],
            'policy_sha256': t.exp['inputs']['compact_policy']['sha256']}
        t.descriptor['configs'] = {'matching': f.match, 'dictionary': f.settings}
        t.descriptor['seed'] = 12
        t.descriptor['required_graphs'] = [graph_hash(f.g)]
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
        'dictionary', workload_sha256=scope, pairs=22)
    p = thaw(owner.policy)
    log = PairLog(stage.root / 'matching', owner=owner.identity, scope=thaw(stage.scope),
        limits=p['log'], max_iterations=f.match['max_iterations'], lease=stage.lease)
    matcher = CompactMatcher(log, config=f.match, context=thaw(owner.bound.context), policy=p['pair'],
        workload_sha256=scope, schedule=p['schedule'], lease=stage.lease)
    return stage, log, matcher


def test_actual_dictionary_completes_with_separate_reserved_and_observed_counts(admitted):
    owner, f, base = admitted
    selected = json.loads(owner.bound._run.read_input('execution_job'))['payload']['representation_jobs']['r']
    assert selected['descriptor']['seed'] == f.samples.seed == 12
    stage, log, matcher = dictionary_log(owner, f)
    before = owner.reserved
    actual = f.fit(matcher); count = log.state['completed_pairs']
    owner.finish_stage(stage, log_terminal_sha256=log.finish(), stream_terminal_sha256=None,
                       completed_pairs=count)
    intent = json.loads((stage.root / 'intent.json').read_bytes())
    receipt = json.loads((stage.root / 'stage-complete.json').read_bytes())
    assert intent['pair_count_policy']['name'] == MODE and intent['pairs'] == 22
    assert intent['pair_count_policy']['capacity']['max_matrix_entries'] == 36
    assert receipt['completed_pairs'] == count == 20 < intent['pairs']
    assert sum(x['matrix'].size for x in actual['matrices']) == 32
    assert stage.closed and owner.reserved == before
    assert actual['dictionary'].identity == f.fit(base.Scores(f.match))['dictionary'].identity
    assert receipt['execution_admitted'] is False
    # Complete the required MCM with the actual produced dictionary, then prove
    # aggregate accounting uses20+10actual pairs rather than22+10capacity.
    from tradingagents.research.onchain_replication.compact_pair_log import PairLog
    from tradingagents.research.onchain_replication.compact_matcher import CompactMatcher
    from tradingagents.research.onchain_replication.mcm_score_stream import MCMScoreStream
    from tradingagents.research.onchain_replication.matching_identity import graph_identity
    from tradingagents.research.onchain_replication.cache import cache_key
    from tests.research.onchain_replication.test_mcm_score_stream import POLICY as MCM_POLICY
    _, _, _, kernel = fixture(); d = actual['dictionary']; p = thaw(owner.policy)
    workload = cache_key({'schema_version': 1, 'kind': 'mcm', 'workflow': f.kw['workflow'],
        'backend': f.kw['backend'], 'graph': graph_hash(f.g), 'node_order': node_order_hash(f.g.node_ids),
        'dictionary': d.identity, 'ordered_motifs': [graph_identity(m) for m in d.representatives],
        'matching': f.match, 'dtype': 'float32'})
    mcm = owner.begin('mcm-' + graph_hash(f.g), workload_sha256=workload, pairs=10)
    log = PairLog(mcm.root / 'matching', owner=owner.identity, scope=thaw(mcm.scope),
        limits=p['log'], max_iterations=f.match['max_iterations'], lease=mcm.lease)
    matcher = CompactMatcher(log, config=f.match, context=thaw(owner.bound.context), policy=p['pair'],
        workload_sha256=workload, schedule=p['schedule'], lease=mcm.lease)
    stream = MCMScoreStream(mcm.root / 'stream', graph=f.g, dictionary=d, matching_config=f.match,
        workflow=f.kw['workflow'], backend=f.kw['backend'], owner=owner.identity,
        chunk_cells=p['score_chunk_cells'], compute=matcher, lease=mcm.lease)
    kernel.mcm(f.g, d, f.match, **f.kw, score_pair=stream, policy=MCM_POLICY, lease=mcm.lease)
    owner.finish_stage(mcm, log_terminal_sha256=log.finish(),
                       stream_terminal_sha256=stream.finish()['terminal_sha256'])
    owner.finish()
    final = json.loads((owner.root / 'complete.json').read_bytes())
    assert final['pairs'] == 30 and final['stages'] == 2 and final['representation_admitted'] is False


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


def test_in_range_false_completion_count_refuses_at_saved_log_join(admitted):
    owner, f, _ = admitted
    stage, log, matcher = dictionary_log(owner, f)
    with pytest.raises(ValueError, match='denominator'):
        owner.finish_stage(stage, log_terminal_sha256=log.finish(), stream_terminal_sha256=None,
                           completed_pairs=1)
    assert owner.poisoned and not (stage.root / 'stage-complete.json').exists()

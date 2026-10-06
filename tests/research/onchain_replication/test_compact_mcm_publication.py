"""Registered output-policy joins with actual first-owner synthetic claims."""
import json
from contextlib import contextmanager
from pathlib import Path
import pytest
from tests.research.onchain_replication import test_first_owner as first
from tests.research.onchain_replication.test_compact_owner import finish_zero_dictionary, completed_mcm
from tests.research.onchain_replication.test_compact_policy import candidate
from tests.research.onchain_replication.test_mcm_score_stream import fixture
from tradingagents.research.onchain_replication import compact_owner
from tradingagents.research.onchain_replication.neighborhoods import graph_hash


@pytest.fixture
def ready(request):
    helper = first.Tests(); mode = getattr(request, 'param', 'valid')
    def prepare(t):
        _, f, _, _ = fixture(); p = candidate(); p['pair']['normalization_chunk_entries'] = 64
        t.policy['limits'] = p['pair']; t.input('pair_policy', t.policy)
        t.descriptor['pair_execution']['policy_sha256'] = t.exp['inputs']['pair_policy']['sha256']
        t.input('compact_policy', {'schema_version': 1, 'backend': p['backend'],
            'stage_policy': p, 'max_workflow_retained_logical_bytes': 30000000})
        t.input('compact_output', {'schema_version': 1, 'backend': p['backend'],
            'max_artifact_bytes': 8248, 'max_workflow_output_bytes': 16439 if mode == 'budget' else 16440})
        t.descriptor['compact_execution'] = {'backend': p['backend'],
            'policy_sha256': t.exp['inputs']['compact_policy']['sha256']}
        t.descriptor['configs'] = {'matching': f.match}
        t.descriptor['required_graphs'] = [graph_hash(f.g)]
        for item in (t.item, t.execution['payload']['representation_jobs']['r']):
            item.update(native_backend=p['backend'], compact_policy_input='compact_policy',
                        compact_mcm_output_input='compact_output')
        if mode == 'route': t.item['compact_mcm_output_input'] = 'sample'
    t = helper.fixture(prepare); journal, bound = helper.open(t)
    owner = compact_owner.attach(bound, policy_input='compact_policy')
    finish_zero_dictionary(owner)
    stage, log, stream = completed_mcm(owner)
    owner.finish_stage(stage, log_terminal_sha256=log, stream_terminal_sha256=stream)
    scope = json.loads((stage.root / 'stream/start.json').read_bytes())['scope']
    try: yield owner, stage, scope, t
    finally: helper.doCleanups()


def test_current_registered_owner_publishes_reads_and_closes_without_representation_claim(ready):
    from tradingagents.research.onchain_replication import compact_mcm_publication as api
    owner, stage, scope, t = ready
    ticket = api.publish(owner, stage, output_input='compact_output', expected_scope=scope)
    proof = api.verify(owner, stage, output_input='compact_output', expected_scope=scope,
                       receipt_sha256=ticket['receipt_sha256'])
    assert proof['representation_admitted'] is False and proof['workflow_reserved_output_bytes'] == 16440
    assert proof['claim_sha256'] == t.run._claim_sha256
    with api.open_verified(owner, stage, output_input='compact_output', expected_scope=scope,
                           receipt_sha256=ticket['receipt_sha256']) as matrix:
        assert matrix.shape == (7, 2) and not matrix.flags.writeable
    owner.finish()
    assert owner.closed
    with pytest.raises(ValueError): api.publish(owner, stage, output_input='compact_output', expected_scope=scope)


def test_duplicate_publication_poisons_owner_and_forbids_completion(ready):
    from tradingagents.research.onchain_replication import compact_mcm_publication as api
    owner, stage, scope, _ = ready
    api.publish(owner, stage, output_input='compact_output', expected_scope=scope)
    with pytest.raises(ValueError):
        api.publish(owner, stage, output_input='compact_output', expected_scope=scope)
    assert owner.poisoned and not owner.closed
    with pytest.raises(ValueError, match='terminal or poisoned'): owner.finish()


@pytest.mark.parametrize('ready', ['route', 'budget'], indirect=True)
def test_unselected_or_underreserved_output_refused_before_namespace(ready):
    from tradingagents.research.onchain_replication import compact_mcm_publication as api
    owner, stage, scope, t = ready
    with pytest.raises(ValueError): api.publish(owner, stage, output_input='compact_output', expected_scope=scope)
    assert not (t.root / 'research_artifacts/onchain_compact_outputs').exists()


def test_foreign_stage_scope_and_terminal_claim_cannot_publish(ready):
    from tradingagents.research.onchain_replication import compact_mcm_publication as api
    owner, stage, scope, t = ready
    with pytest.raises(ValueError):
        api.publish(owner, stage, output_input='compact_output', expected_scope=scope | {'graph': 'a' * 64})
    t.run.fail('synthetic revoked output owner')
    with pytest.raises(ValueError): api.publish(owner, stage, output_input='compact_output', expected_scope=scope)
    assert not (t.root / 'research_artifacts/onchain_compact_outputs').exists()


@pytest.mark.parametrize('target', ['receipt', 'inventory'])
def test_last_nested_exit_lease_cannot_change_wrapper_evidence(ready, monkeypatch, target):
    from tradingagents.research.onchain_replication import compact_mcm_publication as api
    owner, stage, scope, t = ready
    ticket = api.publish(owner, stage, output_input='compact_output', expected_scope=scope)
    original = api.output.open_verified
    @contextmanager
    def injected(*args, lease, **kwargs):
        exiting = False
        def late_lease():
            lease()
            if exiting:
                root = Path(ticket['directory'])
                if target == 'receipt': (root / 'receipt.json').write_bytes(b'{}')
                else: (root / 'orphan').write_bytes(b'preserve')
        with original(*args, lease=late_lease, **kwargs) as matrix:
            yield matrix
            exiting = True
    monkeypatch.setattr(api.output, 'open_verified', injected)
    with pytest.raises(ValueError):
        with api.open_verified(owner, stage, output_input='compact_output', expected_scope=scope,
                               receipt_sha256=ticket['receipt_sha256']) as matrix:
            assert matrix.shape == (7, 2)

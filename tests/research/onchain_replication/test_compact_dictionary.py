"""Actual scientific samples through compact dictionary production/publication."""
from pathlib import Path
from types import SimpleNamespace
import json
import shutil
import numpy as np
import pytest
from tests.research.test_lifecycle import git
from tests.research.onchain_replication import test_compact_sample_proof as samples
from tradingagents.research.onchain_replication.provenance import file_hash, thaw
from tradingagents.research.onchain_replication.dictionary import fit_dictionary
from tradingagents.research.onchain_replication.matching_reference import match_reference

ROOT = Path(__file__).resolve().parents[3]
KERNEL = 'research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-2026-09-30/workload.py'


@pytest.fixture
def admitted(request, monkeypatch):
    training = samples.publication.sampling.training
    original = training.first.Tests.fixture; configs = training.configs; candidate = training.candidate
    option = getattr(request, 'param', 'valid')
    def config():
        value = configs(); value['matching']['beta_final'] = 1.; return value
    def compact():
        value = candidate(); value['pair']['normalization_chunk_entries'] = 64; return value
    monkeypatch.setattr(training, 'configs', config); monkeypatch.setattr(training, 'candidate', compact)
    def fixture(helper, mutate):
        def prepare(t):
            mutate(t)
            policy = dict(schema_version=1, max_matrix_bytes=65536, max_identity_array_bytes=65536,
                max_manifest_bytes=65536, max_artifact_bytes=1000000,
                max_loaded_array_bytes=65536, max_attempt_bytes=1000000 + 3*8192)
            if option == 'budget': policy['max_attempt_bytes'] -= 1
            if option == 'matrix': policy['max_matrix_bytes'] = 1
            if option == 'identity': policy['max_identity_array_bytes'] = 1
            t.input('compact_dictionary', policy)
            for item in (t.item, t.execution['payload']['representation_jobs']['r']):
                item.update(compact_dictionary_input='compact_dictionary',
                    compact_dictionary_count_policy='capacity-with-exact-completion-v1')
            if option == 'route': t.item['compact_dictionary_input'] = 'sample'
            target = t.root / KERNEL; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / KERNEL, target); git(t.root, 'add', '--', KERNEL)
            if option != 'source': t.exp['source_files'][KERNEL] = file_hash(target)
        return original(helper, prepare)
    monkeypatch.setattr(training.first.Tests, 'fixture', fixture)
    gen = samples.admitted.__wrapped__(SimpleNamespace(param='valid'), monkeypatch)
    published, t = next(gen)
    try: yield samples.api().admit(published), t
    finally:
        try: next(gen)
        except StopIteration: pass


def api():
    from tradingagents.research.onchain_replication import compact_dictionary
    return compact_dictionary


def test_actual_dictionary_publishes_exact_oracle_and_matrix_scores(admitted):
    proof, t = admitted; m = api(); route = proof._published._draws._training
    match = thaw(proof.owner.matching); settings = thaw(route.settings)
    oracle = fit_dictionary(proof.samples, match, settings)
    result = m.produce(proof, input_name='compact_dictionary'); result.check()
    d = result.dictionary
    assert d.memberships == oracle.memberships and d.hierarchy == oracle.hierarchy
    for a, b in zip(d.representatives, oracle.representatives, strict=True): assert a is b
    matrix = result.matrices[0]['matrix']; n = len(proof.samples.graphs)
    expected = np.zeros((n,n))
    for i in range(n):
        for j in range(i):
            a,b = proof.samples.graphs[i],proof.samples.graphs[j]
            expected[i,j] = expected[j,i] = 1-(match_reference(a,b,match).score+match_reference(b,a,match).score)/2
    np.testing.assert_array_equal(matrix, expected)
    assert result.record['completed_pairs'] == n*(n-1) == 6
    assert result.record['workload_sha256'] == proof.scope
    assert result.record['sample_provenance_admitted'] is True
    assert result.record['representation_admitted'] is False
    assert proof.owner.stages['dictionary'].closed
    assert (result.directory/'artifact/manifest.json').is_file()
    with pytest.raises(ValueError): m.produce(proof, input_name='compact_dictionary')


@pytest.mark.parametrize('admitted', ['budget','matrix','identity','route','source'], indirect=True)
def test_preflight_refusals_do_not_claim_dictionary_stage(admitted):
    proof,t = admitted; m = api()
    with pytest.raises(ValueError): m.produce(proof, input_name='compact_dictionary')
    assert not proof.owner.stages and not m.directory(proof).exists()
    assert not proof.owner.poisoned


def test_second_direction_failure_preserves_first_score_and_revokes_owner(admitted, monkeypatch):
    proof,t = admitted; m = api(); original = m.compact_matcher.engine.create; calls = []
    def create(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2: raise OSError('synthetic reverse failure')
        return original(*args, **kwargs)
    monkeypatch.setattr(m.compact_matcher.engine, 'create', create)
    with pytest.raises(OSError, match='reverse'): m.produce(proof, input_name='compact_dictionary')
    terminal = json.loads((proof.owner.root/'dictionary/matching/terminal.json').read_bytes())
    assert terminal['status'] == 'failed' and terminal['state']['completed_pairs'] == 1
    assert (m.directory(proof)/'failed.json').exists() and proof.owner.poisoned
    with pytest.raises(ValueError): m.produce(proof, input_name='compact_dictionary')
    assert len(calls) == 2


def test_saved_or_resident_matrix_drift_is_refused(admitted):
    proof,t = admitted; m = api(); result = m.produce(proof, input_name='compact_dictionary')
    result.matrices[0]['matrix'][0,1] += .1
    with pytest.raises(ValueError): result.check()


def test_last_lease_sample_mutation_cannot_publish_dictionary(admitted, monkeypatch):
    proof,t = admitted; m = api(); original = proof.lease
    def changed():
        original()
        if (m.directory(proof)/'complete.json').exists():
            g = proof.samples.graphs[0]; object.__setattr__(g,'node_features',g.node_features+1)
    monkeypatch.setattr(proof,'lease',changed)
    with pytest.raises(ValueError): m.produce(proof,input_name='compact_dictionary')
    assert proof.owner.poisoned and (m.directory(proof)/'failed.json').exists()


def test_completed_stage_foreign_marker_revokes_dictionary(admitted):
    proof,t = admitted; m = api(); result = m.produce(proof,input_name='compact_dictionary')
    (proof.owner.root/'dictionary/failed.json').write_bytes(b'{}')
    with pytest.raises(ValueError,match='inventory'): result.check()


def test_double_log_cleanup_failure_still_revokes_owner_and_preserves_attempt(admitted, monkeypatch):
    proof,t = admitted; m = api(); close = m.compact_pair_log.PairLog.close
    def fail(*args): raise OSError('synthetic fail terminal failure')
    def broken_close(log): close(log); raise OSError('synthetic close failure')
    def create(*args,**kwargs): raise RuntimeError('synthetic primary numerical failure')
    monkeypatch.setattr(m.compact_pair_log.PairLog,'fail',fail)
    monkeypatch.setattr(m.compact_pair_log.PairLog,'close',broken_close)
    monkeypatch.setattr(m.compact_matcher.engine,'create',create)
    with pytest.raises(m.compact_matcher.CleanupFailure) as caught: m.produce(proof,input_name='compact_dictionary')
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert proof.owner.poisoned, 'cleanup bypassed owner revocation'
    assert (m.directory(proof)/'failed.json').is_file(), 'cleanup bypassed failure receipt'


def test_owner_revoked_during_parent_setup_cannot_claim_output_directory(admitted, monkeypatch):
    proof,t = admitted; m = api(); mkdir = m.durable_mkdir
    def revoke(path): mkdir(path); t.run.fail('synthetic owner revocation during parent preparation')
    monkeypatch.setattr(m,'durable_mkdir',revoke)
    with pytest.raises(ValueError): m.produce(proof,input_name='compact_dictionary')
    assert not m.directory(proof).exists(), 'stale owner created attempt directory'

"""Current-owner sample provenance and independent semantic refusals."""
from dataclasses import replace
import copy
import pytest
from tests.research.onchain_replication import test_compact_samples as publication
from tradingagents.research.onchain_replication.provenance import thaw
from tradingagents.research.onchain_replication.cache import cache_key


@pytest.fixture
def admitted(request, monkeypatch):
    fixture = publication.admitted.__wrapped__(request, monkeypatch)
    draws, t = next(fixture)
    try: yield publication.api().publish(draws, input_name='compact_samples'), t
    finally:
        try: next(fixture)
        except StopIteration: pass


def api():
    from tradingagents.research.onchain_replication import compact_sample_proof
    return compact_sample_proof


def test_actual_published_samples_admit_exact_dictionary_scope_without_new_sample(admitted, monkeypatch):
    published, t = admitted; m = api()
    monkeypatch.setattr(publication.sampling.api(), '_kernel', lambda: (_ for _ in ()).throw(AssertionError('no sampler replay')))
    proof = m.admit(published); proof.check(); proof.lease()
    assert proof.samples is published.samples
    assert proof.record['sample_provenance_admitted'] is True
    assert proof.record['publication_sha256'] == published.receipt_sha256
    assert len(proof.scope) == 64
    assert proof.record['weighted_draws_verified'] == 3
    assert proof.record['induced_neighborhoods_verified'] == 3
    assert proof.record['complete_calendar_admitted'] is False
    assert not published._draws._training.owner.stages


def test_audit_independently_refuses_changed_semantics_even_with_recomputed_sample_identity(admitted):
    published, t = admitted; m = api(); draws = published._draws; route = draws._training
    events = m._events(draws); samples = published.samples; policy = thaw(draws._policy)
    def audit(value, saved): return m._audit(route, value, saved, policy, lease=lambda: None)
    result = audit(samples, events); assert result['weighted_draws_verified'] == 3
    cfg = thaw(route.settings)
    def identity(value):
        return replace(value, identity=cache_key({'training_graphs': value.source_hashes, 'config': cfg,
            'seed': value.seed, 'records': value.records, 'rng_state': value.rng_state}))
    records = thaw(samples.records); records[0]['probability'] *= .5
    changed = identity(replace(samples, records=tuple(records)))
    saved = copy.deepcopy(events); saved[0]['record'] = records[0]
    with pytest.raises(ValueError, match='probability'): audit(changed, saved)
    g = samples.graphs[0]; changed = replace(samples, graphs=(replace(g, node_features=g.node_features + 1), *samples.graphs[1:]))
    with pytest.raises(ValueError, match='induced'): audit(changed, events)
    for key, value, reason in [('selected_indices_sha256', 'f'*64, 'selected'), ('retained_array_bytes', 1, 'retained')]:
        saved = copy.deepcopy(events); saved[0][key] = value
        with pytest.raises(ValueError, match=reason): audit(samples, saved)
    with pytest.raises(ValueError, match='identity'): audit(replace(samples, identity='f'*64), events)


def test_terminal_and_arbitrary_sample_objects_cannot_get_proof(admitted):
    published, t = admitted; m = api()
    with pytest.raises(ValueError): m.admit(published.samples)
    proof = m.admit(published)
    t.run.fail('synthetic proof owner closure')
    with pytest.raises(ValueError): proof.lease()


def test_final_proof_callback_cannot_change_sample_or_parent(admitted, monkeypatch):
    published, t = admitted; m = api(); proof = m.admit(published); original = published.lease
    def changed():
        original(); g = published._draws._training.training_graphs[0]
        object.__setattr__(g, 'node_features', g.node_features + 1)
    monkeypatch.setattr(published, 'lease', changed)
    with pytest.raises(ValueError): proof.check()

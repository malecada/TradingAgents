import json
from pathlib import Path
import uuid

import numpy as np
import pytest

from tradingagents.research.onchain_replication.feature_journal import FeatureJournal, read_feature_journal
from tradingagents.research.onchain_replication.journal_recovery import reconcile_feature_journal
from tradingagents.research.onchain_replication.provenance import file_hash


def setup(tmp_path):
    owner = {'experiment': 'synthetic-killed', 'source_commit': 'a'*40,
             'producer': 'motif-11', 'workflow_identity': 'b'*64}
    directory = tmp_path/'research_artifacts/onchain_representations'/owner['workflow_identity']/owner['experiment']
    journal = FeatureJournal(directory, owner, required_graphs=['c'*64])
    journal('graph_complete', {'workflow_identity': 'b'*64, 'graph_hash': 'c'*64},
            {'feature': np.ones(32), 'aligned_vectors': None})
    # A second component write was interrupted before its durable event.
    (directory/'checkpoint-000001').mkdir()
    (directory/'checkpoint-000001/partial.bin').write_bytes(b'preserve me')
    run = tmp_path/'research_runs'/owner['experiment']
    run.mkdir(parents=True)
    (run/'claim.json').write_text(json.dumps({'source': owner['source_commit'], 'experiment_id': owner['experiment']}))
    (run/'failed.json').write_text(json.dumps({'status': 'failed', 'experiment_id': owner['experiment'],
        'claim_sha256': file_hash(run/'claim.json'), 'reason': 'synthetic killed worker',
        'ended_at': '2026-09-24T00:00:00Z', 'output_sha256': {}}))
    base = tmp_path/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/owner['experiment']
    (base/'guard').mkdir(parents=True)
    launch = {'experiment': owner['experiment'], 'source_commit': owner['source_commit'], 'nonce': 'fixture', 'monitor_pid': 1}
    (base/'owner.json').write_text(json.dumps(launch))
    unit = 'onchain-replication-'+uuid.uuid4().hex+'.service'
    guard = {'owner_identity': launch, 'monitor_pid': 1, 'cleanup_verified': True, 'phase': 'failed',
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'unit': unit, 'cgroup': '/sys/fs/cgroup/'+unit}
    (base/'guard/final.json').write_text(json.dumps(guard))
    proof = {'claim_sha256': file_hash(run/'claim.json'), 'failed_sha256': file_hash(run/'failed.json'),
             'owner_sha256': file_hash(base/'owner.json'), 'guard_sha256': file_hash(base/'guard/final.json'),
             'start_sha256': file_hash(directory/'start.json')}
    return owner, directory, proof, base


def test_unsealed_journal_recovers_only_durable_prefix_without_recomputing(tmp_path):
    owner, directory, proof, _ = setup(tmp_path)
    path = reconcile_feature_journal(tmp_path, directory, owner, proof, max_array_bytes=4096)
    assert path.name == 'failed.json'
    state, binding = read_feature_journal(path, file_hash(path), owner, required_graphs=['c'*64], max_array_bytes=4096)
    np.testing.assert_array_equal(state['completed_graphs']['c'*64]['feature'], np.ones(32))
    assert binding is None
    assert (directory/'checkpoint-000001/partial.bin').read_bytes() == b'preserve me'
    evidence = json.loads((directory/'recovery-evidence.json').read_bytes())
    assert evidence['retained_unpublished_components'] == ['checkpoint-000001']
    assert not evidence['computation_repeated'] and not evidence['continuation_admitted']
    with pytest.raises(FileExistsError, match='terminal'):
        reconcile_feature_journal(tmp_path, directory, owner, proof, max_array_bytes=4096)


@pytest.mark.parametrize('fault', ['live', 'wrong_owner', 'event_gap', 'corrupt_component'])
def test_unproven_death_or_broken_journal_does_not_create_terminal(tmp_path, fault):
    owner, directory, proof, base = setup(tmp_path)
    if fault in ('live', 'wrong_owner'):
        path = base/'guard/final.json'
        guard = json.loads(path.read_bytes())
        if fault == 'live':
            guard['cleanup_verified'] = False
        else:
            guard['owner_identity']['experiment'] = 'other-owner'
        path.write_text(json.dumps(guard))
        proof['guard_sha256'] = file_hash(path)
    elif fault == 'event_gap':
        (directory/'event-000000.json').rename(directory/'event-000001.json')
    else:
        path = directory/'checkpoint-000000/manifest.json'
        path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):
        reconcile_feature_journal(tmp_path, directory, owner, proof, max_array_bytes=4096)
    assert not (directory/'failed.json').exists() and not (directory/'complete.json').exists()


@pytest.mark.parametrize('after', ['recovery-candidate.json', 'recovery-evidence.json'])
def test_interrupted_observer_finishes_identical_publication_without_work(tmp_path, monkeypatch, after):
    import tradingagents.research.onchain_replication.journal_recovery as module
    owner, directory, proof, _ = setup(tmp_path)
    actual = module._immutable
    def interrupted(path, record):
        actual(path, record)
        if path.name == after:
            raise InterruptedError('synthetic observer interruption')
    monkeypatch.setattr(module, '_immutable', interrupted)
    with pytest.raises(InterruptedError):
        reconcile_feature_journal(tmp_path, directory, owner, proof, max_array_bytes=4096)
    retained_hash = file_hash(directory/after)
    monkeypatch.setattr(module, '_immutable', actual)
    path = reconcile_feature_journal(tmp_path, directory, owner, proof, max_array_bytes=4096)
    assert path.name == 'failed.json' and file_hash(directory/after) == retained_hash


@pytest.mark.parametrize('field,value', [('status', 'complete'), ('experiment_id', 'unrelated'), ('claim_sha256', 'f'*64)])
def test_failed_terminal_must_bind_exact_claim(tmp_path, field, value):
    owner, directory, proof, _ = setup(tmp_path)
    path = tmp_path/'research_runs'/owner['experiment']/'failed.json'
    failed = json.loads(path.read_bytes())
    failed[field] = value
    path.write_text(json.dumps(failed))
    proof['failed_sha256'] = file_hash(path)
    with pytest.raises(ValueError, match='exact owner claim'):
        reconcile_feature_journal(tmp_path, directory, owner, proof, max_array_bytes=4096)
    assert not (directory/'recovery-candidate.json').exists()

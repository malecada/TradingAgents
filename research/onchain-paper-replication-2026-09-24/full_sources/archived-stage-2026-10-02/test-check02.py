"""Actual tiny dictionary/MCM archived joins, independent fresh attempts."""
import hashlib
import json
import pytest

from tests.research.onchain_replication.test_archive_chunks import Transport
from tests.research.onchain_replication.test_compact_stage import completed
from tests.research.onchain_replication import test_compact_stage as local_fixture
from tradingagents.research.onchain_replication import archive_pair_writer as writer


def fixture(tmp_path, monkeypatch, kind='mcm', wrong_score=False):
    from tradingagents.research.onchain_replication import archived_stage as module
    root = tmp_path/'source'; root.mkdir()
    transport = Transport(tmp_path/'remote'); captured = {}
    original = local_fixture.consumer
    # Explicitly replace only the fixture's constructor, never a production reader.
    def consumer(root, f, workload, schedule):
        from tests.research.onchain_replication.test_compact_matcher import CONTEXT, POLICY
        from tradingagents.research.onchain_replication import compact_matcher as matcher
        pair_policy = POLICY | {'normalization_chunk_entries':64}
        limits = {'chunk_events':3,'max_events':200,'max_pairs':64,'max_logical_bytes':60000}
        policy = {'schema_version':1,'remote_prefix':'stage-fixture','transport_identity':transport.identity,
            'max_chunks':67,'max_metadata_bytes':(7*67+8)*writer.io.META_LIMIT,'local_free_floor_bytes':10*1024**3}
        log = writer.ArchivePairLog(root/'matching',owner='e'*64,
            scope=matcher.scope(f.match,CONTEXT,pair_policy,workload,schedule),limits=limits,
            max_iterations=f.match['max_iterations'],lease=lambda:None,transport=transport,archive_policy=policy)
        captured.update(log=log,policy=policy)
        return matcher.CompactMatcher(log,config=f.match,context=CONTEXT,policy=pair_policy,
            workload_sha256=workload,schedule=schedule,lease=lambda:None),log
    monkeypatch.setattr(local_fixture,'consumer',consumer)
    contract = completed(root,kind,monkeypatch,progress=True,wrong_score=wrong_score)
    monkeypatch.setattr(local_fixture,'consumer',original)
    budget = (3*67+8)*writer.io.META_LIMIT
    return module,root,dict(**contract,archive_complete_sha256=captured['log'].archive_complete_sha,
        archive_policy=captured['policy'],transport=transport,attempt=tmp_path/'stage01',
        max_read_metadata_bytes=budget,max_stage_bytes=budget+40*128+8*writer.io.META_LIMIT,lease=lambda:None)


@pytest.mark.parametrize('kind',['dictionary','mcm'])
def test_actual_archived_stage_joins_checkpoints_and_full_score_stream(tmp_path,monkeypatch,kind):
    module,root,contract = fixture(tmp_path,monkeypatch,kind)
    result = module.verify(root,**contract)
    assert result['completed_pairs'] == contract['pairs'] and result['checkpoints'] > 0
    assert result['checkpoint_logical_bytes'] > 0 and result['execution_admitted'] is False
    assert result['archive_complete_sha256'] == contract['archive_complete_sha256']
    assert (contract['attempt']/'checkpoint-references.bin').stat().st_size == 40*result['checkpoints']
    saved = (contract['attempt']/'complete.json').read_bytes()
    assert json.loads(saved) == result
    with pytest.raises((ValueError,FileExistsError)): module.verify(root,**contract)
    assert (contract['attempt']/'complete.json').read_bytes() == saved
    assert not (contract['attempt']/'failed.json').exists()


@pytest.mark.parametrize('target',['checkpoint','score','extra_checkpoint','denominator'])
def test_corruption_or_wrong_denominator_cannot_complete(tmp_path,monkeypatch,target):
    module,root,contract = fixture(tmp_path,monkeypatch)
    if target == 'checkpoint':
        path = next((root/'checkpoints').glob('*/state/annealing/M.npy'));path.write_bytes(b'x'*path.stat().st_size)
    if target == 'score': (root/'stream/batches/chunk-000000000000.bin').write_bytes(b'x'*32)
    if target == 'extra_checkpoint': (root/'checkpoints/orphan').mkdir()
    if target == 'denominator': contract['pairs'] += 1
    with pytest.raises(ValueError): module.verify(root,**contract)
    assert not (contract['attempt']/'complete.json').exists()


def test_valid_score_stream_with_wrong_score_refuses_exact_event_join(tmp_path,monkeypatch):
    module,root,contract = fixture(tmp_path,monkeypatch,wrong_score=True)
    with pytest.raises(ValueError,match='score'): module.verify(root,**contract)


@pytest.mark.parametrize('target',['checkpoint','score','reference','source','read'])
def test_final_callback_mutation_refuses_return(tmp_path,monkeypatch,target):
    module,root,contract = fixture(tmp_path,monkeypatch)
    def live():
        if not (contract['attempt']/'complete.json').exists():return
        paths = {'checkpoint':next((root/'checkpoints').glob('*/state/annealing/M.npy')),
            'score':root/'stream/batches/chunk-000000000000.bin',
            'reference':contract['attempt']/'checkpoint-references.bin',
            'source':root/'matching/chunk-000000000000.json',
            'read':contract['attempt']/'events/chunk-000000000000/complete.json'}
        path = paths[target];path.write_bytes(b'x'*path.stat().st_size)
    contract['lease'] = live
    with pytest.raises((ValueError,UnicodeError)):module.verify(root,**contract)
    assert (contract['attempt']/'failed.json').exists()


def test_reference_and_metadata_budget_refuses_before_claim(tmp_path,monkeypatch):
    module,root,contract = fixture(tmp_path,monkeypatch)
    contract['max_stage_bytes'] = 1
    with pytest.raises(ValueError):module.verify(root,**contract)
    assert not contract['attempt'].exists()

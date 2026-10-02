"""Fresh cold-read claims against closed synthetic archives; no network."""
import json
import pytest

from tests.research.onchain_replication.test_archive_pair_writer import fixture as writer_fixture, first, sha


def fixture(tmp_path):
    from tradingagents.research.onchain_replication import archive_pair_reader as reader
    writer, transport, kwargs = writer_fixture(tmp_path)
    log = writer.ArchivePairLog(**kwargs)
    first(log)
    log.begin(sha(b'p1'), sha(b'i1')); log.complete(.5, 'iteration_cap', 1)
    log.finish()
    contract = dict(root=log.root, expected_sha256=log.archive_complete_sha,
        owner=kwargs['owner'], scope=kwargs['scope'], archive_policy=kwargs['archive_policy'],
        attempt=tmp_path/'cold01', transport=transport, lease=lambda: None,
        max_read_metadata_bytes=(3*kwargs['archive_policy']['max_chunks']+4)*reader.io.META_LIMIT)
    return reader, transport, log, contract


def hashes(root):
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


def test_cold_read_all_full_partial_chunks_preserves_closed_writer(tmp_path):
    module, transport, log, contract = fixture(tmp_path)
    before = hashes(log.root)
    result = module.verify(**contract)
    assert result['archive_complete_sha256'] == log.archive_complete_sha
    assert result['replay']['completed_pairs'] == 2 and result['replay']['progress_events'] == 1
    assert result['replay']['record_bytes'] == 5*168 and result['replay']['chunks'] == 2
    assert result['execution_admitted'] is False
    assert hashes(log.root) == before
    assert not list(contract['attempt'].rglob('*.bin'))
    assert len(list(contract['attempt'].glob('chunk-*/complete.json'))) == 2
    saved = hashes(contract['attempt'])
    with pytest.raises((ValueError, FileExistsError)): module.verify(**contract)
    assert hashes(contract['attempt']) == saved and hashes(log.root) == before


@pytest.mark.parametrize('field', ['owner','scope','hash','policy','budget'])
def test_wrong_trust_or_budget_refuses_before_read_claim(tmp_path, field):
    module, transport, log, contract = fixture(tmp_path)
    if field == 'owner': contract['owner'] = '0'*64
    if field == 'scope': contract['scope'] = contract['scope'] | {'workflow':'0'*64}
    if field == 'hash': contract['expected_sha256'] = '0'*64
    if field == 'policy': contract['archive_policy'] = contract['archive_policy'] | {'remote_prefix':'other'}
    if field == 'budget': contract['max_read_metadata_bytes'] = 1
    before = hashes(log.root)
    with pytest.raises(ValueError): module.verify(**contract)
    assert not contract['attempt'].exists() and hashes(log.root) == before


@pytest.mark.parametrize('member', ['chunk-000000000000.json','disposed-000000000000.json',
    'copies/chunk-000000000000/complete.json','reads/chunk-000000000000/verified.json'])
def test_changed_source_metadata_refuses_before_remote_read(tmp_path, member):
    module, transport, log, contract = fixture(tmp_path)
    (log.root/member).write_bytes(b'{}\n')
    with pytest.raises(ValueError): module.verify(**contract)
    assert not contract['attempt'].exists()


@pytest.mark.parametrize('member', ['failed.json','cleanup-failed.json'])
def test_source_failure_marker_including_dangling_link_refuses(tmp_path, member):
    module, transport, log, contract = fixture(tmp_path)
    (log.root/member).symlink_to(log.root/'missing')
    with pytest.raises(ValueError): module.verify(**contract)
    assert not contract['attempt'].exists()


@pytest.mark.parametrize('failure', ['corrupt','missing'])
def test_failed_download_retained_without_changing_source(tmp_path, failure):
    module, transport, log, contract = fixture(tmp_path)
    before = hashes(log.root)
    if failure == 'corrupt': transport.corrupt = True
    else: next(transport.root.glob('*/payload.bin')).unlink()
    with pytest.raises((ValueError, OSError)): module.verify(**contract)
    assert (contract['attempt']/'failed.json').exists()
    assert not (contract['attempt']/'complete.json').exists()
    assert hashes(log.root) == before


@pytest.mark.parametrize('target', ['source','consumption','revocation'])
def test_final_callback_cannot_invalidate_success(tmp_path, target):
    module, transport, log, contract = fixture(tmp_path)
    def lease():
        if not (contract['attempt']/'complete.json').exists(): return
        if target == 'source': (log.root/'chunk-000000000000.json').write_bytes(b'{}\n')
        if target == 'consumption': (contract['attempt']/'chunk-000000000000/complete.json').write_bytes(b'{}\n')
        if target == 'revocation': raise RuntimeError('owner lost')
    contract['lease'] = lease
    with pytest.raises((ValueError, RuntimeError)): module.verify(**contract)
    assert (contract['attempt']/'failed.json').exists()

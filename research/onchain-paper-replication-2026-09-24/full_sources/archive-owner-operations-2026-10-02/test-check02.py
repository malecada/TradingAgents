"""Real current-owner reservations; no financial trial or external transfer."""
import json
import pytest
from tests.research.onchain_replication.test_archive_owner_policy import admitted, select


def attach(admitted):
    from tradingagents.research.onchain_replication import archive_owner_operations as operations
    return operations.attach(select(admitted))


def test_actual_stage_reservations_are_exclusive_finite_and_retained(admitted):
    ledger = attach(admitted);owner = admitted[1]
    with pytest.raises((ValueError,FileExistsError)):attach(admitted)
    stage = owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    write = ledger.writer(stage)
    assert write.record['reserved_remote_payload_bytes'] == 200*168
    assert write.record['reserved_decoded_transfer_bytes'] == 3*200*168
    assert (write.root/'intent.json').is_file()
    with pytest.raises(ValueError):ledger.writer(stage)
    with pytest.raises(ValueError):ledger.reader(stage)
    write.lease();write.complete('a'*64)
    with pytest.raises(ValueError):write.lease()
    with pytest.raises(ValueError):ledger.writer(stage)
    claims = []
    for index in range(4):
        read = ledger.reader(stage);claims.append(read.root)
        assert read.record['ordinal'] == index
        assert read.record['reserved_decoded_transfer_bytes'] == 200*168
        read.complete('b'*64)
    assert len(set(claims)) == 4
    before = {str(p):p.read_bytes() for p in ledger.root.rglob('*.json')}
    with pytest.raises(ValueError):ledger.reader(stage)
    assert before == {str(p):p.read_bytes() for p in ledger.root.rglob('*.json')}
    assert ledger.reserved['decoded_transfer_bytes'] == 7*200*168
    assert ledger.reserved['remote_payload_bytes'] == 200*168
    assert json.loads((write.root/'complete.json').read_bytes())['reference_sha256'] == 'a'*64
    ledger.close()


def test_ambiguous_failure_never_refunds_or_reopens_claim(admitted):
    ledger = attach(admitted);owner = admitted[1]
    stage = owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    write = ledger.writer(stage);write.fail(OSError('ambiguous upload'))
    assert (write.root/'failed.json').is_file()
    assert ledger.reserved['decoded_transfer_bytes'] == 3*200*168
    for call in (lambda:write.complete('a'*64),lambda:ledger.writer(stage),lambda:ledger.reader(stage)):
        with pytest.raises(ValueError):call()
    from tradingagents.research.onchain_replication import archive_owner_operations as operations
    with pytest.raises((ValueError,FileExistsError)):operations.attach(select(admitted))
    ledger.close()


def test_changed_claim_cannot_release_reservation(admitted):
    ledger = attach(admitted);owner = admitted[1]
    stage = owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    write = ledger.writer(stage)
    (write.root/'intent.json').write_bytes(b'{}')
    with pytest.raises(ValueError):write.complete('a'*64)
    assert not (write.root/'complete.json').exists()
    assert ledger.reserved['decoded_transfer_bytes'] == 3*200*168
    ledger.close()


def test_owner_transition_lock_covers_selection_consumption(admitted,monkeypatch):
    selection = select(admitted);owner = admitted[1];original = owner.boundary
    attempted = []
    def boundary():
        original()
        with pytest.raises(ValueError,match='concurrent'):
            owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
        attempted.append(True)
    monkeypatch.setattr(owner,'boundary',boundary)
    from tradingagents.research.onchain_replication import archive_owner_operations as operations
    ledger = operations.attach(selection)
    assert attempted and not owner.stages
    ledger.close()


def test_public_close_during_operation_lease_cannot_return_live(admitted,monkeypatch):
    ledger = attach(admitted);owner = admitted[1]
    stage = owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    write = ledger.writer(stage);original = owner.lease
    def lease():
        original();ledger.close()
    monkeypatch.setattr(owner,'lease',lease)
    with pytest.raises(ValueError):write.lease()
    assert ledger.reserved['decoded_transfer_bytes'] == 3*200*168
    ledger.close()


def test_attachment_callback_failure_retains_primary_under_transition(admitted,monkeypatch):
    selection = select(admitted)
    from tradingagents.research.onchain_replication import archive_owner_operations as operations
    primary = RuntimeError('late attachment rejection')
    def reject(self,*,full):raise primary
    monkeypatch.setattr(operations.Ledger,'_current',reject)
    with pytest.raises(RuntimeError) as caught:operations.attach(selection)
    assert caught.value is primary
    assert (admitted[1].root.parent/'archive-operations/closed.json').is_file()
    assert admitted[1]._transition.acquire(blocking=False)
    admitted[1]._transition.release()


def test_constructor_uncertain_close_is_fatal_and_releases_transition(admitted,monkeypatch):
    selection = select(admitted)
    from tradingagents.research.onchain_replication import archive_owner_operations as operations
    close = operations.os.close;injected = []
    def uncertain(fd):
        path = operations.os.readlink('/proc/self/fd/'+str(fd))
        close(fd)
        if path.endswith('/archive-operations') and not injected:
            injected.append(True);raise OSError('injected after real close')
    monkeypatch.setattr(operations.os,'close',uncertain)
    with pytest.raises(operations.io.CleanupFailure):operations.attach(selection)
    assert injected and admitted[1]._transition.acquire(blocking=False)
    admitted[1]._transition.release()


def test_completion_write_failure_retains_reservation(admitted,monkeypatch):
    ledger = attach(admitted);owner = admitted[1]
    stage = owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    claim = ledger.writer(stage)
    from tradingagents.research.onchain_replication import archive_owner_operations as operations
    original = operations.io._write
    def write(fd,name,raw):
        if name == 'complete.json':raise OSError('completion publication failed')
        return original(fd,name,raw)
    monkeypatch.setattr(operations.io,'_write',write)
    with pytest.raises(OSError):claim.complete('a'*64)
    assert (claim.root/'failed.json').is_file()
    assert ledger.reserved['decoded_transfer_bytes'] == 3*200*168
    with pytest.raises(ValueError):ledger.reader(stage)
    ledger.close()


def test_owner_revocation_after_claim_publication_is_spent(admitted,monkeypatch):
    ledger = attach(admitted);owner = admitted[1]
    stage = owner.begin('dictionary',workload_sha256='d'*64,pairs=0)
    original = owner.lease
    def lease():
        original()
        if ledger._active is not None and (ledger._active.root/'intent.json').exists():
            owner.poisoned = True
    monkeypatch.setattr(owner,'lease',lease)
    with pytest.raises(ValueError):ledger.writer(stage)
    assert (ledger._active.root/'failed.json').is_file()
    assert ledger.reserved['decoded_transfer_bytes'] == 3*200*168
    ledger.close()

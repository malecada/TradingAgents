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

"""Callback-free final current-owner verification on actual registered owners."""
from types import SimpleNamespace
import pytest
from tests.research.onchain_replication import test_compact_training as training
from tradingagents.research.onchain_replication import compact_owner


def test_actual_owner_type_required():
    with pytest.raises(ValueError,match='actual'):compact_owner.verify_current(object())


@pytest.fixture
def admitted():
    gen=training.admitted.__wrapped__(SimpleNamespace(param='valid'));owner,args,t=next(gen)
    try:yield owner,t
    finally:
        try:next(gen)
        except StopIteration:pass


def test_actual_owner_checks_without_external_lease(admitted,monkeypatch):
    owner,t=admitted
    def refuse():raise AssertionError('external lease called')
    monkeypatch.setattr(owner,'lease',refuse);monkeypatch.setattr(owner.bound,'lease',refuse)
    compact_owner.verify_current(owner)


@pytest.mark.parametrize('mode',['poisoned','closing','foreign','owner_terminal','representation_terminal','reservation','configuration','binding_metadata','run_dangling','other_owner'])
def test_terminal_foreign_or_changed_owner_refused(admitted,mode):
    owner,t=admitted
    if mode in ('poisoned','closing'):setattr(owner,mode,True)
    elif mode=='foreign':(owner.root/'foreign').write_bytes(b'preserved')
    elif mode=='owner_terminal':(owner.root/'failed.json').write_bytes(b'{}')
    elif mode=='representation_terminal':(owner.root.parent/'complete.json').write_bytes(b'{}')
    elif mode=='reservation':owner.reserved += 1
    elif mode=='configuration':owner.maximum += 1
    elif mode=='binding_metadata':owner.bound._snapshots.clear()
    elif mode=='run_dangling':(owner.bound._run.directory/'failed.json').symlink_to('missing-terminal')
    elif mode=='other_owner':(owner.root.parent.parent/'foreign-owner').mkdir()
    with pytest.raises(ValueError):compact_owner.verify_current(owner)

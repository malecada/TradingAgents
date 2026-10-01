"""Fatal cleanup uncertainty at actual tail/batch/stream descriptor boundaries."""
import os
import numpy as np
import pytest
from tests.research.onchain_replication import test_score_tail as tails
from tests.research.onchain_replication import test_score_batches as batches
from tests.research.onchain_replication import test_mcm_score_stream as streams
from tradingagents.research.onchain_replication import score_batches as batch,score_tail as tail,mcm_score_stream as stream


@pytest.fixture
def trap(monkeypatch):
    class Trap:
        broken = set(); owned = set(); attempted = []; closed = set(); real = staticmethod(os.close)
        def close(self,fd):
            self.attempted.append(fd)
            if fd in self.broken: raise OSError('synthetic descriptor not released')
            self.real(fd); self.closed.add(fd)
        def owns(self,*fds):
            values={x for x in fds if x is not None};self.owned.update(values)
            # Earlier file operations may have used the same integer before
            # this fixture acquired it. Track only this live ownership interval.
            self.closed.difference_update(values)
            self.attempted[:]=[fd for fd in self.attempted if fd not in values]
    t = Trap(); monkeypatch.setattr(batch.os,'close',t.close)
    try: yield t
    finally:
        # Only the fault-injected fixture's known unreleased handles are cleaned
        # by the test harness. Production must never retry ambiguous close.
        for fd in t.owned-t.closed:
            try:t.real(fd)
            except OSError:pass


@pytest.mark.parametrize('when',['close','finish','constructor'])
def test_tail_attempts_both_owned_descriptors_and_cleanup_is_fatal(tmp_path,monkeypatch,trap,when):
    objects=[]
    def arm(obj):
        objects.append(obj); trap.owns(obj.record_fd,obj.fd); trap.broken.add(obj.record_fd)
    if when == 'constructor':
        def fail(obj,*args,**kwargs):arm(obj);raise RuntimeError('synthetic primary tail construction')
        monkeypatch.setattr(tail.ScoreTail,'_check',fail)
        action=lambda:tails.tail(tmp_path)
    else:
        obj=tails.tail(tmp_path)
        if when=='finish':obj.append(0,'b'*64,.2);obj.append(1,'c'*64,.3)
        arm(obj); action=obj.close if when=='close' else obj.finish
    with pytest.raises(BaseException) as caught:action()
    assert not isinstance(caught.value,Exception),'uncertain tail cleanup escaped as ordinary error'
    obj=objects[0];assert obj.closed and obj.fd in trap.closed
    assert trap.attempted.count(obj.record_fd)==1
    if when=='constructor':assert isinstance(caught.value.__cause__,RuntimeError)
    obj.close();assert trap.attempted.count(obj.record_fd)==1


@pytest.mark.parametrize('when',['finish','constructor'])
def test_batch_cleanup_is_fatal_at_terminal_and_before_constructor_returns(tmp_path,monkeypatch,trap,when):
    if when=='constructor':
        def fail(fd,name,raw):
            trap.owns(fd);trap.broken.add(fd);raise RuntimeError('synthetic primary batch construction')
        monkeypatch.setattr(batch,'_write',fail);action=lambda:batches.writer(tmp_path)
    else:
        obj=batches.writer(tmp_path);obj.append(0,np.ones(4));obj.append(4,np.ones(2))
        trap.owns(obj.fd);trap.broken.add(obj.fd);action=obj.finish
    with pytest.raises(BaseException) as caught:action()
    assert not isinstance(caught.value,Exception),'uncertain batch cleanup escaped as ordinary error'
    if when=='constructor':assert isinstance(caught.value.__cause__,RuntimeError)
    else:obj.close()
    assert all(trap.attempted.count(fd)==1 for fd in trap.broken)


@pytest.mark.parametrize('when',['callback','constructor','finish'])
def test_stream_closes_remaining_children_and_fails_fatally(tmp_path,monkeypatch,trap,when):
    base,f,d,kernel=streams.fixture();objects=[]
    def arm(obj,broken):
        objects.append(obj);trap.owns(obj.fd,obj.batches.fd)
        if obj.active is not None:trap.owns(obj.active.fd,obj.active.record_fd)
        trap.broken.add(broken)
    if when=='constructor':
        def fail(obj):arm(obj,obj.batches.fd);raise RuntimeError('synthetic primary stream construction')
        monkeypatch.setattr(stream.MCMScoreStream,'_check',fail)
        action=lambda:streams.stream(tmp_path,f,d,base.Scores(f.match))
    else:
        def compute(*args):
            arm(obj,obj.active.record_fd);raise RuntimeError('synthetic primary numerical failure')
        obj=streams.stream(tmp_path,f,d,compute if when=='callback' else base.Scores(f.match))
        if when=='callback':
            action=lambda:kernel.mcm(f.g,d,f.match,**f.kw,score_pair=obj,policy=streams.POLICY,lease=lambda:None)
        else:
            kernel.mcm(f.g,d,f.match,**f.kw,score_pair=obj,policy=streams.POLICY,lease=lambda:None)
            arm(obj,obj.fd);action=obj.finish
    with pytest.raises(BaseException) as caught:action()
    assert not isinstance(caught.value,Exception),'uncertain stream cleanup escaped as ordinary error'
    obj=objects[0];assert obj.closed
    assert trap.owned-trap.broken <= trap.closed
    if when!='finish':assert isinstance(caught.value.__cause__,RuntimeError)
    obj.close();assert all(trap.attempted.count(fd)==1 for fd in trap.broken)

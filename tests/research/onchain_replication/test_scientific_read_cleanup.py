"""Owned bounded metadata reader closes and construction failure handling."""
import os
import pytest
from tradingagents.research.onchain_replication import score_batches as io


@pytest.mark.parametrize('body_fails',[False,True])
def test_stream_close_uncertainty_is_fatal_and_primary_retained(tmp_path,monkeypatch,body_fails):
    (tmp_path/'value').write_bytes(b'value');root,fd=io._open(tmp_path)
    original=io.os.fdopen;closed=[];primary=ValueError('synthetic read failure')
    class Stream:
        def __init__(self,stream):self.stream=stream
        def fileno(self):return self.stream.fileno()
        def read(self,*args):
            if body_fails:raise primary
            return self.stream.read(*args)
        def close(self):
            self.stream.close();closed.append(1);raise OSError('synthetic stream close uncertainty')
        def __enter__(self):return self
        def __exit__(self,*args):self.close()
    monkeypatch.setattr(io.os,'fdopen',lambda *args,**kwargs:Stream(original(*args,**kwargs)))
    try:
        with pytest.raises(io.CleanupFailure) as caught:io._read(fd,'value',20)
        assert closed==[1]
        if body_fails:assert caught.value.__cause__ is primary
    finally:os.close(fd)


def test_stream_construction_failure_releases_owned_fd(tmp_path,monkeypatch):
    (tmp_path/'value').write_bytes(b'value');root,fd=io._open(tmp_path);opened=[]
    original_open=io.os.open;original_close=io.os.close;closed=[]
    def track(*args,**kwargs):
        value=original_open(*args,**kwargs);opened.append(value);return value
    def close(value):closed.append(value);return original_close(value)
    def fail(*args,**kwargs):raise OSError('synthetic fdopen construction failure')
    monkeypatch.setattr(io.os,'open',track);monkeypatch.setattr(io.os,'close',close)
    monkeypatch.setattr(io.os,'fdopen',fail)
    try:
        with pytest.raises(OSError):io._read(fd,'value',20)
        assert len(opened)==1 and closed==opened
    finally:
        # Preserve a failing red check without leaking its descriptor to tests.
        for value in opened:
            if value not in closed:original_close(value)
        original_close(fd)

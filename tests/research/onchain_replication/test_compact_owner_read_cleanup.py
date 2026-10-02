"""Fatal one-shot cleanup for exact owner metadata and inventory readers."""
import pytest
from tradingagents.research.onchain_replication import compact_owner as module


@pytest.mark.parametrize('function',['exact','entries'])
@pytest.mark.parametrize('body_fails',[False,True])
def test_owner_reader_close_preserves_primary_and_is_fatal(tmp_path,monkeypatch,function,body_fails):
    (tmp_path/'intent.json').write_bytes(b'original');original=module.os.close;injected=[]
    def close(fd):
        path=module.os.readlink('/proc/self/fd/'+str(fd));original(fd)
        if path==str(tmp_path):
            injected.append(fd);raise OSError('synthetic owner reader close uncertainty')
    monkeypatch.setattr(module.os,'close',close)
    with pytest.raises(module.io.CleanupFailure) as caught:
        if function=='exact':module.exact(tmp_path,'intent.json',b'wrong' if body_fails else b'original')
        else:module.entries(tmp_path,{'wrong' if body_fails else 'intent.json'},required={'intent.json'})
    assert len(injected)==1
    if body_fails:assert isinstance(caught.value.__cause__,ValueError)

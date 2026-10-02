"""Final reservation callbacks precede the last callback-free scientific join."""
import pytest
from tests.research.onchain_replication.test_archived_stage import fixture


def test_finalizer_is_immutable_and_does_not_replay_remote(tmp_path,monkeypatch):
    module,root,contract = fixture(tmp_path,monkeypatch)
    calls=[];original=contract['transport'].get;final=[]
    def get(*args,**kwargs):
        calls.append(args[0]);return original(*args,**kwargs)
    monkeypatch.setattr(contract['transport'],'get',get)
    def finalize(result):
        with pytest.raises(TypeError):result['completed_pairs']=0
        final.append((result,len(calls)))
    result=module.verify(root,**contract,on_verified=finalize)
    assert len(final)==1 and dict(final[0][0])==result and len(calls)==final[0][1]


@pytest.mark.parametrize('target',['checkpoint','score','reference','read','source','complete'])
def test_finalizer_mutation_is_not_acknowledged(tmp_path,monkeypatch,target):
    module,root,contract=fixture(tmp_path,monkeypatch)
    def finalize(result):
        paths={'checkpoint':next((root/'checkpoints').glob('*/state/annealing/M.npy')),
            'score':root/'stream/batches/chunk-000000000000.bin',
            'reference':contract['attempt']/'checkpoint-references.bin',
            'read':contract['attempt']/'events/chunk-000000000000/complete.json',
            'source':root/'matching/terminal.json','complete':contract['attempt']/'complete.json'}
        path=paths[target];path.write_bytes(b'x'*path.stat().st_size)
    with pytest.raises((ValueError,UnicodeError)):
        module.verify(root,**contract,on_verified=finalize)
    assert (contract['attempt']/'failed.json').is_file()


def test_invalid_finalizer_does_not_create_attempt(tmp_path,monkeypatch):
    module,root,contract=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError):module.verify(root,**contract,on_verified=1)
    assert not contract['attempt'].exists()


@pytest.mark.parametrize('target',['metadata','checkpoint_file','checkpoint_root','score_inventory','score_batch','score_tail'])
def test_owned_read_close_uncertainty_is_fatal(tmp_path,monkeypatch,target):
    import inspect
    module,root,contract=fixture(tmp_path,monkeypatch)
    original=module.os.close;injected=[]
    def close(fd):
        path=module.os.readlink('/proc/self/fd/'+str(fd))
        caller=inspect.currentframe().f_back
        function=caller.f_code.co_name;filename=caller.f_code.co_filename
        original(fd)
        hit={'metadata':function=='read' and filename.endswith('/compact_stage.py'),
            'checkpoint_file':path.endswith('/M.npy'),
            'checkpoint_root':path.endswith('/state') and 'checkpoints' in path,
            'score_inventory':function=='inventory' and filename.endswith('/compact_stage.py'),
            'score_batch':function=='stream' and filename.endswith('/compact_stage.py'),
            'score_tail':function=='verify' and filename.endswith('/score_tail.py')}[target]
        # The helper introduced by the fix changes the direct caller; inspect
        # the full stack to preserve injection at the same owned boundary.
        if not hit:
            stack=inspect.stack()
            hit={'metadata':any(f.function=='read' and f.filename.endswith('/compact_stage.py') for f in stack),
                'checkpoint_file':path.endswith('/M.npy'),
                'checkpoint_root':path.endswith('/state') and 'checkpoints' in path,
                'score_inventory':any(f.function=='inventory' and f.filename.endswith('/compact_stage.py') for f in stack),
                'score_batch':path.endswith('/stream/batches') and any(f.function=='stream' and f.filename.endswith('/compact_stage.py') for f in stack),
                'score_tail':path.endswith('/tail-000000000000') and any(f.function=='verify' and f.filename.endswith('/score_tail.py') for f in stack)}[target]
        if hit and not injected:
            injected.append(path);raise OSError('synthetic close uncertainty after actual close')
    monkeypatch.setattr(module.os,'close',close)
    with pytest.raises(module.io.CleanupFailure):module.verify(root,**contract)
    assert len(injected)==1

"""Synthetic descriptor observations; no native job or transport."""
import os
import pytest
from tradingagents.research.onchain_replication import real_pilot_storage as m
from tradingagents.research.onchain_replication import workflow_storage as w


def setup_union(tmp_path):
    (tmp_path/'research_artifacts').mkdir()
    (tmp_path/'research_runs').mkdir()
    (tmp_path/'research_runs/.lock').touch()
    for paths in m.residual_paths(tmp_path).values():
        for path in paths:path.mkdir(parents=True,exist_ok=True)
    limits=dict(max_allocated_bytes=10**8,max_logical_bytes=10**7,max_entries=10000,max_depth=64,max_scan_seconds=5)
    budget=dict(schema_version=2,kind=m.KIND,authority_root=str(tmp_path),experiment=m.EXPERIMENT,
        roots=[str(tmp_path/'research_artifacts'),str(tmp_path/'research_runs'/m.EXPERIMENT)],
        shared_files=[str(tmp_path/'research_runs/.lock')],limits=limits)
    return m.WritableUnion(budget,tmp_path)


def test_one_walk_matches_standalone_residuals(tmp_path,monkeypatch):
    union=setup_union(tmp_path)
    for paths in m.residual_paths(tmp_path).values():
        for path in paths:(path/'payload').write_bytes(b'abc')
    expected=m.residual_check(tmp_path);seen=[];real=w.os.scandir
    def scan(fd):
        s=os.fstat(fd);seen.append((s.st_dev,s.st_ino));return real(fd)
    monkeypatch.setattr(w.os,'scandir',scan)
    got=union.check()
    assert len(seen)==len(set(seen)), 'a subtree was walked twice'
    for name in expected:
        for key in ('allocated_bytes','logical_file_bytes','entries','regular_files','directories'):
            assert got['residual_domains'][name][key]==expected[name][key]


def test_residual_aggregate_and_file_limits(tmp_path,monkeypatch):
    union=setup_union(tmp_path)
    policy=dict(m.RESIDUAL_POLICY['training_and_lifecycle'],logical_bytes=5,max_file_bytes=4)
    monkeypatch.setitem(m.RESIDUAL_POLICY,'training_and_lifecycle',policy)
    paths=m.residual_paths(tmp_path)['training_and_lifecycle']
    (paths[0]/'a').write_bytes(b'123');(paths[1]/'a').write_bytes(b'123')
    with pytest.raises(w.StorageLimit):union.check()
    (paths[1]/'a').unlink();(paths[0]/'a').write_bytes(b'12345')
    with pytest.raises(w.StorageLimit):union.check()


def test_birth_disappearance_replacement(tmp_path):
    union=setup_union(tmp_path);p=m.residual_paths(tmp_path)['runtime_temp_cache'][0]
    union.check();p.rename(p.with_name('old'));p.mkdir()
    with pytest.raises(ValueError,match='residual root replaced'):union.check()


def test_retry_discards_partial_subdomain_counts(tmp_path,monkeypatch):
    union=setup_union(tmp_path);p=m.residual_paths(tmp_path)['runtime_temp_cache'][0]
    (p/'a').write_bytes(b'123');os.link(p/'a',p/'b')
    monkeypatch.setattr(w.time,'sleep',lambda _: (p/'b').unlink())
    result=union.check()['residual_domains']['runtime_temp_cache']
    assert result['regular_files']==1 and result['logical_file_bytes']==3


def test_symlink_refused(tmp_path):
    union=setup_union(tmp_path);p=m.residual_paths(tmp_path)['runtime_temp_cache'][0]
    (p/'bad').symlink_to('/unopened')
    with pytest.raises(ValueError,match='symbolic link'):union.check()


def test_late_birth_restarts_whole_observation(tmp_path,monkeypatch):
    union=setup_union(tmp_path);p=m.residual_paths(tmp_path)['runtime_temp_cache'][0];p.rmdir()
    real=union._birth;calls=[0]
    def birth():
        calls[0]+=1
        if calls[0]==2:p.mkdir();(p/'late').write_bytes(b'late')
        return real()
    monkeypatch.setattr(union,'_birth',birth)
    got=union.check()
    assert calls[0]==4
    assert got['residual_domains']['runtime_temp_cache']['logical_file_bytes']==4


def test_observed_birth_cannot_disappear_in_discarded_attempt(tmp_path,monkeypatch):
    union=setup_union(tmp_path);p=m.residual_paths(tmp_path)['runtime_temp_cache'][0];p.rmdir()
    original=m._residual_roots;calls=[0]
    def roots(*a):
        result=original(*a);calls[0]+=1
        if calls[0]==1:p.mkdir();(p/'a').write_bytes(b'x');os.link(p/'a',p/'b')
        return result
    monkeypatch.setattr(m,'_residual_roots',roots)
    def remove(_):
        (p/'a').unlink();(p/'b').unlink();p.rmdir()
    monkeypatch.setattr(w.time,'sleep',remove)
    with pytest.raises(ValueError,match='disappeared after birth'):union.check()


def test_shared_deadline_and_close_failure(tmp_path,monkeypatch):
    union=setup_union(tmp_path);clock=[0.];real=w.os.scandir
    def scan(fd):clock[0]=6.;return real(fd)
    monkeypatch.setattr(w.time,'monotonic',lambda:clock[0]);monkeypatch.setattr(w.os,'scandir',scan)
    with pytest.raises(w.StorageLimit,match='time'):union.check()
    monkeypatch.undo();real_close=w.os.close
    def close(fd):real_close(fd);raise OSError('close uncertainty')
    monkeypatch.setattr(w.os,'close',close)
    with pytest.raises(w.StorageCleanupFailure):union.check()


@pytest.mark.parametrize('kind',['fifo','device','directory_change'])
def test_authenticated_traversal_refusals(tmp_path,monkeypatch,kind):
    union=setup_union(tmp_path);p=m.residual_paths(tmp_path)['runtime_temp_cache'][0]
    if kind=='fifo':
        os.mkfifo(p/'bad')
        with pytest.raises(ValueError,match='special file'):union.check()
        return
    (p/'a').write_bytes(b'x');real=w.os.stat
    def changed(path,*a,**kw):
        result=real(path,*a,**kw)
        if kw.get('dir_fd') is not None and path==('a' if kind=='device' else p.name):
            from types import SimpleNamespace
            attrs={k:getattr(result,k) for k in dir(result) if k.startswith('st_')}
            attrs['st_dev' if kind=='device' else 'st_ino']+=1
            return SimpleNamespace(**attrs)
        return result
    monkeypatch.setattr(w.os,'stat',changed)
    with pytest.raises(ValueError,match='filesystem|changed while opening'):union.check()


def test_historical_siblings_still_count_in_union(tmp_path):
    union=setup_union(tmp_path);p=tmp_path/'research_artifacts/history';p.mkdir();(p/'old').write_bytes(b'old')
    before=union.check();(p/'new').write_bytes(b'012345')
    after=union.check()
    assert after['logical_file_bytes']==before['logical_file_bytes']+6
    assert after['entries']==before['entries']+1
    for domain in before['residual_domains']:
        assert after['residual_domains'][domain]['logical_file_bytes']==before['residual_domains'][domain]['logical_file_bytes']


@pytest.mark.parametrize('field',['regular_files','directories'])
def test_residual_count_limits_below_union(tmp_path,monkeypatch,field):
    union=setup_union(tmp_path);p=m.residual_paths(tmp_path)['runtime_temp_cache'][0]
    monkeypatch.setitem(m.RESIDUAL_POLICY,'runtime_temp_cache',dict(m.RESIDUAL_POLICY['runtime_temp_cache'],**{field:1}))
    if field=='regular_files':(p/'a').touch();(p/'b').touch()
    else:(p/'child').mkdir()
    with pytest.raises(w.StorageLimit) as error:union.check()
    assert error.value.residual_domain=='runtime_temp_cache'
    assert error.value.residual_observation[field]==2
    assert error.value.observation['partial_root']['residual_domain']=='runtime_temp_cache'


def test_prospective_lifecycle_birth_is_counted(tmp_path,monkeypatch):
    old=setup_union(tmp_path);target=old.target;target.rmdir()
    union=m.WritableUnion(old.budget,tmp_path);real=union._birth;calls=[0]
    def birth():
        calls[0]+=1
        if calls[0]==2:target.mkdir();(target/'new').write_bytes(b'12345')
        return real()
    monkeypatch.setattr(union,'_birth',birth)
    got=union.check()
    assert got['residual_domains']['training_and_lifecycle']['logical_file_bytes']==5
    assert union.target_identity is not None

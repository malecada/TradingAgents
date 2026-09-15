"""Independent new protocol reconstruction; all sources and cells invented."""
import os
import pytest
from tests.research.test_options_timing_control import build_fixture,start,now,write
from tests.research.test_options_capture_control import source_binding
from tests.research.test_options_capture_independent import external_evidence
from tradingagents.research_options_timing import control, independent_verify as verify


@pytest.fixture
def case(tmp_path):return build_fixture(tmp_path/'repo')


def test_independent_failed_terminal_external_quiescence(case,monkeypatch):
    episode=start(case)
    when=now()
    from tests.research.test_options_timing_control import ref
    ack={'claim_sha256':episode.claim_hash,'worker_lease_sha256':verify.digest(verify.canonical(episode.claim['episode_protocol']['worker_lease'])),'stopped_at':when,'status':'stopped'}
    write(case[0],'returned/ack.json',ack);episode.acknowledge_stop(ack=ref(case[0],'returned/ack.json'),now_utc=when)
    evidence=external_evidence(case,episode,when=when)
    ended=now();episode.finish(status='failed',cells=[{'id':c,'status':'unavailable','reason':'invented'} for c in episode.claim['experiment']['cells']],reason='invented',now_utc=ended)
    def forbidden(*args,**kwargs):raise AssertionError('controller admission reused')
    monkeypatch.setattr(control,'_admit',forbidden);monkeypatch.setattr(control,'verify_episode',forbidden)
    with pytest.raises(ValueError,match='quiescence'):verify.verify(root=case[0],now_utc=ended)
    assert verify.verify(root=case[0],now_utc=ended,quiescence_evidence=evidence)['status']=='failed'
    write(case[0],'returned/exit-observation.json',b'changed')
    with pytest.raises(ValueError):verify.verify(root=case[0],now_utc=ended,quiescence_evidence=evidence)


def test_full_once_analysis_and_terminal(case):
    episode=start(case);end=episode.claim['episode_protocol']['observation_window']['end']
    later=(*case[:4],end);binding,source=source_binding(later,episode)
    evidence=external_evidence(later,episode)
    with pytest.raises(ValueError):episode.analysis_intent(binding=binding,commit=source,now_utc=case[4])
    episode.analysis_intent(binding=binding,commit=source,now_utc=end)
    with pytest.raises(FileExistsError):episode.analysis_intent(binding=binding,commit=source,now_utc=end)
    episode.write_output('books.json',b'{}',now_utc=end)
    episode.finish(status='complete',cells=[{'id':c,'status':'unavailable','reason':'invented'} for c in episode.claim['experiment']['cells']],reason='invented',now_utc=end)
    assert verify.verify(root=case[0],now_utc=end,quiescence_evidence=evidence)['status']=='complete'
    with pytest.raises(ValueError):control.Episode.resume(root=case[0],now_utc=end)


@pytest.mark.parametrize('kind',['symlink','fifo','pending','oversize'])
def test_unsafe_outputs_precede_hash(case,monkeypatch,kind):
    episode=start(case);path=episode.directory/'outputs'/('.pending-invented' if kind=='pending' else 'books.json')
    if kind=='symlink':path.symlink_to(case[0]/'design.json')
    elif kind=='fifo':os.mkfifo(path)
    elif kind=='oversize':
        with path.open('wb') as f:f.truncate(16*1024**2+1)
    else:path.write_bytes(b'invented')
    actual=verify.file_hash
    def guard(p):
        if p==path:raise AssertionError('unsafe member hashed')
        return actual(p)
    monkeypatch.setattr(verify,'file_hash',guard)
    with pytest.raises(ValueError):verify.verify(root=case[0],now_utc=now())
    assert path.lstat()

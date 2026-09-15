"""Invented disposable protocol cases; no real source or economic calculation."""
from datetime import timedelta
import json
import os
import pytest
from tests.research.test_options_capture_control import build_fixture, start, source_binding, ref, write, commit, rebind
from tradingagents.research_options_capture import control as control
from tradingagents.research_options_capture import independent_verify as verify


@pytest.fixture
def case(tmp_path):
    return build_fixture(tmp_path/'repo')


def external_evidence(case, episode, *, when=None, mode='sealed-worker-exit'):
    root=case[0];when=when or case[4]
    write(root,'returned/exit-observation.json',{'synthetic_only':True,'observed_at':when})
    review={'decision':'verify-options-worker-quiescence','claim_sha256':episode.claim_hash,
            'worker_lease_sha256':verify.digest(verify.canonical(episode.claim['episode_protocol']['worker_lease'])),
            'mode':mode,'observed_at':when,'evidence':ref(root,'returned/exit-observation.json')}
    write(root,'returned/quiescence-review.json',review)
    c=commit(root)
    return dict(ref(root,'returned/quiescence-review.json'),commit=c)


def test_active_reconstructs_without_controller_admission(case,monkeypatch):
    episode=start(case)
    def forbidden(*args,**kwargs):raise AssertionError('controller self-check reused')
    monkeypatch.setattr(control,'_admit',forbidden)
    monkeypatch.setattr(control,'verify_episode',forbidden)
    result=verify.verify(root=case[0],now_utc=case[4])
    assert result['status']=='active' and result['history_count']==19
    assert result['quiescence']=='unavailable'


def test_full_independent_episode_and_missing_external_stop(case):
    episode=start(case);end=episode.claim['episode_protocol']['observation_window']['end']
    later=(*case[:4],end)
    binding,source=source_binding(later,episode)
    evidence=external_evidence(later,episode)
    episode.analysis_intent(binding=binding,commit=source,now_utc=end)
    episode.write_output('books.json',b'{}',now_utc=end)
    episode.finish(status='complete',cells=[{'id':f'case-{i}','status':'unavailable','reason':'invented'} for i in range(8)],reason='invented',now_utc=end)
    with pytest.raises(verify.VerificationError,match='quiescence'):
        verify.verify(root=case[0],now_utc=end)
    assert verify.verify(root=case[0],now_utc=end,quiescence_evidence=evidence)['status']=='complete'
    write(case[0],'returned/exit-observation.json',b'changed')
    with pytest.raises(verify.VerificationError,match='hash'):
        verify.verify(root=case[0],now_utc=end,quiescence_evidence=evidence)


@pytest.mark.parametrize('field',['family','grant','history','runtime','source','future'])
def test_independent_mutated_claim_fails(case,field):
    episode=start(case);root=case[0]
    if field=='history':
        write(root,'research_runs/history-04/failed.json',{})
    elif field=='source':
        write(root,'design.json',b'changed')
    elif field=='runtime':
        write(root,'tradingagents/research_options_capture/journal.py',b'changed')
    else:
        claim=json.loads((episode.directory/'claim.json').read_bytes())
        if field=='family':claim['family']['attempt_budget']=5
        elif field=='grant':claim['episode_book_grant']['sha256']='0'*64
        else:claim['started_at']=claim['episode_protocol']['observation_window']['start']
        write(episode.directory,'claim.json',claim)
    with pytest.raises((ValueError,KeyError)):
        verify.verify(root=root,now_utc=case[4])


@pytest.mark.parametrize('kind',['symlink','fifo','pending','oversize'])
def test_output_inventory_rejected_before_hash(case,monkeypatch,kind):
    episode=start(case)
    path=episode.directory/'outputs'/('.pending-invented' if kind=='pending' else 'books.json')
    if kind=='symlink':path.symlink_to(case[0]/'design.json')
    elif kind=='fifo':os.mkfifo(path)
    elif kind=='oversize':
        with path.open('wb') as f:f.truncate(16*1024**2+1)
    else:path.write_bytes(b'invented interrupted publication')
    old=verify.file_hash;reads=[]
    def check(p):
        if p==path:reads.append(p);raise AssertionError('unsafe content read')
        return old(p)
    monkeypatch.setattr(verify,'file_hash',check)
    with pytest.raises(verify.VerificationError):verify.verify(root=case[0],now_utc=case[4])
    assert not reads and path.lstat()


def test_early_analysis_and_lease_expiry_evidence(case):
    episode=start(case);end=episode.claim['episode_protocol']['observation_window']['end']
    later=(*case[:4],end);binding,source=source_binding(later,episode)
    evidence=external_evidence(later,episode,mode='lease-expired')
    with pytest.raises(verify.VerificationError,match='premature'):
        verify.verify(root=case[0],now_utc=end,quiescence_evidence=evidence)
    evidence=external_evidence(later,episode)
    episode.analysis_intent(binding=binding,commit=source,now_utc=end)
    value=json.loads((episode.directory/'control/analysis-intent.json').read_bytes())
    value['started_at']=(verify.timestamp(end)-timedelta(seconds=1)).isoformat()
    write(episode.directory,'control/analysis-intent.json',value)
    with pytest.raises(verify.VerificationError,match='observation end'):
        verify.verify(root=case[0],now_utc=end,quiescence_evidence=evidence)


def test_failure_terminal_requires_external_lease_observation(case):
    episode=start(case);expiry=episode.claim['episode_protocol']['worker_lease']['expires_at']
    episode.finish(status='failed',cells=[],reason='invented lease expiry',now_utc=expiry)
    with pytest.raises(verify.VerificationError,match='quiescence'):
        verify.verify(root=case[0],now_utc=expiry)
    evidence=external_evidence(case,episode,when=expiry,mode='lease-expired')
    assert verify.verify(root=case[0],now_utc=expiry,quiescence_evidence=evidence)['status']=='failed'


@pytest.mark.parametrize('mutation',['grant','family','history','resource'])
def test_structurally_valid_envelope_cannot_bypass_new_protocol(case,mutation):
    episode=start(case);root,spec,grant,source,now=case
    if mutation=='grant':grant['increment']=2
    elif mutation=='family':spec['families'][control.FAMILY]['attempt_budget']=5
    elif mutation=='history':grant['prior_claims'].pop('history-04')
    else:spec['experiments'][control.TARGET]['episode_protocol']['resources']['staging_reserve_bytes']=1
    source=rebind(root,spec,grant)
    claim=json.loads((episode.directory/'claim.json').read_bytes())
    claim.update(source=source,design_source=source,registration_sha256=control.sha((root/'episode.json').read_bytes()),experiment=spec['experiments'][control.TARGET],family=spec['families'][control.FAMILY],episode_protocol=spec['experiments'][control.TARGET]['episode_protocol'],episode_book_grant=spec['experiments'][control.TARGET]['episode_book_grant'])
    # Synthetic bypass of start() to prove independent checks beyond legacy
    # structure, never a route used on the real retained claim inventory.
    from datetime import datetime,timezone
    claim['started_at']=datetime.now(timezone.utc).isoformat()
    write(episode.directory,'claim.json',claim)
    assert verify.verify_claim(episode.directory)['source']==source
    with pytest.raises(verify.VerificationError):
        verify.verify(root=root,now_utc=claim['started_at'])


@pytest.mark.parametrize('mutation',['seal_after_intent','terminal_before_intent'])
def test_retained_phase_clocks_cannot_be_backdated(case,mutation):
    episode=start(case);end=episode.claim['episode_protocol']['observation_window']['end']
    later=(*case[:4],end);binding,source=source_binding(later,episode)
    evidence=external_evidence(later,episode)
    episode.analysis_intent(binding=binding,commit=source,now_utc=end)
    if mutation=='seal_after_intent':
        seal=json.loads((case[0]/'returned/seal.json').read_bytes())
        seal['sealed_at']=(verify.timestamp(end)+timedelta(seconds=1)).isoformat()
        write(case[0],'returned/seal.json',seal)
        bound=json.loads((episode.directory/'control/source-binding.json').read_bytes())
        bound['seal']=ref(case[0],'returned/seal.json');write(episode.directory,'control/source-binding.json',bound)
    else:
        episode.finish(status='failed',cells=[],reason='invented',now_utc=end)
        receipt=json.loads((episode.directory/'failed.json').read_bytes())
        receipt['ended_at']=(verify.timestamp(end)-timedelta(seconds=1)).isoformat()
        write(episode.directory,'failed.json',receipt)
        evidence=external_evidence(case,episode)
    with pytest.raises(verify.VerificationError,match='phase'):
        verify.verify(root=case[0],now_utc=(verify.timestamp(end)+timedelta(seconds=2)).isoformat(),quiescence_evidence=evidence)

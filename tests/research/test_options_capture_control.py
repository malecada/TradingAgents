"""Disposable nineteen-shaped history, no actual data/network or financial work."""
import copy
from datetime import datetime,timezone,timedelta
import json
from pathlib import Path
import shutil
import subprocess
import pytest
from tradingagents.research_options_capture import control as m
from tradingagents.research.verify import verify_claim


def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True,stderr=subprocess.PIPE).strip()
def write(root,name,value):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(value if isinstance(value,bytes) else m.encoded(value))
def ref(root,name):return {'path':name,'sha256':m.file_sha(root/name)}
def commit(root):
    git(root,'add','.');git(root,'commit','-qm','invented fixture');return git(root,'rev-parse','HEAD')


def build_fixture(root):
    root.mkdir();git(root,'init','-q');git(root,'config','user.name','Synthetic');git(root,'config','user.email','test@example.invalid')
    actual=Path(__file__).resolve().parents[2]
    for package in ('research','research_amended','research_extended','research_spread','research_options_capture'):
        for p in (actual/'tradingagents'/package).glob('*.py'):write(root,'tradingagents/'+package+'/'+p.name,p.read_bytes())
    write(root,'design.json',b'{}');write(root,'policy.md',b'invented frozen policy');write(root,'charter.md',b'invented charter');write(root,'runner.py',b'# invented')
    family={'mechanism_id':m.MECHANISM,'attempt_budget':4,'prior_attempts':1}
    other={'mechanism_id':'invented-other','attempt_budget':30,'prior_attempts':0}
    dataset={'identity':'invented-history','exposures':[],'history_reference':'invented'}
    spec={'program_id':'invented','families':{m.FAMILY:family,'other':other},'datasets':{'history':dataset},'experiments':{}}
    oldruntime={p.name:m.file_sha(p) for p in (actual/'tradingagents/research').glob('*.py')}
    for i in range(19):
        name=f'history-{i:02d}'
        spec['experiments'][name]={'family':m.FAMILY if i<3 else 'other','stage':'exploratory','parent':None,'source_files':{'runner.py':m.file_sha(root/'runner.py')},'runtime_hashes':oldruntime,'charter':ref(root,'charter.md'),'selection':ref(root,'policy.md'),
            'inputs':{'design':{'path':'design.json','sha256':m.file_sha(root/'design.json'),'dataset':'history'}},'outputs':[],'cells':[],
            'windows':[{'dataset':'history','start':'2020-01-01T00:00:00+00:00','end':'2020-01-02T00:00:00+00:00','availability':'existing'}]}
    write(root,'history.json',spec);source=commit(root)
    for i,(name,exp) in enumerate(spec['experiments'].items()):
        directory=root/'research_runs'/name;(directory/'outputs').mkdir(parents=True)
        claim={'schema_version':1,'program_id':'invented','experiment_id':name,'started_at':f'2020-01-03T00:00:{i:02d}+00:00','source':source,'design_source':source,'registration':'history.json','registration_sha256':m.sha(m.encoded(spec)),
               'bindings':None,'bindings_sha256':None,'inputs':exp['inputs'],'experiment':exp,'family':spec['families'][exp['family']],
               'windows':[{**w,'identity':dataset['identity'],'state':'exposed'} for w in exp['windows']],'prior_exposures':[]}
        write(directory,'claim.json',claim)
        failed=i in (4,5,6);status='failed' if failed else 'complete'
        write(directory,status+'.json',{'status':status,'experiment_id':name,'claim_sha256':m.file_sha(directory/'claim.json'),'output_sha256':{},'source':source,'registration_sha256':claim['registration_sha256'],'cells':[],'cell_count':0,'unavailable_count':0})
    history_source=commit(root)
    now=datetime.now(timezone.utc);start=now+timedelta(days=1);end=start+timedelta(days=44)
    spec=copy.deepcopy(spec);spec['datasets']['future']={'identity':'invented-future','exposures':[],'history_reference':'new prospective'}
    protocol={'schema_version':1,'observation_window':{'start':start.isoformat(),'end':end.isoformat()},'worker_lease':{'not_before':start.isoformat(),'expires_at':(end+timedelta(days=1)).isoformat()},'analysis_inputs':{'observations':{'path':'returned/observations.json'}}}
    exp={'family':m.FAMILY,'stage':'exploratory','parent':'history-02','source_files':{'runner.py':m.file_sha(root/'runner.py')},'runtime_hashes':m.runtime_hashes(),'charter':ref(root,'charter.md'),'selection':ref(root,'policy.md'),'inputs':{'design':{'path':'design.json','sha256':m.file_sha(root/'design.json'),'dataset':'history'}},'outputs':['books.json'],'cells':[f'case-{i}' for i in range(8)],'windows':[{'dataset':'future','start':start.isoformat(),'end':end.isoformat(),'availability':'prospective'}],'episode_protocol':protocol}
    prior,_=m.inventory(root)
    grant={'schema_version':1,'target_experiment':m.TARGET,'program_id':'invented','family_id':m.FAMILY,'mechanism_id':m.MECHANISM,'original_budget':4,'prior_attempts':1,'increment':1,'effective_budget':5,'target_contract_sha256':m.sha(m.canonical(exp)),'history_source':history_source,'prior_claims':prior,'options_prior_ids':['history-00','history-01','history-02']}
    spec['experiments'][m.TARGET]=exp
    source=rebind(root,spec,grant)
    return root,spec,grant,source,datetime.now(timezone.utc).isoformat()


def rebind(root,spec,grant):
    exp=spec['experiments'][m.TARGET]
    grant['target_contract_sha256']=m.sha(m.canonical({k:v for k,v in exp.items() if k!='episode_book_grant'}))
    write(root,'review.md',b'invented independent review');write(root,'preflight-result.json',{'status':'pass','scope':'invented'})
    common={'target_experiment':m.TARGET,'target_contract_sha256':grant['target_contract_sha256'],'prior_claims_sha256':m.sha(m.canonical(grant['prior_claims']))}
    write(root,'approval.json',dict(common,decision='approve-single-prospective-options-book-episode',independent_review=ref(root,'review.md')))
    write(root,'preflight.json',dict(common,status='pass',reports=[ref(root,'preflight-result.json')]))
    grant['review']=ref(root,'approval.json');grant['preflight']=ref(root,'preflight.json');write(root,'grant.json',grant)
    exp['episode_book_grant']=ref(root,'grant.json');write(root,'episode.json',spec)
    return commit(root)


@pytest.fixture
def fixture(tmp_path):return build_fixture(tmp_path/'repo')
def start(f):return m.Episode.start(root=f[0],registration='episode.json',source=f[3],now_utc=f[4])


def source_binding(f,episode):
    root=f[0];write(root,'returned/observations.json',b'{}');write(root,'returned/manifest.json',{'invented':True})
    seal={'claim_sha256':episode.claim_hash,'worker_lease_sha256':m.sha(m.canonical(episode.claim['episode_protocol']['worker_lease'])),'manifest_sha256':m.file_sha(root/'returned/manifest.json'),'worker_stopped':True,'sealed_at':f[4]}
    write(root,'returned/seal.json',seal)
    episode.bind_source(seal=ref(root,'returned/seal.json'),manifest=ref(root,'returned/manifest.json'),now_utc=f[4])
    inputs={'observations':dict(ref(root,'returned/observations.json'),availability='complete')}
    review={'decision':'admit-frozen-options-source','claim_sha256':episode.claim_hash,'source_manifest_sha256':m.file_sha(root/'returned/manifest.json'),'inputs_sha256':m.sha(m.canonical(inputs))}
    write(root,'returned/review.json',review)
    binding={'claim_sha256':episode.claim_hash,'target_contract_sha256':f[2]['target_contract_sha256'],'source_manifest':ref(root,'returned/manifest.json'),'inputs':inputs,'independent_review':ref(root,'returned/review.json')}
    write(root,'returned/binding.json',binding);source=commit(root)
    return ref(root,'returned/binding.json'),source


def test_full_legacy_compatible_episode_once(fixture):
    e=start(fixture);fixture=(*fixture[:4],e.claim['episode_protocol']['observation_window']['end']);assert verify_claim(e.directory)['episode_protocol']==e.claim['episode_protocol']
    assert len(m.inventory(fixture[0],m.TARGET)[0])==19
    b,c=source_binding(fixture,e);e.analysis_intent(binding=b,commit=c,now_utc=fixture[4])
    with pytest.raises(FileExistsError):e.analysis_intent(binding=b,commit=c,now_utc=fixture[4])
    e.write_output('books.json',b'{}',now_utc=fixture[4])
    cells=[{'id':f'case-{i}','status':'unavailable','reason':'invented'} for i in range(8)]
    assert e.finish(status='complete',cells=cells,reason='invented',now_utc=fixture[4])['terminal']
    assert m.historical_verify(e.directory)['status']=='complete'
    assert m.verify_episode(root=fixture[0],now_utc=fixture[4])['status']=='complete'
    with pytest.raises(m.ControlError):m.Episode.resume(root=fixture[0],now_utc=fixture[4])
    with pytest.raises(m.ControlError):start(fixture)


@pytest.mark.parametrize('mutation',['increment','history','family','future','runtime','physical'])
def test_preclaim_guards(fixture,mutation):
    root,spec,grant,source,now=fixture
    if mutation=='increment':grant['increment']=2
    elif mutation=='history':grant['prior_claims'].pop('history-04')
    elif mutation=='family':spec['families'][m.FAMILY]['attempt_budget']=5
    elif mutation=='future':spec['experiments'][m.TARGET]['episode_protocol']['worker_lease']['not_before']='2020-01-01T00:00:00+00:00'
    elif mutation=='runtime':spec['experiments'][m.TARGET]['runtime_hashes']['research/verify.py']='0'*64
    elif mutation=='physical':write(root,'history.json',{})
    source=rebind(root,spec,grant)
    with pytest.raises(ValueError):m.Episode.start(root=root,registration='episode.json',source=source,now_utc=now)
    assert not (root/'research_runs'/m.TARGET).exists()


def test_stop_pending_then_lease_expiry_failed_no_reopen(fixture):
    e=start(fixture)
    assert e.finish(status='failed',cells=[],reason='unreachable worker',now_utc=fixture[4])=={'status':'stop-pending','terminal':False}
    assert not (e.directory/'failed.json').exists()
    expiry=e.claim['episode_protocol']['worker_lease']['expires_at']
    assert e.finish(status='failed',cells=[],reason='lease expired',now_utc=expiry)['terminal']
    with pytest.raises(m.ControlError):m.Episode.resume(root=fixture[0],now_utc=expiry)


def test_concurrent_claim_and_frozen_old_admission_refusal(fixture):
    from concurrent.futures import ThreadPoolExecutor
    from tradingagents.research.admission import admit
    def attempt():
        try:start(fixture);return 'started'
        except m.ControlError:return 'refused'
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(lambda _:attempt(),range(2)))==['refused','started']
    with pytest.raises(ValueError):admit(root=fixture[0],registration='episode.json',experiment=m.TARGET,source=fixture[3])


def test_analysis_corruption_cannot_replay_but_failure_closes(fixture):
    e=start(fixture);fixture=(*fixture[:4],e.claim['episode_protocol']['observation_window']['end']);b,c=source_binding(fixture,e);e.analysis_intent(binding=b,commit=c,now_utc=fixture[4])
    write(e.directory,'control/analysis-intent.json',{})
    with pytest.raises(ValueError):e.analysis_intent(binding=b,commit=c,now_utc=fixture[4])
    with pytest.raises(ValueError):e.write_output('books.json',b'{}',now_utc=fixture[4])
    assert e.finish(status='failed',cells=[],reason='corrupt analysis intent retained, no replay',now_utc=fixture[4])['terminal']


def test_binding_has_no_configuration_channel(fixture):
    e=start(fixture);fixture=(*fixture[:4],e.claim['episode_protocol']['observation_window']['end']);b,c=source_binding(fixture,e)
    value=json.loads((fixture[0]/b['path']).read_bytes());value['costs']={'fee':'0'}
    write(fixture[0],b['path'],value);c=commit(fixture[0]);b=ref(fixture[0],b['path'])
    with pytest.raises(m.ControlError):e.analysis_intent(binding=b,commit=c,now_utc=fixture[4])
    assert not (e.directory/'control/analysis-intent.json').exists()


def test_later_unrelated_active_claim_visible_and_allowed(fixture):
    e=start(fixture);root=fixture[0]
    old=copy.deepcopy(json.loads((root/'research_runs/history-03/claim.json').read_bytes()))
    spec=copy.deepcopy(fixture[1]);exp=copy.deepcopy(spec['experiments']['history-03']);name='later-unrelated'
    spec['experiments'][name]=exp;write(root,'later.json',spec);source=commit(root)
    old.update(experiment_id=name,experiment=exp,source=source,design_source=source,registration='later.json',registration_sha256=m.sha(m.encoded(spec)),started_at=(m.utc(fixture[4])+timedelta(seconds=1)).isoformat())
    # Legacy exposures include the new prospective dataset but its history is empty.
    directory=root/'research_runs'/name;(directory/'outputs').mkdir(parents=True);write(directory,'claim.json',old)
    resumed=m.Episode.resume(root=root,now_utc=(m.utc(fixture[4])+timedelta(seconds=2)).isoformat())
    assert resumed.claim_hash==e.claim_hash
    assert name in m.inventory(root,m.TARGET,allow_active=True)[0]


def test_stop_ack_and_design_input_mutation(fixture):
    e=start(fixture);root=fixture[0]
    ack={'claim_sha256':e.claim_hash,'worker_lease_sha256':m.sha(m.canonical(e.claim['episode_protocol']['worker_lease'])),'stopped_at':fixture[4],'status':'stopped'}
    write(root,'ack.json',ack);e.acknowledge_stop(ack=ref(root,'ack.json'),now_utc=fixture[4])
    write(root,'design.json',b'changed')
    with pytest.raises(m.ControlError):m.Episode.resume(root=root,now_utc=fixture[4])


def test_analysis_observation_boundary_and_retained_intent(fixture):
    e=start(fixture);b,c=source_binding(fixture,e)
    end=e.claim['episode_protocol']['observation_window']['end']
    before=(m.utc(end)-timedelta(microseconds=1)).isoformat()
    with pytest.raises(m.ControlError,match='observation end'):
        e.analysis_intent(binding=b,commit=c,now_utc=before)
    assert not (e.directory/'control/analysis-intent.json').exists()
    e.analysis_intent(binding=b,commit=c,now_utc=end)
    value=json.loads((e.directory/'control/analysis-intent.json').read_bytes())
    value['started_at']=before;write(e.directory,'control/analysis-intent.json',value)
    with pytest.raises(m.ControlError,match='observation end'):
        m.verify_episode(root=fixture[0],now_utc=end)


def test_early_seal_can_fail_close_without_analysis(fixture):
    e=start(fixture);b,c=source_binding(fixture,e)
    with pytest.raises(m.ControlError,match='observation end'):
        e.analysis_intent(binding=b,commit=c,now_utc=fixture[4])
    assert e.finish(status='failed',cells=[],reason='early source failure; no analysis',now_utc=fixture[4])['terminal']


@pytest.mark.parametrize('status',['complete','failed'])
@pytest.mark.parametrize('kind',['symlink','directory','fifo','pending','unexpected'])
def test_finish_rejects_unsafe_output_before_hashing(fixture,monkeypatch,status,kind):
    import os
    e=start(fixture);source_binding(fixture,e)
    path=e.directory/'outputs'/('books.json' if kind in ('symlink','directory','fifo') else '.pending-invented' if kind=='pending' else 'unregistered.json')
    if kind=='symlink':path.symlink_to(fixture[0]/'design.json')
    elif kind=='directory':path.mkdir()
    elif kind=='fifo':os.mkfifo(path)
    else:path.write_bytes(b'invented retained partial')
    original=m.file_sha;reads=[]
    def checked(candidate):
        if Path(candidate)==path:
            reads.append(str(candidate));raise AssertionError('unsafe output was read')
        return original(candidate)
    monkeypatch.setattr(m,'file_sha',checked)
    with pytest.raises(m.ControlError,match='terminal publication refused'):
        e.finish(status=status,cells=[],reason='invented',now_utc=fixture[4])
    assert not reads and path.lstat()
    assert not (e.directory/'complete.json').exists() and not (e.directory/'failed.json').exists()

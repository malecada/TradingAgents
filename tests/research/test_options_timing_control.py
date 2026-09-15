"""Disposable twenty-predecessor timing lifecycle, invented evidence only."""
import copy
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import pytest
from tests.research import test_options_capture_control as old
from tradingagents.research_options_capture import independent_verify as old_verify
from tradingagents.research_options_timing import control as m
from tradingagents.research_options_timing import independent_verify as independent

write,ref,commit=old.write,old.ref,old.commit
PARENT='options-episode-20260911'


def now():return datetime.now(timezone.utc).isoformat()


def build_fixture(root):
    initial=old.build_fixture(root)
    parent=old.start(initial)
    stopped=now()
    ack={'claim_sha256':parent.claim_hash,'worker_lease_sha256':m.sha(m.canonical(parent.claim['episode_protocol']['worker_lease'])),'stopped_at':stopped,'status':'stopped'}
    write(root,'parent-return/ack.json',ack)
    parent.acknowledge_stop(ack=ref(root,'parent-return/ack.json'),now_utc=stopped)
    write(root,'parent-return/observation.json',{'synthetic_only':True,'observed_at':stopped})
    review={'decision':'verify-options-worker-quiescence','claim_sha256':parent.claim_hash,'worker_lease_sha256':ack['worker_lease_sha256'],'mode':'sealed-worker-exit','observed_at':stopped,'evidence':ref(root,'parent-return/observation.json')}
    write(root,'parent-return/quiescence.json',review);quiet_commit=commit(root)
    quiet=dict(ref(root,'parent-return/quiescence.json'),commit=quiet_commit)
    ended=now()
    parent.finish(status='failed',cells=[{'id':c,'status':'unavailable','reason':'invented initial capture unavailable'} for c in parent.claim['experiment']['cells']],reason='invented',now_utc=ended)
    checked=old_verify.verify(root=root,now_utc=now(),quiescence_evidence=quiet)
    terminal=json.loads((parent.directory/'failed.json').read_bytes())
    close={'terminal_sha256':m.file_sha(parent.directory/'failed.json'),'quiescence_evidence':quiet,'terminal_verification':checked,'cell_count':8,'unavailable_count':8,'financial_output_count':0,'analysis_intent':False,'total_identities':20}
    write(root,'parent-return/closure.json',close)
    cert={'schema_version':1,'experiment_id':PARENT,'claim_sha256':parent.claim_hash,'terminal_sha256':close['terminal_sha256'],'control_sha256':terminal['control_sha256'],'output_sha256':{},'closed_at':terminal['ended_at'],'quiescence_evidence':quiet,'closure_review':ref(root,'parent-return/closure.json'),'prior_claims_sha256':m.sha(m.canonical(initial[2]['prior_claims'])),'original_grant':parent.claim['episode_book_grant']}
    write(root,'closed-parent.json',cert)
    actual=Path(__file__).resolve().parents[2]
    for p in (actual/'tradingagents/research_options_timing').glob('*.py'):
        write(root,'tradingagents/research_options_timing/'+p.name,p.read_bytes())
    baseline=commit(root)
    spec=copy.deepcopy(initial[1]);exp=copy.deepcopy(spec['experiments'][PARENT])
    exp.pop('episode_book_grant');exp['parent']=PARENT;exp['runtime_hashes']=m.runtime_hashes()
    start=datetime.now(timezone.utc)+timedelta(days=2);end=start+timedelta(days=44)
    exp['episode_protocol'].update(schema_version=3,hourly_acquisition_delay_ms=2000,observation_window={'start':start.isoformat(),'end':end.isoformat()},worker_lease={'not_before':start.isoformat(),'expires_at':(end+timedelta(hours=1)).isoformat()})
    spec['datasets']['timing-future']={'identity':'invented-timing-future','exposures':[],'history_reference':'new prospective'}
    exp['windows']=[{'dataset':'timing-future','start':start.isoformat(),'end':end.isoformat(),'availability':'prospective'}]
    spec['experiments'][m.TARGET]=exp
    prior,_=m.inventory(root)
    grant={'schema_version':2,'target_experiment':m.TARGET,'program_id':'invented','family_id':m.FAMILY,'mechanism_id':m.MECHANISM,'original_budget':4,'prior_attempts':1,'increment':1,'effective_budget':6,'prior_effective_budget':5,'parent_experiment':PARENT,'consumed_episode_grant':parent.claim['episode_book_grant'],'closed_parent':ref(root,'closed-parent.json'),'history_source':baseline,'prior_claims':prior,'options_prior_ids':['history-00','history-01','history-02',PARENT]}
    source=rebind(root,spec,grant)
    return root,spec,grant,source,now()


def rebind(root,spec,grant):
    exp=spec['experiments'][m.TARGET]
    grant['target_contract_sha256']=m.sha(m.canonical({k:v for k,v in exp.items() if k!='episode_book_grant'}))
    common={'target_experiment':m.TARGET,'target_contract_sha256':grant['target_contract_sha256'],'prior_claims_sha256':m.sha(m.canonical(grant['prior_claims']))}
    write(root,'timing-review.md',b'invented timing review');write(root,'timing-resource.json',{'synthetic_only':True})
    write(root,'timing-approval.json',dict(common,decision='approve-single-timing-corrected-options-episode',independent_review=ref(root,'timing-review.md')))
    write(root,'timing-preflight.json',dict(common,status='pass',reports=[ref(root,'timing-resource.json')]))
    grant.update(review=ref(root,'timing-approval.json'),preflight=ref(root,'timing-preflight.json'))
    write(root,'timing-grant.json',grant);exp['episode_book_grant']=ref(root,'timing-grant.json')
    write(root,'timing.json',spec)
    return commit(root)


def start(f):return m.Episode.start(root=f[0],registration='timing.json',source=f[3],now_utc=f[4])


@pytest.fixture
def case(tmp_path):return build_fixture(tmp_path/'repo')


def test_twenty_inventory_and_exclusive_successor(case):
    before=m.inventory(case[0])[0];assert len(before)==20
    assert before[PARENT]['control_sha256']
    e=start(case)
    assert m.inventory(case[0],m.TARGET)[0]==before
    assert independent.verify(root=case[0],now_utc=case[4])['history_count']==20
    with pytest.raises(ValueError):start(case)
    assert e.claim['episode_protocol']['hourly_acquisition_delay_ms']==2000


@pytest.mark.parametrize('mutation',['budget','parent','prior','delay','schema','old-grant','physical-old','runtime'])
def test_preclaim_refusals(case,mutation):
    root,spec,grant,source,clock=case
    exp=spec['experiments'][m.TARGET]
    if mutation=='budget':grant['effective_budget']=7
    elif mutation=='parent':exp['parent']='history-02'
    elif mutation=='prior':grant['prior_claims'].pop(PARENT)
    elif mutation=='delay':exp['episode_protocol']['hourly_acquisition_delay_ms']=1999
    elif mutation=='schema':exp['episode_protocol']['schema_version']=2
    elif mutation=='old-grant':grant['consumed_episode_grant']['sha256']='0'*64
    elif mutation=='physical-old':write(root,'history.json',{})
    else:exp['runtime_hashes']['research_options_capture/control.py']='0'*64
    source=rebind(root,spec,grant)
    with pytest.raises((ValueError,KeyError)):m.Episode.start(root=root,registration='timing.json',source=source,now_utc=now())
    assert not (root/'research_runs'/m.TARGET).exists()

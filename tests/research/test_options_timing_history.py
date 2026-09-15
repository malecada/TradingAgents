"""Closed twentieth-protocol reconstruction over full live synthetic history."""
import copy
import json
import pytest
from tests.research.test_options_timing_control import build_fixture,start,now,write,ref,commit,PARENT
from tradingagents.research_options_timing import closed_history as h,control


@pytest.fixture
def case(tmp_path):return build_fixture(tmp_path/'repo')


def check(case,**changes):
    root,spec,grant,source,_=case
    successor={'experiment_id':control.TARGET,'source':source,'design_source':source,'grant':spec['experiments'][control.TARGET]['episode_book_grant']}
    successor.update(changes)
    return h.verify_parent(root=root,certificate=grant['closed_parent'],source=source,design_source=source,now_utc=now(),successor=successor)


def test_full_visible_successor_and_unbound_mechanism_refusal(case):
    assert check(case)['history_count']==20
    e=start(case);assert check(case)['status']=='failed'
    # Existing frozen verifier remains unchanged and rejects this descendant;
    # new reconstruction explicitly accounts for it in the full live tree.
    from tradingagents.research_options_capture import independent_verify as old
    cert=json.loads((case[0]/case[2]['closed_parent']['path']).read_bytes())
    with pytest.raises(ValueError,match='same-family'):old.verify(root=case[0],now_utc=now(),quiescence_evidence=cert['quiescence_evidence'])
    spec=copy.deepcopy(case[1]);spec['experiments']['another-options']=copy.deepcopy(e.claim['experiment'])
    write(case[0],'extra.json',spec);c=commit(case[0])
    wrong=copy.deepcopy(e.claim);wrong.update(experiment_id='another-options',source=c,design_source=c,registration='extra.json',registration_sha256=control.file_sha(case[0]/'extra.json'))
    write(case[0],'research_runs/another-options/claim.json',wrong)
    with pytest.raises(ValueError):check(case)


@pytest.mark.parametrize('mutation',['control','stop-reference','quiescence','terminal-count','original-grant','successor-source','successor-grant','equal-parent-end'])
def test_closed_boundary_attacks(case,mutation):
    root=case[0]
    if mutation.startswith('successor') or mutation=='equal-parent-end':
        e=start(case)
        if mutation=='successor-source':
            with pytest.raises(ValueError):check(case,source='0'*40)
            return
        if mutation=='successor-grant':
            with pytest.raises(ValueError):check(case,grant={'path':'timing-grant.json','sha256':'0'*64})
            return
        claim=json.loads((e.directory/'claim.json').read_bytes());claim['started_at']=json.loads((root/'research_runs'/PARENT/'failed.json').read_bytes())['ended_at'];write(e.directory,'claim.json',claim)
    elif mutation=='control':write(root,f'research_runs/{PARENT}/control/stop-ack.json',{})
    elif mutation=='stop-reference':write(root,'parent-return/ack.json',{})
    elif mutation=='quiescence':write(root,'parent-return/observation.json',b'changed')
    elif mutation=='terminal-count':
        terminal=json.loads((root/'research_runs'/PARENT/'failed.json').read_bytes());terminal['unavailable_count']=0;write(root,f'research_runs/{PARENT}/failed.json',terminal)
    else:write(root,'grant.json',{})
    with pytest.raises((ValueError,KeyError)):check(case)


@pytest.mark.parametrize('mutation',['omitted','outputs','controls','claims'])
def test_same_invocation_proof_mapping_must_match_grant(case,monkeypatch,mutation):
    start(case)
    original=h.verify_parent
    def changed(**kwargs):
        proof=original(**kwargs)
        if mutation=='omitted':
            proof['verified_inventory'].pop('history-04');proof['verified_claims'].pop('history-04')
        elif mutation=='outputs':proof['verified_inventory'][PARENT]['output_sha256']={'fake.json':'0'*64}
        elif mutation=='controls':proof['verified_inventory'][PARENT]['control_sha256']={}
        else:proof['verified_claims'].pop(PARENT)
        return proof
    monkeypatch.setattr(h,'verify_parent',changed)
    from tradingagents.research_options_timing import independent_verify
    with pytest.raises(ValueError):independent_verify.verify(root=case[0],now_utc=now())
    with pytest.raises(ValueError):control.Episode.resume(root=case[0],now_utc=now())


def test_old_bytes_changed_between_calls_are_not_cached(case):
    start(case)
    from tradingagents.research_options_timing import independent_verify
    assert independent_verify.verify(root=case[0],now_utc=now())['status']=='active'
    write(case[0],'parent-return/ack.json',{'changed_between_calls':True})
    with pytest.raises(ValueError):independent_verify.verify(root=case[0],now_utc=now())

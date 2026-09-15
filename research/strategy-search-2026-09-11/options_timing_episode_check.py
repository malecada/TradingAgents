"""Finite synthetic full worker episode. No HTTP or financial evaluation.

A real frozen package/assignment is copied under a retained temporary root.
Only acquisition and wall-clock waiting are substituted. Actual adapter, source
checks, journals, calendar, selection and seals run. Run under resource_guard_v2.
"""
import argparse
import base64
from bisect import bisect_right
from datetime import datetime,timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from unittest.mock import patch

from tradingagents.research_options_timing import worker
from tradingagents.research_options_timing.journal import encode,digest
from tradingagents.research_options_timing.schedule import calendar,DAY,HOUR,groups
from tradingagents.research_options_timing.transport import request_url

ROOT=Path(__file__).resolve().parents[2]
_spec=importlib.util.spec_from_file_location('synthetic_episode_fixture',ROOT/'tests/research/test_options_capture_adapter.py')
fixture=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(fixture)


def main(report_path,resume_root=None):
    if resume_root is not None:
        temp=Path(resume_root);package=temp/'package';data=temp/'data'
        raw=(package/'assignment.json').read_bytes();assignment=json.loads(raw);expected=digest(raw)
        files=assignment['package_files'];t=assignment['entry_ms']
    else:
        temp=Path(tempfile.mkdtemp(prefix='options-timing-full-episode-'));package=temp/'package';package.mkdir();data=temp/'data'
        files={}
        for name in worker.PACKAGE_FILES:
            source=ROOT/('scripts/options_timing_release_bootstrap.py' if name=='release_bootstrap.py' else name)
            dest=package/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);files[name]=digest(dest.read_bytes())
        t=fixture.T
        def iso(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat()
        claim={'source':'b'*40,'authority':'local-master-only','synthetic':True,'episode_protocol':{'schema_version':3,'hourly_acquisition_delay_ms':2000,'worker_lease':{'not_before':iso(t-120000),'expires_at':iso(t+45*DAY+60000)},'observation_window':{'start':iso(t),'end':iso(t+44*DAY+5000)}}}
        (package/'claim.json').write_bytes(encode(claim))
        assignment={'schema_version':1,'entry_ms':t,'lease_not_before_ms':t-120000,'lease_expires_ms':t+45*DAY+60000,
            'claim_path':'claim.json','claim_sha256':digest(encode(claim)),'package_files':files,'journal_caps':worker.CAPS,'terminal_reserves':worker.RESERVES,
            'authority':'raw-worker-only','target':'options-timing-20260915','source_commit':'b'*40,'data_root':str(data),'host_identity':os.uname().nodename}
        raw=encode(assignment);(package/'assignment.json').write_bytes(raw);expected=digest(raw)
    options,futures=fixture.metadata()
    expiry=t+7*DAY;date=datetime.fromtimestamp(expiry/1000,timezone.utc).strftime('%y%m%d')
    for row in options['optionSymbols']:
        row['expiryDate']=expiry;row['symbol']=row['underlying'][:-4]+'-'+date+'-100-'+row['side'][0]
    consumed=set();inventory={};latest_deadline=t-60001
    if data.exists():
        chosen=worker.selected_projection(json.loads((data/'selection.json').read_bytes())['result']) if (data/'selection.json').exists() else None
        frozen=calendar(t,chosen);slotmap={(name,s['id']):s for name,rows in frozen.items() for s in rows}
        for path in sorted(data.rglob('*')):
            if not path.is_file():continue
            content=path.read_bytes();relative=path.relative_to(data).as_posix()
            inventory[relative]={'sha256':digest(content),'bytes':len(content)}
            if path.name.startswith('intent-'):
                intent=json.loads(content);key=(path.parent.name,intent['slot']);consumed.add(key)
                latest_deadline=max(latest_deadline,slotmap[key]['deadline_ms'])
    before_path=Path(str(report_path)+'.inventory-before.json')
    with before_path.open('x') as before:json.dump(inventory,before,sort_keys=True);before.write('\n')
    clock=[latest_deadline+1 if resume_root is not None else t-60000];times=sorted({s['scheduled_ms'] for rows in calendar(t).values() for s in rows})
    attempts=[];initial_consumed=len(consumed);groups_seen=0;started=time.monotonic();audit=Path(str(report_path)+'.attempts.jsonl').open('x');progress=Path(str(report_path)+'.progress.jsonl').open('x')
    def checkpoint(stage):
        progress.write(json.dumps({'stage':stage,'fixture_root':str(temp),'assignment_sha256':expected,'elapsed_seconds':time.monotonic()-started,'synthetic_requests':len(attempts),'groups':groups_seen,'clock_ms':clock[0],'proof_script_sha256':digest(Path(__file__).read_bytes()),'prior_consumed_intents':initial_consumed,'inventory_before_sha256':digest(before_path.read_bytes())})+'\n');progress.flush();os.fsync(progress.fileno())
    checkpoint('start')
    def sleep(unused):
        index=bisect_right(times,clock[0]);clock[0]=times[index] if index<len(times) else assignment['lease_expires_ms']
    def payload(slot):
        recipe=slot['request'];params=recipe['parameters'];route=recipe['endpoint'].split('/')[-1];at=slot['scheduled_ms']
        if route=='exchangeInfo':return options if '/eapi/' in recipe['endpoint'] else futures
        if route=='fundingInfo':return [{'symbol':a+'USDT','fundingIntervalHours':8,'adjustedFundingRateCap':'0.01','adjustedFundingRateFloor':'-0.01'} for a in ('BTC','ETH')]
        if route=='time':return {'serverTime':at+250}
        if route=='index':return {'indexPrice':'100','time':at+250,'underlying':params['underlying']}
        if route=='depth':
            result={'T':at+200,'E':at+250,'lastUpdateId':1,'bids':[['100','100']],'asks':[['100.1','100']]}
            if '/eapi/' in recipe['endpoint']:result.update(bids=[['2','100']],asks=[['2.1','100']])
            return result
        if route=='premiumIndex':return {'symbol':params['symbol'],'markPrice':'100','time':at+250,'nextFundingTime':t+((at-t)//(8*HOUR)+1)*8*HOUR}
        if route=='mark':return [{'symbol':params['symbol'],'markPrice':'2.05','delta':'0.5' if params['symbol'].endswith('-C') else '-0.5'}]
        if route=='fundingRate':
            start,end=params['startTime'],params['endTime'];first=(start-t+8*HOUR-1)//(8*HOUR)
            return [{'symbol':params['symbol'],'fundingTime':event,'fundingRate':'0.0001','markPrice':'100'} for k in range(first,(end-t)//(8*HOUR)+1) if (event:=t+k*8*HOUR)>=t]
        raise ValueError('unhandled fixed source route')
    def acquire(journal,names,*,deadline_ms):
        nonlocal groups_seen
        for name in names:
            identity=(journal.path.name,name)
            if identity in consumed:raise RuntimeError('duplicate attempted slot across bounded segments')
            consumed.add(identity);audit.write(json.dumps({'journal':identity[0],'slot':name})+'\n');audit.flush();os.fsync(audit.fileno())
            slot=journal.slots[name];at=clock[0];body=json.dumps(payload(slot),separators=(',',':')).encode();sha=digest(body)
            assert len(body)<=slot['body_cap']
            meta={'request_url':request_url(slot['request']),'child_started':True,'attempted':True,'request_ms':at+200,'request_monotonic_ns':(at+200)*1000000,
                'http_status':200,'body_complete':True,'error':None,'retrieval_ms':at+290,'retrieval_monotonic_ns':(at+290)*1000000,
                'body_bytes':len(body),'body_sha256':sha,'controller_retrieval_ms':at+300,'controller_retrieval_monotonic_ns':(at+300)*1000000,
                'controller_window_start_ms':at,'controller_window_start_monotonic_ns':at*1000000,'controller_deadline_ms':deadline_ms,'controller_deadline_monotonic_ns':deadline_ms*1000000,
                'child_exit_code':0,'clock_consistent':True,'within_controller_deadline':True,'synthetic_no_http':True}
            journal.partial(name,body);journal.record(name,body,metadata=meta);attempts.append(name)
        clock[0]+=300
        groups_seen+=1
        if groups_seen%25==0:checkpoint('acquisition')
        return {'halt_on_access_restriction':False}
    with patch.object(worker,'__file__',str(package/'tradingagents/research_options_timing/worker.py')):
        source=worker.run(package,data,expected,acquisition=acquire,now=lambda:clock[0],sleep=sleep)
    checkpoint('sealed');progress.close();audit.close()
    status_counts={};skipped=0;receipts=0;total_attempted_receipts=0;total_daily=0;total_final=0
    for name in worker.JOURNALS:
        paths=list((data/name).glob('receipt-*.json'));receipts+=len(paths)
        for path in paths:
            value=json.loads(path.read_bytes());status_counts[value['status']]=status_counts.get(value['status'],0)+1
            skipped+=value.get('metadata',{}).get('reason')=='frozen post-exit unused slot'
            attempted=value.get('metadata',{}).get('synthetic_no_http') is True
            total_attempted_receipts+=attempted
            total_daily+=attempted and name=='daily';total_final+=attempted and name=='final'
    result={'scope':'Full synthetic worker lifecycle only; no HTTP or financial evaluation. Known and selected raw timestamps follow sequential fake-clock acquisition.','source_hashes':files,'fixture_root':str(temp),'assignment_sha256':expected,
        'elapsed_seconds':time.monotonic()-started,'source_status':source['status'],'source_seal_sha256':digest((data/'source-seal.json').read_bytes()),
        'intended_slots':17144,'receipts':receipts,'status_counts':status_counts,'synthetic_requests':len(attempts),'unique_synthetic_requests':len(set(attempts)),'total_completed_synthetic_receipts':total_attempted_receipts,'prior_consumed_intents':initial_consumed,
        'inventory_before_path':str(before_path),'inventory_before_sha256':digest(before_path.read_bytes()),'no_duplicate_attempt_across_segments':True,
        'postexit_unused_receipts':skipped,'segment_daily_requests':sum(a.startswith('d') for a in attempts),'segment_final_requests':sum(a.startswith('final-') for a in attempts),
        'total_completed_daily_requests':total_daily,'total_completed_final_requests':total_final,
        'prior_members_unchanged':all(digest((data/name).read_bytes())==item['sha256'] for name,item in inventory.items()),
        'calendar_hours':1057,'selected_hold_hours':144,'fake_clock_end_ms':clock[0],'final_history_scheduled_ms':t+45*DAY,
        'complete':source['status']=='complete' and receipts==17144 and len(attempts)==len(set(attempts)) and total_attempted_receipts+skipped+sum(v for k,v in status_counts.items() if k!='received')==17144}
    with Path(report_path).open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    if not result['complete']:raise RuntimeError('synthetic lifecycle did not complete full denominator')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report',required=True);parser.add_argument('--resume-root');args=parser.parse_args();main(args.report,args.resume_root)

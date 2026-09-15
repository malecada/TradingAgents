"""Synthetic calendar storage arithmetic and bounded journal lifecycle measurement.

No public transport or market bodies. Direct near-complete fixture construction
is distinguished from timed fsynced Journal operations. Existing evidence stays
immutable. Invoke through resource_guard_v2.py, with a fresh report path.
"""
import argparse
import base64
import contextlib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import tempfile
import time

from tradingagents.research_options_capture import worker
from tradingagents.research_options_capture.journal import Journal,encode,digest
from tradingagents.research_options_capture.schedule import calendar,groups,ASSETS,DAY
from tradingagents.research_options_capture.transport import request_url
_spec=importlib.util.spec_from_file_location('synthetic_resource_fixture',Path(__file__).resolve().parents[2]/'tests/research/test_options_capture_adapter.py')
fixture=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(fixture)

CLAIM=digest(b'{"invented":true}')


def metadata(slot,raw):
    at=slot['scheduled_ms'];mono=2**63-1
    return {'request_url':request_url(slot['request']),'child_started':True,'attempted':True,
            'request_ms':at,'request_monotonic_ns':mono-5000000000,'http_status':200,
            'body_complete':True,'error':'\uffff'*300,'retrieval_ms':at+5000,
            'retrieval_monotonic_ns':mono,'body_bytes':len(raw),'body_sha256':digest(raw),
            'controller_retrieval_ms':at+5000,'controller_retrieval_monotonic_ns':mono,
            'controller_window_start_ms':at,'controller_window_start_monotonic_ns':mono-5000000000,
            'controller_deadline_ms':at+5000,'controller_deadline_monotonic_ns':mono,
            'child_exit_code':-999999,'clock_consistent':True,'within_controller_deadline':True}


def encoded_members(slot,raw):
    name=slot['id']
    intent=encode({'kind':'intent','claim_sha256':CLAIM,'slot':name,'request':slot['request'],'now_ms':slot['scheduled_ms']+5000})
    receipt=encode({'kind':'receipt','claim_sha256':CLAIM,'slot':name,'request':slot['request'],'status':'received',
                    'body_base64':base64.b64encode(raw).decode(),'body_sha256':digest(raw),'body_bytes':len(raw),'metadata':metadata(slot,raw)})
    return intent,receipt


def arithmetic():
    selections={a:{'call':a+'-270131-'+('0'*50)+'1-C','put':a+'-270131-'+('0'*50)+'1-P','expiry_ms':fixture.T+30*DAY} for a in ASSETS}
    calendars=calendar(fixture.T,selections);rows={};cache={}
    for name,slots in calendars.items():
        total=0;rounded=0;production_members=0;max_receipt=0;worst_fragmented=0
        for slot in slots:
            cap=slot['body_cap']
            raw=cache.setdefault(cap,b'x'*cap)
            intent,receipt=encoded_members(slot,raw)
            frame=max(8192,(cap+62)//63);lengths=[min(frame,cap-i) for i in range(0,cap,frame)]
            total+=len(intent)+len(receipt)+cap
            rounded+=sum(math.ceil(n/4096)*4096 for n in (len(intent),len(receipt),*lengths))
            worst_fragmented+=math.ceil(len(intent)/4096)*4096+math.ceil(len(receipt)/4096)*4096+cap+64*4095
            production_members+=2+len(lengths);max_receipt=max(max_receipt,len(receipt))
        spec=encode({'claim_sha256':CLAIM,'slots':slots,'total_cap':worker.CAPS[name],'terminal_reserve':worker.RESERVES[name]})
        total+=len(spec);rounded+=math.ceil(len(spec)/4096)*4096;production_members+=2
        # Enforced Journal caps count recovery, pending staging and seal bytes;
        # maximum simultaneous members is70*slot_count+10, regardless lifecycle.
        count_cap=70*len(slots)+10
        rows[name]={'slots':len(slots),'maximum_body_raw_bytes':sum(s['body_cap'] for s in slots),
            'all_received_serialized_bytes':total,'serialized_spec_bytes':len(spec),
            'production_prefix_regular_file_blocks_bytes':rounded,'production_received_members':production_members,
            'legal64prefix_received_rounding_upper_bytes':worst_fragmented+len(spec)+4095,
            'largest_serialized_receipt_bytes':max_receipt,'additional_single_publication_staging_bytes':max(max_receipt,len(spec)),
            'logical_cap':worker.CAPS[name],'terminal_reserve':worker.RESERVES[name],
            'nonterminal_cap':worker.CAPS[name]-worker.RESERVES[name],
            'all_received_plus_one_staging_fits_nonterminal':total+max(max_receipt,len(spec))<=worker.CAPS[name]-worker.RESERVES[name],
            'all_lifecycle_member_cap':count_cap,
            'all_lifecycle_regular_file_allocation_upper_bytes':worker.CAPS[name]+count_cap*4095}
    logical=sum(worker.CAPS.values())+64*worker.MIB
    members=sum(r['all_lifecycle_member_cap'] for r in rows.values())+128
    physical=logical+members*4095
    return {'journals':rows,'logical_with_auxiliary_cap_bytes':logical,'logical_fits2GiB':logical<=2*1024**3,
        'allocation_unit_ceiling':4096,'all_lifecycle_member_upper':members,
        'regular_file_allocation_upper_bytes':physical,'fits8GiB_regular_file_allocation':physical<=8*1024**3,
        'remaining8GiB_after_regular_file_bound':8*1024**3-physical,
        'qualification':'Exact serialized all-received maximum-sized invented bodies and pessimistic metadata; this is not semantic HTTP admission. Global logical/member caps also bound recovery, failed publication and seals. Rounded regular-file bound includes legal64-prefix fragmentation and staging; filesystem metadata, unrelated writers and external release/runtime files are outside that filedata bound. A reservation is not a guarantee of future free disk.'}


def write(path,raw):
    with path.open('xb') as stream:stream.write(raw)


def journal_args(claim,slots,name,check=lambda:None):
    return dict(claim_path=claim,claim_sha256=CLAIM,slots=slots,total_cap=worker.CAPS[name],terminal_reserve=worker.RESERVES[name],check_source=check)


def main(report_path):
    report={'scope':'Invented engineering only; no HTTP, empirical claim or economic result.','source_hashes':{n:digest(Path(worker.__file__).with_name(n+'.py').read_bytes()) for n in ('journal','schedule','worker','transport')},'started_wall_ms':time.time_ns()//1000000}
    progress=Path(str(report_path)+'.progress.jsonl').open('x')
    def checkpoint(stage):
        progress.write(json.dumps({'stage':stage,'report':report})+'\n');progress.flush();os.fsync(progress.fileno())
    begin=time.monotonic();report['arithmetic']=arithmetic();report['arithmetic_seconds']=time.monotonic()-begin;checkpoint('arithmetic')
    with tempfile.TemporaryDirectory(prefix='options-worker-resource-') as temp:
        root=Path(temp);claim=root/'claim.json';write(claim,b'{"invented":true}')
        initial,known,_=fixture.initial();selection=fixture.selected();selected=worker.selected_projection(selection)
        rich=json.loads(base64.b64decode(initial['body_base64']))
        rich['optionSymbols'].extend({'symbol':'OTHER-'+str(i),'underlying':'OTHERUSDT','padding':'x'*350} for i in range(9996))
        rich['padding']=''
        used=len(json.dumps(rich,separators=(',',':')).encode());rich['padding']='x'*(5*1024**2-used)
        initial=fixture.receipt(initial['request'],rich,fixture.T-60000)
        assert initial['body_bytes']==5*1024**2 and len(rich['optionSymbols'])==10000
        report['entry_metadata_fixture']={'raw_bytes':initial['body_bytes'],'option_rows':10000,'qualification':'Four eligible invented contracts;9996 irrelevant invented contracts plus padding; no current exchange metadata.'}
        calendars=calendar(fixture.T,selected)
        # Actual initial journal creation, with source callback representing a
        # frozen eight-file ~2MiB inventory hash (no history validation).
        source=b's'*262144
        def check():
            for unused in range(8):hashlib.sha256(source).digest()
        t=time.monotonic()
        with contextlib.ExitStack() as stack:
            journals={n:stack.enter_context(Journal(root/('initial-'+n),**journal_args(claim,calendars[n],n,check))) for n in ('bootstrap','known','daily','final')}
            report['initial_four_journal_open_seconds']=time.monotonic()-t
            boot=journals['bootstrap'];boot.begin_group([s['id'] for s in calendars['bootstrap']],now_ms=fixture.T-60000)
            for s in calendars['bootstrap']:
                row=initial if s['id']=='initial-options-rules' else None
                body=base64.b64decode(row['body_base64']) if row else b'{}'
                boot.partial(s['id'],body);boot.record(s['id'],body,metadata=row['metadata'] if row else {})
            # Timed five-second critical section has no HTTP latency. It includes
            # actual adapter selection, full8456-slot selected specification,
            # full verification/recover and durable selected group publication.
            t=time.monotonic();kn=journals['known'];names=groups(calendars['known'])[0][1]
            kn.begin_group(names,now_ms=fixture.T)
            for n in names:
                row=known[n.removeprefix('h0000-')];body=base64.b64decode(row['body_base64'])
                kn.partial(n,body);kn.record(n,body,metadata=row['metadata'])
            from tradingagents.research_options_capture.adapter import select_initial
            parsed={n:json.loads((kn.path/('receipt-'+n+'.json')).read_bytes()) for n in names}
            chosen=select_initial(json.loads((boot.path/'receipt-initial-options-rules.json').read_bytes()),worker.initial_roles(parsed),entry_ms=fixture.T)
            worker.publish(root/'selection.json',{'result':chosen,'assignment_sha256':'0'*64})
            generated=calendar(fixture.T,worker.selected_projection(chosen))
            sj=stack.enter_context(Journal(root/'initial-selected',**journal_args(claim,generated['selected'],'selected',check)))
            sj.recover(now_ms=fixture.T)
            selected_names=groups(generated['selected'])[0][1];sj.begin_group(selected_names,now_ms=fixture.T)
            for n in selected_names:sj.partial(n,b'{}');sj.record(n,b'{}',metadata={'invented':True})
            report['entry_local_critical_seconds']=time.monotonic()-t
            report['entry_remaining_of5_seconds_before_network']=5-report['entry_local_critical_seconds']
            report['entry_scope']='Known8 durable bodies, actual adapter, selection publication,8456selectedcalendar/spec/recover and selected8 durable bodies. Includes raw5MiB10000-row invented metadata; no HTTP latency, actual transport subprocess creation or VPS storage measurement. Positive remaining time is not a network-latency guarantee.'
        checkpoint('entry')
        # Near-complete known+selected fixture at full8192 bytes per slot with
        # real production1prefix each. Direct setup writes are not fsynced.
        t=time.monotonic();body=b'x'*8192
        for name in ('known','selected'):
            p=root/name;p.mkdir();write(p/'lock',b'')
            args=journal_args(claim,calendars[name],name)
            j=Journal(p,**args);write(p/'spec.json',encode(j.spec))
            for slot in calendars[name][:-8]:
                intent,receipt=encoded_members(slot,body)
                write(p/('intent-'+slot['id']+'.json'),intent)
                write(p/('partial-'+slot['id']+'-000000.bin'),body)
                write(p/('receipt-'+slot['id']+'.json'),receipt)
        report['near_complete_setup_seconds']=time.monotonic()-t;checkpoint('near_complete_setup')
        t=time.monotonic();measurements={}
        with contextlib.ExitStack() as together:
            active={}
            for name in ('known','selected'):
                start=time.monotonic();active[name]=together.enter_context(Journal(root/name,**journal_args(claim,calendars[name],name)))
                measurements[name]={'open_validate_seconds':time.monotonic()-start}
            report['near_complete_scope']='Both full8456-slot journals held simultaneously; all initial journal caches also remain referenced. No full-size daily journal fixture.'
            for name,j in active.items():
                tail=calendars[name][-8:];tick=time.monotonic()
                j.begin_group([s['id'] for s in tail],now_ms=tail[0]['scheduled_ms'])
                for s in tail:j.partial(s['id'],body);j.record(s['id'],body,metadata=metadata(s,body))
                append=time.monotonic()-tick;tick=time.monotonic();j.seal('complete');seal=time.monotonic()-tick
                st=[p.stat() for p in j.path.iterdir()]
                measurements[name].update(final8_fsynced_partial_receipt_seconds=append,complete_seal_seconds=seal,
                    logical_bytes=sum(v.st_size for v in st),allocated_file_blocks_bytes=sum(v.st_blocks*512 for v in st),members=len(st))
        report['near_complete_measurements']=measurements;report['near_complete_lifecycle_seconds']=time.monotonic()-t
        filesystem=os.statvfs(root)
        report['filesystem']={'fragment_size':filesystem.f_frsize,'block_size':filesystem.f_bsize,'available_inodes':filesystem.f_favail,
                              'scope':'Measured local test filesystem; not VPS admission.'}
        report['resource_usage']={'elapsed_seconds_before_cleanup':time.monotonic()-begin,'ru_maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    report['total_elapsed_seconds']=time.monotonic()-begin
    report['conclusions']={'serialized_calendar_fits_proposed_caps':all(r['all_received_plus_one_staging_fits_nonterminal'] for r in report['arithmetic']['journals'].values()),
        'local_initialization_under5seconds_without_network':report['entry_local_critical_seconds']<5,
        'fullsize_metadata_hourly_network_VPS_and_all_lifecycle_success_proved':False}
    checkpoint('complete');progress.close()
    with Path(report_path).open('x') as out:json.dump(report,out,indent=2);out.write('\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--report',required=True);args=parser.parse_args();main(args.report)

"""Offline invented journal files only."""
import hashlib
import json
from pathlib import Path
import pytest
from tradingagents.research_options_capture.journal import Journal,JournalError


def setup(tmp_path,**changes):
    claim=tmp_path/'claim.json';claim.write_bytes(b'invented active claim')
    args=dict(claim_path=claim,claim_sha256=hashlib.sha256(claim.read_bytes()).hexdigest(),
              slots=[{'id':s,'scheduled_ms':t,'deadline_ms':t+5,'request':{'url':'https://invalid.example/'+s},'body_cap':32} for s,t in [('a',10),('b',20),('c',30)]],
              total_cap=50000,terminal_reserve=2048,check_source=lambda:None)
    args.update(changes)
    return tmp_path/'journal',args


def test_intent_receipt_seal_and_readonly_manifest(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        with pytest.raises(JournalError):j.record('a',b'x',metadata={})
        intent=j.begin('a',now_ms=12);assert len(intent['intent_sha256'])==64
        j.record('a',b'raw',metadata={'status':200})
        j.recover(now_ms=36)
        assert [c['status'] for c in j.validate()['slots']]==['received','missed','missed']
        j.seal('complete')
        with pytest.raises(JournalError):j.begin('b',now_ms=20)
    with pytest.raises(JournalError):
        with Journal(path,**args):pass
    with Journal(path,**args,readonly=True) as j:assert len(j.validate()['slots'])==3
    assert not (tmp_path/'complete.json').exists()


def test_crash_before_after_intent_no_retry_and_partials(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        j.begin('a',now_ms=10);j.partial('a',b'part')
    with Journal(path,**args) as j:
        out=j.recover(now_ms=23)
        assert [c['status'] for c in out['slots']]==['unavailable','future_or_unattempted','future_or_unattempted']
        assert (path/'partial-a-000000.bin').read_bytes()==b'part'
        with pytest.raises(JournalError):j.begin('a',now_ms=10)
        j.begin('b',now_ms=23);j.record('b',b'ok',metadata={})


def test_crash_during_atomic_publication_retains_pending(tmp_path,monkeypatch):
    import os
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        original=os.link
        monkeypatch.setattr(os,'link',lambda *a,**k:(_ for _ in ()).throw(OSError('invented crash')))
        with pytest.raises(OSError):j.begin('a',now_ms=10)
        monkeypatch.setattr(os,'link',original)
    with Journal(path,**args) as j:
        j.recover(now_ms=16)
        assert j.validate()['slots'][0]['status']=='missed'
        assert any(k.startswith('pending-') for k in j.validate()['members'])


def test_duplicate_concurrent_and_changed_claim(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        with pytest.raises(BlockingIOError):
            with Journal(path,**args):pass
        j.begin('a',now_ms=10)
        with pytest.raises(JournalError):j.begin('a',now_ms=10)
        j.record('a',b'ok',metadata={})
        with pytest.raises(JournalError):j.record('a',b'new',metadata={})
        args['claim_path'].write_bytes(b'changed')
        with pytest.raises(JournalError):j.begin('b',now_ms=20)


def test_caps_and_future_terminal(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        j.begin('a',now_ms=10)
        with pytest.raises(JournalError):j.partial('a',b'x'*33)
        j.partial('a',b'x'*20)
        with pytest.raises(JournalError):j.partial('a',b'x'*13)
        with pytest.raises(JournalError):j.record('a',b'x'*33,metadata={})
        with pytest.raises(JournalError):j.record('a',b'',metadata={'huge':'x'*50000})
        with pytest.raises(JournalError):j.seal('complete')
        seal=j.seal('failed');assert seal['suppressed_count']==2
        assert [c['status'] for c in j.validate()['slots']][1:]==['suppressed','suppressed']


def test_outer_terminal_and_symlink_refusal(tmp_path):
    path,args=setup(tmp_path)
    (tmp_path/'failed.json').write_text('{}')
    with pytest.raises(JournalError):
        with Journal(path,**args):pass
    (tmp_path/'failed.json').unlink()
    with Journal(path,**args) as j:
        (path/'receipt-a.json').symlink_to(args['claim_path'])
        with pytest.raises(JournalError):j.validate()


def test_corrupt_record_source_boundary_and_spec(tmp_path):
    path,args=setup(tmp_path);checks=[];args['check_source']=lambda:checks.append(1)
    with Journal(path,**args) as j:
        j.begin('a',now_ms=10);j.record('a',b'ok',metadata={})
        value=json.loads((path/'receipt-a.json').read_bytes());value['body_sha256']='0'*64
        (path/'receipt-a.json').write_text(json.dumps(value))
        with pytest.raises(JournalError):j.validate()
    assert len(checks)>3


def test_crash_after_publication_never_retries(tmp_path,monkeypatch):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        j.begin('a',now_ms=10)
        original=Path.unlink
        def crash(p,*a,**kw):
            if p.name.startswith('pending-'):raise OSError('after atomic link')
            return original(p,*a,**kw)
        monkeypatch.setattr(Path,'unlink',crash)
        with pytest.raises(OSError):j.record('a',b'raw',metadata={})
        monkeypatch.setattr(Path,'unlink',original)
    with Journal(path,**args) as j:
        assert j.recover(now_ms=16)['slots'][0]['status']=='received'
        with pytest.raises(JournalError):j.begin('a',now_ms=10)
        assert any(k.startswith('pending-') for k in j.validate()['members'])


def test_deadlines_lock_replacement_and_parent_symlink(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        for t in (9,16):
            with pytest.raises(JournalError):j.begin('a',now_ms=t)
        j.recover(now_ms=15)
        assert j.validate()['slots'][0]['status']=='future_or_unattempted'
        (path/'lock').unlink();(path/'lock').write_bytes(b'')
        with pytest.raises(JournalError):j.begin('a',now_ms=15)
    target=tmp_path/'real';target.mkdir();(tmp_path/'alias').symlink_to(target,target_is_directory=True)
    with pytest.raises(JournalError):Journal(tmp_path/'alias'/'journal',**args)


def test_spec_mutation_and_source_failure(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        (path/'spec.json').write_bytes(b'{}')
        with pytest.raises(JournalError):j.validate()
    path2=tmp_path/'j2';args['check_source']=lambda:(_ for _ in ()).throw(JournalError('source changed'))
    with pytest.raises(JournalError):
        with Journal(path2,**args):pass


def test_parallel_group_all_intents_before_independent_receipts(tmp_path):
    path,args=setup(tmp_path)
    args['slots']=[{'id':f'a-{i}','scheduled_ms':10,'deadline_ms':15,'request':{'id':i},'body_cap':32} for i in range(16)]+[{'id':'later','scheduled_ms':20,'deadline_ms':25,'request':{},'body_cap':32}]
    with Journal(path,**args) as j:
        tokens=j.begin_group([f'a-{i}' for i in range(16)],now_ms=10)
        assert len(tokens)==16
        assert sum(c['status']=='intent_without_receipt' for c in j.validate()['slots'])==16
        with pytest.raises(JournalError):j.begin('later',now_ms=20)
        for i in reversed(range(16)):j.record(f'a-{i}',b'ok',metadata={})
        j.begin('later',now_ms=20)


def test_group_partial_crash_and_bound(tmp_path,monkeypatch):
    path,args=setup(tmp_path)
    args['slots'][1].update(scheduled_ms=10,deadline_ms=15)
    with Journal(path,**args) as j:
        original=j._publish
        def fail(name,*a,**kw):
            if name=='intent-b.json':raise JournalError('synthetic disk stop')
            return original(name,*a,**kw)
        monkeypatch.setattr(j,'_publish',fail)
        with pytest.raises(JournalError):j.begin_group(['a','b'],now_ms=10)
        monkeypatch.setattr(j,'_publish',original)
        recovered=j.recover(now_ms=16)
        assert [c['status'] for c in recovered['slots']][:2]==['unavailable','missed']
    args['slots']=[dict(args['slots'][0],id=f's-{i}') for i in range(17)]
    with pytest.raises(JournalError):Journal(tmp_path/'too-many',**args)


def test_partial_prefix_and_intent_recovery_clock_validation(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        j.begin('a',now_ms=12);j.partial('a',b'abc')
        with pytest.raises(JournalError):j.record('a',b'xyz',metadata={})
        with pytest.raises(JournalError):j.recover(now_ms=11)
        j.record('a',b'abcdef',metadata={})
        value=json.loads((path/'intent-a.json').read_bytes());value['now_ms']=100
        (path/'intent-a.json').write_text(json.dumps(value))
        with pytest.raises(JournalError):j.validate()


def test_missed_clock_cannot_be_rewritten_into_active_window(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        j.recover(now_ms=16)
        value=json.loads((path/'receipt-a.json').read_bytes());value['metadata']['recovered_at_ms']=15
        (path/'receipt-a.json').write_text(json.dumps(value))
        with pytest.raises(JournalError):j.validate()


def test_failed_seal_relabel_and_recovery_log_semantics(tmp_path):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        j.seal('failed')
        value=json.loads((path/'seal.json').read_bytes());value['status']='complete'
        (path/'seal.json').write_text(json.dumps(value))
        with pytest.raises(JournalError):j.validate()
    path2=tmp_path/'other'
    with Journal(path2,**args) as j:
        j.recover(now_ms=16)
        (path2/'recovery-000000.json').write_text('{}')
        with pytest.raises(JournalError):j.validate()


def test_cached_appends_do_not_rescan_and_boundary_detects_change(tmp_path,monkeypatch):
    path,args=setup(tmp_path)
    with Journal(path,**args) as j:
        original=j._inventory
        monkeypatch.setattr(j,'_inventory',lambda:(_ for _ in ()).throw(AssertionError('append full scan')))
        j.begin('a',now_ms=10);j.partial('a',b'a');j.record('a',b'ab',metadata={})
        monkeypatch.setattr(j,'_inventory',original)
        (path/'receipt-a.json').write_text('{}')
        with pytest.raises(JournalError):j.validate()


def test_pending_member_pressure_preserves_failed_seal_capacity(tmp_path,monkeypatch):
    path,args=setup(tmp_path);args['slots']=args['slots'][:1];args['slots'][0]['body_cap']=1024
    with Journal(path,**args) as j:
        j.begin('a',now_ms=10)
        original=Path.unlink
        def crash(p,*a,**kw):
            if p.name.startswith('pending-'):raise OSError('postlink crash')
            return original(p,*a,**kw)
        monkeypatch.setattr(Path,'unlink',crash)
        for _ in range(100):
            try:j.partial('a',b'x')
            except OSError:pass
            except JournalError:break
        else:pytest.fail('count pressure did not stop')
        monkeypatch.setattr(Path,'unlink',original)
        j.seal('failed')
        assert j.validate()['members']['seal.json']['bytes']>0


def full_size_fixture(directory):
    """17,000 invented slots, each full8KiB body; no transport or history admission."""
    import time
    directory.mkdir();claim=directory/'claim.json';claim.write_bytes(b'full-size invented active claim')
    slots=[{'id':f's-{i:05d}','scheduled_ms':(i//16)*3600000,'deadline_ms':(i//16)*3600000+5000,
            'request':{'url':'https://invalid.example/source','slot':i},'body_cap':8192} for i in range(17000)]
    args=dict(claim_path=claim,claim_sha256=hashlib.sha256(claim.read_bytes()).hexdigest(),slots=slots,
              total_cap=512*1024**2,terminal_reserve=4096,check_source=lambda:None)
    begun=__import__('time').monotonic();max_batch=0
    with Journal(directory/'journal',**args) as j:
        for offset in range(0,len(slots),16):
            group=slots[offset:offset+16];started=time.monotonic()
            j.begin_group([s['id'] for s in group],now_ms=group[0]['scheduled_ms'])
            for s in reversed(group):j.record(s['id'],b'x'*8192,metadata={'status':200,'invented':True})
            max_batch=max(max_batch,time.monotonic()-started)
        validation_started=time.monotonic();manifest=j.validate();validation=time.monotonic()-validation_started
        j.seal('complete')
    with Journal(directory/'journal',**args,readonly=True) as j:
        sealed=j.validate()
    assert len(manifest['slots'])==17000 and all(c['status']=='received' for c in sealed['slots'])
    return {'slot_count':17000,'receipt_count':17000,'raw_bytes':17000*8192,'journal_bytes':sealed['bytes'],
            'member_count':len(sealed['members']),'max_synthetic_batch_seconds':max_batch,
            'explicit_validation_seconds':validation,'elapsed_seconds':time.monotonic()-begun,
            'scope':'Cooperative offline filesystem journal only; no transport or actual historical admission cost.'}


def near_complete_setup(directory):
    import time
    from tradingagents.research_options_capture.journal import encode,digest
    begun=time.monotonic();directory.mkdir();claim=directory/'claim.json';claim.write_bytes(b'near-complete invented claim')
    journal=directory/'journal';journal.mkdir();(journal/'lock').write_bytes(b'')
    slots=[{'id':f's-{i:05d}','scheduled_ms':(i//16)*3600000,'deadline_ms':(i//16)*3600000+5000,
            'request':{'url':'https://invalid.example/source','slot':i},'body_cap':8192} for i in range(17000)]
    spec={'claim_sha256':digest(claim.read_bytes()),'slots':slots,'total_cap':512*1024**2,'terminal_reserve':4096}
    (journal/'spec.json').write_bytes(encode(spec))
    import base64
    body=b'x'*8192
    for slot in slots[:-24]:
        common={'claim_sha256':spec['claim_sha256'],'slot':slot['id'],'request':slot['request']}
        (journal/('intent-'+slot['id']+'.json')).write_bytes(encode(dict(common,kind='intent',now_ms=slot['scheduled_ms'])))
        (journal/('receipt-'+slot['id']+'.json')).write_bytes(encode(dict(common,kind='receipt',status='received',body_base64=base64.b64encode(body).decode(),body_sha256=digest(body),body_bytes=len(body),metadata={'status':200,'invented':True})))
    return {'setup_seconds':time.monotonic()-begun,'prepopulated_slots':16976,'declared_slots':17000,
            'setup_method':'Direct invented fixture writes, not production durable lifecycle; timed child fully validates before appending.'}


def near_complete_invocation(directory):
    import time
    spec=json.loads((directory/'journal/spec.json').read_bytes())
    args=dict(claim_path=directory/'claim.json',claim_sha256=spec['claim_sha256'],slots=spec['slots'],
              total_cap=spec['total_cap'],terminal_reserve=spec['terminal_reserve'],check_source=lambda:None)
    begun=time.monotonic()
    with Journal(directory/'journal',**args) as j:
        entry_seconds=time.monotonic()-begun;batch_times=[]
        for group in (spec['slots'][-24:-8],spec['slots'][-8:]):
            started=time.monotonic();j.begin_group([s['id'] for s in group],now_ms=group[0]['scheduled_ms'])
            for slot in reversed(group):j.record(slot['id'],b'x'*8192,metadata={'status':200,'invented':True})
            batch_times.append(time.monotonic()-started)
        started=time.monotonic();j.validate();validation_seconds=time.monotonic()-started
        started=time.monotonic();j.seal('complete');seal_seconds=time.monotonic()-started
    started=time.monotonic()
    with Journal(directory/'journal',**args,readonly=True) as j:manifest=j.validate()
    readonly_seconds=time.monotonic()-started
    assert len(manifest['slots'])==17000 and all(c['status']=='received' for c in manifest['slots'])
    return {'entry_seconds':entry_seconds,'late_16_batch_seconds':batch_times[0],'tail_8_batch_seconds':batch_times[1],
            'full_validation_seconds':validation_seconds,'seal_seconds':seal_seconds,'readonly_seconds':readonly_seconds,
            'elapsed_seconds':time.monotonic()-begun,'journal_bytes':manifest['bytes'],'members':len(manifest['members']),
            'slots':17000,'raw_bytes':17000*8192,'scope':'Near-complete cooperative journal invocation; no transport or actual historical admission cost; setup direct writes separately bounded.'}


def test_full_size_guarded_journal(tmp_path):
    import importlib.util
    import sys
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('journal_guard',root/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    for stage,function,limit in [('setup','near_complete_setup',300),('invocation','near_complete_invocation',120)]:
        driver=tmp_path/(stage+'-driver.py')
        driver.write_text('import importlib.util,json,sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(root))+')\ns=importlib.util.spec_from_file_location("fixture",'+repr(str(Path(__file__).resolve()))+')\nm=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nr=m.'+function+'(Path('+repr(str(tmp_path/'fixture'))+'))\nPath('+repr(str(tmp_path/(stage+'-result.json')))+').write_text(json.dumps(r,indent=2))\n')
        report=guard.run_guard([sys.executable,'-B',str(driver)],wall_seconds=limit)
        (tmp_path/(stage+'-guard.json')).write_text(json.dumps(report,indent=2))
        assert report['child_exit_code']==0 and report['limit_reason'] is None,report
    result=json.loads((tmp_path/'invocation-result.json').read_bytes())
    assert result['late_16_batch_seconds']<5

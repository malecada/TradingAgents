"""Invented subprocess frames and in-memory HTTP only; no network."""
import base64
import hashlib
import http.client
import io
import json
import os
import sys
import time
from types import SimpleNamespace

import pytest
from tradingagents.research_options_capture.journal import Journal, JournalError
from tradingagents.research_options_capture import transport as t


FAKE = r'''
import base64, ctypes, hashlib, json, os, signal, sys, time
s=json.load(sys.stdin);mode=sys.argv[1]
if os.getppid()!=s['parent_pid']:sys.exit(2)
if ctypes.CDLL(None).prctl(1,signal.SIGKILL,0,0,0)!=0:sys.exit(2)
if os.getppid()!=s['parent_pid']:sys.exit(2)
def emit(**kw):print(json.dumps(kw),flush=True)
if mode=='hang':time.sleep(10)
emit(kind='start',request_ms=time.time_ns()//1000000,request_monotonic_ns=time.monotonic_ns())
if mode=='duplicate':emit(kind='start',request_ms=0,request_monotonic_ns=0)
status=int(mode) if mode.isdigit() else 200
emit(kind='headers',http_status=status)
body=b'x'*s['body_cap']
if mode=='overflow':body+=b'x'
step=max(8192,(s['body_cap']+62)//63)
if mode=='overflow':step=len(body)
for offset in range(0,len(body),step):emit(kind='chunk',base64=base64.b64encode(body[offset:offset+step]).decode())
if mode=='partial':sys.exit(0)
end=time.time_ns()//1000000+(500 if mode=='clockjump' else 0)
emit(kind='done',http_status=status,body_complete=True,error=None,
 retrieval_ms=end,retrieval_monotonic_ns=time.monotonic_ns(),
 body_bytes=len(body),body_sha256='0'*64 if mode=='wronghash' else hashlib.sha256(body).hexdigest())
if mode=='afterdone':emit(kind='headers',http_status=200)
if mode=='trailing':sys.stdout.write('garbage');sys.stdout.flush()
'''


def setup(tmp_path, count=1, duration=5000, cap=8192):
    claim=tmp_path/'claim.json';claim.write_bytes(b'invented claim')
    now=time.time_ns()//1000000;deadline=now+duration
    slots=[dict(id=f's{i}',scheduled_ms=now,deadline_ms=deadline,
                request={'endpoint':'https://eapi.binance.com/eapi/v1/time','parameters':{}},body_cap=cap)
           for i in range(count)]
    args=dict(claim_path=claim,claim_sha256=hashlib.sha256(claim.read_bytes()).hexdigest(),
              slots=slots,total_cap=64*1024**2,terminal_reserve=8192,check_source=lambda:None)
    return tmp_path/'journal',args,now,deadline


def collect(j, deadline, mode):
    return t._collect(j,list(j.slots),deadline_ms=deadline,
                      spawn_command=[sys.executable,'-B','-c',FAKE,mode])


def test_full_sixteen_durable_prefixes_and_no_retry(tmp_path):
    path,args,now,deadline=setup(tmp_path,count=16)
    with Journal(path,**args) as j:
        j.begin_group(list(j.slots),now_ms=now)
        result=collect(j,deadline,'ok')
        assert not result['halt_on_access_restriction']
        assert all(m['body_complete'] and m['clock_consistent'] and m['within_controller_deadline'] for m in result['sources'].values())
        assert len(list(path.glob('partial-*.bin')))==16
        before=j.validate()
        with pytest.raises(ValueError,match='no retry'):collect(j,deadline,'ok')
        assert j.validate()==before
        j.seal('complete')


@pytest.mark.parametrize('mode',['403','418','429','451'])
def test_restriction_retained_and_signalled(tmp_path,mode):
    path,args,now,deadline=setup(tmp_path)
    with Journal(path,**args) as j:
        j.begin('s0',now_ms=now)
        assert collect(j,deadline,mode)['halt_on_access_restriction']
        assert json.loads((path/'receipt-s0.json').read_bytes())['metadata']['http_status']==int(mode)


@pytest.mark.parametrize('mode',['partial','hang'])
def test_incomplete_or_deadline_no_reissue(tmp_path,mode):
    path,args,now,deadline=setup(tmp_path,duration=300)
    started=time.monotonic()
    with Journal(path,**args) as j:
        j.begin('s0',now_ms=now)
        result=collect(j,deadline,mode)['sources']['s0']
        assert not result['body_complete']
        assert result['body_bytes']==(8192 if mode=='partial' else 0)
        assert time.monotonic()-started<3
        assert j.recover(now_ms=deadline+1)['slots'][0]['status']=='received'
        with pytest.raises(ValueError):collect(j,deadline,mode)


@pytest.mark.parametrize('mode',['duplicate','overflow','wronghash','afterdone','trailing'])
def test_protocol_failure_retains_prefix_and_unknown_state(tmp_path,mode):
    path,args,now,deadline=setup(tmp_path)
    with Journal(path,**args) as j:
        j.begin('s0',now_ms=now)
        with pytest.raises(ValueError):collect(j,deadline,mode)
        receipt=json.loads((path/'receipt-s0.json').read_bytes())
        assert not receipt['metadata']['body_complete']
        assert receipt['body_bytes']==(0 if mode in ('duplicate','overflow') else 8192)
        j.validate()


def test_group_preconditions_have_no_side_effects(tmp_path):
    path,args,now,deadline=setup(tmp_path,count=2)
    with Journal(path,**args) as j:
        j.begin('s0',now_ms=now);before=j.validate()
        with pytest.raises(ValueError):collect(j,deadline,'ok')
        assert j.validate()==before


def test_wall_jump_in_worker_invalidates_clock(tmp_path):
    path,args,now,deadline=setup(tmp_path)
    with Journal(path,**args) as j:
        j.begin('s0',now_ms=now)
        result=collect(j,deadline,'clockjump')['sources']['s0']
        # Worker retrieval must also be internally consistent, independently of
        # the controller's normal clock (regression for ignored worker clocks).
        assert not result['clock_consistent']


@pytest.mark.parametrize('endpoint,params',[
    ('http://eapi.binance.com/eapi/v1/time',{}),
    ('https://eapi.binance.com/eapi/v1/order',{}),
    ('https://evil.example/eapi/v1/time',{}),
    ('https://eapi.binance.com/eapi/v1/time?x=1',{}),
    ('https://u:p@eapi.binance.com/eapi/v1/time',{}),
    ('https://fapi.binance.com/fapi/v1/fundingRate',{'symbol':'BTCUSDT','startTime':10,'endTime':9,'limit':1000}),
    ('https://fapi.binance.com/fapi/v1/depth',{'symbol':'BTCUSDT','limit':20}),
])
def test_only_exact_public_requests(endpoint,params):
    with pytest.raises(ValueError):t.request_url({'endpoint':endpoint,'parameters':params})


@pytest.mark.parametrize('raw,complete,body',[
    (b'HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\nabc',True,b'abc'),
    (b'HTTP/1.1 200 OK\r\nContent-Length: 8\r\n\r\nabc',False,b'abc'),
    (b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n0\r\n\r\n',True,b'abc'),
    (b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n8\r\nabc',False,b'abc'),
])
def test_worker_http_completeness_without_network(monkeypatch,raw,complete,body):
    response=http.client.HTTPResponse(SimpleNamespace(makefile=lambda *a,**k:io.BytesIO(raw)));response.begin()
    conn=SimpleNamespace(sock=None,request=lambda *a,**k:None,getresponse=lambda:response,close=lambda:None)
    monkeypatch.setattr(t.http.client,'HTTPSConnection',lambda *a,**k:conn)
    monkeypatch.setattr(t.ctypes,'CDLL',lambda *a,**k:SimpleNamespace(prctl=lambda *a:0))
    frames=[];monkeypatch.setattr(t,'_emit',frames.append)
    t.worker({'parent_pid':os.getppid(),'request':{'endpoint':'https://eapi.binance.com/eapi/v1/time','parameters':{}},
              'body_cap':8192,'deadline_monotonic_ns':time.monotonic_ns()+1000000000})
    assert frames[-1]['body_complete'] is complete
    assert b''.join(base64.b64decode(f['base64']) for f in frames if f['kind']=='chunk')==body


def test_full_metadata_worker_frame_bound(monkeypatch):
    body=b'x'*(5*1024**2);stream=io.BytesIO(body)
    response=SimpleNamespace(status=200,length=None,read1=stream.read)
    conn=SimpleNamespace(sock=None,request=lambda *a,**k:None,getresponse=lambda:response,close=lambda:None)
    monkeypatch.setattr(t.http.client,'HTTPSConnection',lambda *a,**k:conn)
    monkeypatch.setattr(t.ctypes,'CDLL',lambda *a,**k:SimpleNamespace(prctl=lambda *a:0))
    frames=[];monkeypatch.setattr(t,'_emit',frames.append)
    t.worker({'parent_pid':os.getppid(),'request':{'endpoint':'https://eapi.binance.com/eapi/v1/exchangeInfo','parameters':{}},
              'body_cap':len(body),'deadline_monotonic_ns':time.monotonic_ns()+1000000000})
    assert len([f for f in frames if f['kind']=='chunk'])<=64
    assert all(len(json.dumps(f))<t.MAX_FRAME for f in frames)
    assert frames[-1]['body_complete']


def test_close_failure_retains_tail(monkeypatch):
    stream=io.BytesIO(b'abc')
    response=SimpleNamespace(status=200,length=None,read1=stream.read)
    def close():raise OSError('invented close failure')
    conn=SimpleNamespace(sock=None,request=lambda *a,**k:None,getresponse=lambda:response,close=close)
    monkeypatch.setattr(t.http.client,'HTTPSConnection',lambda *a,**k:conn)
    monkeypatch.setattr(t.ctypes,'CDLL',lambda *a,**k:SimpleNamespace(prctl=lambda *a:0))
    frames=[];monkeypatch.setattr(t,'_emit',frames.append)
    t.worker({'parent_pid':os.getppid(),'request':{'endpoint':'https://eapi.binance.com/eapi/v1/time','parameters':{}},
              'body_cap':8192,'deadline_monotonic_ns':time.monotonic_ns()+1000000000})
    assert not frames[-1]['body_complete']
    assert frames[-1]['body_bytes']==3
    assert base64.b64decode(frames[-2]['base64'])==b'abc'


@pytest.mark.parametrize('state',['sealed','outerterminal','unlocked'])
def test_no_network_without_active_journal(tmp_path,monkeypatch,state):
    path,args,now,deadline=setup(tmp_path)
    calls=[]
    monkeypatch.setattr(t.subprocess,'Popen',lambda *a,**k:calls.append(1))
    with Journal(path,**args) as j:
        j.begin('s0',now_ms=now)
        if state=='sealed':j.seal('failed')
        if state=='outerterminal':(tmp_path/'failed.json').write_text('{}')
        if state!='unlocked':
            before={p.name:p.read_bytes() for p in path.iterdir()}
            with pytest.raises(JournalError):collect(j,deadline,'ok')
            assert before=={p.name:p.read_bytes() for p in path.iterdir()}
    if state=='unlocked':
        with pytest.raises(JournalError):collect(j,deadline,'ok')
    assert not calls

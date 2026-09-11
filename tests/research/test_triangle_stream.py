"""Invented frames only; no network or historical quotes."""
import base64
import importlib.util
import json
from pathlib import Path
import sys
import pytest

DIRECTORY=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
sys.path.insert(0,str(DIRECTORY))
import triangle_stream as stream


def message(symbol,update=1,price=None,quantity='1000000',padding=0):
    prices={'BTCUSDT':'100','ETHUSDT':'10','ETHBTC':'0.1'}
    return json.dumps({'stream':symbol.lower()+'@bookTicker','data':{'s':symbol,'u':update,'b':price or prices[symbol],'a':price or prices[symbol],'B':quantity,'A':quantity},'padding':'x'*padding}).encode()


def fixture_metadata():
    spec=json.loads((DIRECTORY/'triangle-request-spec.json').read_text())
    request=next(r for r in spec['requests'] if r['kind']=='exchange-info')
    raw=json.dumps({'symbols':[{'symbol':symbol,'baseAsset':pair[0],'quoteAsset':pair[1],'status':'TRADING','isSpotTradingAllowed':True,'filters':[]} for symbol,pair in stream.triangle_capture.PAIRS.items()]}).encode()
    record={**request,'body_base64':base64.b64encode(raw).decode(),'body_bytes':len(raw),'body_sha256':stream.sha(raw),'attempted':True,'body_complete':True,'http_status':200,'error':None}
    return {'request_spec':spec,'requests':[record]},{'cells':[{'id':request['id'],**stream.triangle_capture.parse_response(raw,request)}]}


def replay(events,end=540_000_000_000,reason='deadline'):
    store={};spec=stream.default_spec()
    writer=stream.RawChunks(spec,lambda name,value:store.__setitem__(name,stream.lifecycle_bytes(value)))
    for stamp,payload,fields in events:writer.append('inbound-frame',payload,stamp,**{'opcode':1,'fin':True,**fields})
    writer.finish()
    return stream.replay(spec,writer.replay_records(store.__getitem__),{'end_elapsed_ns':end,'end_reason':reason},{'status':'complete'})


def quotes(stamp=0,update=1,**kw):return [(stamp,message(s,update,**kw),{}) for s in stream.triangle_bound.SYMBOLS]


def test_right_boundary_age_and_duplicate_no_refresh():
    bins,summary=replay(quotes()+quotes(900_000_000))
    rows=next(iter(bins['series'].values()))
    assert all(r[0] for r in rows[:10]) and rows[10][0]==0
    assert summary['diagnostics']['duplicates']==3
    assert len(rows)==5400 and sum(len(v) for v in bins['series'].values())==43200


def test_conflict_regression_and_strict_recovery():
    events=quotes()+[(100_000_000,message('BTCUSDT',1,price='101'),{}),(200_000_000,message('BTCUSDT',0),{}),(300_000_000,message('BTCUSDT',2),{})]
    bins,summary=replay(events)
    rows=next(iter(bins['series'].values()))
    assert rows[0][0]==rows[1][0]==0 and rows[2][0]!=0
    assert summary['diagnostics']['conflicting_duplicates']==summary['diagnostics']['regressions']==1


def test_fragment_completion_and_global_malformed_recovery():
    btc=message('BTCUSDT')
    events=quotes() [1:]+[(10_000_000,btc[:20],{'fin':False}),(150_000_000,btc[20:],{'opcode':0}),(250_000_000,b'not json',{})]+quotes(350_000_000,2)
    bins,_=replay(events);rows=next(iter(bins['series'].values()))
    assert [bool(r[0]) for r in rows[:4]]==[False,True,False,True]


def test_zero_quantity_preserves_factor_and_fees():
    bins,_=replay(quotes(quantity='0'))
    for rows in bins['series'].values():
        row=dict(zip(bins['columns'],rows[0]))
        assert row['status']==1 and row['gross_factor']==pytest.approx(1)
        assert not any(row[f'size_sufficient_leg{i}'] for i in (1,2,3))
        assert row['simple_cash_proxy_usdt']<=0


def test_complete_outputs_early_failure_and_metadata_mismatch(tmp_path):
    capture,admission=fixture_metadata()
    def persist(name,value):(tmp_path/name).write_bytes(stream.lifecycle_bytes(value))
    def failed(spec,writer):return {'status':'unavailable','end_reason':'refused','end_elapsed_ns':0}
    _,bins,summary,cells=stream.run(stream.default_spec(),capture,admission,persist,lambda n:(tmp_path/n).read_bytes(),failed)
    assert len(cells)==9 and len(list(tmp_path.iterdir()))==35
    assert all(r==[0,1] for rows in bins['series'].values() for r in rows)
    assert summary['graduation'] is False
    admission['cells'][0]['extra']='mismatch'
    with pytest.raises(ValueError):stream.metadata(capture,admission)


def test_chunk_hash_and_caps():
    store={};spec=stream.default_spec();spec['raw_max_bytes']=3
    writer=stream.RawChunks(spec,lambda n,v:store.__setitem__(n,stream.lifecycle_bytes(v)))
    writer.append('inbound-frame',b'123',0,opcode=1,fin=True)
    with pytest.raises(stream.CaptureLimit):writer.append('inbound-frame',b'4',1,opcode=1,fin=True)
    assert writer.dropped['body_sha256']==stream.sha(b'4')
    writer.finish();assert not hasattr(writer,'records')
    store['raw-00.json']+=b' '
    with pytest.raises(ValueError):list(writer.replay_records(store.__getitem__))

@pytest.mark.parametrize('refuse',[False,True,'oversize','bad-header'])
def test_real_protocol_fake_socket_controls_refusal_and_no_retries(monkeypatch,refuse):
    # Real Sans-I/O protocol; only DNS/socket/TLS system interfaces are invented.
    stream._protocol(stream.default_spec())
    from websockets.frames import Frame,Opcode
    from websockets.utils import accept_key
    sockets=[]
    class FakeSocket:
        def __init__(self,*args):self.sent=[];self.received=0;sockets.append(self)
        def settimeout(self,*args):pass
        def connect(self,address):self.address=address
        def sendall(self,data):self.sent.append(data)
        def shutdown(self,*args):pass
        def close(self):pass
        def recv(self,*args):
            self.received+=1
            if self.received==1:
                if refuse=='bad-header':return b'HTTP/1.1 101 Switching Protocols\r\nX-Unknown: '+b'x'*3000
                if refuse is True:return b'HTTP/1.1 403 Forbidden\r\nContent-Length: 6\r\nContent-Type: text/plain\r\n\r\ndenied'
                key=next(line.split(b': ',1)[1].decode() for line in self.sent[0].split(b'\r\n') if line.lower().startswith(b'sec-websocket-key:'))
                return ('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept_key(key)+'\r\n\r\n').encode()
            if self.received==2 and refuse=='oversize':return Frame(Opcode.TEXT,b'x'*65537).serialize(mask=False)
            if self.received==2:return Frame(Opcode.PING,b'synthetic').serialize(mask=False)
            if self.received==3:return Frame(Opcode.TEXT,message('BTCUSDT')).serialize(mask=False)
            return b''
    monkeypatch.setattr(stream.socket,'getaddrinfo',lambda *a,**k:[(2,1,6,'',('192.0.2.1',9443)),(2,1,6,'',('192.0.2.2',9443))])
    monkeypatch.setattr(stream.socket,'socket',FakeSocket)
    class Context:
        def wrap_socket(self,sock,**kw):return sock
    monkeypatch.setattr(stream.ssl,'create_default_context',Context)
    monkeypatch.setattr(stream.signal,'setitimer',lambda *a:None)
    monkeypatch.setattr(stream,'_message',lambda *a:pytest.fail('Financial parsing during acquisition'))
    store={};writer=stream.RawChunks(stream.default_spec(),lambda n,v:store.__setitem__(n,stream.lifecycle_bytes(v)))
    report=stream.acquire(stream.default_spec(),writer);writer.finish()
    records=list(writer.replay_records(store.__getitem__))
    assert len(sockets)==1 and sockets[0].address==('192.0.2.1',9443)
    if refuse=='bad-header':
        assert any(r['kind']=='incomplete-handshake-prefix-digest' for r in records);return
    assert report['http_status']==(403 if refuse is True else 101)
    if refuse=='oversize':
        assert report['end_reason']=='frame_protocol_error';return
    if refuse is True:assert any(base64.b64decode(r['body_base64'])==b'denied' for r in records)
    else:assert any(r['kind']=='outbound-control-wire' for r in records) and any(r.get('opcode')==9 for r in records)


def test_full_bin_invented_payload_file_replay(tmp_path):
    capture,admission=fixture_metadata()
    def transport(spec,writer):
        for index in range(5400):
            for symbol in stream.triangle_bound.SYMBOLS:writer.append('inbound-frame',message(symbol,index,padding=250),(index+1)*100_000_000,opcode=1,fin=True)
        return {'status':'complete','end_reason':'deadline','end_elapsed_ns':540_000_000_000}
    def persist(name,value):(tmp_path/name).write_bytes(stream.lifecycle_bytes(value))
    capture,bins,summary,cells=stream.run(stream.default_spec(),capture,admission,persist,lambda n:(tmp_path/n).read_bytes(),transport)
    assert len(cells)==9 and all(c['status']=='complete' for c in cells)
    assert all(c['valid_bins']==5400 for c in summary['cases'].values())
    assert sum(p.stat().st_size for p in tmp_path.iterdir())<=64*1024**2
    assert all((tmp_path/f'raw-{i:02d}.json').stat().st_size<=1024**2 for i in range(32))

DRIVER=r'''
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
import fixture
import triangle_stream as runner
from tradingagents.research import runtime_hashes
root=Path(__file__).resolve().parent
fixture.DIRECTORY=root
mode=sys.argv[1]
def git(*args):return subprocess.check_output(['git','-c','core.hooksPath=/dev/null',*args],cwd=root,text=True).strip()
def sha(name):return hashlib.sha256((root/name).read_bytes()).hexdigest()
capture,admission=fixture.fixture_metadata()
for name,value in [('metadata_capture',capture),('metadata_admission',admission),('request_spec',runner.default_spec())]:
    (root/(name+'.json')).write_bytes(runner.lifecycle_bytes(value))
(root/'charter.md').write_text('Invented bounded stream lifecycle; no market observation.')
git('init','-q')
ids=['transport',*[runner.triangle_bound.case_id(*case) for case in runner.triangle_bound.CASES]]
outputs=[f'raw-{i:02d}.json' for i in range(32)]+['capture.json','bins.json','summary.json']
names=['driver.py','fixture.py','triangle_stream.py','triangle_bound.py','triangle_capture.py','options_metadata.py','carry_capture.py']
registration={'schema_version':1,'program_id':'synthetic-stream','families':{'s':{'mechanism_id':'synthetic-stream','attempt_budget':1,'prior_attempts':0,'history_reference':'invented'}},'datasets':{'s':{'identity':'invented','history_reference':'invented','exposures':[{'start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','state':'spent'}]}},'experiments':{'synthetic-stream':{'family':'s','parent':None,'charter':{'path':'charter.md','sha256':sha('charter.md')},'question':'Synthetic resource validation','stage':'development','reuse':'exploratory','windows':[{'dataset':'s','start':'2000-01-01T00:00:00Z','end':'2001-01-01T00:00:00Z','availability':'existing'}],'inputs':{n:{'path':n+'.json','sha256':sha(n+'.json'),'dataset':'s'} for n in ['request_spec','metadata_capture','metadata_admission']},'source_files':{n:sha(n) for n in names},'runtime_hashes':runtime_hashes(),'selection':None,'cells':ids,'outputs':outputs}}}
(root/'registration.json').write_text(json.dumps(registration))
git('add','.')
git('-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-qm','invented')
source=git('rev-parse','HEAD')
closed=[]
def fake_transport(spec,writer):
    stamp=0
    try:
        if mode=='frames':
            for index in range(100000):writer.append('inbound-frame',b'',0,opcode=9,fin=True)
        for index in range(5400):
            stamp=(index+1)*100_000_000
            if mode=='max' and index%10:continue
            for symbol in runner.triangle_bound.SYMBOLS:
                writer.append('inbound-frame',fixture.message(symbol,index,price=('1.1'+'0'*60+'1') if symbol=='ETHUSDT' else ('1.'+'0'*61+'1'),padding=7500 if mode=='max' else 250),stamp,opcode=1,fin=True)
        if mode=='max':
            stamp=540_000_000_000
            # All bins first exist; final-time opaque control payloads exhaust the exact raw cap.
            payload=fixture.message('BTCUSDT',5401);payload+=b' '*(65536-len(payload))
            while True:writer.append('inbound-frame',payload,stamp,opcode=1,fin=True)
        return {'status':'complete','end_reason':'deadline','end_elapsed_ns':stamp}
    except runner.CaptureLimit as exc:
        return {'status':'unavailable','end_reason':str(exc),'end_elapsed_ns':stamp,'unretained_event':writer.dropped}
    finally:closed.append(time.monotonic())
runner.acquire=fake_transport
runner.REGISTRATION='registration.json';runner.EXPERIMENT='synthetic-stream'
runner.__file__=str(root/'research/fixture/triangle_stream.py')
sys.argv=['triangle_stream.py','--source',source]
runner.main()
finalize=time.monotonic()-closed[0]
folder=root/'research_runs/synthetic-stream/outputs'
summary=json.loads((folder/'summary.json').read_text());capture=json.loads((folder/'capture.json').read_text());bins=json.loads((folder/'bins.json').read_text())
assert len(list(folder.iterdir()))==35
assert sum(len(rows) for rows in bins['series'].values())==43200
assert all(row['valid_bins']==(5400 if mode=='full' else 0 if mode=='frames' else 5399) for row in summary['cases'].values())
assert any(row['qualified_bins']==(5400 if mode=='full' else 0 if mode=='frames' else 5399) for row in summary['cases'].values())
assert finalize<=60
actual=sum(path.stat().st_size for path in folder.iterdir())
assert actual<=64*1024**2
assert all((folder/f'raw-{i:02d}.json').stat().st_size<=1024**2 for i in range(32))
if mode=='max':assert capture['transport']['unretained_event'] and capture['raw_payload_bytes']>19*1024**2
if mode=='frames':assert capture['transport']['end_reason']=='raw_chunk_capacity' and 80000<capture['receipt_count']<100000
(root/'synthetic-result.json').write_text(json.dumps({'mode':mode,'output_bytes':actual,'raw_bytes':capture['raw_payload_bytes'],'finalization_seconds':finalize,'cpu_count':len(os.sched_getaffinity(0)),'top_cells':9,'subslots':43200,'source_sha256':{n:sha(n) for n in names}}))
'''

@pytest.mark.parametrize('mode',['full','max','frames'])
def test_actual_guarded_lifecycle(tmp_path,mode):
    import shutil,subprocess
    for name in ['triangle_stream.py','triangle_bound.py','triangle_capture.py','options_metadata.py','carry_capture.py','triangle-request-spec.json','triangle_stream_guard.py','resource_guard_v2.py']:
        shutil.copyfile(DIRECTORY/name,tmp_path/name)
    shutil.copyfile(__file__,tmp_path/'fixture.py')
    (tmp_path/'driver.py').write_text(DRIVER)
    result=subprocess.run([sys.executable,'-B',str(tmp_path/'triangle_stream_guard.py'),'--report',str(tmp_path/'guard-report.json'),'--',sys.executable,'-B',str(tmp_path/'driver.py'),mode],capture_output=True,text=True,timeout=90)
    (tmp_path/'guard-stdout.txt').write_text(result.stdout+result.stderr)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads((tmp_path/'guard-report.json').read_text())
    assert report['rss_limit_bytes']==512*1024**2 and report['wall_limit_seconds']==600
    assert report['limit_reason'] is None


def test_exact_parity_and_fee_adjusted_parity():
    for prices,fee in [({'BTCUSDT':'1','ETHBTC':'13','ETHUSDT':'13'},0),({'BTCUSDT':'1','ETHBTC':'997002999','ETHUSDT':'1000000000'},.001)]:
        quotes={s:stream._message(message(s,price=p))[2] for s,p in prices.items()}
        positive,sizes=stream.exact_screen(quotes,'btc-eth',1000,fee)
        assert not positive and all(sizes)
        if fee==0:assert stream.triangle_bound._case(quotes,'btc-eth',1000,fee)['cash_profit_usdt']>0


@pytest.mark.parametrize('value',['1'*65,'1e33','1e-33','NaN','Infinity'])
def test_numeric_scope(value):
    with pytest.raises(ValueError):stream._message(message('BTCUSDT',price=value))


def test_id_bounds_and_named_shutdown():
    with pytest.raises(ValueError):stream._message(message('BTCUSDT',2**63))
    bins,summary=replay(quotes()+[(100_000_000,b'{"e":"serverShutdown"}',{})])
    assert summary['diagnostics']['server_shutdown_messages']==1
    assert 'server_shutdown' in bins['reason_codes'].values()


def test_tiny_frames_exact_count_cap():
    store={};spec=stream.default_spec()
    writer=stream.RawChunks(spec,lambda n,v:store.__setitem__(n,stream.lifecycle_bytes(v)))
    with pytest.raises(stream.CaptureLimit,match='raw_chunk_capacity'):
        for index in range(100000):writer.append('inbound-frame',b'',index,opcode=9,fin=True)
    writer.finish()
    assert sum(1 for _ in writer.replay_records(store.__getitem__))==writer.count<100000
    # The independent frame guard can bind before chunk capacity at a smaller synthetic bound.
    small={**spec,'frame_limit':3};short=stream.RawChunks(small,lambda *args:None)
    for index in range(3):short.append('inbound-frame',b'',index,opcode=9,fin=True)
    with pytest.raises(stream.CaptureLimit,match='frame_count_cap'):short.append('inbound-frame',b'',4,opcode=9,fin=True)
    assert sum(v['bytes'] for v in writer.chunks)<32*1024**2


def test_deep_json_preserves_denominator_and_receipts(tmp_path):
    capture,admission=fixture_metadata()
    def transport(spec,writer):
        writer.append('inbound-frame',b'{"x":'+b'['*12000+b'0'+b']'*12000+b'}',0,opcode=1,fin=True)
        return {'status':'complete','end_reason':'deadline','end_elapsed_ns':540_000_000_000}
    def persist(name,value):(tmp_path/name).write_bytes(stream.lifecycle_bytes(value))
    _,bins,summary,cells=stream.run(stream.default_spec(),capture,admission,persist,lambda n:(tmp_path/n).read_bytes(),transport)
    assert len(cells)==9 and len(list(tmp_path.iterdir()))==35
    assert sum(len(rows) for rows in bins['series'].values())==43200
    assert summary['diagnostics']['malformed_messages']==1

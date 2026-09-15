import importlib.util
import json
from datetime import datetime,timezone
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('tested_future_source',Path(__file__).resolve().parents[2]/'research/defi-depth-2026-09-15/financial_source_policy.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def design():
    return {'url':'https://mainnet.base.org','attempt_delays_seconds':[0,15,60],'minimum_response_pause_seconds':5,
            'inherited_endpoint_stop':None,'prior_request_keys':[],'max_physical_requests':100,
            'worst_case_raw_bytes':100*262144,'denials_stop_endpoint':[401,403,418,429,451],
            'recognized_rpc_throttling':{'codes':[-32016],'message_fragments_casefold':sorted(m.THROTTLE_FRAGMENTS)}}


class Fake:
    def __init__(self,responses):self.responses=list(responses);self.now=0;self.saved={};self.calls=[];self.sleeps=[]
    def publish(self,name,value):
        assert name not in self.saved;self.saved[name]=value
    def sleep(self,seconds):assert 0<seconds<=5;self.now+=seconds;self.sleeps.append(seconds)
    def fetch(self,url,payload,*,max_bytes):
        assert self.saved[payload['id']+'-attempt.json']['attempted']
        self.calls.append((self.now,payload,max_bytes))
        status,body,error,complete=self.responses.pop(0)
        if isinstance(body,dict):body=json.dumps({**body,'jsonrpc':'2.0','id':payload['id']}).encode()
        return {'http_status':status,'body':body,'headers':{},'error':error,'body_complete':complete}
    def source(self,d=None):
        return m.Source(d or design(),self.publish,self.fetch,monotonic=lambda:self.now,sleep=self.sleep,
                        utc=lambda:datetime(2026,1,1,tzinfo=timezone.utc))


def good():return (200,{'result':'0x2a'},None,True)
def transient():return (503,{'error':{'code':-32011,'message':'no backend is currently healthy to serve traffic'}},'HTTP 503',True)
def parse(value,observed):return int(value,16)


def test_three_visible_slots_and_only_new_transient_retries():
    f=Fake([transient(),transient(),good()]);s=f.source()
    r=s.request('income','eth_call',[{'to':'a','data':'b'},'fixed'],parse)
    assert r['status']=='complete' and r['value']==42 and r['successful_physical_slot']==3
    assert [c[0] for c in f.calls]==[0,15,75]
    assert s.attempts==3 and len(f.saved)==6
    assert s.raw_bytes==sum(o['body_bytes'] for k,o in f.saved.items() if k.endswith('receipt.json'))
    assert all(c[2]==16384 for c in f.calls)


def test_success_unused_attempts_and_next_request_pacing():
    f=Fake([good(),good()]);s=f.source()
    s.request('first','eth_call',['first'],parse);s.request('second','eth_call',['second'],parse)
    assert [c[0] for c in f.calls]==[0,5]
    assert len(f.saved)==12
    assert not f.saved['first-try2-attempt.json']['attempted']
    assert not f.saved['first-try3-attempt.json']['attempted']


def test_http_denial_or_rpc_quota_stops_all_later_calls():
    for response in [(429,b'quota','HTTP 429',True),
                     (200,{'error':{'code':-32016,'message':'limited'}},None,True),
                     (503,{'error':{'code':-1,'message':'rate limit'}},'HTTP 503',True)]:
        f=Fake([response]);s=f.source()
        assert s.request('a','eth_call',['a'],parse)['status']=='unavailable'
        assert s.request('b','eth_call',['b'],parse)['status']=='unavailable'
        assert s.stopped and s.attempts==1 and len(f.saved)==12


def test_inherited_failed_key_and_duplicate_new_key_never_sent():
    f=Fake([good()]);d=design();d['prior_request_keys']=[m.Q.request_key('eth_call',['old'])];s=f.source(d)
    with pytest.raises(ValueError,match='inherited'):s.request('a','eth_call',['old'],parse)
    assert not f.calls
    s.request('b','eth_call',['new'],parse)
    with pytest.raises(ValueError,match='duplicate new'):s.request('c','eth_call',['new'],parse)
    assert len(f.calls)==1


def test_schema_error_no_retry_but_missing_dependencies_publish_all_slots():
    f=Fake([(200,{'result':'not hex'},None,True)]);s=f.source()
    assert s.request('a','eth_call',['a'],parse)['status']=='unavailable'
    assert s.attempts==1
    for name in ('b','c'):
        assert s.request(name,'eth_call',[None],parse,dependency='missing block')['status']=='unavailable'
    assert len(f.saved)==18 and len(f.calls)==1


def test_transport_timeout_retry_and_certificate_no_retry():
    f=Fake([(None,b'', 'TimeoutError: 30-second request wall deadline',False),good()]);s=f.source()
    assert s.request('a','eth_call',['a'],parse)['status']=='complete' and s.attempts==2
    f=Fake([(None,b'', 'URLError: certificate verify failed',False)]);s=f.source()
    assert s.request('a','eth_call',['a'],parse)['status']=='unavailable' and s.attempts==1


def test_exhausted_retries_and_pre_send_resource_bound():
    f=Fake([transient()]*3);s=f.source()
    assert s.request('a','eth_call',['a'],parse)['status']=='unavailable' and s.attempts==3
    f=Fake([]);d=design();d['worst_case_raw_bytes']=16383;s=f.source(d)
    with pytest.raises(ValueError,match='reservation'):s.request('a','eth_call',['a'],parse)
    assert not f.calls and not f.saved


def test_actual_clock_header_does_not_claim_adjacent_or_nearest():
    day={'candidate_block':123,'timestamp':1000}
    raw={'number':'0x7b','timestamp':'0x3e7','baseFeePerGas':'0x1','hash':'0x'+'a'*64,'parentHash':'0x'+'b'*64}
    r=m.actual_clock_header(raw,day,2000)
    assert r['actual_clock_offset_seconds']==-1 and not r['nearest_block_or_adjacent_bracket_proved']
    raw['timestamp']='0x3e6'
    with pytest.raises(ValueError,match='clock'):m.actual_clock_header(raw,day,2000)


def test_nonretryable_body_has_priority_over_transient_http():
    for body in (b'rate limit exceeded',b'certificate verification failed',
                 {'error':{'code':-32601,'message':'Method not found'}},
                 {'error':{'code':-32000,'message':'execution reverted'}}):
        f=Fake([(503,body,'HTTP 503',True)]);s=f.source()
        assert s.request('a','eth_call',['a'],parse)['status']=='unavailable'
        assert s.attempts==1
        if body==b'rate limit exceeded':assert s.stopped


def test_mandatory_policy_cannot_be_weakened_or_mutated_by_caller():
    for field in ('denials_stop_endpoint','recognized_rpc_throttling'):
        d=design();d[field]=[] if field=='denials_stop_endpoint' else {'codes':[],'message_fragments_casefold':[]}
        with pytest.raises(ValueError,match='cannot be weakened'):Fake([]).source(d)
    d=design();f=Fake([(429,b'quota','HTTP 429',True)]);s=f.source(d)
    d['denials_stop_endpoint'].clear();d['recognized_rpc_throttling']['codes'].clear()
    s.request('a','eth_call',['a'],parse);s.request('b','eth_call',['b'],parse)
    assert s.attempts==1 and s.stopped


def test_reservation_types_are_exact_positive_integers():
    for value in (0,-1,0.5,True,float('inf')):
        for key in ('max_physical_requests','worst_case_raw_bytes'):
            d=design();d[key]=value
            with pytest.raises(ValueError,match='positive exact integer'):Fake([]).source(d)


def test_retry_after_honored_or_endpoint_stopped_without_retry():
    for header in ('120','Thu, 01 Jan 2026 00:02:00 GMT'):
        f=Fake([transient(),good()]);original=f.fetch
        def fetch(url,payload,*,max_bytes):
            response=original(url,payload,max_bytes=max_bytes)
            if response['http_status']==503:response['headers']['Retry-After']=header
            return response
        s=m.Source(design(),f.publish,fetch,monotonic=lambda:f.now,sleep=f.sleep,utc=lambda:datetime(2026,1,1,tzinfo=timezone.utc))
        assert s.request('a','eth_call',['a'],parse)['status']=='complete'
        assert [c[0] for c in f.calls]==[0,120]
    for header in ('301','nonsense','-1'):
        f=Fake([transient()]);original=f.fetch
        def fetch(url,payload,*,max_bytes):
            response=original(url,payload,max_bytes=max_bytes);response['headers']['Retry-After']=header;return response
        s=m.Source(design(),f.publish,fetch,monotonic=lambda:f.now,sleep=f.sleep,utc=lambda:datetime(2026,1,1,tzinfo=timezone.utc))
        assert s.request('a','eth_call',['a'],parse)['status']=='unavailable'
        s.request('b','eth_call',['b'],parse)
        assert s.attempts==1 and s.stopped

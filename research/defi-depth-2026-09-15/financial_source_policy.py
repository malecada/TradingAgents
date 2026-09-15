"""Pure orchestration for prospectively enumerated F1/F3 source requests.

Each new logical key has three visible physical slots. Transient retries belong
to that same new claim; inherited actual/uncertain keys cannot be requested.
No historical runner or active F2 policy is changed by this module.
"""
import base64
from copy import deepcopy
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
import math
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

Q=module('future_retained_source_primitives','q3_protocol.py')
T=module('future_bounded_transport','financial_transport.py')
ALLOWED=('eth_getBlockByNumber','eth_call','eth_getCode')
DELAYS=(0,15,60)
CAPS={'eth_getBlockByNumber':262144,'eth_call':16384,'eth_getCode':65536}
DENIALS={401,403,418,429,451}
THROTTLE_CODES={-32016}
THROTTLE_FRAGMENTS={'over rate limit','rate limit','rate-limit','rate_limit','too many requests','quota exceeded'}
HARD_FAILURE_FRAGMENTS=('certificate','ssl:','authentication','permission denied','access denied','unauthorized','forbidden')


class Source:
    def __init__(self,design,publish,fetch=T.public_post,*,monotonic=time.monotonic,sleep=time.sleep,
                 utc=lambda:datetime.now(timezone.utc)):
        design=deepcopy(design)
        if any(type(design[k]) is not int or design[k]<=0 for k in ('max_physical_requests','worst_case_raw_bytes')):
            raise ValueError('positive exact integer resource reservations required')
        if set(design['denials_stop_endpoint'])!=DENIALS:
            raise ValueError('mandatory endpoint-denial policy cannot be weakened')
        rule=design['recognized_rpc_throttling']
        if set(rule['codes'])!=THROTTLE_CODES or set(rule['message_fragments_casefold'])!=THROTTLE_FRAGMENTS:
            raise ValueError('mandatory throttle policy cannot be weakened')
        if design['url']!='https://mainnet.base.org':raise ValueError('fixed Base public endpoint required')
        if design['attempt_delays_seconds']!=list(DELAYS) or design['minimum_response_pause_seconds']!=5:
            raise ValueError('exact registered pace/retry design required')
        if design.get('inherited_endpoint_stop'):
            raise ValueError('inherited endpoint stop cannot be bypassed')
        self.design,self.publish,self.fetch=design,publish,fetch
        self.monotonic,self.sleep,self.utc=monotonic,sleep,utc
        self.prior=set(design['prior_request_keys']);self.keys=set();self.ids=set()
        self.stopped=None;self.last_response=None;self.attempts=0;self.raw_bytes=0;self.provider_pause=0

    def wait_after_response(self,delay):
        if self.last_response is not None:
            while (remaining:=self.last_response+delay-self.monotonic())>0:self.sleep(min(remaining,5))

    def limited(self,body):
        text=body.decode('utf-8',errors='replace').casefold()
        if any(fragment in text for fragment in THROTTLE_FRAGMENTS):
            return 'recognized throttle text in retained response'
        try:value=Q.old.q1.helpers.strict_json(body)
        except (ValueError,TypeError):return None
        if not isinstance(value,dict) or not isinstance(value.get('error'),dict):return None
        error=value['error']
        if error.get('code') in THROTTLE_CODES:
            return 'recognized RPC throttle: '+str(error)
        return None

    @staticmethod
    def nontransient_failure(body,error):
        text=(body.decode('utf-8',errors='replace')+' '+str(error or '')).casefold()
        if any(fragment in text for fragment in HARD_FAILURE_FRAGMENTS):
            return 'nonretryable access/authentication/TLS failure'
        try:value=Q.old.q1.helpers.strict_json(body)
        except (ValueError,TypeError):return None
        if isinstance(value,dict) and isinstance(value.get('error'),dict):
            rpc=value['error']
            # Only this explicitly registered backend-outage RPC envelope is
            # compatible with retryable502/503/504. Other RPC errors never retry.
            if rpc.get('code')==-32011 and str(rpc.get('message','')).casefold()=='no backend is currently healthy to serve traffic':
                return None
            return 'nonretryable RPC error: '+str(rpc)
        return None

    def request(self,logical_id,method,params,parser,*,dependency=None):
        if method not in ALLOWED or logical_id in self.ids or not isinstance(logical_id,str) or not logical_id:
            raise ValueError('unique logical ID and allowed read-only method required')
        self.ids.add(logical_id)
        key=Q.request_key(method,params)
        if dependency is None and self.stopped is None:
            if key in self.prior:raise ValueError('inherited attempted or uncertain request cannot be retried or aliased')
            if key in self.keys:raise ValueError('duplicate new logical key; only its internal physical slots may retry')
            self.keys.add(key)
        result=None;last_reason=None;retry=True;retry_after_delay=0
        for index,delay in enumerate(DELAYS):
            physical_id=f'{logical_id}-try{index+1}'
            reason=self.stopped or dependency
            if result is not None:reason='logical request already complete; remaining physical slot unused'
            elif not retry:reason=last_reason or 'nontransient source failure; no further physical attempt'
            member={'jsonrpc':'2.0','id':physical_id,'method':method,'params':params}
            if reason is None:
                if self.attempts>=self.design['max_physical_requests']:raise ValueError('physical request reservation exhausted')
                if self.raw_bytes+CAPS[method]>self.design['worst_case_raw_bytes']:raise ValueError('raw reservation insufficient before request')
                self.wait_after_response(max(5,delay,retry_after_delay,self.provider_pause))
            intent={'id':physical_id,'logical_id':logical_id,'logical_key':key,'physical_slot':index+1,
                'attempted':reason is None,'reason':reason,'url':self.design['url'],'request':member,
                'request_utc':self.utc().isoformat(),'max_response_bytes':CAPS[method]}
            self.publish(physical_id+'-attempt.json',intent)
            if reason is None:
                self.attempts+=1
                response=self.fetch(self.design['url'],member,max_bytes=CAPS[method])
                self.last_response=self.monotonic()
            else:response={'body':b'','http_status':None,'headers':{},'error':reason,'body_complete':False}
            body=response['body']
            if not isinstance(body,bytes) or len(body)>CAPS[method]:raise ValueError('transport violated exact prefix byte contract')
            self.raw_bytes+=len(body)
            if reason is None:
                if response['http_status'] in self.design['denials_stop_endpoint']:
                    self.stopped='HTTP access/quota denial: '+str(response['http_status'])
                self.stopped=self.stopped or self.limited(body)
                combined=(body.decode('utf-8',errors='replace')+' '+str(response['error'] or '')).casefold()
                if any(fragment in combined for fragment in HARD_FAILURE_FRAGMENTS):
                    self.stopped=self.stopped or 'Access/authentication/TLS response; endpoint stopped'
            ended=self.utc()
            retry_after_delay=0
            if reason is None and response['headers'].get('Retry-After') is not None:
                try:
                    value=response['headers']['Retry-After'].strip()
                    if value.isascii() and value.isdecimal():retry_after_delay=int(value)
                    else:
                        target=parsedate_to_datetime(value)
                        if target.tzinfo is None:raise ValueError('Retry-After lacks timezone')
                        retry_after_delay=max(0,math.ceil((target-ended).total_seconds()))
                    if retry_after_delay>300:raise ValueError('Retry-After exceeds registered300second bound')
                except (ValueError,TypeError,OverflowError) as exc:
                    self.stopped=self.stopped or 'Unusable provider Retry-After; endpoint stopped: '+str(exc)
            if reason is None:self.provider_pause=retry_after_delay
            receipt={**intent,'retrieval_utc':ended.isoformat(),'http_status':response['http_status'],
                'headers':response['headers'],'body_complete':response['body_complete'],'error':response['error'],
                'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'body_base64':base64.b64encode(body).decode(),
                'endpoint_stopped_reason':self.stopped,'provider_retry_after_seconds':retry_after_delay}
            self.publish(physical_id+'-receipt.json',receipt)
            if reason is not None:continue
            retry=False
            hard_failure=self.nontransient_failure(body,response['error'])
            if self.stopped:last_reason=self.stopped
            elif hard_failure:last_reason=hard_failure
            elif response['http_status'] in (502,503,504):
                last_reason='registered transient HTTP '+str(response['http_status']);retry=True
            elif response['http_status'] is None and response['error']:
                # Only known transport classes; arbitrary adapter errors are not retryable.
                error=str(response['error'])
                retry=error.startswith(('TimeoutError:','URLError:','ConnectionError:','ConnectionResetError:',
                                        'ConnectionAbortedError:','RemoteDisconnected:','IncompleteRead:'))
                if any(term in error.casefold() for term in ('certificate','ssl:','authentication','permission denied','access denied')):retry=False
                last_reason=error
            elif response['error'] or response['http_status']!=200 or not response['body_complete']:
                last_reason=response['error'] or 'incomplete or non-success HTTP response'
                # Body read timeout may have status200 and a retained partial prefix.
                retry=str(response['error']).startswith(('TimeoutError:','IncompleteRead:'))
            else:
                try:
                    decoded=Q.old.q1.envelope(body,member)
                    result={'id':logical_id,'status':'complete','value':parser(decoded,ended.timestamp()),
                            'successful_physical_slot':index+1}
                except (ValueError,TypeError,KeyError) as exc:
                    last_reason='nonretryable RPC/schema/model failure: '+str(exc)
        return result or {'id':logical_id,'status':'unavailable','reason':last_reason or self.stopped or dependency or 'all physical slots unavailable'}


def actual_clock_header(value,day,observed):
    header=Q.old.parse_header(value,day['candidate_block'],observed)
    if not day['timestamp']-1<=header['timestamp']<=day['timestamp']:
        raise ValueError('recorded header clock outside fixed target-minus-one-second interval')
    return {**header,'target_timestamp':day['timestamp'],'actual_clock_offset_seconds':header['timestamp']-day['timestamp'],
            'provider_assertion_only':True,'nearest_block_or_adjacent_bracket_proved':False}

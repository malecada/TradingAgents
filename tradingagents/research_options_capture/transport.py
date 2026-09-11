"""Bounded public HTTPS subprocess transport; no admission, selection, or schedule.

The caller must own a valid assignment and durable journal intent for each
request. Received raw bytes are persisted before any market-body interpretation.
Tests inject a fake child command; the production wrapper never accepts one.
"""
import base64
import ctypes
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import sys
import time
from urllib.parse import urlencode, urlsplit

MAX_FRAME=131072


def request_url(request):
    if set(request)!={'endpoint','parameters'}:raise ValueError('exact endpoint/parameters required')
    endpoint=request['endpoint'];params=request['parameters'];url=urlsplit(endpoint)
    if url.scheme!='https' or url.username or url.password or url.port or url.query or url.fragment:raise ValueError('literal public HTTPS endpoint required')
    routes={
      'eapi.binance.com':{'/eapi/v1/time':(),'/eapi/v1/exchangeInfo':(),'/eapi/v1/index':('underlying',),'/eapi/v1/depth':('symbol','limit'),'/eapi/v1/mark':('symbol',)},
      'fapi.binance.com':{'/fapi/v1/time':(),'/fapi/v1/exchangeInfo':(),'/fapi/v1/fundingInfo':(),'/fapi/v1/depth':('symbol','limit'),'/fapi/v1/premiumIndex':('symbol',),'/fapi/v1/fundingRate':('symbol','startTime','endTime','limit')}}
    if url.hostname not in routes or url.path not in routes[url.hostname] or not isinstance(params,dict) or set(params)!=set(routes[url.hostname][url.path]):raise ValueError('unregistered public route/parameters')
    if 'underlying' in params and params['underlying'] not in ('BTCUSDT','ETHUSDT'):raise ValueError('underlying')
    if 'symbol' in params:
        symbol=params['symbol']
        if not isinstance(symbol,str) or len(symbol)>64:raise ValueError('symbol')
        if url.hostname=='fapi.binance.com' and symbol not in ('BTCUSDT','ETHUSDT'):raise ValueError('futures symbol')
        if url.hostname=='eapi.binance.com' and not re.fullmatch(r'(BTC|ETH)-\d{6}-\d+(?:\.\d+)?-[CP]',symbol):raise ValueError('options symbol')
    if 'limit' in params and (type(params['limit']) is not int or params['limit']!=(1000 if url.path.endswith('fundingRate') else 10)):raise ValueError('fixed limit')
    for key in ('startTime','endTime'):
        if key in params and (type(params[key]) is not int or not 0<=params[key]<=2**63-1):raise ValueError('integer funding window')
    if 'startTime' in params and params['startTime']>params['endTime']:raise ValueError('funding window ordering')
    return endpoint+('?' + urlencode(params) if params else '')


def _emit(value):
    sys.stdout.write(json.dumps(value,separators=(',',':'),allow_nan=False)+'\n');sys.stdout.flush()


def worker(spec):
    """Single public attempt; read1 and parent deadline bound slow/blocked peers."""
    parent=spec['parent_pid']
    if type(parent) is not int or os.getppid()!=parent:raise ValueError('worker parent changed')
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(1,signal.SIGKILL,0,0,0)!=0:raise OSError('parent-death guard unavailable')
    if os.getppid()!=parent:raise ValueError('worker parent changed after guard')
    request=spec['request'];url=request_url(request);parts=urlsplit(url)
    cap=spec['body_cap'];deadline=spec['deadline_monotonic_ns']
    if type(cap) is not int or not 0<cap<=5*1024**2 or type(deadline) is not int:raise ValueError('body/deadline bound')
    before=time.time_ns()//1000000;mono=time.monotonic_ns();body=bytearray();pending=bytearray();status=None;error=None;complete=False;conn=None
    # At most63 full frames plus one tail, matching the journal's64-prefix cap.
    # Small routine bodies use a single frame. Unpublished child/pipe bytes are
    # not claimed durable; parent recovery preserves the uncertain intent.
    frame_size=max(8192,(cap+62)//63)
    def retain(chunk):
        room=cap-len(body);part=chunk[:room];body.extend(part);pending.extend(part)
        while len(pending)>=frame_size:
            _emit({'kind':'chunk','base64':base64.b64encode(pending[:frame_size]).decode()})
            del pending[:frame_size]
        if len(chunk)>room:raise ValueError('response body exceeds bound')
    _emit({'kind':'start','request_ms':before,'request_monotonic_ns':mono})
    try:
        remaining=(deadline-time.monotonic_ns())/1e9
        if remaining<=0:raise TimeoutError('deadline before connection')
        conn=http.client.HTTPSConnection(parts.hostname,timeout=remaining)
        conn.request('GET',parts.path+('?' + parts.query if parts.query else ''),headers={'Accept':'application/json','User-Agent':'registered-options-research/1'})
        response=conn.getresponse();status=response.status
        _emit({'kind':'headers','http_status':status})
        while True:
            remaining=(deadline-time.monotonic_ns())/1e9
            if remaining<=0:raise TimeoutError('response deadline')
            if conn.sock is not None:conn.sock.settimeout(remaining)
            try:chunk=response.read1(min(4096,cap+1-len(body)))
            except http.client.IncompleteRead as exc:
                retain(exc.partial)
                raise
            if not chunk:
                if response.length not in (None,0):raise http.client.IncompleteRead(b'',response.length)
                complete=True;break
            retain(chunk)
        if status!=200:error='HTTP '+str(status)+'; no redirect or retry'
    except Exception as exc:error=type(exc).__name__+': '+str(exc)[:256]
    finally:
        if pending:_emit({'kind':'chunk','base64':base64.b64encode(pending).decode()})
        if conn is not None:
            try:conn.close()
            except Exception as exc:
                complete=False;error=type(exc).__name__+': close failed: '+str(exc)[:240]
    _emit({'kind':'done','http_status':status,'body_complete':complete,'error':error,
           'retrieval_ms':time.time_ns()//1000000,'retrieval_monotonic_ns':time.monotonic_ns(),
           'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest()})


def _collect(journal,names,*,deadline_ms,spawn_command=None):
    """Collect one already-intended group; keep partial/late/denied slots.

    Full journal validation must precede the acquisition window. Raw bodies are
    never interpreted here. A process crash can leave an intent without receipt;
    controlled recovery marks that slot unavailable, never reissues it.
    """
    if not names or len(names)>16 or len(set(names))!=len(names) or type(deadline_ms) is not int:raise ValueError('bounded group/deadline')
    # Reassert existing journal authority at the side-effect boundary, including
    # active context, unchanged lock/source/claim and absence of a terminal seal.
    journal._boundary()
    journal._current()
    wall=time.time_ns()//1000000;mono=time.monotonic_ns()
    deadline=mono+max(0,deadline_ms-wall)*1000000
    if deadline_ms-wall>60000:raise ValueError('at most60second invocation')
    urls={}
    # Validate every precondition before any child or journal mutation. A mixed
    # valid/invalid group must not consume or overwrite an existing attempt.
    for name in names:
        slot=journal.slots[name]
        if wall<slot['scheduled_ms']:raise ValueError('no request before scheduled window')
        if slot['deadline_ms']!=deadline_ms or not (journal.path/('intent-'+name+'.json')).is_file():raise ValueError('matching durable intent/deadline required')
        if (journal.path/('receipt-'+name+'.json')).exists():raise ValueError('receipt already exists; no retry')
        urls[name]=request_url(slot['request'])
    if len({journal.slots[n]['scheduled_ms'] for n in names})!=1:raise ValueError('same scheduled group required')
    selector=selectors.DefaultSelector();children={};results={};stop=False
    command=spawn_command or [sys.executable,'-B',str(Path(__file__).resolve()),'--worker']
    invalid_name=None
    try:
        for name in names:
            slot=journal.slots[name]
            if time.monotonic_ns()>=deadline:break
            process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
            children[name]={'process':process,'buffer':bytearray(),'body':bytearray(),'metadata':{'request_url':urls[name],'child_started':True,'attempted':False},'done':False,'eof':False,'phase':'new','frames':0}
            message={'parent_pid':os.getpid(),'request':slot['request'],'body_cap':slot['body_cap'],'deadline_monotonic_ns':deadline}
            process.stdin.write(json.dumps(message).encode());process.stdin.close()
            os.set_blocking(process.stdout.fileno(),False);selector.register(process.stdout,selectors.EVENT_READ,name)
        while any(not row['eof'] for row in children.values()) and time.monotonic_ns()<deadline:
            for key,_ in selector.select(min(.02,max(0,(deadline-time.monotonic_ns())/1e9))):
                name=key.data;row=children[name]
                invalid_name=name
                chunk=os.read(key.fileobj.fileno(),8192)
                if not chunk:
                    if row['buffer']:raise ValueError('trailing incomplete worker frame')
                    selector.unregister(key.fileobj);row['eof']=True;continue
                row['buffer'].extend(chunk)
                while b'\n' in row['buffer']:
                    raw,_,tail=row['buffer'].partition(b'\n');row['buffer']=bytearray(tail)
                    if len(raw)>MAX_FRAME:raise ValueError('worker frame bound')
                    frame=json.loads(raw)
                    if not isinstance(frame,dict):raise ValueError('worker frame object')
                    kind=frame.get('kind')
                    if row['done']:raise ValueError('worker emitted after completion')
                    if kind=='start':
                        if row['phase']!='new' or set(frame)!={'kind','request_ms','request_monotonic_ns'} or any(type(frame[k]) is not int or frame[k]<0 for k in ('request_ms','request_monotonic_ns')):raise ValueError('worker start frame')
                        row['phase']='started';row['metadata'].update({k:frame[k] for k in ('request_ms','request_monotonic_ns')});row['metadata']['attempted']=True
                    elif kind=='headers':
                        if row['phase']!='started' or set(frame)!={'kind','http_status'} or type(frame['http_status']) is not int or not 100<=frame['http_status']<=599:raise ValueError('worker headers frame')
                        row['phase']='body'
                        row['metadata']['http_status']=frame['http_status'];stop|=frame['http_status'] in (403,418,429,451)
                    elif kind=='chunk':
                        if row['phase']!='body' or set(frame)!={'kind','base64'} or not isinstance(frame['base64'],str):raise ValueError('worker chunk frame')
                        part=base64.b64decode(frame['base64'],validate=True)
                        if not part or len(row['body'])+len(part)>journal.slots[name]['body_cap'] or row['frames']>=64:raise ValueError('worker body bound')
                        journal.partial(name,part)
                        row['body'].extend(part);row['frames']+=1
                    elif kind=='done':
                        expected={'kind','http_status','body_complete','error','retrieval_ms','retrieval_monotonic_ns','body_bytes','body_sha256'}
                        if row['phase'] not in ('started','body') or set(frame)!=expected or type(frame['body_complete']) is not bool:raise ValueError('worker done frame')
                        if any(type(frame[k]) is not int or frame[k]<0 for k in ('retrieval_ms','retrieval_monotonic_ns','body_bytes')):raise ValueError('worker done integer')
                        if frame['error'] is not None and (not isinstance(frame['error'],str) or len(frame['error'])>300):raise ValueError('worker error')
                        if frame['http_status']!=row['metadata'].get('http_status') or (frame['body_complete'] and row['phase']!='body'):raise ValueError('worker done status')
                        if frame['body_bytes']!=len(row['body']) or frame['body_sha256']!=hashlib.sha256(row['body']).hexdigest():raise ValueError('worker raw mismatch')
                        row['metadata'].update({k:v for k,v in frame.items() if k!='kind'});row['done']=True
                        row['metadata']['controller_retrieval_ms']=time.time_ns()//1000000
                        row['metadata']['controller_retrieval_monotonic_ns']=time.monotonic_ns()
                    else:raise ValueError('worker frame kind')
                if len(row['buffer'])>MAX_FRAME:raise ValueError('worker pending frame bound')
                invalid_name=None
    except BaseException:
        if invalid_name in children:children[invalid_name]['done']=False
        raise
    finally:
        # Children never survive a completed/failed invocation. Unexpected parent
        # death additionally uses Linux PDEATHSIG in the production child.
        for row in children.values():
            process=row['process']
            if process.poll() is None:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
        cleanup_errors=[]
        for row in children.values():
            process=row['process']
            try:
                row['metadata']['child_exit_code']=process.wait(timeout=2)
                process.stdout.close()
            except (OSError,subprocess.TimeoutExpired) as exc:
                row['done']=False;row['metadata']['cleanup_error']=type(exc).__name__;cleanup_errors.append(type(exc).__name__)
        selector.close()
        retention_errors=[]
        for name in names:
            row=children.get(name);body=bytes(row['body']) if row else b''
            metadata=dict(row['metadata']) if row else {'request_url':urls[name],'child_started':False,'attempted':False}
            if not row or not row['done'] or not row['eof'] or row['buffer'] or metadata.get('child_exit_code')!=0:
                metadata.update(body_complete=False,error='incomplete/deadline/worker protocol; no retry',retrieval_ms=time.time_ns()//1000000,retrieval_monotonic_ns=time.monotonic_ns())
            start=metadata.get('request_ms');start_mono=metadata.get('request_monotonic_ns')
            end=metadata.get('controller_retrieval_ms',metadata.get('retrieval_ms'));end_mono=metadata.get('controller_retrieval_monotonic_ns',metadata.get('retrieval_monotonic_ns'))
            worker_end=metadata.get('retrieval_ms');worker_end_mono=metadata.get('retrieval_monotonic_ns')
            def clock_pair(a,am,b,bm):
                return all(type(v) is int for v in (a,am,b,bm)) and a<=b and am<=bm and abs((b-a)-(bm-am)/1e6)<=100
            consistent=clock_pair(start,start_mono,end,end_mono) and clock_pair(start,start_mono,worker_end,worker_end_mono) and worker_end_mono<=end_mono and worker_end<=end+1
            metadata['clock_consistent']=consistent
            metadata['within_controller_deadline']=type(end) is int and end<=deadline_ms and type(end_mono) is int and end_mono<=deadline
            metadata['body_bytes']=len(body);metadata['body_sha256']=hashlib.sha256(body).hexdigest()
            try:journal.record(name,body,metadata=metadata)
            except Exception as exc:retention_errors.append(name+': '+type(exc).__name__)
            results[name]=metadata
        if cleanup_errors:raise RuntimeError('worker cleanup could not be proved: '+','.join(cleanup_errors))
        if retention_errors:raise RuntimeError('raw receipt publication failed; retain intents/prefixes: '+','.join(retention_errors))
    return {'sources':results,'halt_on_access_restriction':stop,'scope':'Public acquisition only; raw journal source states are not execution or financial admission.'}


def collect(journal,names,*,deadline_ms):
    return _collect(journal,names,deadline_ms=deadline_ms)


if __name__=='__main__':
    if sys.argv[1:]!=['--worker']:raise SystemExit('This module has no standalone capture authority.')
    worker(json.loads(sys.stdin.buffer.read(16385)))

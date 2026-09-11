"""One bounded TLS capture, followed by fixed local-state replay; no orders."""
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import signal
import socket
import ssl
import time

from tradingagents.research import ResearchRun
import triangle_bound
import triangle_capture
from options_metadata import strict_json, lifecycle_bytes

REGISTRATION='research/strategy-search-2026-09-11/gates-triangle-stream.json'
EXPERIMENT='triangle-stream-20260911'
URL='wss://stream.binance.com:9443/stream?streams=btcusdt@bookTicker/ethusdt@bookTicker/ethbtc@bookTicker'
STREAMS={s.lower()+'@bookTicker':s for s in triangle_bound.SYMBOLS}
CHUNKS=32


def default_spec():
    return {'schema_version':1,'experiment':'triangle-stream-20260911','url':URL,'capture_seconds':540,'finalize_seconds':60,
            'bin_ms':100,'bins':5400,'max_local_age_ms':1000,'raw_max_bytes':20*1024**2,
            'message_max_bytes':65536,'frame_limit':100000,'raw_chunks':32,'chunk_max_bytes':1048576,
            'chunk_flush_seconds':30,'output_max_bytes':64*1024**2,'socket_read_bytes':4096,
            'open_timeout_seconds':20,'close_timeout_seconds':2,'http_line_max_bytes':2048,
            'http_max_headers':32,'http_body_max_bytes':65536,'http_wire_prefix_max_bytes':131072,'bin_encoding':'declared-column arrays; shared local quote provenance',
            'websockets_version':'15.0.1','proxy':False,'compression':False,'reconnect':False,
            'dns_policy':'first returned address only; no fallback TCP attempts',
            'decimal_policy':'literal finite decimal strings; prices positive, quantities nonnegative',
            'update_id_max':2**63-1,'decimal_max_characters':64,'decimal_adjusted_exponent_min':-32,'decimal_adjusted_exponent_max':32,
            'qualification':'exact rational sign and per-leg sizes; float financial scalars diagnostic only',
            'metadata_source':'saved triangle exchange-info only; no saved quote substitution',
            'header_allowlist':['date','content-type','upgrade','connection','sec-websocket-accept']}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(raw):return hashlib.sha256(raw).hexdigest()


class CaptureLimit(Exception):pass


class RawChunks:
    """Bounded raw frame receipts; immutable fixed JSON output slots."""
    def __init__(self,spec,persist):
        self.spec=spec;self.persist=persist;self.chunks=[];self.current=[];self.raw_bytes=0;self.count=0;self.last_flush=0;self.current_size=64;self.dropped=None
    def flush(self):
        if not self.current:return
        if len(self.chunks)>=CHUNKS:raise CaptureLimit('raw_chunk_capacity')
        body={'index':len(self.chunks),'receipts':self.current}
        if len(lifecycle_bytes(body))>self.spec['chunk_max_bytes']:raise CaptureLimit('serialized_chunk_cap')
        self.persist(f'raw-{len(self.chunks):02d}.json',body)
        self.chunks.append({'name':f'raw-{len(self.chunks):02d}.json','bytes':len(lifecycle_bytes(body)),'sha256':sha(lifecycle_bytes(body))});self.current=[];self.current_size=64
    def append(self,kind,payload,elapsed_ns,**fields):
        self.dropped={'kind':kind,'body_bytes':len(payload),'body_sha256':sha(payload),'elapsed_ns':elapsed_ns}
        if self.count>=self.spec['frame_limit']:raise CaptureLimit('frame_count_cap')
        if self.raw_bytes+len(payload)>self.spec['raw_max_bytes']:raise CaptureLimit('raw_byte_cap')
        record={'sequence':self.count,'kind':kind,'elapsed_ns':elapsed_ns,'observation_utc':datetime.now(timezone.utc).isoformat(),
                'body_bytes':len(payload),'body_sha256':sha(payload),'body_base64':base64.b64encode(payload).decode(),**fields}
        item=lifecycle_bytes(record)
        bound=len(item)+8*item.count(b'\n')+16
        if self.current_size+bound>self.spec['chunk_max_bytes']:self.flush()
        if len(self.chunks)>=CHUNKS:raise CaptureLimit('raw_chunk_capacity')
        self.current.append(record);self.count+=1;self.raw_bytes+=len(payload);self.current_size+=bound;self.dropped=None
        if elapsed_ns-self.last_flush>=self.spec['chunk_flush_seconds']*10**9:
            self.flush();self.last_flush=elapsed_ns
    def finish(self):
        self.flush()
        while len(self.chunks)<CHUNKS:
            body={'index':len(self.chunks),'receipts':[]};self.persist(f'raw-{len(self.chunks):02d}.json',body);self.chunks.append({'name':f'raw-{len(self.chunks):02d}.json','bytes':len(lifecycle_bytes(body)),'sha256':sha(lifecycle_bytes(body))})

    def replay_records(self,load):
        sequence=0;previous=-1
        for index,ref in enumerate(self.chunks):
            raw=load(ref['name'])
            if len(raw)!=ref['bytes'] or sha(raw)!=ref['sha256']:raise ValueError('persisted chunk integrity')
            chunk=strict_json(raw)
            if chunk['index']!=index:raise ValueError('persisted chunk index')
            for record in chunk['receipts']:
                if record.get('sequence')!=sequence or type(record.get('elapsed_ns')) is not int or record['elapsed_ns']<previous:raise ValueError('raw receipt sequence/clock invalid')
                payload=base64.b64decode(record['body_base64'],validate=True)
                if type(record['body_bytes']) is not int or len(payload)!=record['body_bytes'] or sha(payload)!=record['body_sha256']:raise ValueError('raw receipt integrity')
                sequence+=1;previous=record['elapsed_ns']
                yield record
        if sequence!=self.count:raise ValueError('raw receipt count')


def _protocol(spec):
    # These are package-supported HTTP security settings, fixed before import.
    for key,value in [('MAX_LINE_LENGTH',spec['http_line_max_bytes']),('MAX_NUM_HEADERS',spec['http_max_headers']),('MAX_BODY_SIZE',spec['http_body_max_bytes'])]:
        os.environ['WEBSOCKETS_'+key]=str(value)
    import websockets
    import websockets.http11 as http
    from websockets.client import ClientProtocol
    from websockets.uri import parse_uri
    if websockets.__version__!=spec['websockets_version'] or (http.MAX_LINE_LENGTH,http.MAX_NUM_HEADERS,http.MAX_BODY_SIZE)!=(spec['http_line_max_bytes'],spec['http_max_headers'],spec['http_body_max_bytes']):
        raise ValueError('WebSocket runtime bounds/version differ')
    logger=logging.getLogger('triangle_stream.protocol');logger.disabled=True
    return ClientProtocol(parse_uri(URL),extensions=[],subprotocols=[],max_size=spec['message_max_bytes'],logger=logger)


def acquire(spec,writer):
    """Protocol parsing only. No financial JSON parsing or quote use here."""
    start=time.monotonic_ns();deadline=start+spec['capture_seconds']*10**9
    sock=None;proto=None;opened=False;prefix=bytearray();wire_tail=b''
    report={'url':URL,'attempts':0,'start_utc':datetime.now(timezone.utc).isoformat(),'status':'unavailable','end_reason':'not_started','dns_addresses':[]}
    previous_handler=signal.getsignal(signal.SIGALRM);previous_timer=signal.getitimer(signal.ITIMER_REAL)
    def timeout(*_):raise TimeoutError('fixed_transport_deadline')
    signal.signal(signal.SIGALRM,timeout)
    def elapsed():return time.monotonic_ns()-start
    def outgoing():
        for data in proto.data_to_send():
            if data:
                if opened:writer.append('outbound-control-wire',data,elapsed())
                sock.sendall(data)
            else:
                try:sock.shutdown(socket.SHUT_WR)
                except OSError:pass
    try:
        proto=_protocol(spec)
        signal.setitimer(signal.ITIMER_REAL,max(.001,spec['open_timeout_seconds']-elapsed()/1e9))
        addresses=socket.getaddrinfo('stream.binance.com',9443,type=socket.SOCK_STREAM)
        report['dns_addresses']=[{'family':a[0],'ip':a[4][0]} for a in addresses[:32]]
        if not addresses:raise OSError('no_dns_addresses')
        family,kind,protocol,_,address=addresses[0]
        sock=socket.socket(family,kind,protocol);sock.settimeout(spec['open_timeout_seconds']);report['attempts']=1
        sock.connect(address)
        sock=ssl.create_default_context().wrap_socket(sock,server_hostname='stream.binance.com')
        sock.settimeout(1)
        request=proto.connect();proto.send_request(request);outgoing()
        from websockets.http11 import Response
        from websockets.frames import Frame,Opcode
        while time.monotonic_ns()<deadline:
            if writer.count>=spec['frame_limit']:raise CaptureLimit('frame_count_cap')
            try:data=sock.recv(spec['socket_read_bytes'])
            except socket.timeout:
                if opened and writer.current and elapsed()-writer.last_flush>=spec['chunk_flush_seconds']*10**9:
                    writer.flush();writer.last_flush=elapsed()
                continue
            now=elapsed()
            if not data:
                proto.receive_eof();raise EOFError('connection_closed')
            if not opened:
                remaining=spec['http_wire_prefix_max_bytes']-len(prefix);prefix.extend(data[:remaining])
                if len(data)>remaining:raise CaptureLimit('http_prefix_cap')
            wire_tail=(wire_tail+data)[-spec['message_max_bytes']:]
            proto.receive_data(data)
            for event in proto.events_received():
                if isinstance(event,Response):
                    report['http_status']=event.status_code
                    header_block=bytes(prefix).partition(b'\r\n\r\n')[0]
                    allowed=[line for line in header_block.split(b'\r\n')[1:] if line.partition(b':')[0].lower().decode('ascii',errors='replace') in spec['header_allowlist']]
                    writer.append('handshake-header-projection',b'\r\n'.join(allowed),now,original_header_bytes=len(header_block),original_header_sha256=sha(header_block),scope='Only literal allowlisted lines retained; complete received header block hashed, not fully retained.')
                    report['headers']={key.lower():value for key,value in event.headers.raw_items() if key.lower() in spec['header_allowlist']}
                    writer.append('handshake-body',bytes(event.body or b''),now,status=event.status_code,headers=report['headers'])
                    if event.status_code!=101 or proto.handshake_exc is not None:raise ValueError('handshake_rejected')
                    opened=True;prefix.clear();signal.setitimer(signal.ITIMER_REAL,max(.001,(deadline-time.monotonic_ns())/1e9))
                elif isinstance(event,Frame):
                    writer.append('inbound-frame',bytes(event.data),now,opcode=int(event.opcode),fin=event.fin)
                    if event.opcode is Opcode.CLOSE:raise EOFError('server_close')
            outgoing()
            if proto.handshake_exc is not None:raise ValueError('handshake_protocol_error')
            if getattr(proto,'parser_exc',None) is not None:raise ValueError('frame_protocol_error')
        report.update(status='complete' if opened else 'unavailable',end_reason='deadline',end_elapsed_ns=spec['capture_seconds']*10**9)
    except Exception as exc:
        safe_reasons={'connection_closed','server_close','handshake_rejected','handshake_protocol_error','frame_protocol_error','fixed_transport_deadline','no_dns_addresses'}
        reason=str(exc) if isinstance(exc,CaptureLimit) or str(exc) in safe_reasons else type(exc).__name__
        if isinstance(exc,CaptureLimit):report['unretained_event']=writer.dropped
        if isinstance(exc,TimeoutError) and opened and elapsed()>=spec['capture_seconds']*10**9:
            report.update(status='complete',end_reason='deadline',end_elapsed_ns=spec['capture_seconds']*10**9)
        else:
            report.update(end_reason=reason,end_elapsed_ns=min(elapsed(),spec['capture_seconds']*10**9))
            if not opened and prefix:
                try:writer.append('incomplete-handshake-prefix-digest',b'',elapsed(),observed_prefix_bytes=len(prefix),observed_prefix_sha256=sha(bytes(prefix)),complete=False,scope='Bounded observed prefix hashed only; arbitrary header values not retained.')
                except CaptureLimit:report['unretained_handshake_prefix_sha256']=sha(bytes(prefix));report['unretained_handshake_prefix_bytes']=len(prefix)
            # Partial wire diagnostics cannot be promoted into a complete message.
            raw=(bytes(prefix).partition(b'\r\n\r\n')[2] if not opened else wire_tail)[:spec['http_body_max_bytes']]
            if raw:
                try:writer.append('incomplete-wire-diagnostic',raw,elapsed())
                except CaptureLimit:report['unretained_diagnostic_sha256']=sha(raw);report['unretained_diagnostic_bytes']=len(raw)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        if sock is not None:
            try:
                sock.settimeout(spec['close_timeout_seconds'])
                if opened and proto is not None:
                    outgoing()
                    if proto.state.name=='OPEN':proto.send_close(1000,'fixed capture ended');outgoing()
            except Exception:pass
            finally:sock.close()
        signal.signal(signal.SIGALRM,previous_handler);signal.setitimer(signal.ITIMER_REAL,*previous_timer)
    report.update(opened=opened,raw_bytes=writer.raw_bytes,receipt_count=writer.count,unretained_event=report.get('unretained_event',writer.dropped),
                  receipt_scope='Complete protocol frame payloads and bounded failure diagnostics; no financial schema parsed during acquisition.')
    return report


def metadata(capture,admission):
    spec=capture['request_spec']
    if sha(canonical(spec).encode())!=triangle_capture.SPEC_CANONICAL_SHA256:raise ValueError('saved metadata specification differs')
    expected=next(r for r in spec['requests'] if r['id']=='triangle-exchange-info')
    rows=[r for r in capture['requests'] if r['id']==expected['id']];parents=[r for r in admission['cells'] if r['id']==expected['id']]
    if len(rows)!=1 or len(parents)!=1:raise ValueError('saved metadata denominator invalid')
    record=rows[0]
    if canonical({key:record.get(key) for key in expected})!=canonical(expected):raise ValueError('saved metadata identity invalid')
    raw=base64.b64decode(record['body_base64'],validate=True)
    if type(record['body_bytes']) is not int or len(raw)!=record['body_bytes'] or len(raw)>5*1024**2 or sha(raw)!=record['body_sha256'] or record.get('attempted') is not True or record.get('body_complete') is not True or type(record.get('http_status')) is not int or record['http_status']!=200 or record.get('error') is not None:raise ValueError('saved metadata raw receipt invalid')
    result=triangle_capture.parse_response(raw,expected)
    if canonical(parents[0])!=canonical({'id':expected['id'],**result}):raise ValueError('saved metadata normalized admission differs')
    return {'status':'complete','request_utc':record.get('request_utc'),'retrieval_utc':record.get('retrieval_utc'),'scope':'Original metadata clock, not stream-time eligibility or old quote substitution.'}


def _decimal(value,positive):
    if not isinstance(value,str) or len(value)>64:raise ValueError('numeric_scope')
    number=Decimal(value)
    if not number.is_finite() or not -32<=number.adjusted()<=32:raise ValueError('numeric_scope')
    result=float(number)
    if not number.is_finite() or number<0 or positive and number<=0 or not math.isfinite(result) or number!=0 and result==0:raise ValueError('invalid_decimal')
    return result


def _message(raw):
    data=strict_json(raw)
    if not isinstance(data,dict) or data.get('stream') not in STREAMS or not isinstance(data.get('data'),dict):raise ValueError('unknown_envelope')
    row=data['data'];symbol=STREAMS[data['stream']]
    if row.get('s')!=symbol or type(row.get('u')) is not int or not 0<=row['u']<=2**63-1:raise ValueError('invalid_identity')
    quote={out:_decimal(row[key],positive) for out,key,positive in [('bidPrice','b',True),('askPrice','a',True),('bidQty','B',False),('askQty','A',False)]}
    quote['_exact']={out:Fraction(Decimal(row[key])) for out,key in [('bidPrice','b'),('askPrice','a'),('bidQty','B'),('askQty','A')]}
    if quote['_exact']['bidPrice']>quote['_exact']['askPrice']:raise ValueError('crossed_quote')
    return symbol,row['u'],quote,canonical(data)


def exact_screen(quotes,direction,capital,fee):
    amount=Fraction(capital);multiplier=Fraction(999,1000) if fee else Fraction(1);sizes=[]
    for symbol,side,_,_ in triangle_bound.PATHS[direction]:
        row=quotes[symbol]['_exact']
        required=amount/row['askPrice'] if side=='buy' else amount
        sizes.append(required<=row['askQty' if side=='buy' else 'bidQty'])
        amount=(required if side=='buy' else amount*row['bidPrice'])*multiplier
    return amount>capital,sizes


def replay(spec,records,transport,meta):
    """Only called after acquisition closes. Fixed 5400 local right boundaries."""
    state={s:{'id':-1,'valid':False,'reason':'missing'} for s in triangle_bound.SYMBOLS}
    series={triangle_bound.case_id(*case):[] for case in triangle_bound.CASES}
    diagnostics={'duplicates':0,'conflicting_duplicates':0,'regressions':0,'id_jumps':0,'malformed_messages':0,'control_frames':0,'server_shutdown_messages':0}
    iterator=iter(records);pending=next(iterator,None);fragment=None;provenance=[]
    reasons={}
    def reason_id(reason):
        if reason not in reasons:reasons[reason]=len(reasons)+1
        return reasons[reason]
    def invalidate(reason):
        for value in state.values():value.update(valid=False,reason=reason)
    def process(record):
        nonlocal fragment
        raw=base64.b64decode(record['body_base64'],validate=True)
        if type(record['body_bytes']) is not int or len(raw)!=record['body_bytes'] or sha(raw)!=record['body_sha256']:raise ValueError('raw_replay_integrity')
        if record['kind']!='inbound-frame':return
        opcode=record['opcode'];stamp=record['elapsed_ns']
        if opcode in (8,9,10):
            diagnostics['control_frames']+=1
            if opcode==8:invalidate('closed')
            return
        if opcode==2:invalidate('unsupported_binary_message');fragment=None;return
        if opcode==1:
            if fragment is not None:invalidate('fragment_error')
            fragment=bytearray(raw)
        elif opcode==0 and fragment is not None:fragment.extend(raw)
        else:invalidate('fragment_error');fragment=None;return
        if len(fragment)>spec['message_max_bytes']:invalidate('message_size');fragment=None;return
        if not record['fin']:return
        message=bytes(fragment);fragment=None
        try:
            parsed=strict_json(message)
            if isinstance(parsed,dict) and (parsed.get('e')=='serverShutdown' or isinstance(parsed.get('data'),dict) and parsed['data'].get('e')=='serverShutdown'):
                diagnostics['server_shutdown_messages']+=1;invalidate('server_shutdown');return
            symbol,update,quote,payload=_message(message)
        except (ValueError,TypeError,KeyError,InvalidOperation,OverflowError,RecursionError):
            diagnostics['malformed_messages']+=1;invalidate('malformed_message');return
        current=state[symbol]
        if update==current['id']:
            if payload==current.get('payload'):diagnostics['duplicates']+=1
            else:current.update(valid=False,reason='conflicting_duplicate');diagnostics['conflicting_duplicates']+=1
            return
        if update<current['id']:
            current.update(valid=False,reason='regression');diagnostics['regressions']+=1;return
        if current['id']>=0 and update>current['id']+1:diagnostics['id_jumps']+=1
        current.update(id=update,quote=quote,payload=payload,arrival=stamp,valid=True,reason=None)
    for bin_index in range(spec['bins']):
        boundary=(bin_index+1)*spec['bin_ms']*10**6
        while pending is not None and pending['elapsed_ns']<=boundary:
            process(pending);pending=next(iterator,None)
        if meta['status']!='complete':reason='metadata_unavailable'
        elif boundary>transport['end_elapsed_ns'] or boundary==transport['end_elapsed_ns'] and transport['end_reason']!='deadline':reason='capture_tail_'+transport['end_reason']
        elif any(not value['valid'] for value in state.values()):reason=next(value['reason'] for value in state.values() if not value['valid'])
        elif any(boundary-value['arrival']>spec['max_local_age_ms']*10**6 for value in state.values()):reason='stale_local_observation'
        else:reason=None
        provenance.append([reason_id(reason)] if reason else [0,*[(boundary-state[s]['arrival'])/1e6 for s in triangle_bound.SYMBOLS],*[state[s]['id'] for s in triangle_bound.SYMBOLS]])
        for direction,capital,fee in triangle_bound.CASES:
            target=series[triangle_bound.case_id(direction,capital,fee)]
            if reason:target.append([0,reason_id(reason)]);continue
            try:
                value=triangle_bound._case({s:state[s]['quote'] for s in state},direction,capital,fee)
                factor=value['after_fee_roundtrip_factor'];positive,sizes=exact_screen({s:state[s]['quote'] for s in state},direction,capital,fee);size=all(sizes)
                target.append([2 if positive and size else 1,0,value['gross_roundtrip_factor'],factor,value['cash_profit_usdt'],
                               value['convention_diagnostic']['capital_times_log_factor_usdt'],
                               value['three_fees_terminal_usdt_equivalent'],value['fee_decomposition_difference_usdt'],
                               *[leg['executed_base_quantity_before_fee'] for leg in value['trace']],
                               *[leg['displayed_best_base_quantity'] for leg in value['trace']],
                               *sizes])
            except (ValueError,TypeError,OverflowError,ZeroDivisionError):target.append([0,reason_id('case_arithmetic_unavailable')])
    for unused in iterator:pass  # Validate every persisted receipt, including final control traffic.
    summaries={}
    for name,rows in series.items():
        valid=sum(row[0]!=0 for row in rows);qualified=sum(row[0]==2 for row in rows)
        longest=streak=0
        for row in rows:
            streak=streak+1 if row[0]==2 else 0;longest=max(longest,streak)
        summaries[name]={'planned_bins':spec['bins'],'valid_bins':valid,'qualified_bins':qualified,'unqualified_bins':valid-qualified,
                         'unavailable_bins':spec['bins']-valid,'fraction_of_planned':qualified/spec['bins'],
                         'fraction_of_valid':qualified/valid if valid else None,'longest_consecutive_qualified_bins':longest,
                         'sampled_span_seconds':max(0,longest-1)*spec['bin_ms']/1000,
                         'scope':'Overlapping local sampled states, not trades, uninterrupted opportunities, exchange latency or annual frequency.'}
    return {'series':series,'planned_subslots':8*spec['bins'],'bin_ms':spec['bin_ms'],
            'status_codes':{'0':'unavailable','1':'unqualified','2':'qualified'},'reason_codes':{str(value):key for key,value in reasons.items()},
            'columns':['status','reason_code','gross_factor','after_fee_factor','simple_cash_proxy_usdt','invalid_log_cash_shadow','three_fees_usdt_equivalent','fee_reconciliation_difference',
                       'required_qty_leg1','required_qty_leg2','required_qty_leg3','available_qty_leg1','available_qty_leg2','available_qty_leg3',
                       'size_sufficient_leg1','size_sufficient_leg2','size_sufficient_leg3'],
            'unavailable_row_columns':['status','reason_code'],'bin_provenance':provenance,
            'provenance_columns':['reason_code','btc_age_ms','eth_age_ms','ethbtc_age_ms','btc_update_id','eth_update_id','ethbtc_update_id']}, {'cases':summaries,'diagnostics':diagnostics,
            'metadata':meta,'graduation':False,'expected_return_confidence':'unavailable','power':'unavailable','beta':'unavailable','annual_relevance':'unavailable',
            'local_clock_scope':'Latest locally observed states age<=1s at right boundary; no extra arrival-skew cutoff or cross-symbol contemporaneity claim.'}


def run(spec,capture_input,admission_input,persist,load_chunk,transport=None):
    if canonical(spec)!=canonical(default_spec()):raise ValueError('stream spec differs from frozen definition')
    writer=RawChunks(spec,persist)
    report=(transport or acquire)(spec,writer)
    finalization_start=time.monotonic()
    prior_handler=signal.getsignal(signal.SIGALRM);prior_timer=signal.getitimer(signal.ITIMER_REAL)
    def expired(*_):raise TimeoutError('finalization exceeded60seconds')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,spec['finalize_seconds'])
    try:return _finalize(spec,writer,report,capture_input,admission_input,persist,load_chunk,finalization_start)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,prior_handler);signal.setitimer(signal.ITIMER_REAL,*prior_timer)


def _finalize(spec,writer,report,capture_input,admission_input,persist,load_chunk,finalization_start):
    writer.finish()
    try:meta=metadata(capture_input,admission_input)
    except Exception as exc:meta={'status':'unavailable','reason':type(exc).__name__}
    bins,summary=replay(spec,writer.replay_records(load_chunk),report,meta)
    cells=[{'id':'transport','status':report['status'],**({'reason':report['end_reason']} if report['status']!='complete' else {})}]
    for name,row in summary['cases'].items():cells.append({'id':name,'status':'complete' if row['valid_bins'] else 'unavailable',**({'reason':'no valid locally qualified source bins'} if not row['valid_bins'] else {})})
    capture={'transport':report,'raw_chunks':[f'raw-{i:02d}.json' for i in range(CHUNKS)],'receipt_count':writer.count,'raw_payload_bytes':writer.raw_bytes,'planned_top_cells':9,'planned_subslots':43200}
    total=sum(chunk['bytes'] for chunk in writer.chunks)+sum(len(lifecycle_bytes(out)) for out in (capture,bins,summary))
    if total>spec['output_max_bytes']:raise ValueError('total serialized outputs exceed64MiB')
    persist('capture.json',capture);persist('bins.json',bins);persist('summary.json',summary)
    if time.monotonic()-finalization_start>spec['finalize_seconds']:raise TimeoutError('finalization exceeded60seconds')
    return capture,bins,summary,cells


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as registered:
        spec=strict_json(registered.read_input('request_spec'))
        capture=strict_json(registered.read_input('metadata_capture'));admission=strict_json(registered.read_input('metadata_admission'))
        _,_,_,cells=run(spec,capture,admission,registered.write_json,lambda name:(registered.directory/'outputs'/name).read_bytes())
        registered.finish(cells)


if __name__=='__main__':main()

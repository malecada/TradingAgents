"""Readmit fixed parent receipts without fetching or calculating financial outcomes."""
import base64
import csv
from datetime import datetime
import hashlib
import io
import json
from urllib.parse import urlencode
import zipfile
import carry_capture as carry
import dated_archive as archive
import dated_mark as mark

START=1777593600000
END=1782432000000


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(raw):return hashlib.sha256(raw).hexdigest()

def strict(raw):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise ValueError('duplicate JSON key')
            out[key]=value
        return out
    def reject(value):raise ValueError('nonfinite JSON token')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=reject)


def index(rows,ids):
    if not isinstance(rows,list) or len(rows)!=len(ids) or any(not isinstance(row,dict) for row in rows) or {row['id'] for row in rows}!=set(ids):
        raise ValueError('exact parent denominator required')
    return {row['id']:row for row in rows}


def utc(value):
    result=datetime.fromisoformat(value)
    if result.tzinfo is None or result.utcoffset().total_seconds()!=0:raise ValueError('explicit UTC receipt clock required')
    return result


def raw_receipt(record,request,limit,url):
    if canonical({key:record.get(key) for key in request})!=canonical(request):raise ValueError('request identity differs')
    if url is not None and record.get('request_url')!=url:raise ValueError('request URL differs')
    if record.get('attempted') is not True or record.get('body_complete') is not True or type(record.get('http_status')) is not int or record['http_status']!=200 or record.get('error') is not None:raise ValueError('source not complete HTTP200')
    raw=base64.b64decode(record['body_base64'],validate=True)
    if type(record['body_bytes']) is not int or len(raw)!=record['body_bytes'] or len(raw)>limit or sha(raw)!=record['body_sha256']:raise ValueError('raw length/hash/bound differs')
    before,after=utc(record['request_utc']),utc(record['retrieval_utc'])
    if after<before:raise ValueError('negative receipt interval')
    return raw,before,after


def match(parent,normalized):
    if parent.get('status')!='complete' or normalized.get('status')!='complete' or canonical(parent)!=canonical(normalized):raise ValueError('raw reconstruction differs from complete parent admission')


def carry_sources(capture,admission):
    spec=carry.frozen_request_spec()
    if canonical(capture['request_spec'])!=canonical(spec):raise ValueError('carry specification differs')
    ids=[x['id'] for x in spec['requests']]
    rec,parents=index(capture['requests'],ids),index(admission['cells'],ids)
    values,states={},{}
    for req in spec['requests']:
        key=req['id'];state={'id':key,'status':'unavailable'}
        try:
            url=req['url']+('?' + urlencode(req['parameters']) if req['parameters'] else '')
            raw,before,after=raw_receipt(rec[key],req,5*1024**2,url)
            value=strict(raw);normal=carry.admit_response(req,raw)
            if req['kind']=='funding':
                normal['coverage']=carry.funding_coverage(value)
                if normal['coverage']['status']!='complete':raise ValueError('full Q2 funding calendar unavailable')
            if req['kind']=='server-time':
                lo=int(before.timestamp()*1000)-5000;hi=int(after.timestamp()*1000)+5000;t=normal['server_time_ms']
                normal['clock_check']={'earliest_allowed_ms':lo,'latest_allowed_ms':hi,'server_minus_request_ms':t-(lo+5000),'server_minus_retrieval_ms':t-(hi-5000),'agrees':lo<=t<=hi}
                if not lo<=t<=hi:raise ValueError('server clock disagreement')
            match(parents[key],{'id':key,**normal});values[key]=value
            state.update(status='complete',body_sha256=sha(raw),body_bytes=len(raw),request_utc=rec[key]['request_utc'],retrieval_utc=rec[key]['retrieval_utc'])
        except MemoryError:raise
        except Exception as exc:state['reason']=type(exc).__name__+': '+str(exc)
        states[key]=state
    return values,states


def archive_sources(capture,admission):
    spec=archive.frozen_request_spec()
    if canonical(capture['request_spec'])!=canonical(spec):raise ValueError('archive specification differs')
    requests={x['id']:x for x in spec['requests']};ids=list(requests)
    rec,parents=index(capture['requests'],ids),index(admission['cells'],ids)
    raws,states,values={}, {},{}
    for key,req in requests.items():
        states[key]={'id':key,'status':'unavailable'}
        try:
            raw,_,_=raw_receipt(rec[key],req,5*1024**2,None);raws[key]=raw
            if req['kind']=='checksum':
                normal={'id':key,'status':'complete','declared_archive_sha256':archive.checksum_digest(raw,req['filename']),
                        'scope':'Provider checksum format only; paired ZIP integrity/admission reported in ZIP cell.'}
                match(parents[key],normal)
                states[key].update(status='complete',body_sha256=sha(raw),body_bytes=len(raw))
        except MemoryError:raise
        except Exception as exc:states[key]['reason']=type(exc).__name__+': '+str(exc)
    for key,req in requests.items():
        if req['kind']!='zip':continue
        try:
            pair=key[:-3]+'checksum'
            if key not in raws or states[pair]['status']!='complete':raise ValueError('ZIP or checksum unavailable')
            normal=archive.validate_archive(raws[key],raws[pair],req)
            match(parents[key],{'id':key,**normal})
            with zipfile.ZipFile(io.BytesIO(raws[key])) as zipped:
                rows=list(csv.reader(io.StringIO(zipped.read(normal['member']).decode('utf-8'))))
            if rows and rows[0]==archive.HEADER:rows=rows[1:]
            values[key]=rows
            states[key].update(status='complete',body_sha256=sha(raws[key]),body_bytes=len(raws[key]),
                               member_sha256=normal['member_sha256'],coverage=normal['coverage'])
        except MemoryError:raise
        except Exception as exc:states[key]['reason']=type(exc).__name__+': '+str(exc)
    return values,states


def mark_sources(capture,admission,receipt_bytes):
    spec=mark.default_spec()
    if canonical(capture['request_spec'])!=canonical(spec):raise ValueError('mark specification differs')
    ids=[x['id'] for x in spec['requests']]
    refs,parents=index(capture['receipts'],ids),index(admission['cells'],ids)
    closed=utc(capture['capture_closed_utc']);values,states={},{}
    for req in spec['requests']:
        key=req['id'];state={'id':key,'status':'unavailable'}
        try:
            rb=receipt_bytes[key];receipt=strict(rb);ref=refs[key]
            if sha(rb)!=ref['receipt_sha256'] or ref['path']!=key+'-receipt.json':raise ValueError('mark receipt file reference differs')
            raw,before,after=raw_receipt(receipt,req,256*1024,req['endpoint']+'?'+urlencode(req['parameters']))
            if closed<after:raise ValueError('mark capture closed before receipt')
            for field in ('body_sha256','body_bytes','request_utc','retrieval_utc'):
                if canonical(ref[field])!=canonical(receipt[field]):raise ValueError('mark reference metadata differs')
            normal=mark.admit(receipt);match(parents[key],{'id':key,**normal});values[key]=strict(raw)
            state.update(status='complete',body_sha256=sha(raw),body_bytes=len(raw),complete_slots=56)
        except MemoryError:raise
        except Exception as exc:state['reason']=type(exc).__name__+': '+str(exc)
        states[key]=state
    return values,states


def clipped(rows):
    selected=[r for r in rows if START<=int(r[0])<END]
    return selected,{'source_rows':len(rows),'retained_rows':len(selected),
        'before':sum(int(r[0])<START for r in rows),'at_or_after_end':sum(int(r[0])>=END for r in rows)}


def readmit(inputs):
    groups=[('carry',carry_sources,[x['id'] for x in carry.frozen_request_spec()['requests']]),
            ('archive',archive_sources,[x['id'] for x in archive.frozen_request_spec()['requests']]),
            ('mark',mark_sources,[x['id'] for x in mark.default_spec()['requests']])]
    all_values,states={},{}
    for name,fn,ids in groups:
        try:
            args=[strict(inputs[name+'_capture']),strict(inputs[name+'_admission'])]
            if name=='mark':args.append({key:inputs[key.replace('-','_')+'_receipt'] for key in ids})
            values,checks=fn(*args)
        except MemoryError:raise
        except Exception as exc:
            values={};checks={key:{'id':key,'status':'unavailable','reason':type(exc).__name__+': '+str(exc)} for key in ids}
        all_values.update(values);states.update(checks)
    data,errors,clipping={'benchmarks':{}},{},{}
    for asset in ('BTC','ETH'):
        key=asset.lower()+'-spot'
        if states[key]['status']=='complete':data['benchmarks'][asset]=clipped(all_values[key])[0]
    for asset in ('BTC','ETH'):
        pre=asset.lower();needed=[pre+'-'+x for x in ('spot','perp','mark','funding','dated-mark')]+[f'{pre}-{month}-zip' for month in ('2026-05','2026-06')]
        missing=[key for key in needed if states[key]['status']!='complete']
        if missing:errors[asset]='Required source unavailable: '+', '.join(missing);continue
        try:
            piece={};counts={}
            for name in ('spot','perp','mark'):
                piece[name],counts[name]=clipped(all_values[pre+'-'+name])
            piece['dated'],counts['dated']=clipped(sum((all_values[f'{pre}-{month}-zip'] for month in ('2026-05','2026-06')),[]))
            # Full Q2 calendar was independently readmitted above. Slice canonical
            # May1 00:00..June25 16:00 slots, not raw clock comparisons at June26.
            full=all_values[pre+'-funding'];piece['funding']=full[90:258]
            counts['funding']={'source_events':len(full),'canonical_before':90,'canonical_retained':168,'canonical_after':15,
                'entry_slot_excluded':1,'expected_credited':167,'ownership':'canonical May1..June25 slots; first slot excluded; actual included clocks must be after start+5s and before end'}
            piece['dated_mark']=all_values[pre+'-dated-mark']
            data[asset]=piece;clipping[asset]=counts
        except MemoryError:raise
        except Exception as exc:errors[asset]=type(exc).__name__+': '+str(exc)
    return data,{'source_states':states,'source_count':20,'errors':errors,'clipping':clipping,
                 'source_files':{name:{'sha256':sha(raw),'bytes':len(raw)} for name,raw in inputs.items()}}

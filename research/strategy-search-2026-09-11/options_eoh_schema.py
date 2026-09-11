"""Two-object lexical schema discovery; no interpretation of option prices."""
from __future__ import annotations
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import zipfile
import zlib

import carry_capture as transport_module
from options_metadata import strict_json, lifecycle_bytes
from tradingagents.research import ResearchRun

SPEC_SHA = 'c63b965bf8f160996058d6dbc15cbdb88736d10525a3e135067266f73ebc2b30'
REGISTRATION = 'research/strategy-search-2026-09-11/gates-options-eoh.json'
EXPERIMENT = 'options-eoh-schema-20260911'


def checksum_record(raw, filename):
    match = re.fullmatch(r'([a-fA-F0-9]{64})  '+re.escape(filename)+r'\n?', raw.decode('utf-8'))
    if not match:
        raise ValueError('exact SHA256 and frozen basename checksum record required')
    return match.group(1).lower()


def lexical_schema(raw, digest, spec):
    import csv
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('paired ZIP checksum mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        if len(entries) != 1 or entries[0].filename != spec['expected_member'] or entries[0].is_dir():
            raise ValueError('exact single CSV member required')
        member = entries[0]
        if member.flag_bits & 1 or member.compress_size <= 0 or member.file_size > spec['max_uncompressed_bytes'] or member.file_size / member.compress_size > spec['max_compression_ratio']:
            raise ValueError('ZIP encryption/expansion/compression-ratio bound')
        with archive.open(member) as stream:
            content = stream.read(spec['max_uncompressed_bytes']+1)
        if len(content) != member.file_size or len(content) > spec['max_uncompressed_bytes']:
            raise ValueError('uncompressed member length mismatch or bound')
    decoded = content.decode('utf-8')
    prior_limit = csv.field_size_limit(spec['max_csv_field_characters'])
    try:
        reader = csv.reader(io.StringIO(decoded, newline=''), delimiter=',', quotechar='"', strict=True)
        first = next(reader, None)
        if first is None:
            raise ValueError('empty CSV object')
        header_part = {'candidate_header': first, 'column_index_base': 0}
        if len(lifecycle_bytes(header_part)) > spec['max_schema_output_bytes']:
            raise ValueError('candidate header exceeds actual encoded schema bound')
        minimum_column_bytes=len(json.dumps({'column_index':0,'empty_string_count':0,'absent_column_count':0},separators=(',',':')))
        if len(first)*minimum_column_bytes > spec['max_schema_output_bytes']:
            raise ValueError('column profile necessarily exceeds encoded schema bound')
        widths = Counter({len(first):1}); after_widths = Counter(); empty = Counter()
        ragged, total, maximum_width, ragged_lower_bytes = [], 1, len(first), 0
        for record in reader:
            total += 1
            width = len(record)
            if width*minimum_column_bytes > spec['max_schema_output_bytes']:
                raise ValueError('column profile necessarily exceeds encoded schema bound')
            widths[width] += 1; after_widths[width] += 1
            maximum_width = max(maximum_width, width)
            if width != len(first):
                ragged_lower_bytes += len(str(total))+1
                if ragged_lower_bytes > spec['max_schema_output_bytes']:
                    raise ValueError('ragged index list necessarily exceeds encoded schema bound')
                ragged.append(total)
            for index, value in enumerate(record):
                if value == '':
                    empty[index] += 1
            if total % 1024 == 0 and len(lifecycle_bytes({'ragged_record_indices':ragged,'empty_string_counts':dict(empty)})) > spec['max_schema_output_bytes']:
                raise ValueError('intermediate literal schema exceeds actual encoded bound')
        result = {**header_part, 'status':'complete', 'header_semantics':'unverified candidate; may be data, never automatically mapped',
                  'member':spec['expected_member'], 'member_sha256':hashlib.sha256(content).hexdigest(),
                  'uncompressed_bytes':len(content), 'utf8_bom_present':content.startswith(b'\xef\xbb\xbf'),
                  'total_records_including_first':total, 'records_after_first':total-1,
                  'record_width_frequencies':dict(sorted(widths.items())), 'record_index_base':1,
                  'ragged_record_count':len(ragged), 'ragged_record_indices':ragged,
                  'blank_record_count_including_first':widths[0],
                  'column_missingness_after_first':[{'column_index':index, 'empty_string_count':empty[index],
                    'absent_column_count':sum(n for width,n in after_widths.items() if width <= index)} for index in range(maximum_width)],
                  'field_semantics':'unavailable; no bid/ask/size/time mapping, numerical interpretation, frequency or chain completeness'}
        if len(lifecycle_bytes(result)) > spec['max_schema_output_bytes']:
            raise ValueError('actual encoded schema output bound exceeded')
        return result
    finally:
        csv.field_size_limit(prior_limit)


def capture(spec, transport=transport_module.public_get, persist_receipt=None):
    canonical=json.dumps(spec,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if hashlib.sha256(canonical).hexdigest()!=SPEC_SHA:
        raise ValueError('request specification differs from frozen definition')
    receipts, bodies, denied = [], [], set()
    deadline=time.monotonic()+90
    for request in spec['requests']:
        begin=time.monotonic(); stamp=datetime.now(timezone.utc).isoformat(); host=urlsplit(request['url']).hostname
        reason='not attempted after same-host denial' if host in denied else 'not attempted: cooperative resource deadline' if begin+20>deadline else None
        response=transport(request['url']) if reason is None else {'body':b'','http_status':None,'headers':{},'body_complete':False,'error':reason}
        body=response['body']
        if not isinstance(body,bytes): raise ValueError('transport must preserve bytes')
        if len(body)>spec['max_response_bytes']:
            body=body[:spec['max_response_bytes']];response={**response,'body_complete':False,'error':'oversize response; retained exact prefix'}
        if response['http_status'] in transport_module.DENIALS:denied.add(host)
        receipt={**request,'request_utc':stamp,'retrieval_utc':datetime.now(timezone.utc).isoformat(),
                 'elapsed_seconds':time.monotonic()-begin,'attempted':reason is None,
                 'http_status':response['http_status'],'body_complete':response['body_complete'],'error':response['error'],
                 'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'body_base64':base64.b64encode(body).decode(),
                 'headers':{k:v for k,v in response['headers'].items() if k.lower() in ('date','content-type')}}
        receipts.append(receipt);bodies.append(body)
        if persist_receipt is not None:persist_receipt(request['id']+'-receipt.json',receipt)
    cells=[]
    for receipt in receipts:
        valid=receipt['http_status']==200 and receipt['body_complete'] and not receipt['error']
        cells.append({'id':receipt['id'],'status':'complete' if valid else 'unavailable',
                      **({} if valid else {'reason':receipt['error'] or 'incomplete HTTP response'})})
    digest=None
    if cells[1]['status']=='complete':
        try:digest=checksum_record(bodies[1],spec['requests'][0]['filename'])
        except (UnicodeError,ValueError) as exc:cells[1].update(status='unavailable',reason=str(exc))
    schema={'status':'unavailable','reason':'complete verified ZIP/checksum pair required'}
    integrity={'status':'unavailable','reason':'complete verified ZIP/checksum pair required'}
    if cells[0]['status']=='complete' and digest is not None:
        if hashlib.sha256(bodies[0]).hexdigest()==digest:
            integrity={'status':'complete','sha256':digest}
        else:integrity={'status':'unavailable','reason':'paired ZIP checksum mismatch'}
        try:schema=lexical_schema(bodies[0],digest,spec)
        except MemoryError:raise
        except Exception as exc:schema={'status':'unavailable','reason':type(exc).__name__+': '+str(exc)}
    if schema['status']!='complete':cells[0].update(status='unavailable',reason=schema['reason'])
    raw={'schema_version':1,'request_spec':spec,'requests':receipts,'total_body_bytes':sum(len(body) for body in bodies)}
    output={'cells':cells,'paired_integrity':integrity,'lexical_schema':schema,
            'checksum_cell_scope':'Syntax/source receipt only; paired integrity is reported separately',
            'scope':'Literal single-object discovery; no prices, clocks, executable quotes or financial meaning admitted'}
    size=sum(len(lifecycle_bytes(x)) for x in receipts)+len(lifecycle_bytes(raw))+len(lifecycle_bytes(output))
    if size>spec['max_output_bytes']:raise RuntimeError('total actual encoded output budget exceeded; prior receipts retained')
    return raw,output,cells


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=Path(__file__).resolve().parents[2],registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        raw,schema,cells=capture(strict_json(run.read_input('request_spec')),persist_receipt=run.write_json)
        run.write_json('eoh-capture.json',raw);run.write_json('eoh-schema.json',schema);run.finish(cells)

if __name__=='__main__':main()

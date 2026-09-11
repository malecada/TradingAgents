import base64
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
from unittest.mock import patch
import pytest

P=Path(__file__).resolve().parents[2]/'research/strategy-search-2026-09-11'
for name in ('carry_capture','options_metadata','options_eoh_schema'):
    spec=importlib.util.spec_from_file_location(name,P/(name+'.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
m=sys.modules['options_eoh_schema']
SPEC=json.loads((P/'options-eoh-request-spec.json').read_text())


def zipped(content=b'unknown,unknown,\n, ,x\nq\n\n',name=None,extra=False,compression=zipfile.ZIP_STORED):
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=compression) as z:
        z.writestr(name or SPEC['expected_member'],content)
        if extra:z.writestr('extra.csv','x')
    return out.getvalue()


def schema(raw,spec=SPEC):return m.lexical_schema(raw,hashlib.sha256(raw).hexdigest(),spec)


def response(body,status=200):return {'body':body,'http_status':status,'headers':{},'body_complete':True,'error':None}


def test_literal_duplicate_header_ragged_blank_and_empty_are_preserved():
    result=schema(zipped())
    assert result['candidate_header']==['unknown','unknown','']
    assert result['total_records_including_first']==4 and result['records_after_first']==3
    assert result['record_width_frequencies']=={0:1,1:1,3:2}
    assert result['ragged_record_indices']==[3,4]
    assert result['blank_record_count_including_first']==1
    assert result['column_missingness_after_first']==[
        {'column_index':0,'empty_string_count':1,'absent_column_count':1},
        {'column_index':1,'empty_string_count':0,'absent_column_count':2},
        {'column_index':2,'empty_string_count':0,'absent_column_count':2}]
    assert result['field_semantics'].startswith('unavailable')


@pytest.mark.parametrize('content',[b'',b'\xff',b'a,b\n"unterminated',b'a\n'+b'x'*(1048576+1)])
def test_empty_decode_csv_and_field_errors(content):
    with pytest.raises((ValueError,UnicodeError,csv.Error)):schema(zipped(content))


@pytest.mark.parametrize('name',['../outside.csv','/absolute.csv','wrong.csv'])
def test_wrong_or_path_members_rejected(name):
    with pytest.raises(ValueError):schema(zipped(name=name))


def test_extra_members_encryption_crc_and_deflate_fail():
    with pytest.raises(ValueError):schema(zipped(extra=True))
    raw=bytearray(zipped());offset=raw.index(b'PK\x01\x02');struct.pack_into('<H',raw,offset+8,1)
    with pytest.raises(ValueError):schema(bytes(raw))
    raw=bytearray(zipped());raw[30+len(SPEC['expected_member'])]^=1
    with pytest.raises(zipfile.BadZipFile):schema(bytes(raw))
    raw=bytearray(zipped(compression=zipfile.ZIP_DEFLATED));raw[30+len(SPEC['expected_member'])]=255
    with pytest.raises(Exception):schema(bytes(raw))


def test_expansion_and_summary_bounds_bom_and_checksum():
    with pytest.raises(ValueError):schema(zipped(b'x'*100),{**SPEC,'max_uncompressed_bytes':50})
    with pytest.raises(ValueError):schema(zipped(b'x'*10000,compression=zipfile.ZIP_DEFLATED),{**SPEC,'max_compression_ratio':2})
    with pytest.raises(ValueError):schema(zipped(),{**SPEC,'max_schema_output_bytes':10})
    result=schema(zipped(b'\xef\xbb\xbfname\nx\n'));assert result['utf8_bom_present'] and result['candidate_header']==['\ufeffname']
    with pytest.raises(ValueError):m.checksum_record(b'0'*64+b' wrong.zip\n',SPEC['requests'][0]['filename'])
    with pytest.raises(ValueError):m.lexical_schema(zipped(),'0'*64,SPEC)


def test_both_receipts_precede_parsing_and_bad_schema_keeps_denominator():
    raw=zipped(b'a\n"bad');digest=hashlib.sha256(raw).hexdigest();checksum=(digest+'  '+SPEC['requests'][0]['filename']+'\n').encode()
    saved=[]
    original=m.lexical_schema
    def checked(*args):
        assert len(saved)==2
        return original(*args)
    with patch.object(m,'lexical_schema',checked):
        capture,result,cells=m.capture(SPEC,transport=lambda url:response(checksum if url.endswith('CHECKSUM') else raw),persist_receipt=lambda name,value:saved.append((name,value)))
    assert len(saved)==len(cells)==2
    assert cells[0]['status']=='unavailable' and cells[1]['status']=='complete'
    assert result['paired_integrity']['status']=='complete'
    assert base64.b64decode(saved[0][1]['body_base64'])==raw


def test_denial_suppresses_second_request_and_keeps_both_receipts():
    calls=[];saved=[]
    def transport(url):calls.append(url);return response(b'denied',403)
    _,_,cells=m.capture(SPEC,transport=transport,persist_receipt=lambda n,r:saved.append(r))
    assert len(calls)==1 and len(cells)==len(saved)==2
    assert all(x['status']=='unavailable' for x in cells)
    assert saved[1]['attempted'] is False


def test_success_and_spec_mismatch():
    raw=zipped();checksum=(hashlib.sha256(raw).hexdigest()+'  '+SPEC['requests'][0]['filename']+'\n').encode()
    _,result,cells=m.capture(SPEC,transport=lambda url:response(checksum if url.endswith('CHECKSUM') else raw))
    assert all(x['status']=='complete' for x in cells)
    assert result['lexical_schema']['total_records_including_first']==4
    with pytest.raises(ValueError):m.capture({**SPEC,'max_requests':3})


def test_wide_row_rejected_before_column_counter_amplification():
    raw=zipped(b'header\n'+b','*50000+b'\n')
    checksum=(hashlib.sha256(raw).hexdigest()+'  '+SPEC['requests'][0]['filename']+'\n').encode()
    saved=[]
    _,result,cells=m.capture(SPEC,transport=lambda url:response(checksum if url.endswith('CHECKSUM') else raw),persist_receipt=lambda n,r:saved.append(r))
    assert len(saved)==len(cells)==2
    assert result['paired_integrity']['status']=='complete'
    assert cells[0]['status']=='unavailable'
    assert 'column profile necessarily exceeds' in cells[0]['reason']

"""Independent adversarial metadata-only fixtures; no real corpus path opened."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time

import pyarrow as pa
import pyarrow.parquet as pq

HERE=Path(__file__).parent
source=HERE.parent/'news_provenance.py'
loader=importlib.util.spec_from_file_location('independent_news_metadata_synthetic',source)
engine=importlib.util.module_from_spec(loader);loader.loader.exec_module(engine)


def verify():
    cases=[]
    with tempfile.TemporaryDirectory(prefix='independent-news-fixtures-') as temporary:
        root=Path(temporary)
        # Nonempty row groups plant article-like data in statistics and arbitrary
        # schema metadata. Only safe type categories/name digests may be emitted.
        schema=pa.schema([pa.field('id',pa.int64()),pa.field('retrieved_at',pa.timestamp('ns')),
                          pa.field('headline',pa.string()),pa.field('UNKNOWN-PRIVATE-FIELD',pa.string())],
                         metadata={b'PRIVATE-METADATA-KEY':b'PRIVATE-METADATA-VALUE'})
        table=pa.Table.from_arrays([pa.array([1,2]),pa.array([1,2],type=pa.timestamp('ns')),
                                   pa.array(['PRIVATE-ARTICLE-MIN','PRIVATE-ARTICLE-MAX']),pa.array(['secret-a','secret-b'])],schema=schema)
        parquet=root/'sample.parquet';pq.write_table(table,parquet,write_statistics=True)
        raw=parquet.read_bytes();length=int.from_bytes(raw[-8:-4],'little');offset=len(raw)-8-length
        assert b'PRIVATE-ARTICLE' in raw[offset:]
        calls=[];original=engine.os.pread
        def watched(fd,n,at):calls.append((at,n));return original(fd,n,at)
        engine.os.pread=watched
        try:result=engine.inspect_file(str(parquet),'parquet',engine.default_spec())
        finally:engine.os.pread=original
        assert result['status']=='present' and calls==[(0,4),(len(raw)-8,8),(offset,length)]
        encoded=engine.encoded(result)
        assert all(secret not in encoded for secret in (b'PRIVATE',b'secret-a',b'secret-b'))
        assert result['schema']['unknown_name_sha256']==[hashlib.sha256(b'UNKNOWN-PRIVATE-FIELD').hexdigest()]
        for region in result['regions']:
            a,n=region['offset'],region['length'];assert region['sha256']==hashlib.sha256(raw[a:a+n]).hexdigest()
        cases.append({'id':'nonempty-parquet-statistics-kv-privacy','status':'PASS','read_regions':calls})
        header=b' ID ,retrieved_at,HEADLINE,unknown-private\r\n';csv=root/'header.csv';csv.write_bytes(header+b'PRIVATE-RECORD-ROW\n')
        reads=[];original=engine.os.read
        def watchedread(fd,n):reads.append(n);return original(fd,n)
        engine.os.read=watchedread
        try:result=engine.inspect_file(str(csv),'csv-header',engine.default_spec())
        finally:engine.os.read=original
        assert result['status']=='present' and reads==[1]*(len(header)-1)
        assert result['regions'][0]['length']==len(header)-1
        assert b'PRIVATE' not in engine.encoded(result) and b'unknown-private' not in engine.encoded(result)
        cases.append({'id':'CRLF-first-physical-line-no-read-ahead','status':'PASS','read_bytes':len(reads)})
        for label,body in (('multiline',b'id,"unfinished\nPRIVATE-LINE\n'),('invalid-UTF8',b'id,\xff\n'),('headerless',b'PRIVATE-ARTICLE,not-a-field\n')):
            csv.write_bytes(body);result=engine.inspect_file(str(csv),'csv-header',engine.default_spec())
            assert result['status']=='unavailable' and 'schema' not in result and b'PRIVATE' not in engine.encoded(result)
            cases.append({'id':label,'status':'PASS'})
        csv.write_bytes(b'id,date\nPRIVATE-RECORD\n');previous=csv.stat();original=engine.os.read;mutated=False
        def in_place(fd,n):
            nonlocal mutated
            value=original(fd,n)
            if not mutated:
                mutated=True;time.sleep(.03)
                with csv.open('r+b',buffering=0) as writer:writer.write(b'id,evil\n')
                os.utime(csv,ns=(previous.st_atime_ns,previous.st_mtime_ns))
            return value
        engine.os.read=in_place
        try:result=engine.inspect_file(str(csv),'csv-header',engine.default_spec())
        finally:engine.os.read=original
        assert result['status']=='unavailable' and result['reason_code']=='concurrent_file_change' and 'schema' not in result
        assert result['identity_before']['ctime_ns']!=result['identity_after']['ctime_ns']
        cases.append({'id':'in-place-rewrite-preserved-size-mtime','status':'PASS'})
        csv.write_bytes(b'id,date\n');original=engine.os.read;swapped=False
        def swap_path(fd,n):
            nonlocal swapped
            value=original(fd,n)
            if not swapped:
                swapped=True;replacement=root/'replacement.csv';replacement.write_bytes(b'id,date\n');os.replace(replacement,csv)
            return value
        engine.os.read=swap_path
        try:result=engine.inspect_file(str(csv),'csv-header',engine.default_spec())
        finally:engine.os.read=original
        assert result['status']=='unavailable' and result['reason_code']=='concurrent_file_change' and 'schema' not in result
        cases.append({'id':'same-length-path-replacement','status':'PASS'})
        real=root/'real';real.mkdir();(real/'header.csv').write_bytes(b'id,date\n')
        link=root/'link';link.symlink_to(real)
        result=engine.inspect_file(str(link/'header.csv'),'csv-header',engine.default_spec())
        assert result['status']=='unavailable' and result['regions']==[]
        cases.append({'id':'intermediate-symlink-no-data-read','status':'PASS'})
    return {'status':'PASS','inspector_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'real_corpus_paths_opened':0,
            'network_requests':0,'cases':cases,'scope':'Independent invented nonempty Parquet/header/path-change tests; no production inspection or financial calculation.'}


if __name__=='__main__':
    result=verify()
    with (HERE/'news-privacy-synthetic-review.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result))

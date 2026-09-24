"""Hash-verified streaming ETH Parquet adapter; never imports old launchers."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import math
import json
from contextlib import nullcontext
import re
import pyarrow as pa
import pyarrow.parquet as pq
from .contracts import Transaction
from .provenance import file_hash, require_hash, utc


COLUMNS = ('hash','block_timestamp','from_address','to_address','value','receipt_status')


def address(value, nullable=False):
    if nullable and value in (None, 'None'):
        return None
    if not isinstance(value,str) or re.fullmatch(r'0x[0-9a-fA-F]{40}',value) is None:
        raise ValueError('malformed ETH address')
    return value.lower()


def decode_eth(manifest: dict, schema: dict):
    start,end=utc(manifest['start_utc']),utc(manifest['end_utc'])
    if start>=end:raise ValueError('source interval')
    if not set(COLUMNS)<=set(schema):raise ValueError('required ETH schema fields missing')
    for member in manifest['members']:
        require_hash(member['sha256'])
        path=Path(member['path'])
        if file_hash(path)!=member['sha256']:raise ValueError('source hash mismatch')
        if member['format']=='parquet':
            context=nullcontext(path)
        elif member['format']=='projected_zstd':
            context=projected_parquet(json.loads(path.read_bytes()),manifest['scratch'])
        else:
            raise ValueError('unavailable source encoding')
        with context as source:
            yield from _decode_member(source,member,schema,start,end)


def _decode_member(source,member,schema,start,end):
        parquet=pq.ParquetFile(source,metadata=getattr(source,'parquet_metadata',None),pre_buffer=False)
        actual={f.name:str(f.type) for f in parquet.schema_arrow}
        if any(actual.get(k)!=v for k,v in schema.items()):raise ValueError('source schema mismatch')
        for batch in parquet.iter_batches(batch_size=8192,columns=list(COLUMNS),use_threads=False):
            columns=batch.to_pydict()
            for row in zip(*(columns[k] for k in COLUMNS),strict=True):
                identity,ts,sender,recipient,value,status=row
                if not isinstance(identity,str) or re.fullmatch('0x[0-9a-fA-F]{64}',identity) is None:
                    raise ValueError('invalid transaction hash')
                if ts.tzinfo is None:ts=ts.replace(tzinfo=timezone.utc) # declared archive ns UTC
                if not start<=ts<end:raise ValueError('source timestamp outside manifest')
                if not math.isfinite(value) or value<0 or status not in (0,1):raise ValueError('invalid value/status')
                yield Transaction('ETH',identity.lower(),ts.isoformat().replace('+00:00','Z'),
                                  address(sender),address(recipient,True),value/1e18,status,
                                  member['sha256'],'approximate_ETH')


from contextlib import contextmanager
import io
import tempfile
import zstandard
from .provenance import digest


class AcquiredReader(io.RawIOBase):
    """Random-access reader rejects holes rather than returning sparse zero bytes."""
    def __init__(self,file,intervals,size):
        super().__init__();self.file=file;self.intervals=sorted(intervals);self.size=size
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.file.tell()
    def seek(self,offset,whence=0):return self.file.seek(offset,whence)
    def read(self,size=-1):
        start=self.tell();end=self.size if size<0 else min(self.size,start+size)
        if start<0 or start>self.size:raise ValueError('invalid read offset')
        cursor=start
        for a,b in self.intervals:
            if b<=cursor:continue
            if a>cursor:break
            cursor=min(end,b)
            if cursor==end:break
        if cursor!=end:raise ValueError('unacquired parquet byte range')
        return self.file.read(end-start)
    def readinto(self,buffer):
        data=self.read(len(buffer));buffer[:len(data)]=data;return len(data)


@contextmanager
def projected_parquet(manifest,scratch):
    """Read retained, independently hashed compressed ranges without refetching.

    Span offsets are half-open. Legacy inclusive ends must be explicitly mapped
    by the new source-admission manifest. Source hashes include this mapping.
    """
    size=manifest['size']
    if type(size) is not int or not 12<=size<=8*1024**3:raise ValueError('logical parquet size limit')
    intervals=[]
    with tempfile.TemporaryFile(dir=scratch) as file:
        file.truncate(size)
        for span in sorted(manifest['spans'],key=lambda s:s['start']):
            a,b=span['start'],span['end']
            if not 0<=a<b<=size or (intervals and a<intervals[-1][1]):raise ValueError('invalid/overlapping ranges')
            if not 0<span['raw_bytes']<=64*1024**2 or span['raw_bytes']!=b-a:raise ValueError('raw range limit')
            if not 0<span['stored_bytes']<=65*1024**2:raise ValueError('stored range limit')
            with Path(span['path']).open('rb') as stream:stored=stream.read(span['stored_bytes']+1)
            if len(stored)!=span['stored_bytes'] or digest(stored)!=span['stored_sha256']:raise ValueError('stored range hash')
            if zstandard.frame_content_size(stored)!=b-a:raise ValueError('range decompression length')
            raw=zstandard.ZstdDecompressor().decompress(stored,max_output_size=b-a,allow_extra_data=False)
            if digest(raw)!=span['raw_sha256']:raise ValueError('raw range hash')
            file.seek(a);file.write(raw);intervals.append((a,b))
        file.flush();file.seek(0)
        reader=AcquiredReader(file,intervals,size)
        reader.seek(size-8);trailer=reader.read(8)
        if trailer[4:]!=b'PAR1':raise ValueError('invalid parquet trailer')
        length=int.from_bytes(trailer[:4],'little')
        if not 0<length<=4*1024**2:raise ValueError('footer limit')
        reader.seek(size-length-8)
        footer=reader.read(length+8)
        reader.parquet_metadata=pq.read_metadata(io.BytesIO(b'PAR1'+footer))
        reader.seek(0)
        yield reader

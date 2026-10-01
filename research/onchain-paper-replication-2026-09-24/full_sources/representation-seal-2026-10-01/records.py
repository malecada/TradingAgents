"""Exclusive bounded metadata write with prebound intended content identity."""
import os
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,sync_directory

def write_metadata(metadata,directory,name,value,cap):
    raw=canonical_bytes(value)
    if type(cap) is not int or cap<=0 or len(raw)>cap:raise ValueError('record metadata allowance exceeded')
    expected=digest(raw);path=directory/name
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    sync_directory(directory)
    metadata.read(path,expected,cap)
    return {'path':str(path),'sha256':expected}

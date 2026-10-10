"""Finite engineering selection; these references do not instantiate Admission/Owner.

Metadata import is stdlib-only. Backend import, runtime comparison and sealed
loading happen only for a selected immutable pair session. No compilation API.
"""
import hashlib,json,os,stat
from pathlib import Path

HELPER_SHA256 = '80b045d499136ba722402e9ae596411e109fcc00e70b445f5f7c3f2e82b3a422'
LIBRARY_SHA256 = '9fd95c85ae9c5572adad1f0c8824d6f52f09762cc06fcb7ad03b17a6cc03e3f2'
SOURCE_SHA256 = '8c7b2f34ff0e3da95ae34f77134b2b47560e3e0307945371a2e10c461ac962e8'
FORMAT = 'compiled-small-lse-prototype04-session-v1'
FIELDS = {'format','library_path','library_sha256','source_path','source_sha256',
          'runtime_path','runtime_sha256','runtime_bytes'}

def require(ok,message):
    if not ok:raise ValueError(message)

def digest(value):
    return type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)

def freeze(value):
    if value is None or value is False:return None
    require(type(value) is dict and set(value)==FIELDS,'exact normalization policy fields required')
    require(all(type(value[k]) is str for k in FIELDS-{'runtime_bytes'}),'plain policy strings required')
    require(value['format']==FORMAT and value['library_sha256']==LIBRARY_SHA256 and value['source_sha256']==SOURCE_SHA256,'unsupported compiled normalization policy')
    require(digest(value['runtime_sha256']) and type(value['runtime_bytes']) is int and 0<value['runtime_bytes']<=4096,'finite exact runtime reference required')
    for key in ('library_path','source_path','runtime_path'):
        p=value[key]
        require(0<len(p)<=4096 and '\x00' not in p and p.startswith('/') and str(Path(p))==p and '..' not in Path(p).parts,'canonical absolute reference required')
    return tuple((k,value[k]) for k in sorted(FIELDS))

def attach(owner,value):
    owner._compiled_normalization_policy=freeze(value)
    owner._compiled_normalization_policy_pin=owner._compiled_normalization_policy

def current(owner):
    require(owner._compiled_normalization_policy is owner._compiled_normalization_policy_pin,'compiled normalization selection changed')

def options(owner):
    current(owner)
    return {'compiled_normalization_policy_value':dict(owner._compiled_normalization_policy)} if owner._compiled_normalization_policy is not None else {}

def join(owner,child):
    current(owner);current(child)
    require(owner._compiled_normalization_policy==child._compiled_normalization_policy,'compiled normalization chain changed')

def read_reference(path,expected,limit,exact_size=None):
    """Bounded regular-file body check; no authority claim for its parent path."""
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'bounded regular reference required')
        if exact_size is not None:require(before.st_size==exact_size,'reference size differs')
        chunks=[];remaining=before.st_size+1
        while remaining:
            block=os.read(fd,remaining)
            if not block:break
            chunks.append(block);remaining-=len(block)
        body=b''.join(chunks);after=os.fstat(fd)
        fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
        require(tuple(getattr(before,k) for k in fields)==tuple(getattr(after,k) for k in fields)
                and len(body)==before.st_size and hashlib.sha256(body).hexdigest()==expected,'reference body differs')
        return body
    finally:os.close(fd)

def runtime_metadata(body):
    value=json.loads(body)
    fields={'format','python','numpy','scipy','platform','machine','byteorder','executable','runtime_inventory_sha256'}
    require(type(value) is dict and set(value)==fields and all(type(v) is str for v in value.values()),'exact typed runtime metadata required')
    require(value['format']=='compiled-small-lse-runtime-reference-v1'
            and value['python']=='3.13.13' and value['numpy']=='2.3.0' and value['scipy']=='1.17.1'
            and value['platform']=='linux' and value['machine']=='x86_64' and value['byteorder']=='little'
            and value['executable'].startswith('/') and len(value['executable'])<=4096
            and digest(value['runtime_inventory_sha256']),'unsupported normalization runtime metadata')
    return value

def open_backend(owner):
    current(owner)
    if owner._compiled_normalization_policy is None:return None
    p=dict(owner._compiled_normalization_policy)
    read_reference(p['source_path'],SOURCE_SHA256,65536)
    expected=runtime_metadata(read_reference(p['runtime_path'],p['runtime_sha256'],4096,p['runtime_bytes']))
    import sys,platform
    import numpy,scipy
    actual=dict(python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,platform=sys.platform,
                machine=platform.machine(),byteorder=sys.byteorder,executable=sys.executable)
    require(all(expected[k]==v for k,v in actual.items()),'selected runtime differs')
    helper_path=Path(__file__).with_name('compiled_small_lse.py')
    read_reference(helper_path,HELPER_SHA256,65536)
    from . import compiled_small_lse
    require(Path(compiled_small_lse.__file__).resolve()==helper_path.resolve(),'selected helper path differs')
    # Original helper authenticates and seals this exact library body before dlopen.
    # Unsupported loader conditions return its original SciPy fallback; fatal and
    # ambiguous-cleanup errors propagate. No generated authority or build occurs.
    return compiled_small_lse.open_backend(p['library_path'],p['library_sha256'])

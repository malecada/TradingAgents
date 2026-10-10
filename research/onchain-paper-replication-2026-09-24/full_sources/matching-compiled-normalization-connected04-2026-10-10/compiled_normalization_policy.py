"""Finite engineering selection; these references do not instantiate Admission/Owner.

Metadata import is stdlib-only. Backend import, runtime comparison and sealed
loading happen only for a selected immutable pair session. No compilation API.
"""
import hashlib,json,os,stat
from pathlib import Path

HELPER_SHA256 = '7f98ca93c5100e475c1a6de0280e4ce546c0adc26c3865820068b868014c496e'
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

def read_reference(path,expected,limit,exact_size=None,*,owned=False):
    """Bounded regular-file body check; no authority claim for its parent path."""
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        if owned:require(before.st_uid==os.getuid(),"library reference owner differs")
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

def _backend_references(owner):
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
    return p,compiled_small_lse

def open_backend(owner):
    references=_backend_references(owner)
    if references is None:return None
    p,helper=references
    return helper.open_backend(p['library_path'],p['library_sha256'])

class BackendOwner:
    """One lazy load attempt, one sequential lease, one terminal cleanup.

    All authority remains outside this engineering object. Closed or poisoned
    owners never retry loading or ambiguous cleanup. No process-global cache.
    """
    def __init__(self, value):
        from types import SimpleNamespace
        import threading
        attach(self,value)
        require(self._compiled_normalization_policy is not None,'selected owner policy required')
        thread=threading.get_ident()
        opened=False;closed=False;active=None;backend=None;backend_pins=()
        owned_close=None;close_attempted=False;close_error=None;pins=()
        def close():
            nonlocal closed,active,close_attempted,close_error
            closed=True;active=None
            if close_error is not None:raise close_error
            if close_attempted:return
            close_attempted=True
            if owned_close is not None:
                try:owned_close()
                except BaseException as error:
                    close_error=error;raise
        def check():
            require(threading.get_ident()==thread,'normalization owner thread differs')
            require(not closed,'normalization owner closed')
            current(self)
            for name,function,code in pins:
                require(getattr(self,name) is function and function.__code__ is code,'normalization owner method changed')
            if backend is not None:
                for name,function,code in backend_pins:
                    require(getattr(backend,name) is function and function.__code__ is code,'owned normalization function changed')
                require(backend.current(),'owned normalization seals/function state differs')
        def borrow(client):
            nonlocal opened,active,backend,backend_pins,owned_close
            token=None;released=False;lease=None;lease_pins=()
            def lease_check():
                check();join(self,client)
                require(not released and active is token,'normalization borrow expired or redirected')
                for name,function,code in lease_pins:
                    require(getattr(lease,name) is function and function.__code__ is code,'normalization borrow method changed')
            def release():
                nonlocal released,active
                if released:return
                released=True
                if active is token:active=None
                else:require(closed,'normalization borrow token changed')
            def lse(block,*,axis,keepdims,fallback):
                lease_check()
                return backend.lse(block,axis=axis,keepdims=keepdims,fallback=fallback)
            try:
                check();join(self,client)
                require(active is None,'normalization owner already borrowed')
                token=object();active=token
                # Lease allocation precedes backend allocation; publication is
                # still guarded until the final return below.
                lease=SimpleNamespace(lse=lse,close=release,current=lease_check)
                lease_pins=tuple((name,getattr(lease,name),getattr(lease,name).__code__) for name in ('lse','close','current'))
                p,helper=_backend_references(self)
                if not opened:
                    opened=True
                    backend=helper.open_backend(p['library_path'],p['library_sha256'])
                    owned_close=backend.close
                    backend_pins=tuple((name,getattr(backend,name),getattr(backend,name).__code__) for name in ('lse','close','current','loaded'))
                # Each loaded lease freshly reads the original library reference.
                # A clean disabled initial loader keeps its original fallback;
                # this owner never retries loading, even if that path recovers.
                if backend.loaded():read_reference(p['library_path'],p['library_sha256'],65536,owned=True)
                lease_check()
                return lease
            except BaseException as primary:
                # Failure before a lease reaches the session is owner-owned.
                # Retain originally acquired cleanup, including pin failures.
                try:
                    if backend is not None and owned_close is None:owned_close=backend.close
                    close()
                except BaseException as cleanup:
                    try:BaseException.add_note(primary,'normalization owner cleanup failed: '+repr(cleanup))
                    except BaseException:pass
                raise
        self.borrow=borrow;self.current=check;self.close=close
        pins=tuple((name,getattr(self,name),getattr(self,name).__code__) for name in ('borrow','current','close'))

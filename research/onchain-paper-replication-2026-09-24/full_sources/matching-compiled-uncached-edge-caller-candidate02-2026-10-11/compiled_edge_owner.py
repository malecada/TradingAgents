"""Finite engineering native owner; never an Admission, Owner or runtime grant.
No import-time scientific imports, native load, source reads or compilation.
"""
import hashlib,json,os,stat,sys,types
from pathlib import Path
from . import compiled_normalization_policy as references

SOURCE='6b0391049ddff37892c74e074d1d7506c0a3527ae44aba013c06cb66295695b8'
LIBRARY='a97c0b503ae749216636db96b0243af835da4c7c016fbb05d31eeda2e4623e98'
ADAPTER='55f41c5e46ad893eacf9ac229b3e04bc444ec0626ce946cca98a32270ebb6eb2'
FORMAT='cpython-uncached-edge-owner-v1'
FIELDS={'format','source_path','source_sha256','adapter_path','adapter_sha256','library_path','library_sha256','runtime_path','runtime_sha256','runtime_bytes','abi_path','abi_sha256','abi_bytes'}

def require(value,message):
    if not value:raise ValueError(message)

def freeze(value):
    if value is None:return None
    require(type(value) is dict and set(value)==FIELDS,'exact edge policy fields required')
    require(all(type(value[k]) is str for k in FIELDS-{'runtime_bytes','abi_bytes'}),'plain edge policy required')
    require(value['format']==FORMAT and value['source_sha256']==SOURCE and value['adapter_sha256']==ADAPTER and value['library_sha256']==LIBRARY,'unsupported edge bodies')
    for prefix in ('source','adapter','library','runtime','abi'):
        path=value[prefix+'_path'];digest=value[prefix+'_sha256']
        require(path.startswith('/') and len(path)<=4096 and '\0' not in path and str(Path(path))==path and '..' not in Path(path).parts,'canonical absolute role path required')
        require(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'exact role hash required')
    for k in ('runtime_bytes','abi_bytes'):require(type(value[k]) is int and 0<value[k]<=4096,'bounded metadata role required')
    return tuple(sorted(value.items()))


def attach(owner,value):
    owner._compiled_edge_policy=freeze(value)
    owner._compiled_edge_policy_pin=owner._compiled_edge_policy

def current_policy(owner):
    require(owner._compiled_edge_policy is owner._compiled_edge_policy_pin,'edge policy replaced')

def options(owner):
    current_policy(owner)
    return {'compiled_edge_policy_value':dict(owner._compiled_edge_policy)} if owner._compiled_edge_policy is not None else {}

def join(owner,child):
    current_policy(owner);current_policy(child)
    require(owner._compiled_edge_policy==child._compiled_edge_policy,'edge policy chain differs')

def abi_metadata(body):
    value=json.loads(body)
    require(type(value) is dict and value=={'format':'cpython-edge-abi-v1','implementation':'cpython','cache_tag':'cpython-313','soabi':'cpython-313-x86_64-linux-gnu','ext_suffix':'.cpython-313-x86_64-linux-gnu.so','pointer_bits':64},'unsupported exact CPython ABI')
    return value

def _note(primary,error):
    try:BaseException.add_note(primary,'edge cleanup failed; no retry: '+repr(error))
    except BaseException:pass

def read_reference(path,expected,limit,exact_size=None,*,owned=False):
    """Original bounded body/signature algorithm; preserve primary on close failure."""
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    primary=None;close=os.close
    try:
        before=os.fstat(fd)
        require(not owned or before.st_uid==os.getuid(),'library owner differs')
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=limit,'bounded regular role required')
        require(exact_size is None or before.st_size==exact_size,'role extent differs')
        parts=[];remaining=before.st_size+1
        while remaining:
            block=os.read(fd,remaining)
            if not block:break
            parts.append(block);remaining-=len(block)
        body=b''.join(parts);after=os.fstat(fd)
        fields=('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')
        require(tuple(getattr(before,k) for k in fields)==tuple(getattr(after,k) for k in fields) and len(body)==before.st_size and hashlib.sha256(body).hexdigest()==expected,'role body differs')
        return body
    except BaseException as error:primary=error;raise
    finally:
        try:close(fd)
        except BaseException as error:
            if primary is None:raise
            _note(primary,error)

class EdgeOwner:
    """One lazy attempt, one sequential session borrow, retained captured cleanup."""
    def __init__(self,policy,*,numpy,scipy,agreement):
        import threading
        frozen=freeze(policy);require(frozen is not None,'explicit selected policy required')
        require(type(numpy) is types.ModuleType and numpy is sys.modules.get('numpy') and type(scipy) is types.ModuleType and scipy is sys.modules.get('scipy'),'original loaded scientific modules required')
        require(type(agreement) is types.FunctionType and agreement.__module__=='tradingagents.research.onchain_replication.matching_reference' and agreement.__name__=='agreement','original agreement role required')
        p=dict(frozen);thread=threading.get_ident();np=numpy;sp=scipy;original=agreement
        fd=None;fdpin=None;module=None;fill=None;active=None;attempted=False;closed=False;close_error=None
        close_fd=os.close
        methods={}
        def close():
            nonlocal fd,closed,close_error,active
            closed=True;active=None
            if close_error is not None:raise close_error
            if fd is not None:
                value=fd;fd=None
                try:close_fd(value)
                except BaseException as error:close_error=error;raise
        def metadata():
            import platform,sysconfig,struct
            require(threading.get_ident()==thread and not closed,'edge owner unavailable')
            require(self.policy is frozen,'edge policy replaced')
            for name,method in methods.items():require(getattr(self,name) is method,'edge owner capability replaced')
            source=read_reference(p['source_path'],SOURCE,65536)
            adapter=read_reference(p['adapter_path'],ADAPTER,65536)
            runtime=references.runtime_metadata(read_reference(p['runtime_path'],p['runtime_sha256'],4096,p['runtime_bytes']))
            abi=abi_metadata(read_reference(p['abi_path'],p['abi_sha256'],4096,p['abi_bytes']))
            actual=dict(python=platform.python_version(),numpy=np.__version__,scipy=sp.__version__,platform=sys.platform,machine=platform.machine(),byteorder=sys.byteorder,executable=sys.executable)
            require(all(runtime[k]==v for k,v in actual.items()),'runtime reference differs')
            require(sys.implementation.name==abi['implementation'] and sys.implementation.cache_tag==abi['cache_tag'] and sysconfig.get_config_var('SOABI')==abi['soabi'] and sysconfig.get_config_var('EXT_SUFFIX')==abi['ext_suffix'] and struct.calcsize('P')*8==abi['pointer_bits'],'CPython ABI differs')
            raw=read_reference(p['library_path'],LIBRARY,65536,17072,owned=True)
            return adapter,raw
        def current():
            try:
                metadata()
                if attempted:
                    import fcntl
                    require(fd is not None and module is not None and module.fill is native_fill,'edge backend unavailable/replaced')
                    s=os.fstat(fd);require((s.st_dev,s.st_ino,s.st_size)==fdpin and fcntl.fcntl(fd,fcntl.F_GET_SEALS)==seals,'sealed backend changed')
            except BaseException as primary:
                try:close()
                except BaseException as error:_note(primary,error)
                raise
        def acquire():
            nonlocal attempted,fd,fdpin,module,fill,native_fill,seals
            adapter,raw=metadata()
            if attempted:current();return
            attempted=True
            try:
                import fcntl,importlib.util,importlib.machinery,uuid
                seals=fcntl.F_SEAL_WRITE|fcntl.F_SEAL_GROW|fcntl.F_SEAL_SHRINK|fcntl.F_SEAL_SEAL
                fd=os.memfd_create('uncached-edge',os.MFD_CLOEXEC|os.MFD_ALLOW_SEALING)
                view=memoryview(raw)
                while view:
                    n=os.write(fd,view);require(n>0,'short sealed write');view=view[n:]
                fcntl.fcntl(fd,fcntl.F_ADD_SEALS,seals)
                require(fcntl.fcntl(fd,fcntl.F_GET_SEALS)==seals and os.pread(fd,len(raw)+1,0)==raw,'sealed same-kernel body differs')
                info=os.fstat(fd);fdpin=(info.st_dev,info.st_ino,info.st_size)
                # Unique full name avoids reuse of a prior extension cache key
                # when a descriptor pathname is recycled; final ABI name retained.
                name='_owned_edge_'+uuid.uuid4().hex+'._edge_chunk';path='/proc/self/fd/'+str(fd)
                loader=importlib.machinery.ExtensionFileLoader(name,path)
                spec=importlib.util.spec_from_file_location(name,path,loader=loader)
                require(spec is not None,'native spec unavailable')
                module=importlib.util.module_from_spec(spec);loader.exec_module(module)
                native_fill=module.fill
                namespace={'__name__':'_authenticated_edge_adapter'}
                exec(compile(adapter,p['adapter_path'],'exec',dont_inherit=True),namespace)
                fill=namespace['make_filler'](module,np,original)
                current()
            except BaseException as primary:
                try:close()
                except BaseException as error:_note(primary,error)
                raise
        def borrow(client):
            nonlocal active
            require(active is None,'only one edge session borrow allowed')
            try:
                acquire();token=object();active=token;released=False
                def lease_current():
                    require(not released and active is token,'edge borrow expired');current()
                def release():
                    nonlocal active,released
                    if released:return
                    released=True
                    require(active is token or closed,'edge borrow replaced')
                    active=None
                def apply(*args):
                    # Session.current already performed fresh body/runtime joins.
                    require(not closed and not released and active is token and module.fill is native_fill,'edge borrow unavailable')
                    return fill(*args)
                try:return types.SimpleNamespace(fill=apply,current=lease_current,close=release)
                except BaseException as primary:
                    try:release()
                    except BaseException as error:_note(primary,error)
                    raise
            except BaseException as primary:
                try:close()
                except BaseException as error:_note(primary,error)
                raise
        native_fill=None;seals=None
        self.policy=frozen;self.current=current;self.borrow=borrow;self.close=close
        methods.update(current=current,borrow=borrow,close=close)

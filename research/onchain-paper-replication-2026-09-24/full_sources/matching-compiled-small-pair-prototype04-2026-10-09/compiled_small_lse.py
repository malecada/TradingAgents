"""Uninstalled guarded prototype. No authority or universal bitwise equivalence."""
import ctypes,hashlib,platform,sys,os,stat
try:import fcntl
except ImportError:fcntl=None
from pathlib import Path
import numpy as np
from scipy.special import logsumexp as _original
_CODE=_original.__code__
_PATH=Path(__file__).with_name('reduction.so')
_EXPECTED='9fd95c85ae9c5572adad1f0c8824d6f52f09762cc06fcb7ad03b17a6cc03e3f2'
_PTR=ctypes.POINTER(ctypes.c_double)
_ARGS=[_PTR,_PTR,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int]
# Values independently compiled from the existing local Linux headers (PROBE03).
_F_ADD_SEALS=1033
_F_GET_SEALS=1034
_F_SEAL_WRITE=8
_F_SEAL_GROW=4
_F_SEAL_SHRINK=2
_F_SEAL_SEAL=1
_MFD_CLOEXEC=1
_MFD_ALLOW_SEALING=2

def _new_memfd():
    native=getattr(os,'memfd_create',None)
    if native is not None:return native('small-lse-prototype03',_MFD_CLOEXEC|_MFD_ALLOW_SEALING)
    # Old-build Python may omit memfd_create despite the runtime libc/kernel API.
    libc=ctypes.CDLL(None,use_errno=True)
    function=libc.memfd_create;function.argtypes=[ctypes.c_char_p,ctypes.c_uint];function.restype=ctypes.c_int
    fd=function(b'small-lse-prototype03',_MFD_CLOEXEC|_MFD_ALLOW_SEALING)
    if fd<0:
        error=ctypes.get_errno();raise OSError(error,os.strerror(error))
    return fd

_lib=_fn=None
_fd=None
_pin=None
_SEALS=None

def _load_sealed():
    """Authenticate once, then retain kernel-immutable bytes and descriptor."""
    source=owned=None
    result=primary=None
    try:
        if not (sys.platform=='linux' and sys.byteorder=='little' and platform.machine()=='x86_64'
                and ctypes.sizeof(ctypes.c_double)==8 and fcntl is not None):return None
        seals=_F_SEAL_WRITE|_F_SEAL_GROW|_F_SEAL_SHRINK|_F_SEAL_SEAL
        source=os.open(_PATH,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
        before=os.fstat(source)
        if not (stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_uid==os.getuid()
                and 0<before.st_size<=65536):return None
        parts=[];remaining=before.st_size+1
        while remaining:
            part=os.read(source,remaining)
            if not part:break
            parts.append(part);remaining-=len(part)
        raw=b''.join(parts)
        after=os.fstat(source)
        if ((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
            !=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
            or len(raw)!=before.st_size or hashlib.sha256(raw).hexdigest()!=_EXPECTED):return None
        owned=_new_memfd()
        view=memoryview(raw)
        while view:
            count=os.write(owned,view)
            if count<=0:raise OSError('short sealed library write')
            view=view[count:]
        fcntl.fcntl(owned,_F_ADD_SEALS,seals)
        if fcntl.fcntl(owned,_F_GET_SEALS)!=seals or os.pread(owned,len(raw)+1,0)!=raw:return None
        info=os.fstat(owned);pin=(info.st_dev,info.st_ino,info.st_size)
        library=ctypes.CDLL('/proc/self/fd/'+str(owned),mode=os.RTLD_NOW|os.RTLD_LOCAL)
        function=library.small_lse;function.argtypes=list(_ARGS);function.restype=ctypes.c_int
        result=(library,function,owned,pin,seals)
    except (OSError,AttributeError) as error:
        primary=error  # Unsupported route may fall back only after clean release.
    except BaseException as error:
        primary=error
        raise
    finally:
        failures=[]
        if source is not None:
            try:os.close(source)
            except BaseException as error:failures.append(('source',source,error))
        # Successful source close is a prerequisite for retained-FD transfer.
        if owned is not None and (result is None or primary is not None or failures):
            try:os.close(owned)
            except BaseException as error:failures.append(('memfd',owned,error))
        if failures:
            failure=primary if primary is not None else failures[0][2]
            for kind,fd,error in failures:
                BaseException.add_note(failure,f'{kind} fd {fd} cleanup uncertain; no retry: {type(error).__name__}')
            raise failure
    return result

_loaded=_load_sealed()
if _loaded is not None:_lib,_fn,_fd,_pin,_SEALS=_loaded
_loaded=None

_close_error=None

def close():
    """Terminal disable; never retry an ambiguous close on a possibly reused FD."""
    global _fn,_fd,_close_error
    _fn=None
    if _close_error is not None:raise _close_error
    if _fd is not None:
        fd=_fd;_fd=None
        try:os.close(fd)
        except BaseException as error:
            _close_error=error
            BaseException.add_note(error,f'memfd {fd} close uncertain; backend disabled; no retry')
            raise

def _live():
    try:
        if _fd is None:return False
        info=os.fstat(_fd)
        return (info.st_dev,info.st_ino,info.st_size)==_pin and fcntl.fcntl(_fd,_F_GET_SEALS)==_SEALS
    except (OSError,AttributeError):return False
_ORIGINAL_FN=_fn
_NP_PINS=(np.geterr,np.isfinite,np.abs,np.all,np.empty,np.ndarray)
def lse(block,*,axis,keepdims,fallback):
    eligible=(_fn is not None and _fn is _ORIGINAL_FN and _fn.argtypes==_ARGS and _fn.restype is ctypes.c_int
        and fallback is _original and fallback.__code__ is _CODE
        and (np.geterr,np.isfinite,np.abs,np.all,np.empty,np.ndarray)==_NP_PINS
        and np.geterr()=={'divide':'warn','over':'warn','under':'ignore','invalid':'warn'}
        and type(block)is np.ndarray and block.dtype==np.float64 and block.ndim==2
        and all(1<=d<=4 for d in block.shape) and all(0<s<=2**31-1 and s%8==0 for s in block.strides)
        and axis in (0,1) and keepdims is True and np.isfinite(block).all() and np.all(np.abs(block)<=256.))
    if eligible:eligible=_live()
    if not eligible:return fallback(block,axis=axis,keepdims=keepdims)
    result=np.empty((block.shape[0],1) if axis==1 else (1,block.shape[1]),dtype=np.float64)
    status=_fn(block.ctypes.data_as(_PTR),result.ctypes.data_as(_PTR),*block.shape,
               block.strides[0]//8,block.strides[1]//8,axis)
    if status:return fallback(block,axis=axis,keepdims=keepdims)
    return result

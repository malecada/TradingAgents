"""Uninstalled guarded prototype. No authority or universal bitwise equivalence."""
import ctypes,hashlib,platform,sys
from pathlib import Path
import numpy as np
from scipy.special import logsumexp as _original
_CODE=_original.__code__
_PATH=Path(__file__).with_name('reduction.so')
_EXPECTED='9fd95c85ae9c5572adad1f0c8824d6f52f09762cc06fcb7ad03b17a6cc03e3f2'
_PTR=ctypes.POINTER(ctypes.c_double)
_ARGS=[_PTR,_PTR,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int]
_lib=_fn=None
try:
 if (sys.byteorder=='little' and platform.machine()=='x86_64' and ctypes.sizeof(ctypes.c_double)==8
         and _PATH.stat().st_size<=65536 and hashlib.sha256(_PATH.read_bytes()).hexdigest()==_EXPECTED):
  _lib=ctypes.CDLL(str(_PATH));_fn=_lib.small_lse;_fn.argtypes=list(_ARGS);_fn.restype=ctypes.c_int
except (OSError,AttributeError):pass
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
    if eligible:
        try:eligible=_PATH.stat().st_size<=65536 and hashlib.sha256(_PATH.read_bytes()).hexdigest()==_EXPECTED
        except OSError:eligible=False
    if not eligible:return fallback(block,axis=axis,keepdims=keepdims)
    result=np.empty((block.shape[0],1) if axis==1 else (1,block.shape[1]),dtype=np.float64)
    status=_fn(block.ctypes.data_as(_PTR),result.ctypes.data_as(_PTR),*block.shape,
               block.strides[0]//8,block.strides[1]//8,axis)
    if status:return fallback(block,axis=axis,keepdims=keepdims)
    return result

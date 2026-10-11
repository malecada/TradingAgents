"""Explicit engineering-only adapter; caller supplies already loaded extension.
No library discovery, build, loading or authority capability is performed here.
"""
import types

def make_filler(native, np, agreement):
    if type(native.fill) is not types.BuiltinFunctionType or native.fill.__module__!='_edge_chunk':
        raise ValueError('exact CPython extension function required')
    fill=native.fill
    ndarray=np.ndarray;float64=np.dtype('float64');int64=np.dtype('int64')
    def apply(weights,af,bf,left,right,count,callback,progress):
        # All eligibility decisions precede native writes. Unsupported -> original.
        if callback is not agreement or native.fill is not fill:return False
        if type(count) is not int or not 1<=count<=1024:return False
        if any(type(x) is not ndarray for x in (weights,af,bf,left,right)):return False
        if weights.dtype!=float64 or weights.shape!=(count,) or not weights.flags.writeable:return False
        if any(x.dtype!=float64 or x.ndim!=2 or x.flags.writeable for x in (af,bf)):return False
        if any(x.dtype!=int64 or x.shape!=(count,) for x in (left,right)):return False
        indices=tuple(range(count))
        # After this point an error uses this index to replay the original prefix.
        progress[0]=0
        return fill(weights,af,bf,left,right,count,callback,progress,indices)
    return apply

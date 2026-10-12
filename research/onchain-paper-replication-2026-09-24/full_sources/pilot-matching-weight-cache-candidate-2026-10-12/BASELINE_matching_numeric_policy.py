"""Explicit C05 edge-agreement selection; never Run/Owner/source authority.

The enclosing admitted caller authenticates these source and NumPy runtime bodies.
The adapter pins live helper identities, copies only <=1024 int64 indices per
side into immutable bytes, and delegates refusals to the already authenticated
edge lease when supplied by ImmutablePairSession. Node agreements remain scalar.
"""
from types import MappingProxyType
import numpy as np
from . import matching_numeric_kernel as kernel, phase_timing

POLICY=MappingProxyType(dict(format='bounded-numpy-agreement-c05-v1',
    min_chunk_entries=256,max_chunk_entries=1024,max_index_bytes=16384,
    atol=1e-8,rtol=1e-6))


def freeze(value):
    if value is None:return None
    if (type(value) is not dict or set(value)!=set(POLICY) or
            any(type(value[k]) is not type(v) or value[k]!=v for k,v in POLICY.items())):
        raise ValueError('fixed C05 numeric kernel policy required')
    return tuple(sorted(value.items()))


def attach(owner,value):
    owner._numeric_kernel_policy=freeze(value)
    owner._numeric_kernel_policy_pin=owner._numeric_kernel_policy


def current(owner):
    if owner._numeric_kernel_policy is not owner._numeric_kernel_policy_pin:
        raise ValueError('numeric kernel selection changed')


def options(owner):
    current(owner)
    return {} if owner._numeric_kernel_policy is None else {'numeric_kernel_policy':dict(owner._numeric_kernel_policy)}


def join(owner,child):
    current(owner);current(child)
    if owner._numeric_kernel_policy!=child._numeric_kernel_policy:
        raise ValueError('numeric kernel chain changed')


class NumericAgreementAdapter:
    def __init__(self,policy):
        self.policy=freeze(dict(policy) if type(policy) is MappingProxyType else policy)
        if self.policy is None:raise ValueError('explicit numeric policy required')
        self._pin=self.policy
        self._functions=tuple((name,getattr(kernel,name),getattr(kernel,name).__code__)
                              for name in ('fill_agreement','_immutable'))
        self._numpy=np
        self._ops=tuple((name,getattr(np,name)) for name in
            ('frombuffer','shares_memory','any','isfinite','abs','subtract','square','sum','negative','divide','exp','geterr'))
        self._counts=dict(numpy_chunks=0,numpy_entries=0,fallback_chunks=0,index_bytes=0)

    def current(self):
        if self.policy is not self._pin or kernel.np is not self._numpy:
            raise ValueError('numeric adapter changed')
        for name,function,code in self._functions:
            if getattr(kernel,name) is not function or function.__code__ is not code:
                raise ValueError('numeric helper changed')
        for name,function in self._ops:
            if getattr(np,name) is not function:raise ValueError('numeric runtime changed')

    def snapshot(self):
        return dict(self._counts)

    def fill(self,out,left,right,li,ri,count,scalar,progress):
        self.current()
        if (type(count) is int and 256<=count<=1024 and
                all(type(x) is np.ndarray and x.dtype==np.dtype('int64') and
                    x.ndim==1 and len(x)>=count for x in (li,ri))):
            # Max simultaneous immutable index bodies: 16,384 bytes. No full
            # graph copy. Refusal leaves out/progress and caller cursor intact.
            il=np.frombuffer(li[:count].tobytes(),dtype=np.int64)
            ir=np.frombuffer(ri[:count].tobytes(),dtype=np.int64)
            self._counts['index_bytes']+=16*count
            if kernel.fill_agreement(left,right,il,ir,out,0,count):
                out[:count]*=.5
                progress[0]=count
                self._counts['numpy_chunks']+=1;self._counts['numpy_entries']+=count
                phase_timing.add_count('agreement_numpy_chunks',1)
                phase_timing.add_count('agreement_numpy_entries',count)
                return True
        self._counts['fallback_chunks']+=1
        phase_timing.add_count('agreement_fallback_chunks',1)
        return False

"""Private bounded JSON snapshot, not cached authority or mutable execution state."""
import math
from types import MappingProxyType
from .provenance import canonical_bytes
POLICY={'format':'immutable-target-execution-v1','max_bytes':65536,'max_nodes':8192,'max_depth':24}
def require(ok,message):
    if not ok:raise ValueError(message)
def selected(value):
    if value is None or value is False:return False
    require(type(value) is dict and set(value)==set(POLICY) and value==POLICY and type(value['format']) is str and all(type(value[k]) is int for k in ('max_bytes','max_nodes','max_depth')),'explicit immutable target metadata policy required')
    return True

def snapshot(value):
    # Only exact JSON builtins; each newly constructed backing dict remains
    # private to its mappingproxy. No caller mutable object is retained.
    nodes=0;string_bytes=0
    def freeze(x,depth):
        nonlocal nodes,string_bytes
        nodes+=1;require(nodes<=8192 and depth<=24,'target JSON nodes/depth bound')
        kind=type(x)
        if x is None or kind is bool:return x
        if kind is int:
            require(-(2**63)<=x<2**63,'target JSON integer bound');return x
        if kind is float:
            require(math.isfinite(x),'target JSON finite float required');return x
        if kind is str:
            require(len(x)<=65536,'target JSON string bound');string_bytes+=len(x.encode('utf-8'))
            require(string_bytes<=65536,'target JSON cumulative string bound');return x
        if kind is list:
            require(len(x)<=8192-nodes,'target JSON list bound')
            return tuple(freeze(item,depth+1) for item in x)
        if kind is dict:
            require(len(x)<=8192-nodes,'target JSON object bound');copy={}
            for key,item in x.items():
                require(type(key) is str,'target JSON string keys required')
                private_key=freeze(key,depth+1);copy[private_key]=freeze(item,depth+1)
            return MappingProxyType(copy)
        raise ValueError('unsupported target JSON type')
    tree=freeze(value,0);pin=canonical_bytes(tree)
    require(type(pin) is bytes and len(pin)<=65536,'target JSON canonical byte bound')
    return (tree,pin)

def current(target):
    anchor=target._execution_anchor
    require(type(anchor) is tuple and len(anchor)==2 and anchor is target._execution_anchor_pin and target._execution is anchor[0] and target._execution_pin is anchor[1],'target immutable execution snapshot changed')

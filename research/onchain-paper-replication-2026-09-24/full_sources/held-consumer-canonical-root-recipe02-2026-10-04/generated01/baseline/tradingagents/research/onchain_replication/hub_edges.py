"""Exact induced-edge sizing for an explicit finite set of neighborhood centers.

This isolated engineering component never changes scientific neighborhood caps.
Inputs/mapped residency, Python/runtime and callback state are excluded from the
numeric scratch envelope. The registered wrapper must own/checkpoint/bound time.
"""
import numpy as np


def measure(edge_index,node_count,expected,*,max_buffer_bytes,edge_chunk=65536,checkpoint=None):
    if type(node_count) is not int or node_count<=0:
        raise ValueError('positive integer node count required')
    if not isinstance(edge_index,np.ndarray) or edge_index.dtype!=np.dtype(np.int64) or edge_index.ndim!=2 or edge_index.shape[0]!=2:
        raise ValueError('int64 endpoint matrix required')
    if not isinstance(expected,dict) or not 1<=len(expected)<=64:
        raise ValueError('one to 64 explicit centers required')
    if any(type(k) is not int or not 0<=k<node_count or type(v) is not int or not 1<=v<=node_count for k,v in expected.items()):
        raise ValueError('center or expected cardinality outside domain')
    if type(edge_chunk) is not int or not 1<=edge_chunk<=65536 or type(max_buffer_bytes) is not int or max_buffer_bytes<=0:
        raise ValueError('positive bounded numeric policy required')
    e=edge_index.shape[1]
    required=node_count+32*min(edge_chunk,e)+16*len(expected)+65536
    if required>max_buffer_bytes:raise ValueError('numeric allowance exceeded')
    for first in range(0,e,edge_chunk):
        part=edge_index[:,first:first+edge_chunk]
        if part.min()<0 or part.max()>=node_count:raise ValueError('endpoint outside node domain')
    selected=np.zeros(node_count,dtype=bool)
    rows=[]
    for center,want in expected.items():
        selected[:]=False;selected[center]=True
        for first in range(0,e,edge_chunk):
            a,b=edge_index[:,first:first+edge_chunk]
            selected[b[a==center]]=True
            selected[a[b==center]]=True
        count=int(np.count_nonzero(selected))
        if count!=want:raise ValueError('retained census cardinality differs from exact neighborhood')
        induced=0
        for first in range(0,e,edge_chunk):
            a,b=edge_index[:,first:first+edge_chunk]
            induced+=int(np.count_nonzero(selected[a]&selected[b]))
        row={'center':center,'nodes':count,'directed_edges':induced}
        if checkpoint is not None:checkpoint(row.copy())
        rows.append(row)
    return rows

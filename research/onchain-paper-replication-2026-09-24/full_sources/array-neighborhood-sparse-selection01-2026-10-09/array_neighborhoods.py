"""Optional complete induced neighborhoods with an explicit array allowance.

The allowance covers retained numeric indices and conservative per-call numeric
scratch/output copies. It is not total RSS: graph inputs, Python metadata/IDs,
validation internals and caller-retained prior outputs require separate admission.
No frozen configuration or existing consumer is changed by this component.
"""
import numpy as np
from threading import Lock
from .contracts import AttributedGraph
from .neighborhoods import graph_hash


def _merge_indices(selected, block):
    # Explicit array scratch: concatenation, two boolean masks, result.
    # Avoid np.union1d's version-dependent hash-table allocation.
    merged=np.concatenate((selected,block))
    merged.sort(kind='quicksort')
    distinct=np.empty(len(merged),dtype=bool)
    distinct[:1]=True
    distinct[1:]=merged[1:]!=merged[:-1]
    return merged[distinct]


class ArrayNeighborhoodIndex:
    """Exclusive, context-owned sparse index; complete extraction, never truncation."""
    def __init__(self, graph, *, max_buffer_bytes, edge_chunk=65536):
        if type(max_buffer_bytes) is not int or max_buffer_bytes <= 0:
            raise ValueError('positive integer buffer allowance required')
        if type(edge_chunk) is not int or edge_chunk <= 0:
            raise ValueError('positive integer edge chunk required')
        n=len(graph.node_ids); e=graph.edge_index.shape[1]
        node_width=graph.node_features.shape[1]*graph.node_features.dtype.itemsize
        edge_width=graph.edge_features.shape[1]*graph.edge_features.dtype.itemsize
        # Retained: two int64 stable edge orders and two int64 offset arrays.
        # Scratch envelope: sort work/counts, frontiers/masks, selected indices,
        # global-to-local map, kept-edge indices and bounded gather temporaries.
        # Deliberately additive (including temporaries not simultaneously live).
        self.buffer_allowance=16*(e+n+1)+16*e+40*(n+1)+4*n+edge_chunk*(64+2*node_width+2*edge_width)
        if self.buffer_allowance>max_buffer_bytes:
            raise ValueError('neighborhood index buffer allowance exceeded')
        self.max_buffer_bytes=max_buffer_bytes; self.edge_chunk=edge_chunk
        self.graph=graph; self.identity=graph_hash(graph); self.closed=False
        self._lock=Lock()
        self.orders=[]; self.offsets=[]
        try:
            for endpoints in graph.edge_index:
                self.orders.append(np.argsort(endpoints,kind='stable'))
                offsets=np.empty(n+1,dtype=np.int64); offsets[0]=0
                counts=np.bincount(endpoints,minlength=n)
                np.cumsum(counts,out=offsets[1:]); del counts
                self.offsets.append(offsets)
        except BaseException:
            self.close()
            raise

    def __enter__(self):
        self._open()
        return self

    def __exit__(self,*exc):
        self.close()

    def _open(self):
        if self.closed:
            raise ValueError('neighborhood index is closed')

    def close(self):
        if not self._lock.acquire(blocking=False):
            raise ValueError('neighborhood index is busy')
        try:
            self.orders=[]; self.offsets=[]; self.graph=None; self.closed=True
        finally:
            self._lock.release()

    def _blocks(self,node,direction):
        start=int(self.offsets[direction][node]); stop=int(self.offsets[direction][node+1])
        for pos in range(start,stop,self.edge_chunk):
            yield self.orders[direction][pos:min(stop,pos+self.edge_chunk)]

    def _select(self,center,config):
        self._open(); n=len(self.graph.node_ids)
        hops=config['hop_depth']; limit=config['maximum_neighborhood_nodes']
        if type(center) is not int or not 0<=center<n:
            raise ValueError('invalid center')
        if type(hops) is not int or hops<0 or type(limit) is not int or limit<1:
            raise ValueError('invalid neighborhood selection contract')
        selected=np.array([center],dtype=np.int64)
        frontier=selected
        for _ in range(hops):
            candidates=np.empty(0,dtype=np.int64)
            for node in frontier:
                for direction in (0,1):
                    for edges in self._blocks(node,direction):
                        candidates=_merge_indices(candidates,self.graph.edge_index[1-direction,edges])
            del frontier
            positions=np.searchsorted(selected,candidates)
            np.minimum(positions,len(selected)-1,out=positions)
            following=candidates[candidates!=selected[positions]]
            del positions,candidates
            for pos in range(0,len(following),self.edge_chunk):
                selected=_merge_indices(selected,following[pos:pos+self.edge_chunk])
            if len(selected)>limit:
                raise ValueError('neighborhood capacity exceeded, no truncation')
            frontier=following
            del following
            if not len(frontier):break
        return selected,selected

    def _induced_blocks(self,indices,selected):
        for node in indices:
            for edges in self._blocks(node,0):
                targets=self.graph.edge_index[1,edges]
                positions=np.searchsorted(selected,targets)
                np.minimum(positions,len(selected)-1,out=positions)
                yield edges[selected[positions]==targets]

    def selected(self,center,config):
        """Return independent ascending global indices, not scratch-backed state."""
        if not self._lock.acquire(blocking=False):
            raise ValueError('neighborhood index is busy')
        try:
            indices,_=self._select(center,config)
            return indices
        finally:
            self._lock.release()

    def neighborhood(self,center,config):
        if not self._lock.acquire(blocking=False):
            raise ValueError('neighborhood index is busy')
        try:
            return self._neighborhood(center,config)
        finally:
            self._lock.release()

    def _neighborhood(self,center,config):
        indices,selected=self._select(center,config); g=self.graph
        count=sum(len(edges) for edges in self._induced_blocks(indices,selected))
        node_bytes=len(indices)*g.node_features.shape[1]*g.node_features.dtype.itemsize
        edge_bytes=count*(16+g.edge_features.shape[1]*g.edge_features.dtype.itemsize)
        # Source arrays and immutable AttributedGraph copies can coexist.
        if self.buffer_allowance+2*(node_bytes+edge_bytes)>self.max_buffer_bytes:
            raise ValueError('neighborhood output buffer allowance exceeded')
        keep=np.empty(count,dtype=np.int64); cursor=0
        for edges in self._induced_blocks(indices,selected):
            keep[cursor:cursor+len(edges)]=edges;cursor+=len(edges)
        keep.sort(kind='quicksort')  # Exact original directed edge-column order.
        nodes=np.empty((len(indices),g.node_features.shape[1]),dtype=g.node_features.dtype)
        edges=np.empty((2,count),dtype=np.int64)
        features=np.empty((count,g.edge_features.shape[1]),dtype=g.edge_features.dtype)
        for pos in range(0,len(indices),self.edge_chunk):
            block=indices[pos:pos+self.edge_chunk];nodes[pos:pos+len(block)]=g.node_features[block]
        for pos in range(0,count,self.edge_chunk):
            block=keep[pos:pos+self.edge_chunk]
            edges[:,pos:pos+len(block)]=np.searchsorted(indices,g.edge_index[:,block])
            features[pos:pos+len(block)]=g.edge_features[block]
        return AttributedGraph(tuple(g.node_ids[i] for i in indices),nodes,edges,features,self.identity,g.node_ids[center])

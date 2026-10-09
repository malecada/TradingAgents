"""Deterministic overlap-weighted training-only local graph sampling."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .contracts import AttributedGraph,graph_to_dict,validate_graph
from .cache import cache_key
from .provenance import utc,freeze


def graph_hash(graph):
    # Exact canonical JSON identity, streamed so weekly arrays need no giant list copy.
    from dataclasses import fields
    from collections.abc import Mapping
    from .provenance import canonical_bytes
    import hashlib
    validate_graph(graph);h=hashlib.sha256()
    def feed(value):
        if isinstance(value,np.ndarray):
            h.update(b'[')
            for i,row in enumerate(value):
                if i:h.update(b',')
                h.update(canonical_bytes(row.tolist()))
            h.update(b']')
        elif isinstance(value,Mapping):
            h.update(b'{')
            for i,key in enumerate(sorted(value)):
                if i:h.update(b',')
                h.update(canonical_bytes(key));h.update(b':');feed(value[key])
            h.update(b'}')
        else:h.update(canonical_bytes(value))
    feed({f.name:getattr(graph,f.name) for f in fields(graph)})
    return h.hexdigest()


class NeighborhoodIndex:
    """Bounded sparse adjacency index, reused across all centers of one graph."""
    def __init__(self,graph):
        self.graph=graph;self.identity=graph_hash(graph)
        n=len(graph.node_ids);self.orders=[];self.offsets=[]
        for endpoints in graph.edge_index:
            order=np.argsort(endpoints,kind='stable');self.orders.append(order)
            self.offsets.append(np.concatenate(([0],np.cumsum(np.bincount(endpoints,minlength=n)))))

    def selected(self,center,config):
        if not 0<=center<len(self.graph.node_ids):raise ValueError('invalid center')
        selected={center};front={center}
        for _ in range(config['hop_depth']):
            new=set()
            for node in front:
                for direction in (0,1):
                    edges=self.orders[direction][self.offsets[direction][node]:self.offsets[direction][node+1]]
                    new.update(map(int,self.graph.edge_index[1-direction,edges]))
            front=new-selected;selected|=new
            if len(selected)>config['maximum_neighborhood_nodes']:raise ValueError('neighborhood capacity exceeded, no truncation')
        return sorted(selected)

    def neighborhood(self,center,config):
        g=self.graph;indices=self.selected(center,config);mapping={old:new for new,old in enumerate(indices)}
        candidates=np.concatenate([self.orders[0][self.offsets[0][i]:self.offsets[0][i+1]] for i in indices])
        keep=np.array(sorted(int(e) for e in candidates if int(g.edge_index[1,e]) in mapping),dtype=np.int64)
        edges=np.array([(mapping[int(a)],mapping[int(b)]) for a,b in g.edge_index[:,keep].T],dtype=np.int64).reshape(-1,2).T
        return AttributedGraph(tuple(g.node_ids[i] for i in indices),g.node_features[indices],edges,g.edge_features[keep],self.identity,g.node_ids[center])


def neighborhood(graph,center,config):
    if not 0<=center<len(graph.node_ids):raise ValueError('invalid center')
    selected={center};front={center}
    # Weak reachability but retain direction/attributes in the induced graph.
    for _ in range(config['hop_depth']):
        new=set()
        for a,b in graph.edge_index.T:
            if int(a) in front:new.add(int(b))
            if int(b) in front:new.add(int(a))
        front=new-selected;selected|=new
        if len(selected)>config['maximum_neighborhood_nodes']:raise ValueError('neighborhood capacity exceeded, no truncation')
    indices=sorted(selected);mapping={old:new for new,old in enumerate(indices)}
    mask=np.array([int(a) in selected and int(b) in selected for a,b in graph.edge_index.T],dtype=bool)
    edges=np.array([(mapping[int(a)],mapping[int(b)]) for a,b in graph.edge_index[:,mask].T],dtype=np.int64).reshape(-1,2).T
    return AttributedGraph(tuple(graph.node_ids[i] for i in indices),graph.node_features[indices],edges,graph.edge_features[mask],graph_hash(graph),graph.node_ids[center])


@dataclass(frozen=True)
class SampleManifest:
    graphs: tuple[AttributedGraph, ...]
    records: tuple[dict, ...]
    source_hashes: tuple[str, ...]
    rng_state: dict
    seed: int
    identity: str

    def __post_init__(self):
        object.__setattr__(self,'records',freeze(self.records))
        object.__setattr__(self,'rng_state',freeze(self.rng_state))


def sample_neighborhoods(graphs,config,seed):
    start,end=utc(config['train_start']),utc(config['train_end'])
    training=[]
    for g in graphs:
        if utc(g.start_utc)>=start and utc(g.available_at)<end:
            validate_graph(g);training.append(g)
    training.sort(key=lambda g:(g.start_utc,g.asset,graph_hash(g)))
    hashes=tuple(graph_hash(g) for g in training)
    if len(set(hashes))!=len(hashes):raise ValueError('duplicate training graph')
    offsets=np.cumsum([0]+[len(g.node_ids) for g in training])
    total=int(offsets[-1])
    if total<config['sample_count']:raise ValueError('insufficient unique centers')
    weights=np.ones(total,dtype=np.float64)
    rng=np.random.Generator(np.random.PCG64(seed));records=[];samples=[]
    active_gi=None;index=None
    for _ in range(config['sample_count']):
        probability=weights/weights.sum()
        chosen=int(rng.choice(total,p=probability))
        gi=int(np.searchsorted(offsets,chosen,side='right')-1);center=chosen-int(offsets[gi])
        g=training[gi]
        if gi!=active_gi:index=NeighborhoodIndex(g);active_gi=gi
        sub=index.neighborhood(center,config)
        records.append({'graph_hash':hashes[gi],'center_id':g.node_ids[center],'center_index':center,'probability':float(probability[chosen]),'node_count':len(sub.node_ids),'edge_count':sub.edge_index.shape[1]})
        samples.append(sub);weights[chosen]=0
        weights[int(offsets[gi])+np.asarray(index.selected(center,config),dtype=np.int64)]*=.5
    state=rng.bit_generator.state
    identity=cache_key({'training_graphs':hashes,'config':config,'seed':seed,'records':records,'rng_state':state})
    return SampleManifest(tuple(samples),tuple(records),hashes,state,seed,identity)

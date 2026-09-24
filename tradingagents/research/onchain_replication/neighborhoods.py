"""Deterministic overlap-weighted training-only local graph sampling."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .contracts import AttributedGraph,graph_to_dict,validate_graph
from .cache import cache_key
from .provenance import utc,freeze


def graph_hash(graph):return cache_key(graph_to_dict(graph))


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
    for _ in range(config['sample_count']):
        probability=weights/weights.sum()
        chosen=int(rng.choice(total,p=probability))
        gi=int(np.searchsorted(offsets,chosen,side='right')-1);center=chosen-int(offsets[gi])
        g=training[gi];sub=neighborhood(g,center,config)
        records.append({'graph_hash':hashes[gi],'center_id':g.node_ids[center],'center_index':center,'probability':float(probability[chosen]),'node_count':len(sub.node_ids),'edge_count':sub.edge_index.shape[1]})
        samples.append(sub);weights[chosen]=0
        lookup={x:i for i,x in enumerate(g.node_ids)}
        for name in sub.node_ids:weights[int(offsets[gi])+lookup[name]]*=.5
    state=rng.bit_generator.state
    identity=cache_key({'training_graphs':hashes,'config':config,'seed':seed,'records':records,'rng_state':state})
    return SampleManifest(tuple(samples),tuple(records),hashes,state,seed,identity)

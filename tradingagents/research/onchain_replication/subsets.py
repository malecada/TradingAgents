"""Declared whale/fund graph transformations with origin counts retained explicitly."""
import numpy as np
from .contracts import GraphSnapshot,validate_graph
from .neighborhoods import graph_hash
from .cache import cache_key


def filter_graph(graph,variant,*,cohort=None,cohort_hash=None,exact_incident_volumes=None):
    validate_graph(graph)
    if graph.edge_aggregates is None:raise ValueError('original raw edge aggregates required; log inversion forbidden')
    if variant=='whale':
        if graph.asset=='BTC':
            from fractions import Fraction
            if exact_incident_volumes is None or len(exact_incident_volumes)!=len(graph.node_ids):raise ValueError('exact BTC incident volumes required')
            incident=np.array([Fraction(v) for v in exact_incident_volumes],dtype=object)
        else:
            incident=np.zeros(len(graph.node_ids))
            np.add.at(incident,graph.edge_index[0],graph.edge_aggregates[:,1]);np.add.at(incident,graph.edge_index[1],graph.edge_aggregates[:,1])
        if not len(incident):raise ValueError('empty original graph')
        cutoff=(Fraction(9,10) if graph.asset=='BTC' else .9)*incident.max()
        keep_nodes=incident<=cutoff;decision={'threshold':.9,'strict':True}
    elif variant=='fund':
        from .provenance import require_hash
        if cohort is None or not cohort:raise ValueError('original admitted fund cohort unavailable')
        require_hash(cohort_hash);members=set(cohort)
        keep_nodes=np.array([node in members for node in graph.node_ids]);decision={'cohort_hash':cohort_hash}
    else:raise ValueError('unknown graph variant')
    mask=keep_nodes[graph.edge_index[0]]&keep_nodes[graph.edge_index[1]]
    edges=graph.edge_index[:,mask];weights=graph.edge_aggregates[mask]
    nodes=np.flatnonzero(keep_nodes)
    if not len(nodes):raise ValueError('variant has no admitted nodes')
    remap=np.full(len(graph.node_ids),-1,dtype=np.int64);remap[nodes]=np.arange(len(nodes));edges=remap[edges]
    features=np.zeros((len(nodes),4))
    for (a,b),(count,value) in zip(edges.T,weights,strict=True):
        features[a,1]+=count;features[a,3]+=value;features[b,0]+=count;features[b,2]+=value
    parent=graph_hash(graph)
    receipt={'variant':variant,'parent_graph_hash':parent,'decision':decision,'exact_incident_volume_hash':None if exact_incident_volumes is None else cache_key([str(v) for v in exact_incident_volumes]),'retained_nodes':len(nodes),'retained_edges':len(weights),'removed_edges':int((~mask).sum()),'raw_event_counter_policy':'origin admission counters retained; variant edge removals separately recorded, not relabeled raw exclusions'}
    result=GraphSnapshot(graph.asset,graph.start_utc,graph.end_utc,graph.available_at,graph.source_hashes,cache_key({'parent_config':graph.graph_config_hash,'variant':receipt}),tuple(graph.node_ids[i] for i in nodes),np.log1p(features),edges,np.log1p(weights),graph.raw_count,graph.admitted_count,graph.exclusion_counts,weights)
    validate_graph(result)
    return result,receipt

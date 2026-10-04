"""Explicit JSON contracts for small motif/sample artifacts; no object pickle."""
import numpy as np
from .contracts import AttributedGraph,validate_attributed
from .neighborhoods import SampleManifest
from .dictionary import Dictionary,dictionary_hash
from .provenance import thaw


def graph_to_record(g):
    return {'node_ids':g.node_ids,'node_features':g.node_features.tolist(),'edge_index':g.edge_index.tolist(),'edge_features':g.edge_features.tolist(),'edge_width':g.edge_features.shape[1],'parent_hash':g.parent_hash,'center_id':g.center_id}


def graph_from_record(value):
    v=dict(value);width=v.pop('edge_width');v['node_features']=np.asarray(v['node_features'],dtype=float);v['edge_index']=np.asarray(v['edge_index'],dtype=np.int64).reshape(2,-1);v['edge_features']=np.asarray(v['edge_features'],dtype=float).reshape(-1,width)
    g=AttributedGraph(**v);validate_attributed(g);return g


def samples_to_record(samples):
    return {'graphs':[graph_to_record(g) for g in samples.graphs],'records':thaw(samples.records),'source_hashes':samples.source_hashes,'rng_state':thaw(samples.rng_state),'seed':samples.seed,'identity':samples.identity}


def samples_from_record(value):
    v=dict(value);v['graphs']=tuple(graph_from_record(g) for g in v['graphs']);v['source_hashes']=tuple(v['source_hashes']);return SampleManifest(**v)


def dictionary_to_record(dictionary):
    v={name:thaw(getattr(dictionary,name)) for name in ('memberships','sample_hash','training_graph_hashes','config','matching_config_hash','identity','hierarchy')}
    v['representatives']=[graph_to_record(g) for g in dictionary.representatives];return v


def dictionary_from_record(value):
    v=dict(value);v['representatives']=tuple(graph_from_record(g) for g in v['representatives']);v['memberships']=tuple(tuple(x) for x in v['memberships']);v['training_graph_hashes']=tuple(v['training_graph_hashes']);v['hierarchy']=tuple(v['hierarchy'])
    result=Dictionary(**v)
    if dictionary_hash(result)!=result.identity:raise ValueError('dictionary artifact identity mismatch')
    return result

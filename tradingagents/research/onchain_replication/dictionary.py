"""Average-linkage motif dictionaries with deterministic medoids and partitions."""
from __future__ import annotations
from dataclasses import dataclass,replace
import numpy as np
from scipy.cluster.hierarchy import linkage,cut_tree
from scipy.spatial.distance import squareform
from .cache import cache_key
from .provenance import freeze
from .matching_reference import match_reference


def cluster_medoids(distance,k):
    distance=np.asarray(distance,dtype=float)
    n=len(distance)
    if distance.shape!=(n,n) or not 1<=k<=n or not np.isfinite(distance).all() or (distance<0).any() or not np.allclose(distance,distance.T):raise ValueError('invalid clustering distance')
    if n==k:groups=[[i] for i in range(n)]
    elif k==1:groups=[list(range(n))]
    else:
        tree=linkage(squareform(distance,checks=True),method='average')
        labels=cut_tree(tree,n_clusters=k).reshape(-1)
        groups=[list(np.flatnonzero(labels==label).astype(int)) for label in sorted(set(labels))]
    centers=[group[int(np.argmin(distance[np.ix_(group,group)].sum(1)))] for group in groups]
    order=np.argsort(centers)
    return [centers[i] for i in order],[groups[i] for i in order]


def _distance(graphs,config):
    n=len(graphs);distance=np.zeros((n,n),dtype=np.float64)
    for i in range(n):
        for j in range(i):
            similarity=(match_reference(graphs[i],graphs[j],config).score+match_reference(graphs[j],graphs[i],config).score)/2
            distance[i,j]=distance[j,i]=1-similarity
    return distance


@dataclass(frozen=True)
class Dictionary:
    representatives: tuple
    memberships: tuple
    sample_hash: str
    training_graph_hashes: tuple[str, ...]
    config: dict
    matching_config_hash: str
    identity: str
    hierarchy: tuple

    def __post_init__(self):
        object.__setattr__(self,'config',freeze(self.config))
        object.__setattr__(self,'hierarchy',freeze(self.hierarchy))


def fit_dictionary(samples,matching_config,dictionary_config):
    k=dictionary_config['size'];graphs=samples.graphs
    if len(graphs)<k:raise ValueError('insufficient dictionary samples')
    rng=np.random.Generator(np.random.PCG64(samples.seed));hierarchy=[]
    def fit(indices,owners):
        indices=sorted(indices) # original sample order controls linkage/medoid ties
        if len(indices)>dictionary_config['partition_threshold']:
            chunk=dictionary_config['partition_size']
            if chunk<=k:raise ValueError('partition fails to reduce sample set')
            shuffled=list(rng.permutation(indices));representatives=[];next_owners={}
            for start in range(0,len(shuffled),chunk):
                part=sorted(map(int,shuffled[start:start+chunk]))
                centers,groups=cluster_medoids(_distance([graphs[i] for i in part],matching_config),min(k,len(part)))
                selected=[part[i] for i in centers]
                expanded=[sorted(j for i in group for j in owners[part[i]]) for group in groups]
                representatives.extend(selected);next_owners.update(zip(selected,expanded,strict=True))
                hierarchy.append({'samples':part,'representatives':selected,'original_memberships':expanded})
            return fit(representatives,next_owners)
        centers,groups=cluster_medoids(_distance([graphs[i] for i in indices],matching_config),k)
        return [indices[i] for i in centers],[sorted(j for i in group for j in owners[indices[i]]) for group in groups]
    centers,groups=fit(list(range(len(graphs))),{i:[i] for i in range(len(graphs))})
    dictionary=Dictionary(tuple(graphs[i] for i in centers),tuple(tuple(x) for x in groups),samples.identity,samples.source_hashes,dict(dictionary_config),cache_key(matching_config),'',tuple(hierarchy))
    return replace(dictionary,identity=dictionary_hash(dictionary))


def dictionary_hash(dictionary):
    graphs=[{'nodes':g.node_ids,'node_features':g.node_features.tolist(),'edge_index':g.edge_index.tolist(),'edge_features':g.edge_features.tolist(),'parent_hash':g.parent_hash,'center_id':g.center_id} for g in dictionary.representatives]
    return cache_key({'graphs':graphs,'sample_hash':dictionary.sample_hash,'training_graph_hashes':dictionary.training_graph_hashes,'config':dictionary.config,'matching_hash':dictionary.matching_config_hash,'memberships':dictionary.memberships,'hierarchy':dictionary.hierarchy})


def reorder_dictionary(dictionary,order):
    if sorted(order)!=list(range(len(dictionary.representatives))):raise ValueError('invalid dictionary permutation')
    result=replace(dictionary,representatives=tuple(dictionary.representatives[i] for i in order),memberships=tuple(dictionary.memberships[i] for i in order))
    return replace(result,identity=dictionary_hash(result))

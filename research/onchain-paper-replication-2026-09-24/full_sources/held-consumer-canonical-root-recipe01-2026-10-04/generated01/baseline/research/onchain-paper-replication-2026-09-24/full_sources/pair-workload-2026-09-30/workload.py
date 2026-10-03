"""Exact scalar dictionary/MCM callback workloads; NOT empirical admission.

Purposes are derived inside the actual algorithm, not accepted from a caller.
The callback must durably publish or reuse an exact completed score before it
returns. Its reply binds the purpose; this module does not prove that publication,
ResearchRun ownership, ancestry, array integrity, quotas or orphan reconciliation.
Replay starts from the original seed and asks the same completed-pair references;
only the admitted callback may decide whether to compute, resume or reuse them.
"""
from dataclasses import replace
import math
import numpy as np
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.dictionary import Dictionary,cluster_medoids,dictionary_hash
from tradingagents.research.onchain_replication.neighborhoods import SampleManifest,NeighborhoodIndex,graph_hash,node_order_hash
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.matching_pair import BACKEND,hash_string
from tradingagents.research.onchain_replication.provenance import thaw


def require(value,message):
    if not value:raise ValueError(message)


def common(workflow,backend,max_entries,callback):
    hash_string(workflow)
    require(cache_key(backend)==cache_key(BACKEND),'explicit scalar backend required')
    require(type(max_entries) is int and max_entries>0,'positive matrix capacity required')
    require(callable(callback),'explicit completed-pair callback required')


def score(callback,purpose,a,b):
    expected=cache_key(purpose)
    # Each purpose has an independent callback copy. Mutation cannot redefine
    # the expected key or later requests in this deterministic workload.
    result=callback(thaw(purpose),a,b)
    require(isinstance(result,dict) and set(result)=={'purpose_sha256','score'}
            and result['purpose_sha256']==expected,'completed score purpose differs')
    value=result['score']
    require(type(value) in (float,int) and math.isfinite(value),'finite scalar score required')
    require(0. <= value <= 1.,'scalar similarity range differs')
    return float(value)


def fit(samples,matching_config,dictionary_config,*,workflow,backend,max_entries,score_pair):
    common(workflow,backend,max_entries,score_pair)
    require(isinstance(samples,SampleManifest),'actual sample manifest required')
    settings=dict(dictionary_config)
    require('pair_execution' not in settings,'unmodified sampling configuration required')
    for field in ('size','sample_count','partition_threshold','partition_size'):
        require(type(settings.get(field)) is int and settings[field]>0,'positive dictionary configuration required')
    k=settings['size'];graphs=samples.graphs;n=len(graphs)
    require(n==settings['sample_count'] and n>=k and len(samples.records)==n,'sample membership dimensions')
    require(settings['partition_threshold']>=k and settings['partition_size']>k,'partition must reduce samples')
    require(cache_key({'training_graphs':samples.source_hashes,'config':settings,'seed':samples.seed,
                      'records':samples.records,'rng_state':samples.rng_state})==samples.identity,'sample identity differs')
    typed=[]
    for g,record in zip(graphs,samples.records,strict=True):
        require(g.parent_hash in samples.source_hashes and record['graph_hash']==g.parent_hash
                and record['center_id']==g.center_id and record['node_count']==len(g.node_ids)
                and record['edge_count']==g.edge_index.shape[1],'sample graph/record membership differs')
        typed.append(graph_identity(g))
    numerical=cache_key({'config':matching_config,'backend':backend})
    scope=cache_key({'schema_version':1,'kind':'dictionary','workflow':workflow,'backend':backend,
        'sample':samples.identity,'typed_sample_graphs':typed,'matching':matching_config,
        'dictionary':settings,'seed':samples.seed})
    matrices={};blocks=[];hierarchy=[];used=0
    rng=np.random.Generator(np.random.PCG64(samples.seed))
    def distances(indices,owners,stage):
        nonlocal used
        key=tuple(indices)
        block={'indices':indices,'owners':[[i,owners[i]] for i in indices],
               'stage':stage,'rng_state':rng.bit_generator.state,'hierarchy_prefix':hierarchy}
        block_hash=cache_key(block)
        # Like the scalar dictionary oracle, an identical ordered subset shares
        # its complete matrix. No extra matching occurrence is invented.
        if key in matrices:return matrices[key]
        count=len(indices);require(used+count*count<=max_entries,'dictionary matrix capacity exceeded')
        used+=count*count;matrix=np.zeros((count,count),dtype=np.float64)
        for i in range(count):
            for j in range(i):
                values=[]
                for left,right in ((indices[i],indices[j]),(indices[j],indices[i])):
                    purpose={'schema_version':1,'kind':'dictionary','workload_sha256':scope,
                        'block_sha256':block_hash,'sample_indices':[left,right],
                        'typed_graphs':[typed[left],typed[right]]}
                    values.append(score(score_pair,purpose,graphs[left],graphs[right]))
                matrix[i,j]=matrix[j,i]=1-(values[0]+values[1])/2
        matrices[key]=matrix;blocks.append({'indices':list(indices),'block_sha256':block_hash,'matrix':matrix})
        return matrix
    def reduce(indices,owners,level):
        indices=sorted(indices)
        if len(indices)>settings['partition_threshold']:
            shuffled=list(rng.permutation(indices));representatives=[];next_owners={}
            for start in range(0,len(shuffled),settings['partition_size']):
                part=sorted(map(int,shuffled[start:start+settings['partition_size']]))
                centers,groups=cluster_medoids(distances(part,owners,{'level':level,'partition_start':start}),min(k,len(part)))
                selected=[part[i] for i in centers]
                expanded=[sorted(j for i in group for j in owners[part[i]]) for group in groups]
                representatives.extend(selected);next_owners.update(zip(selected,expanded,strict=True))
                hierarchy.append({'samples':part,'representatives':selected,'original_memberships':expanded})
            require(len(representatives)<len(indices),'partition fails to reduce samples')
            return reduce(representatives,next_owners,level+1)
        centers,groups=cluster_medoids(distances(indices,owners,{'level':level,'partition_start':None}),k)
        return [indices[i] for i in centers],[sorted(j for i in group for j in owners[indices[i]]) for group in groups]
    centers,groups=reduce(list(range(n)),{i:[i] for i in range(n)},0)
    d=Dictionary(tuple(graphs[i] for i in centers),tuple(tuple(x) for x in groups),samples.identity,
        samples.source_hashes,settings|{'pair_execution':dict(backend)},numerical,'',tuple(hierarchy))
    return {'dictionary':replace(d,identity=dictionary_hash(d)),'matrices':blocks,'workload_sha256':scope,
            'empirical_admission_verified':False}


def mcm(graph,dictionary,matching_config,*,workflow,backend,max_entries,score_pair):
    common(workflow,backend,max_entries,score_pair)
    require(dictionary_hash(dictionary)==dictionary.identity,'dictionary identity differs')
    require(cache_key(dictionary.config.get('pair_execution'))==cache_key(backend),'dictionary scalar backend differs')
    require(dictionary.matching_config_hash==cache_key({'config':matching_config,'backend':backend}),'dictionary matching differs')
    n=len(graph.node_ids);motifs=dictionary.representatives
    require(n>0 and len(motifs)>0 and n*len(motifs)<=max_entries,'MCM matrix capacity exceeded')
    typed=[graph_identity(motif) for motif in motifs]
    parent=graph_hash(graph)
    scope=cache_key({'schema_version':1,'kind':'mcm','workflow':workflow,'backend':backend,
        'graph':parent,'node_order':node_order_hash(graph.node_ids),'dictionary':dictionary.identity,
        'ordered_motifs':typed,'matching':matching_config,'dtype':'float32'})
    result=np.empty((n,len(motifs)),dtype=np.float32)
    index=NeighborhoodIndex(graph)
    for center in range(n):
        local=index.neighborhood(center,dictionary.config);local_id=graph_identity(local)
        for motif,m in enumerate(motifs):
            purpose={'schema_version':1,'kind':'mcm','workload_sha256':scope,'graph_hash':parent,
                'center_index':center,'center_id':graph.node_ids[center],'motif_index':motif,
                'typed_graphs':[local_id,typed[motif]]}
            # The journal's exact completed-pair map is the validity mask. An
            # absent result never becomes numerical zero; allocation is returned
            # only after all cells have explicit completed results.
            result[center,motif]=score(score_pair,purpose,local,m)
    return result

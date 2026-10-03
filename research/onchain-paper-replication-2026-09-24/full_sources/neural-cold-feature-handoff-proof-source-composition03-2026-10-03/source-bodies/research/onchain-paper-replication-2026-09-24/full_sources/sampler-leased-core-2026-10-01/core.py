"""Leased resident sampling with per-draw evidence, not a durable producer.

Derived from neighborhoods.sample_neighborhoods. The frozen selection/RNG/overlap
semantics are unchanged. Callers must own immutable inputs, enforce a process
guard, durably reserve attempts and publish checkpoints; this has no resume API.
The direct weight limit covers weights/probability, NOT NumPy choice scratch/RSS.
"""
from contextlib import ExitStack
import numpy as np
from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash,SampleManifest
from tradingagents.research.onchain_replication.neighborhood_policy import validate_neighborhood_policy,open_array_index,sample_array_bytes
from tradingagents.research.onchain_replication.contracts import validate_graph
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.provenance import utc,freeze,thaw

def require(value,message):
    if not value:raise ValueError(message)

def sample(graphs,config,seed,*,policy,lease,checkpoint):
    require(callable(lease) and callable(checkpoint),'mandatory lease and checkpoint callbacks required')
    require(isinstance(policy,dict) and set(policy)=={'schema_version','max_centers','max_direct_weight_bytes','neighborhood'}
        and type(policy['schema_version']) is int and policy['schema_version']==1,'sampler policy schema differs')
    require(all(type(policy[k]) is int and policy[k]>0 for k in ('max_centers','max_direct_weight_bytes')),'positive sampler bounds required')
    neighborhood=validate_neighborhood_policy(policy['neighborhood'])
    require(neighborhood is not None,'bounded array-neighborhood policy required')
    require(type(seed) is int and seed>=0,'nonnegative integer seed required')
    config=thaw(config)
    require(type(config.get('sample_count')) is int and config['sample_count']>0,'positive sample count required')
    require(type(config.get('hop_depth')) is int and config['hop_depth']>=0
        and type(config.get('maximum_neighborhood_nodes')) is int and config['maximum_neighborhood_nodes']>0,'neighborhood configuration differs')
    start,end=utc(config['train_start']),utc(config['train_end'])
    require(start<end,'training interval differs');lease()
    training=[]
    for g in graphs:
        if utc(g.start_utc)>=start and utc(g.available_at)<end:
            validate_graph(g);training.append(g)
    training.sort(key=lambda g:(g.start_utc,g.asset,graph_hash(g)))
    hashes=tuple(graph_hash(g) for g in training)
    require(len(set(hashes))==len(hashes),'duplicate training graph')
    total=sum(len(g.node_ids) for g in training)
    require(config['sample_count']<=total<=policy['max_centers'],'training center capacity differs')
    require(16*total<=policy['max_direct_weight_bytes'],'direct weight array allowance exceeded')
    lease()
    offsets=np.cumsum([0]+[len(g.node_ids) for g in training])
    weights=np.ones(total,dtype=np.float64)
    rng=np.random.Generator(np.random.PCG64(seed));records=[];samples=[]
    active=None;index=None;retained=0;previous=None
    with ExitStack() as stack:
        for draw in range(config['sample_count']):
            lease();before=thaw(rng.bit_generator.state)
            probability=weights/weights.sum()
            chosen=int(rng.choice(total,p=probability));chosen_probability=float(probability[chosen])
            del probability # Never retain the preceding probability at the next draw.
            gi=int(np.searchsorted(offsets,chosen,side='right')-1);center=chosen-int(offsets[gi])
            g=training[gi]
            if gi!=active:
                stack.close();lease()
                index=stack.enter_context(open_array_index(g,neighborhood));active=gi
            sub=index.neighborhood(center,config)
            retained+=sample_array_bytes(sub)
            require(retained<=neighborhood['max_sample_array_bytes'],'retained sample array allowance exceeded')
            record={'graph_hash':hashes[gi],'center_id':g.node_ids[center],'center_index':center,
                'probability':chosen_probability,'node_count':len(sub.node_ids),'edge_count':sub.edge_index.shape[1]}
            samples.append(sub);records.append(record);weights[chosen]=0
            selected=np.asarray(index.selected(center,config),dtype=np.int64)
            weights[int(offsets[gi])+selected]*=.5
            event={'schema_version':1,'index':draw,'previous_sha256':previous,
                'training_graphs':hashes,'configuration_sha256':cache_key(config),'seed':seed,
                'numpy':np.__version__,'bit_generator':'PCG64','rng_before':before,
                'rng_after':thaw(rng.bit_generator.state),'record':record,
                'selected_indices_sha256':node_order_hash(selected),'retained_array_bytes':retained}
            sha=cache_key(event);lease();checkpoint(freeze(event|{'sha256':sha}));lease();previous=sha
        state=thaw(rng.bit_generator.state)
        identity=cache_key({'training_graphs':hashes,'config':config,'seed':seed,'records':records,'rng_state':state})
        lease()
        return SampleManifest(tuple(samples),tuple(records),hashes,state,seed,identity)

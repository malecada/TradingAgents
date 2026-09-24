"""Compose fixed graph representations with explicit fold and raw-graph lineage.

This pure component has no empirical admission or automatic restart. Empirical
callers must supply admitted complete graphs, a guarded job and a durable
checkpoint callback; completed representations must be reused by identity.
Trainable GAT/GIN/MLP weights remain in the temporal model, never cached here.
"""
from dataclasses import dataclass
import numpy as np
import torch
from .cache import cache_key
from .contracts import validate_graph
from .neighborhoods import graph_hash,sample_neighborhoods
from .dictionary import fit_dictionary
from .mcm import mcm_features
from .serialization import samples_to_record,dictionary_to_record
from .graph_baselines import node2vec,graphwave,watchyourstep,align_embeddings
from .evaluation import feature_hash
from .provenance import utc


@dataclass(frozen=True)
class PreparedFeatures:
    features: dict
    binding: dict
    dictionary: object = None


def prepare_features(graphs,examples,fold,arm,seed,configs,*,max_entries,checkpoint):
    if not callable(checkpoint):raise ValueError('explicit durable checkpoint callback required')
    if type(max_entries) is not int or max_entries<=0:raise ValueError('explicit resource-derived allocation ceiling required')
    if examples.fold_hash!=fold.member_hash:raise ValueError('fold membership differs')
    arms={'proposed','training_label_permutation','mcm_without_gat','gat_without_mcm','gin','node2vec','watchyourstep','graphwave'}
    if arm not in arms:raise ValueError('graph representation arm required')
    graphs=tuple(graphs);by_hash={};asset=None;weeks=set()
    for graph in graphs:
        validate_graph(graph);identity=graph_hash(graph)
        if asset is not None and graph.asset!=asset:raise ValueError('mixed asset graph population')
        asset=graph.asset
        if identity in by_hash or graph.start_utc in weeks:raise ValueError('duplicate graph population')
        if not set(graph.source_hashes)<=set(examples.source_hashes):raise ValueError('unbound graph source')
        by_hash[identity]=graph;weeks.add(graph.start_utc)
    required={h for row in (*examples.train,*examples.test) for h in row.graph_hashes}
    if not required or not required<=set(by_hash):raise ValueError('required graph membership incomplete')
    for row in (*examples.train,*examples.test):
        if len(row.graph_hashes)!=len(row.graph_available_at):raise ValueError('graph clock lineage dimensions')
        for identity,availability in zip(row.graph_hashes,row.graph_available_at,strict=True):
            if utc(by_hash[identity].available_at)!=utc(availability) or utc(availability)>utc(row.decision_at):raise ValueError('graph clock lineage differs')
    fitting_config={**configs['dictionary'],'train_start':fold.train_start,'train_end':fold.train_end}
    dictionary=None;dictionary_hash=cache_key({'component':'no_motif_dictionary','arm':arm})
    def graph_lineage(identity):
        return {'input_graph_hash':identity,'asset':by_hash[identity].asset,
        'source_hashes':list(by_hash[identity].source_hashes),'start_utc':by_hash[identity].start_utc,
        'end_utc':by_hash[identity].end_utc,'available_at':by_hash[identity].available_at,
        'node_order_hash':cache_key(by_hash[identity].node_ids),'edge_index_hash':feature_hash(by_hash[identity].edge_index)}
    lineage={identity:graph_lineage(identity) for identity in sorted(required)}
    needs_mcm=arm in {'proposed','training_label_permutation','mcm_without_gat'}
    if needs_mcm:
        samples=sample_neighborhoods(graphs,fitting_config,seed)
        checkpoint('samples_complete',{'sample_hash':samples.identity},samples_to_record(samples))
        dictionary=fit_dictionary(samples,configs['matching'],fitting_config,
            checkpoint=lambda state:checkpoint('dictionary_progress',{'sample_hash':samples.identity},state))
        dictionary_hash=dictionary.identity
        for identity in dictionary.training_graph_hashes:
            lineage.setdefault(identity,graph_lineage(identity))
        checkpoint('dictionary_complete',{'dictionary_hash':dictionary_hash},dictionary_to_record(dictionary))
    features={};prior_nodes=None;prior_vectors=None;prior_hash=None
    # Historical intermediate snapshots participate in static embedding alignment,
    # even if no scored day refers to them. Process publication order, not event
    # order: an earlier week can be published after a scored later week. This
    # makes the entire predecessor chain available at each graph's own clock.
    first=min(utc(by_hash[h].start_utc) for h in required)
    last=max(utc(by_hash[h].available_at) for h in required)
    selected=sorted(((h,g) for h,g in by_hash.items() if first<=utc(g.start_utc) and utc(g.available_at)<=last),key=lambda x:(utc(x[1].available_at),utc(x[1].start_utc),x[0]))
    alignment_order=[]
    for identity,graph in selected:
        if arm not in {'node2vec','watchyourstep'} and identity not in required:continue
        n=len(graph.node_ids)
        if not n:raise ValueError('empty admitted graph representation')
        context={'graph_hash':identity,'dictionary_hash':dictionary_hash,'fold_id':fold.id,'seed':seed,'arm':arm}
        if needs_mcm:
            if n*len(dictionary.representatives)>max_entries:raise ValueError('MCM representation capacity exceeded')
            values=mcm_features(graph,dictionary,configs['matching'],
                checkpoint=lambda cursor,prefix:checkpoint('mcm_progress',{**context,'next_node':cursor},prefix.copy()))
            feature={'mcm':torch.tensor(values,dtype=torch.float32),'edge_index':torch.tensor(np.array(graph.edge_index),dtype=torch.long)}
        elif arm in {'gin','gat_without_mcm'}:
            feature={'mcm':torch.tensor(np.array(graph.node_features),dtype=torch.float32),'edge_index':torch.tensor(np.array(graph.edge_index),dtype=torch.long)}
        else:
            config=configs['baselines']['graph'][arm]
            callback=lambda cursor,state:checkpoint('embedding_progress',{**context,'cursor':cursor},state)
            if arm=='graphwave':vectors=graphwave(graph.edge_index,n,config,max_entries=max_entries,checkpoint=callback)
            else:
                engine=node2vec if arm=='node2vec' else watchyourstep
                vectors,logs=engine(graph.edge_index,n,config,seed,max_entries=max_entries,checkpoint=callback)
                if prior_vectors is not None:vectors=align_embeddings(graph.node_ids,vectors,prior_nodes,prior_vectors)
                record=lineage.setdefault(identity,graph_lineage(identity))
                record['alignment_previous_graph_hash']=prior_hash
                record['max_basis_available_at']=graph.available_at
                if prior_hash is not None and utc(lineage[prior_hash]['max_basis_available_at'])>utc(graph.available_at):
                    raise ValueError('noncausal alignment ancestry')
                alignment_order.append(identity)
                prior_nodes=graph.node_ids;prior_vectors=vectors;prior_hash=identity
            feature=np.asarray(vectors.mean(axis=0),dtype=np.float32)
        checkpoint('graph_complete',context,feature)
        if identity in required:features[identity]=feature
    representation='motif_mcm' if needs_mcm else arm
    binding={'schema_version':2,'representation':representation,'asset':asset,'fold_id':fold.id,
        'fold_hash':examples.fold_hash,'train_hash':examples.train_hash,'seed':seed,
        'dictionary_hash':dictionary_hash,'dictionary_training_graph_hashes':[] if dictionary is None else list(dictionary.training_graph_hashes),
        'configuration_hash':cache_key({'dictionary':fitting_config,'matching':configs['matching'],'baselines':configs['baselines']}),
        'feature_hashes':{h:feature_hash(value) for h,value in features.items()},'lineage':lineage,
        'alignment_order':alignment_order,'alignment_order_policy':'available_at,start_utc,graph_hash; start at earliest required event week'}
    checkpoint('representation_complete',{'binding_hash':cache_key(binding)},binding)
    return PreparedFeatures(features,binding,dictionary)

"""Compose fixed graph representations with explicit fold and raw-graph lineage.

This pure component has no empirical admission or automatic restart. Empirical
callers must supply admitted complete graphs, a guarded job and a durable
checkpoint callback; completed representations must be reused by identity.
Trainable GAT/GIN/MLP weights remain in the temporal model, never cached here.
"""
from dataclasses import dataclass,asdict
import numpy as np
import torch
from .cache import cache_key
from .contracts import validate_graph
from .neighborhoods import graph_hash,sample_neighborhoods
from .dictionary import fit_dictionary
from .mcm import mcm_features
from .serialization import samples_to_record,dictionary_to_record,samples_from_record,dictionary_from_record
from .graph_baselines import node2vec,graphwave,watchyourstep,align_embeddings
from .evaluation import feature_hash
from .provenance import utc


@dataclass(frozen=True)
class PreparedFeatures:
    features: dict
    binding: dict
    dictionary: object = None


def representation_arm(arm):
    """Frozen diagnostics share exactly the proposed dictionary and MCM bytes."""
    return 'proposed' if arm in {'proposed','training_label_permutation','mcm_without_gat'} else arm


def prepare_features(graphs,examples,fold,arm,seed,configs,*,max_entries,checkpoint,resume_state=None):
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
    workflow_identity=cache_key({'graph_population':sorted(by_hash),'required_graphs':sorted(required),
        'fold':asdict(fold),'train_hash':examples.train_hash,'arm':representation_arm(arm),'seed':seed,'configs':configs})
    resume_state=resume_state or {'identity':workflow_identity}
    if resume_state.get('identity') is None and set(resume_state)<={'identity','completed_graphs','graph_progress'} and not resume_state.get('completed_graphs') and not resume_state.get('graph_progress'):
        resume_state={'identity':workflow_identity}
    if resume_state.get('identity')!=workflow_identity:raise ValueError('representation checkpoint identity differs')
    emit=checkpoint
    checkpoint=lambda stage,context,payload:emit(stage,{'workflow_identity':workflow_identity,**context},payload)
    dictionary=None;dictionary_hash=cache_key({'component':'no_motif_dictionary','arm':arm})
    def graph_lineage(identity):
        return {'input_graph_hash':identity,'asset':by_hash[identity].asset,
        'source_hashes':list(by_hash[identity].source_hashes),'start_utc':by_hash[identity].start_utc,
        'end_utc':by_hash[identity].end_utc,'available_at':by_hash[identity].available_at,
        'node_order_hash':cache_key(by_hash[identity].node_ids),'edge_index_hash':feature_hash(by_hash[identity].edge_index)}
    lineage={identity:graph_lineage(identity) for identity in sorted(required)}
    needs_mcm=arm in {'proposed','training_label_permutation','mcm_without_gat'}
    if needs_mcm:
        if 'samples' in resume_state:samples=samples_from_record(resume_state['samples'])
        else:
            samples=sample_neighborhoods(graphs,fitting_config,seed)
            checkpoint('samples_complete',{'sample_hash':samples.identity},samples_to_record(samples))
        if 'dictionary' in resume_state:dictionary=dictionary_from_record(resume_state['dictionary'])
        else:
            dictionary=fit_dictionary(samples,configs['matching'],fitting_config,
                resume_state=resume_state.get('dictionary_progress'),
                checkpoint=lambda state:checkpoint('dictionary_progress',{'sample_hash':samples.identity},state))
            checkpoint('dictionary_complete',{'dictionary_hash':dictionary.identity},dictionary_to_record(dictionary))
        if dictionary.sample_hash!=samples.identity:raise ValueError('resumed dictionary sample differs')
        dictionary_hash=dictionary.identity
        for identity in dictionary.training_graph_hashes:
            lineage.setdefault(identity,graph_lineage(identity))
    features={};prior_nodes=None;prior_vectors=None;prior_hash=None
    # Historical intermediate snapshots participate in static embedding alignment,
    # even if no scored day refers to them. Process publication order, not event
    # order: an earlier week can be published after a scored later week. This
    # makes the entire predecessor chain available at each graph's own clock.
    first=min(utc(by_hash[h].start_utc) for h in required)
    last=max(utc(by_hash[h].available_at) for h in required)
    selected=sorted(((h,g) for h,g in by_hash.items() if first<=utc(g.start_utc) and utc(g.available_at)<=last),key=lambda x:(utc(x[1].available_at),utc(x[1].start_utc),x[0]))
    completed_ids=set(resume_state.get('completed_graphs',{}))
    selected_ids=[h for h,g in selected if arm in {'node2vec','watchyourstep'} or h in required]
    if not completed_ids<=set(selected_ids):raise ValueError('resumed graph population differs')
    if arm in {'node2vec','watchyourstep'} and completed_ids!=set(selected_ids[:len(completed_ids)]):raise ValueError('alignment recovery requires a complete causal prefix')
    alignment_order=[]
    for identity,graph in selected:
        if arm not in {'node2vec','watchyourstep'} and identity not in required:continue
        n=len(graph.node_ids)
        if not n:raise ValueError('empty admitted graph representation')
        context={'graph_hash':identity,'dictionary_hash':dictionary_hash,'fold_id':fold.id,'seed':seed,'arm':arm}
        completed=resume_state.get('completed_graphs',{}).get(identity)
        progress=resume_state.get('graph_progress',{}).get(identity,{})
        vectors=None
        if completed is not None:
            feature=completed['feature'];vectors=completed.get('aligned_vectors')
            if arm in {'node2vec','watchyourstep'}:
                if vectors is None and identity!=selected_ids[len(completed_ids)-1]:pass
                else:
                    if vectors is None or vectors.shape!=(n,configs['baselines']['graph'][arm]['dimensions']) or not np.isfinite(vectors).all():raise ValueError('resumed alignment dimensions')
                    if not np.array_equal(feature,np.asarray(vectors.mean(0),dtype=np.float32)):raise ValueError('resumed alignment readout differs')
        elif needs_mcm:
            if n*len(dictionary.representatives)>max_entries:raise ValueError('MCM representation capacity exceeded')
            output=None;cursor=0
            if 'mcm' in progress:
                cursor=progress['next_node'];prefix=progress['mcm']
                if type(cursor) is not int or not 0<=cursor<=n or prefix.shape!=(cursor,len(dictionary.representatives)) or prefix.dtype!=np.float32 or not np.isfinite(prefix).all():raise ValueError('resumed MCM dimensions/cursor')
                output=np.zeros((n,len(dictionary.representatives)),dtype=np.float32);output[:cursor]=prefix
            values=mcm_features(graph,dictionary,configs['matching'],
                output=output,start_node=cursor,
                checkpoint=lambda cursor,prefix:checkpoint('mcm_progress',{**context,'next_node':cursor},prefix.copy()))
            feature={'mcm':torch.tensor(values,dtype=torch.float32),'edge_index':torch.tensor(np.array(graph.edge_index),dtype=torch.long)}
        elif arm in {'gin','gat_without_mcm'}:
            feature={'mcm':torch.tensor(np.array(graph.node_features),dtype=torch.float32),'edge_index':torch.tensor(np.array(graph.edge_index),dtype=torch.long)}
        else:
            config=configs['baselines']['graph'][arm]
            callback=lambda cursor,state:checkpoint('embedding_progress',{**context,'cursor':cursor},state)
            if arm=='graphwave':vectors=graphwave(graph.edge_index,n,config,max_entries=max_entries,checkpoint=callback,resume_state=progress.get('embedding'))
            else:
                engine=node2vec if arm=='node2vec' else watchyourstep
                vectors,logs=engine(graph.edge_index,n,config,seed,max_entries=max_entries,checkpoint=callback,resume_state=progress.get('embedding'))
                if prior_vectors is not None:vectors=align_embeddings(graph.node_ids,vectors,prior_nodes,prior_vectors)
            feature=np.asarray(vectors.mean(axis=0),dtype=np.float32)
        if arm in {'node2vec','watchyourstep'}:
            record=lineage.setdefault(identity,graph_lineage(identity))
            record['alignment_previous_graph_hash']=prior_hash
            record['max_basis_available_at']=graph.available_at
            if prior_hash is not None and utc(lineage[prior_hash]['max_basis_available_at'])>utc(graph.available_at):raise ValueError('noncausal alignment ancestry')
            alignment_order.append(identity)
            prior_nodes=graph.node_ids;prior_vectors=vectors;prior_hash=identity
        if completed is None:checkpoint('graph_complete',context,{'feature':feature,'aligned_vectors':vectors if arm in {'node2vec','watchyourstep'} else None})
        if identity in required:features[identity]=feature
    representation='motif_mcm' if needs_mcm else arm
    binding={'schema_version':3,'workflow_identity':workflow_identity,'representation':representation,'asset':asset,'fold_id':fold.id,
        'fold_hash':examples.fold_hash,'train_hash':examples.train_hash,'seed':seed,
        'dictionary_hash':dictionary_hash,'dictionary_training_graph_hashes':[] if dictionary is None else list(dictionary.training_graph_hashes),
        'configuration_hash':cache_key({'dictionary':fitting_config,'matching':configs['matching'],'baselines':configs['baselines']}),
        'feature_hashes':{h:feature_hash(value) for h,value in features.items()},'lineage':lineage,
        'alignment_order':alignment_order,'alignment_order_policy':'available_at,start_utc,graph_hash; start at earliest required event week'}
    checkpoint('representation_complete',{'binding_hash':cache_key(binding)},binding)
    return PreparedFeatures(features,binding,dictionary)

"""Durable representation events; loading never authorizes empirical continuation."""
from pathlib import Path
import json
from .component_store import save_component,load_component
from .provenance import file_hash,durable_mkdir,sync_directory,canonical_bytes,require_hash,utc
from .cache import cache_key
from ..lifecycle import _immutable

STAGES={'samples_complete','dictionary_progress','dictionary_complete','mcm_progress',
        'embedding_progress','graph_complete','representation_complete'}


def required_set(values):
    values=tuple(values)
    if not values or len(values)!=len(set(values)):raise ValueError('nonempty unique required graph set needed')
    for value in values:require_hash(value)
    return sorted(values)


def array_bytes(value):
    """Retained numeric payload only; Python/JSON/temporary memory needs the guard."""
    import numpy as np
    import torch
    if isinstance(value,np.ndarray):return value.nbytes
    if isinstance(value,torch.Tensor):return value.numel()*value.element_size()
    if isinstance(value,dict):return sum(array_bytes(x) for x in value.values())
    if isinstance(value,(list,tuple)):return sum(map(array_bytes,value))
    return 0


class FeatureJournal:
    def __init__(self,directory,owner,*,required_graphs,parent=None):
        self.directory=Path(directory);durable_mkdir(self.directory.parent)
        self.required=required_set(required_graphs)
        self.parent=parent
        inherited_identity=None
        if parent is not None:
            prior=Path(parent['path'])
            if not prior.is_absolute() or prior.name!='failed.json' or prior.parent.parent.resolve()!=self.directory.parent.resolve() or file_hash(prior)!=parent['sha256']:raise ValueError('journal successor requires pinned failed sibling')
            metadata=json.loads(prior.read_bytes())
            if metadata['status']!='failed' or canonical_bytes(metadata['owner'])!=canonical_bytes(parent['owner']) or metadata['required_graphs']!=self.required:raise ValueError('journal parent owner/status/membership differs')
            inherited_identity=metadata['workflow_identity']
            if inherited_identity is not None:require_hash(inherited_identity)
        self.directory.mkdir(exist_ok=False);sync_directory(self.directory.parent)
        _immutable(self.directory/'owner.json',owner)
        _immutable(self.directory/'start.json',{'schema_version':1,'owner':owner,
            'required_graphs':self.required,'parent':parent,'workflow_identity':inherited_identity})
        self.owner=owner;self.records=[];self.identity=inherited_identity;self.sealed=False

    def __call__(self,stage,context,payload):
        if self.sealed or stage not in STAGES:raise ValueError('closed/unknown representation stage')
        identity=context['workflow_identity']
        if self.identity is not None and self.identity!=identity:raise ValueError('mixed representation workflow')
        self.identity=identity
        index=len(self.records)
        binding={'owner':self.owner,'stage':stage,'context':context}
        path=save_component(self.directory/f'checkpoint-{index:06d}',payload,binding)
        record={'stage':stage,'context':context,'path':str(path.relative_to(self.directory)),
                'sha256':file_hash(path),'binding':binding}
        _immutable(self.directory/f'event-{index:06d}.json',record)
        self.records.append(record)

    def seal(self,status,*,reason=None):
        if self.sealed or status not in ('complete','failed'):raise ValueError('invalid journal closure')
        if status=='complete' and (not self.records or self.records[-1]['stage']!='representation_complete'):raise ValueError('representation completion not reached')
        path=self.directory/(status+'.json')
        _immutable(path,{'schema_version':1,'status':status,'reason':reason,'owner':self.owner,
                         'workflow_identity':self.identity,'events':self.records,'parent':self.parent,
                         'required_graphs':self.required})
        self.sealed=True;return path


def read_feature_journal(path,expected_hash,expected_owner,*,required_graphs,max_array_bytes,_ancestors=()):
    """Reconstruct retained state only; caller must admit a new successor separately."""
    path=Path(path)
    if path.resolve() in _ancestors or len(_ancestors)>=8:raise ValueError('journal parent cycle/depth')
    if path.is_symlink() or file_hash(path)!=expected_hash:raise ValueError('journal manifest hash differs')
    manifest=json.loads(path.read_bytes())
    if manifest['schema_version']!=1 or manifest['status'] not in ('complete','failed') or canonical_bytes(manifest['owner'])!=canonical_bytes(expected_owner):raise ValueError('journal owner/status differs')
    required=required_set(required_graphs)
    if manifest['required_graphs']!=required:raise ValueError('journal required graph membership differs')
    state={'identity':manifest['workflow_identity'],'completed_graphs':{},'graph_progress':{}}
    binding=None
    parent=manifest.get('parent')
    if parent is not None:
        prior=Path(parent['path'])
        if not prior.is_absolute() or prior.name!='failed.json' or prior.parent.parent.resolve()!=path.parent.parent.resolve():raise ValueError('journal parent must be failed sibling')
        state,binding=read_feature_journal(prior,parent['sha256'],parent['owner'],required_graphs=required,max_array_bytes=max_array_bytes,_ancestors=(*_ancestors,path.resolve()))
        if state['identity'] is None:
            if state['completed_graphs'] or state['graph_progress']:raise ValueError('empty parent has numerical state')
            state['identity']=manifest['workflow_identity']
        if state['identity']!=manifest['workflow_identity']:raise ValueError('journal parent workflow differs')
    for i,event in enumerate(manifest['events']):
        stage=event['stage'];context=event['context']
        if stage not in STAGES or context['workflow_identity']!=state['identity']:raise ValueError('journal workflow/stage differs')
        expected={'owner':expected_owner,'stage':stage,'context':context}
        if event['path']!=f'checkpoint-{i:06d}/manifest.json' or canonical_bytes(event['binding'])!=canonical_bytes(expected):raise ValueError('journal checkpoint binding differs')
        if binding is not None and stage!='representation_complete':raise ValueError('completed numerical work cannot be repeated')
        if stage=='dictionary_progress':state.pop('dictionary_progress',None)
        if stage=='dictionary_complete':state.pop('dictionary_progress',None)
        if stage in ('mcm_progress','embedding_progress','graph_complete'):
            graph=context['graph_hash'];require_hash(graph)
            if graph in state['completed_graphs']:raise ValueError('completed graph cannot be replaced')
            state['graph_progress'].pop(graph,None)
        payload=load_component(path.parent/event['path'],event['sha256'],expected,max_array_bytes=max_array_bytes)
        if stage=='graph_complete' and payload.get('aligned_vectors') is not None:
            # Only the last completed basis is necessary to continue the causal
            # chain; old graph readouts remain. Full vector bytes stay on disk.
            for old in state['completed_graphs'].values():old['aligned_vectors']=None
        if array_bytes(state)+array_bytes(payload)>max_array_bytes:raise ValueError('retained representation array budget exceeded')
        if stage=='samples_complete':state['samples']=payload
        elif stage=='dictionary_progress':state['dictionary_progress']=payload
        elif stage=='dictionary_complete':state['dictionary']=payload
        elif stage=='mcm_progress':state['graph_progress'][context['graph_hash']]={'mcm':payload,'next_node':context['next_node']}
        elif stage=='embedding_progress':state['graph_progress'][context['graph_hash']]={'embedding':payload}
        elif stage=='graph_complete':state['completed_graphs'][context['graph_hash']]=payload
        elif stage=='representation_complete':
            if context.get('binding_hash')!=cache_key(payload):raise ValueError('final binding hash differs')
            if binding is not None and canonical_bytes(binding)!=canonical_bytes(payload):raise ValueError('publication recovery changed complete representation')
            binding=payload
    if manifest['status']=='complete' and binding is None:raise ValueError('journal completion absent')
    if binding is not None:
        from .evaluation import feature_hash
        keys={'schema_version','workflow_identity','representation','asset','fold_id','fold_hash','train_hash','seed','dictionary_hash','dictionary_training_graph_hashes','configuration_hash','feature_hashes','lineage','alignment_order','alignment_order_policy'}
        if set(binding)!=keys or binding['schema_version']!=3 or binding['workflow_identity']!=state['identity']:raise ValueError('final workflow/schema differs')
        if binding['asset'] not in ('BTC','ETH') or binding['representation'] not in ('motif_mcm','gin','gat_without_mcm','node2vec','watchyourstep','graphwave') or type(binding['seed']) is not int or binding['seed']<0:raise ValueError('final representation metadata differs')
        for name in ('workflow_identity','fold_hash','train_hash','dictionary_hash','configuration_hash'):require_hash(binding[name])
        if set(binding['feature_hashes'])!=set(required) or not set(required)<=set(state['completed_graphs']):raise ValueError('final graph closure incomplete')
        if binding['feature_hashes']!={h:feature_hash(state['completed_graphs'][h]['feature']) for h in binding['feature_hashes']}:raise ValueError('final feature hashes differ')
        if not (set(required)|set(binding['dictionary_training_graph_hashes']))<=set(binding['lineage']):raise ValueError('final input lineage incomplete')
        for h,record in binding['lineage'].items():
            if record['input_graph_hash']!=h or record['asset']!=binding['asset'] or not record['source_hashes']:raise ValueError('final raw graph lineage differs')
            for sha in (h,record['node_order_hash'],record['edge_index_hash'],*record['source_hashes']):require_hash(sha)
            if not utc(record['start_utc'])<utc(record['end_utc'])<=utc(record['available_at']):raise ValueError('final graph clocks differ')
        order=binding['alignment_order']
        if binding['representation'] in ('node2vec','watchyourstep'):
            if len(order)!=len(set(order)) or set(order)!=set(binding['lineage']):raise ValueError('final alignment closure differs')
            for i,h in enumerate(order):
                item=binding['lineage'][h]
                if item['alignment_previous_graph_hash']!=(order[i-1] if i else None) or item['max_basis_available_at']!=item['available_at']:raise ValueError('final alignment parent differs')
                if i and utc(binding['lineage'][order[i-1]]['available_at'])>utc(item['available_at']):raise ValueError('final alignment is noncausal')
        elif order:raise ValueError('unexpected alignment lineage')
        if binding['representation']=='motif_mcm':
            from .serialization import dictionary_from_record
            dictionary=dictionary_from_record(state['dictionary'])
            if dictionary.identity!=binding['dictionary_hash'] or list(dictionary.training_graph_hashes)!=binding['dictionary_training_graph_hashes']:raise ValueError('final dictionary differs')
    if file_hash(path)!=expected_hash:raise ValueError('journal changed during read')
    return state,binding

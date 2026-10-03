"""Selected current-owner saved MCM to fixed graph tensor inputs.

No graph_complete publication or empirical admission is granted here. Returned
tensors are mutable; their receipt lease checks the pinned feature identity.
"""
import importlib.util
from pathlib import Path
from types import MappingProxyType
import numpy as np
import torch
from tradingagents.research.onchain_replication.provenance import file_hash,freeze,thaw
from tradingagents.research.onchain_replication.neighborhoods import graph_hash as hash_graph,node_order_hash

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
saved=load('graph_feature_saved_mcm',HERE.parent/'mcm-artifact-route-2026-10-01/route.py')
boundary=load('graph_feature_tensor_boundary',HERE.parent/'graph-feature-boundary-2026-10-01/boundary.py')
SOURCES=tuple(sorted(set(saved.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in (__file__,boundary.__file__)}))
require=saved.require

class Features:
    __slots__=('_feature','_record','_lease','_hash','_chunk')
    def __init__(self,feature,record,lease,chunk):
        object.__setattr__(self,'_feature',MappingProxyType(dict(feature)))
        object.__setattr__(self,'_record',freeze(record));object.__setattr__(self,'_lease',lease)
        object.__setattr__(self,'_hash',record['feature_hash']);object.__setattr__(self,'_chunk',chunk)
    def __setattr__(self,name,value):raise AttributeError('feature receipt attributes are immutable')
    @property
    def feature(self):return self._feature
    @property
    def record(self):return self._record
    def _check(self):
        a=self._feature['mcm'];e=self._feature['edge_index']
        require(type(a) is torch.Tensor and type(e) is torch.Tensor and a.device.type==e.device.type=='cpu'
            and a.dtype==torch.float32 and e.dtype==torch.int64 and not a.requires_grad and not e.requires_grad,
            'fixed feature tensor properties changed')
        require(boundary.identity(a.numpy(),e.numpy(),self._chunk)==self._hash,'fixed feature tensor content changed')
    def lease(self):self._check();self._lease();self._check()


def prepare(owned,journal,*,dictionary_ticket,graph_hash,mcm_input,output_input,read_input,proof_sha256,feature_input):
    saved.actual_owner(owned,journal)
    route=owned.workload;bound=route.bound;ad=bound._run.admission
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'graph feature source differs')
    sources()
    require(route.descriptor['arm'] in ('proposed','training_label_permutation','mcm_without_gat'),'MCM feature arm required')
    require(type(graph_hash) is str and graph_hash in route.descriptor['required_graphs'] and graph_hash in route._graphs,
        'exact required graph membership needed')
    graph=route._graphs[graph_hash];require(hash_graph(graph)==graph_hash,'graph feature bytes differ')
    edges=graph.edge_index;n=len(graph.node_ids);k=route.settings['size'];order=node_order_hash(graph.node_ids)
    require(type(edges) is np.ndarray and edges.dtype==np.dtype('int64') and edges.ndim==2 and edges.shape[0]==2,
        'native graph edges required')
    require(n>0 and k>0 and n*k<=route.control['max_entries'],'graph feature entry bound exceeded')
    metadata=saved.producer.Metadata(ad.root)
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered graph feature input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(Path(bound.record['journal_directory'])/'claim.json')
    plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(bound.record['producer'])
    selected=job.get('payload',{}).get('representation_jobs',{}).get(bound.record['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('feature_tensor_input')==selected.get('feature_tensor_input')==feature_input,
        'selected graph feature policy differs')
    policy=registered(feature_input)
    require(isinstance(policy,dict) and set(policy)=={'schema_version','max_numeric_bytes','chunk_entries'}
        and type(policy['schema_version']) is int and policy['schema_version']==1
        and type(policy['max_numeric_bytes']) is int and policy['max_numeric_bytes']>0
        and type(policy['chunk_entries']) is int and 0<policy['chunk_entries']<=65536,'graph feature policy differs')
    chunk=policy['chunk_entries'];required=2*(4*n*k+edges.nbytes)+9*chunk
    require(required<=policy['max_numeric_bytes'],'graph feature numeric bound exceeded before MCM admission')
    metadata.lease();sources()
    admitted=saved.admit(owned,journal,dictionary_ticket=dictionary_ticket,graph_hash=graph_hash,
        mcm_input=mcm_input,output_input=output_input,read_input=read_input,proof_sha256=proof_sha256)
    matrix=admitted.mcm
    require(matrix.shape==(n,k) and admitted.record['node_order_sha256']==order,'admitted graph dimensions/order differ')
    expected=boundary.identity(matrix,edges,chunk)
    def lease():
        metadata.lease();sources();admitted.lease()
        require(route._graphs.get(graph_hash) is graph and graph.edge_index is edges and hash_graph(graph)==graph_hash
            and node_order_hash(graph.node_ids)==order,'graph feature prerequisite changed')
        require(boundary.identity(matrix,edges,chunk)==expected,'graph feature source identity changed')
        metadata.lease();sources()
    feature=boundary.materialize(matrix,edges,expected_hash=expected,max_numeric_bytes=policy['max_numeric_bytes'],
        chunk_entries=chunk,lease=lease)
    record={'schema_version':1,'owner':thaw(bound.record),'graph_hash':graph_hash,'node_order_sha256':order,
        'feature_hash':expected,'mcm_provenance':thaw(admitted.record),
        'tensor_policy':{'input':feature_input,'sha256':ad.inputs[feature_input]['sha256']},
        'reserved_numeric_bytes':required,'tensor_bytes':4*n*k+edges.nbytes}
    result=Features(feature,record,lease,chunk);result.lease();return result

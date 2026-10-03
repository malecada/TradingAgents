"""Actual terminal transition to lazy native CPU graph features.

The private numeric helper is not research admission. prepare calls the actual
registered seal transition exactly once; no arbitrary Receipt is accepted.
Budgets cover this call's arrays/copies/chunks and still-live original returned
tensor wrappers. Aliases/autograd storage, model state, parent graphs, Python,
stream buffers and RSS remain outside this numeric allowance.
"""
import importlib.util
from pathlib import Path
import threading
import weakref
import torch
from tradingagents.research.onchain_replication import feature_residency,feature_pipeline
from tradingagents.research.onchain_replication.provenance import file_hash,freeze,thaw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('native_map_seal',HERE/'seal.py')
seal=importlib.util.module_from_spec(spec);spec.loader.exec_module(seal)
reader=seal.reader;boundary=seal.publication.closure.graphs.boundary
require=seal.require;equal=seal.equal
SOURCES=tuple(sorted(set(seal.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in (__file__,feature_residency.__file__,feature_pipeline.__file__)}))

def policy(value):
    require(type(value) is dict and set(value)=={'schema_version','max_live_tensor_bytes','max_numeric_bytes','chunk_entries'}
        and type(value['schema_version']) is int and value['schema_version']==1
        and all(type(v) is int and v>0 for k,v in value.items() if k!='schema_version')
        and value['chunk_entries']<=65536,'native batch policy differs')
    return dict(value)

def minimum_capacity(graphs,required,motifs,settings):
    require(type(motifs) is int and motifs>0 and bool(required),'native minimum capacity population differs')
    sizes=[]
    for h in required:
        graph=graphs[h]
        require(len(graph.node_ids)>0 and graph.edge_index.ndim==2 and graph.edge_index.shape[0]==2,'native minimum capacity graph differs')
        sizes.append(4*len(graph.node_ids)*motifs+8*graph.edge_index.shape[0]*graph.edge_index.shape[1])
    largest=max(sizes)
    require(largest<=settings['max_live_tensor_bytes'] and 2*largest+9*settings['chunk_entries']<=settings['max_numeric_bytes'],
        'native single-graph capacity insufficient before sealing')

def tensor_signature(value):
    require(type(value) is torch.Tensor and value.device.type=='cpu' and value.dtype in (torch.float32,torch.int64)
        and not value.requires_grad and value.storage_offset()==0 and value.is_contiguous(),'returned tensor layout changed')
    storage=value.untyped_storage()
    return (tuple(value.shape),tuple(value.stride()),value.dtype,value.device,value.requires_grad,
        storage._cdata,storage.data_ptr(),storage.nbytes(),value.numel()*value.element_size())

class _NativeMap(feature_residency.FixedFeatureMap):
    """Private numeric adapter. Construction alone grants no research admission."""
    def __init__(self,root,references,settings,*,lease,read_lease):
        self.root=Path(root);self._policy=freeze(policy(settings));self._refs=freeze(references)
        require(bool(references) and callable(lease) and callable(read_lease),'native references and leases required')
        self._lease=lease;self._read_lease=read_lease;self._lock=threading.Lock();self._live=[];self._bytes={}
        for h,ref in references.items():
            require(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),'graph identity differs')
            require(type(ref) is dict and set(ref)=={'path','sha256','context','nodes','motifs','edge_shape','feature_hash','max_manifest_bytes','max_artifact_bytes'},'native reference schema differs')
            require(all(type(ref[k]) is int and ref[k]>0 for k in ('nodes','motifs','max_manifest_bytes','max_artifact_bytes'))
                and ref['max_manifest_bytes']<=reader.MANIFEST_LIMIT,'native reference bounds differ')
            require(type(ref['edge_shape']) is list and len(ref['edge_shape'])==2 and all(type(n) is int and n>=0 for n in ref['edge_shape'])
                and ref['edge_shape'][0]==2,'native edge shape differs')
            require(all(type(ref[k]) is str and len(ref[k])==64 and all(c in '0123456789abcdef' for c in ref[k]) for k in ('sha256','feature_hash')),'native reference hash differs')
            path=Path(ref['path']);require(path.is_absolute() and path.resolve()==path and path.is_relative_to(self.root),'native component path differs')
            self._bytes[h]=4*ref['nodes']*ref['motifs']+8*ref['edge_shape'][0]*ref['edge_shape'][1]
    def __len__(self):return len(self._refs)
    def __iter__(self):return iter(self._refs)
    def __getitem__(self,key):return self.load_batch([key])[key]
    def live_tensor_bytes(self):
        require(self._lock.acquire(blocking=False),'native batch operation already active')
        try:return self._live_tensor_bytes()
        finally:self._lock.release()
    def _live_tensor_bytes(self):
        alive=[];total=0
        for reference,signature in self._live:
            value=reference()
            if value is None:continue
            require(tensor_signature(value)==signature,'returned tensor storage/shape changed')
            total+=signature[-2];alive.append((reference,signature))
        self._live=alive;return total
    def _inspect(self,h):
        ref=self._refs[h];path=Path(ref['path'])
        manifest,_,headers,_=reader.inspect_component(path,ref['sha256'],ref['context'],self.root,
            ref['max_manifest_bytes'],ref['max_artifact_bytes'],self._bytes[h])
        def scalar(x):return {'kind':'scalar','value':x}
        tree={'kind':'dict','items':[[scalar('feature'),{'kind':'dict','items':[
            [scalar('mcm'),{'kind':'array','member':'array-000000.npy'}],
            [scalar('edge_index'),{'kind':'array','member':'array-000001.npy'}]]}],[scalar('aligned_vectors'),scalar(None)]]}
        require(equal(manifest['tree'],tree) and set(manifest['arrays'])=={'array-000000.npy','array-000001.npy'},'native feature tree differs')
        for name,shape,dtype in (('array-000000.npy',[ref['nodes'],ref['motifs']],'float32'),('array-000001.npy',list(ref['edge_shape']),'int64')):
            info=manifest['arrays'][name]
            require(info['shape']==shape and info['dtype']==dtype and headers[name][1] is False,'native shape/type/order differs')
    def _read(self,h):
        self._inspect(h);ref=self._refs[h]
        return reader.read_component(ref['path'],ref['sha256'],ref['context'],root=self.root,
            max_manifest_bytes=ref['max_manifest_bytes'],max_artifact_bytes=ref['max_artifact_bytes'],
            max_array_bytes=self._bytes[h],lease=self._read_lease)['feature']
    def load_batch(self,keys):
        require(self._lock.acquire(blocking=False),'native batch operation already active')
        result={};native=None;feature=None;success=False
        try:
            selected={}
            for h in keys:
                require(h in self._refs,'unknown native graph key');selected[h]=None
            live=self._live_tensor_bytes();sizes=[self._bytes[h] for h in selected];total=sum(sizes);scratch=9*self._policy['chunk_entries']
            require(live+total<=self._policy['max_live_tensor_bytes']
                and live+total+(max(sizes) if sizes else 0)+scratch<=self._policy['max_numeric_bytes'],
                'aggregate native batch allowance exceeded before allocation')
            self._lease();retained=0
            for h in selected:
                native=self._read(h)
                feature=boundary.materialize(native['mcm'],native['edge_index'],expected_hash=self._refs[h]['feature_hash'],
                    max_numeric_bytes=self._policy['max_numeric_bytes']-live-retained,
                    chunk_entries=self._policy['chunk_entries'],lease=self._read_lease)
                native=None;result[h]=feature;retained+=self._bytes[h]
                self._live.extend((weakref.ref(t),tensor_signature(t)) for t in feature.values());feature=None
            self._lease();require(self._live_tensor_bytes()<=live+total,'returned native payload accounting differs')
            success=True;return result
        finally:
            native=None;feature=None
            if not success:result.clear()
            self._lock.release()
    def verified_hashes(self):
        require(self._lock.acquire(blocking=False),'native batch operation already active')
        native=None
        try:
            live=self._live_tensor_bytes();scratch=9*self._policy['chunk_entries']
            require(live<=self._policy['max_live_tensor_bytes'] and live+max(self._bytes.values())+scratch<=self._policy['max_numeric_bytes'],
                'native verification allowance exceeded before allocation')
            self._lease();actual={}
            for h in self._refs:
                native=self._read(h);value=boundary.identity(native['mcm'],native['edge_index'],self._policy['chunk_entries'])
                require(value==self._refs[h]['feature_hash'],'native feature wire hash differs');actual[h]=value;native=None
            self._lease();return actual
        finally:native=None;self._lock.release()

def prepare(owned,journal,*,batch_input,**seal_arguments):
    require(set(seal_arguments)=={'examples','fold','denominator_input','dictionary_ticket','closure_input','output_input','seal_input'},'exact seal preparation arguments required')
    seal.saved.actual_owner(owned,journal);bound=owned.workload.bound;run=bound._run;ad=run.admission
    metadata=seal.producer.Metadata(ad.root)
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'native map source differs')
    sources()
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered native batch input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(Path(bound.record['journal_directory'])/'claim.json');plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(bound.record['producer']);selected=job.get('payload',{}).get('representation_jobs',{}).get(bound.record['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict) and item.get('native_feature_batch_input')==selected.get('native_feature_batch_input')==batch_input,'selected native batch policy differs')
    settings=policy(registered(batch_input));seal_policy=registered(seal_arguments['seal_input'])
    closure=registered(seal_arguments['closure_input']);output=registered(closure['graph_admission']['output_input'])
    minimum_capacity(owned.workload._graphs,owned.workload.descriptor['required_graphs'],owned.workload.settings['size'],settings)
    # No caller-supplied Receipt or callback grants admission: this is the actual
    # once-only transition. Cold/recovered terminal admission is a later route.
    terminal=seal.finish(owned,journal,**seal_arguments);terminal.lease()
    proof=metadata.read(Path(terminal.record['publication']['path']),terminal.record['publication']['sha256'],seal_policy['max_metadata_bytes'])
    binding=proof['closure']['binding'];binding_name,journal_name=seal.outputs(item,selected,ad.experiment['outputs'])
    declared=terminal.record['outputs'][binding_name]
    require(equal(metadata.read(Path(declared['path']),declared['sha256'],seal_policy['max_metadata_bytes']),binding),'native map published binding differs')
    refs={};graphs=owned.workload._graphs;motifs=owned.workload.settings['size']
    require(set(proof['closure']['graphs'])==set(binding['feature_hashes'])==set(owned.workload.descriptor['required_graphs']),'native map graph population differs')
    for h,record in proof['closure']['graphs'].items():
        event=metadata.read(Path(record['event']['path']),record['event']['sha256'],output['max_metadata_bytes']);g=graphs[h]
        require(record['feature_hash']==binding['feature_hashes'][h] and event['sha256']==record['component']['sha256'],'native map proven feature differs')
        refs[h]={'path':record['component']['path'],'sha256':record['component']['sha256'],'context':event['binding'],
            'nodes':len(g.node_ids),'motifs':motifs,'edge_shape':list(g.edge_index.shape),'feature_hash':record['feature_hash'],
            'max_manifest_bytes':output['max_manifest_bytes'],'max_artifact_bytes':output['max_artifact_bytes']}
    def lease():terminal.lease();metadata.lease();sources()
    def read_lease():run._active();bound._guard()
    result=_NativeMap(ad.root,refs,settings,lease=lease,read_lease=read_lease)
    lease();require(result.verified_hashes()==binding['feature_hashes'],'native map verified feature population differs')
    return feature_pipeline.PreparedFeatures(result,binding,None),terminal

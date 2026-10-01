"""Exclusive compact graph artifacts and current-owner saved tensor admission.

Preserves actual fixed MCM/edge values and their producer ancestry. Output
reservations cover every required graph conservatively. The resident allowance
counts source arrays, original tensor payload and one loaded payload, excluding
other parents, provenance readbacks, I/O/Python scratch, mapped pages and model
state. Repeated retained loads require outer accounting. No representation seal,
cold reuse, native dispatch or empirical release is granted here.
"""
import io as buffers
import json
import os
import sys
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch
from . import compact_features, compact_mcm, compact_samples, compact_owner, component_store
from . import score_batches as io
from .cache import cache_key
from .provenance import canonical_bytes, durable_mkdir, file_hash, freeze, thaw

require = io._require


def _owner(features): return features._mcm._dictionary._proof.owner


def directory(features):
    owner = _owner(features); bound = owner.bound.record
    return (owner.bound._run.admission.root/'research_artifacts/onchain_compact_graphs'/
        bound['workflow_identity']/bound['experiment']/features.record['graph_hash'])


def _payload(features):
    # Views only: save array nodes supported by the strict component reader.
    return {'feature':{key:features.feature[key].numpy() for key in ('mcm','edge_index')},'aligned_vectors':None}


def _original(features):
    compact_features._original(features._mcm); features._numeric()
    mcm = features._mcm; record = features.record
    require(record['graph_hash'] == mcm.record['graph_hash']
        and record['mcm_receipt_sha256'] == mcm.receipt_sha256
        and record['feature_hash'] == features._boundary_module.identity(mcm.matrix,mcm._graph.edge_index,features._chunk),
        'original compact graph feature lineage differs')


def _template(payload,context):
    arrays = {}; entries = []
    def scalar(x): return {'kind':'scalar','value':x}
    for key,dtype in (('mcm',np.dtype('float32')),('edge_index',np.dtype('int64'))):
        array = payload['feature'][key]
        require(type(array) is np.ndarray and array.dtype == dtype and array.flags.c_contiguous,
            'native compact graph array required')
        header = buffers.BytesIO()
        np.lib.format.write_array_header_1_0(header,np.lib.format.header_data_from_array_1_0(array))
        name = f'array-{len(arrays):06d}.npy'
        arrays[name] = {'sha256':'0'*64,'bytes':len(header.getvalue())+array.nbytes,
            'shape':list(array.shape),'dtype':str(array.dtype)}
        entries.append([scalar(key),{'kind':'array','member':name}])
    tree = {'kind':'dict','items':[[scalar('feature'),{'kind':'dict','items':entries}],
        [scalar('aligned_vectors'),scalar(None)]]}
    return {'schema_version':1,'context':context,'tree':tree,'arrays':arrays}


def _prepare(features,input_name):
    features._check(); _original(features)
    sources = compact_features._sources(features._mcm)
    owner = _owner(features); run = owner.bound._run; bound = owner.bound.record
    selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound['representation']]
    item = json.loads(run.read_input(selected['plan_input']))['producers'][bound['producer']]
    require(type(input_name) is str and input_name in run.admission.inputs
        and selected.get('compact_graph_output_input') == item.get('compact_graph_output_input') == input_name,
        'explicit compact graph output route differs')
    policy = json.loads(run.read_input(input_name))
    fields = {'schema_version','max_manifest_bytes','max_artifact_bytes','max_resident_array_bytes','max_workflow_output_bytes'}
    require(type(policy) is dict and set(policy) == fields
        and type(policy['schema_version']) is int and policy['schema_version'] == 1
        and all(type(policy[k]) is int and 0 < policy[k] < 2**63 for k in fields-{'schema_version'})
        and policy['max_manifest_bytes'] <= compact_samples.MANIFEST_LIMIT,'compact graph output policy differs')
    training = compact_mcm._training(features._mcm._dictionary)
    required = tuple(training.descriptor['required_graphs'])
    require(features.record['graph_hash'] in required,'required compact graph output differs')
    reserved = len(required)*(policy['max_artifact_bytes']+3*io.META_LIMIT)
    require(reserved <= policy['max_workflow_output_bytes'],'compact graph workflow output allowance exceeded')
    numeric = sum(a.nbytes for a in _payload(features)['feature'].values())
    require(numeric == features.record['tensor_bytes'] and 3*numeric <= policy['max_resident_array_bytes'],
        'compact graph source/tensor/readback payload allowance exceeded')
    start = {'schema_version':1,'kind':'compact-graph-feature','owner':owner.identity,
        'graph_hash':features.record['graph_hash'],'feature_hash':features.record['feature_hash'],
        'feature_receipt_sha256':cache_key(thaw(features.record)),
        'feature_provenance':thaw(features.record),'policy_input':input_name,
        'policy_sha256':run.admission.inputs[input_name]['sha256'],'sources':sources,
        'reserved_workflow_output_bytes':reserved,'reserved_resident_payload_bytes':3*numeric,
        'numeric_payload_bytes':numeric,'resumable':False,'representation_admitted':False}
    io._json(start)
    template = _template(_payload(features),start)
    manifest = len(canonical_bytes(template)); artifact = manifest+sum(a['bytes'] for a in template['arrays'].values())
    require(manifest <= policy['max_manifest_bytes'] and artifact <= policy['max_artifact_bytes'],
        'compact graph encoded artifact allowance exceeded before publication')
    proof = start | {'encoded_manifest_bytes':manifest,'encoded_artifact_bytes':artifact}
    io._json(proof | {'start_sha256':'0'*64,'artifact_sha256':'0'*64})
    return policy,start,proof


class Published:
    def __init__(self,features,policy,start,record,root,inode,reference,reader):
        self._features = self._authority = features; self._policy = freeze(policy)
        self._start = freeze(start); self._record = freeze(record); self._directory = root
        self._inode = inode; self._reference = reference; self._reader = reader
        self._pin = cache_key(self._configuration())
    record = property(lambda self:self._record)
    directory = property(lambda self:self._directory)
    receipt_sha256 = property(lambda self:self._reference)
    def _configuration(self):
        return {'policy':thaw(self._policy),'start':thaw(self._start),'record':thaw(self.record),
            'directory':str(self.directory),'inode':self._inode,'reference':self._reference}
    def _integrity(self):
        require(self._features is self._authority and cache_key(self._configuration()) == self._pin,
            'compact graph artifact view changed')
        require(self.record['feature_receipt_sha256'] == cache_key(thaw(self._features.record)),
            'original feature receipt changed')
    def lease(self):
        self._integrity(); self._features.lease(); self._integrity()
    def _evidence(self):
        self._integrity(); root,fd = io._open(self.directory)
        try:
            info = os.fstat(fd); require((info.st_dev,info.st_ino) == self._inode,'compact graph attempt inode changed')
            names = {'start.json','artifact','complete.json'}
            compact_owner.entries(root,names,required=names)
            require(io._read(fd,'start.json',io.META_LIMIT) == io._json(thaw(self._start)), 'compact graph start changed')
            raw = io._read(fd,'complete.json',io.META_LIMIT)
            require(io._hash(raw) == self.receipt_sha256 and raw == io._json(thaw(self.record)), 'compact graph completion changed')
            args = (root/'artifact/manifest.json',self.record['artifact_sha256'],thaw(self._start))
            manifest,_,headers,_ = self._reader.inspect_component(*args,root,
                self._policy['max_manifest_bytes'],self._policy['max_artifact_bytes'],self.record['numeric_payload_bytes'])
            expected = _template(_payload(self._features),thaw(self._start))
            require(set(manifest['arrays']) == set(expected['arrays']),'compact graph array membership differs')
            for name in expected['arrays']:
                expected['arrays'][name]['sha256'] = manifest['arrays'][name]['sha256']
                require(headers[name][1] is False,'compact graph array order differs')
            require(canonical_bytes(manifest) == canonical_bytes(expected),'compact graph tree or descriptors differ')
            size = (root/'artifact/manifest.json').stat().st_size
            require(size == self.record['encoded_manifest_bytes']
                and size+sum(a['bytes'] for a in manifest['arrays'].values()) == self.record['encoded_artifact_bytes'],
                'compact graph encoded size differs')
            io._root(root,fd); return args
        finally: io._cleanup((lambda:os.close(fd),))
    def _check(self):
        self._features._check(); compact_features._sources(self._features._mcm)
        self.lease(); _original(self._features); self._evidence()
    def check(self):
        owner = _owner(self._features)
        require(owner._transition.acquire(blocking=False),'concurrent compact graph check')
        try:self._check()
        finally:owner._transition.release()
    def _load(self):
        self._check(); args = self._evidence()
        payload = self._reader.read_component(*args,root=self.directory,
            max_manifest_bytes=self._policy['max_manifest_bytes'],max_artifact_bytes=self._policy['max_artifact_bytes'],
            max_array_bytes=self.record['numeric_payload_bytes'],lease=self.lease)
        self.lease(); _original(self._features)
        compact_samples._equal_numeric(payload,_payload(self._features)); self._evidence()
        tensors = {k:torch.from_numpy(a) for k,a in payload['feature'].items()}
        result = Loaded(self,tensors)
        result.lease(); _original(self._features); self._evidence(); result._numeric()
        return result
    def load(self):
        owner = _owner(self._features)
        require(owner._transition.acquire(blocking=False),'concurrent compact graph load')
        try:return self._load()
        finally:owner._transition.release()


class Loaded:
    __slots__ = ('_published','_feature','_record')
    def __init__(self,published,tensors):
        object.__setattr__(self,'_published',published)
        object.__setattr__(self,'_feature',MappingProxyType(tensors))
        object.__setattr__(self,'_record',freeze({'schema_version':1,'graph_receipt_sha256':published.receipt_sha256,
            'graph_directory':str(published.directory),'feature_hash':published.record['feature_hash'],
            'graph_hash':published.record['graph_hash'],'representation_admitted':False}))
    def __setattr__(self,name,value):raise AttributeError('saved graph receipt attributes are immutable')
    feature = property(lambda self:self._feature)
    record = property(lambda self:self._record)
    def _numeric(self):
        f = self._published._features
        require(self.record['graph_receipt_sha256'] == self._published.receipt_sha256,'saved graph authority changed')
        for key,dtype in (('mcm',torch.float32),('edge_index',torch.int64)):
            t = self.feature[key]
            require(type(t) is torch.Tensor and t.dtype == dtype and t.device.type == 'cpu'
                and not t.requires_grad and t.is_contiguous(),'saved graph tensor properties changed')
        require(f._boundary_module.identity(self.feature['mcm'].numpy(),self.feature['edge_index'].numpy(),f._chunk)
            == f.record['feature_hash'],'saved graph feature bytes changed')
    def lease(self):
        self._numeric(); self._published.lease(); self._numeric()
    def check(self):
        owner = _owner(self._published._features)
        require(owner._transition.acquire(blocking=False),'concurrent saved graph check')
        try:
            self._published._check(); self.lease(); _original(self._published._features)
            self._published._evidence(); self._numeric()
        finally:owner._transition.release()


def _failed(owner,root,inode):
    owner.poisoned = True
    path,fd = io._open(root)
    try:
        info = os.fstat(fd); require((info.st_dev,info.st_ino) == inode,'failed graph attempt inode changed')
        if not compact_owner.present(root/'failed.json'):
            io._write(fd,'failed.json',io._json({'schema_version':1,'status':'failed','owner':owner.identity}))
        io._root(path,fd)
    finally:io._cleanup((lambda:os.close(fd),))


def publish(features, *, input_name):
    require(type(features) is compact_features.Features,'actual compact Features required')
    owner = _owner(features)
    require(owner._transition.acquire(blocking=False),'concurrent compact graph publication')
    fd = None; claimed = False; inode = None
    try:
        policy,start,proof = _prepare(features,input_name); root = directory(features)
        require(root.is_absolute() and root.resolve() == root and not compact_owner.present(root),
            'compact graph output already claimed or redirected')
        reader = compact_samples._reader(); features.lease(); _original(features); durable_mkdir(root.parent)
        require(root.resolve() == root,'compact graph parent redirected'); features.lease()
        root.mkdir(); claimed = True; info = root.lstat(); inode = (info.st_dev,info.st_ino)
        parent,parent_fd = io._open(root.parent)
        try:os.fsync(parent_fd);io._root(parent,parent_fd)
        finally:io._cleanup((lambda:os.close(parent_fd),))
        root,fd = io._open(root); require(os.fstat(fd).st_dev == owner.root.stat().st_dev,'compact graph device differs')
        start_sha = io._write(fd,'start.json',io._json(start))
        features.lease(); _original(features); io._root(root,fd)
        require(io._read(fd,'start.json',io.META_LIMIT) == io._json(start),'compact graph start changed before write')
        path = component_store.save_component(root/'artifact',_payload(features),start)
        artifact_sha = file_hash(path)
        features.lease(); _original(features); io._root(root,fd)
        record = proof | {'start_sha256':start_sha,'artifact_sha256':artifact_sha}
        reference = io._write(fd,'complete.json',io._json(record))
        result = Published(features,policy,start,record,root,inode,reference,reader)
        # Admission compares loaded original bytes, not just a post-write hash.
        saved = result._load(); del saved
        return result
    except BaseException as primary:
        if claimed:
            try:_failed(owner,root,inode)
            except BaseException as failure:
                primary.add_note('Graph failure marker: '+repr(failure))
                if isinstance(failure,io.CleanupFailure):raise failure from primary
        raise
    finally:
        primary = sys.exception()
        try:
            if fd is not None:
                try:io._cleanup((lambda:os.close(fd),))
                except BaseException as cleanup:
                    owner.poisoned = True
                    try:_failed(owner,root,inode)
                    except BaseException as error:cleanup.add_note('Graph failure marker: '+repr(error))
                    if primary is not None:raise cleanup from primary
                    raise
        finally:owner._transition.release()

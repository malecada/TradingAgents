"""Selected compact MCM to bounded fixed CPU graph inputs.

The copied MCM and edge tensors feed the trainable MLP/GAT downstream. This
component does not train or detach a learned encoder, publish graph artifacts,
close a representation, or admit empirical execution. The allowance counts
source/copy payloads plus conversion scratch, not parent graph attributes,
dictionary/sample storage, Python overhead, model state or whole-workflow RSS.
"""
import importlib.util
import json
from pathlib import Path
from types import MappingProxyType

import numpy as np
import torch
from . import compact_mcm
from .cache import cache_key
from .neighborhoods import node_order_hash
from .provenance import file_hash, freeze, thaw

require = compact_mcm.require
ROOT = compact_mcm.ROOT
BOUNDARY = 'research/onchain-paper-replication-2026-09-24/full_sources/graph-feature-boundary-2026-10-01/boundary.py'


def _boundary():
    spec = importlib.util.spec_from_file_location('compact_feature_boundary', ROOT/BOUNDARY)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def _sources(mcm):
    result = compact_mcm._sources(mcm._dictionary)
    ad = mcm._dictionary._proof.owner.bound._run.admission
    sha = ad.experiment['source_files'].get(BOUNDARY)
    require(sha is not None and file_hash(ROOT/BOUNDARY) == sha
        and file_hash(ad.root/BOUNDARY) == sha, 'compact feature boundary source differs')
    return result | {BOUNDARY:sha}


def _original(mcm):
    """Rejoin original ancestry and saved output without external callbacks."""
    mcm._integrity()
    compact_mcm._original(mcm._dictionary,mcm._graph,mcm.record['graph_hash'])
    mcm._numeric(); mcm._evidence()
    compact_mcm.publication._verify(Path(mcm.record['output']['directory']),
        thaw(mcm.record['output_args']) | {'stage_root':mcm._stage.root},
        thaw(mcm.record['output_proof']),lambda:None,mcm.record['output']['receipt_sha256'])


class Features:
    __slots__ = ('_mcm','_feature','_record','_chunk','_boundary_module','_pin')

    def __init__(self,mcm,feature,record,chunk,boundary):
        object.__setattr__(self,'_mcm',mcm)
        object.__setattr__(self,'_feature',MappingProxyType(dict(feature)))
        object.__setattr__(self,'_record',freeze(record))
        object.__setattr__(self,'_chunk',chunk)
        object.__setattr__(self,'_boundary_module',boundary)
        object.__setattr__(self,'_pin',cache_key(record))

    def __setattr__(self,name,value): raise AttributeError('feature receipt attributes are immutable')
    feature = property(lambda self:self._feature)
    record = property(lambda self:self._record)

    def _numeric(self):
        require(cache_key(thaw(self.record)) == self._pin,'compact feature receipt changed')
        a,e = self.feature['mcm'],self.feature['edge_index']
        require(type(a) is torch.Tensor and type(e) is torch.Tensor
            and a.device.type == e.device.type == 'cpu' and a.dtype == torch.float32 and e.dtype == torch.int64
            and not a.requires_grad and not e.requires_grad and a.is_contiguous() and e.is_contiguous(),
            'fixed compact feature tensor properties changed')
        require(self._boundary_module.identity(a.numpy(),e.numpy(),self._chunk) == self.record['feature_hash'],
            'compact feature tensor content changed')

    def lease(self):
        self._numeric(); self._mcm.lease(); self._numeric()

    def _check(self):
        self._mcm._check(); _sources(self._mcm); self.lease()
        _original(self._mcm); self._numeric()

    def check(self):
        owner = self._mcm._dictionary._proof.owner
        require(owner._transition.acquire(blocking=False),'concurrent compact feature check')
        try: self._check()
        finally: owner._transition.release()


def prepare(mcm, *, input_name):
    require(type(mcm) is compact_mcm.Produced,'actual compact MCM Produced required')
    owner = mcm._dictionary._proof.owner
    require(owner._transition.acquire(blocking=False),'concurrent compact feature conversion')
    try:
        mcm._check(); sources = _sources(mcm)
        training = compact_mcm._training(mcm._dictionary)
        require(training.descriptor['arm'] in ('proposed','training_label_permutation','mcm_without_gat'),
            'compact MCM feature arm required')
        run = owner.bound._run; bound = owner.bound.record
        selected = json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][bound['representation']]
        item = json.loads(run.read_input(selected['plan_input']))['producers'][bound['producer']]
        require(type(input_name) is str and input_name in run.admission.inputs
            and item.get('compact_feature_input') == selected.get('compact_feature_input') == input_name,
            'explicit compact feature route differs')
        policy = json.loads(run.read_input(input_name))
        require(type(policy) is dict and set(policy) == {'schema_version','max_numeric_bytes','chunk_entries'}
            and type(policy['schema_version']) is int and policy['schema_version'] == 1
            and type(policy['max_numeric_bytes']) is int and 0 < policy['max_numeric_bytes'] < 2**63
            and type(policy['chunk_entries']) is int and 0 < policy['chunk_entries'] <= 65536,
            'compact feature policy differs')
        matrix,edges = mcm.matrix,mcm._graph.edge_index; chunk = policy['chunk_entries']
        require(type(edges) is np.ndarray and edges.dtype == np.dtype('int64')
            and edges.ndim == 2 and edges.shape[0] == 2,'native compact feature edges required')
        numeric = matrix.nbytes+edges.nbytes; required = 2*numeric+9*chunk
        require(required <= policy['max_numeric_bytes'],'compact feature numeric allowance exceeded before allocation')
        boundary = _boundary(); expected = boundary.identity(matrix,edges,chunk)
        def lease():
            mcm.lease()
            require(mcm.matrix is matrix and mcm._graph.edge_index is edges,'compact feature original arrays changed')
        lease(); _original(mcm)
        feature = boundary.materialize(matrix,edges,expected_hash=expected,
            max_numeric_bytes=policy['max_numeric_bytes'],chunk_entries=chunk,lease=lease)
        record = {'schema_version':1,'owner':owner.identity,'graph_hash':mcm.record['graph_hash'],
            'node_order_sha256':node_order_hash(mcm._graph.node_ids),'feature_hash':expected,
            'mcm_receipt_sha256':mcm.receipt_sha256,'mcm_directory':str(mcm.directory),
            'policy_input':input_name,'policy_sha256':run.admission.inputs[input_name]['sha256'],
            'reserved_numeric_bytes':required,'tensor_bytes':numeric,'sources':sources,
            'representation_admitted':False,'graph_artifact_published':False}
        result = Features(mcm,feature,record,chunk,boundary)
        result.lease(); _original(mcm); result._numeric(); _sources(mcm)
        return result
    finally: owner._transition.release()

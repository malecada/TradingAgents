"""Typed target/workload adapter for a genuine completed original import stage."""
from pathlib import Path
from . import original_import_stage,compact_owner,original_dictionary,job
from .cache import cache_key
from .provenance import canonical_bytes,thaw,file_hash
from .matching_pair import BACKEND
from .matching_identity import graph_identity
from .neighborhoods import graph_hash,node_order_hash
from .contracts import GraphSnapshot

KERNEL='research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py'
HELPER='research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-2026-09-30/workload.py'

def require(value,message):
    if not value:raise ValueError(message)


def workload_record(*,workflow,backend,graph,node_order,dictionary,ordered_motifs,matching,original_matching,execution_matching,execution_identity):
    return {'schema_version':2,'kind':'mcm-imported-original','workflow':workflow,'backend':backend,
      'graph':graph,'node_order':node_order,'dictionary':dictionary,'ordered_motifs':list(ordered_motifs),
      'matching':matching,'original_matching':original_matching,'execution_matching':execution_matching,
      'import_execution_identity':execution_identity,'dtype':'float32'}


class Target:
    def __init__(self,execution,graph,key):
        require(type(execution) is original_import_stage.ImportedExecution,'genuine imported execution required')
        require(type(graph) is GraphSnapshot,'actual registered weekly graph required')
        execution.check();self.execution=execution;self.graph=graph;self.key=key
        self.owner=execution._owner;self.dictionary=execution._materialized._dictionary
        self.receipt_sha256=execution._stage.reference
        self._objects=(id(execution),id(graph),id(self.owner),id(self.dictionary),self._arrays())
        descriptor=execution._stage.prepared._selection['selected']['descriptor']
        required=descriptor['required_graphs'];mapping=descriptor.get('resource_graph_inputs')
        require(type(mapping) is dict and set(mapping)==set(required) and key in mapping,'complete explicit resource target inputs required')
        self._input=mapping[key];self._mapping=canonical_bytes(mapping)
        run=self.owner.bound._run
        require(type(self._input) is str and self._input in run.admission.inputs,'registered target manifest required')
        self._manifest_sha=run.admission.inputs[self._input]['sha256']
        self._manifest=original_dictionary._read_registered(run,self._input)
        manifest=original_dictionary.parse(self._manifest)
        require(manifest['graph_hash']==key and graph_hash(graph)==key,'target graph content differs')
        self._execution=execution.check();self._execution_pin=canonical_bytes(self._execution)
        self._node_order=node_order_hash(graph.node_ids)
        self._motifs=[graph_identity(m) for m in self.dictionary.representatives]
        self.scope=self.derive_scope();self._scope_pin=canonical_bytes(self.scope)
        self.check()

    def _arrays(self):
        return tuple(id(getattr(self.graph,name)) for name in ('node_ids','node_features','edge_index','edge_features','edge_aggregates'))

    def _pins(self):
        require((id(self.execution),id(self.graph),id(self.owner),id(self.dictionary),self._arrays())==self._objects,'import target objects changed')
        require(self.execution._owner is self.owner and self.execution._materialized._dictionary is self.dictionary and self.execution._stage.reference==self.receipt_sha256,'import target authority chain changed')
        descriptor=self.execution._stage.prepared._selection['selected']['descriptor']
        require(canonical_bytes(descriptor['resource_graph_inputs'])==self._mapping and descriptor['resource_graph_inputs'][self.key]==self._input,'target input mapping changed')
        require(canonical_bytes(self._execution)==self._execution_pin and canonical_bytes(self.scope)==self._scope_pin,'target execution/workload changed')

    def derive_scope(self):
        current=self._execution['current'];ordered=[graph_identity(m) for m in self.dictionary.representatives]
        require(current['original_dictionary']==self.dictionary.identity and current['original_matching']==self.dictionary.matching_config_hash,'original dictionary identity family differs')
        require(current['execution_matching']==cache_key({'config':thaw(self.owner.matching),'backend':BACKEND}),'current backend matching differs')
        workload=cache_key(workload_record(workflow=self.owner.bound.record['workflow_identity'],backend=BACKEND,
          graph=self.key,node_order=self._node_order,dictionary=self.dictionary.identity,ordered_motifs=ordered,
          matching=thaw(self.owner.matching),original_matching=self.dictionary.matching_config_hash,
          execution_matching=current['execution_matching'],execution_identity=self._execution['execution_identity']))
        return {'graph':self.key,'node_order':self._node_order,'dictionary':self.dictionary.identity,
          'ordered_motifs':cache_key(ordered),'matching':current['execution_matching'],'workflow':workload}

    def final(self,*,full_graph=True):
        self._pins();compact_owner.verify_current(self.owner)
        original_import_stage.content(self.execution._stage)
        require(self.execution._materialized._integrity()['ordered_motifs']==self._motifs,'original motif order changed')
        require(self.derive_scope()==self.scope,'imported workload independently differs')
        if full_graph:
            require(graph_hash(self.graph)==self.key and node_order_hash(self.graph.node_ids)==self._node_order,'registered target contents changed')

    def lease(self):
        # Inner callbacks keep frozen input contract; full graph hashes run at
        # producer/kernel boundaries, not once per pair on a million-node graph.
        self.execution.check();self.final(full_graph=False)

    def check(self):
        self.lease();run=self.owner.bound._run
        require(run.admission.inputs[self._input]['sha256']==self._manifest_sha and original_dictionary._read_registered(run,self._input)==self._manifest,'target manifest changed')
        require(canonical_bytes(self.execution.check())==self._execution_pin,'completed imported execution identity changed')
        self.final()

    def sources(self):
        self.check();run=self.owner.bound._run;result={}
        for name in sorted(job.required_sources()|{KERNEL,HELPER}):
            expected=run.admission.experiment['source_files'].get(name)
            require(expected is not None and file_hash(run.admission.root/name)==expected,'imported numerical source closure differs')
            result[name]=expected
        return result

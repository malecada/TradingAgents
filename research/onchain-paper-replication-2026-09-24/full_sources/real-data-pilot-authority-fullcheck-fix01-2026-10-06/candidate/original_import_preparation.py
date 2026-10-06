"""Prospective pre-birth import slice; no completed Owner/stage or MCM permission.

Install with the genuine resource Binding factory/Owner patch only after review.
No fresh dictionary Proof, Produced, matching log or zero-pair stage is created.
"""
import hashlib
from pathlib import Path
from . import original_dictionary as original
from .cache import cache_key
from .provenance import canonical_bytes,thaw,file_hash


def require(value,message):
    if not value:raise ValueError(message)


def required_stages(descriptor):
    require(type(descriptor) is dict and descriptor.get('dictionary_origin')=='imported-original-v1','explicit imported origin required before Owner birth')
    graphs=descriptor.get('required_graphs')
    require(type(graphs) is list and 0<len(graphs)<=9 and all(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h) for h in graphs),'target graph identities invalid')
    require(graphs==sorted(set(graphs)),'target graph order/membership differs')
    return ('dictionary-import',)+tuple('mcm-'+h for h in graphs)


def materialization_bytes(record):
    """Numeric payload only, not JSON/Python/process peak; no array import."""
    require(type(record) is dict and type(record.get('representatives')) is list and 0<len(record['representatives'])<=32,'bounded original representatives required')
    total=0
    for graph in record['representatives']:
        n=len(graph['node_ids']);nf=graph['node_features'];ei=graph['edge_index'];ef=graph['edge_features'];width=graph['edge_width']
        require(n>0 and type(nf) is list and len(nf)==n and type(nf[0]) is list and len(nf[0])>0,'node feature extent')
        w=len(nf[0]);require(all(type(row) is list and len(row)==w for row in nf),'ragged node features')
        require(type(ei) is list and len(ei)==2 and all(type(row) is list for row in ei) and len(ei[0])==len(ei[1]),'edge extent')
        e=len(ei[0]);require(type(width) is int and width>0 and type(ef) is list and len(ef)==e and all(type(row) is list and len(row)==width for row in ef),'edge feature extent')
        total+=8*(n*w+2*e+e*width)
        require(total<2**63,'numeric payload overflow')
    return total


_SEAL=object()


class PreparedImport:
    """Genuine Binding-bound metadata selection before any compact Owner birth."""
    def __init__(self,seal,bound,cap,input_name,job_input,selection,source):
        require(seal is _SEAL,'use admitted prepare entry')
        self._bound=bound;self._run=bound._run;self._cap=cap;self._cap_pin=cap
        self._input=input_name;self._job_input=job_input
        self._selection=selection;self._source=source
        self._closed=False
        self._pin=self._configuration()
        self._check()

    def _configuration(self):
        bound=self._bound;run=self._run
        return canonical_bytes({'binding':thaw(bound.record),'context':thaw(bound.context),'limits':thaw(bound.limits),
          'run_directory':str(run.directory),'claim':run._claim_sha256,
          'snapshots':{str(p):v for p,v in bound._snapshots.items()},'job_input':self._job_input,
          'input':self._input,'selection':self._selection,'source':self._source})

    def _selection_now(self):
        from .resource_binding import assert_selected
        assert_selected(self._bound,self._job_input)
        run=self._run;value=original.parse(original._read_registered(run,self._job_input))
        require(value['kind']=='compact_resource','resource-only import kind required')
        selected=value['payload']['representation_jobs'][self._bound.record['representation']]
        item=original.parse(original._read_registered(run,selected['plan_input']))['producers'][self._bound.record['producer']]
        require(selected['descriptor']==item['descriptor'] and cache_key(selected['descriptor'])==self._bound.record['workflow_identity'],'current selected descriptor differs')
        require(selected.get('original_dictionary_input')==item.get('original_dictionary_input')==self._input,'original dictionary selector differs')
        descriptor=selected['descriptor'];stages=required_stages(descriptor)
        require(descriptor.get('original_dictionary_import')=={'input':self._input,'sha256':run.admission.inputs[self._input]['sha256']},'original control registration differs')
        return {'job':value,'selected':selected,'producer':item,'required_stages':list(stages)}

    def _check(self):
        from . import matching_owner
        require(not self._closed and type(self._bound) is matching_owner.Binding and self._bound._run is self._run,'original Binding inactive/replaced')
        require(type(self._cap) is original.ImportedOriginal and self._cap is self._cap_pin,'actual original evidence capability required')
        require(self._configuration()==self._pin,'prepared import configuration changed')
        self._bound.check();self._cap.check()
        require(self._selection_now()==self._selection,'resource selection changed')
        for name,sha in self._source.items():
            require(self._run.admission.experiment['source_files'].get(name)==sha and file_hash(self._run.admission.root/name)==sha,'import candidate source changed')
        # Callback-free pins after all live checks/readback above.
        require(self._bound._run is self._run and self._configuration()==self._pin,'Binding changed during final check')

    def stage_contract(self):
        self._check()
        return self._stage_contract_metadata()

    def _stage_contract_metadata(self):
        # Callback-free construction only. Callers retain genuine full checks:
        # stage_contract checks immediately before this helper; execution_contract
        # checks before all construction and again before returning any value.
        # Contract to be consumed by future Owner constructor BEFORE root birth.
        value={'kind':'dictionary-import','required_stages':self._selection['required_stages'],
          'current_binding':cache_key(thaw(self._bound.record)),
          'control_input':self._input,'control_sha256':self._run.admission.inputs[self._input]['sha256'],
          'job_input':self._job_input,'job_sha256':self._run.admission.inputs[self._job_input]['sha256'],
          'descriptor_sha256':self._bound.record['workflow_identity']}
        return original.parse(canonical_bytes(value))

    def execution_contract(self):
        """Identity ingredients only: no Owner receipt or execution grant."""
        self._check()
        from .matching_pair import BACKEND
        policy=original.parse(self._cap._policy)
        raw=original._read_registered(self._run,policy['refs']['matching_config']['input'])
        scientific=original.parse(raw)
        current=self._selection['selected']['descriptor']['configs']['matching']
        require(canonical_bytes(current)==canonical_bytes(scientific),'current numerical matching settings differ from original')
        value={'original_dictionary':policy['dictionary_identity'],
          'original_matching':cache_key(scientific),
          'execution_matching':cache_key({'config':current,'backend':BACKEND}),
          'backend':BACKEND,'current_binding':cache_key(thaw(self._bound.record)),
          'current_source':self._run.admission.source,'runtime_hash':self._bound.context['runtime_hash'],'source_modules':self._source,
          'stage_contract':self._stage_contract_metadata(),'mcm_execution_admitted':False}
        self._check()
        require(original._read_registered(self._run,policy['refs']['matching_config']['input'])==raw,'original matching bytes changed after lease')
        return original.parse(canonical_bytes(value))

    def materialize(self,*,max_numeric_bytes):
        """Bounded original objects, not a current completed import capability."""
        require(type(max_numeric_bytes) is int and 0<max_numeric_bytes<=16*1024**2,'finite motif payload allowance required')
        self._check()
        def build(evidence):
            record=evidence.dictionary_record();extent=materialization_bytes(record)
            require(extent<=max_numeric_bytes,'motif numeric allowance exceeded before allocation')
            # Only this selected boundary imports numerical dependencies.
            import numpy as np
            from .contracts import AttributedGraph,validate_attributed
            from .dictionary import Dictionary,dictionary_hash
            from .matching_identity import graph_identity
            graphs=[]
            for g in record['representatives']:
                graph=AttributedGraph(tuple(g['node_ids']),np.asarray(g['node_features'],dtype=np.float64),
                  np.asarray(g['edge_index'],dtype=np.int64).reshape(2,-1),
                  np.asarray(g['edge_features'],dtype=np.float64).reshape(-1,g['edge_width']),g['parent_hash'],g['center_id'])
                validate_attributed(graph);graphs.append(graph)
            dictionary=Dictionary(tuple(graphs),tuple(tuple(x) for x in record['memberships']),record['sample_hash'],
              tuple(record['training_graph_hashes']),record['config'],record['matching_config_hash'],record['identity'],tuple(record['hierarchy']))
            require(dictionary_hash(dictionary)==record['identity'],'materialized original scientific identity differs')
            identities=tuple(graph_identity(g) for g in dictionary.representatives)
            return dictionary,identities,evidence,extent
        result=self._cap.with_evidence(build)
        self._check()
        dictionary,identities,evidence,extent=result
        from .dictionary import dictionary_hash
        from .matching_identity import graph_identity
        require(dictionary_hash(dictionary)==evidence.dictionary_identity and tuple(graph_identity(g) for g in dictionary.representatives)==identities,'materialized original changed across lease')
        return MaterializedOriginal(_SEAL,self,dictionary,identities,evidence,extent)

    def close(self):
        require(not self._closed,'prepared import already closed')
        self._closed=True;self._cap.close()


def _evidence_pin(evidence):
    return (evidence.dictionary_identity,evidence.sample_identity,tuple(evidence.representative_indices),
      evidence.original_terminal,evidence.original_claim,hashlib.sha256(evidence._dictionary_bytes).hexdigest(),evidence.bundle_sha256)


def _check_materialized_metadata(value):
    require(value._evidence is value._evidence_object and _evidence_pin(value._evidence)==value._evidence_value,'original evidence object/provenance changed')
    require(type(value.numeric_bytes) is int and value.numeric_bytes==value._numeric_bytes,'original numeric extent changed')
    require(value._dictionary.identity==value._evidence.dictionary_identity,'original Dictionary identity changed')


class MaterializedOriginal:
    """No Owner/import receipt exists yet; deliberately rejected by MCM routes."""
    def __init__(self,seal,prepared,dictionary,identities,evidence,extent):
        require(seal is _SEAL,'only actual bounded materialization may construct')
        self._prepared=prepared;self._dictionary=dictionary;self._motifs=identities
        self._evidence=evidence;self._evidence_object=evidence;self._evidence_value=_evidence_pin(evidence)
        self.numeric_bytes=extent;self._numeric_bytes=extent
        self._object_pin=(id(prepared),id(dictionary),tuple((id(g),*(id(getattr(g,n)) for n in ('node_features','edge_index','edge_features'))) for g in dictionary.representatives))

    def check(self):
        self._prepared._check()
        return self._integrity()

    def _integrity(self):
        """Callback-free numeric/object rejoin after current authority check."""
        _check_materialized_metadata(self)
        from .dictionary import dictionary_hash
        from .matching_identity import graph_identity
        require((id(self._prepared),id(self._dictionary),tuple((id(g),*(id(getattr(g,n)) for n in ('node_features','edge_index','edge_features'))) for g in self._dictionary.representatives))==self._object_pin,'original object replaced')
        require(sum(getattr(g,name).nbytes for g in self._dictionary.representatives for name in ('node_features','edge_index','edge_features'))==self.numeric_bytes,'materialized numeric extent differs')
        require(dictionary_hash(self._dictionary)==self._evidence.dictionary_identity and tuple(graph_identity(g) for g in self._dictionary.representatives)==self._motifs,'original numeric evidence changed')
        return {'original_dictionary':self._evidence.dictionary_identity,'original_matching':self._dictionary.matching_config_hash,
          'representative_sample_indices':list(self._evidence.representative_indices),'ordered_motifs':list(self._motifs),
          'bundle_sha256':self._evidence.bundle_sha256,'numeric_bytes':self.numeric_bytes,
          'owner_stage_completed':False,'mcm_execution_admitted':False}


def prepare(bound,*,input_name,job_input='execution_job'):
    from . import matching_owner
    require(type(bound) is matching_owner.Binding,'actual current Binding required')
    from .resource_binding import assert_selected
    assert_selected(bound,job_input)
    bound.check();run=bound._run
    # Candidate module location and full installed source hash must be admitted.
    sources={}
    for path in (Path(__file__).resolve(),Path(original.__file__).resolve()):
        require(path.is_relative_to(run.admission.root),'import module outside admitted source root')
        name=str(path.relative_to(run.admission.root));expected=run.admission.experiment['source_files'].get(name)
        require(expected is not None and file_hash(path)==expected,'import preparation source not admitted');sources[name]=expected
    raw=original.parse(original._read_registered(run,job_input))
    require(raw['kind']=='compact_resource','resource-only import kind required')
    selected=raw['payload']['representation_jobs'][bound.record['representation']]
    item=original.parse(original._read_registered(run,selected['plan_input']))['producers'][bound.record['producer']]
    stages=required_stages(selected['descriptor'])
    require(not (Path(bound.record['journal_directory'])/'compact').exists(),'import selection must precede Owner birth')
    cap=original.admit(bound,input_name=input_name,job_input=job_input)
    return PreparedImport(_SEAL,bound,cap,input_name,job_input,
      {'job':raw,'selected':selected,'producer':item,'required_stages':list(stages)},sources)

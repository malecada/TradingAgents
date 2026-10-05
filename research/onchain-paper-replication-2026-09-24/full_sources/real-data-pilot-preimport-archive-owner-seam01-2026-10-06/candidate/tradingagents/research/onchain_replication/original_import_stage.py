"""Genuine imported stage under a preselected current compact Owner.

New stage kind has original imported evidence, never fabricated matching logs.
Resource worker dispatch and MCM imported wrapper remain separate integrations.
"""
import os
from pathlib import Path
from . import compact_owner as owners, compact_policy, original_dictionary as original
from . import original_import_preparation as preparation, resource_binding
from . import score_batches as io,import_metadata
from .cache import cache_key
from .provenance import canonical_bytes,thaw

require=io._require


def _write(root,name,raw):
    return import_metadata.write(root,name,raw)


def _birth(root):
    return import_metadata.birth(root)


class ImportStage:
    def __init__(self,owner,prepared,policy,held):
        require(type(owner) is owners.Owner and type(prepared) is preparation.PreparedImport and prepared._bound is owner.bound,'actual current imported owner required')
        resource_binding.assert_selected(owner.bound,prepared._job_input)
        held.check(owner);owner.boundary();prepared._check()
        require(owner.required==tuple(prepared.stage_contract()['required_stages']) and owner.required[0]=='dictionary-import','owner did not select import before birth')
        require(not owner.stages and owner.active is None,'import stage must be first and unused')
        policy=resource_binding.import_policy(policy)
        self.owner=owner;self.prepared=prepared;self.policy=policy
        self.name='dictionary-import';self.kind='dictionary-import';self.root=owner.root/self.name
        self.reservation=policy['max_stage_bytes'];self.closed=False;self.reference=None;self.materialized=None
        require(owner.reserved+self.reservation<=owner.maximum,'import stage cumulative reservation exhausted')
        self._policy_pin=canonical_bytes(policy);self._objects=(id(owner),id(prepared));self._root_pin=str(self.root)
        record={'schema_version':1,'kind':self.kind,'owner':owner.identity,'stage':self.name,
          'binding_sha256':cache_key(thaw(owner.bound.record)),'prebirth_contract':prepared.stage_contract(),
          'execution':prepared.execution_contract(),'policy':policy,'reserved_logical_bytes':self.reservation}
        self.intent=owners.body(record);self._intent_pin=self.intent
        _birth(self.root);info=self.root.lstat();self.inode=(info.st_dev,info.st_ino);self._inode_pin=self.inode
        _write(self.root,'intent.json',self.intent)
        owner.stages[self.name]=self;owner.active=self
        owner.reserved+=self.reservation;owner._reserved=owner.reserved
        self.integrity()

    def integrity(self):
        resource_binding.assert_selected(self.owner.bound,self.prepared._job_input)
        require(type(self.owner) is owners.Owner and self.owner.stages.get(self.name) is self and self.owner.required[0]==self.name,'import stage membership changed')
        require((id(self.owner),id(self.prepared))==self._objects and self.prepared._bound is self.owner.bound,'import authority replaced')
        require(self.name==self.kind=='dictionary-import' and str(self.root)==self._root_pin and self.root==self.owner.root/self.name and self.root.resolve()==self.root,'import stage path/kind changed')
        require(canonical_bytes(self.policy)==self._policy_pin and self.reservation==self.policy['max_stage_bytes'],'import policy/reservation changed')
        require(self.intent==self._intent_pin and self.inode==self._inode_pin,'import intent/inode pin changed')
        info=self.root.lstat();require((info.st_dev,info.st_ino)==self.inode,'import stage inode changed')
        import_metadata.exact(self.root,'intent.json',self.intent)
        expected={'intent.json'}|({'import-complete.json'} if self.closed else set())
        owners.entries(self.root,expected,required=expected,_imported=True)
        if self.closed:
            require(self.materialized is self._materialized_pin,'materialized original replaced')
            require(self.materialized._integrity()==self._numeric_record,'imported numeric/provenance changed')
            import_metadata.exact(self.root,'import-complete.json',self._receipt)
            require(self.reference==io._hash(self._receipt),'import receipt hash changed')

    def lease(self):
        self.owner.lease();self.prepared._check();self.integrity()
        require((self.closed and self.owner.active is not self) or (not self.closed and self.owner.active is self),'import active stage differs')


def content(stage):
    require(type(stage) is ImportStage and stage.closed,'actual completed import stage required')
    stage.integrity()
    require(stage.owner.stages.get(stage.name) is stage,'import receipt transplanted')
    return {'completed_pairs':0,'imported_original':True,'receipt_sha256':stage.reference,
      'original_dictionary':stage._numeric_record['original_dictionary']}


def complete_import(owner,prepared,*,stage_policy):
    require(type(owner) is owners.Owner,'actual owner required')
    with owners._held(owner) as held:
        try:
            stage=ImportStage(owner,prepared,stage_policy,held)
            numeric=prepared.materialize(max_numeric_bytes=stage.policy['max_numeric_bytes'])
            record=numeric.check();execution=prepared.execution_contract()
            require(record['original_matching']==execution['original_matching'],'original matching identities differ')
            held.check(owner);stage.lease();owner.boundary()
            receipt={'schema_version':1,'kind':'dictionary-import-complete','owner':owner.identity,
              'intent_sha256':io._hash(stage.intent),'numeric':record,'execution':execution,
              'current_matching_pairs':0,'historical_work_recomputed':False}
            raw=owners.body(receipt)
            # Completion publication is a one-way boundary; no retry on error.
            _write(stage.root,'import-complete.json',raw)
            stage.materialized=stage._materialized_pin=numeric;stage._numeric_record=record
            stage._receipt=raw;stage.reference=io._hash(raw);stage.closed=True;owner.active=None
            stage.lease();held.check(owner);content(stage);owner.boundary()
            return stage
        except BaseException:
            owner.poisoned=True;raise


def attach(prepared,*,policy_input,stage_policy_input,archive_transport=None):
    """Create genuine Owner once, after exact resource/job/input preflight."""
    require(type(prepared) is preparation.PreparedImport,'actual prepared import required');prepared._check()
    bound=prepared._bound;resource_binding.assert_selected(bound,prepared._job_input)
    run=bound._run;selection=prepared._selection
    selected=selection['selected'];item=selection['producer'];descriptor=selected['descriptor']
    for value in (selected,item):
        require(value.get('compact_policy_input')==policy_input and value.get('native_backend')==compact_policy.BACKEND,'compact import owner route differs')
        require(value.get('original_dictionary_stage_input')==stage_policy_input,'explicit import stage policy differs')
    require(descriptor.get('original_dictionary_stage')=={'input':stage_policy_input,'sha256':run.admission.inputs[stage_policy_input]['sha256']},'import stage policy descriptor differs')
    require(descriptor.get('compact_execution')=={'backend':compact_policy.BACKEND,'policy_sha256':run.admission.inputs[policy_input]['sha256']},'compact owner policy descriptor differs')
    archive_name=selected.get('compact_archive_input')
    archive_selected=archive_name is not None or item.get('compact_archive_input') is not None
    require(archive_selected==(archive_transport is not None),'registered archive requires genuine preimport transport; local route cannot accept one')
    if archive_selected:
        from . import archive_dispatch,archive_owner_policy,archive_owner_operations
        from .real_pilot_import_caller import admitted
        _,current,pilot=admitted(run.admission,original.parse(original._read_registered(run,prepared._job_input)))
        require(pilot['schema_version']==2 and canonical_bytes(current)==canonical_bytes(selected),'exact schema2 real-pilot archive selection required')
        require(type(archive_transport) is archive_dispatch.View and type(archive_transport._context) is archive_dispatch.Context,'genuine archive dispatch view required')
        context=archive_transport._context
        require(context._run is run and context.view(bound.record['representation']) is archive_transport and context._record['job_input']==prepared._job_input,'archive view belongs to another original Run/representation')
        context._outer();prepared._check()
    policy=resource_binding.import_policy(original.parse(original._read_registered(run,stage_policy_input)))
    envelope=original.parse(original._read_registered(run,policy_input))
    require(set(envelope)=={'schema_version','backend','stage_policy','max_workflow_retained_logical_bytes'} and type(envelope['schema_version']) is int and envelope['schema_version']==1 and envelope['backend']==compact_policy.BACKEND,'compact envelope differs')
    require(type(envelope['max_workflow_retained_logical_bytes']) is int and envelope['max_workflow_retained_logical_bytes']>=owners.OWNER_BYTES+policy['max_stage_bytes'],'finite imported owner reservation required')
    # Validate future MCM policy, not a fabricated zero-pair dictionary stage.
    compact_policy.validate(envelope['stage_policy'],kind='mcm',pairs=1)
    require(canonical_bytes(envelope['stage_policy']['pair'])==canonical_bytes(thaw(bound.limits)),'import current pair limits differ')
    owner=owners.Owner(bound,policy_input,envelope,descriptor,imported=prepared)
    if archive_transport is None:return owner,complete_import(owner,prepared,stage_policy=policy)
    try:
        # Real selection and durable ledger birth occur while Owner is still empty.
        archive_owner_operations.attach(archive_owner_policy.select(owner,input_name=archive_name,transport=archive_transport))
        context._outer();prepared._check()
        return owner,complete_import(owner,prepared,stage_policy=policy)
    except BaseException as primary:
        owner.poisoned=True
        ledger=getattr(owner,'_archive_operations',None)
        if ledger is not None:
            ledger._poisoned=True
            io._close_after_failure(ledger.close,primary)
        raise


class ImportedExecution:
    """Current completed import-stage authority, separate from original Dictionary.

    A target graph is NOT supplied by this capability. The future typed MCM
    adapter must authenticate its registered target before deriving workload.
    """
    def __init__(self,stage):
        require(type(stage) is ImportStage and stage.closed,'actual completed imported stage required')
        stage.lease();content(stage)
        self._stage=stage;self._owner=stage.owner;self._bound=stage.owner.bound
        self._materialized=stage.materialized
        self._pin=(id(stage),id(stage.owner),id(stage.owner.bound),id(stage.materialized),stage.reference,stage.inode)
        self._execution=stage.prepared.execution_contract()
        self._execution_pin=canonical_bytes(self._execution)
        self.check()

    def check(self):
        stage=self._stage
        require(type(stage) is ImportStage and (id(stage),id(self._owner),id(self._bound),id(self._materialized),stage.reference,stage.inode)==self._pin,'import execution authority replaced')
        require(stage.owner is self._owner and self._owner.bound is self._bound and stage.materialized is self._materialized,'import execution owner chain changed')
        stage.lease();content(stage)
        current=stage.prepared.execution_contract()
        require(canonical_bytes(current)==self._execution_pin==canonical_bytes(self._execution),'import execution configuration changed')
        # Callback-free original numeric/receipt/owner joins after last callback.
        owners.verify_current(self._owner);stage.integrity();numeric=self._materialized._integrity()
        require(current['original_dictionary']==numeric['original_dictionary'] and current['original_matching']==numeric['original_matching'],'import identity families differ')
        return {'execution_identity':cache_key({'import_receipt':stage.reference,'current':current}),
          'import_receipt_sha256':stage.reference,'current':original.parse(self._execution_pin),
          'original':numeric,'financial_representation_admitted':False}

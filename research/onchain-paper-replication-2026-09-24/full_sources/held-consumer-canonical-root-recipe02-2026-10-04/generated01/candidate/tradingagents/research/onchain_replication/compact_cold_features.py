"""Explicit same-run compact detachment after genuine complete publication.

A new durable file authority retires original-object checks only after their
last full verification. No historical reuse, financial admission, memory saving
or capacity follows. External retained aliases remain the caller's liability.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
import threading
from types import SimpleNamespace
from . import cold_files, compact_terminal, compact_publication, compact_native_features, compact_stage
from . import matching_owner, resources, job as job_module, archive_owner_seal
from .feature_pipeline import PreparedFeatures
from .feature_residency import FixedFeatureMap
from .provenance import canonical_bytes, freeze, thaw, file_hash, durable_mkdir
from .. import lifecycle

ROOT=Path(__file__).resolve().parents[3]
KIND='same-run-complete-compact-file-authority-v1'
_KEY=object()
require=cold_files.require
NAMESPACES=('onchain_representations','onchain_pair_workflows','onchain_compact_sampler',
 'onchain_compact_samples','onchain_compact_dictionary','onchain_compact_mcm','onchain_compact_outputs',
 'onchain_compact_graphs','onchain_compact_publications','onchain_compact_terminals')


def required_sources():
    return compact_native_features.required_sources()|{str(Path(m.__file__).resolve().relative_to(ROOT))
        for m in (cold_files,compact_stage,archive_owner_seal)}|{str(Path(__file__).resolve().relative_to(ROOT))}


def selected(run,representation,job,item):
    a=job.get('compact_cold_handoff_input');b=item.get('compact_cold_handoff_input')
    if a is None and b is None:return None
    require(type(a) is str and a==b and a in run.admission.inputs,'cold execution policy route differs')
    value=json.loads(run.read_input(a))
    fields={'schema_version','kind','evidence_roots','watch','handoff_output','max_metadata_bytes',
        'max_files','max_directories','max_total_bytes','max_file_bytes','max_depth','chunk_bytes'}
    require(type(value) is dict and set(value)==fields and type(value['schema_version']) is int
        and value['schema_version']==1 and value['kind']==KIND,'cold policy schema differs')
    for key in fields-{'schema_version','kind','evidence_roots','watch','handoff_output'}:
        require(type(value[key]) is int and 0<value[key]<2**63,'cold finite policy differs')
    require(value['chunk_bytes']<=1024**2 and value['max_metadata_bytes']<=2*1024**2,'cold metadata/chunk cap differs')
    require(type(value['evidence_roots']) is list and value['evidence_roots']==sorted(set(value['evidence_roots']))
        and value['evidence_roots'],'cold evidence roots differ')
    watch=value['watch'];require(type(watch) is dict and set(watch)=={'root','limits'},'cold storage watch required')
    execution=json.loads(run.read_input('execution_job'))
    require(execution['resources'].get('storage_budget')==watch,'cold watch is not the registered whole-tree watch')
    p=Path(watch['root']);require(p.is_absolute() and p.resolve()==p,'cold watch root differs')
    output=value['handoff_output'];require(type(output) is str and Path(output).name==output
        and output in run.admission.experiment['outputs'] and output not in (job['binding_output'],job['journal_output']),
        'cold output is not separately registered')
    for name in required_sources():
        sha=run.admission.experiment['source_files'].get(name)
        require(sha is not None and file_hash(ROOT/name)==sha and file_hash(run.admission.root/name)==sha,'cold source closure differs: '+name)
    return value


def _guard(run,guard,policy):
    ad=run.admission;p=guard['resources'];owner=guard['owner'];base=Path(guard['base'])
    args=SimpleNamespace(root=ad.root,registration=ad.registration,experiment=ad.experiment_id,source=ad.source)
    live=resources.assert_guarded_worker(base/'guard',job_module._command(args,'worker'),
        required_paths=[Path(x) for x in p['disk_paths']],wall_seconds=p['wall_seconds'],
        memory_max_bytes=p['memory_max_bytes'],memory_high_bytes=p['memory_high_bytes'],disk_floor_bytes=p['disk_floor_bytes'])
    require(canonical_bytes(live.get('owner_identity'))==canonical_bytes(owner)
        and all(k in live and canonical_bytes(live[k])==canonical_bytes(v) for k,v in p.items()),'cold guard identity/policy differs')
    require(live.get('storage_budget')==policy['watch'],'cold complete storage watch differs')
    require(type(live.get('monitor_pid')) is int and live['monitor_pid']==owner['monitor_pid'],'cold live monitor identity differs')
    require(job_module.same_process_alive(owner['monitor_pid'],owner['monitor_start_ticks']),'cold monitor disappeared')


class Authority:
    __slots__=('_run','_record','_pin','_snapshot','_guard_record','_stages','_outputs','_lock','_state')
    def __init__(self,key,run,record,snapshot,guard,stages,outputs):
        require(key is _KEY,'cold authority requires genuine terminal factory')
        for name,value in (('_run',run),('_record',freeze(record)),('_pin',hashlib.sha256(canonical_bytes(record)).hexdigest()),
            ('_snapshot',snapshot),('_guard_record',freeze(guard)),('_stages',freeze(stages)),('_outputs',freeze(outputs)),
            ('_lock',threading.Lock()),('_state',{'failed':False,'observed':dict(outputs)})):
            object.__setattr__(self,name,value)
    def __setattr__(self,name,value):raise AttributeError('cold authority is immutable')
    def check(self,*,full=False):
        require(self._lock.acquire(blocking=False),'concurrent cold authority check')
        try:
            require(not self._state['failed'],'cold authority poisoned')
            require(hashlib.sha256(canonical_bytes(thaw(self._record))).hexdigest()==self._pin,'cold authority record changed')
            run=self._run;ad=run.admission;record=thaw(self._record)
            require(type(run) is lifecycle.ResearchRun and set(vars(run))=={'admission','directory','_published_outputs','_claim_sha256'},
                'cold run gained untracked ownership')
            run._active();run._check_source();run._check_inputs()
            require(ad.source==record['source'] and ad.registration_sha256==record['registration_sha256']
                and ad.experiment_id==record['experiment'],'cold run identity changed')
            require(hashlib.sha256(canonical_bytes(matching_owner.inventory(ad.root,include_torch=True))).hexdigest()==record['runtime_hash'],
                'cold runtime changed')
            _guard(run,thaw(self._guard_record),record['policy'])
            expected=set(record['policy']['evidence_roots'])
            for namespace in NAMESPACES:
                path=ad.root/'research_artifacts'/namespace/record['workflow_identity']
                require(not path.is_symlink() and path.resolve()==path and path.exists()==(str(path.relative_to(ad.root)) in expected), 'cold namespace population changed')
            original_dirs,original_files=cold_files.original_subset(self._snapshot,tuple(record['policy']['evidence_roots']))
            require(canonical_bytes(original_dirs)==canonical_bytes(record['directory_pins'])
                and canonical_bytes(original_files)==canonical_bytes(record['file_pins']),'cold authority lost original evidence pins')
            self._snapshot.check(full=full)
            with lifecycle._lock(ad.root):
                run._active();registry=dict(run._published_outputs)
                require(set(registry)<=set(ad.experiment['outputs']) and all(registry.get(k)==v for k,v in self._state['observed'].items()),
                    'cold output registry changed')
                root=run.directory/'outputs';require(root.resolve()==root and set(p.name for p in root.iterdir())==set(registry),'cold output membership changed')
                for name,sha in registry.items():
                    require(Path(name).name==name,'cold output name changed')
                    require(cold_files.read_hash(root/name,record['policy']['max_file_bytes'],record['policy']['chunk_bytes'])[1]==sha,'cold output bytes changed')
                self._state['observed'].update(registry)
            if full:
                for stage in self._stages:
                    contract=thaw(stage['contract'])
                    if 'archive' in contract:
                        archive_owner_seal.check_content(Path(stage['root']),expected_sha256=stage['sha256'],contract=contract)
                    else:compact_stage.verify(Path(stage['root']),expected_sha256=stage['sha256'],lease=lambda:_guard(run,thaw(self._guard_record),record['policy']),**contract)
                self._snapshot.check(full=True)
            _guard(run,thaw(self._guard_record),record['policy']);run._active();run._check_source();run._check_inputs()
        except BaseException:
            self._state['failed']=True;raise
        finally:self._lock.release()
    def lease(self):self.check(full=False)


class _Features(FixedFeatureMap):
    def __init__(self,mapping,authority,hashes,boundary,chunk):
        self._mapping=mapping;self._authority=authority;self._hashes=freeze(hashes)
        self._boundary=boundary;self._chunk=chunk;self._lock=threading.Lock()
    def __len__(self):return len(self._mapping)
    def __iter__(self):return iter(self._mapping)
    def __getitem__(self,key):return self.load_batch([key])[key]
    def live_tensor_bytes(self):return self._mapping.live_tensor_bytes()
    def verified_hashes(self):
        require(self._lock.acquire(blocking=False),'concurrent cold feature check')
        try:
            actual=self._mapping.verified_hashes();self._authority.lease()
            require(actual==dict(self._hashes),'cold feature population changed');return actual
        finally:self._lock.release()
    def load_batch(self,keys):
        require(self._lock.acquire(blocking=False),'concurrent cold feature load')
        loaded=None
        try:
            loaded=self._mapping.load_batch(keys);self._authority.lease();self._mapping.live_tensor_bytes()
            for h,f in loaded.items():
                require(self._boundary.identity(f['mcm'].numpy(),f['edge_index'].numpy(),self._chunk)==self._hashes[h],
                    'cold returned feature changed')
            return loaded
        except BaseException:
            if loaded is not None:loaded.clear()
            loaded=None;f=None;raise
        finally:self._lock.release()


def prepare(published,*,terminal_input,input_name):
    # The selected producer supplies its actual Published object. Mint the
    # original terminal here; never accept a caller-constructed terminal callback.
    require(type(published) is compact_publication.Published,'actual compact scientific publication required')
    terminal=compact_terminal.finish(published,input_name=terminal_input)
    require(type(terminal) is compact_terminal.Receipt,'actual compact terminal required; resource-only receipts refused')
    terminal.check();owner=terminal._owner;bound=owner.bound;run=bound._run;ad=run.admission
    representation=bound.record['representation']
    job=json.loads(run.read_input('execution_job'))['payload']['representation_jobs'][representation]
    item=json.loads(run.read_input(job['plan_input']))['producers'][bound.record['producer']]
    policy=selected(run,representation,job,item)
    require(policy is not None and job['compact_cold_handoff_input']==input_name,'cold explicit route required')
    require(type(run) is lifecycle.ResearchRun and set(vars(run))=={'admission','directory','_published_outputs','_claim_sha256'},'cold run contains untracked state')
    resident=compact_native_features.prepare(terminal,input_name=job['compact_native_features_input'])
    if 'cold_proof_input' in json.loads(run.read_input('execution_job'))['payload']:
        from . import compact_cold_proof
        compact_cold_proof.observe(run,published,terminal,resident)
    require(owner._transition.acquire(blocking=False),'concurrent cold terminal handoff')
    claimed=False;directory=None;inode=None
    try:
        terminal.lease();terminal._verify(full=True)
        require(owner.closed and owner.closing and not owner.poisoned and owner.active is None,'cold owner not successfully closed')
        require(terminal.record['status']=='complete' and terminal.record['format']==compact_terminal.FORMAT
            and terminal.record['resident_originals_retained'] is True,'cold scientific terminal differs')
        hashes=thaw(resident.features._hashes);binding=thaw(resident.binding)
        require(binding['schema_version']==3 and sorted(hashes)==list(job['descriptor']['required_graphs'])
            and hashes==binding['feature_hashes'],'cold complete scientific graph population differs')
        identity=bound.record['workflow_identity'];experiment=bound.record['experiment']
        expected=[]
        for namespace in NAMESPACES:
            path=ad.root/'research_artifacts'/namespace/identity
            if path.exists():
                require(path.resolve()==path and set(p.name for p in path.iterdir())=={experiment},'cold conflicting attempt namespace')
                expected.append(str(path.relative_to(ad.root)))
        require(sorted(expected)==policy['evidence_roots'],'cold complete evidence namespace set differs')
        guard={'resources':thaw(bound._resources),'owner':thaw(bound._owner),'base':str(bound._base)}
        _guard(run,guard,policy)
        directory=ad.root/'research_artifacts/onchain_compact_handoffs'/identity/experiment
        watch=Path(policy['watch']['root'])
        require(directory.is_relative_to(watch) and all((ad.root/p).is_relative_to(watch) for p in expected)
            and (run.directory/'outputs').is_relative_to(watch),'cold watch misses retained evidence/output')
        require(directory.resolve()==directory and not directory.exists() and not directory.is_symlink(),'cold handoff already reserved or redirected')
        output=policy['handoff_output'];require(output not in run._published_outputs and not (run.directory/'outputs'/output).exists(),'cold handoff output already reserved')
        limits={k:policy[k] for k in ('max_files','max_directories','max_total_bytes','max_file_bytes','max_depth','chunk_bytes')}
        snapshot=cold_files.capture(ad.root,tuple(expected),limits)
        stages=[{'root':str(s.root),'sha256':s.reference,'contract':thaw(s.contract)} for _,s in sorted(owner.stages.items())]
        record={'schema_version':1,'kind':KIND,'status':'complete','experiment':ad.experiment_id,
            'workflow_identity':identity,'source':ad.source,'registration_sha256':ad.registration_sha256,'runtime_hash':bound.context['runtime_hash'],
            'policy':policy,'input':input_name,'policy_sha256':ad.inputs[input_name]['sha256'],
            'terminal':thaw(terminal.record),'binding_sha256':hashlib.sha256(lifecycle._encode(binding)).hexdigest(),
            'file_pins':list(snapshot.files),'directory_pins':list(snapshot.directories),'stages':stages,
            'original_object_verification_retired':True,'external_alias_release_verified':False,
            'memory_saving_verified':False,'empirical_admission_verified':False}
        raw=canonical_bytes(record);encoded=lifecycle._encode(record)
        require(max(len(raw),len(encoded))<=min(policy['max_metadata_bytes'],policy['max_file_bytes']),'cold receipt capacity exceeded before claim')
        require(len(snapshot.files)+2<=limits['max_files'] and len(snapshot.directories)+1<=limits['max_directories']
            and sum(pin[1][4] for pin in snapshot.files)+2*len(encoded)+policy['max_metadata_bytes']<=limits['max_total_bytes'],
            'cold receipt reservation exceeds finite evidence allowance')
        durable_mkdir(directory.parent)
        inode=cold_files.durable_birth(directory);claimed=True
        start_raw=canonical_bytes({'kind':KIND,'input':input_name,'owner':owner.identity})
        cold_files.write_once(directory,inode,'start.json',start_raw,policy['max_metadata_bytes'])
        terminal.lease();terminal._verify(full=True);snapshot.check(full=True)
        cold_files.write_once(directory,inode,'complete.json',raw,policy['max_metadata_bytes']);run.write_json(output,record)
        # The new immutable receipt is also within the permanent file authority.
        snapshot=cold_files.extend(snapshot,directory,inode,{'start.json':start_raw,'complete.json':raw})
        authority=Authority(_KEY,run,record,snapshot,guard,stages,dict(run._published_outputs))
        m=compact_native_features._api()
        mapping=m._NativeMap(ad.root,thaw(resident.features._mapping._refs),thaw(resident.features._mapping._policy),
            lease=authority.lease,read_lease=authority.lease)
        features=_Features(mapping,authority,hashes,m.boundary,resident.features._chunk)
        prepared=PreparedFeatures(features,binding,None)
        require(features.verified_hashes()==hashes,'cold saved feature hashes differ')
        authority.check(full=True)
        return prepared
    except BaseException as primary:
        owner.poisoned=True
        # Never overwrite prior evidence or downgrade a failed handoff to resident fallback.
        if claimed:
            try:cold_files.write_once(directory,inode,'failed.json',canonical_bytes({'kind':KIND,'status':'failed'}),policy['max_metadata_bytes'])
            except BaseException as later:
                selected_error=cold_files.preserve(primary,later)
                if selected_error is not primary:raise selected_error
        raise
    finally:
        primary=sys.exception()
        try:owner._transition.release()
        except BaseException as later:
            owner.poisoned=True
            raise cold_files.preserve(primary,later)


def finalize(prepared):
    require(type(prepared.features) is _Features and type(prepared.features._authority) is Authority,'actual detached compact features required')
    authority=prepared.features._authority;authority.check(full=True)
    require(hashlib.sha256(lifecycle._encode(thaw(prepared.binding))).hexdigest()==authority._record['binding_sha256'],'cold final binding changed')
    require(prepared.features.verified_hashes()==dict(prepared.features._hashes),'cold final numeric population differs')
    authority.check(full=True)

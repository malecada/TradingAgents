"""Live first/successor ownership; no pair allocation or numerical routing.

A binding is a checked snapshot, not a lock. Call check at numerical boundaries
under the outer job's source freeze. Successors require registered ancestry and
observed predecessor death. Workload, checkpoint/orphan integrity and workflow
quotas must still be admitted before any pair allocation or numerical continuation.
"""
import json
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

from tradingagents.research.lifecycle import ResearchRun, _lock, _immutable
from tradingagents.research.onchain_replication import job, resources, matching_pair
from . import matching_ancestry as ancestry
from .feature_journal import FeatureJournal,required_set
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import canonical_bytes, digest, file_hash, freeze

ROOT=Path(__file__).resolve().parents[3]
SELF=str(Path(__file__).resolve().relative_to(ROOT))
LIMIT=65536

class JournalConstructionError(RuntimeError):
    """Preserved partial namespace requires outer-run closure, never local retry."""


def _creation_path(expected,root,required):
    require(expected.resolve()==expected and expected.is_relative_to(root),'journal creation path is redirected')
    ancestor=expected.parent
    while not ancestor.exists():ancestor=ancestor.parent
    info=ancestor.stat()
    require(ancestor.resolve()==ancestor and stat.S_ISDIR(info.st_mode) and info.st_dev==root.stat().st_dev,
            'journal ancestor type/device differs')
    require(equal(required_set(required),required),'required graph list must be canonical before creation')


def require(condition,message):
    if not condition:raise ValueError(message)


def equal(a,b):return canonical_bytes(a)==canonical_bytes(b)


def signature(value):
    # Reading may update atime; content identity uses modification/change clocks.
    return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))


def metadata(path,root):
    """Compact same-device regular metadata; a sole writer is still required."""
    require(path.is_absolute() and path.resolve()==path and path.is_relative_to(root),'metadata path containment differs')
    before=path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==root.stat().st_dev and before.st_size<=LIMIT,'metadata file extent/type differs')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        require(signature(os.fstat(fd))==signature(before),'metadata changed before open')
        with os.fdopen(fd,'rb',closefd=False) as stream:raw=stream.read(LIMIT+1)
        require(signature(os.fstat(fd))==signature(before) and signature(path.stat())==signature(before) and len(raw)<=LIMIT,'metadata changed during read')
    finally:os.close(fd)
    return json.loads(raw),digest(raw)


def _guard(run,p,guard_owner,base,*,execution=None):
    ad=run.admission
    args=SimpleNamespace(root=ad.root,registration=ad.registration,experiment=ad.experiment_id,source=ad.source)
    # bind already authenticated execution before acquiring the lifecycle lock.
    # Other callers retain their fresh registered-input read.
    pilot_context=(ad,execution if execution is not None else json.loads(run.read_input('execution_job'))) if p['reserve_bytes']<3*resources.GIB else None
    live=resources.assert_guarded_worker(base/'guard',job._command(args,'worker'),
        required_paths=[Path(x) for x in p['disk_paths']],wall_seconds=p['wall_seconds'],
        memory_max_bytes=p['memory_max_bytes'],memory_high_bytes=p['memory_high_bytes'],disk_floor_bytes=p['disk_floor_bytes'],pilot_context=pilot_context)
    require(equal(live.get('owner_identity'),guard_owner),'guard owner differs from admitted claim')
    require(all(k in live and equal(live[k],v) for k,v in p.items()),'guard policy differs from registration')
    require(type(live.get('monitor_pid')) is int and live['monitor_pid']==guard_owner['monitor_pid'],'live monitor differs from retained owner')
    require(job.same_process_alive(guard_owner['monitor_pid'],guard_owner['monitor_start_ticks']),'guard monitor is no longer alive')


class Binding:
    def __init__(self,run,record,context,limits,resources_policy,snapshots,guard_owner,base,ancestry_arguments=None):
        self._run=run;self.record=freeze(record);self.context=freeze(context);self.limits=freeze(limits)
        self._resources=freeze(resources_policy);self._snapshots=dict(snapshots)
        self._owner=freeze(guard_owner);self._base=base
        self._ancestry_arguments=None if ancestry_arguments is None else dict(ancestry_arguments)

    def _guard(self):
        _guard(self._run,self._resources,self._owner,self._base)

    def lease(self):
        """Cheap active claim/journal/guard check; does NOT recheck source/inputs."""
        run=self._run;run._active()
        directory=Path(self.record['journal_directory'])
        self._guard()
        if self._ancestry_arguments is None:
            require(list(directory.parent.iterdir())==[directory],'another representation owner appeared')
        else:
            ancestry.verify(run,**self._ancestry_arguments,current_journal=directory)
        require(not any((directory/name).exists() for name in ('complete.json','failed.json')),'representation journal is terminal')
        reader=metadata
        if self.record.get('resource_only') is True:
            from .import_metadata import metadata as reader
        for path,expected in self._snapshots.items():
            require(reader(path,run.admission.root)[1]==expected,'owner metadata changed after binding')
        self._guard()

    def check(self):
        """Full current-source/input/runtime and lease check; no pair work."""
        run=self._run;run._active();run._check_source();run._check_inputs()
        _source(run,self.record['numerical_source'])
        require(digest(canonical_bytes(inventory(run.admission.root,include_torch=True)))==self.context['runtime_hash'],'registered runtime changed')
        self.lease()


def _anchor_blobs(raw,sizes):
    """Parse Git's binary-safe batch frames without treating body newlines as headers."""
    require(len(raw)<=sum(sizes)+128*len(sizes),'anchor response exceeds expected source extent')
    offset=0
    for expected in sizes:
        end=raw.find(b'\n',offset,min(len(raw),offset+128))
        require(end>=0,'anchor response header missing or oversized')
        fields=raw[offset:end].split(b' ')
        require(len(fields)==3 and fields[1]==b'blob','anchor object missing or not a blob')
        matching_pair.hash_string(fields[0].decode('ascii'),40)
        require(fields[2].isdigit() and int(fields[2])==expected,'anchor source extent differs')
        offset=end+1;end=offset+expected
        require(end<len(raw) and raw[end:end+1]==b'\n','anchor body or delimiter truncated')
        yield memoryview(raw)[offset:end]
        offset=end+1
    require(offset==len(raw),'anchor response has trailing data')


def _anchor_read(root,commit,names,sizes):
    require(len(names)==len(sizes) and all(type(n) is str and '\n' not in n and '\x00' not in n for n in names),
            'anchor request contains invalid name')
    requests=''.join(commit+':'+name+'\n' for name in names).encode()
    # check_output uses communicate(input), avoiding simultaneous pipe deadlock
    # and reaping the process on failure. No results are cached across checks.
    raw=subprocess.check_output(['git','cat-file','--batch'],input=requests,cwd=root,stderr=subprocess.DEVNULL)
    yield from _anchor_blobs(raw,sizes)


def _source(run,numerical):
    ad=run.admission;registered=ad.experiment['source_files'];required=job.required_sources()
    require(required|{SELF}<=set(registered),'complete owner/execution source closure required')
    require(isinstance(numerical,dict) or hasattr(numerical,'items'),'numerical source mapping required')
    require(set(numerical)=={'commit','files'} and set(numerical['files'])==required,'numerical source closure differs')
    matching_pair.hash_string(numerical['commit'],40)
    for name in sorted(required|{SELF}):
        require(file_hash(ROOT/name)==registered[name],'imported implementation differs from admitted source')
    # Explicit exact-byte compatibility. Actual execution commit remains in the
    # owner; an older anchor is only a numerical context, never a forged owner.
    names=sorted(required)
    for name in names:
        require(numerical['files'][name]==registered[name],'numerical source differs from current execution')
    sizes=[(ROOT/name).stat().st_size for name in names]
    for name,raw in zip(names,_anchor_read(ad.root,numerical['commit'],names,sizes),strict=True):
        require(digest(raw)==numerical['files'][name],'numerical anchor committed source differs')


def bind(run,*,representation,plan_input,producer,policy_input,journal_directory=None,
         continuation_input=None,death_input=None,_create=False,_first=False,job_input='execution_job',_resource=False):
    require(isinstance(run,ResearchRun),'actual admitted ResearchRun required')
    run._active();run._check_source()
    ad=run.admission
    execution=json.loads(run.read_input(job_input))
    if _resource:
        from .resource_binding import validate_job
        validate_job(execution)
        require(continuation_input is None and death_input is None,'resource successor not admitted')
    else:
        require(job_input=='execution_job','legacy matching job input differs');job.job_schema(execution)
    require(type(execution['schema_version']) is int,'execution schema version must be integer')
    require(execution['kind']==('compact_resource' if _resource else 'fit'),'matching producer job kind differs')
    policy_resources=job.resource_policy(execution['resources'],ad.root,pilot_context=(ad,execution) if _resource else None)
    jobs=execution['payload'].get('representation_jobs',{})
    require(representation in jobs,'representation absent from execution job')
    selected=jobs[representation]
    require(selected.get('operation')=='produce' and selected.get('plan_input')==plan_input
            and selected.get('producer')==producer and selected.get('pair_checkpoint_input')==policy_input,'selected producer/policy differs')
    plan=json.loads(run.read_input(plan_input))
    require(isinstance(plan,dict) and type(plan.get('schema_version')) is int and plan['schema_version']==2 and producer in plan.get('producers',{}),'explicit version2 producer plan required')
    item=plan['producers'][producer]
    require(item.get('pair_checkpoint_input')==policy_input and equal(item.get('descriptor'),selected.get('descriptor')),'producer policy/descriptor differs')
    require(item.get('binding_output')!=item.get('journal_output') and {item.get('binding_output'),item.get('journal_output')}<=set(ad.experiment['outputs']),'producer outputs are not admitted')
    require((continuation_input is None)==(death_input is None),'continuation and death inputs must be paired')
    for key,value in [('continuation_input',continuation_input),('death_input',death_input)]:
        require(selected.get(key)==value and item.get(key)==value,'selected successor route differs')
    ancestry_arguments=None if continuation_input is None else dict(representation=representation,plan_input=plan_input,
        producer=producer,policy_input=policy_input,continuation_input=continuation_input,death_input=death_input)
    policy=json.loads(run.read_input(policy_input))
    require(isinstance(policy,dict) and set(policy)=={'schema_version','backend','limits','numerical_source'} and type(policy['schema_version']) is int and policy['schema_version']==1,'pair execution policy schema differs')
    require(equal(policy['backend'],matching_pair.BACKEND),'pair numerical backend differs')
    limits=policy['limits']
    require(isinstance(limits,dict) and set(limits)==matching_pair.POLICY_FIELDS and all(type(v) is int and v>0 for v in limits.values()),'pair limits differ')
    require(limits['chunk_edges']<=65536,'pair edge chunk exceeds bound')
    descriptor=item['descriptor']
    require(descriptor.get('arm')=='proposed','checkpoint backend requires motif representation')
    require(equal(descriptor.get('pair_execution'),{'backend':policy['backend'],'policy_sha256':ad.inputs[policy_input]['sha256']}),'explicit backend/policy workflow identity differs')
    if _resource:
        from .original_import_preparation import required_stages
        required_stages(descriptor)
        require(selected.get('original_dictionary_input')==item.get('original_dictionary_input') and type(selected.get('original_dictionary_input')) is str,'original import selection differs')
    identity=cache_key(descriptor)
    expected=ad.root/'research_artifacts/onchain_representations'/identity/ad.experiment_id
    if not _create:
        require(journal_directory is not None,'existing admitted journal directory required')
        directory=Path(journal_directory)
        require(directory==expected and directory.resolve()==expected and directory.is_dir()
                and directory.stat().st_dev==ad.root.stat().st_dev,'exact admitted journal directory required')
    # All source/runtime/policy and live-worker checks precede journal creation.
    _source(run,policy['numerical_source'])
    env=json.loads(run.read_input(execution['environment_input']))
    require(equal(env,inventory(ad.root,include_torch=True)),'registered execution environment differs')
    base=ad.root/job.PREFIX/'runs'/ad.experiment_id
    snapshots={}
    def read(path):
        reader=metadata
        if _resource:
            from .import_metadata import metadata as reader
        value,h=reader(path,ad.root);snapshots[path]=h;return value
    launch=read(base/'launch.json');guard_owner=read(base/'owner.json')
    require(set(launch)=={'experiment','source_commit','supervisor_pid','nonce'} and launch['experiment']==ad.experiment_id and launch['source_commit']==ad.source,'guard launch differs')
    require(set(guard_owner)==set(launch)|{'monitor_pid','monitor_start_ticks'} and all(equal(guard_owner[k],v) for k,v in launch.items()),'guard owner/launch join differs')
    _guard(run,policy_resources,guard_owner,base)
    if _create:
        require(journal_directory is None and ((_first and ancestry_arguments is None) or (not _first and ancestry_arguments is not None)),
                'constructor requires exact first-owner or successor mode')
        with _lock(ad.root):
            run._active();_guard(run,policy_resources,guard_owner,base,execution=execution)
            _creation_path(expected,ad.root,descriptor['required_graphs'])
            if _first:
                require(not expected.parent.exists() and not expected.parent.is_symlink(),
                        'representation namespace already reserved; fresh first owner forbidden')
                parent=None
            else:
                ancestry.verify(run,**ancestry_arguments)
                info=ad.inputs[continuation_input];path=ad.root/info['path']
                manifest,_=metadata(path,ad.root)
                require(file_hash(path)==info['sha256'],'parent changed before successor creation')
                parent={'path':str(path),'sha256':info['sha256'],'owner':manifest['owner']}
            owner={'experiment':ad.experiment_id,'source_commit':ad.source,'producer':producer,'workflow_identity':identity}
            run._active();_guard(run,policy_resources,guard_owner,base,execution=execution)
            try:
                from .feature_journal import _RESOURCE_METADATA
                journal=FeatureJournal(expected,owner,required_graphs=descriptor['required_graphs'],parent=parent,
                    **({'_metadata_role':_RESOURCE_METADATA} if _resource else {}))
                publish=_immutable
                if _resource:
                    from .import_metadata import write as write_metadata
                    publish=lambda path,value:write_metadata(path.parent,path.name,canonical_bytes(value))
                publish(expected/'claim.json',{'owner':owner,'descriptor':descriptor,'plan_input':plan_input,
                    'binding_output':item['binding_output'],'registration_sha256':ad.registration_sha256,
                    'pair_checkpoint_input':policy_input,'pair_checkpoint_policy_sha256':ad.inputs[policy_input]['sha256'],
                    'continuation_input':continuation_input,'death_input':death_input,
                    **({'job_input':job_input,'job_sha256':ad.inputs[job_input]['sha256'],'resource_only':True} if _resource else {})})
            except BaseException as error:
                if _resource and (not isinstance(error,Exception) or isinstance(error,MemoryError)):
                    error.add_note('partial resource journal preserved at '+str(expected));raise
                if not _first:raise
                raise JournalConstructionError('partial journal construction preserved at '+str(expected)) from error
        try:
            return journal,bind(run,representation=representation,plan_input=plan_input,producer=producer,
                policy_input=policy_input,journal_directory=expected,continuation_input=continuation_input,death_input=death_input,job_input=job_input,_resource=_resource)
        except BaseException as error:
            if _resource and (not isinstance(error,Exception) or isinstance(error,MemoryError)):
                error.add_note('unbound resource journal preserved at '+str(expected));raise
            if not _first:raise
            raise JournalConstructionError('unbound journal construction preserved at '+str(expected)) from error
    directory=Path(journal_directory)
    require(directory==expected and directory.resolve()==expected and directory.is_dir() and directory.stat().st_dev==ad.root.stat().st_dev,'exact admitted journal directory required')
    require(not any((directory/name).exists() for name in ('complete.json','failed.json')),'representation journal is terminal')
    owner={'experiment':ad.experiment_id,'source_commit':ad.source,'producer':producer,'workflow_identity':identity}
    require(equal(read(directory/'owner.json'),owner),'representation owner differs')
    start=read(directory/'start.json')
    require(type(start.get('schema_version')) is int and start['schema_version']==1 and equal(start.get('owner'),owner)
            and equal(start.get('required_graphs'),descriptor['required_graphs']),'journal start differs')
    if ancestry_arguments is None:
        require(start.get('parent') is None and start.get('workflow_identity') is None,'first owner cannot contain a failed parent')
        require(list(directory.parent.iterdir())==[directory],'first owner cannot omit another representation attempt')
    claim=read(directory/'claim.json')
    required_claim={'owner':owner,'descriptor':descriptor,'plan_input':plan_input,'binding_output':item['binding_output'],
        'registration_sha256':ad.registration_sha256,'pair_checkpoint_input':policy_input,'pair_checkpoint_policy_sha256':ad.inputs[policy_input]['sha256']}
    if _resource:required_claim.update(job_input=job_input,job_sha256=ad.inputs[job_input]['sha256'],resource_only=True)
    require(all(k in claim and equal(claim[k],v) for k,v in required_claim.items()),'representation claim differs')
    record={'experiment':ad.experiment_id,'source_commit':ad.source,'claim_sha256':run._claim_sha256,
        'registration_sha256':ad.registration_sha256,'representation':representation,'producer':producer,
        'workflow_identity':identity,'policy_sha256':ad.inputs[policy_input]['sha256'],
        'journal_directory':str(directory),'numerical_source':policy['numerical_source']}
    if _resource:record.update(job_input=job_input,job_sha256=ad.inputs[job_input]['sha256'],resource_only=True)
    context={'namespace':identity,'source_commit':policy['numerical_source']['commit'],'runtime_hash':digest(canonical_bytes(env))}
    bound=Binding(run,record,context,limits,policy_resources,snapshots,guard_owner,base,ancestry_arguments)
    bound.lease()
    return bound


def open_successor(run,*,representation,plan_input,producer,policy_input,continuation_input,death_input):
    """Create exactly one successor journal under verified live ownership.

    Returns (journal, binding). Pair allocation and numerical work still require
    workload, integrity, quota and orphan admission; this performs none of them.
    """
    require(continuation_input is not None and death_input is not None,'registered successor inputs required')
    return bind(run,representation=representation,plan_input=plan_input,producer=producer,
                policy_input=policy_input,continuation_input=continuation_input,death_input=death_input,_create=True)


def open_first(run,*,representation,plan_input,producer,policy_input):
    """Create one fresh journal after source/runtime/policy/live-guard admission.

    Existing namespaces, including empty or partially created ones, refuse.
    Numerical production is separate; a failed creation is never silently retried.
    """
    return bind(run,representation=representation,plan_input=plan_input,producer=producer,
                policy_input=policy_input,_create=True,_first=True)

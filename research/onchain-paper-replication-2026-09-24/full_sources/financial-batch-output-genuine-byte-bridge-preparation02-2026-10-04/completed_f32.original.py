"""Explicit completed imported Produced f32 members, never scientific Published.

Future guarded source only. No caller hashes, paths or callback can mint the
adapter. A genuine completed producer and original live held transition are
required; no active-stage HeldBatches token is extended past its stage.
"""
import hashlib,json,os,threading
from pathlib import Path
from contextlib import contextmanager
from . import compact_mcm,compact_owner,imported_mcm_identity,held_score_consumer
from . import archive_non_tail as durable
from .provenance import thaw,canonical_bytes
_WORKER=None
_LOCK=threading.RLock()
SOURCE='tradingagents/research/onchain_replication/completed_f32.py'
require=durable.require

def _source(run):
    run._active();run._check_source();run._check_inputs()
    expected=run.admission.experiment['source_files'].get(SOURCE)
    require(Path(__file__)==run.admission.root/SOURCE and type(expected) is str and hashlib.sha256(durable._source_body(Path(__file__))).hexdigest()==expected,'actual completed-f32 source not admitted')
    held_score_consumer._sources(run)

def _selected(run,job_input):
    _source(run)
    job=json.loads(run.read_input(job_input));jobs=job['payload']['representation_jobs']
    require(job['kind']=='compact_resource' and len(jobs)==1,'separate original imported resource route only')
    selected=next(iter(jobs.values()));name=selected.get(durable.KEY)
    if name is None:return None
    require(type(name) is str and name in run.admission.inputs,'registered completed population required')
    raw=run.read_input(name);require(len(raw)<=8192,'completed population metadata bound')
    policy=durable.validate_policy(json.loads(raw))
    if policy['schema_version']!=3:return None
    require(durable.encode(policy)==raw,'canonical completed population policy')
    graphs=durable._selection_graphs(run,job,name,(policy['receipt_output'],policy['terminal_output']))
    require(graphs=={s['graph'] for s in policy['slots']},'complete registered raw graph population')
    nodes=selected['descriptor']['resource_fixture']['target_nodes']
    require(set(nodes)==graphs and all(type(n) is int and 1<=n<=4 for n in nodes.values()),'explicit original tiny imported targets; larger populations need separate preparation')
    from . import selected_non_tail_transport as engine
    tx_raw=run.read_input(policy['transport_input']);tx=engine.parse_policy(tx_raw,policy)
    # Full raw container=manifest plus original32-column f32 body. Proposal and
    # actual command budgets remain separate; reserve complete upper bounds.
    parts=commands=rounded=channel=total=0
    for slot in policy['slots']:
        sizes=(8192,4*32*nodes[slot['graph']]);require(slot['max_members']==2 and slot['max_bytes']>=sum(sizes),'complete original raw container reservation insufficient')
        total+=sum(sizes)
        for size in sizes:
            for offset in range(0,size,policy['part_bytes']):
                width=min(policy['part_bytes'],size-offset);parts+=1;commands+=3
                rounded+=engine.charge(0,0,tx['stderr_bytes'],512)+engine.charge(width,0,tx['stderr_bytes'],512)+engine.charge(0,width,tx['stderr_bytes'],512)
                channel+=2*width+3*(tx['stderr_bytes']+2+512)
    require(parts<=policy['max_parts'] and commands<=policy['max_commands'] and rounded<=policy['max_rounded_bytes'],'whole raw proposal bounds')
    require(2*parts<=tx['max_parts'] and commands<=tx['max_commands'] and rounded<=tx['max_rounded_bytes'] and channel<=tx['max_channel_bytes'],'whole raw command/channel bounds')
    require(commands*(tx['command_seconds']+tx['cleanup_seconds'])<=policy['deadline_seconds']<=job['resources']['wall_seconds'],'whole raw command cleanup deadline')
    require(2*total+commands*(tx['stderr_bytes']+2)<=tx['max_local_bytes'] and 3+2*len(nodes)+6*parts<=tx['max_files'],'whole raw recovery/diagnostic local limits')
    return name,policy

class CompletedF32:
    __slots__=('_objects','_producer','_producer_pin','_reader','_cm','_closed','_failed','_frozen')
    def __setattr__(self,k,v):
        if getattr(self,'_frozen',False):raise AttributeError('completed adapter immutable')
        object.__setattr__(self,k,v)
    def __delattr__(self,k):raise AttributeError('completed adapter immutable')
    def __init__(self,produced,held):
        require(type(produced) is compact_mcm.Produced,'genuine completed MCM Produced required')
        target=produced._dictionary
        require(type(target) is imported_mcm_identity.Target,'original imported Target required; scientific NPY lineage is not this route')
        owner=target.owner;stage=produced._stage
        require(type(owner) is compact_owner.Owner and type(stage) is compact_owner.Stage and type(held) is compact_owner._HeldTransition,'actual Owner/Stage/held token required')
        self._objects=(target,stage,held,produced,owner,owner.bound,owner.bound._run)
        self._producer=produced;self._producer_pin=canonical_bytes(thaw(produced.record))
        self._reader=None;self._cm=None;self._closed=False;self._failed=False;self._frozen=True
        try:
            self._authority();api=held_score_consumer._api(owner.bound._run)
            ticket=produced.record['output'];root=Path(ticket['directory'])/'artifact'
            cm=api.content.open_local(root,kind='mcm-output',document_sha256=ticket['artifact_sha256'])
            reader=cm.__enter__();object.__setattr__(self,'_cm',cm);object.__setattr__(self,'_reader',reader)
            self._checked()
        except BaseException as primary:self._close(primary)
    def _authority(self):
        require(not self._closed and not self._failed,'completed adapter revoked/closed')
        target,stage,held,produced,owner,bound,run=self._objects
        require(produced is self._producer and produced._dictionary is target and produced._stage is stage and produced._graph is target.graph and target.owner is owner and owner.bound is bound and bound._run is run,'completed original object ancestry changed')
        require(type(produced) is compact_mcm.Produced and type(target) is imported_mcm_identity.Target and bound.record.get('resource_only') is True,'genuine imported Produced authority required')
        held.check(owner);require(stage.closed and owner.active is None and not owner.closed and not owner.poisoned and owner.stages.get(stage.name) is stage,'completed current-owner stage required')
        require(canonical_bytes(thaw(produced.record))==self._producer_pin,'original producer completion changed')
        _source(run);compact_owner.verify_current(owner)
        # Private actual verifier under the original held lock: no recursive
        # public Produced.check(), no substitute hashes or semantic recasting.
        produced._check();held.check(owner)
        require(stage.closed and owner.active is None and produced._dictionary is target and produced._stage is stage and canonical_bytes(thaw(produced.record))==self._producer_pin,'completed authority changed during verification')
    def _checked(self):
        try:
            self._authority();self._reader.check()
            require(self._reader.kind=='mcm-output' and self._reader.reference==self._producer.record['output']['artifact_sha256'] and self._reader.root==Path(self._producer.record['output']['directory'])/'artifact','original raw container differs')
            require({n for n,_ in self._reader._pin}=={'manifest.json','matrix.f32'},'complete raw companions required')
            self._authority();self._reader.check()
        except BaseException:
            object.__setattr__(self,'_failed',True);self._objects[4].poisoned=True;raise
    def read_part(self,name,offset,count):
        try:
            self._checked();require(name=='matrix.f32' and type(offset) is int and offset>=0 and offset%4==0 and type(count) is int and 0<count<=1048576 and count%4==0,'bounded original f32-aligned payload range')
            raw=self._reader.read_part(name,offset,count);self._checked();return raw
        except BaseException:
            object.__setattr__(self,'_failed',True);self._objects[4].poisoned=True;raise
    def _close(self,primary=None):
        if self._closed:
            if primary is not None:raise primary
            return
        failure=primary
        def attempt(action):
            nonlocal failure
            try:action()
            except BaseException as error:failure=durable.select(failure,error)
        if self._reader is not None:attempt(self._checked)
        cm=self._cm;object.__setattr__(self,'_cm',None)
        if cm is not None:attempt(lambda:cm.__exit__(None,None,None))
        attempt(self._authority)
        object.__setattr__(self,'_closed',True)
        if failure is not None:
            object.__setattr__(self,'_failed',True);self._objects[4].poisoned=True;raise failure

@contextmanager
def open_completed(produced,held):
    source=CompletedF32(produced,held)
    try:yield source
    except BaseException as primary:source._close(primary);raise
    else:source._close()

@contextmanager
def completed_worker(run,*,job_input='execution_job'):
    """Future genuine caller surrounds original producer; never starts a run."""
    global _WORKER
    with _LOCK:
        require(_WORKER is None,'another raw worker scope is active')
        selection=_selected(run,job_input);require(selection is not None,'explicit completed raw selection required')
        context=durable.Context(run,policy_input=selection[0],job_input=job_input)
        try:
            require(type(context) is durable.Context and context.policy['schema_version']==3 and context.run is run,'genuine selected raw Context required')
            context.check();_WORKER=context
        except BaseException as primary:durable.close_all([lambda:context.close(primary)],primary)
    failure=None
    try:yield context
    except BaseException as primary:failure=primary
    finally:
        try:context.close(failure)
        except BaseException as error:failure=durable.select(failure,error)
        finally:
            with _LOCK:
                if _WORKER is context:_WORKER=None
        if failure is not None:raise failure

def consume_if_selected(produced,held):
    require(type(produced) is compact_mcm.Produced,'genuine produced object required')
    target=produced._dictionary
    require(type(target) is imported_mcm_identity.Target,'raw imported route only; no scientific Published substitution')
    run=target.owner.bound._run;selected=_selected(run,target.owner.bound.record['job_input'])
    if selected is None:return False
    with _LOCK:
        context=_WORKER
        require(type(context) is durable.Context and context.run is run and context.input==selected[0] and context.policy==selected[1],'selected raw worker scope absent or changed')
        context.check()
    with open_completed(produced,held) as source:
        operation=context.bind(source).claim();operation.dispatch();context.check()
    held.check(target.owner);produced._check();return True

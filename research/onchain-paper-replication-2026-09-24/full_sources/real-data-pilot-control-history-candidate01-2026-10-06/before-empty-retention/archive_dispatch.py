"""Explicit outer archive dispatch; preparation does not admit SSH or resources.

One original job context shares durable conservative payload reservations across
all selected representations. Only existing private held-operation wrappers may
activate transport calls. No recovery, refund, retry or remote deletion API.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from threading import get_ident, Lock

from ..lifecycle import ResearchRun, _encode
from . import archive_transport as low, matching_owner
from .provenance import canonical_bytes, digest, freeze, thaw

KEY='compact_archive_transport_input'
FORMAT='archive-dispatch-v1'
META=131072


def require(value,message):
    if not value:raise ValueError(message)


def capacity(*,max_events,chunk_events,record_bytes,stages,reads):
    require(all(type(v) is int and 0<v<2**63 for v in (max_events,chunk_events,record_bytes,stages,reads)), 'finite archive dispatch population required')
    chunks=(max_events+chunk_events-1)//chunk_events
    full,last=divmod(max_events,chunk_events)
    rounded=full*((chunk_events*record_bytes//low.BLOCK_BYTES+1)*low.BLOCK_BYTES)
    if last:rounded+=(last*record_bytes//low.BLOCK_BYTES+1)*low.BLOCK_BYTES
    payload=max_events*record_bytes
    result={'logical_bytes':stages*payload*(3+reads),
        'rounded_bytes':stages*(payload+(2+reads)*rounded),
        'commands':stages*chunks*(4+reads),'chunks':stages*chunks}
    require(all(v<2**63 for v in result.values()),'archive dispatch capacity overflow')
    return result


def _connection(value):
    require(type(value) is dict and set(value)=={'host','user','port','identity_file','known_hosts_file'},'explicit transport connection required')
    for key in ('host','user'):
        require(type(value[key]) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,252}',value[key]),'transport endpoint differs')
    require(type(value['port']) is int and 1<=value['port']<=65535,'transport port differs')
    for key in ('identity_file','known_hosts_file'):
        p=value[key]
        require(type(p) is str and p.startswith('/') and len(p)<=4096 and not any(ord(c)<32 or ord(c)==127 for c in p),'transport authentication path required')
    return hashlib.sha256(json.dumps({'format':'archive-ssh-transport-v1','connection':value},sort_keys=True).encode()).hexdigest()


def policy(value):
    fields={'schema_version','format','connection','rate_kbit','max_seconds','max_payload_bytes',
        'max_commands','max_diagnostic_bytes','max_control_bytes','namespace','receipt_output','terminal_output'}
    typed=type(value) is dict and value.get('schema_version')==2
    history=type(value) is dict and 'control_history' in value
    if history:
        from .archive_control_history import validate
        require(typed,'control history only explicit typed resource route');validate(value['control_history'])
        fields=fields|{'control_history'}
    require(type(value) is dict and set(value)==fields|({'typed_payload_input'} if typed else set()) and value['schema_version']==(2 if typed else 1) and value['format']==FORMAT,'archive dispatch policy schema')
    if typed:require(type(value['typed_payload_input']) is str and bool(value['typed_payload_input']),'registered typed payload input required')
    _connection(value['connection'])
    require(all(type(value[k]) is int and 0<value[k]<2**63 for k in
        ('rate_kbit','max_seconds','max_payload_bytes','max_commands','max_diagnostic_bytes','max_control_bytes')),'positive transport limits required')
    require(type(value['namespace']) is str and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}',value['namespace']),'fresh transport namespace required')
    outputs=[value[k] for k in ('receipt_output','terminal_output')]
    require(all(type(v) is str and Path(v).name==v and v not in ('','.', '..') for v in outputs) and len(set(outputs))==2,'distinct registered archive control outputs required')
    return value


@dataclass(frozen=True)
class Plan:
    run: object
    record: object


def preflight(run,payload,compact_routes,*,job_input='execution_job'):
    """All selected representations before population work; creates no namespace."""
    execution=json.loads(run.read_input(job_input))
    if execution.get('kind')=='compact_resource':
        require(type(run) is ResearchRun,'actual real-pilot archive Run required')
        run._active();run._check_source()
        from .real_pilot_import_caller import admitted
        name,selected,pilot=admitted(run.admission,execution)
        require(pilot['schema_version']==2 and 'archive_inputs' in pilot and compact_routes=={name:True},'explicit schema2 real-pilot archive dispatch required')
        require(canonical_bytes(execution['payload'])==canonical_bytes(payload),'archive dispatch actual job differs')
    else:
        require(execution['kind']=='fit' and canonical_bytes(execution['payload'])==canonical_bytes(payload),'archive dispatch actual job differs')
    selected={};names=set();remote=set();total={'logical_bytes':0,'rounded_bytes':0,'commands':0,'chunks':0}
    from . import compact_training, archive_pair_writer, archive_owner_policy
    for representation,job in payload['representation_jobs'].items():
        item=json.loads(run.read_input(job['plan_input']))['producers'][job['producer']] if job.get('operation')=='produce' else {}
        name=job.get(KEY);other=item.get(KEY)
        archive=job.get('compact_archive_input') or item.get('compact_archive_input')
        if archive is None and name is None and other is None:continue
        require(isinstance(run,ResearchRun),'actual archive dispatch ResearchRun required');run._active()
        require(compact_routes.get(representation) is True and job['operation']=='produce','archive dispatch requires actual compact route')
        require(type(name) is str and name==other and name in run.admission.inputs,'archive transport both-plan input differs')
        compact_training._archive_extension(run,job,item)
        config=policy(json.loads(run.read_input(name)));names.add(name)
        archived=json.loads(run.read_input(archive))
        require(set(archived)==archive_owner_policy.FIELDS and archived['schema_version']==1
            and archived['backend']==archive_owner_policy.BACKEND,'archive policy schema differs before population')
        positive=archive_owner_policy.FIELDS-{'schema_version','backend','transport_identity','remote_namespace'}
        require(all(type(archived[k]) is int and 0<archived[k]<2**63 for k in positive)
            and archived['max_stage_verifications']<=1024,'archive policy allowances differ before population')
        require(archived['transport_identity']==_connection(config['connection']),'archive endpoint identity differs from registered policy')
        require(type(archived['remote_namespace']) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,19}',archived['remote_namespace']),
            'archive remote namespace differs before population')
        require(archived['remote_namespace'] not in remote,'archive representations must have distinct remote namespaces')
        remote.add(archived['remote_namespace'])
        if execution.get('kind')=='compact_resource':
            mcm_policy=json.loads(run.read_input(job['compact_mcm_input']))
            if mcm_policy.get('schema_version')==2 and 'durability' in mcm_policy:
                # Eager dependency only; genuine MCM validator admits policy.
                from . import chunk_durability
        envelope=json.loads(run.read_input(job['compact_policy_input']))
        limits=envelope['stage_policy']['log'];stages=1+len(job['descriptor']['required_graphs'])
        bound=capacity(max_events=limits['max_events'],chunk_events=limits['chunk_events'],record_bytes=archive_pair_writer.events.RECORD_BYTES,stages=stages,reads=archived['max_stage_verifications'])
        require(bound['logical_bytes']<=archived['max_decoded_transfer_bytes'] and
            stages*limits['max_events']*archive_pair_writer.events.RECORD_BYTES<=archived['max_remote_payload_bytes'],
            'archive logical capacity insufficient before population')
        for k in total:total[k]+=bound[k]
        selected[representation]={'job_sha256':digest(canonical_bytes(job)), 'workflow_identity':digest(canonical_bytes(job['descriptor'])),
            'policy_input':archive,'policy_sha256':run.admission.inputs[archive]['sha256'],
            'remote_namespace':archived['remote_namespace'],'capacity':bound}
    if not selected:return None
    require(len(names)==1,'all archive representations require one job-wide transport policy input')
    name=names.pop();config=policy(json.loads(run.read_input(name)))
    typed_record=None
    if config['schema_version']==2:
        require(execution['kind']=='compact_resource' and len(selected)==1,'typed storage only selected single real resource representation')
        # Load selected helpers before the imported authority lease captures its
        # actual module/code baseline. Legacy policies do not import this path.
        from . import typed_payload_policy, typed_payload_operations, typed_score_store, typed_tail_binding, mcm_raw_parts
        if 'control_history' in config:
            from . import archive_control_history

        role=config['typed_payload_input']
        require(role in run.admission.inputs,'typed payload input unregistered')
        raw=run.read_input(role);typed=typed_payload_policy.validate(json.loads(raw))
        expected_graphs=set()
        for item in payload['representation_jobs'].values():expected_graphs.update(item['descriptor']['required_graphs'])
        require(set(typed['graphs'])==expected_graphs,'typed full graph roster differs')
        extra=typed_payload_policy.capacity(typed)
        for k in total:total[k]+=extra[k]
        typed_record={'input':role,'input_sha256':digest(raw),'policy':typed,'capacity':extra}
    require(total['rounded_bytes']<=config['max_payload_bytes'] and total['commands']<=config['max_commands'],'insufficient whole-job rounded transport allowance')
    # Each diagnostic has a finite escaped stderr receipt, plus the finite payload.
    if 'control_history' in config:
        from .archive_control_history import capacity as control_capacity
        bounds=control_capacity(config['control_history'],config['max_commands'])
        require(config['max_diagnostic_bytes']>=bounds['diagnostic_bytes'] and config['max_control_bytes']>=bounds['control_bytes'],'insufficient bounded retained controls/failure headroom')
    else:
        require(config['max_diagnostic_bytes']>=config['max_payload_bytes']+META*config['max_commands'],'insufficient cumulative diagnostic allowance')
        require(config['max_control_bytes']>=META*(8+4*config['max_commands']),'insufficient durable reservation/failure headroom')
    require({config['receipt_output'],config['terminal_output']}<=set(run.admission.experiment['outputs']),'archive terminal/control outputs unregistered')
    record={'schema_version':1,'format':FORMAT,'experiment':run.admission.experiment_id,'source_commit':run.admission.source,
        'claim_sha256':run._claim_sha256,'input':name,'input_sha256':run.admission.inputs[name]['sha256'],
        'job_sha256':digest(canonical_bytes(execution)),'policy':config,'representations':selected,'capacity':total,
        'job_input':job_input,'job_input_sha256':run.admission.inputs[job_input]['sha256'],
        'units':'logical reservations and rounded payload reservations exclude SSH wire overhead','execution_admitted':False}
    if typed_record is not None:record['typed_payloads']=typed_record
    return Plan(run,freeze(record))


def _fatal(error):return not isinstance(error,Exception) or isinstance(error,MemoryError)


def _retain(primary,error):
    if primary is None:return error
    if primary is error:return primary
    if not _fatal(primary) and _fatal(error):error.__cause__=primary;return error
    primary.add_note('archive dispatch cleanup: '+repr(error)[:512]);return primary


def _close_owned(action):
    """Close exactly once; uncertainty cannot replace an existing fatal."""
    primary=sys.exc_info()[1]
    try:action()
    except BaseException as error:
        if primary is not None and _fatal(primary):
            primary.add_note('archive owned close uncertainty: '+repr(error)[:512])
            raise primary
        if _fatal(error):raise error from primary
        failure=low.archive.io.CleanupFailure('archive owned close uncertain; no retry')
        failure.add_note(repr(error)[:512])
        raise failure from primary


class _Budget:
    def __init__(self,context):self.context=context
    @property
    def remaining(self):return self.context._limits['max_payload_bytes']-self.context._spent['rounded_bytes']
    def reserve(self,size):self.context._reserve(size)


class _Transport(low.Transport):
    def next(self,kind):
        c=self._dispatch_context;c._live()
        require(c._in_call and not c._diagnostic_started,'archive diagnostic allocation outside original command')
        result=super().next(kind)
        c._counter=self.counter;c._diagnostic_started=True
        if c._history is not None:c._diagnostic_file=result.name
        return result


class View:
    __slots__=('_context','_name','identity')
    def __init__(self,context,name):
        object.__setattr__(self,'_context',context);object.__setattr__(self,'_name',name)
        object.__setattr__(self,'identity',context._transport.identity)
    def __setattr__(self,key,value):raise AttributeError('archive dispatch view is immutable')
    def mkdir(self,path):return self._context._call(self,'mkdir',path)
    def put(self,source,path):return self._context._call(self,'put',source,path)
    def get(self,path,destination,*,expected_bytes):return self._context._call(self,'get',path,destination,expected_bytes=expected_bytes)


class Context:
    def __init__(self,plan):
        require(type(plan) is Plan,'preflight archive dispatch plan required')
        self._run=plan.run;self._record=thaw(plan.record);self._limits=self._record['policy']
        self._run._active();self._run._check_source()
        require(digest(self._run.read_input(self._record['input']))==self._record['input_sha256'],'archive transport input changed')
        from . import job
        self._base=self._run.admission.root/job.PREFIX/'runs'/self._run.admission.experiment_id
        require(self._run.admission.inputs[self._record['job_input']]['sha256']==self._record['job_input_sha256'],'archive job input identity changed')
        execution=json.loads(self._run.read_input(self._record['job_input']));self._resources=execution['resources']
        require(digest(canonical_bytes(execution))==self._record['job_sha256'],'original archive execution job changed')
        self._guard,self._guard_sha=matching_owner.metadata(self._base/'owner.json',self._run.admission.root)
        launch,self._launch_sha=matching_owner.metadata(self._base/'launch.json',self._run.admission.root)
        require(launch['experiment']==self._record['experiment'] and launch['source_commit']==self._record['source_commit'] and all(self._guard.get(k)==v for k,v in launch.items()),'original archive launch/owner differs')
        matching_owner._guard(self._run,self._resources,self._guard,self._base)
        parent=self._run.admission.root/'research_artifacts'
        require(parent.is_dir() and parent.resolve()==parent,'canonical admitted artifact scaffold required')
        self._parent_inode=self._signature(parent)
        require(any(parent==Path(p) or parent.is_relative_to(Path(p)) for p in self._resources['disk_paths']),
            'archive context filesystem not covered by registered guard')
        self.root=parent/('archive-dispatch-'+self._limits['namespace'])
        require(not os.path.lexists(self.root),'archive transport namespace already reserved')
        self.root.mkdir();self._inode=self._signature(self.root)
        self._history_policy=self._limits.get('control_history');self._history=None;self._control_journal=None;self._diagnostic_journal=None
        self._publication_count=0;self._root_control_bytes=0;self._diagnostic_receipts=0;self._diagnostic_file=None
        if self._history_policy is not None:
            from .archive_control_history import Interval,Journal
            self._history=Interval(self._history_policy)
            self._control_journal=Journal(self.root/'controls',record_bytes=self._history_policy['success_control_bytes'],total_bytes=self._limits['max_control_bytes']-8*META,records=4*self._limits['max_commands'],shard_bytes=self._history_policy['shard_bytes'])
        self._expected={};self._bytes=0;self._spent={'rounded_bytes':0,'logical_bytes':0,'commands':0};self._spent_pin=canonical_bytes(self._spent)
        self._closed=False;self._failed=False;self._cap=None;self._in_call=False;self._lock=Lock();self._claims=set()
        try:
            parent_path,parent_fd=low.archive.io._open(parent)
            try:
                parent_inode=low.archive.io._signature(os.fstat(parent_fd))[:2]
                require(parent_inode==self._parent_inode,'original archive parent replaced before synchronization')
                os.fsync(parent_fd);low.archive.io._root(parent_path,parent_fd)
                require(self._signature(parent)==parent_inode and self._signature(self.root)==self._inode,'archive parent changed during context birth')
            finally:_close_owned(lambda:os.close(parent_fd))
            self._publish('intent.json',self._record)
            self._budget=_Budget(self);self._callback=self._live
            self._transport=_Transport(self._limits['connection'],self.root/'diagnostics',self._budget,
                lease_callback=self._callback,rate_kbit=self._limits['rate_kbit'],max_seconds=self._limits['max_seconds'],
                **({'receipt_sink':self._receive_control} if self._history is not None else {}))
            self._transport._dispatch_context=self
            self._diag_inode=self._signature(self._transport.diagnostics);self._counter=0
            if self._history is not None:
                self._diagnostic_journal=Journal(self.root/'diagnostic-controls',record_bytes=self._history_policy['success_diagnostic_bytes'],total_bytes=self._limits['max_diagnostic_bytes']-META-low.archive.MAX_BYTES,records=self._limits['max_commands'],shard_bytes=self._history_policy['shard_bytes'])
            self._history_bundle=(self._history,self._control_journal,self._diagnostic_journal)
            self._diagnostic_pins={}
            self._configuration=self._config();self._config_pin=canonical_bytes(self._configuration)
            self._views={name:View(self,name) for name in self._record['representations']}
            self._run.write_json(self._limits['receipt_output'],{'context':str(self.root.relative_to(self._run.admission.root)),
                'intent_sha256':digest(self._expected['intent.json']),'inode':list(self._inode),'transport_input_sha256':self._record['input_sha256'],
                'representations':self._record['representations']})
            self._receipt_sha=self._run._published_outputs[self._limits['receipt_output']]
            self._receipt_inode=low.archive.io._signature((self._run.directory/'outputs'/self._limits['receipt_output']).lstat())
            self._outer()
        except BaseException as primary:
            result={'status':'failed','phase':'construction','error_type':type(primary).__name__,
                'spent':self._spent,'transport_input_sha256':self._record['input_sha256']}
            failure=primary
            try:self._publish('constructor-failed.json',result)
            except BaseException as error:failure=_retain(failure,error)
            try:self._run.write_json(self._limits['terminal_output'],result)
            except BaseException as error:failure=_retain(failure,error)
            self._closed=True
            raise failure

    @staticmethod
    def _signature(path):
        value=path.lstat();require(stat.S_ISDIR(value.st_mode) and path.resolve()==path,'archive context directory redirected')
        return value.st_dev,value.st_ino

    def _config(self):
        t=self._transport
        return {'record':self._record,'root':str(self.root),'inode':self._inode,'host':t.host,'identity':t.identity,
            'ssh':t.ssh,'scp':t.scp,'rate':t.rate_bytes,'seconds':t.max_seconds,'diagnostics':str(t.diagnostics)}

    def _publish(self,name,value):
        raw=canonical_bytes(value)
        if self._history is not None and (name.startswith(('command-','result-','reservation-','operation-','typed-')) and 'failed' not in name):
            if len(raw)>self._history_policy['success_control_bytes']:
                # Preserve the exact refused original record in finite failure
                # headroom; no command success or retry is inferred.
                self._publish('oversize-'+name,value)
                raise ValueError('original success control exceeds selected record cap; retained, stop')
            self._control_journal.append(name,raw);self._bytes+=len(raw);self._publication_count+=1;return
        if self._history is not None:
            require(self._root_control_bytes+len(raw)<=8*META,'failure/control headroom exhausted')
            self._root_control_bytes+=len(raw)
        require(len(raw)<=META and self._bytes+len(raw)<=self._limits['max_control_bytes'],'archive control allowance exhausted')
        require(self._signature(self.root)==self._inode,'original archive context changed')
        path,fd=low.archive.io._open(self.root)
        try:
            low.archive.io._write(fd,name,raw);low.archive.io._root(path,fd)
        finally:_close_owned(lambda:os.close(fd))
        self._expected[name]=raw;self._bytes+=len(raw);self._publication_count+=1

    def _receive_control(self,path,raw,success):
        require(self._history is not None and self._in_call and path.parent==self.root/'diagnostics' and self._diagnostic_receipts<self._spent['commands'],'receipt outside actual selected command')
        self._diagnostic_receipts+=1
        if success and len(raw)<=self._history_policy['success_diagnostic_bytes']:
            self._diagnostic_journal.append(path.name,raw)
        else:
            require(len(raw)<=META,'failed original diagnostic exceeds finite headroom')
            root,fd=low.archive.io._open(path.parent)
            try:low.archive.io._write(fd,path.name,raw);low.archive.io._root(root,fd)
            finally:_close_owned(lambda:os.close(fd))
            if success:raise ValueError('original successful diagnostic exceeds selected compact cap; bytes retained, stop')

    def _outer(self,*,sampled=False):
        require(not self._closed,'archive context closed')
        self._run._active()
        require(self._run._claim_sha256==self._record['claim_sha256'],'archive original run claim differs')
        require(canonical_bytes(self._config())==self._config_pin and self._transport.budget is self._budget and self._transport.live is self._callback,'archive mutable transport configuration differs')
        require(type(self._transport) is _Transport and self._transport._dispatch_context is self
            and set(vars(self._transport))=={'identity','host','ssh','scp','rate_bytes','max_seconds','live','budget','diagnostics','counter','_dispatch_context'}|({'_receipt_sink'} if self._history is not None else set())
            and self._budget.context is self,'archive transport adapter replaced')
        require(self._transport.counter==self._counter and canonical_bytes(self._spent)==self._spent_pin,'archive transport counter refund/replacement')
        require(self._signature(self.root)==self._inode and self._signature(self.root/'diagnostics')==self._diag_inode,'original archive namespace replaced')
        for path,expected in ((self._base/'owner.json',self._guard_sha),(self._base/'launch.json',self._launch_sha)):
            require(matching_owner.metadata(path,self._run.admission.root)[1]==expected,'archive original guard evidence changed')
        matching_owner._guard(self._run,self._resources,self._guard,self._base)
        require(self._signature(self.root.parent)==self._parent_inode and self._signature(self.root)==self._inode
            and self._signature(self.root/'diagnostics')==self._diag_inode,'archive original namespace changed across guard callback')
        if self._history is not None:
            require(all(a is b for a,b in zip((self._history,self._control_journal,self._diagnostic_journal),self._history_bundle)) and self._history.p==self._limits['control_history'] and self._history_policy==self._limits['control_history'],'selected history objects/policy replaced')
            require(self._transport._receipt_sink==self._receive_control,'selected receipt sink replaced')
            self._history.check(self._full_history,force=not sampled)
            return
        self._full_history()

    def _full_history(self):
        root,fd=low.archive.io._open(self.root)
        try:
            low.archive._inventory(fd,set(self._expected)|{'diagnostics'}|({'controls','diagnostic-controls'} if self._history is not None else set()))
            for name,raw in self._expected.items():require(low.archive.io._read(fd,name,META)==raw,'archive original reservation changed')
            low.archive.io._root(root,fd)
        finally:_close_owned(lambda:os.close(fd))
        receipt=self._run.directory/'outputs'/self._limits['receipt_output']
        require(low.archive.io._signature(receipt.lstat())==self._receipt_inode and matching_owner.metadata(receipt,self._run.admission.root)[1]==self._receipt_sha,'archive context output anchor changed')
        if self._history is not None:
            self._control_journal.audit();self._diagnostic_journal.audit()
        snapshot=self._diagnostics()
        require(all(snapshot.get(k)==v for k,v in self._diagnostic_pins.items()),'original archive diagnostic changed')
        require(self._signature(self.root)==self._inode,'original archive namespace changed during local checks')

    def _output_anchor(self,name,raw,original=None):
        path=self._run.directory/'outputs'/name
        before=low.archive.io._signature(path.lstat())
        require(original is None or before==original,'original archive terminal output replaced')
        require(self._run._published_outputs.get(name)==digest(raw)
            and matching_owner.metadata(path,self._run.admission.root)[1]==digest(raw)
            and low.archive.io._signature(path.lstat())==before,'archive terminal output differs from original expected bytes')
        return before

    def _diagnostics(self):
        root,fd=low.archive.io._open(self.root/'diagnostics');result={};total=0
        try:
            require(low.archive.io._signature(os.fstat(fd))[:2]==self._diag_inode,'original archive diagnostics directory changed')
            scanner=os.scandir(fd)
            try:
                for entry in scanner:
                    name=entry.name
                    require(re.fullmatch(r'(?:command|get)-[0-9]{4,}\.bin(?:\.transport\.json)?',name),'foreign archive diagnostic')
                    require(len(result)<(2 if self._history is not None else 2*self._spent['commands']),'archive diagnostic count exceeded')
                    if self._history is not None:require(self._diagnostic_file is not None and name in (self._diagnostic_file,self._diagnostic_file+'.transport.json'),'diagnostic outside actual current command')
                    child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
                    try:
                        before=os.fstat(child);signature=low.archive.io._signature(before)
                        limit=META if name.endswith('.json') else (low.archive.MAX_BYTES if self._history is not None else self._limits['max_payload_bytes'])
                        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=limit,'archive diagnostic type/extent changed')
                        total+=before.st_size;require(total<=(META+low.archive.MAX_BYTES if self._history is not None else self._limits['max_diagnostic_bytes']),'archive diagnostic cumulative allowance exceeded')
                        h=hashlib.sha256();remaining=before.st_size
                        while remaining:
                            raw=os.read(child,min(65536,remaining));require(raw,'archive diagnostic truncated');h.update(raw);remaining-=len(raw)
                        require(not os.read(child,1) and low.archive.io._signature(os.fstat(child))==signature
                            and low.archive.io._signature(os.stat(name,dir_fd=fd,follow_symlinks=False))==signature,'archive diagnostic changed while reading')
                        result[name]={'signature':list(signature),'sha256':h.hexdigest(),'bytes':before.st_size}
                    finally:_close_owned(lambda:os.close(child))
            finally:_close_owned(scanner.close)
            low.archive.io._root(root,fd)
        finally:_close_owned(lambda:os.close(fd))
        return result

    def _live(self):
        self._outer(sampled=True);cap=self._cap
        require(cap is not None and cap['thread']==get_ident(),'transport outside live archive operation')
        cap['held'].check(cap['ledger'].owner);cap['lease']()
        require(self._cap is cap and cap['ledger'].selection._transport is cap['view'],'archive operation revoked or transport replaced')
        self._outer(sampled=True)

    def view(self,name):return self._views[name]

    def _reserve(self,size):
        self._live()
        require(self._in_call and type(size) is int and 0<=size<=self._budget.remaining,'archive rounded payload allowance exhausted')
        self._spent['rounded_bytes']+=size;self._spent_pin=canonical_bytes(self._spent)
        self._publish('reservation-%08d.json'%(self._publication_count if self._history is not None else len(self._expected)),{'spent':self._spent,'bytes':size,'claim':self._cap['claim_sha256']})

    def _call(self,view,kind,*args,**kwargs):
        require(self._lock.acquire(blocking=False),'concurrent/reentrant archive transport call')
        primary=None;started=False
        try:
            self._live();require(self._cap['view'] is view and not self._failed,'wrong archive representation or failed context')
            remote=args[1] if kind=='put' else args[0]
            suffix='' if kind=='mkdir' else '/payload.bin'
            require(type(remote) is str and re.fullmatch(re.escape(self._cap['remote_prefix'])+r'-[0-9]{12}'+re.escape(suffix),remote),'archive remote member outside captured stage')
            require(self._spent['commands']<self._limits['max_commands'],'archive command allowance exhausted')
            started=True
            self._spent['commands']+=1;self._spent_pin=canonical_bytes(self._spent)
            self._publish('command-%08d.json'%self._spent['commands'],{'kind':kind,'spent':self._spent,'claim':self._cap['claim_sha256']})
            # next() increments once before the next callback for each operation.
            self._in_call=True;self._diagnostic_started=False
            # Constructor configuration is immutable; adapter's own next() is
            # the sole permitted transition of its diagnostics counter.
            result=getattr(self._transport,kind)(*args,**kwargs)
            self._live()
            if self._history is not None:
                require(self._diagnostic_receipts==self._spent['commands'],'actual original command receipt absent')
                # Successful command outputs are exactly zero bytes. Preserve
                # their original name/stat/empty hash before removing only that
                # empty staging file; get bodies remain caller-owned.
                empty_records=[]
                for empty in (self.root/'diagnostics').iterdir():
                    if empty.name.startswith('command-') and empty.name.endswith('.bin'):
                        st=empty.lstat();require(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size==0,'successful command output not empty')
                        empty_records.append({'name':empty.name,'stat':list(low.archive.io._signature(st)),'sha256':digest(b''),'bytes':0})
                        require(low.archive.io._signature(empty.lstat())==low.archive.io._signature(st),'empty command staging changed')
                        empty.unlink()
                low.sync_directory(self.root/'diagnostics')
            diagnostic_snapshot=self._diagnostics()
            delta={k:v for k,v in diagnostic_snapshot.items() if k not in self._diagnostic_pins}
            self._diagnostic_pins=diagnostic_snapshot
            self._publish('result-%08d.json'%self._spent['commands'],{'status':'complete','spent':self._spent,
                'diagnostics':delta,**({'empty_staging':empty_records} if self._history is not None else {})})
            return result
        except BaseException as error:
            primary=error
            if started:
                self._failed=True
                delta={}
                try:
                    snapshot=self._diagnostics()
                    require(all(snapshot.get(k)==v for k,v in self._diagnostic_pins.items()),'original archive diagnostic changed during failure')
                    delta={k:v for k,v in snapshot.items() if k not in self._diagnostic_pins}
                    self._diagnostic_pins=snapshot
                except BaseException as cleanup:primary=_retain(primary,cleanup)
                try:self._publish('command-failed-%08d.json'%self._spent['commands'],{'error_type':type(primary).__name__,'spent':self._spent,'diagnostics':delta})
                except BaseException as cleanup:primary=_retain(primary,cleanup)
            raise primary
        finally:self._in_call=False;self._lock.release()

    def close(self,primary=None):
        require(not self._closed and self._cap is None and not self._in_call,'archive context duplicate/active close')
        failure=primary
        try:self._outer();self._run._check_source()
        except BaseException as error:failure=_retain(failure,error)
        result={'status':'failed' if failure is not None or self._failed else 'complete','intent_sha256':digest(self._expected['intent.json']),
            'spent':self._spent,'error_type':type(failure).__name__ if failure else None,'wire_bytes_measured':False}
        try:self._publish('terminal.json',result)
        except BaseException as error:failure=_retain(failure,error)
        if failure is not None:
            result={**result,'status':'failed','error_type':type(failure).__name__}
        output_pin=None;output_raw=_encode(result)
        try:
            self._run.write_json(self._limits['terminal_output'],result)
            output_pin=self._output_anchor(self._limits['terminal_output'],output_raw)
        except BaseException as error:failure=_retain(failure,error)
        try:
            self._outer()
            require(output_pin is not None,'archive original terminal output unavailable')
            self._output_anchor(self._limits['terminal_output'],output_raw,output_pin)
        except BaseException as error:failure=_retain(failure,error)
        if failure is not None:
            try:self._publish('close-failed.json',{'error_type':type(failure).__name__,'intent_sha256':digest(self._expected['intent.json'])})
            except BaseException as error:failure=_retain(failure,error)
        self._closed=True
        if failure is not None:raise failure


@contextmanager
def binding(transport,ledger,stage,claim,held,lease):
    """Private wrappers supply the actual captured held token, never public lease."""
    if type(transport) is not View:
        yield;return
    from . import archive_owner_operations as operations
    require(type(ledger) is operations.Ledger and type(stage) is operations.owners.Stage
        and type(claim) is operations.Operation and type(held) is operations.owners._HeldTransition,'actual held archive operation required')
    c=transport._context;held.check(ledger.owner)
    require(c._cap is None and ledger.selection._transport is transport and claim._ledger is ledger
        and claim._stage is stage and ledger.owner.bound._run is c._run,'archive capability owner differs')
    expected=c._record['representations'][transport._name]
    require(ledger.owner.bound.record['workflow_identity']==expected['workflow_identity'],'archive capability workflow differs')
    require(ledger.selection.record['policy_sha256']==expected['policy_sha256'],'archive capability policy differs')
    raw=canonical_bytes(thaw(claim.record));key=digest(raw)
    require(key not in c._claims,'archive operation cannot be rebound')
    cap={'ledger':ledger,'held':held,'lease':lease,'view':transport,'thread':get_ident(),'claim_sha256':key,
        'remote_prefix':ledger.selection.writer_policy(stage.name)['remote_prefix']}
    c._cap=cap;primary=None
    try:
        c._outer();c._live();c._claims.add(key)
        logical=claim.record['reserved_decoded_transfer_bytes']
        c._spent['logical_bytes']+=logical;c._spent_pin=canonical_bytes(c._spent)
        require(c._spent['logical_bytes']<=c._record['capacity']['logical_bytes'],'archive logical reservation exceeds preflight')
        c._publish('operation-'+key+'.json',{'claim':thaw(claim.record),'spent':c._spent})
        yield
    except BaseException as error:primary=error;raise
    finally:
        c._cap=None
        # No expired scientific lease is invoked during terminal content checks.
        try:c._outer()
        except BaseException as error:
            failure=_retain(primary,error)
            raise failure

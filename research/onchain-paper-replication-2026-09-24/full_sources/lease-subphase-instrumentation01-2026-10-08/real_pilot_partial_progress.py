"""Bounded diagnostic snapshots of genuine MCM counters; no completion authority.

An optional registered schema2 selector enables flushed stdout JSON lines. Counts
are acknowledged observations, not exact final totals after interruption. Pair
iterations that have not published a completion are never counted as pairs.
"""
import json
import math
import sys
import time

MAX_LINE_BYTES = 2048


def require(value, message):
    if not value:
        raise ValueError('partial MCM telemetry: '+message)


def policy(value):
    require(type(value) is dict and set(value)=={'schema_version','interval_seconds','max_records'},'exact policy required')
    require(type(value['schema_version']) is int and value['schema_version']==1,'schema differs')
    require(type(value['interval_seconds']) is int and 1<=value['interval_seconds']<=3600,'finite interval required')
    require(type(value['max_records']) is int and 1<=value['max_records']<=1024,'finite record cap required')
    return dict(value)


def _time(value):
    require(type(value) in (int,float) and math.isfinite(value) and value>=0,'monotonic time differs')
    return float(value)


def _hash(value, widths):
    return type(value) is str and len(value) in widths and all(c in '0123456789abcdef' for c in value)


def _buffered_prefix(stream, batch_cells):
    """Diagnostic volatile watermark only; never a completion/restart receipt."""
    active=getattr(stream,'active',None)
    if active is None:
        return (batch_cells if stream.cells==batch_cells else None), None
    status=getattr(active,'durability_status',None)
    if status is None:return None,None
    acknowledged=status['acknowledged_records'];durable=status['durable_records']
    start=active.start['start_cell']
    require(type(acknowledged) is int and type(durable) is int and
            type(start) is int and start>=0 and
            type(active.start['cells']) is int and active.start['cells']>0 and
            0<=durable<=acknowledged<=active.start['cells'] and
            (start==batch_cells or
             (active.closed is True and not active.poisoned and
              acknowledged==durable==active.start['cells'] and
              batch_cells==start+acknowledged)) and
            start+acknowledged==stream.cells,'buffered tail watermark differs')
    return start+durable,status.get('poisoned',False)


class MCMProgress:
    def __init__(self, selection, nodes, *, claim_sha256, source, output=None, clock=time.monotonic):
        self.policy=policy(selection)
        require(type(nodes) is dict and len(nodes)==7 and all(_hash(k,(64,)) and type(v) is int and 0<v<2**58 for k,v in nodes.items()),'seven full graph extents required')
        require(_hash(claim_sha256,(64,)) and _hash(source,(40,64)),'actual caller provenance fields required')
        self.nodes=dict(nodes);self.claim=claim_sha256;self.source=source
        self.output=sys.stdout if output is None else output;self.clock=clock
        self.key=None;self.seen=set();self.began=self.observed=_time(clock());self.started=None
        self.last_emitted=None;self.records=0;self.last=None;self.error=None;self.previous=(0,0,0,0,0)

    def begin(self, graph_hash, rows, motifs):
        require(graph_hash in self.nodes and graph_hash not in self.seen and rows==self.nodes[graph_hash] and type(motifs) is int and motifs==32,'graph denominator or repeated graph differs')
        now=_time(self.clock());require(now>=self.observed,'clock moved backwards')
        self.key=graph_hash;self.seen.add(graph_hash);self.started=now;self.observed=now
        self.previous=(0,0,0,0,0)
        self._process_cpu_begin=time.process_time();self._first_batch_sample=None
        # A new graph is still subject to the shared whole-job interval/record cap.

    def poll(self, log, stream):
        if self.error is not None or self.records>=self.policy['max_records'] or log is None:
            return
        try:
            self._poll(log,stream)
        except BaseException as error:
            # Do not repeatedly break cleanup leases; the original failure still propagates.
            self.error=type(error).__name__
            raise

    def _poll(self, log, stream):
        require(self.key is not None,'graph interval absent')
        now=_time(self.clock());require(now>=self.observed,'clock moved backwards');self.observed=now
        if self.last_emitted is not None and now-self.last_emitted<self.policy['interval_seconds']:
            return
        state=log.state
        started=state['started_pairs'];matched=state['completed_pairs']
        tail=0 if stream is None else stream.cells
        batches=None if stream is None else stream.batches
        batch_cells=0 if batches is None else batches.cells
        batch_count=0 if batches is None else batches.chunks
        counts=(started,matched,tail,batch_cells,batch_count);total=self.nodes[self.key]*32
        require(all(type(n) is int and 0<=n<=total for n in counts),'invalid acknowledged counter')
        require(batch_count<=batch_cells<=tail<=matched<=started<=total and started-matched<=1,'counter order differs')
        require(all(n>=p for n,p in zip(counts,self.previous)),'acknowledged count moved backwards')
        require((state['pending'] is not None)==(started!=matched),'pending pair differs')
        elapsed=now-self.started
        row={'kind':'real_pilot_partial_mcm_progress','schema_version':1,'sequence':self.records,
             'claim_sha256':self.claim,'source':self.source,'graph_hash':self.key,
             'expected_nodes':self.nodes[self.key],'motifs':32,'expected_matching_pairs':total,
             'observed_elapsed_seconds':elapsed,'scope_elapsed_seconds':now-self.began,
             'started_matching_pairs':started,'acknowledged_computed_matching_pairs':matched,
             'pending_pair':state['pending'] is not None,'durable_tail_cells':tail,
             'durable_score_batch_cells':batch_cells,'durable_score_batches':batch_count,
             'acknowledged_pairs_per_second':matched/elapsed if elapsed>0 else None,
             'durable_batch_cells_per_second':batch_cells/elapsed if elapsed>0 else None,
             'full_mcm_completion_verified_here':False,'joint_update_verified_here':False,
             'representation_credit':0,'paper_financial_fits':0,
             'last_budget_slot':self.records+1==self.policy['max_records'],
             'qualification':'Last acknowledged diagnostic observation; not final counts, current local/remote availability, stage completion or authority. Full MCM and update require outer verified summary.'}
        if stream is not None and getattr(stream,'_durability_policy',None) is not None:
            durable,poisoned=_buffered_prefix(stream,batch_cells)
            cpu=time.process_time()-self._process_cpu_begin
            require(math.isfinite(cpu) and cpu>=0,'process CPU clock differs')
            if batch_count and self._first_batch_sample is None:
                self._first_batch_sample={'completed_batches':batch_count,'batch_cells':batch_cells,
                    'observed_wall_seconds':elapsed,'observed_process_cpu_seconds':cpu}
            row.update(observed_process_cpu_seconds=cpu,
                       process_cpu_scope='whole caller since graph begin; not isolated matcher',
                       first_completed_batch_sample=self._first_batch_sample)
            row.update(schema_version=2,acknowledged_tail_cells=tail,
                       durable_tail_cells=durable,durability_poisoned=poisoned,
                       durability_watermark='volatile sampled prefix; not restart authority')
        raw=json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n'
        require(len(raw.encode('utf-8'))<=MAX_LINE_BYTES,'diagnostic line exceeds finite bound')
        written=self.output.write(raw);require(written==len(raw),'short telemetry write')
        self.output.flush()
        self.records+=1;self.last_emitted=now;self.previous=counts;self.last=row

    def summary(self):
        return {'kind':'partial_mcm_diagnostics_only','records':self.records,
                'max_records':self.policy['max_records'],'max_stdout_bytes':MAX_LINE_BYTES*self.policy['max_records'],
                'record_cap_reached':self.records==self.policy['max_records'],
                'telemetry_error':self.error,'last_observation':None if self.last is None else dict(self.last),
                'representation_credit':0,'paper_financial_fits':0,
                'qualification':'Partial progress never changes outer graph dispositions, training completion or financial credit. Hard kill may leave only prior captured stdout; no final observation or fixed sampling-latency guarantee.'}


DIAGNOSTIC_PHASES = ('lease', 'pair_validation', 'state_create',
    'advance_annealing_including_rank_transition', 'advance_hardening', 'score_only', 'retention_live', 'event_publication',
    'lease_authority', 'lease_start_metadata', 'lease_progress')
DIAGNOSTIC_MAX_BYTES = 8192
STARTUP_ONCE = ('archive_preflight','archive_context','bind','import_preparation',
                'import_attach','import_execution','lease_activation')
STARTUP_GRAPHS = ('target','prepare','production')
STARTUP_MAX_PHASES = len(STARTUP_ONCE)+7*len(STARTUP_GRAPHS)


class PlannedScoringStop(RuntimeError):
    """Registered partial resource measurement ended; no MCM completion."""


def diagnostic_policy(value):
    require(type(value) is dict and set(value)=={'schema_version','max_completed_pairs',
        'checkpoint_every_pairs','checkpoint_relative'},'exact diagnostic policy required')
    require(type(value['schema_version']) is int and value['schema_version']==1,'diagnostic schema differs')
    maximum=value['max_completed_pairs'];every=value['checkpoint_every_pairs']
    require(type(maximum) is int and 1<=maximum<=1024 and type(every) is int
        and 1<=every<=maximum,'finite diagnostic comparison/checkpoint bounds required')
    require(value['checkpoint_relative']=='scoring-diagnostic/progress.json','fixed diagnostic checkpoint required')
    return dict(value)


class ScoringDiagnostic:
    def __init__(self, selection, directory, *, claim_sha256, source, clock=time.monotonic):
        import os
        from pathlib import Path
        self.policy=diagnostic_policy(selection);self._policy=json.dumps(self.policy,sort_keys=True)
        require(_hash(claim_sha256,(64,)) and _hash(source,(40,64)),'diagnostic provenance required')
        self.claim=claim_sha256;self.source=source;self.clock=clock;self.began=_time(clock())
        self.matching_began=None;self.completed=0;self.graph=None;self.graph_base=0;self.graph_completed=0;self.tail=None
        self.timings={key:{'seconds':0.,'calls':0} for key in DIAGNOSTIC_PHASES}
        self.stopped=False;self.writes=0
        self._refresh_at=None;self._refresh_count=0
        self.startup=[];self._startup_active=None;self._startup_started=None
        self._startup_seen=set();self._startup_last=self.began
        parent=Path(directory);require(parent.is_dir() and parent.resolve()==parent,'diagnostic parent differs')
        self.directory=parent/'scoring-diagnostic';self.directory.mkdir(exist_ok=False)
        self.fd=os.open(self.directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try:
            self._write();self._refresh_at=self.began
        except BaseException:
            os.close(self.fd);self.fd=None;raise

    def _check(self):
        require(json.dumps(self.policy,sort_keys=True)==self._policy,'diagnostic policy changed')

    def _startup_now(self):
        now=_time(self.clock());require(now>=self._startup_last,'startup clock reversed')
        self._startup_last=now;return now

    def startup_enter(self,phase,graph_index=None):
        self._check()
        require((phase in STARTUP_ONCE and graph_index is None) or
                (phase in STARTUP_GRAPHS and type(graph_index) is int and 0<=graph_index<7),
                'bounded startup phase/index required')
        key=(phase,graph_index)
        require(self._startup_active is None and key not in self._startup_seen
                and len(self.startup)<STARTUP_MAX_PHASES,'startup phase repeated, nested or exhausted')
        now=self._startup_now();self._startup_seen.add(key)
        self.startup.append({'phase':phase,'graph_index':graph_index,'state':'entered',
                            'entered_seconds':now-self.began,'elapsed_seconds':0.})
        self._startup_active=len(self.startup)-1;self._startup_started=now
        # Entry is durable before the original operation starts.
        self._write()

    def _startup_finish(self,state,error=None):
        self._check();require(self._startup_active is not None,'startup phase absent')
        now=self._startup_now();item=self.startup[self._startup_active]
        item['elapsed_seconds']=now-self._startup_started;item['state']=state
        if error is not None:item['failure_type']=type(error).__name__[:64]
        self._startup_active=None;self._startup_started=None
        self._write()

    def startup_complete(self):self._startup_finish('completed')

    def startup_failed(self,error):
        if self._startup_active is not None:self._startup_finish('failed',error)

    def measure(self, phase, function, *args, **kwargs):
        self._check();require(phase in self.timings,'unregistered timing phase')
        began=_time(self.clock())
        try:result=function(*args,**kwargs)
        except BaseException as original:
            try:self._record(phase,began)
            except BaseException as later:original.add_note('Diagnostic timing failed: '+repr(later))
            raise
        self._record(phase,began);return result

    def _measure_lease_subphase(self,phase,function,*args):
        """Private lease-only aggregate; outer measure retains refresh ownership."""
        self._check()
        require(phase in ('lease_authority','lease_start_metadata','lease_progress')
                and phase in self.timings,'unregistered lease subphase')
        began=_time(self.clock())
        try:result=function(*args)
        except BaseException as original:
            try:self._record_lease_subphase(phase,began)
            except BaseException as later:original.add_note('Diagnostic lease timing failed: '+repr(later))
            raise
        self._record_lease_subphase(phase,began);return result

    def _record_lease_subphase(self,phase,began):
        now=_time(self.clock());elapsed=now-began;require(elapsed>=0,'diagnostic clock reversed')
        item=self.timings[phase];item['seconds']+=elapsed;item['calls']+=1
        require(math.isfinite(item['seconds']) and item['calls']<2**63,'diagnostic aggregate overflow')
        # Never write here: no new checkpoint/failure between original body calls.

    def _record(self,phase,began):
        now=_time(self.clock());elapsed=now-began;require(elapsed>=0,'diagnostic clock reversed')
        item=self.timings[phase];item['seconds']+=elapsed;item['calls']+=1
        require(math.isfinite(item['seconds']) and item['calls']<2**63,'diagnostic aggregate overflow')
        if self._refresh_count<480 and now-self._refresh_at>=60:
            self._write()
            self._refresh_at=now;self._refresh_count+=1

    def begin(self, graph_hash, log):
        self._check();require(not self.stopped and _hash(graph_hash,(64,))
            and log.state['completed_pairs']==0,'fresh diagnostic graph log required')
        if self.matching_began is None:self.matching_began=_time(self.clock())
        self.graph=graph_hash;self.graph_base=self.completed;self.graph_completed=0;self.tail=None
        self._write()  # Persist matching-log entry before the first pair checkpoint.

    def completed_pair(self,log):
        self._check();require(not self.stopped and self.graph is not None
            and log.state['pending'] is None and log.state['completed_pairs']==self.graph_completed+1,
            'actual next completed pair required')
        self.graph_completed+=1;self.completed+=1
        require(self.completed<=self.policy['max_completed_pairs'],'diagnostic comparison cap exceeded')
        if self.completed==self.policy['max_completed_pairs']:
            self.stopped=True;self._write()
            raise PlannedScoringStop('registered completed scalar comparison limit reached')
        if self.completed%self.policy['checkpoint_every_pairs']==0:self._write()

    def observe_tail(self,log,stream):
        self._check()
        if log is None or stream is None:return
        require(log.state['completed_pairs']==self.graph_completed,'diagnostic log count changed')
        batches=stream.batches;batch_cells=0 if batches is None else batches.cells
        require(type(stream.cells) is int and 0<=batch_cells<=stream.cells<=self.graph_completed,'diagnostic tail order differs')
        durable,poisoned=_buffered_prefix(stream,batch_cells)
        self.tail={'acknowledged_tail_cells':stream.cells,'durable_tail_cells':durable,
            'completed_batch_cells':batch_cells,'durability_poisoned':poisoned}
        self._write()

    def summary(self):
        self._check();now=_time(self.clock());elapsed=now-self.began;require(elapsed>=0,'diagnostic elapsed differs')
        matching=None if self.matching_began is None else now-self.matching_began
        require(matching is None or matching>=0,'matching clock reversed')
        return {'schema_version':1,'kind':'partial_scalar_scoring_diagnostic','policy':dict(self.policy),
            'claim_sha256':self.claim,'source':self.source,'graph_hash':self.graph,
            'completed_scalar_pairs':self.completed,'graph_completed_scalar_pairs':self.graph_completed,
            'scope_elapsed_seconds':elapsed,'matching_elapsed_seconds':matching,
            'pairs_per_second':self.completed/matching if matching else None,
            'phase_timings':{k:dict(v) for k,v in self.timings.items()},'tail_observation':self.tail,
            'startup_progress':{'active':self._startup_active,'phases':[dict(v) for v in self.startup]},
            'planned_stop_reached':self.stopped,'checkpoint_writes_before_this_snapshot':self.writes,
            'full_mcm_complete':False,'representation_credit':0,'model_update_complete':False,'paper_financial_fits':0,
            'qualification':'Completed pair-log acknowledgements only; final capped pair may not enter score tail. Timings are selected inclusive seams, not a disjoint profile; annealing advance includes atomic rank transition. Extraction is not isolated. Automatic refresh is sampled after timing callbacks, at most once per60seconds and480times; blocked calls have no guaranteed refresh. Remaining startup is measured after population/input/graph/model loading; phases include entry checkpoint publication and exclude exit publication. Matching entry precedes matcher/index preparation. Tail durability is a sampled watermark. Outer exit/recovery remain separate.'}

    def _write(self):
        import os
        raw=(json.dumps(self.summary(),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
        require(len(raw)<=DIAGNOSTIC_MAX_BYTES,'diagnostic checkpoint exceeds bound')
        fd=os.open('progress.tmp',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.replace('progress.tmp','progress.json',src_dir_fd=self.fd,dst_dir_fd=self.fd);os.fsync(self.fd)
            self.writes+=1
        except BaseException:raise

    def close(self):
        import os
        if self.fd is not None:os.close(self.fd);self.fd=None

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

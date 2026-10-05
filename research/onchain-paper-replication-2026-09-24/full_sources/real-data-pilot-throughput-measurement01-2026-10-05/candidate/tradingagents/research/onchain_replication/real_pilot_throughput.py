"""Seven-graph pilot measurements only; never source or completion authority."""
import math
import time


def require(value,message):
    if not value:raise ValueError('pilot timing: '+message)


def seconds(value):
    require(type(value) in (int,float) and math.isfinite(value) and value>=0,'invalid monotonic elapsed time')
    return float(value)


class MCMMeasurements:
    """Counts become completed only after the caller's genuine retained check.

    Timings include imported MCM production and its mandatory retained checks,
    excluding the preceding outer storage scan. Partial work is uncredited and
    unknown. No guard memory, physical storage or numerical-fit proof is inferred.
    """
    def __init__(self,nodes,*,population_scope,clock=time.monotonic):
        require(type(nodes) is dict and len(nodes)==7 and all(type(k) is str and len(k)==64
                and all(c in '0123456789abcdef' for c in k) and type(n) is int and n>0 for k,n in nodes.items()),'seven actual graph extents required')
        require(population_scope in ('resource_pilot_subset','full_fold_input'),'unknown population scope')
        self.clock=clock;self.began=seconds(clock());self.population_scope=population_scope
        self.rows={k:{'graph_hash':k,'expected_nodes':n,'motifs':32,'expected_motif_cells':n*32,
                      'status':'unavailable','reason':'not_attempted','elapsed_seconds':None,
                      'completed_nodes':None,'completed_motif_cells':None} for k,n in sorted(nodes.items())}
        self.active=None;self.start=None;self.closed=False

    def begin(self,key):
        require(not self.closed and self.active is None and key in self.rows and self.rows[key]['status']=='unavailable','graph already attempted or transition active')
        now=seconds(self.clock());require(now>=self.began,'monotonic clock moved backwards')
        self.active=key;self.start=now;self.rows[key].update(status='active',reason=None)

    def completed(self,key,retained):
        require(not self.closed and self.active==key,'different active graph')
        row=self.rows[key]
        require(type(retained) is dict and retained.get('graph_hash')==key
                and type(retained.get('rows')) is int and retained['rows']==row['expected_nodes']
                and type(retained.get('motifs')) is int and retained['motifs']==32
                and type(retained.get('cells')) is int and retained['cells']==row['expected_motif_cells'],
                'retained full-graph denominator differs')
        elapsed=seconds(self.clock()-self.start)
        row.update(status='complete',elapsed_seconds=elapsed,completed_nodes=retained['rows'],completed_motif_cells=retained['cells'])
        self.active=None;self.start=None

    def failed(self,error):
        require(not self.closed and isinstance(error,BaseException),'actual failure required')
        if self.active is not None:
            self.rows[self.active].update(status='failed',elapsed_seconds=seconds(self.clock()-self.start),
                                         reason=type(error).__name__+': '+str(error)[:1024])
            self.active=None;self.start=None
        for row in self.rows.values():
            if row['status']=='unavailable':row['reason']='not_attempted_after_failure'
        self.closed=True

    def summary(self,training):
        require(self.active is None,'unfinished graph interval cannot be reported complete')
        rows=[dict(row) for row in self.rows.values()]
        require(len(rows)==7 and all(row['status'] in ('complete','failed','unavailable') for row in rows),'graph disposition denominator differs')
        complete=[row for row in rows if row['status']=='complete']
        completed_cells=sum(row['completed_motif_cells'] for row in complete)
        completed_seconds=sum(row['elapsed_seconds'] for row in complete)
        attempted_seconds=sum(row['elapsed_seconds'] for row in rows if row['elapsed_seconds'] is not None)
        phase_seconds=None
        if training is not None:
            require(type(training) is dict and training.get('status')=='complete' and training.get('optimizer_steps')==1
                    and training.get('financial_fit_complete') is False and type(training.get('seconds')) is dict,
                    'actual one-update completion required')
            phase_seconds={key:seconds(value) for key,value in training['seconds'].items()}
        return {'schema_version':1,'scope':'seven full graphs/original32 motifs and one resource update only',
                'population_scope':self.population_scope,'decisions':16,'lookback_days':28,'original_samples':512,
                'full_fold_fit':False,'financial_fit_complete':False,'paper_financial_fits':0,
                'graphs':rows,'graph_denominator':7,'complete_graphs':len(complete),
                'failed_graphs':sum(row['status']=='failed' for row in rows),
                'unavailable_graphs':sum(row['status']=='unavailable' for row in rows),
                'verified_completed_nodes':sum(row['completed_nodes'] for row in complete),
                'verified_completed_motif_cells':completed_cells,'completed_mcm_seconds':completed_seconds,
                'attempted_mcm_seconds':attempted_seconds,
                'completed_motif_cells_per_second':completed_cells/completed_seconds if complete and completed_seconds>0 else None,
                'verified_motif_cells_per_attempted_second':completed_cells/attempted_seconds if complete and attempted_seconds>0 else None,
                'scope_elapsed_seconds':seconds(self.clock()-self.began),'one_update_phase_seconds':phase_seconds,
                'guard_resource_evidence':None,
                'qualification':'Intervals start after population and graph loading; MCM intervals include production plus retained verification. Partial failed work is unknown and receives no completed count. Guard/kernel peaks, storage and actual outer exits require separately joined closure evidence.'}

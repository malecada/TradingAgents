"""Independent diagnostic seam checks; no scientific inputs or authorities."""
import ast
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace as N

HERE=Path(__file__).resolve().parent
C=HERE.parent/'real-data-pilot-startup-timing01-2026-10-08'
ROOT=HERE.parents[3]
checks=[]
def check(value,label):
    if not value:raise AssertionError(label)
    checks.append(label)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def methods(path):
    cls=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='ScoringDiagnostic')
    return {n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
check(sha(C/'real_pilot_import_caller.py')=='cfb38250f2b4114b1fdc36f852bd5432215591021fda6724b985f9febdc66f40','exact_caller')
check(sha(C/'real_pilot_partial_progress.py')=='0452c3baf16de5a20ed7c2648c5193ef307df0176c4ab7988b0e8a40acdd00c7','exact_diagnostic')
for name in ('real_pilot_import_caller.py','real_pilot_partial_progress.py'):
    check(sha(C/('baseline_'+name))==sha(ROOT/'tradingagents/research/onchain_replication'/name),'frozen_baseline_'+name)
old=methods(C/'baseline_real_pilot_partial_progress.py');new=methods(C/'real_pilot_partial_progress.py')
for name in ('_check','measure','_record','completed_pair','observe_tail','_write','close'):
    check(ast.dump(old[name])==ast.dump(new[name]),'unchanged_diagnostic_'+name)
check([ast.dump(n) for n in new['begin'].body[:-1]]==[ast.dump(n) for n in old['begin'].body],'matching_begin_only_appends_publication')
m=load(C/'real_pilot_partial_progress.py','independent_startup_diagnostic')
policy={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':64,'checkpoint_relative':'scoring-diagnostic/progress.json'}
with tempfile.TemporaryDirectory(dir=HERE) as tmp:
    clock=[0.]
    d=m.ScoringDiagnostic(policy,Path(tmp),claim_sha256='a'*64,source='b'*64,clock=lambda:clock[0])
    try:
        checkpoint=Path(tmp)/'scoring-diagnostic/progress.json'
        for phase in m.STARTUP_ONCE:
            d.startup_enter(phase);clock[0]+=1.25;d.startup_complete()
        for phase in m.STARTUP_GRAPHS:
            for index in range(7):
                d.startup_enter(phase,index)
                snap=json.loads(checkpoint.read_text())
                check(snap['startup_progress']['phases'][-1]['state']=='entered','durable_entry_'+phase+str(index))
                clock[0]+=1.25;d.startup_complete()
        check(len(d.startup)==28 and d._startup_active is None,'complete_finite_roster')
        check(checkpoint.stat().st_size<=8192,'full_roster_retains_original_cap')
        writes=d.writes;log=N(state={'completed_pairs':0})
        d.begin('c'*64,log)
        snap=json.loads(checkpoint.read_text())
        check(d.writes==writes+1 and snap['graph_hash']=='c'*64 and snap['completed_scalar_pairs']==0,'matching_entry_durable_zero_credit')
        stopped=False
        for count in range(1,1025):
            log.state={'completed_pairs':count,'pending':None};clock[0]+=0.5
            try:d.completed_pair(log)
            except m.PlannedScoringStop:
                check(count==1024,'stop_only_at_original_limit');stopped=True
        snap=json.loads(checkpoint.read_text())
        check(stopped and snap['completed_scalar_pairs']==1024 and snap['planned_stop_reached'],'original_acknowledgement_stop_semantics')
        check(not snap['full_mcm_complete'] and not snap['model_update_complete'] and snap['paper_financial_fits']==0,'no_completion_credit')
        check(checkpoint.stat().st_size<=8192,'scoring_plus_roster_retains_original_cap')
    finally:d.close()
result={'decision':'accepted-source-only','checks':checks,
        'sources':{str((C/name).relative_to(ROOT)):sha(C/name) for name in ('real_pilot_import_caller.py','real_pilot_partial_progress.py')},
        'scope':'Independent AST and actual synthetic bounded checkpoint/1024-acknowledgement behavior. No authority, graph, array, model or empirical imports. Existing 8192B checkpoint and exact counter/stop methods retained. Timing begins after population/input/graph/model loading, includes entry checkpoint cost, excludes exit publication. Production phase is inclusive of scoring and is not disjoint startup time. Current native21 untouched. Source-only; source/entry integration and actual runtime timings remain unavailable.'}
out=HERE/'TIMING_REVIEW01.json'
with out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'decision':result['decision'],'checks':len(checks),'review_sha256':sha(out)}))

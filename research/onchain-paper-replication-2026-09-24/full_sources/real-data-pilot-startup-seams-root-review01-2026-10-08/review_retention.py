"""Independent exact wrapper review, without retained data or authorities."""
import ast,hashlib,json
from pathlib import Path
from types import SimpleNamespace as N
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
C=HERE.parent/'real-data-pilot-retention-timing01-2026-10-08'
checks=[]
def check(value,label):
    if not value:raise AssertionError(label)
    checks.append(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(value,label):
    if not value:raise ValueError(label)
check(sha(C/'stage_retention.py')=='7312829458f7495638cf07f56b1464ca08b6ce28357d7557372821eddef2dac8','exact_retention')
check(sha(C/'real_pilot_partial_progress.py')=='f6e922082c4ab22196a1be118174bdf03f10ae8ee3ae2b58e18842ef7f163e7f','exact_diagnostic')
check(sha(C/'baseline_stage_retention.py')==sha(ROOT/'tradingagents/research/onchain_replication/stage_retention.py'),'frozen_main_baseline')
check(sha(C/'baseline_real_pilot_partial_progress.py')=='0452c3baf16de5a20ed7c2648c5193ef307df0176c4ab7988b0e8a40acdd00c7','accepted_startup_baseline')
a=ast.parse((C/'baseline_stage_retention.py').read_text());b=ast.parse((C/'stage_retention.py').read_text())
old_cls=next(n for n in a.body if isinstance(n,ast.ClassDef) and n.name=='Controller')
cls=next(n for n in b.body if isinstance(n,ast.ClassDef) and n.name=='Controller')
old_methods={n.name:n for n in old_cls.body if isinstance(n,ast.FunctionDef)}
methods={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
check(set(methods)-set(old_methods)=={'_live'},'one_private_body_only')
for name in old_methods:
    if name!='live':check(ast.dump(old_methods[name])==ast.dump(methods[name]),'unchanged_'+name)
body=methods['_live'];body.name='live'
check(ast.dump(old_methods['live'])==ast.dump(body),'original_body_exact_ast')
body.name='_live'
# Collapse the new wrapper/body split to verify the entire original module.
cls.body=[old_methods['live'] if isinstance(n,ast.FunctionDef) and n.name=='live' else n for n in cls.body if not (isinstance(n,ast.FunctionDef) and n.name=='_live')]
check(ast.dump(a)==ast.dump(b),'whole_retention_inverse')
raw=(C/'real_pilot_partial_progress.py').read_text()
check(raw.replace("'score_only', 'retention_live'", "'score_only'")==(C/'baseline_real_pilot_partial_progress.py').read_text(),'diagnostic_one_constant_inverse')
ns={'require':require}
exec(compile(ast.Module(body=[methods['live'],body],type_ignores=[]),'isolated_retention_methods','exec'),ns)
trace=[]
x=N(current_frame='frame',_authority=lambda:trace.append('authority'),_state=lambda:(trace.append('state'),1)[1],_integrity=lambda:trace.append('integrity'))
x._live=lambda:ns['_live'](x)
x.matcher=N(_diagnostic=None,_check=lambda:trace.append('matcher'),_ack_check=lambda frame:trace.append(('ack',frame)))
ns['live'](x);plain=list(trace);trace.clear()
def measure(phase,function):
    trace.append(('timer',phase));return function()
x.matcher._diagnostic=N(measure=measure)
ns['live'](x)
check(trace[0]==('timer','retention_live') and trace[1:]==plain,'unchanged_original_check_order')
for point in ('_authority','_integrity'):
    error=OSError('original '+point);saved=getattr(x,point)
    def fail():raise error
    setattr(x,point,fail)
    try:ns['live'](x)
    except OSError as actual:check(actual is error,'original_failure_identity_'+point)
    else:raise AssertionError('lost original failure')
    setattr(x,point,saved)
result={'decision':'accepted-source-only','checks':checks,
        'sources':{str((C/name).relative_to(ROOT)):sha(C/name) for name in ('stage_retention.py','real_pilot_partial_progress.py')},
        'scope':'Different-author exact module inverse and actual isolated live-method trace/error identity checks. No real Controller/Matcher/Owner/Run, data arrays or model execution. Existing matcher assigns _diagnostic before Controller construction; existing diagnostic measure semantics and startup cap proof reused. Inclusive retention timing overlaps lease and does not measure pure I/O. No optimization, runtime attribution, current integration or entry release.'}
out=HERE/'RETENTION_REVIEW01.json'
with out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'checks':len(checks),'decision':result['decision'],'review_sha256':sha(out)}))

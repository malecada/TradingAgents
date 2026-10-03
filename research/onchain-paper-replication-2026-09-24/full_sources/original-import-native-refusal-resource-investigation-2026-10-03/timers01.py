"""Actual active-loop timer expression with an explicitly fake clock/watch."""
import ast,hashlib,json,sys
from pathlib import Path
from types import SimpleNamespace as NS
P=Path(__file__).resolve().parent;S=P.parent/'original-import-native-refusal-worker-preparation02-2026-10-03/refusal_outer01.py';tree=ast.parse(S.read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');g=next(n for n in run.body if isinstance(n,ast.Try) and any(isinstance(x,ast.While) for x in n.body));loop=next(n for n in g.body if isinstance(n,ast.While));clock={'now':1839.9};events=[]
def check():events.append('watch');clock['now']+=5;return {'allocated_bytes':1,'logical_file_bytes':1}
def require(v,m):
 if not v:raise ValueError(m)
# Actual body statements through its time assertion, before real filesystem/log
# operations or sleep. No process or clock is shared with a live job.
selected=[]
for node in loop.body:
 selected.append(node)
 if 'outer active deadline reached' in ast.unparse(node):break
env={'watch':NS(check=check),'GIB':1024**3,'require':require,'shutil':NS(disk_usage=lambda _:NS(free=11*1024**3)),'root':None,'time':NS(monotonic=lambda:clock['now']),'started':0}
try:exec(compile(ast.Module(body=selected,type_ignores=[]),'actual active timer','exec'),env)
except ValueError as e:assert str(e)=='outer active deadline reached'
else:raise AssertionError('actual timer did not refuse')
assert clock['now']==1844.9
# The finalbody has no 60-second elapsed guard. Its own monotonic call is only
# terminal elapsed telemetry; inventory has a separate local30s scan deadline.
assert not any(isinstance(n,ast.Constant) and n.value==60 for part in g.finalbody for n in ast.walk(part))
print(json.dumps({'source_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'actual_active_deadline_seconds':1840,'synthetic_clock_before_watch':1839.9,'synthetic_watch_seconds':5,'actual_timer_refusal_at_fake_elapsed':clock['now'],'whole_closure_60_second_guard_in_finalbody':False,'separate_systemctl_wait_allowances_seconds':[10,10,10],'separate_supervisor_wait_allowances_seconds':[20,5],'separate_inventory_scan_seconds':30,'sum_of_these_separate_allowances_seconds':85,'hard_whole_invocation_bound_proved':False,'elapsed_wall_sleep_or_OS_job':False,'numerical_imports':False},indent=2))

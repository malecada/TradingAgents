import ast,importlib.util,json,os,time
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04';S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source/tradingagents/research/onchain_replication');out=[]
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('watch',A/'workflow_storage.py');io=load('io',S/'owned_io.py');tree=ast.parse((S/'resources.py').read_text());wanted={'_native_select','_native_reason','_native_finalize','observe_storage','boundaries'};nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in wanted]
p=H/'native-controls';p.mkdir();(p/'a').write_bytes(b'opaque');limits=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
env={'native_io':io,'native_unit_limits':{'opaque':'present'},'state':{},'storage_watch':m.StorageWatch(p,limits),'physical_policy':None,'disk_paths':[p],'disk_floor_bytes':100,'begin':0,'wall_seconds':100,'time':SimpleNamespace(monotonic=lambda:1),'shutil':SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=100))}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-resources-subset','exec'),env)
env['observe_storage']();assert env['state']['storage_peak_logical_file_bytes']==6;out.append({'case':'genuine-observe-success','peak':6})
# Exact floor is allowed; one byte below refuses. No actual guard entered.
env['boundaries']();env['shutil']=SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=99))
try:env['boundaries']()
except RuntimeError as e:assert str(e)=='disk floor breached';out.append({'case':'genuine-boundaries-disk-floor','free':99,'floor':100,'refused':True})
else:raise AssertionError('floor admitted')
env['shutil']=SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=100));env['time']=SimpleNamespace(monotonic=lambda:101)
try:env['boundaries']()
except RuntimeError as e:assert str(e)=='registered wall-clock limit exceeded';out.append({'case':'genuine-boundaries-deadline','refused':True})
else:raise AssertionError('wall deadline admitted')
env['storage_watch']=m.StorageWatch(p,{**limits,'max_logical_bytes':1});env['state']={}
try:env['observe_storage']()
except m.StorageLimit as e:assert e.reason=='logical' and env['state']['phase']=='failed' and env['state']['storage_breach']['logical_file_bytes']==6;out.append({'case':'genuine-native-storage-failure','state':env['state']})
else:raise AssertionError('storage breach admitted')
class Fatal(KeyboardInterrupt):
 def __str__(self):raise SystemExit('diagnostic must not replace original fatal')
fatal=Fatal();state={};assert env['_native_reason'](state,fatal,io) is fatal;out.append({'case':'genuine-native-firstfatal-diagnostic','original_selected':True,'phase':state['phase']})
# Every independent finalization action still runs and real descriptors close.
state={};calls=[];fds=[os.open(p,os.O_RDONLY|os.O_DIRECTORY) for _ in range(3)];first=MemoryError('first actual fatal');later=KeyboardInterrupt('later actual fatal');ordinary=RuntimeError('ordinary')
def action(i,e):
 def f():os.close(fds[i]);calls.append(i);raise e
 return f
selected,failed=env['_native_finalize'](state,ordinary,[(str(i),action(i,e)) for i,e in enumerate([ordinary,first,later])],io)
assert selected is first and failed and calls==[0,1,2] and state['phase']=='failed'
out.append({'case':'genuine-native-finalization','selected_first_actual_fatal':True,'all_actions':calls,'phase':state['phase']})
# Ordinary cleanup error stops rather than retrying census; all close calls happen once.
m.os=SimpleNamespace(**vars(os));seen=[]
def close(fd):os.close(fd);seen.append(fd);raise RuntimeError('close uncertainty')
m.os.close=close
try:m.StorageWatch(p,limits).check()
except m.StorageCleanupFailure:assert len(seen)==1;out.append({'case':'ordinary-real-close-error','closed_once':True,'no_retry':True})
else:raise AssertionError('uncertain cleanup accepted')
(H/'NATIVE_CONTROLS01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'cases':len(out),'status':'PASS','native_guard_entered':False}))

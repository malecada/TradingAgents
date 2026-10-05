"""Focused stdlib scheduling regression; extracted exact source callbacks, no launch."""
import ast,copy,hashlib,importlib.util,json,sys,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).parent
PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01')
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
PREFIX='tradingagents/research/onchain_replication/'
OLD_SHA='0534945d070521c4dcfe85adcdfe6fa39e698a2a3101f95756828d3d33069375'
STORAGE_SHA='91e21c525a156cc8c25877ac35f0308896a1a0d1e6279d5aecf91d7e02567780'
GIB=1024**3

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
S=load('actual_storage',CAP/PREFIX/'workflow_storage.py')
R=load('actual_resources',CAP/PREFIX/'resources.py')
def require(ok,why):
 if not ok:raise ValueError(why)
def function(source,name):return next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name==name)
def install(nodes,env):exec(compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes),type_ignores=[])),'<exact-source-functions>','exec'),env)
def limits():return {'max_allocated_bytes':1024**2,'max_logical_bytes':1024**2,'max_entries':64,'max_depth':8,'max_scan_seconds':5}

class Scheduling(unittest.TestCase):
 def setUp(self):
  self.old=(PARENT/'parent01.py').read_text();self.new=(P/'parent01.py').read_text();self.source=(CAP/PREFIX/'resources.py').read_text()
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.cap=self.root/'cap';self.cap.mkdir();self.parent=self.root/'parent';self.parent.mkdir()
 def callbacks(self,source,capwatch,parentwatch,disk):
  launch=function(source,'launch');nodes=[n for n in launch.body if isinstance(n,ast.FunctionDef) and n.name in ('checked','active_checked')]
  env={'watch':capwatch,'parentwatch':parentwatch,'CAP':self.cap,'shutil':SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=disk())),'require':require,'GIB':GIB}
  install(nodes,env);return env
 def test_exact_inverse_and_source_bound_scheduling(self):
  self.assertEqual(hashlib.sha256(self.old.encode()).hexdigest(),OLD_SHA)
  original=" def checked():\n  watch.check();parentwatch.check();require(shutil.disk_usage(CAP).free>=10*GIB,'active disk floor')"
  replacement=" def active_checked():\n  parentwatch.check();require(shutil.disk_usage(CAP).free>=10*GIB,'active disk floor')\n def checked():\n  watch.check();active_checked()"
  restored=self.new.replace(replacement,original).replace('result=supervise(command,CAP,env,directory,1840,active_checked,spawned)','result=supervise(command,CAP,env,directory,1840,checked,spawned)')
  self.assertEqual(restored,self.old)
  launch=function(self.new,'launch');calls=[n for n in ast.walk(launch) if isinstance(n,ast.Call)]
  supervisor=next(n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='supervise')
  self.assertEqual(ast.unparse(supervisor.args[5]),'active_checked')
  pre=next(n for n in launch.body if isinstance(n,ast.Expr) and ast.unparse(n.value)=='checked()');self.assertLess(pre.lineno,supervisor.lineno)
  cleanup=next(n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='_cleanup' and any(k.arg=='primary' for k in n.keywords))
  self.assertEqual(ast.unparse(cleanup.args[0].left),'(retain_cleanup, retain_terminal, checked)')
  self.assertGreater(cleanup.lineno,supervisor.lineno)
 def test_red_duplicate_cap_census_green_guard_publication(self):
  events=[];phase={'active':False};capwatch=S.StorageWatch(self.cap,limits());parentwatch=S.StorageWatch(self.parent,limits());guardwatch=S.StorageWatch(self.cap,limits())
  class ParentCap:
   def check(inner):
    events.append('parent-CAP')
    if phase['active']:raise S.StorageMutationObservation('injected duplicate concurrent census','guard')
    return capwatch.check()
  class ParentTree:
   def check(inner):events.append('parent-tree');return parentwatch.check()
  def disk():events.append('disk');return 11*GIB
  old=self.callbacks(self.old,ParentCap(),ParentTree(),disk);new=self.callbacks(self.new,ParentCap(),ParentTree(),disk)
  new['checked']();self.assertEqual(events,['parent-CAP','parent-tree','disk']);events.clear();phase['active']=True
  with self.assertRaises(S.StorageMutationObservation):old['checked']()
  events.clear();(self.cap/'guard').mkdir();(self.cap/'owner.json').write_text('{}');(self.cap/'guard/cpu_ready.json').write_text('{}')
  observation=guardwatch.check();new['active_checked']();self.assertEqual(events,['parent-tree','disk']);self.assertEqual(observation['regular_files'],2);self.assertEqual(observation['logical_file_bytes'],4)
  phase['active']=False;events.clear();(self.cap/'guard/final.json').write_text('{}');(self.parent/'parent-terminal.json').write_text('{}');new['checked']()
  self.assertEqual(events,['parent-CAP','parent-tree','disk']);self.assertEqual(guardwatch.check()['regular_files'],3)
 def test_active_parent_disk_and_prepost_cap_refusals(self):
  class Watch:
   fail=False
   def check(self):
    if self.fail:raise S.StorageLimit('entries',{})
  capwatch=Watch();parentwatch=Watch();disk={'free':11*GIB};env=self.callbacks(self.new,capwatch,parentwatch,lambda:disk['free'])
  parentwatch.fail=True
  with self.assertRaises(S.StorageLimit):env['active_checked']()
  parentwatch.fail=False;disk['free']=9*GIB
  with self.assertRaisesRegex(ValueError,'active disk floor'):env['active_checked']()
  disk['free']=11*GIB;capwatch.fail=True
  for phase in ('before-spawn','after-drained-success','after-drained-failure'):
   with self.subTest(phase=phase),self.assertRaises(S.StorageLimit):env['checked']()
  # Actual retained watcher rejects post-drain excess with original finite limits.
  bounded=limits();bounded['max_logical_bytes']=8;actual=S.StorageWatch(self.cap,bounded);(self.cap/'late-terminal').write_bytes(b'123456789')
  actual_env=self.callbacks(self.new,actual,Watch(),lambda:11*GIB)
  with self.assertRaises(S.StorageLimit):actual_env['checked']()
 def test_native_source_pins_and_all_guard_boundaries(self):
  pins=json.loads((PARENT/'PROTOCOL_PINS01.json').read_bytes())
  for name,pin in pins.items():self.assertEqual(hashlib.sha256((CAP/name).read_bytes()).hexdigest(),pin)
  self.assertEqual(hashlib.sha256((CAP/PREFIX/'workflow_storage.py').read_bytes()).hexdigest(),STORAGE_SHA)
  guard=function(self.source,'guarded_run');calls=[n for n in ast.walk(guard) if isinstance(n,ast.Call)]
  boundaries=sorted(n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=='boundaries')
  dispatch=next(n.lineno for n in calls if ast.unparse(n.func)=='subprocess.run' and ast.unparse(n.args[0])=='args')
  release=next(n.lineno for n in calls if ast.unparse(n.func)=='_native_atomic' and 'release.json' in ast.unparse(n))
  self.assertEqual(len(boundaries),3);self.assertLess(boundaries[0],dispatch);self.assertLess(dispatch,boundaries[1]);self.assertLess(boundaries[1],release);self.assertGreater(boundaries[2],release)
  final_observe=next(n.lineno for n in calls if ast.unparse(n.func)=='actions.append' and ast.unparse(n.args[0])=="('observe-storage', observe_storage)")
  final_disk=next(n.lineno for n in calls if ast.unparse(n.func)=='actions.append' and ast.unparse(n.args[0])=="('final-disk-floor', final_disk)")
  final_publish=next(n.lineno for n in calls if ast.unparse(n.func)=='actions.append' and ast.unparse(n.args[0])=="('publish', publish)")
  self.assertLess(boundaries[2],final_observe);self.assertLess(final_observe,final_disk);self.assertLess(final_disk,final_publish)
  # Execute the actual guard's metadata boundary functions with a real tiny tree.
  nodes=[n for n in ast.walk(guard) if isinstance(n,ast.FunctionDef) and n.name in ('observe_storage','boundaries','final_disk')]
  actual=S.StorageWatch(self.cap,limits());env={**R.__dict__,'storage_watch':actual,'state':{},'native_unit_limits':None,'physical_policy':None,'disk_paths':[self.cap],'disk_floor_bytes':10*GIB,'begin':time.monotonic(),'wall_seconds':1800,'shutil':SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=11*GIB))}
  install(nodes,env)
  for name in ('predispatch','prerelease','running'):
   (self.cap/(name+'.json')).write_text('{}');env['boundaries']();self.assertEqual(env['state']['storage_observation']['regular_files'],len(list(self.cap.iterdir())))
  env['observe_storage']();env['final_disk']()
  # Real storage excess and disk refusal continue to abort the native boundary.
  tight=limits();tight['max_logical_bytes']=1;env['storage_watch']=S.StorageWatch(self.cap,tight)
  with self.assertRaises(S.StorageLimit):env['boundaries']()
  env['storage_watch']=actual;env['shutil']=SimpleNamespace(disk_usage=lambda p:SimpleNamespace(free=9*GIB))
  with self.assertRaisesRegex(RuntimeError,'disk floor'):env['boundaries']()
  with self.assertRaisesRegex(RuntimeError,'final disk floor'):env['final_disk']()
 def test_missing_release_and_policy_mismatch_never_admit(self):
  receipt=self.cap/'guard';receipt.mkdir();(receipt/'live.json').write_text(json.dumps({'command':['synthetic-command'],'phase':'running'}))
  kwargs={'required_paths':[self.cap],'wall_seconds':1800,'disk_floor_bytes':10*GIB}
  with self.assertRaises(FileNotFoundError):R.assert_guarded_worker(receipt,['synthetic-command'],**kwargs)
  (receipt/'release.json').write_text('{"kernel_controls_verified":false}')
  with self.assertRaisesRegex(RuntimeError,'guard not released'):R.assert_guarded_worker(receipt,['synthetic-command'],**kwargs)
  with self.assertRaisesRegex(RuntimeError,'command identity'):R.assert_guarded_worker(receipt,['other-command'],**kwargs)
  job=(CAP/PREFIX/'job.py').read_text();worker=function(job,'worker');text=ast.unparse(worker)
  self.assertLess(text.index('resources.assert_guarded_worker'),text.index('ResearchRun.start'))
  self.assertLess(text.index('execution guard policy differs from registration'),text.index('ResearchRun.start'))
  self.assertFalse({'numpy','torch','scipy','pandas'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)

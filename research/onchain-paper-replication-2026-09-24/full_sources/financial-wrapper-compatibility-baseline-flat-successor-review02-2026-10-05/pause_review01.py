from pathlib import Path
import ast,sys,os,signal,time,subprocess,types,json,resource
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-compatibility-baseline-flat-successor-preparation02-2026-10-05';sys.path.insert(0,str(P));sys.path.insert(0,str(P/'utilities'));import watch01 as W;import owned_io as IO
scope=D/'owned-publication02';scope.mkdir(mode=0o700)
tree=ast.parse((P/'caller03.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('raw','process_state','paused_census')];env={'Path':Path,'os':os,'signal':signal,'time':time,'subprocess':subprocess,'FILE':4194304,'D':scope};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-candidate-pause','exec'),env)
code="from pathlib import Path\nimport sys,time\np=Path(sys.argv[1])\nfor i in range(3000):\n (p/('body-%04d'%i)).write_bytes(b'x')\n time.sleep(.001)\ntime.sleep(10)\n"
def limits():resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304))
child=subprocess.Popen([sys.executable,'-B','-c',code,str(scope)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,preexec_fn=limits);results={}
try:
 identity=env['process_state'](child)[1];time.sleep(.03)
 try:W.census(scope)
 except ValueError as error:results['old_race_refusal']=str(error)
 else:results['old_race_refusal']=None
 # Actual stored publication is paused while the original watcher measures it.
 sample=env['paused_census'](child,identity,W,IO);results['paused_sample']=sample
 before=len(list(scope.iterdir()));time.sleep(.025);after=len(list(scope.iterdir()));assert after>before;results['actual_resumed_publication']=True
 try:env['paused_census'](child,identity+1,W,IO)
 except AssertionError:results['wrong_start_ticks_refused']=True
 else:raise AssertionError('wrong child identity accepted')
 primary=KeyboardInterrupt('controlled sampled fatal')
 def fatal(root):raise primary
 try:env['paused_census'](child,identity,types.SimpleNamespace(census=fatal,POLICY=W.POLICY),IO)
 except BaseException as error:assert error is primary;results['first_fatal_preserved']=True
 else:raise AssertionError('fatal vanished')
 begin=time.monotonic()
 while env['process_state'](child)[0]=='T':assert time.monotonic()-begin<1;time.sleep(.005)
 results['fatal_resumed_actual_child']=True
finally:
 try:os.killpg(child.pid,signal.SIGKILL)
 except ProcessLookupError:pass
 status=child.wait(timeout=10);results['actual_reaped_exit']=status;results['pid']=child.pid;results['start_ticks']=identity
assert not Path('/proc',str(child.pid)).exists();results['pid_absent']=True
assert results['old_race_refusal'] is not None, 'unpaused negative control was stable; do not claim reproduced race'
assert not any(n in sys.modules for n in ('numpy','torch','pandas'))
(D/'PAUSE_CHECK02.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))

"""Bounded real local Git cleanup and exact close-finally error precedence."""
import ast,hashlib,importlib.util,json,os,sys
from pathlib import Path
D=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('independent_transport_supplement',D/'remote-source/recover01.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M);checks=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def absent(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
before=set(os.listdir('/proc/self/fd'));body=M.git(['--version']);after=set(os.listdir('/proc/self/fd'));call=M.CALLS[-1]
ok('actual local Git version successful',body.startswith(b'git version') and call['exit']==0 and call['cleanup_failures']==[]);ok('actual original child and group absent',absent(call['pid']) and absent(call['pid'],True));ok('same observed FD numbers before/after',before==after)
tree=ast.parse((D/'remote-source/recover01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='write');tr=next(n for n in fn.body if isinstance(n,ast.Try));pairs=[]
for cls in (MemoryError,KeyboardInterrupt,SystemExit):
 p=D/'owned01'/('closed-fd-'+cls.__name__);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd);primary=cls('original write-body fatal')
 # Reuse the source's exact finalbody, with actual owned already-closed descriptor.
 # This isolates the close-error branch; it is not a real transport/write incident.
 code=ast.Module(body=[ast.Try(body=[ast.Raise(exc=ast.Name(id='primary',ctx=ast.Load()),cause=None)],handlers=[],orelse=[],finalbody=tr.finalbody)],type_ignores=[]);ast.fix_missing_locations(code);observed=None
 try:exec(compile(code,'<exact remote write finally>','exec'),{'os':os,'fd':fd,'primary':primary})
 except BaseException as e:observed=e
 ok('unguarded close replaces first fatal '+cls.__name__,type(observed)is OSError and observed.errno==9 and observed.__context__ is primary)
 pairs.append({'primary_type':cls.__name__,'observed_type':type(observed).__name__,'errno':observed.errno,'primary_only_context':observed.__context__ is primary})
out={'count':len(checks),'checks':checks,'actual_local_git_operation':call,'network_operations':0,'fd_scope':'Snapshot of current process FD numbers, not complete historical FD provenance','close_finally_witness':pairs,'qualification':'Exact source finally block over actually owned closed descriptors; isolated branch counterexample, not a production IO failure or native action.'};(D/'SUPPLEMENT01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'count':len(checks),'first_fatal_close_masking_confirmed':True}))

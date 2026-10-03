import ast,difflib,json
from pathlib import Path
P=Path(__file__).parent;a=(P/'baseline01.py').read_text();s=(P/'launcher02.py').read_text();b=s
# Exact inverse of declared finite headroom and authenticated class plumbing.
s=s.replace('def fatal(e,cleanup_types=()):return','def fatal(e):return').replace('not isinstance(e,(CleanupFailure,*cleanup_types))','not isinstance(e,CleanupFailure)')
s=s.replace('def select(first,later,cleanup_types=()):','def select(first,later):').replace('if fatal(first,cleanup_types):','if fatal(first):').replace('if fatal(later,cleanup_types) or first is None:','if fatal(later) or first is None:').replace('if isinstance(later,(CleanupFailure,*cleanup_types)):','if isinstance(later,CleanupFailure):')
s=s.replace('def actions(callbacks,primary=None,cleanup_types=()):','def actions(callbacks,primary=None):').replace('select(selected,e,cleanup_types);','select(selected,e);').replace('and fatal(selected,cleanup_types):','and fatal(selected):').replace('not fatal(selected,cleanup_types):','not fatal(selected):')
s=s.replace('def root_watch(directory,*,reserve_bytes=9*1024**2,reserve_entries=8):','def root_watch(directory):').replace('count<=32-reserve_entries and stat.S_ISREG','count<=32 and stat.S_ISREG').replace('total<=32*1024**2-reserve_bytes and shutil.disk_usage','total<=32*1024**2 and shutil.disk_usage')
s=s.replace('def cleanup_descendants(root,identity,supervisor_pid,ctx,*,register_cleanup_type=None):','def cleanup_descendants(root,identity,supervisor_pid,ctx):').replace('primary=None;observed={};cleanup_types=[]\n def attempt','primary=None;observed={}\n def attempt').replace('primary=select(primary,error,cleanup_types)\n def controller','primary=select(primary,error)\n def controller')
s=s.replace('  cleanup_types.append(owned.CleanupFailure)\n  if register_cleanup_type is not None:register_cleanup_type(owned.CleanupFailure)\n','')
s=s.replace("raw=sys.modules['proof_raw01'];primary=None;process=None;fds=[];handlers={};result=None;observed={};cleanup_types=[]","raw=sys.modules['proof_raw01'];primary=None;process=None;fds=[];handlers={};result=None;observed={}")
s=s.replace('primary=select(primary,e,cleanup_types)\n def stop','primary=select(primary,e)\n def stop').replace('cleanup_descendants(root,identity,process.pid,ctx,register_cleanup_type=cleanup_types.append)','cleanup_descendants(root,identity,process.pid,ctx)').replace('for fd in fds),primary,cleanup_types)','for fd in fds),primary)')
start=a.index('  # Pure observations only, never fabricate a lifecycle/native terminal.');end=a.index(' if primary is not None:raise primary\n return result',start)
s=s.replace('  primary=finish_tail(directory,root,identity,q,request_reference,process,observed,primary,result,cleanup_types)\n',a[start:end])
t=ast.parse(s);t.body=[n for n in t.body if not isinstance(n,ast.FunctionDef) or n.name not in {'tail_write','finish_tail'}]
assert ast.dump(t)==ast.dump(ast.parse(a))
(P/'launcher02.patch').write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='launcher01.py',tofile='launcher02.py')))
print(json.dumps({'inverse_whole_AST':'identical','allowed_changes':['final tail helper/call','finite output headroom','authenticated canonical cleanup type plumbing'],'unchanged':'request/release/recovery/source/native/supervisor/scientific/caller route'}))

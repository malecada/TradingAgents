import ast, hashlib, importlib.util, json, os, stat, sys, time, types
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE/'financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04'
PRIM=BASE/'held-consumer-final-recovery-preparation04-2026-10-03'
sys.path.insert(0,str(PRIM))
spec=importlib.util.spec_from_file_location('review_r4',PRIM/'recovery04.py');r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
versions={}
for name in ('capture01.py','capture02.py'):
 body=(ROOT/name).read_bytes();assert (HERE/name).read_bytes()==body;versions[name]=body
check(sha(versions['capture02.py'])=='d0153e8d08afbd9e0df4a3cd5e0715c16738b1008ada0870b8b5cf93c1cda17b','exact02')
loops={};mains={}
for name,body in versions.items():
 tree=ast.parse(body);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');mains[name]=main
 loops[name]=next(n for n in main.body if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=='inventory')
old=versions['capture01.py'].decode().splitlines(keepends=True);new=versions['capture02.py'].decode().splitlines(keepends=True)
a=loops['capture01.py'];b=loops['capture02.py']
# New comment introducing corrected loop is part of declared substitution.
inverse=''.join(new[:b.lineno-2]+old[a.lineno-2:a.end_lineno]+new[b.end_lineno:])
check(inverse.encode()==versions['capture01.py'],'whole byte inverse only final loop/comment')
for name in mains:
 mains[name].body.remove(loops[name])
check(ast.dump(mains['capture01.py'])==ast.dump(mains['capture02.py']),'all other main AST unchanged')

def inv(root):
 rows=[]
 def visit(p,rel):
  s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory';rows.append(r)
   for q in sorted(p.iterdir()):visit(q,q.name if rel=='.' else rel+'/'+q.name)
   return
  else:
   b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b),union_path='tiny/'+rel)
  rows.append(r)
 visit(root,'.');return sorted(rows,key=lambda r:r['path'])
def require(v,msg):
 if not v:raise ValueError(msg)
def run(loop,inventory):
 env=dict(Path=Path,stat=stat,os=os,r4=r4,require=require,digest=sha,inventory=inventory,time=time,start=time.monotonic(),FILE=4*1024**2)
 try:exec(compile(ast.Module(body=[loop],type_ignores=[]),'<exact-final-original-loop>','exec'),env);return 'accepted'
 except BaseException as e:return type(e).__name__+': '+str(e)
results=[]
for case in ('unchanged','extra-file','extra-directory','extra-link','remove','body','mode','link-target'):
 root=HERE/('owned-'+case);root.mkdir(mode=0o700);(root/'body').write_bytes(b'opaque original\n');(root/'literal').symlink_to('absent')
 before=inv(root)
 if case=='extra-file':(root/'late').write_bytes(b'late opaque\n')
 elif case=='extra-directory':(root/'late').mkdir()
 elif case=='extra-link':(root/'late').symlink_to('absent-late')
 elif case=='remove':(root/'body').unlink()
 elif case=='body':(root/'body').write_bytes(b'changed opaque\n')
 elif case=='mode':(root/'body').chmod(0o600)
 elif case=='link-target':(root/'literal').unlink();(root/'literal').symlink_to('other-absent')
 inventory=[dict(scope='tiny',original_root=str(root),members=before)]
 oldres=run(loops['capture01.py'],inventory);newres=run(loops['capture02.py'],inventory)
 check((newres=='accepted')==(case=='unchanged'),'02 '+case)
 if case.startswith('extra-'):check(oldres=='accepted','original RED '+case)
 results.append(dict(case=case,old=oldres,new=newres,inventory=inventory,actual_members=inv(root)))
# Exact put function, real owned file and actual EBADF from builtin close.
# Controlled fsync seam closes only its owned fd then raises the original fatal.
tree=ast.parse(versions['capture02.py']);put=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='put')
fatal=MemoryError('controlled first fatal at fsync');fd_saved=[]
def injected_fsync(fd):
 fd_saved.append(fd);os.close(fd);raise fatal
env={'require':require,'FILE':4*1024**2,'os':types.SimpleNamespace(fsync=injected_fsync)}
exec(compile(ast.Module(body=[put],type_ignores=[]),'<exact-put>','exec'),env)
try:env['put'](HERE/'owned-put-fatal',b'opaque fatal witness\n')
except BaseException as e:
 put_result={'raised_type':type(e).__name__,'raised_errno':getattr(e,'errno',None),'primary_preserved':e is fatal,'context_is_primary':e.__context__ is fatal,'descriptor_absent':not Path('/proc/self/fd/'+str(fd_saved[0])).exists()}
else:raise AssertionError('fatal witness unexpectedly returned')
check(put_result['raised_type']=='OSError' and put_result['raised_errno']==9 and not put_result['primary_preserved'] and put_result['context_is_primary'],'CF2 real close masks first fatal')
out={'source_sha256':{n:sha(b) for n,b in versions.items()},'checks':checks,'count':len(checks),'late_member_witnesses':results,'put_fatal_witness':put_result,'qualification':'Exact extracted source with owned tiny opaque trees. Fsync callback is deliberately injected; descriptor close/EBADF and exception identity are actual. No actual Root failure or native launch asserted.'}
(HERE/'CHECKS01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({'count':len(checks),'source_sha256':out['source_sha256'],'put_fatal_witness':put_result}))

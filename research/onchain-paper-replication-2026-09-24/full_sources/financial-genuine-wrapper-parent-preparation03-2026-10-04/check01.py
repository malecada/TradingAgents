"""Exact PF1 AST and real directory IO; genuine errors, no native controls."""
import ast,copy,json,os,types
from pathlib import Path
import recovery04 as R
from owned_io import _fatal,CleanupFailure
H=Path(__file__).resolve().parent;checks=[];outcomes=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def suite(name):
 t=ast.parse((H/name).read_bytes());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='launch')
 return next(n for n in f.body if isinstance(n,ast.Try) and any('os.fsync(fd)'==ast.unparse(x) for x in n.body))
old=suite('baseline-parent01.py');new=suite('parent01.py')
def run(node,primary,secondary):
 fd=os.open(H,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);calls=[];caught=None
 def sync(value):
  calls.append('fsync');os.fsync(value)
  if primary is not None:raise primary
 def close(value):
  calls.append('close');os.close(value)
  if secondary is not None:raise secondary
 env={'os':types.SimpleNamespace(fsync=sync,close=close),'fd':fd,'R':R}
 try:exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[])),'<exact-directory-close>','exec'),env)
 except BaseException as e:caught=e
 check('actual directory fsync then single close',calls==['fsync','close'])
 try:os.fstat(fd)
 except OSError:pass
 else:raise AssertionError('actual descriptor remains open')
 return caught
primary=KeyboardInterrupt('PF1 original fatal');secondary=OSError('PF1 secondary close');red=run(old,primary,secondary);check('RED exact old masks original fatal',red is secondary)
(H/'RED01.json').write_text(json.dumps({'id':'PF1','original_fatal':type(primary).__name__,'escaped':type(red).__name__,'escaped_is_secondary':red is secondary,'real_directory_fsync_close':True})+'\n')
for pclass in [None,ValueError,MemoryError,KeyboardInterrupt,SystemExit]:
 for sclass in [None,OSError,MemoryError,KeyboardInterrupt,SystemExit]:
  p=None if pclass is None else pclass('original primary');s=None if sclass is None else sclass('secondary cleanup');got=run(new,p,s)
  if p is not None and _fatal(p):check('first primary fatal identity',got is p)
  elif s is not None and _fatal(s):check('first cleanup fatal identity',got is s)
  elif s is None:check('no secondary preserves primary',got is p)
  else:check('ordinary uncertainty retains both',isinstance(got,CleanupFailure) and got.failures==tuple(x for x in (p,s) if x is not None))
  outcomes.append({'primary':None if p is None else type(p).__name__,'secondary':None if s is None else type(s).__name__,'observed':None if got is None else type(got).__name__})
inv=json.loads((H/'INVERSE01.json').read_bytes())
for name,key in [('parent01.py','parent'),('supervisor01.py','supervisor')]:
 actual=(H/name).read_text();baseline=(H/('baseline-'+name)).read_text();restored=actual.replace(inv[key]['new'],inv[key]['old']);check(name+' complete byte inverse',restored==baseline);check(name+' complete AST inverse',ast.dump(ast.parse(restored))==ast.dump(ast.parse(baseline)))
(H/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'matrix':outcomes,'actual_native_commands':False},indent=2)+'\n');print(len(checks),'PF1 checks passed')

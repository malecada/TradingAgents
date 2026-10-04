import ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent/'financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04';PRIM=HERE.parent/'held-consumer-final-recovery-preparation04-2026-10-03'
sys.path.insert(0,str(PRIM));spec=importlib.util.spec_from_file_location('r4_put',PRIM/'recovery04.py');r4=importlib.util.module_from_spec(spec);spec.loader.exec_module(r4)
b=(ROOT/'capture03.py').read_bytes();(HERE/'capture03.py').write_bytes(b)
checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def require(v,msg):
 if not v:raise ValueError(msg)
check(hashlib.sha256(b).hexdigest()=='1fd5699ecf0238c57a58919f4afa652750ab6c58bac6789332f38c725f534b75','exact03')
old=(HERE/'capture02.py').read_text();new=b.decode();told=ast.parse(old);tnew=ast.parse(new)
a=next(n for n in told.body if isinstance(n,ast.FunctionDef) and n.name=='put');p=next(n for n in tnew.body if isinstance(n,ast.FunctionDef) and n.name=='put')
lines=new.splitlines(keepends=True);oldlines=old.splitlines(keepends=True)
inverse=''.join(lines[:p.lineno-1]+oldlines[a.lineno-1:a.end_lineno]+lines[p.end_lineno:]).replace('put(r4, destination / relative, body)','put(destination / relative, body)').replace('put(r4, union /','put(union /').replace('put(r4, HERE /','put(HERE /')
check(inverse==old,'full byte inverse put and four call sites')
check(ast.dump(ast.parse(inverse))==ast.dump(told),'complete AST inverse')
fdresults=[]
for i,kind in enumerate((MemoryError,KeyboardInterrupt,SystemExit,GeneratorExit,ValueError,OSError)):
 primary=kind('first controlled exception');fds=[]
 def fsync(fd):fds.append(fd);os.close(fd);raise primary
 env={'require':require,'FILE':4*1024**2,'os':types.SimpleNamespace(fsync=fsync,write=os.write)}
 exec(compile(ast.Module(body=[p],type_ignores=[]),'<actual03-put>','exec'),env)
 try:env['put'](r4,HERE/('owned03-fatal'+str(i)),b'opaque\n')
 except BaseException as error:
  expectfatal=kind in (MemoryError,KeyboardInterrupt,SystemExit,GeneratorExit)
  check((error is primary) if expectfatal else (type(error).__name__=='CleanupFailure' and primary in error.failures),'first fatal/ordinary close '+kind.__name__)
  check(not Path('/proc/self/fd/'+str(fds[0])).exists(),'actual descriptor absent '+kind.__name__)
  fdresults.append(dict(primary=kind.__name__,raised=type(error).__name__,same_primary=error is primary,descriptor_absent=True))
 else:raise AssertionError('exception missing')
env={'require':require,'FILE':4*1024**2,'os':os};exec(compile(ast.Module(body=[p],type_ignores=[]),'<actual03-put>','exec'),env)
for i,body in enumerate((b'',b'opaque complete\n')):
 path=HERE/('owned03-valid'+str(i));env['put'](r4,path,body);check(path.read_bytes()==body,'valid readback '+str(i));check(path.stat().st_mode&0o777==0o600,'private body '+str(i))
 try:env['put'](r4,path,body)
 except FileExistsError:checks.append('exclusive collision '+str(i))
 else:raise AssertionError('exclusive collision accepted')
redirect=HERE/'owned03-redirect';redirect.symlink_to(HERE/'owned-unchanged',target_is_directory=True)
try:env['put'](r4,redirect/'not-created',b'x')
except ValueError:checks.append('redirect refused')
else:raise AssertionError('redirect accepted')
check(not (HERE/'owned-unchanged/not-created').exists(),'redirect target unchanged')
# Saved original small real files are retained. Oversize uses only scalar len protocol;
# no 4MiB+ artifact or array is constructed.
class TooLarge:
 def __len__(self):return 4*1024**2+1
try:env['put'](r4,HERE/'not-created-oversize',TooLarge())
except ValueError:checks.append('over4MiB refused before IO')
else:raise AssertionError('oversize accepted')
(HERE/'CHECKS03.json').write_text(json.dumps(dict(count=len(checks),checks=checks,fdresults=fdresults,qualification='Actual R4.new_file/owned cleanup; controlled fsync seam closes genuinely owned descriptor before exception. No actual Root failure, output archive or numerical execution.'),sort_keys=True,indent=2)+'\n');print(json.dumps({'count':len(checks),'fdresults':fdresults}))

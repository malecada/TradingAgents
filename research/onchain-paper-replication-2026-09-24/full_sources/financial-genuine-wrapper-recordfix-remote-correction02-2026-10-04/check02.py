import ast,hashlib,json,os,sys,tempfile,types
from pathlib import Path
H=Path(__file__).resolve().parent;s=Path(sys.argv[1]).read_text();tree=ast.parse(s);checks=[];details=[]
def ok(n,v):
 checks.append({'check':n,'passed':bool(v)})
def select(primary,secondary):
 return next((e for e in (primary,secondary) if isinstance(e,MemoryError) or not isinstance(e,Exception)),primary)
def parts(s):
 t=ast.parse(s);ns={'os':os,'FILE':4*1024**2,'Path':Path,'hashlib':hashlib,'json':json,'HERE':H,'CALLS':[]}
 chosen=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','encode','write','_raise_retained','entry')]
 exec(compile(ast.Module(body=chosen,type_ignores=[]),'extracted-actual-source','exec'),ns)
 if 'entry' not in ns:
  guard=next(n for n in t.body if isinstance(n,ast.If) and isinstance(n.test,ast.Compare))
  fn=ast.FunctionDef(name='entry',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=guard.body,decorator_list=[])
  exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'extracted-original-top-level','exec'),ns)
 return ns
errors=[MemoryError,KeyboardInterrupt,SystemExit,ValueError,OSError]
with tempfile.TemporaryDirectory(prefix='recordfix-remote02-offline-') as d:
 base=Path(d)
 for i,P in enumerate(errors):
  for j,S in enumerate(errors):
   ns=parts(s);first=P('original-write-primary');second=S('actual-close-secondary');calls=[]
   def fsync(fd):os.fsync(fd);raise first
   def close(fd):calls.append(fd);os.close(fd);raise second
   ns['os']=types.SimpleNamespace(**{n:getattr(os,n) for n in ('open','write','O_WRONLY','O_CREAT','O_EXCL','O_NOFOLLOW')},fsync=fsync,close=close)
   path=base/('write-%d-%d'%(i,j));seen=None
   try:ns['write'](path,b'owned-small-opaque-body')
   except BaseException as e:seen=e
   wanted=select(first,second);ok('write error selection %s/%s'%(P.__name__,S.__name__),seen is wanted)
   ok('actual fd closed once %s/%s'%(P.__name__,S.__name__),len(calls)==1 and path.read_bytes()==b'owned-small-opaque-body')
   try:os.fstat(calls[0]);closed=False
   except OSError:closed=True
   ok('actual fd absent %s/%s'%(P.__name__,S.__name__),closed)
   details.append({'scope':'write','primary':P.__name__,'secondary':S.__name__,'observed':type(seen).__name__,'expected':type(wanted).__name__,'same_original_exception':seen is wanted})
 for P in errors:
  for S in errors:
   ns=parts(s);first=P('original-main-primary');second=S('journal-secondary');calls=[]
   def main():raise first
   def write(path,body):calls.append((str(path),hashlib.sha256(body).hexdigest()));raise second
   ns.update(main=main,write=write);seen=None
   try:ns['entry']()
   except BaseException as e:seen=e
   wanted=select(first,second);ok('outer journal error selection %s/%s'%(P.__name__,S.__name__),seen is wanted)
   ok('one attempted failure journal %s/%s'%(P.__name__,S.__name__),len(calls)==1)
   details.append({'scope':'entry','primary':P.__name__,'secondary':S.__name__,'observed':type(seen).__name__,'expected':type(wanted).__name__,'same_original_exception':seen is wanted})
 for P in (MemoryError,KeyboardInterrupt,SystemExit):
  ns=parts(s);owned=base/('entrycollision-'+P.__name__);owned.mkdir();(owned/'FAILED01.json').write_bytes(b'original-owned-collision-preserved');first=P('original-transport-fatal')
  def main():raise first
  ns.update(main=main,HERE=owned);seen=None
  try:ns['entry']()
  except BaseException as e:seen=e
  ok('actual O_EXCL journal first-fatal '+P.__name__,seen is first)
  ok('actual collision original bytes preserved '+P.__name__,(owned/'FAILED01.json').read_bytes()==b'original-owned-collision-preserved')
 ns=parts(s);path=base/'happy';ns['write'](path,b'small');ok('actual happy original byte writer',path.read_bytes()==b'small' and (path.stat().st_mode&0o777)==0o600)
 try:ns['write'](path,b'duplicate');duplicate=False
 except FileExistsError:duplicate=True
 ok('O_EXCL original duplicate refusal',duplicate and path.read_bytes()==b'small')
 try:ns['write'](base/'oversize',b'a'*(4*1024**2+1));oversize=False
 except ValueError:oversize=True
 ok('unchanged 4MiB early refusal',oversize and not (base/'oversize').exists())
 ns=parts(s);seen=[];ns['main']=lambda:seen.append('main-complete');ns['write']=lambda *a:seen.append('unexpected-journal');ns['entry']();ok('happy entry invokes main only',seen==['main-complete'])
if sys.argv[2]=='GREEN':
 v=json.loads((H/'INVERSE02.json').read_text());inverse=s
 for e in reversed(v['edits']):ok('unique narrow inverse',inverse.count(e['new'])==1);inverse=inverse.replace(e['new'],e['old'])
 original=(H/'original-recover01.py').read_text();ok('full original byte inverse',inverse==original);ok('full original AST inverse',ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original)))
 for n in ('git','main','validate_fixed_selection'):
  def fn(raw):return ast.dump(next(x for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef) and x.name==n),include_attributes=False)
  ok('unchanged actual '+n,fn(s)==fn(original))
bad=[r['check'] for r in checks if not r['passed']];out={'status':'PASS' if not bad else 'FAIL','phase':sys.argv[2],'source_sha256':hashlib.sha256(s.encode()).hexdigest(),'check_count':len(checks),'checks':checks,'error_pairs':details,'failures':bad,'network':False,'numerical_imports':False,'qualification':'Extracted actual source functions with real tiny owned file descriptors and bounded metadata fault injection; no authority, remote or numerical claim.'}
(H/(sys.argv[2]+'02.json')).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps({'phase':sys.argv[2],'checks':len(checks),'failures':len(bad)}));sys.exit(1 if bad else 0)

"""Independent real owned dist-info metadata; no patched actual discovery/API."""
import ast,copy,hashlib,importlib.metadata as M,importlib.util,itertools,json,os,sys,types
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'source';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');sys.path.insert(0,str(CAP));spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.independent_runtime_controls',S/'candidate.py');C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C);T=D/'owned02';T.mkdir();checks=[];witness=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,f):
 try:f()
 except (C.Unavailable,ValueError,OSError,TypeError,KeyError):ok(n,True);return
 raise AssertionError('accepted '+n)
def extract(name):return copy.deepcopy(next(x for x in ast.parse((S/'candidate.py').read_text()).body if isinstance(x,ast.FunctionDef) and x.name==name))
def compile_fn(fn,extra):
 ns=dict(vars(C));ns.update(extra);exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<owned-dependency-inputs-only>','exec'),ns);return ns[fn.name]
site=T/'site';site.mkdir();meta=site/'review_pkg-1.2.dist-info';meta.mkdir();record=meta/'RECORD';metadata=meta/'METADATA';metadata.write_bytes(b'Name: review-pkg\nVersion: 1.2\n\nOpaque engineering metadata\n');raw=b'review_pkg-1.2.dist-info/RECORD,,\nreview_pkg/_vendor/opaque-2.dist-info/RECORD,,\n';record.write_bytes(raw);row={'name':'review-pkg','version':'1.2','record':str(record),'record_sha256':C.sha(raw)}
# Only two dependency inputs change: interpreter prefix/site paths. Discovery is
# the real CPython PathDistribution implementation reading actual owned metadata.
fn=extract('_runtime_record')
for x in fn.body:
 if isinstance(x,ast.Import):x.names=[n for n in x.names if n.name!='sysconfig']
record_fn=compile_fn(fn,{'sys':types.SimpleNamespace(prefix=str(T)),'sysconfig':types.SimpleNamespace(get_path=lambda key:str(site))})
ok('owned real installation admitted',record_fn(row)['record']==str(record));d=next(iter(M.distributions(path=[str(site)],name='review-pkg')));ok('real installed own origin',type(d)is M.PathDistribution and d._path==meta);ok('vendored inventory has two RECORDs',len([f for f in d.files if str(f).endswith('.dist-info/RECORD')])==2)
for name in ('REVIEW-PKG','review_pkg','Review.Pkg'):
 ok('normalized real discovery '+name,record_fn(dict(row,name=name))['name']=='review-pkg')
for k,values in {'name':[None,True,'','..','x/y','different'],'version':[None,1,'','9.9'],'record':[None,1,'relative',str(meta/'../RECORD'),str(metadata)],'record_sha256':[None,1,'','A'*64,'0'*64]}.items():
 for i,value in enumerate(values):refuse('registered descriptor '+k+str(i),lambda k=k,value=value:record_fn(dict(row,**{k:value})))
for bad in ({},[],None,dict(row,extra=1)):refuse('complete descriptor '+str(type(bad)),lambda bad=bad:record_fn(bad))
# True duplicate installed origin. Both actual PathDistribution objects are read.
dup=site/'review_pkg-2.0.dist-info';dup.mkdir();(dup/'METADATA').write_bytes(metadata.read_bytes());(dup/'RECORD').write_bytes(b'opaque');M.MetadataPathFinder.invalidate_caches();refuse('duplicate actual installed origin',lambda:record_fn(row));dup.rename(T/'retained-duplicate');M.MetadataPathFinder.invalidate_caches()
# Missing installed origin must not fall back to default source cwd discovery.
meta.rename(T/'retained-meta');M.MetadataPathFinder.invalidate_caches();refuse('missing installed origin',lambda:record_fn(row));(T/'retained-meta').rename(meta);M.MetadataPathFinder.invalidate_caches()
original=metadata.read_bytes()
for i,b in enumerate((b'Name: other\nVersion: 1.2\n',b'Name: review-pkg\nVersion: 8.0\n',b'Name: review-pkg\nName: review-pkg\nVersion: 1.2\n',b'Name: review-pkg\nVersion: 1.2\nVersion: 1.2\n',b'Name: review-pkg\n',b'Version: 1.2\n')):
 metadata.write_bytes(b);refuse('METADATA exact headers '+str(i),lambda:record_fn(row));(T/('retained-header-'+str(i))).write_bytes(b)
metadata.write_bytes(original);os.link(metadata,T/'metadata-hardlink');ok('real stable METADATA hardlink admitted',metadata.stat().st_nlink==2 and record_fn(row)['version']=='1.2')
# Default discovery really sees an owned source egg-info. Selected source uses
# explicit site inputs and still reads the unchanged real installed dist-info.
shadow=T/'source-cwd';shadow.mkdir();egg=shadow/'review_pkg.egg-info';egg.mkdir();(egg/'PKG-INFO').write_bytes(b'Name: review-pkg\nVersion: 99.0\n');sys.path.insert(0,str(shadow));M.MetadataPathFinder.invalidate_caches()
try:ok('actual owned cwd shadow exists',M.version('review-pkg')=='99.0');ok('explicit installed origin avoids shadow',record_fn(row)['version']=='1.2')
finally:sys.path.remove(str(shadow));M.MetadataPathFinder.invalidate_caches()
# RECORD and METADATA refusal before any potentially blocking read.
for name in ('RECORD','METADATA'):
 p=meta/name;hold=meta/(name+'.held');p.rename(hold);refuse('missing '+name,lambda:record_fn(row));p.mkdir();refuse('directory '+name,lambda:record_fn(row));p.rename(meta/(name+'.directory'));p.symlink_to(hold.name);refuse('symlink '+name,lambda:record_fn(row));p.rename(meta/(name+'.symlink'));os.mkfifo(p);refuse('FIFO '+name,lambda:record_fn(row));p.unlink();hold.rename(p)
record.write_bytes(raw+b'mutated');refuse('actual RECORD wrong bytes',lambda:record_fn(row));record.write_bytes(raw)
# Bounded sparse owned extent, not an amendment to an actual native artifact cap.
oversized=T/'over-limit';oversized.mkdir();big=oversized/'METADATA'
with big.open('wb') as f:f.truncate(C.FILE+1)
refuse('4MiB+1 metadata extent',lambda:C._runtime_record_bytes(big))
for roots,label in ((str(T/'missing'),'different roots'),(str(site/'..'/'site'),'noncanonical roots'),(str(T.parent),'outside interpreter prefix')):
 f=compile_fn(copy.deepcopy(fn),{'sys':types.SimpleNamespace(prefix=str(T)),'sysconfig':types.SimpleNamespace(get_path=lambda key,roots=roots:roots)});refuse(label,lambda:f(row))
# Duplicate normalized map names are rejected by the exact added predicate.
runtime=extract('runtime_check');stmt=next(x for x in runtime.body if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and any(isinstance(z,ast.Constant) and z.value=='duplicate normalized runtime distribution' for z in ast.walk(x)));code=compile(ast.Module(body=[stmt],type_ignores=[]),'<exact-normalization-guard>','exec')
refuse('duplicate normalized rows',lambda:exec(code,{'require':C.require,'_runtime_distribution_name':C._runtime_distribution_name,'rows':[row,dict(row,name='Review_Pkg')]}))
# Read-time mutations at exact source boundaries, with real descriptors/files.
def event():return ast.Expr(value=ast.Call(func=ast.Name(id='review_event',ctx=ast.Load()),args=[],keywords=[]))
def census():return set(os.listdir('/proc/self/fd'))
for label,mutator in [('bytes',lambda p:p.write_bytes(b'other opaque bytes')),('mode',lambda p:p.chmod(0o640)),('linkcount',lambda p:os.link(p,p.with_name('extra-link')))]:
 area=T/('change-'+label);area.mkdir();p=area/'RECORD';p.write_bytes(b'original opaque bytes');reader=extract('_runtime_record_bytes');tr=next(x for x in reader.body if isinstance(x,ast.Try));wh=next(x for x in tr.body if isinstance(x,ast.While));wh.body.insert(1,event());called=[]
 def change():
  if not called:called.append(True);mutator(p)
 f=compile_fn(reader,{'review_event':change});before=census();refuse('actual read-time '+label,lambda:f(p));ok('read-time descriptors closed '+label,census()==before)
# Fatal cleanup on actually acquired descriptors; no monkeypatch of modules.
for i,(pc,cc) in enumerate(itertools.product((None,OSError,MemoryError,KeyboardInterrupt,SystemExit),repeat=2)):
 p=T/('fatal-'+str(i));p.write_bytes(b'opaque');reader=extract('_runtime_record_bytes');tr=next(x for x in reader.body if isinstance(x,ast.Try));pos=next(i for i,x in enumerate(tr.body) if isinstance(x,ast.While));tr.body.insert(pos,event());primary=None if pc is None else pc('body');secondaries=[];closed=[]
 class Close(ast.NodeTransformer):
  def visit_Call(self,node):
   node=self.generic_visit(node)
   if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='os' and node.func.attr=='close':node.func=ast.Name(id='review_close',ctx=ast.Load())
   return node
 reader=Close().visit(reader)
 def throw():
  if primary is not None:raise primary
 def close(fd):
  os.close(fd);closed.append(fd)
  if cc is not None:
   err=cc('close');secondaries.append(err);raise err
 f=compile_fn(reader,{'review_event':throw,'review_close':close});before=census();caught=None
 try:f(p)
 except BaseException as e:caught=e
 fatal=lambda e:e is not None and (isinstance(e,MemoryError) or not isinstance(e,Exception))
 expected=primary if fatal(primary) else secondaries[0] if secondaries and fatal(secondaries[0]) else primary if cc is None else None
 ok('first fatal identity '+str(i),caught is expected if expected is not None else caught is None if cc is None else type(caught).__name__=='CleanupFailure');ok('all acquired descriptors closed '+str(i),len(closed)==len(p.parent.parts)+1 and len(set(closed))==len(closed) and census()==before)
ok('no numerical imports',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
(D/'OWNED_REVIEW02.json').write_text(json.dumps({'checks':len(checks),'names':checks,'source_sha256':hashlib.sha256((S/'candidate.py').read_bytes()).hexdigest(),'method':'real owned PathDistribution discovery; exact AST helper except dependency inputs sys.prefix/sysconfig path roots, plus explicit callback scheduling for filesystem mutation/fatal cleanup; no module monkeypatch','retained_oversized_negative_witness':{'path':str(big.relative_to(D)),'bytes':big.stat().st_size,'outside_actual_native_scope':True},'no_numeric_imports':True,'authority':None},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'source_only':True}))

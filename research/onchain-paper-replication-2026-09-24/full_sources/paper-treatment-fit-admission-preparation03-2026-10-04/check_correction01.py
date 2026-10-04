import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
D=Path(__file__).resolve().parent;checks=[]
def check(label,v):
 if not v:raise AssertionError(label)
 checks.append(label)
def load(path,label):
 s=importlib.util.spec_from_file_location(label,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
new=load(D/'overlay/tradingagents/research/onchain_replication/treatment_admission.py','new');old=load(D/'baseline-treatment_admission01.py','old')
job=D.parent/'paper-treatment-production-preparation02-2026-10-04/overlay/tradingagents/research/onchain_replication/job.py'
node=next(n for n in ast.parse(job.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile');a=next(n for n in node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cells' for t in n.targets))
cell='treatment-eth-whale-2020-01-06';week='2020-01-06T00:00:00Z';pin='1'*64
row=eval(compile(ast.Expression(a.value.elt.args[1]),'actual-job-fallback','eval'),{'name':cell})
claim={'experiment_id':'opaque-only','source':'1'*40,'registration_sha256':pin,'experiment':{'cells':[cell]}};terminal={'status':'failed','experiment_id':'opaque-only','claim_sha256':pin};plan={'expected_weeks':[week]};args=(claim,terminal,[row],pin,pin,plan,week,'whale','ETH')
try:old.disposition(*args)
except ValueError as e:check('DA1 RED actual fallback refused',str(e)=='cell asset/week differs')
else:raise AssertionError('DA1 RED missing')
check('DA1 GREEN unchanged fallback object retained',new.disposition(*args,absent=True) is row and set(row)=={'id','status','reason'})
for key,value in [('status','complete'),('id','wrong'),('reason','')]:
 altered=copy.deepcopy(args);altered[2][0][key]=value
 try:new.disposition(*altered,absent=True)
 except (ValueError,StopIteration):checks.append('DA1 refuses altered '+key)
 else:raise AssertionError(key)
for absent,metadata in [(False,row),(True,{**row,'asset':'ETH','week':week})]:
 altered=list(args);altered[2]=[metadata]
 try:new.disposition(*altered,absent=absent)
 except ValueError:checks.append('DA1 separates absent and retained shape '+str(absent))
 else:raise AssertionError('wrong shape')
retained={**row,'asset':'ETH','week':week};altered=list(args);altered[2]=[retained];check('DA1 retained durable shape unchanged',new.disposition(*altered) is retained)
# Exact old owned-fd seam, real fd, injected fdopen/read/close failures only.
tree=ast.parse((D/'baseline-treatment_admission01.py').read_text());reader=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_reader');meta=next(n for n in reader.body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='metadata')
seam=[n for n in meta.body if isinstance(n,ast.With) or (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='fd')];program=compile(ast.Module(body=seam,type_ignores=[]),'original-exact-IO-seam','exec')
path=D/'opaque-reader02.txt';path.write_bytes(b'opaque only\n')
class API:
 O_RDONLY=os.O_RDONLY;O_NOFOLLOW=os.O_NOFOLLOW
 def __init__(self,wrapper,close_error=None):self.created=[];self.wrapper=wrapper;self.close_error=close_error;self.closed=[]
 def open(self,*args):fd=os.open(*args);self.created.append(fd);return fd
 def fdopen(self,*args):return self.wrapper(*args)
 def close(self,fd):os.close(fd);self.closed.append(fd)
 def fstat(self,fd):return os.fstat(fd)
def openfail(*args):raise MemoryError('fdopen')
api=API(openfail)
try:exec(program,{'os':api,'stat':stat,'path':path,'require':old.require,'LIMIT':old.LIMIT})
except MemoryError:pass
fd=api.created[0];check('DA2 RED acquired fd leaked',os.fstat(fd).st_size==12);os.close(fd)
primary=KeyboardInterrupt('read fatal');secondary=OSError('close ordinary')
class Stream:
 def __init__(self,fd,mode,read_error=None,close_error=None):self.real=os.fdopen(fd,mode);self.read_error=read_error;self.close_error=close_error;self.closes=0
 def __enter__(self):return self
 def __exit__(self,*args):self.close()
 def fileno(self):return self.real.fileno()
 def read(self,n):
  if self.read_error is not None:raise self.read_error
  return self.real.read(n)
 def close(self):
  self.closes+=1;self.real.close()
  if self.close_error is not None:raise self.close_error
api=API(lambda fd,mode:Stream(fd,mode,primary,secondary))
try:exec(program,{'os':api,'stat':stat,'path':path,'require':old.require,'LIMIT':old.LIMIT})
except BaseException as e:check('DA3 RED close replaces original fatal',e is secondary and e.__context__ is primary)
# Exact successor helper AST, removing only its local import to inject OS facade.
node=next(n for n in ast.parse((D/'overlay/tradingagents/research/onchain_replication/treatment_admission.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_owned_metadata_bytes');node=copy.deepcopy(node);node.body=[n for n in node.body if not isinstance(n,ast.Import)]
helper_program=compile(ast.Module(body=[node],type_ignores=[]),'exact-successor-owned-IO','exec')
def runhelper(api):
 ns={'os':api,'stat':stat,'require':new.require,'LIMIT':new.LIMIT,'_reader_cleanup':new._reader_cleanup};exec(helper_program,ns);return ns['_owned_metadata_bytes'](path)
api=API(openfail)
try:runhelper(api)
except MemoryError:pass
check('DA2 GREEN fd ownership cleanup called',api.closed==api.created and len(api.created)==1)
try:os.fstat(api.created[0])
except OSError:checks.append('DA2 GREEN actual fd absent')
else:raise AssertionError('fd leaked')
classes=(None,OSError,ValueError,MemoryError,KeyboardInterrupt,SystemExit)
for rcls in classes:
 for ccls in classes:
  read_error=rcls('read') if rcls else None;close_error=ccls('close') if ccls else None;streams=[]
  def wrapper(fd,mode):
   s=Stream(fd,mode,read_error,close_error);streams.append(s);return s
  api=API(wrapper);errors=[e for e in (read_error,close_error) if e is not None];expected=next((e for e in errors if isinstance(e,MemoryError) or not isinstance(e,Exception)),errors[0] if errors else None);observed=None;value=None
  try:value=runhelper(api)
  except BaseException as e:observed=e
  check('first fatal pair '+str((rcls,ccls)),observed is expected)
  check('stream closes once '+str((rcls,ccls)),len(streams)==1 and streams[0].closes==1 and streams[0].real.closed)
  if expected is None:check('real successful read bytes',value==b'opaque only\n')
  elif len(errors)==2:check('secondary object retained '+str((rcls,ccls)),set(id(e) for e in expected.__cause__.exceptions)=={id(e) for e in errors if e is not expected})
  try:os.fstat(api.created[0])
  except OSError:checks.append('actual owned fd absent '+str((rcls,ccls)))
  else:raise AssertionError('unclosed fd')
# Full cleanup primary + two callbacks Cartesian: all callbacks and first fatal.
for pc in classes:
 for ac in classes:
  for bc in classes:
   es=[c(str(i)) if c else None for i,c in enumerate((pc,ac,bc))];events=[]
   def action(i):
    events.append(i)
    if es[i] is not None:raise es[i]
   ordered=[e for e in es if e is not None];expected=next((e for e in ordered if isinstance(e,MemoryError) or not isinstance(e,Exception)),ordered[0] if ordered else None);observed=None
   try:new._reader_cleanup((lambda:action(1),lambda:action(2)),es[0])
   except BaseException as e:observed=e
   check('cleanup matrix identity '+str((pc,ac,bc)),observed is expected)
   check('cleanup matrix all attempts '+str((pc,ac,bc)),events==[1,2])
inv=json.loads((D/'CORRECTION_INVERSE01.json').read_text());s=(D/'overlay/tradingagents/research/onchain_replication/treatment_admission.py').read_text()
for edit in reversed(inv['edits']):check('exact inverse single occurrence',s.count(edit['new'])==1);s=s.replace(edit['new'],edit['old'])
check('full module byte inverse',s.encode()==(D/'baseline-treatment_admission01.py').read_bytes());check('full AST inverse',ast.dump(ast.parse(s))==ast.dump(ast.parse((D/'baseline-treatment_admission01.py').read_bytes())))
for name in ('population_assembly.py','run.py','evaluation.py'):
 rel='overlay/tradingagents/research/onchain_replication/'+name;check('unchanged caller '+name,(D/rel).read_bytes()==(D.parent/'paper-treatment-fit-admission-preparation01-2026-10-04'/rel).read_bytes())
check('producer pins remain unadmitted',new.PRODUCER_SOURCE_PINS is None)
check('no numerical module imported',not any(k in sys.modules for k in ('numpy','torch','scipy')))
(D/'CORRECTION_CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'decision':'source corrections only; independent review required','financial_credit':0},indent=2)+'\n');print(len(checks),'passed')

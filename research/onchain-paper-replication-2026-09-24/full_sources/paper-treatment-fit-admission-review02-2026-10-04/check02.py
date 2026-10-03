"""Different-author exact correction review; stdlib and owned tiny descriptors."""
import ast,copy,hashlib,importlib.util,itertools,json,os,stat
from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'paper-treatment-fit-admission-preparation02-2026-10-04';O=B.parent/'paper-treatment-fit-admission-preparation01-2026-10-04';J=B.parent/'paper-treatment-production-preparation03-2026-10-04/overlay/tradingagents/research/onchain_replication/job.py';REL='overlay/tradingagents/research/onchain_replication/treatment_admission.py';checks=[];witnesses=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def refused(f,label):
 try:f()
 except (ValueError,KeyError,TypeError,AttributeError,StopIteration):checks.append(label);return
 raise AssertionError('not refused: '+label)
def load(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ok(sha(P/'MANIFEST02.json')=='d11820c9ccb8f34e7a482b8c33fd5ad9c5fb34edf51ceb8c268ae98d1fa2a897','candidate manifest pin')
m=json.loads((P/'MANIFEST02.json').read_text());members=m['entries'];ok({e['path'] for e in members}=={str(p.relative_to(P)) for p in P.rglob('*')}-{'MANIFEST02.json'},'manifest complete membership')
for e in members:
 p=P/e['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==e['mode'],'manifest mode')
 if e['type']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==e['bytes'] and sha(p)==e['sha256'],'manifest file hash/extent')
 else:ok(stat.S_ISDIR(s.st_mode),'manifest directory')
delta=json.loads((P/'CORRECTION_INVERSE01.json').read_text());raw=(P/REL).read_text();old=(O/REL).read_text();ok(sha(P/REL)==delta['candidate_sha256'] and sha(O/REL)==delta['baseline_sha256'],'actual source pins');restored=raw
for e in reversed(delta['edits']):ok(restored.count(e['new'])==1,'unique inverse seam');restored=restored.replace(e['new'],e['old'])
ok(restored==old and ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)),'full byte and AST inverse')
for p in sorted(O.rglob('*')):
 if p.is_file() and p.relative_to(O).as_posix()!=REL:ok(p.read_bytes()==(P/p.relative_to(O)).read_bytes(),'unchanged original candidate body '+p.relative_to(O).as_posix())
new=load(P/REL,'review_new');prior=load(O/REL,'review_old');ok(new.PRODUCER_SOURCE_PINS is None,'None producer pins unchanged')
nt=ast.parse(raw);ot=ast.parse(old);allowed={'disposition','_reader','admit_treatment','_reader_cleanup','_owned_metadata_bytes'}
for node in ot.body:
 if isinstance(node,ast.FunctionDef) and node.name not in allowed:
  same=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name==node.name);ok(ast.dump(node)==ast.dump(same),'unchanged function AST '+node.name)
# DA1 exact actual fallback shape, not a hand-improved ledger row.
job=ast.parse(J.read_text());rec=next(n for n in job.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile');assignment=next(n for n in rec.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cells' for t in n.targets));week='2020-01-06T00:00:00Z';cell='treatment-eth-whale-2020-01-06';fallback=eval(compile(ast.Expression(assignment.value.elt.args[1]),'original-observer-fallback','eval'),{'name':cell});pin='0'*64
claim={'experiment_id':'opaque','source':'1'*40,'registration_sha256':pin,'experiment':{'cells':[cell]}};terminal={'status':'failed','experiment_id':'opaque','claim_sha256':pin};plan={'expected_weeks':[week]};args=(claim,terminal,[fallback],pin,pin,plan,week,'whale','ETH')
refused(lambda:prior.disposition(*args),'DA1 RED original actual fallback rejected')
returned=new.disposition(*args,absent=True);ok(returned is fallback and set(returned)=={'id','status','reason'} and returned['status']=='unavailable','DA1 GREEN actual fallback unchanged and unavailable')
refused(lambda:new.disposition(*args),'absent mode required')
for changes in ({'asset':'ETH'},{'week':week},{'extra':True},{'status':'complete'},{'reason':''},{'id':'treatment-btc-whale-2020-01-06'}):
 a=list(copy.deepcopy(args));a[2]=[{**fallback,**changes}];refused(lambda a=a:new.disposition(*a,absent=True),'absent mutation '+str(changes))
for status in ('complete','pending',None):
 a=list(copy.deepcopy(args));a[1]['status']=status;refused(lambda a=a:new.disposition(*a,absent=True),'absent terminal '+str(status))
durable={**fallback,'asset':'ETH','week':week};a=list(args);a[2]=[durable];ok(new.disposition(*a) is durable,'retained unavailable rows still accepted');refused(lambda:new.disposition(*a,absent=True),'retained row cannot impersonate absent')
# Exact actual consumer absence branch, without invoking Run/claim verification.
admit=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='admit_treatment');loop=next(n for n in admit.body if isinstance(n,ast.For));branch=next(n for n in loop.body if isinstance(n,ast.If) and ast.unparse(n.test)=="reference['disposition_input'] is None")
program=compile(ast.Module(body=branch.body,type_ignores=[]),'actual-absence-predicate','exec');path=B/'owned-disposition.json';env={'require':new.require,'row':fallback,'terminal':terminal,'actual_row_path':path}
exec(program,env);checks.append('actual absent path accepted')
path.write_bytes(b'opaque existing row, no authority');refused(lambda:exec(program,env),'existing row refuses absent claim');path.unlink()
path.symlink_to('owned-nonexistent-target')
try:
 ok(os.path.lexists(path) and path.is_symlink() and not path.exists(),'owned dangling symlink is present but exists false')
 exec(program,env);witnesses.append({'id':'DA4','line':234,'path_present':True,'path_is_symlink':True,'path_exists':False,'actual_result':'absence branch accepted a present dangling symlink','impact':'Claimed actual absence is not established for occupied/tampered durable row pathname; distinguish lstat/lexists presence and refuse.'})
finally:path.unlink()
# Cleanup matrix independent of author controls; exact first fatal and secondary identities.
classes=(None,OSError,ValueError,MemoryError,KeyboardInterrupt,SystemExit);fatal=lambda e:isinstance(e,MemoryError) or not isinstance(e,Exception)
for types in itertools.product(classes,repeat=3):
 values=[None if c is None else c('opaque') for c in types];p,a,b=values;calls=[]
 def action(index,error):
  def f():
   calls.append(index)
   if error is not None:raise error
  return f
 errors=[e for e in values if e is not None];expected=next((e for e in errors if fatal(e)),errors[0] if errors else None)
 try:new._reader_cleanup((action(1,a),action(2,b),lambda:calls.append(3)),p)
 except BaseException as e:
  ok(e is expected,'cleanup selected exception identity')
  others=[v for v in errors if v is not expected]
  if others:ok(set(map(id,e.__cause__.exceptions))==set(map(id,others)),'actual secondary exception identities')
 else:ok(expected is None,'error-free cleanup')
 ok(calls==[1,2,3],'all cleanup callbacks attempted')
# Exact new helper AST uses injected os facade only at named fault seams; real owned fd.
file=B/'opaque-reader.txt';file.write_bytes(b'owned metadata only\n');source=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='_owned_metadata_bytes');source=copy.deepcopy(source);source.body=[n for n in source.body if not isinstance(n,ast.Import)]
class API:
 O_RDONLY=os.O_RDONLY;O_NOFOLLOW=os.O_NOFOLLOW
 def __init__(self,stage=None,error=None,close_error=None):self.stage=stage;self.error=error;self.close_error=close_error;self.created=[];self.calls=[]
 def open(self,*a):
  self.calls.append('open')
  if self.stage=='open':raise self.error
  fd=os.open(*a);self.created.append(fd);return fd
 def fdopen(self,fd,mode):
  self.calls.append('fdopen')
  if self.stage=='fdopen':raise self.error
  parent=self
  class Stream:
   def __init__(self):self.real=os.fdopen(fd,mode)
   def fileno(self):return self.real.fileno()
   def read(self,n):
    parent.calls.append('read')
    if parent.stage=='read':raise parent.error
    return self.real.read(n)
   def close(self):
    parent.calls.append('stream-close');self.real.close()
    if parent.close_error is not None:raise parent.close_error
  return Stream()
 def fstat(self,fd):
  self.calls.append('fstat')
  if self.stage=='fstat':raise self.error
  return os.fstat(fd)
 def close(self,fd):
  self.calls.append('raw-close');os.close(fd)
  if self.close_error is not None:raise self.close_error
for stage in ('open','fdopen','fstat','read',None):
 for primary_type,close_type in itertools.product(classes,repeat=2):
  if (stage is None)!=(primary_type is None):continue
  error=None if primary_type is None else primary_type('primary');close_error=None if close_type is None else close_type('close');api=API(stage,error,close_error)
  ns={'os':api,'stat':stat,'require':new.require,'LIMIT':new.LIMIT,'_reader_cleanup':new._reader_cleanup};exec(compile(ast.Module(body=[source],type_ignores=[]),'exact-owned-helper','exec'),ns)
  errors=([error] if error is not None else [])+([close_error] if close_error is not None and stage!='open' else []);expected=next((e for e in errors if fatal(e)),errors[0] if errors else None)
  try:value=ns['_owned_metadata_bytes'](file)
  except BaseException as e:ok(e is expected,'owned IO first fatal identity '+str(stage))
  else:ok(expected is None and value==file.read_bytes(),'owned IO success')
  ok(api.calls.count('raw-close')==(1 if stage=='fdopen' else 0),'raw descriptor ownership transfer '+str(stage))
  ok(api.calls.count('stream-close')==(0 if stage in ('open','fdopen') else 1),'stream closes exactly once '+str(stage))
  for fd in api.created:
   try:os.fstat(fd)
   except OSError:checks.append('actual descriptor closed '+str(stage))
   else:os.close(fd);raise AssertionError('leaked owned descriptor')
# Preserve first fatal even if attaching evidence raises.
class RefuseCause(KeyboardInterrupt):
 def __setattr__(self,name,value):
  if name=='__cause__':raise SystemExit('attachment')
  super().__setattr__(name,value)
original=RefuseCause('primary');calls=[]
def later():calls.append(1);raise OSError('secondary')
try:new._reader_cleanup((later,lambda:calls.append(2)),original)
except BaseException as e:ok(e is original and calls==[1,2],'attachment failure cannot replace primary')
# Native/runtime/read paths are not executed; source gates inspected exactly.
ok("absent=reference['disposition_input'] is None" in raw,'caller derives absence from actual descriptor sentinel')
ok("raise ValueError('UNADMITTED: exact historical cohort" in raw,'fund policy refusal retained')
(B/'candidate-source.py').write_bytes((P/REL).read_bytes())
(B/'CHECKS02.json').write_text(json.dumps({'status':'passed-controls-with-one-new-absence-witness','checks':len(checks),'labels':checks,'witnesses':witnesses,'candidate_sha256':sha(P/REL),'scope':'Independent exact source/metadata/owned descriptor controls; no actual research claims, Run, numerical libraries or native processes'},sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'witnesses':witnesses}))

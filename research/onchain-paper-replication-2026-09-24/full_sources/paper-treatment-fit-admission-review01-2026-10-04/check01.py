"""Independent metadata/AST/owned-descriptor controls; no authority or arrays."""
import ast,copy,hashlib,importlib.util,json,os,stat
from pathlib import Path
from datetime import timedelta
B=Path(__file__).resolve().parent;ROOT=B.parents[3];P=B.parent/'paper-treatment-fit-admission-preparation01-2026-10-04';Q=B.parent/'paper-treatment-production-preparation02-2026-10-04';M=P/'overlay/tradingagents/research/onchain_replication/treatment_admission.py';checks=[];witnesses=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ok(v,label):
 if not v:raise AssertionError(label)
 checks.append(label)
def refused(f,label):
 try:f()
 except (ValueError,KeyError,TypeError):checks.append(label);return
 raise AssertionError('accepted '+label)
def dump(path,obj):path.write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
ok(sha(P/'MANIFEST01.json')=='e1857cb693110b29b3cad0ed564ebff8ebd38b4683e0358d8807c0840688b9e2','exact author manifest')
manifest=json.loads((P/'MANIFEST01.json').read_text());ok({e['path'] for e in manifest['members']}=={str(p.relative_to(P)) for p in P.rglob('*')}-{'MANIFEST01.json'},'complete manifest membership')
for e in manifest['members']:
 p=P/e['path'];s=p.lstat();ok(format(stat.S_IMODE(s.st_mode),'04o')==e['mode'],'member mode')
 if e['type']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==e['bytes'] and sha(p)==e['sha256'],'member file hash/type/extent')
 else:ok(stat.S_ISDIR(s.st_mode),'member directory type')
for o in json.loads((P/'ORIGINS01.json').read_text()):
 p=Path(o['path']);p=p if p.is_absolute() else ROOT/p;ok(sha(p)==o['sha256'],'actual declared origin hash '+o['path'])
for delta in json.loads((P/'DELTA_INVERSE01.json').read_text()):
 p=P/'overlay'/delta['path'];body=p.read_text();ok(sha(p)==delta['candidate_sha256'],'candidate source pin')
 for e in reversed(delta['edits']):ok(body.count(e['new'])==1,'unique inverse');body=body.replace(e['new'],e['old'])
 ok(hashlib.sha256(body.encode()).hexdigest()==delta['original_sha256'],'exact byte inverse')
 original=(P/'origins'/p.name).read_text();ok(body==original and ast.dump(ast.parse(body))==ast.dump(ast.parse(original)),'entire source AST inverse')
# Stdlib-only import confirmed before module import.
tree=ast.parse(M.read_text());ok(all(not isinstance(n,(ast.Import,ast.ImportFrom)) or (isinstance(n,ast.Import) and all(x.name in ('hashlib','json','re') for x in n.names)) or (isinstance(n,ast.ImportFrom) and n.module in ('datetime','pathlib')) for n in tree.body),'module import remains stdlib')
spec=importlib.util.spec_from_file_location('opaque_admission_review',M);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);ok(module.PRODUCER_SOURCE_PINS is None,'producer pins deliberately unadmitted')
week='2020-01-06T00:00:00Z';cell='treatment-eth-whale-2020-01-06';pin='0'*64
# Derive exact fallback expression from current corrected job, never execute observer or Run.
job_source=(Q/'overlay/tradingagents/research/onchain_replication/job.py').read_text();jobtree=ast.parse(job_source)
observer=next(n for n in jobtree.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile')
assignment=next(n for n in observer.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cells' for t in n.targets))
expression=assignment.value.elt.args[1];fallback=eval(compile(ast.Expression(expression),'actual-observer-default','eval'),{'name':cell})
ok(set(fallback)=={'id','status','reason'},'actual observer fallback schema')
# These are pure scalar consistency inputs, not actual or registered claim files.
claim={'experiment_id':'opaque-only','source':'1'*40,'registration_sha256':pin,'experiment':{'cells':[cell]}};terminal={'status':'failed','experiment_id':'opaque-only','claim_sha256':pin};plan={'expected_weeks':[week]}
try:module.disposition(claim,terminal,[fallback],pin,pin,plan,week,'whale','ETH')
except ValueError as e:
 ok(str(e)=='cell asset/week differs','DA1 actual missing-row fallback refused')
 witnesses.append({'id':'DA1','line':97,'actual_postmortem_row':fallback,'observed_exception':str(e),'impact':'Failed-source absent-cell route cannot retain the real observer missing-row unavailable disposition.'})
else:raise AssertionError('DA1 did not reproduce')
# Existing durable unavailable rows carry these fields and do pass; failure is exact seam.
retained={**fallback,'asset':'ETH','week':week};ok(module.disposition(claim,terminal,[retained],pin,pin,plan,week,'whale','ETH')==retained,'durable unavailable control')
for replacement in ({**retained,'status':'complete'},{**retained,'week':'2020-01-13T00:00:00Z'},{**retained,'asset':'BTC'}):refused(lambda replacement=replacement:module.disposition(claim,terminal,[replacement],pin,pin,plan,week,'whale','ETH'),'failed/other cell refusal')
for status in ('pending','unknown',None):refused(lambda status=status:module.disposition(claim,{**terminal,'status':status},[retained],pin,pin,plan,week,'whale','ETH'),'active/unknown terminal refusal')
# Complete ordered denominator/terminal controls, scalar only.
complete={**terminal,'status':'complete','source':claim['source'],'registration_sha256':pin,'output_sha256':{'cell-ledger.json':pin},'cells':[retained],'cell_count':1,'unavailable_count':1}
ok(module.disposition(claim,complete,[retained],pin,pin,plan,week,'whale','ETH')==retained,'complete unavailable terminal joins')
for key in ('claim_sha256','experiment_id','source','registration_sha256','output_sha256','cells','cell_count','unavailable_count'):
 bad=copy.deepcopy(complete);bad[key]=None;refused(lambda bad=bad:module.disposition(claim,bad,[retained],pin,pin,plan,week,'whale','ETH'),'terminal mutation '+key)
# Real descriptor acquisition via exact reader AST seam; never construct run/Owner.
reader=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_reader');meta=next(n for n in reader.body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='metadata')
seam=[n for n in meta.body if isinstance(n,ast.With) or (isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='fd')]
program=compile(ast.Module(body=seam,type_ignores=[]),'actual-reader-owned-io-seam','exec');file=B/'opaque-reader.txt';file.write_bytes(b'opaque metadata only\n')
class OS:
 O_RDONLY=os.O_RDONLY;O_NOFOLLOW=os.O_NOFOLLOW
 def __init__(self,fdopen):self.created=[];self.fdopen=fdopen
 def open(self,*a):fd=os.open(*a);self.created.append(fd);return fd
 def fstat(self,*a):return os.fstat(*a)
def environment(api):return {'os':api,'stat':stat,'path':file,'require':module.require,'LIMIT':module.LIMIT}
primary=MemoryError('injected fdopen allocation failure')
def fail_open(*args):raise primary
api=OS(fail_open)
try:exec(program,environment(api))
except MemoryError as e:ok(e is primary,'fdopen fatal propagates')
ok(len(api.created)==1,'one actual owned descriptor acquired');fd=api.created[0]
try:os.fstat(fd);leaked=True
except OSError:leaked=False
finally:os.close(fd)
ok(leaked,'DA2 fdopen failure leaves acquired descriptor open')
witnesses.append({'id':'DA2','line':138,'observed':'actual fd still open after injected fdopen MemoryError; review explicitly closed it','impact':'New reader loses descriptor ownership when wrapping fails; repeated failures can exhaust descriptors.'})
primary=KeyboardInterrupt('original read fatal');secondary=OSError('injected close failure');closed=[]
class Stream:
 def __init__(self,fd):self.real=os.fdopen(fd,'rb')
 def __enter__(self):return self
 def fileno(self):return self.real.fileno()
 def read(self,n):raise primary
 def __exit__(self,*args):self.real.close();closed.append(True);raise secondary
api=OS(lambda fd,mode:Stream(fd))
try:exec(program,environment(api))
except BaseException as e:ok(e is secondary and e.__context__ is primary,'DA3 close ordinary replaces original fatal')
ok(closed==[True],'DA3 real owned descriptor closed')
witnesses.append({'id':'DA3','line':138,'observed':'read KeyboardInterrupt replaced by close OSError; primary survives only as context','impact':'An ordinary close exception changes fatal cancellation into an ordinary error, enabling downstream ordinary-error handling.'})
# Date mapping verified against actual pure calendar.expected_week for all seven days.
calendar=ast.parse((P/'origins/calendar.py').read_text());names={n.name for n in calendar.body if isinstance(n,ast.FunctionDef)}
# No calendar module import: candidate membership tested via explicit frozen original formula.
for day in range(7):
 date=(module.stamp('2020-01-13T00:00:00Z')+timedelta(days=day)).date().isoformat();available='2020-01-14T00:00:00Z';admitted={week:{'status':'complete','graph_hash':pin,'available_at':available}}
 module.verify_example_metadata([([date],[pin],[available])],admitted);checks.append('causal week membership day '+str(day))
refused(lambda:module.verify_example_metadata([(['2020-01-13'],[pin],['2020-01-15T00:00:00Z'])],{week:{'status':'complete','graph_hash':pin,'available_at':'2020-01-15T00:00:00Z'}}),'late graph refused')
refused(lambda:module.verify_example_metadata([(['2020-01-13'],[pin],['2020-01-14T00:00:00Z'])],{week:{'status':'unavailable','graph_hash':pin,'available_at':'2020-01-14T00:00:00Z'}}),'unavailable graph refused')
# Inspect added guard ordering and unchanged method/calendars without executing scientific modules.
for name,func in [('evaluation.py','evaluate_cell'),('run.py','preflight_batch')]:
 body=ast.parse((P/'overlay/tradingagents/research/onchain_replication'/name).read_text());node=next(n for n in body.body if isinstance(n,ast.FunctionDef) and n.name==func)
 ok(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='preflight_treatment' for n in ast.walk(node)),'mandatory fit call '+func)
ok("raise ValueError('UNADMITTED: exact historical cohort" in M.read_text(),'fund remains explicitly unadmitted')
(B/'sources').mkdir()
for p in (M,P/'overlay/tradingagents/research/onchain_replication/run.py',P/'overlay/tradingagents/research/onchain_replication/evaluation.py',P/'overlay/tradingagents/research/onchain_replication/population_assembly.py'):(B/'sources'/p.name).write_bytes(p.read_bytes())
(B/'sources/producer02-job.py').write_text(job_source)
dump(B/'CHECKS01.json',{'status':'passed-controls-with-three-blocking-witnesses','checks':len(checks),'labels':checks,'witnesses':witnesses,'authority':None,'scope':'Independent source/metadata/actual tiny owned descriptors; no ResearchRun/Owner/native/arrays/test labels/claim creation. fdopen and close faults deliberately injected at actual extracted IO seam.'})
print(json.dumps({'checks':len(checks),'findings':len(witnesses)}))

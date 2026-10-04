from pathlib import Path
import ast,hashlib,importlib.util,json,os,stat,sys
P=Path(__file__).absolute().parent;B=P.parent;A=B/'financial-wrapper-compatibility-operational-delta-flat-successor03-2026-10-04'
s=importlib.util.spec_from_file_location('flat_review_extra',P/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M);R=M.R;checks=[]
def ck(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
old=(P/'ORIGINAL_restore01.py').read_text();new=(P/'restore01.py').read_text();inverse=json.loads((A/'SOURCE_INVERSE01.json').read_bytes());restored=new
for e in reversed(inverse['edits']):
 ck('literal span '+str(e['new_start']),restored[e['new_start']:e['new_end']]==e['new']);restored=restored[:e['new_start']]+e['old']+restored[e['new_end']:]
ck('full literal inverse',restored==old)
ck('full AST inverse',ast.dump(ast.parse(restored))==ast.dump(ast.parse(old)))
o={n.name:n for n in ast.parse(old).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};n={n.name:n for n in ast.parse(new).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
changes=[k for k in o if ast.dump(o[k])!=ast.dump(n[k])];ck('exact five original functions changed',sorted(changes)==sorted(['authenticate_selected','load_capture','load_failed_capture','run','verify_flat']));ck('one added class',set(n)-set(o)=={'VerifiedCohort'})
for k in set(o)-set(changes):ck('unchanged AST:'+k,ast.dump(o[k])==ast.dump(n[k]))
O=P/'owned02';O.mkdir(mode=0o700)
for kind in ('prerequisite-bytes','prerequisite-mode','receiver-mode','ancestor-mode','extra','iterator-close'):
 root=O/kind;root.mkdir(mode=0o700);d=root/'selected';d.mkdir(mode=0o700);a=d/'a';a.write_bytes(b'a');a.chmod(0o600);p=root/'opaque-prerequisite';p.write_bytes(b'not a receipt');p.chmod(0o600)
 c=M.VerifiedCohort();c.read(root,p.name);c.tree(d,{'a'});c.read(d,'a');c.check();original=M.os.scandir;fired=False
 if kind=='iterator-close':
  class It:
   def __init__(self,path):self.raw=original(path)
   def __iter__(self):return self
   def __next__(self):return next(self.raw)
   def close(self):
    global fired
    self.raw.close()
    if not fired:fired=True;p.write_bytes(b'changed prerequisite')
  M.os.scandir=It
 elif kind=='prerequisite-bytes':p.write_bytes(b'changed prerequisite')
 elif kind=='prerequisite-mode':p.chmod(0o644)
 elif kind=='receiver-mode':root.chmod(0o755)
 elif kind=='ancestor-mode':d.chmod(0o755)
 else:(d/'extra').write_bytes(b'foreign')
 error=None
 try:c.check()
 except ValueError as e:error=e
 finally:M.os.scandir=original
 ck('terminal refusal:'+kind,error is not None)
# actual last boundary mutation, after all body IO, must not be trusted.
bundle=B/'financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04';cap,man=M.load_failed_capture(bundle);root=O/'last-boundary';root.mkdir(mode=0o700);dest=root/'flat';dest.mkdir(mode=0o700);result=R.restore(bundle/'failed-remote02.tar.gz',cap['archive'],man,dest);metadata=json.loads((dest/result['metadata_file']).read_bytes());first=dest/next(iter(metadata['flat_members'].values()));calls=0

def boundary():
 global calls
 M.W.census(root);calls+=1
 if calls==2:
  b=first.read_bytes();first.write_bytes(bytes([b[0]^1])+b[1:])
try:M.verify_flat(dest,result,cap,man,boundary)
except ValueError:ck('afterlast-original-boundary-refusal',calls==2)
else:raise AssertionError('last boundary mutation accepted')
# Full first scope survives an actual second-scope write fatal and late close fatal.
root=O/'partial';root.mkdir(mode=0o700);oper=B/'financial-wrapper-compatibility-operational-delta-capture02-2026-10-04';oc,om=M.load_capture(oper);r=M.restore_delta(oper,oc,om,root,lambda:None)
firstmode=R.scan(root/M.OUTPUT);realwrite=R.os.write;realclose=R.os.close;writes=0;closed=[];primary=MemoryError('actual write control');secondary=SystemExit('actual close control');failedfd=None

def write(fd,b):
 global writes,failedfd
 writes+=1
 if writes==3:failedfd=fd;raise primary
 return realwrite(fd,b)
def close(fd):
 realclose(fd);closed.append(fd)
 if fd==failedfd:raise secondary
R.os.write=write;R.os.close=close;error=None
try:M.restore_failed_delta(bundle,cap,man,root,lambda:None)
except BaseException as e:error=e
finally:R.os.write=realwrite;R.os.close=realclose
ck('partial firstfatal actual write/close',error is primary)
ck('completed-first-retained',R.scan(root/M.OUTPUT)==firstmode)
ck('failed-second-partial-retained',len(list((root/M.FAILED_OUTPUT).iterdir()))>0)
for fd in set(closed):
 try:os.fstat(fd)
 except OSError:ck('actual fd closed:'+str(fd),True)
 else:raise AssertionError('open fd')
# Read-only structural publication boundary guarantee, no actual run/receipt.
run=n['run'];calls=[ast.unparse(x) for x in ast.walk(run) if isinstance(x,ast.Call)];text=ast.unparse(run)
ck('cohort rejoin before publication',text.index('cohort.check()')<text.index("R.put(HERE / 'FLAT_RECOVERY01.json'"))
ck('cohort rejoin after final sidecar boundary',text.rindex('cohort.check()')>text.index("R.put(HERE / 'FLAT_POSTWRITE_OBSERVATION01.json'"))
ck('no public successful entry',not (P/'FLAT_RECOVERY01.json').exists())
ck('noNUM',not any(x.split('.')[0] in ('numpy','torch','scipy','pandas') for x in sys.modules))
(P/'READBACK02.json').write_text(json.dumps({'checks':len(checks),'names':checks,'public_run_executed':False,'generated_receipt_fabricated':False,'sidecar_scope_qualification':'Final cohort check occurs after sidecar boundary; sidecar itself is not read into the byte cohort. Remote receipt, selection, selected prerequisites, restored metadata/bodies and final recovery JSON are covered. Root terminal and sidecar actual artifact acceptance remain independent.'},indent=2)+'\n');print(json.dumps({'checks':len(checks),'status':'PASS_SOURCE_CONTROLS'}))

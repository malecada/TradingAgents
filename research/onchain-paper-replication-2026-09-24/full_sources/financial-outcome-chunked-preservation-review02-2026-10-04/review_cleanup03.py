import ast,copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
D=Path(__file__).resolve().parent;S=D/'authenticated-source';sys.path.insert(0,str(S));spec=importlib.util.spec_from_file_location('closure_candidate',S/'chunk_archive01.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
T=D/'owned-cleanup03';T.mkdir();checks=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def census():return set(os.listdir('/proc/self/fd'))
def refuse(n,f):
 before=census()
 try:f()
 except (ValueError,OSError):check(n,True)
 else:raise AssertionError(n)
 check(n+' descriptor census',before==census())
p=T/'parent';p.mkdir();(p/'exists').mkdir();refuse('real mkdir EEXIST cleanup',lambda:N.fresh(p,p/'exists'));(p/'file').write_bytes(b'opaque');refuse('real existing regular child cleanup',lambda:N.fresh(p,p/'file'))
(p/'link').symlink_to(p/'exists',target_is_directory=True);refuse('real existing symlink child cleanup',lambda:N.fresh(p,p/'link'))
# Existing regular output refuses at actual O_EXCL; no instrumentation.
b=N.Bounds();b.anchors[p]=N.anchor(p);before=(p/'file').read_bytes();refuse('actual output exclusive-open failure',lambda:N._write(p,'file',b'new',b));check('existing bytes preserved',(p/'file').read_bytes()==before)
# Instrument only source operation scheduling: create actual first body, then
# raise the original KeyboardInterrupt before the following list bookkeeping.
fn=copy.deepcopy(next(n for n in ast.parse((S/'chunk_archive01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='restore'))
class Insert(ast.NodeTransformer):
 def visit_Expr(self,node):
  if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='_write' and isinstance(node.value.args[1],ast.Name) and node.value.args[1].id=='filename':
   return [node,ast.Expr(value=ast.Call(func=ast.Name(id='stop_after_body',ctx=ast.Load()),args=[],keywords=[]))]
  return node
fn=Insert().visit(fn);ns=dict(vars(N));primary=KeyboardInterrupt('independent partial restore scheduling')
def stop():raise primary
ns['stop_after_body']=stop;exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<exact-restore-boundary>','exec'),ns)
archive=D/'owned02/small-archive';pin=hashlib.sha256((archive/'index.json').read_bytes()).hexdigest();dest=T/'partial-flat';before=census();observed=None
try:ns['restore'](archive,pin,dest)
except BaseException as e:observed=e
check('original partial restore fatal retained',observed is primary);check('partial restore fd census',before==census());check('actual completed body retained',(dest/'body-00000000.bin').read_bytes()==b'opaque');check('failure receipt only',(dest/'restore-failure.json').is_file() and not (dest/'recovery.json').exists() and not (dest/'index.json').exists());refuse('partial flat refuses complete verification',lambda:N.verify_flat(dest,pin))
rr=json.loads((dest/'restore-failure.json').read_bytes());check('failure explicitly preserves partial qualification',rr['status']=='failed' and rr['error_type']=='KeyboardInterrupt' and rr['completed_artifacts']==[])
(D/'CLEANUP_CHECKS03.json').write_text(json.dumps({'count':len(checks),'checks':checks,'qualification':'actual owned descriptor failures and explicit restore boundary scheduling; partial unlisted body is retained, not represented as a complete artifact or successful restoration'},indent=2)+'\n');print(len(checks),'passed')

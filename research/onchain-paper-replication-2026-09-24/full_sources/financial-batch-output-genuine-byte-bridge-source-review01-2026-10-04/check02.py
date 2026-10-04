import ast,hashlib,json,os,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation01-2026-10-04';sys.path.insert(0,str(P))
import byte_bridge01 as B,recovery04 as R,owned_io as IO
out=[]
def refuse(fn,label):
 try:fn()
 except BaseException as e:out.append({'case':label,'refusal':type(e).__name__});return e
 raise AssertionError('accepted '+label)
graphs={'a'*64:2,'b'*64:3};g={'schema_version':1,'kind':'two-imported-target-local-codec-v1','job_input':'execution_job','job_sha256':'c'*64,'role':'score-batches','targets':graphs,'max_logical_bytes':B.LIMIT,'max_allocated_bytes':B.LIMIT,'scientific_publication':False,'transport':False,'retirement':False}
reserve=B.validate_grant(g,'score-batches',graphs,'c'*64);out.append({'case':'valid declared utility grant only','reserve':reserve,'genuine_registration':False})
for k in g:
 bad=dict(g);del bad[k];refuse(lambda:B.validate_grant(bad,'score-batches',graphs,'c'*64),'missing '+k)
for k,vals in [('schema_version',[True,1.0,2]),('max_logical_bytes',[True,float(B.LIMIT),reserve-1,B.LIMIT+1]),('max_allocated_bytes',[0,reserve-1,B.LIMIT+1]),('scientific_publication',[0,True]),('transport',[0,True]),('retirement',[0,True]),('targets',[{}, {'a'*64:2}, {'a'*64:True,'b'*64:3}]),('job_sha256',['d'*64,None]),('role',['mcm-output',None])]:
 for v in vals:
  bad=dict(g);bad[k]=v;refuse(lambda:B.validate_grant(bad,'score-batches',graphs,'c'*64),'bad '+k+' '+repr(v))
root=D/'fatal-io';root.mkdir(mode=0o700)
for i,(pt,ct) in enumerate([(MemoryError,RuntimeError),(SystemExit,RuntimeError),(KeyboardInterrupt,MemoryError),(GeneratorExit,SystemExit),(RuntimeError,MemoryError),(RuntimeError,SystemExit),(ValueError,ValueError),(MemoryError,SystemExit),(BaseException,KeyboardInterrupt)]):
 primary=pt('original write');later=ct('after real close');closed=[];realwrite=os.write;realclose=os.close;path=root/('case-%02d'%i)
 def badwrite(*args):raise primary
 def close(fd):
  realclose(fd);closed.append(fd)
  if len(closed)==1:raise later
 os.write=badwrite;os.close=close
 try:
  try:B._write(R,IO,path,b'opaque')
  except BaseException as e:selected=e
  else:raise AssertionError('unexpected write success')
 finally:os.write=realwrite;os.close=realclose
 assert len(closed)==2 and len(set(closed))==2 and path.exists() and path.stat().st_size==0
 for fd in closed:
  try:os.fstat(fd)
  except OSError:pass
  else:raise AssertionError('descriptor retained')
 if IO._fatal(primary):assert selected is primary
 elif IO._fatal(later):assert selected is later
 else:assert isinstance(selected,IO.CleanupFailure)
 out.append({'case':'actual fatal-close pair '+str(i),'primary':pt.__name__,'later':ct.__name__,'selected':type(selected).__name__,'both_descriptors_closed':True,'empty_partial_retained':True})
# Actual original context-manager misuse RED, original draft unchanged.
ns={'__name__':'independent_old_writer'};tree=ast.parse((P/'byte_bridge01.draft01.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_write')
ns.update(os=os,require=B.require);exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual_original_writer_AST','exec'),ns)
refuse(lambda:ns['_write'](R,IO,root/'old-red',b'x'),'original context-manager RED')
B._write(R,IO,root/'new-green',b'x');assert (root/'new-green').read_bytes()==b'x';out.append({'case':'candidate actual context-manager GREEN'})
with (D/'CHECKS02.json').open('x')as f:json.dump({'count':len(out),'checks':out},f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'checks':len(out),'actual_io_pairs':9}))

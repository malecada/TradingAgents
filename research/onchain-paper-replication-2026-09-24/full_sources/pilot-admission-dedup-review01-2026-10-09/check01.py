"""Independent exact-source predicate/trace tests using tiny protocol fixtures, not Git authority."""
import ast,hashlib,json,re,resource,os,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.nice(10)
H=Path(__file__).resolve().parent;F=H.parent;ROOT=H.parents[3];old=ROOT/'tradingagents/research/admission.py';new=F/'pilot-admission-dedup-source01-2026-10-09/admission.py'
a=old.read_text();b=new.read_text()
before='''        raw = _source_git_batch(root, [oid for oid, _ in extents], bodies=True)
        recorded = _source_batch_parse(raw, len(extents), extents=extents)
'''
after='''        unique = list(dict.fromkeys(extents))
        raw = _source_git_batch(root, [oid for oid, _ in unique], bodies=True)
        returned = _source_batch_parse(raw, len(unique), extents=unique)
        by_extent = dict(zip(unique, returned, strict=True))
        recorded = [by_extent[extent] for extent in extents]
'''
assert b.count(after)==1 and b.replace(after,before)==a
bodies={b'a'*40:b'x',b'b'*40:b'yy'};pins={k:hashlib.sha256(v).hexdigest() for k,v in {'first':b'x','second':b'yy','third':b'x'}.items()}
def run(text,mode=None):
 trace=[];requests=[];local={'first':b'x','second':b'yy','third':b'x'}
 class File:
  def __init__(self,name):self.name=name
  def read_bytes(self):trace.append(('read',self.name));return local[self.name]
 def digest(body):trace.append(('digest',body.hex()));return hashlib.sha256(body).hexdigest()
 def batch(root,req,*,bodies=False):
  requests.append((bodies,len(req)))
  ext=[]
  for i,r in enumerate(req):
   oid=r if bodies else (b'b'*40 if r.endswith(b':second') else b'a'*40)
   raw=globals()['bodies'][oid];size=len(raw)
   if mode=='conflict' and not bodies and i==1:size+=1
   ext.append(oid+b' blob '+str(size).encode()+b'\n'+(raw+b'\n' if bodies else b''))
  out=b''.join(ext)
  if bodies and mode=='suffix':out+=b'bad'
  if bodies and mode=='mutate':local['first']=b'z'
  return out
 ns=dict(Path=Path,re=re,digest=digest,local_path=lambda root,name:File(name),_source_git_batch=batch,_SOURCE_BATCH_FILES=128,_SOURCE_BATCH_BYTES=8*1024**2)
 tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_source_files','_source_batch_parse')];exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual functions>','exec'),ns)
 def call():
  try:ns['_source_files'](None,'current','design',pins);return 'PASS'
  except ValueError as e:return str(e)
 outcome=call()
 if mode=='twice':local['first']=b'z';outcome=(outcome,call())
 return outcome,trace,requests
results=[]
for mode in (None,'conflict','suffix','mutate','twice'):
 x=run(a,mode);y=run(b,mode);assert x[:2]==y[:2],(mode,x,y)
 if mode is None:assert x[2]==[(False,6),(True,6)] and y[2]==[(False,6),(True,2)]
 if mode=='conflict':assert y[0]=='committed source/registration cannot be verified'
 if mode=='twice':assert y[0]==('PASS','committed source differs: first') and len(y[2])==4
 results.append(dict(mode=mode,outcome=y[0],equal_original_validation_trace=True,baseline_requests=x[2],candidate_requests=y[2]))
result=dict(status='PASS',literal_inverse=True,candidate_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),baseline_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),cases=results,qualification='Tiny synthetic Git protocol responses; actual source functions/parser, no claim of genuine Git authority or timing.')
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

"""Exercise actual harness exception/finally AST without numeric imports."""
import ast,copy,hashlib,json,types
from pathlib import Path
D=Path(__file__).resolve().parent
old=D.parent/'pilot34-native-owner-qualification01-2026-10-11/qualify01.py'
new=D/'qualify02.py'
def main_try(p):
 tree=ast.parse(p.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 return next(n for n in main.body if isinstance(n,ast.Try))
a,b=main_try(old),main_try(new)
assert ast.dump(ast.Module(body=a.body,type_ignores=[]))==ast.dump(ast.Module(body=b.body,type_ignores=[]))
class BadString(Exception):
 def __str__(self):raise MemoryError('format')
class Handle:
 def __init__(self,ns):self.ns=ns
 def __enter__(self):return self
 def __exit__(self,*args):return False
 def write(self,body):
  if self.ns['write_error']:raise self.ns['write_error']
  self.ns['published'].append(self.ns['result'])
 def flush(self):pass
 def fileno(self):return 0
class PathStub:
 def __init__(self,ns):self.ns=ns
 def open(self,mode):assert mode=='xb';return Handle(self.ns)
class CloseStub:
 def __init__(self,error):self.error=error
 def close(self):
  if self.error:raise self.error

def execute(node,primary=None,cleanup=None,write=None,encoding=None):
 current=copy.deepcopy(node);current.body=ast.parse('raise injected' if primary else 'pass').body
 module=ast.fix_missing_locations(ast.Module(body=[current],type_ignores=[]))
 ns={'injected':primary,'failure':None,'failed':False,'primary':None,'secondary':[],
     'lease':CloseStub(cleanup),'owner':None,'checks':[],'phases':[],'started':0.,
     'published':[],'write_error':write,'time':types.SimpleNamespace(monotonic=lambda:1.),
     'resource':types.SimpleNamespace(RUSAGE_SELF=0,getrusage=lambda _:types.SimpleNamespace(ru_maxrss=123)),
     'os':types.SimpleNamespace(fsync=lambda _:None)}
 ns['result_path']=PathStub(ns)
 def encode(value):
  if encoding:raise encoding
  return b'opaque mock reporting output'
 ns['encoded']=encode
 raised=None
 try:exec(compile(module,'extracted-existing-handlers','exec'),ns)
 except BaseException as error:raised=error
 return ns,raised
checks=[]
error=BadString('original');ns,raised=execute(a,error)
assert ns['published'][0]['status']=='PASS_FINITE_SYNTHETIC' and isinstance(raised,MemoryError)
checks.append('original01 false PASS reproduced by actual extracted handlers')
for title,error,cleanup,write,encoding in (
 ('primary bad str',BadString('original'),None,None,None),
 ('primary plus cleanup bad str',ValueError('original'),BadString('cleanup'),None,None),
 ('primary plus output failure',ValueError('original'),None,OSError('write'),None),
 ('primary plus encoding failure',ValueError('original'),None,None,MemoryError('encode')),
 ('cleanup first formatting failure',None,BadString('cleanup'),None,None),
 ('publication first failure',None,None,OSError('write'),None)):
 ns,raised=execute(b,error,cleanup,write,encoding)
 expected=error or cleanup or write or encoding
 assert raised is expected and ns['failed'] is True,title
 if ns['published']:assert all(v['status']=='FAILED' for v in ns['published']),title
 checks.append(title)
ns,raised=execute(b)
assert raised is None and not ns['failed'] and ns['published'][0]['status']=='PASS_FINITE_SYNTHETIC'
checks.append('intact success publishes PASS')
checks.append('all original numerical try-body AST unchanged')
command=json.loads((D/'COMMAND02.json').read_text())
assert command['argv'][2]==str(new) and command['script']['sha256']==hashlib.sha256(new.read_bytes()).hexdigest()
assert command['outer_timeout_seconds']==60 and command['maximum_attempts']==1 and command['actual_native_execution'] is False
assert not (D/'attempt01').exists()
checks.extend(['exact repaired script command join','unchanged finite outer bound and one attempt','no native attempt namespace'])
value={'status':'SOURCE_ONLY_REGRESSION_PASS','checks':checks,'actual_native_execution':False,'numeric_body_unchanged':True}
with (D/'SOURCE_CHECK02.json').open('x') as stream:json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')
print(json.dumps({'checks':len(checks),'status':value['status']}))

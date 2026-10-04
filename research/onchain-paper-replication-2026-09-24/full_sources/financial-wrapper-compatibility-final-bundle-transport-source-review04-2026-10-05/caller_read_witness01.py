from pathlib import Path
import ast,hashlib,json,os,stat
D=Path(__file__).resolve().parent;S=D.parent/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05/caller01.py'
t=ast.parse(S.read_bytes());nodes=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ('sig','read')];env={'stat':stat,'hashlib':hashlib,'FILE':4194304,'pins':{}};exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-caller-read','exec'),env)
p=D/'opaque-caller-read';p.write_bytes(b'opaque');raw=p.read_bytes();real_open=Path.open;primary=KeyboardInterrupt('original read fatal');secondary=ValueError('later real close ordinary');closed=[]
class Owned:
 def __init__(self):self.fd=os.open(p,os.O_RDONLY)
 def __enter__(self):return self
 def read(self,*a,**k):raise primary
 def __exit__(self,*a):os.close(self.fd);closed.append(self.fd);raise secondary
Path.open=lambda self,*a,**k:Owned() if self==p else real_open(self,*a,**k)
actual=None
try:env['read'](p,hashlib.sha256(raw).hexdigest())
except BaseException as e:actual=e
finally:Path.open=real_open
assert actual is secondary and actual is not primary and len(closed)==1
try:os.fstat(closed[0])
except OSError:pass
else:raise AssertionError('descriptor remains open')
out={'finding':'CALLER04_READ_FATAL_MASKED_BY_CLOSE','caller_sha256':hashlib.sha256(S.read_bytes()).hexdigest(),'primary':'KeyboardInterrupt','observed':'ValueError','original_fatal_preserved':False,'actual_owned_fd_closed_once':True,'exact_read_and_sig_AST':True,'public_main_invoked':False,'child_started':False};(D/'CALLER_READ_WITNESS01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

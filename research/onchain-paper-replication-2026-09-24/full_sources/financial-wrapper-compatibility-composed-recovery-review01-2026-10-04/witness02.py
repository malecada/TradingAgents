from pathlib import Path
import ast,json,hashlib
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-compatibility-composed-recovery-preparation01-2026-10-04';tree=ast.parse((A/'verify01.py').read_bytes());main=next(n for n in tree.body if isinstance(n,ast.If));tr=next(n for n in main.body if isinstance(n,ast.Try));body=compile(ast.Module(body=tr.handlers[0].body,type_ignores=[]),'exact-main-exception-handler','exec');rows=[]
class HostileInterrupt(KeyboardInterrupt):
 def __str__(self):raise SystemExit('later string diagnostic')
for kind in ['str','print']:
 primary=HostileInterrupt() if kind=='str' else MemoryError('original fatal');secondary=OSError('later print diagnostic')
 def output(*args,**kwargs):raise secondary
 ns={'json':json,'print':output}
 try:
  try:raise primary
  except BaseException as error:ns['error']=error;exec(body,ns)
 except BaseException as actual:
  assert actual is not primary and (isinstance(actual,SystemExit) if kind=='str' else actual is secondary)
  rows.append({'id':'CR3','diagnostic':kind,'primary':type(primary).__name__,'escaped':type(actual).__name__,'original_in_context':actual.__context__ is primary,'first_fatal_preserved':False})
 else:raise AssertionError('fatal missing')
(H/'WITNESS02.json').write_text(json.dumps({'actual_source':'14145d47b0df54c4234c4c029a1108ce8b3e7a9d4638f92b9475d99eb3f7c52f','scope':'exact exception handler only; no run/public main invoked','witnesses':rows},indent=2)+'\n');print(json.dumps(rows))

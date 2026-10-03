import ast,json
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent;seen=[];fatal=KeyboardInterrupt('first control fatal')
def first():seen.append('before');raise fatal
def stop():seen.append('stop');raise ValueError('later stop failure')
def after():seen.append('after')
try:R._cleanup((first,stop,after))
except BaseException as actual:assert actual is fatal
assert seen==['before','stop','after']
tree=ast.parse((H/'parent01.py').read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='child_cleanup')
calls=[n for n in ast.walk(f) if isinstance(n,ast.Call) and ast.unparse(n.func)=='R._cleanup'];assert len(calls)==1
assert all(x in ast.unparse(calls[0]) for x in ("'before'","'stop'","'after'"))
(H/'CHECKS03.json').write_text(json.dumps({'checks':3,'first_fatal_preserved':True,'every_control_attempted':seen,'actual_native_commands':False},indent=2)+'\n');print('3 checks passed')

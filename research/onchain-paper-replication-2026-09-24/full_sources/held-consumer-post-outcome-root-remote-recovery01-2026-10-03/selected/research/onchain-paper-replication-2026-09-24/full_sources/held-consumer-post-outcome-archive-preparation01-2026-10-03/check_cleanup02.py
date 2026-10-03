import ast,json
from pathlib import Path
import post_outcome01 as P
H=Path(__file__).resolve().parent
fatal=KeyboardInterrupt('original synthetic fatal')
closed=[]
def badclose():closed.append(True);raise RuntimeError('synthetic close')
try:
    try:raise fatal
    finally:P.R._cleanup((badclose,))
except BaseException as actual:assert actual is fatal
assert closed==[True]
tree=ast.parse((H/'post_outcome01.py').read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='recover')
tries=[n for n in ast.walk(fn) if isinstance(n,ast.Try) and n.finalbody]
assert len(tries)==1
assert ast.unparse(tries[0].finalbody[0])=='R._cleanup((output.close,))'
(H/'CHECK_CLEANUP02.json').write_text(json.dumps({'checks':3,'status':'passed','first_fatal_preserved':True,'recover_finally_uses_inherited_cleanup':True},indent=2)+'\n')
print('3 cleanup controls passed')

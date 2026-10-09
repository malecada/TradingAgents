import ast,json,subprocess
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[4]
old=ast.parse((D.parent/'full25increment06/recover06.py').read_text());bad=ast.parse((D/'recover08.py').read_text());fixed=ast.parse((D/'recover08_02.py').read_text())
def modecheck(tree):
 return next(n for n in ast.walk(tree) if isinstance(n,ast.Assert) and 'parts[:2]' in ast.unparse(n.test))
a,b,c=map(modecheck,(old,bad,fixed));assert ast.dump(a,include_attributes=False)==ast.dump(c,include_attributes=False)
archive=json.loads((D/'CAPTURE08.json').read_bytes())['archive']['path']
line=subprocess.check_output(['git','ls-tree','HEAD','--',archive],cwd=R,text=True).strip();parts=line.split();assert parts[:2]==['100644','blob']
def check(node,parts):
 try:exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-source-mode-assert','exec'),{'parts':parts,'a':{'path':archive}});return True
 except AssertionError:return False
assert check(a,parts) and check(c,parts) and not check(b,parts)
for mode in ('100844','100755','120000'):
 assert not check(c,[mode,*parts[1:]])
print(json.dumps({'actual_local_git_mode':parts[0],'original06_and_corrected02_same_AST_assert':True,'old08_rejects_actual100644':True,'corrected02_accepts_actual100644':True,'corrected02_refuses':['100844','100755','120000'],'network':False}))

import ast,itertools,json
from pathlib import Path
r=Path(__file__).resolve().parent;tree=ast.parse((r/'verifier01.py').read_bytes());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='verify');node=next(x for x in fn.body if isinstance(x,ast.If)and any(isinstance(n,ast.Name)and n.id=='joined'for n in ast.walk(x)));code=compile(ast.Module(body=[node],type_ignores=[]),'<actual exit-join seam>','exec');checks=[]
for noclaim,actual,child,supervisor in itertools.product((False,True),(None,0,1,137),(0,1,137),(0,1,137)):
 clean={'source_bound_no_dispatch':True,'supervisor_exit':child} if noclaim else {'original_parent_exit':child};parent={'actual_child_exit':child,'supervisor_result':{'exit_code':supervisor},'cleanup':clean};ns={'parent':parent,'context':{'actual_parent_exit':actual},'cleanup':True,'missing':[]};exec(code,ns);expected=actual==child==supervisor==1;assert ns['cleanup']==expected;checks.append([noclaim,actual,child,supervisor,ns['cleanup']])
(r/'CHECKS03.json').write_text(json.dumps({'count':len(checks),'scope':'exact source-extracted scalar exit joins; no genuine receipt objects','cases':checks},sort_keys=True,indent=2)+'\n');print(len(checks))

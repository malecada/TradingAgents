from pathlib import Path
import ast,json,types
D=Path(__file__).resolve().parent;tree=ast.parse((D/'restore01.py').read_text());run=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run');boundary=next(x for x in run.body if isinstance(x,ast.FunctionDef) and x.name=='boundary');rows=[]
def require(v,m):
 if not v:raise ValueError(m)
for kind,start,count,after,free,expected in [('normal',0,63,0,10737418240,True),('sample-ceiling',0,64,0,10737418240,False),('initial-deadline',180,0,180,10737418240,False),('after-deadline',179,0,180,10737418240,False),('floor',0,0,0,10737418239,False)]:
 clock=[start];calls=[];observations=[{} for _ in range(count)]
 def census(p):calls.append(p);clock[0]=after;return {'opaque_synthetic_resource_row':True}
 env={'time':types.SimpleNamespace(monotonic=lambda:clock[0]),'begun':0,'observations':observations,'R':types.SimpleNamespace(require=require,FLOOR=10737418240),'W':types.SimpleNamespace(census=census),'HERE':D,'shutil':types.SimpleNamespace(disk_usage=lambda p:types.SimpleNamespace(free=free))}
 exec(compile(ast.Module(body=[boundary],type_ignores=[]),'<exact original boundary AST>','exec'),env)
 try:env['boundary']();accepted=True;error=None
 except ValueError as e:accepted=False;error=str(e)
 assert accepted==expected
 if kind in ('sample-ceiling','initial-deadline'):assert not calls
 rows.append({'kind':kind,'accepted_synthetic_boundary_only':accepted,'census_calls':len(calls),'rows_after':len(observations),'error':error})
(D/'BOUNDARY01.json').write_text(json.dumps({'exact_original_ast':True,'no_actual_receipt_created':True,'rows':rows},indent=2)+'\n');print(len(rows))

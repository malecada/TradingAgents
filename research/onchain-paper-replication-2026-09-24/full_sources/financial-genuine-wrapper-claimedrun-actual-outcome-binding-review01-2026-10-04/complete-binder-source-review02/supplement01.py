import ast,copy,json
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-claimedrun-outcome-binding-preparation02-2026-10-04';W=H.parent/'financial-genuine-wrapper-claimedrun-claim-window-review01-2026-10-04'
inverse=json.loads((P/'INVERSE02.json').read_bytes());candidate=ast.parse(inverse['verifier_new'].replace('\n  ','\n'));new=[n for n in candidate.body if isinstance(n,ast.Assign)];tree=ast.parse((W/'actual-verify.py').read_bytes());old=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and n.lineno in (261,263)];assert len(old)==2
class Rename(ast.NodeTransformer):
 def visit_Name(self,n):
  n.id={'registered':'gate','exp':'e','windows':'expected_windows','exposures':'expected_exposures'}.get(n.id,n.id);return n
normalized=[Rename().visit(copy.deepcopy(n)) for n in old];assert [ast.dump(n) for n in normalized]==[ast.dump(n) for n in new]
gate=json.loads((W/'actual-old-gate.json').read_bytes());claim=json.loads((W/'actual-old-claim.json').read_bytes());exp=gate['experiments'][claim['experiment_id']];checks=['two actual original assignment ASTs identical modulo local names'];results=[]
for stage in ('exploratory','confirmation'):
 e=copy.deepcopy(exp);e['stage']=stage
 original={'registered':gate,'exp':e};successor={'gate':gate,'e':e}
 exec(compile(ast.Module(body=old,type_ignores=[]),'<genuine scalar original>','exec'),original)
 exec(compile(ast.Module(body=new,type_ignores=[]),'<candidate scalar assignments>','exec'),successor)
 assert original['windows']==successor['expected_windows'] and original['exposures']==successor['expected_exposures'];checks.append('exact original expansion '+stage);results.append({'stage':stage,'state':successor['expected_windows'][0]['state'],'availability':successor['expected_windows'][0]['availability']})
out={'checks':len(checks),'check_names':checks,'results':results,'only_scalar_expected_metadata_no_claim_created':True};(H/'SUPPLEMENT01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out))

"""Execute only the actual helper's final readonly tree-rewalk against local bytes."""
import ast,hashlib,json,stat
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03'
p=OUT/'recover_comparison_outcome01.py';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='2bd1d8d8b3af556111482158daacaaa55c9ff3721786736596e78ca51f2d864c'
tree=ast.parse(raw);loop=next(n for n in tree.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='path')
r=json.loads((OUT/'OUTCOME_RETENTION01.json').read_bytes());expected={x['path']:x for x in r['members']};assert '.' not in expected
ns={'owned':HERE/'restored-collection01','expected':expected,'actual':set(),'stat':stat,'digest':lambda b:hashlib.sha256(b).hexdigest()}
try:exec(compile(ast.Module(body=[loop],type_ignores=[]),str(p),'exec'),ns)
except KeyError as error:
 assert error.args==('.',);result={'finding':'RCO1','reproduced':True,'error_type':'KeyError','missing_key':'.','actual_member_count':len(expected),'root_row_present':False,'scope':'exact original source rewalk only; no network/claims/collector replay'}
else:raise AssertionError('expected genuine helper rewalk refusal absent')
(HERE/'RECOVERY_COUNTEREXAMPLE01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
old=HERE.parent/'neural-cold-feature-handoff-materialization-outcome01-2026-10-03/recover_outcome01.py';before=ast.parse(old.read_bytes())
for name in ('call','digest','put'):
 one=next(n for n in before.body if isinstance(n,ast.FunctionDef) and n.name==name);two=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name);assert ast.dump(one,include_attributes=False)==ast.dump(two,include_attributes=False)
print('PASS actual Git/put/digest helper function AST unchanged; source-only delta review retained')

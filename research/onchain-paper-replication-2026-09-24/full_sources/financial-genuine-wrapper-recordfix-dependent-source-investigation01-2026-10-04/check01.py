"""Evaluate only exact scalar source comparison expressions, never imported model code."""
import ast,json
from pathlib import Path
H=Path(__file__).resolve().parent;P=H/'source/tradingagents/research/onchain_replication';rows=[]
for name,func,left in [('financial_wrapper_fixture.py','_parent',"value['provenance']"),('training.py','_reserve','old'),('evaluation.py','recover_completed_model','old')]:
 tree=ast.parse((P/name).read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==func)
 expr=next(n for n in ast.walk(node) if isinstance(n,ast.Compare) and isinstance(n.left,ast.DictComp) and "'source_commit'" in ast.unparse(n))
 code=compile(ast.Expression(expr),'<exact-source-comparison>','eval');a={'source_commit':'a'*40,'cell_id':'same','config_hash':'configuration','source_hashes':['unchanged-body'],'input_hash':'recipe'};b=dict(a,source_commit='b'*40)
 def agrees(old,new):
  env={'old':old,'value':{'provenance':old},'prov':new,'provenance':new};v=eval(code,{'__builtins__':{}},env);return v if isinstance(expr.ops[0],ast.Eq) else not v
 assert agrees(a,b);rows.append(name+': distinct commits accepted by exact scalar science comparison')
 for k in ['cell_id','config_hash','source_hashes','input_hash']:
  c=dict(b);c[k]='changed';assert not agrees(a,c);rows.append(name+': changed '+k+' refused')
(H/'CHECKS01.json').write_text(json.dumps({'checks':rows,'count':len(rows),'qualification':'scalar expression behavior only, not admission or numerical checkpoint validation','imports_of_copied_source':0},indent=2)+'\n')
print('PASS',len(rows))

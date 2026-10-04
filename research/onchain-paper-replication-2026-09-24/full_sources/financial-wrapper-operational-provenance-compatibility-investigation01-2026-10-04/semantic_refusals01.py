import ast,copy,json
from pathlib import Path
H=Path(__file__).resolve().parent
source=json.loads((H/'SOURCE_CLOSURE_ORIGINAL01.json').read_text())['installed'];claim=json.loads((H/'parent-metadata/claim_input.json').read_text());old=json.loads((H/'parent-metadata/checkpoint_input.json').read_text())['provenance'];assert all(claim['experiment']['source_files'].get(p)==h for p,h in source.items())
t=ast.parse((H/'source-original/tradingagents/research/onchain_replication/financial_wrapper_fixture.py').read_bytes());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_parent');expr=next(n.args[0] for n in ast.walk(f) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='prior scientific provenance differs');compiled=compile(ast.Expression(expr),'<actual-parent-metadata-predicate>','eval');rows=[]
for field,value in [('config_hash','a'*64),('input_hash','b'*64),('dictionary_hash','c'*64),('fold_id','wrong-fold'),('cell_id','wrong-cell'),('model_execution',{'opaque':'not original eager'})]:
 changed=copy.deepcopy(old);changed[field]=value;accepted=eval(compiled,{'__builtins__':{}},{'value':{'provenance':old},'prov':changed});assert not accepted;rows.append({'changed_field':field,'original_comparison_refuses':True})
# Genuine pure metadata plan validator: no Run object or admission is constructed.
classes={'Unavailable','require','validate_plan','_interrupt_case'};env={'PHASES':('agreement','interrupt1','complete100','continue100','predict')};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in classes],type_ignores=[]),'<actual-case-validator>','exec'),env)
oldplan=json.loads((H/'parent-metadata/parent_plan_input.json').read_text());ph=json.loads((H/'ORIGINAL_PHASE_TEMPLATES01.json').read_text());child=next(r['proposed_plan'] for r in ph['slots'] if r['proposed_plan']['phase']=='continue100' and r['proposed_plan']['task']=='classification' and r['proposed_plan']['execution']=='eager');env['_interrupt_case'](child,oldplan,claim['experiment_id'])
for k,v in [('cell_id','wrong-cell'),('task','regression'),('execution','selected')]:
 bad=copy.deepcopy(child);bad[k]=v
 try:env['_interrupt_case'](bad,oldplan,claim['experiment_id'])
 except ValueError:rows.append({'wrong_child_field':k,'original_case_validator_refuses':True})
 else:raise AssertionError('bad case accepted')
(H/'SEMANTIC_REFUSALS01.json').write_text(json.dumps({'historical_claim_all194_source_pins_match':True,'source_predicate_refusal_cases':len(rows),'rows':rows,'future_compatibility_not_implemented':True},indent=2)+'\n');print(json.dumps({'cases':len(rows),'all_refused':True,'source_claim_map_equal':True}))

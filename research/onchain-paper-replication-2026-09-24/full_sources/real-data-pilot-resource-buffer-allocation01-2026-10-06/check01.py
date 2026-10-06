import ast,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
import allocation01 as a
H=Path(__file__).resolve().parent;ROOT=H.parents[3]
P=H.parent/'real-data-pilot-resource-input-builder02-2026-10-06/build_inputs02.py'
s=importlib.util.spec_from_file_location('builder02',P);b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g={week:{'rows':1,'hash':format(i,'064x')} for i,week in enumerate(b.WEEKS)}
budget={'score-tail-f64':{'max_operations':1,'max_preserved_bytes':2560,'max_recovered_bytes':1,'max_chunks':1,'chunk_bytes':2560},'score-batch-f64':{'max_operations':2,'max_preserved_bytes':256,'max_recovered_bytes':256,'max_chunks':2,'chunk_bytes':256},'mcm-output-f32':{'max_operations':1,'max_preserved_bytes':128,'max_recovered_bytes':1,'max_chunks':1,'chunk_bytes':128}}
policy,total,low=b.typed_budget(g,{'chunk_cells':32,'by_week':{w:budget for w in b.WEEKS},'max_control_bytes':8192})
assert all(v['score-tail-f64']['recovered_bytes']==0 for v in low.values())
result=a.graph(1,32,2560,128,4096)
try:a.check_typed_allowances(result,budget)
except ValueError as e:assert 'score-tail-f64/max_recovered_bytes' in str(e)
else:raise AssertionError('mandatory tail replay not charged')
source=ROOT/'tradingagents/research/onchain_replication/typed_payload_operations.py';tree=ast.parse(source.read_text())
call=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and any(isinstance(x,ast.Constant) and x.value=='typed recovery allowance exhausted' for x in n.args))
predicate=compile(ast.Expression(call.args[0]),str(source),'eval')
obj=SimpleNamespace(counter={'recovered':2560,'chunks':2},budget=budget['score-tail-f64'])
assert eval(predicate,{'self':obj}) is False
fixed={k:dict(v) for k,v in budget.items()};fixed['score-tail-f64'].update(max_recovered_bytes=2560,max_chunks=2);a.check_typed_allowances(result,fixed)
obj.budget=fixed['score-tail-f64'];assert eval(predicate,{'self':obj}) is True
assert result['phase_logical_payload_bounds']['tail_part_preserve']==4096+2560+256+3*2560
assert a.allocated_file_upper(100,3,4096)==12385
print(json.dumps({'passed':True,'builder02_accepts_underfunded_tail_replay':True,'actual_recover_predicate_red':True,'corrected_declaration_green':True,'required_tail_recovered_bytes':2560,'required_tail_chunks':2,'no_authority_or_payload_created':True},indent=2))

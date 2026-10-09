"""Exact candidate early predicate AST and checkpoint callback accounting, synthetic only."""
exec(compile((__import__('pathlib').Path(__file__).parent/'verify01.py').read_text().replace("(H/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\\n')","pass"),'<reused focused fixture>','exec'))
# Execute exact normalized/effective predicates from caller with authenticated metadata values.
text=(H/'real_pilot_import_caller.py').read_text();tree=ast.parse(text)
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='admitted')
selected=next(n for n in ast.walk(f) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='batched')
def require(ok,msg):
 if not ok:raise ValueError(msg)
ns=dict(compact_policy=compact_policy,matching_pair=matching_pair,compact_pair=p['pair'],s=plan,require=require)
exec(compile(ast.Module(body=selected.body[3:6],type_ignores=[]),'<exact early metadata predicates>','exec'),ns)
assert ns['effective']==effective and ns['normalized']==normalized
from tradingagents.research.onchain_replication.batched_pair_executor import PairExecutor,CheckpointStop
schedule=copy.deepcopy(p['schedule']);schedule['calls_per_checkpoint']=1;schedule['operations_per_call']=1
calls=[]
def callback(*args):calls.append((args[0],args[1],args[5].copy(),args[6].copy()))
x=PairExecutor(effective,normalized,schedule,callback)
try:x(g,g,'5'*64)
except CheckpointStop:pass
else:raise AssertionError('finite schedule must checkpoint')
assert x.checkpoints==1 and x.reserved_bytes==normalized['max_checkpoint_bytes']+2*matching_pair.LIMIT and x.poisoned
assert len(calls)==1 and calls[0][2]==effective and calls[0][3]==normalized
(H/'RESULT02.json').write_text(json.dumps(dict(status='PASS',early_candidate_predicates=True,synthetic_checkpoint_calls=len(calls),reserved_bytes=x.reserved_bytes,unchanged_registered_schedule=True),indent=2)+'\n')
print('PASS exact early predicates and actual checkpoint accounting')

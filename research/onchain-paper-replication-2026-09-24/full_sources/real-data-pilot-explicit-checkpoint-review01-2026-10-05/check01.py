from pathlib import Path
from types import MappingProxyType
import ast,hashlib,json,sys
D=Path(__file__).resolve().parent;M=D.parents[3];A=D.parent/'real-data-pilot-explicit-checkpoint-execution01-2026-10-05';P=Path('tradingagents/research/onchain_replication');T=A/'candidate'/P
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_bytes())
assert h(A/'MANIFEST01.json')=='b2a51771ad5c54efa9b25d5c9ebf19e96c6cbd574e7e37ca45bae9fcc780162a'
man=read(A/'MANIFEST01.json')
for r in man['members']:
 p=A/r['path'];assert h(p)==r['sha256'] and p.stat().st_size==r['bytes']
for r in read(A/'SOURCE_DELTA01.json')['files']:
 p=Path(r['path']);assert h(M/p)==r['baseline_sha256']==h(A/'baseline'/p.name);assert h(A/'candidate'/p)==r['candidate_sha256'];lines=(A/'candidate'/p).read_text().splitlines(True)
 for e in reversed(r['edits']):assert lines[e['new_start']:e['new_end']]==e['new'];lines[e['new_start']:e['new_end']]=e['old']
 assert ''.join(lines).encode()==(M/p).read_bytes()
def cls(p,name):return next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.ClassDef) and n.name==name)
assert ast.dump(cls(T/'model.py','GraphEncoder'))==ast.dump(cls(A/'baseline/model.py','GraphEncoder'))
a=cls(A/'baseline/model.py','ReplicationModel');b=cls(T/'model.py','ReplicationModel')
for n in a.body:
 if isinstance(n,ast.FunctionDef) and n.name!='__init__':assert ast.dump(n)==ast.dump(next(x for x in b.body if isinstance(x,ast.FunctionDef) and x.name==n.name))
# Metadata-only counterexample: mutate the original selected policy after validation.
f=next(n for n in ast.parse((T/'model.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='validate_execution');env={'MappingProxyType':MappingProxyType};exec(compile(ast.Module(body=[f],type_ignores=[]),str(T/'model.py'),'exec'),env)
p={'schema_version':2,'backend':'streamed-gat-mulsum-v1','block_edges':65536,'graph_activation_checkpointing':True};selection=env['validate_execution'](p);p['graph_activation_checkpointing']=False;p['block_edges']=1
assert selection['graph_activation_checkpointing'] is True and selection['block_edges']==65536
try:selection['graph_activation_checkpointing']=False
except TypeError:pass
else:raise AssertionError('execution metadata writable')
records=[]
for name,version in [('streamed-baseline',1),('checkpointed',2)]:
 r=read(A/name/'attempt/complete.json');assert r['status']=='complete' and r['optimizer_steps']==1 and r['checkpoint_exact_readback'] is True and r['financial_fit_complete'] is False and r['paper_financial_fits']==0
 checkpoint=A/name/'attempt/checkpoint.pt';assert h(checkpoint)==r['checkpoint_sha256'] and checkpoint.stat().st_size==r['checkpoint_bytes']<=4*1024**2
 assert r['model_execution']['schema_version']==version;assert r['batch']==16 and r['lookback']==28 and r['unique_graphs']==7 and r['graph_references']==448
 records.append(r)
assert records[0]['loss']==records[1]['loss'];assert records[0]['gradients']==records[1]['gradients']
failure=read(A/'implicit-refusal/attempt/failed.json');assert failure['optimizer_steps']==0 and failure['optimizer_step_started'] is False and failure['partial_files_retained'] is True and not (A/'implicit-refusal/attempt/checkpoint.pt').exists()
comparison=read(A/'COMPARISON01.json');assert comparison['graph_forward_entries']==[7,14] and comparison['bitwise_equal']['gradient_tensors']==20 and comparison['memory_savings_measured'] is False
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
print(json.dumps({'decision':'pass','source_inverses_and_current_baselines':2,'manifest_members_verified':len(man['members']),'GraphEncoder_and_nonconstructor_model_methods_AST_unchanged':True,'selected_policy_detached_and_immutable':True,'synthetic_checkpoint_hash_size_receipt_joins':2,'implicit_refusal_before_optimizer_checkpoint':True,'numerical_comparison_rerun':False,'checkpoint_bodies_deserialized':False,'numerical_imports':False,'memory_or_capacity_tested':False},sort_keys=True,indent=2))

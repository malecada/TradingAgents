"""Pure metadata checks through actual current validators; no arrays or jobs."""
import ast,copy,hashlib,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
from tradingagents.research.onchain_replication import compact_policy,matching_pair,checkpoint_chunks,stage_retention
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('capacity_builder',HERE/'build01.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
result=builder.build();details=result['CAPACITY_SELECTION01.json'];stage=result['compact_policy.json']['stage_policy'];checks=[]
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def refuse(name,fn):
 try:fn()
 except ValueError:checks.append(name);return
 raise AssertionError(name)
data=builder.read('inputs');config=json.loads((builder.ROOT/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text())
effective=compact_policy.effective_matching(config,stage['pair'])
check('only pair capacity differs',effective==config|{'max_pair_entries':8402640} and config['max_pair_entries']==4000000)
check('deterministic bytes',result==builder.build())
for g in details['graphs']:
 value=compact_policy.validate(stage,kind='mcm',pairs=g['mcm_cells'])
 check('actual compact validator '+g['graph_sha256'][:8],value['logical_reservation_bytes']==g['stage_logical_reservation_bytes'])
for g in data['topology']['graphs']:
 for m in data['motifs']['representatives']:
  # Metadata carriers only: no graph contract or fabricated scientific input.
  a=SimpleNamespace(node_ids=range(g['maximum_cardinality']),edge_index=SimpleNamespace(shape=(2,g['edges'])))
  b=SimpleNamespace(node_ids=range(m['nodes']),edge_index=SimpleNamespace(shape=(2,m['edges'])))
  p=compact_policy.pair_policy(stage['pair'])
  matching_pair.policy_check(a,b,effective,p,allow_checkpoint_layout=True)
check('all224 actual pair-policy checks',True)
check('actual retention validator',stage_retention.validate(stage['restart_retention'],stage['pair'])==stage['restart_retention'])
check('actual sharded geometry',4*checkpoint_chunks.describe([350110,24],'<f8',stage['pair']['checkpoint_layout'],'M')['bytes']+3*65536==stage['pair']['max_checkpoint_bytes'])
check('actual I/O scratch',checkpoint_chunks.io_scratch_bytes(stage['pair']['checkpoint_layout'])==details['checkpoint_io_scratch_bytes'])
# Compile the actual copied kernel validator unchanged, without importing its
# numerical workload; all inputs remain integer metadata.
tree=ast.parse((HERE/'imported_kernel.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy')
namespace={'require':lambda value,message:None if value else (_ for _ in ()).throw(ValueError(message))}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/'imported_kernel.py'),'exec'),namespace)
for g in details['graphs']:namespace['validate_policy'](result['mcm_policy.json']['numeric'],g['mcm_cells'])
check('all7 actual numeric validator',True)
refuse('insufficient stage retained total',lambda:compact_policy.validate(stage|{'max_retained_logical_bytes':1},kind='mcm',pairs=32))
refuse('decreasing pair override',lambda:compact_policy.effective_matching(config,stage['pair']|{'max_pair_entries_override':1}))
refuse('invalid extraction limit',lambda:namespace['validate_policy'](result['mcm_policy.json']['numeric']|{'extraction_limit':0},32))
# Complete source inverse for the sole reservations schema seam.
current=(builder.ROOT/'tradingagents/research/onchain_replication/real_pilot_reservations.py').read_text()
expected=current.replace('set(numeric)==fields',"set(numeric) in (fields,fields|{'extraction_limit'})").replace("compact_policy.positive(numeric[k] for k in fields-{'schema_version'})","compact_policy.positive(numeric[k] for k in fields-{'schema_version'})\n    if 'extraction_limit' in numeric:compact_policy.positive((numeric['extraction_limit'],))")
check('reservations full source inverse',(HERE/'real_pilot_reservations.py').read_text()==expected)
check('kernel byte copy',hashlib.sha256((HERE/'imported_kernel.py').read_bytes()).hexdigest()==builder.PINS['kernel'][1])
check('whole capacity remains unproved',details['execution_admitted'] is False and details['complete_resource_envelope_proven'] is False)
print(json.dumps({'status':'PASS','checks':checks,'count':len(checks),'pair_cases':224,'array_allocations':0,'empirical_runs':0,'native_runs':0},indent=2))

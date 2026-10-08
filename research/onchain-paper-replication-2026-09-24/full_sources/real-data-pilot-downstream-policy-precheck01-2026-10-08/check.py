"""Gate-selected policy metadata only; no authority, graphs or arrays created."""
import ast, hashlib, importlib.abc, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT))
class NoNeural(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'torch','tensorflow','jax'}:
            raise AssertionError('forbidden neural import: '+fullname)
sys.meta_path.insert(0,NoNeural())
from tradingagents.research.onchain_replication import compact_policy, matching_pair, resource_binding, real_pilot_import_caller, checkpoint_chunks
from tradingagents.research.onchain_replication import matching_checkpoint

pins={}
def read(path):
    path=ROOT/path;data=path.read_bytes()
    pins[str(path.relative_to(ROOT))]=hashlib.sha256(data).hexdigest()
    return data

gatepath='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final21-2026-10-08/gate01.json'
gate=json.loads(read(gatepath))
experiment=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261008-21']
def role(name):
    r=experiment['inputs'][name];data=read(r['path'])
    assert hashlib.sha256(data).hexdigest()==r['sha256'],name
    return json.loads(data)

pair=role('pair_policy');compact=role('compact_policy');mcm=role('mcm_policy')
job=role('execution_job');plan=role('producer_plan');pilot=role('pilot')
resource_binding.validate_job(job)
real_pilot_import_caller.schema(job)
real_pilot_import_caller.validate_plan(pilot)
selected=next(iter(job['payload']['representation_jobs'].values()))
item=plan['producers'][selected['producer']]
assert selected['pair_checkpoint_input']==item['pair_checkpoint_input']=='pair_policy'
assert selected['compact_policy_input']==item['compact_policy_input']=='compact_policy'
assert selected['compact_mcm_input']==item['compact_mcm_input']=='mcm_policy'
assert selected['descriptor']==item['descriptor']
assert selected['descriptor']['pair_execution']['policy_sha256']==experiment['inputs']['pair_policy']['sha256']
assert selected['descriptor']['compact_execution']['policy_sha256']==experiment['inputs']['compact_policy']['sha256']
assert pair['limits']==compact['stage_policy']['pair']

# Compile actual pure owner validator while avoiding authority/feature imports.
ownerpath='tradingagents/research/onchain_replication/matching_owner.py'
tree=ast.parse(read(ownerpath));wanted={'require','_pair_limits'}
ns={'matching_pair':matching_pair,'__package__':'tradingagents.research.onchain_replication'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted],type_ignores=[]),ownerpath,'exec'),ns)
ns['_pair_limits'](pair['limits'],resource=True)
compact_policy.validate(compact['stage_policy'],kind='mcm',pairs=mcm['max_entries'])
config=selected['descriptor']['configs']['matching']
effective=compact_policy.effective_matching(config,pair['limits'])
assert config['max_pair_entries']==4000000 and effective['max_pair_entries']==8402640
assert {k:v for k,v in config.items() if k!='max_pair_entries'}=={k:v for k,v in effective.items() if k!='max_pair_entries'}

kernelpath='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-capacity-selection02-2026-10-08/imported_kernel.py'
tree=ast.parse(read(kernelpath));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy')
exec(compile(ast.Module(body=[fn],type_ignores=[]),kernelpath,'exec'),ns)
ns['validate_policy'](mcm['numeric'],mcm['max_entries'])
assert mcm['numeric']['extraction_limit']==350110
assert set(mcm)=={'schema_version','max_entries','max_workflow_metadata_bytes','numeric','durability'} and mcm['schema_version']==2
assert mcm['max_workflow_metadata_bytes']>=3*8192*7
from tradingagents.research.onchain_replication.chunk_durability import policy as durability
assert durability(mcm['durability'])

# Actual lower scalar engine policy receives only ENGINE_FIELDS. Envelope
# dimensions are metadata, not fabricated graphs or empirical size assertions.
n=mcm['numeric']['extraction_limit'];entries=effective['max_pair_entries']
assert entries%n==0
motif_envelope=entries//n
matching_checkpoint.policy(n,motif_envelope,effective,**{k:pair['limits'][k] for k in matching_pair.ENGINE_FIELDS})
stripped=compact_policy.pair_policy(pair['limits'])
tree=ast.parse(read('tradingagents/research/onchain_replication/matching_pair.py'))
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='policy_check')
exec(compile(ast.Module(body=[fn.body[1]],type_ignores=[]),'matching_pair.policy_check schema','exec'),matching_pair.__dict__,{'policy':stripped,'allow_checkpoint_layout':True})
layout=stripped['checkpoint_layout']
required_checkpoint=4*checkpoint_chunks.describe([n,motif_envelope],'<f8',layout,'M')['bytes']+3*matching_pair.LIMIT
assert stripped['max_checkpoint_bytes']>=required_checkpoint
assert stripped['max_state_bytes']>=32*entries+checkpoint_chunks.io_scratch_bytes(layout)
assert stripped['total_checkpoint_bytes']>=2*matching_pair.LIMIT+stripped['max_checkpoint_bytes']
assert 'torch' not in sys.modules
print(json.dumps({'status':'PASS','scope':'metadata schemas and declared capacity envelope only','gate':gatepath,
 'original_capacity':config['max_pair_entries'],'explicit_capacity':entries,'extraction_limit':n,
 'motif_envelope_derived_from_declared_capacity':motif_envelope,'required_checkpoint_bytes':required_checkpoint,
 'scoring_diagnostic':pilot['scoring_diagnostic'],'policy_pins':pins,
 'no_graph_array_owner_run_or_neural_import':True},indent=2))

"""Pure metadata/parser source extraction. No Admission, Owner or private reads."""
import ast,copy,hashlib,json,re,types
from pathlib import Path
ROOT=Path.cwd().resolve();H=Path(__file__).resolve().parent;F=H.parent;O=F/'real-data-pilot-full30-binding-preparation02-2026-10-11';PKG=ROOT/'tradingagents/research/onchain_replication'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(x):return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def extract(name,functions,constants=(),scope=None):
 scope={} if scope is None else scope;path=PKG/name;nodes=[]
 for n in ast.parse(path.read_bytes()).body:
  if isinstance(n,ast.FunctionDef) and n.name in functions:nodes.append(n)
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in n.targets):nodes.append(n)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),scope);return scope

def main():
 docs={p.stem:load(p) for p in (H/'public01').glob('*.json')};old={p.stem:load(p) for p in (O/'public01').glob('*.json')};refs=load(H/'PUBLIC_INPUT_REFS_DRAFT01.json');gate=load(F/'real-data-pilot-full30-entry-preparation01-2026-10-11/gate02.json');experiment=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261011-30'];s=docs['execution_job']['payload']['representation_jobs']['original32'];d=s['descriptor'];pilot=docs['pilot'];item=docs['producer_plan']['producers'][s['producer']]
 assert all(item.get(k)==v for k,v in s.items()) and item['binding_output']==pilot['outputs']['binding'] and item['journal_output']==pilot['outputs']['journal']
 assert experiment['cells']==[pilot['cell_id']] and set(pilot['outputs'].values())<=set(experiment['outputs'])
 assert pilot['resource_policy']==docs['execution_job']['resources']
 assert d['required_graphs']==sorted(pilot['graph_inputs']) and d['resource_graph_inputs']==pilot['graph_inputs'] and len(pilot['graph_inputs'])==7
 assert docs['original_import']['sample_count']==512 and docs['original_import']['motif_count']==32 and docs['original_import']['required_graphs']==sorted(pilot['graph_inputs'])
 assert set(pilot['graph_inputs'].values())|{pilot[k] for k in ('population_plan_input','model_input','training_input')}<=set(refs)
 assert pilot['archive_inputs']=={'policy_input':s['compact_archive_input'],'transport_input':s['compact_archive_transport_input']}
 for field,key,hashkey in [('compact_policy_input','compact_execution','policy_sha256'),('compact_archive_input','compact_archive_execution','policy_sha256'),('pair_checkpoint_input','pair_execution','policy_sha256'),('original_dictionary_input','original_dictionary_import','sha256'),('original_dictionary_stage_input','original_dictionary_stage','sha256')]:assert d[key][hashkey]==refs[s[field]]['sha256']
 join=load(H/'SOURCE_JOIN01.json');numerical=docs['pair_policy']['numerical_source'];assert numerical=={'commit':join['anchor'],'files':join['source_files']} and len(numerical['files'])==198
 for p,v in numerical['files'].items():assert sha(ROOT/p)==v==experiment['source_files'][p]
 assert docs['compact_policy']['stage_policy']['pair']==docs['pair_policy']['limits']
 for role,value in docs.items():
  restored=copy.deepcopy(value)
  if role=='pair_policy':restored['numerical_source']=old[role]['numerical_source']
  if role=='archive_policy':restored['remote_namespace']=old[role]['remote_namespace']
  if role=='archive_transport':restored['namespace']=old[role]['namespace']
  if role in ('execution_job','producer_plan'):
   a=restored['payload']['representation_jobs']['original32'] if role=='execution_job' else restored['producers']['original32'];b=old[role]['payload']['representation_jobs']['original32'] if role=='execution_job' else old[role]['producers']['original32']
   for key in ('pair_execution','compact_archive_execution'):a['descriptor'][key]=b['descriptor'][key]
  assert restored==old[role],role
 caller=extract('real_pilot_import_caller.py',{'require','validate_plan','_finite_resources','_amended_host_reserve'},{'KIND','FILE_MAX','GIB'}, {'Path':Path});assert caller['validate_plan'](pilot)==pilot
 req=caller['require'];typed=extract('typed_payload_policy.py',{'require','validate'},{'ASSUMPTION','LEGACY_KINDS','BATCHED_KIND','KINDS'},{'re':re});assert typed['validate'](docs['typed_payload'])==docs['typed_payload']
 policy=extract('compiled_normalization_policy.py',{'require','digest','freeze','runtime_metadata'},{'FORMAT','FIELDS','LIBRARY_SHA256','SOURCE_SHA256'},{'Path':Path,'json':json})
 adaptive=extract('adaptive_edge_policy.py',{'freeze'})
 timing=extract('matching_owner.py',{'binding_timing_policy'},{'BINDING_TIMING_POLICY'},{'require':req})
 geometry=extract('geometry_publication.py',{'policy'},{'FORMAT','POLICY'},{'require':req})
 mcm=extract('compact_mcm_batched.py',{'selected','validate','_compiled_policy'},{'FORMAT'},{'require':req,'compiled_normalization_policy':types.SimpleNamespace(**policy),'adaptive_edge_policy':types.SimpleNamespace(**adaptive),'matching_owner':types.SimpleNamespace(**timing),'geometry_publication':types.SimpleNamespace(**geometry)})
 for graph in docs['typed_payload']['graphs'].values():mcm['validate'](docs['mcm_policy'],graph['rows']*32)
 execution=docs['mcm_policy']['batched']['execution'];cp=execution['compiled_normalization_policy'];runtime=policy['runtime_metadata']((ROOT/refs['compiled_normalization_runtime']['path']).read_bytes());assert runtime['runtime_inventory_sha256']==refs['environment']['sha256']
 for kind,role in execution['compiled_normalization_inputs'].items():assert str(ROOT/refs[role]['path'])==cp[kind+'_path'] and refs[role]['sha256']==cp[kind+'_sha256']
 expected='ethpilot-20261011-30';assert docs['archive_transport']['namespace']==docs['archive_policy']['remote_namespace']==expected and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,19}',expected)
 assert docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None
 assert len(refs)==66 and 'archive_transport' not in refs
 prepared=load(H/'PREPARED01.json');assert prepared['builder03_result']['inputs']=={k:v for k,v in docs.items() if k!='archive_policy'}
 for name in ('prepared','archive_policy'):
  ref=load(H/'REQUEST01.json')[name];assert sha(ROOT/ref['path'])==ref['sha256'] and (ROOT/ref['path']).stat().st_size==ref['bytes']
 for p in H.glob('*.py'):ast.parse(p.read_bytes())
 result={'status':'PASS_SOURCE_METADATA_ONLY','required_sources':198,'changed_sources':8,'new_sources':2,'current_gate_cell_join':True,'actual_validate_plan':True,'actual_typed_policy_validate':True,'actual_batched_validate_graphs':7,'all_five_descriptor_hash_joins':True,'runtime02_environment_join':True,'namespace_exact':True,'public_body_inverse':True,'qualification':'Pure extracted metadata functions only. No admitted(), Owner, reservation activation, private body or numerical execution. Full batched reservation arithmetic operands unchanged; real bound transport identity remains pending.'}
 (H/'CHECK_RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()

"""Finite actual-parser/public-join proof; no binder, authority or science."""
import ast,copy,hashlib,json
from pathlib import Path
ROOT=Path.cwd().resolve();H=Path(__file__).resolve().parent;F=H.parent;O=F/'real-data-pilot-full30-binding-preparation01-2026-10-11';R=F/'matching-compiled-runtime-input02-2026-10-11';R0=F/'matching-compiled-runtime-input01-2026-10-10'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def main():
 old=load(R0/'RUNTIME_REFERENCE01.json');new=load(R/'RUNTIME_REFERENCE01.json');lineage=load(R/'LINEAGE01.json');environment=ROOT/lineage['environment']['path']
 assert sha(environment)==lineage['environment']['sha256']==new['runtime_inventory_sha256']
 assert old['runtime_inventory_sha256']==sha(R0/'INVENTORY01.json')!=new['runtime_inventory_sha256']
 restored=dict(new);restored['runtime_inventory_sha256']=old['runtime_inventory_sha256'];assert restored==old
 parser=ROOT/lineage['parser']['path'];assert sha(parser)==lineage['parser']['sha256']
 tree=ast.parse(parser.read_bytes());nodes=[]
 for n in tree.body:
  if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in ('require','digest','freeze','runtime_metadata'):nodes.append(n)
 scope={'Path':Path,'json':json};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(parser),'exec'),scope)
 assert scope['runtime_metadata']((R/'RUNTIME_REFERENCE01.json').read_bytes())==new
 policy=load(R/'POLICY01.json');assert dict(scope['freeze'](policy))==policy
 refused=0
 for bad in ({**new,'python':'0'},{**new,'runtime_inventory_sha256':None},{**new,'surplus':'x'}):
  try:scope['runtime_metadata'](raw(bad))
  except ValueError:refused+=1
 assert refused==3
 caller=ROOT/lineage['caller']['path'];assert sha(caller)==lineage['caller']['sha256']
 text=caller.read_text();assert "runtime['runtime_inventory_sha256']==ad.inputs['environment']['sha256']" in text
 # Actual caller predicate operands: old reference fails, corrected reference passes.
 assert old['runtime_inventory_sha256']!=sha(environment) and new['runtime_inventory_sha256']==sha(environment)
 docs={p.stem:load(p) for p in (H/'public01').glob('*.json')};prior={p.stem:load(p) for p in (O/'public01').glob('*.json')}
 for role in docs:
  restored=copy.deepcopy(docs[role])
  if role=='mcm_policy':restored['batched']['execution']['compiled_normalization_policy']=prior[role]['batched']['execution']['compiled_normalization_policy']
  if role=='archive_transport':assert restored['connection'] is None;restored['namespace']=prior[role]['namespace']
  if role=='archive_policy':assert restored['transport_identity'] is None;restored['remote_namespace']=prior[role]['remote_namespace']
  if role in ('execution_job','producer_plan'):
   key=('payload','representation_jobs') if role=='execution_job' else ('producers',)
   a=restored;b=prior[role]
   for k in key:a=a[k];b=b[k]
   a['original32']['descriptor']['compact_archive_execution']=b['original32']['descriptor']['compact_archive_execution']
  assert restored==prior[role],role
 refs=load(H/'PUBLIC_INPUT_REFS_DRAFT01.json');assert len(refs)==66 and 'archive_transport' not in refs
 ex=docs['mcm_policy']['batched']['execution'];assert ex['compiled_normalization_policy']==policy
 for kind,role in ex['compiled_normalization_inputs'].items():assert str(ROOT/refs[role]['path'])==policy[kind+'_path'] and refs[role]['sha256']==policy[kind+'_sha256']
 assert policy['runtime_bytes']==(R/'RUNTIME_REFERENCE01.json').stat().st_size
 prepared=load(H/'PREPARED01.json');assert prepared['builder03_result']['inputs']=={k:v for k,v in docs.items() if k!='archive_policy'}
 request=load(H/'REQUEST01.json');assert request['private_parent'].endswith('pilot-transport-20261011-30-02')
 for key in ('prepared','archive_policy'):
  p=ROOT/request[key]['path'];assert sha(p)==request[key]['sha256'] and p.stat().st_size==request[key]['bytes']
 assert docs['archive_transport']['namespace']==docs['archive_policy']['remote_namespace']=='ethpilot-20261011-30v2'
 assert (H/'MATCHING_SCRATCH_RESERVATION01.json').read_bytes()==(O/'MATCHING_SCRATCH_RESERVATION01.json').read_bytes()
 wrapper=(H/'bind_actual01.py').read_text();assert wrapper.replace('pilot-transport-20261011-30-02','pilot-transport-20261011-30-01').replace('archive-dispatch-ethpilot-20261011-30v2','archive-dispatch-ethpilot-20261011-30')==(O/'bind_actual01.py').read_text()
 for p in H.glob('*.py'):ast.parse(p.read_bytes())
 print(json.dumps({'status':'PASS_SOURCE_METADATA_ONLY','old_genuine_caller_environment_join':False,'corrected_join':True,'actual_parser_malformed_refusals':refused,'private_or_authority_execution':False,'roles_pending_private':66}))
if __name__=='__main__':main()

"""Finite source/public metadata checks; never import or execute the binder."""
import ast, copy, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path.cwd().resolve()
def load(p): return json.loads(p.read_bytes())
def raw(x): return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(x): return hashlib.sha256(raw(x)).hexdigest()
def main():
 origins=load(HERE/'ORIGINS01.json'); docs={p.stem:load(p) for p in (HERE/'public01').glob('*.json')}
 old={k:load(ROOT/v['path']) for k,v in origins['public_templates'].items()}
 job=docs['execution_job']; selected=job['payload']['representation_jobs']['original32']; producer=docs['producer_plan']['producers']['original32']
 assert selected['descriptor']==producer['descriptor']
 assert docs['pilot']['resource_policy']==job['resources']
 pilot=copy.deepcopy(docs['pilot']); pilot['resource_policy']=old['pilot']['resource_policy']; assert pilot==old['pilot']
 for role,key in [('archive_transport','namespace'),('archive_policy','remote_namespace')]:
  restored=copy.deepcopy(docs[role]); assert restored[key]=='ethpilot-20261011-30'; restored[key]=old[role][key]; assert restored==old[role]
 for key,role in [('compact_archive_execution','archive_policy'),('compact_execution','compact_policy'),('pair_execution','pair_policy')]: assert selected['descriptor'][key]['policy_sha256']==digest(docs[role])
 for role in ('compact_policy','pair_policy','original_import','resource_population_plan','typed_payload','mcm_output_policy'): assert docs[role]==old[role]
 rootjob=load(ROOT/origins['root_job']['path']); restored=copy.deepcopy(job); restored['payload']['representation_jobs']['original32']['descriptor']=rootjob['payload']['representation_jobs']['original32']['descriptor']; assert restored==rootjob
 assert docs['mcm_policy']==load(ROOT/origins['root_mcm']['path'])
 refs=load(HERE/'PUBLIC_INPUT_REFS_DRAFT01.json'); assert len(refs)==66 and 'archive_transport' not in refs
 policy=docs['mcm_policy']['batched']['execution']; assert set(policy['compiled_normalization_inputs'])=={'source','library','runtime'}
 for kind,role in policy['compiled_normalization_inputs'].items():
  assert refs[role]['sha256']==policy['compiled_normalization_policy'][kind+'_sha256']
  assert str(ROOT/refs[role]['path'])==policy['compiled_normalization_policy'][kind+'_path']
 prepared=load(HERE/'PREPARED01.json'); assert prepared['builder03_result']['inputs']=={k:v for k,v in docs.items() if k!='archive_policy'}
 assert prepared['builder03_result']['inputs']['archive_transport']['connection'] is None
 request=load(HERE/'REQUEST01.json'); assert set(request)=={'prepared','archive_policy','connection','private_parent','private_leaf'}
 for key in ('prepared','archive_policy'):
  pin=request[key]; b=(ROOT/pin['path']).read_bytes(); assert len(b)==pin['bytes'] and hashlib.sha256(b).hexdigest()==pin['sha256']
 scratch=load(HERE/'MATCHING_SCRATCH_RESERVATION01.json'); prior=load(ROOT/origins['scratch']['path']); restored=copy.deepcopy(scratch)
 for key in ('experiment','installed_source','qualification'): restored[key]=prior[key]
 restored['current_integration_review']=restored.pop('historical_integration_review'); assert restored==prior
 for name in ('prepare_public01.py','bind_actual01.py','check01.py'): ast.parse((HERE/name).read_text())
 wrapper=(HERE/'bind_actual01.py').read_text(); assert "ref(HERE/'REQUEST01.json')" in wrapper and "ref(HERE/'BOUND01.json')" in wrapper and 'REQUEST02' not in wrapper
 assert 'module.bind(ROOT,request)' in wrapper and 'connection_path' not in wrapper
 print(json.dumps({'status':'PASS_SOURCE_PUBLIC_METADATA_ONLY','role_count_pending_private':66,'bound_role_count_required':67,'binder_executed':False,'private_body_read':False,'authority':False}))
if __name__=='__main__': main()

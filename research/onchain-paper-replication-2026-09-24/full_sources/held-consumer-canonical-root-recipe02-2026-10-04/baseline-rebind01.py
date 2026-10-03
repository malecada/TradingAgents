"""Pure draft root rebinding; returns bytes, never installs or releases."""
import copy,json
from pathlib import Path
from prepare01 import CAP,HERE,CASES,encode,read,sha,require,release

def rebind(case,capsule=None):
 require(case in CASES,'unknown fixed case')
 if capsule is not None:
  p=Path(capsule);require(p.is_absolute() and p.resolve()==p and p!=CAP and not p.is_relative_to(CAP),'explicit new canonical capsule required')
 d=json.loads(read(HERE/'generated01/DRAFT_CASES01.json'))[case]
 inputs=d['experiment']['inputs'];bodies={}
 for role in ('execution_job','execution_workspace'):
  path=inputs[role]['path'];body=json.loads(read(HERE/'generated01/input-draft'/path))
  if role=='execution_job':body['resources']['disk_paths']=[capsule];body['resources']['storage_budget']['root']=capsule
  elif capsule is not None:body={'root':capsule,'ledger':str(Path(capsule)/'research_runs'),'artifacts':str(Path(capsule)/'research_artifacts'),'git_common':str(Path(capsule)/'.git')}
  bodies[path]=encode(body);inputs[role]['sha256']=sha(bodies[path])
 # Original contract is a metadata schema; no payload arrays are decoded.
 original=CAP/'fixture_inputs/held'/str(case+'01')/'case-contract.json';contract=json.loads(read(original));contract['experiment_id']=None
 for role,item in contract['additional_inputs'].items():
  ref=inputs[role];raw=bodies.get(ref['path'])
  if raw is None:raw=read(HERE/'generated01/input-baseline'/ref['path'])
  item['reference']={'path':ref['path'],'sha256':sha(raw),'bytes':len(raw)}
 d['case_contract']=contract;d['capsule_root']=capsule
 d['role_copy_recipe']={role:{'from':'generated01/role-baseline/'+case+'/'+role+'.json','action':'rebind root-dependent runtime/native metadata and independently verify; preserve original provenance/config bodies'} for role in ('runtime','software_environment','native_environment','native_policy','original_import_index','original_evidence','matching','target_catalog')}
 d['remaining_authority_roles']=['registration','budget_extension','budget_review','charter','budget_allocation','auxiliary_sources']
 d['candidate_implementation_count']=199;d['candidate_package_count']=148;d['future_total_admission_pin_count']=None
 return d,bodies
if __name__=='__main__':
 result={case:rebind(case)[0] for case in CASES}
 with (HERE/'DRAFT_CASES02.json').open('xb') as f:f.write(encode(result))

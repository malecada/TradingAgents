"""Pure draft root rebinding; returns bytes, never installs or releases."""
import copy,json
from pathlib import Path
from prepare01 import CAP,HERE,CASES,encode,read,sha,require,release

def fresh_capsule(capsule):
 import os,re
 require(type(capsule) is str,'capsule must be an explicit string')
 p=Path(capsule);base=CAP.parent.parent
 require(p.is_absolute() and str(p)==capsule and p.resolve()==p and base.resolve()==base,'canonical absolute authorized root required')
 require(p.name=='source' and p.parent.parent==base,'only a fresh direct unit/source under onchain-fixture-isolation is allowed')
 unit=p.parent;closed=CAP.parent
 require(unit!=closed and not unit.is_relative_to(closed) and not closed.is_relative_to(unit),'closed original unit overlap refused')
 require(re.fullmatch(r'[a-z][a-z0-9-]{7,95}',unit.name) is not None,'bounded fresh unit name required')
 require(not any(x.lower() in ('keys','apis','.env','.ssh','.git','hf_token.txt') for x in p.parts),'protected scope refused')
 require(not os.path.lexists(unit),'existing owner/unit namespace refused; Root must choose a fresh unit')
 return p

def validate_draft(d,case):
 from prepare01 import expectations,ROLES
 expected=expectations();require(case in expected['cases'],'fixed case required')
 require(d['roles']==expected['cases'][case]['roles'] and set(d['roles'])==set(ROLES) and len(d['roles'])==15,'exact15 frozen metadata roles required')
 require(d['experiment']['source_files']==expected['candidate'] and len(d['experiment']['source_files'])==199 and sum(k.startswith('tradingagents/') for k in d['experiment']['source_files'])==148,'exact199/148 source closure required')
 require(d['experiment']['inputs']==expected['cases'][case]['inputs'] and len(d['experiment']['inputs'])==33,'exact33 input roles/body references required')
 require(d['experiment']['outputs']==expected['cases'][case]['outputs'] and len(d['experiment']['outputs'])==6,'exact6 outputs required')
 from pathlib import PurePosixPath
 for role,ref in d['experiment']['inputs'].items():
  name=ref['path'];relative=PurePosixPath(name)
  require(type(name) is str and not relative.is_absolute() and str(relative)==name and '..' not in relative.parts and '\\' not in name and '\0' not in name,'canonical relative input path required')
  require(not any(x.lower() in ('keys','apis','.env','.ssh','.git','hf_token.txt') or x.lower().endswith(('.pem','.key')) for x in relative.parts),'protected input scope refused')
  base=HERE/'generated01'/('input-draft' if role in ('execution_job','execution_workspace') else 'input-baseline');target=base/name
  require(target.resolve()==target and target.is_relative_to(base),'redirected input path refused')
  require(sha(read(target))==ref['sha256'],'all33 current opaque input bodies must match frozen role references')

 require(all(d[k] is None for k in ('fresh_identity','source_commit','design_source','registration_commit','capsule_root','caller','independent_review','full_recovery','dependent_success_evidence','cumulative_allocation')),'draft cannot contain invented authority')
 require(d['experiment']['charter'] is None and d['experiment']['cumulative_budget_extension'] is None and d['experiment']['parent'] is None,'historical authority cannot transfer')

def rebind(case,capsule=None):
 require(case in CASES,'unknown fixed case')
 if capsule is not None:
  fresh_capsule(capsule)
 d=json.loads(read(HERE/'generated01/DRAFT_CASES01.json'))[case]
 validate_draft(d,case)
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

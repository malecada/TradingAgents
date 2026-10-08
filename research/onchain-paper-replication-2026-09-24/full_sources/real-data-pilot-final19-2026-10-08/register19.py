"""Assemble one exact unused19 gate from prepared public references; no claim."""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD=F/'real-data-pilot-final18-2026-10-08';REVIEW=F/'real-data-pilot-retry19-review01-2026-10-08';BUDGET=F/'real-data-pilot-retry19-registration01-2026-10-08'
OLDNAME='eth-paper-real-data-end-to-end-resource-20261008-18';NAME='eth-paper-real-data-end-to-end-resource-20261008-19'
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def save(p,v):
 with p.open('x') as out:json.dump(v,out,sort_keys=True,indent=2);out.write('\n')
def build():
 gate=load(OLD/'gate01.json');oldexp=copy.deepcopy(gate['experiments'][OLDNAME]);e=copy.deepcopy(oldexp)
 oldbudget=F/'real-data-pilot-retry18-registration01-2026-10-08'
 exact={str(oldbudget/'CUMULATIVE_ALLOCATION_PROPOSED89_01.json'):str(BUDGET/'CUMULATIVE_ALLOCATION_PROPOSED90_02.json'),str(oldbudget/'EXTENSION_PROPOSED89_01.json'):str(BUDGET/'EXTENSION_PROPOSED90_02.json'),str(F/'real-data-pilot-seventeenth-resource-failed-review01-2026-10-08/budget89-review01/EXTENSION89_REVIEW01.json'):str(REVIEW/'EXTENSION90_REVIEW02.json')}
 pairs=[(str(OLD),str(HERE)),(str(F/'real-data-pilot-fixed18-metadata-successor01-2026-10-08'),str(F/'real-data-pilot-fixed19-metadata-successor01-2026-10-08'))]
 # Paths in source_files are repository-relative; absolute helper paths must be normalized.
 exact={str(Path(k).relative_to(ROOT)):str(Path(v).relative_to(ROOT)) for k,v in exact.items()}
 pairs=[(str(Path(a).relative_to(ROOT)),str(Path(b).relative_to(ROOT))) for a,b in pairs]
 files={}
 for oldpath in oldexp['source_files']:
  path=exact.get(oldpath,oldpath)
  for before,after in pairs:
   if path.startswith(before+'/'):path=after+path[len(before):]
  assert path not in files;files[path]=ref(ROOT/path)['sha256']
 assert len(files)==len(oldexp['source_files'])==298
 e['source_files']=files
 refs=copy.deepcopy(oldexp['inputs'])
 for role,value in load(HERE/'INPUT_REFS01.json').items():refs[role]={'dataset':'eth',**{k:value[k] for k in ('path','sha256')}}
 refs['pair_policy']={'dataset':'eth',**{k:ref(HERE/'templates/pair_policy01.json')[k] for k in ('path','sha256')}}
 assert len(refs)==59 and 'execution_workspace' in refs
 e['inputs']=refs
 e['charter']={k:ref(HERE/'CHARTER01.md')[k] for k in ('path','sha256')}
 e['cumulative_budget_extension']={'extension':{k:ref(BUDGET/'EXTENSION_PROPOSED90_02.json')[k] for k in ('path','sha256')},'review':{k:ref(REVIEW/'EXTENSION90_REVIEW02.json')[k] for k in ('path','sha256')}}
 e['question']='Representative full real Ethereum pilot with reviewed deferred waiting-process engine imports and explicitly user-authorized2.5GiB startup; full motif/MCM/GAT/attention LSTM method and one joint update/checkpoint, actual runtime guards and throughput/capacity measurements.'
 gate['experiments'][NAME]=e
 assert all(gate['experiments'][k]==v for k,v in load(OLD/'gate01.json')['experiments'].items())
 assert gate['families']==load(OLD/'gate01.json')['families'] and e['parent'] is None
 save(HERE/'gate01.json',gate);save(HERE/'ALL_INPUT_REFS01.json',refs)
 binding=load(OLD/'BINDING_DRAFT01.json')
 for role,name in [('gate','gate01.json'),('draft','INPUT_DRAFT01.json'),('preparation','PREPARATION_RESULT01.json'),('baseline','BASELINE01.json'),('transport_binding','TRANSPORT_BINDING01.json')]:binding[role]=ref(HERE/name)
 binding['transport']=load(HERE/'INPUT_REFS01.json')['archive_transport'];binding['identity']=NAME
 binding['source_adoption_review']=ref(REVIEW/'SOURCE_ADOPTION_REVIEW01.json')
 binding['import_source_review']=ref(REVIEW/'import-review01/SOURCE_REVIEW01.json')
 binding['startup_source_review']=ref(REVIEW/'startup-review01/SOURCE_REVIEW01.json')
 binding['prior_outcome_review']=ref(F/'real-data-pilot-eighteenth-native-refusal-review01-2026-10-08/OUTCOME_REVIEW01.json')
 binding['prior_preservation_complete']=ref(F/'real-data-pilot-eighteenth-native-refusal-increment01-2026-10-08/FRESH_GIT_RECOVERY01.json')
 binding['prior_recovery_review']=ref(F/'real-data-pilot-eighteenth-native-refusal-review01-2026-10-08/returned-git-recovery01/RECOVERY_REVIEW01.json')
 binding['binding_review']=None;binding['status']='DRAFT_NOT_RELEASED'
 save(HERE/'BINDING_DRAFT01.json',binding)
 print(json.dumps({'status':'EXACT_GATE_DRAFT_NOT_ADMITTED','source_pins':len(files),'inputs':len(refs),'old_experiments_unchanged':len(gate['experiments'])-1,'startup_bytes':load(HERE/'inputs01/execution_job.json')['resources']['start_reserve_bytes']}))
if __name__=='__main__':build()

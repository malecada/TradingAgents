"""Add fixed21 to the preserved gate; metadata only, no admission or claim."""
import copy,hashlib,json
from pathlib import Path
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;O=F/'real-data-pilot-final20-2026-10-08';B=F/'real-data-pilot-retry21-registration01-2026-10-08';V=F/'real-data-pilot-owner-policy-review01-2026-10-08';HELP=F/'real-data-pilot-fixed21-metadata-successor01-2026-10-08'
OLD='eth-paper-real-data-end-to-end-resource-20261008-20';N='eth-paper-real-data-end-to-end-resource-20261008-21'
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def save(p,v):
 with p.open('xb') as f:f.write((json.dumps(v,indent=2,sort_keys=True)+'\n').encode())
g0=load(O/'gate03.json');g=copy.deepcopy(g0);e=copy.deepcopy(g0['experiments'][OLD]);files=set(e['source_files']);files.difference_update(str((O/n).relative_to(R)) for n in ['preflight03.py','root_io03.py','prepare07.py'])
files.update(str((H/n).relative_to(R)) for n in ['preflight01.py','root_io.py','prepare21_02.py','register21.py']);files.update(str((HELP/n).relative_to(R)) for n in ['successor04.py','DEPENDENCIES04.json','candidate/real_pilot_storage.py']);files.update(v['path'] for v in load(HELP/'DEPENDENCIES04.json').values());files.update(str((V/n).relative_to(R)) for n in ['SOURCE_REVIEW01.json','METADATA_IDENTITY_REVIEW01.json','EXTENSION92_REVIEW01.json']);files.update(str((B/n).relative_to(R)) for n in ['EXTENSION_PROPOSED92_01.json','CUMULATIVE_ALLOCATION_PROPOSED92_01.json']);e['source_files']={p:ref(R/p)['sha256'] for p in sorted(files)}
for role,v in load(H/'INPUT_REFS01.json').items():e['inputs'][role]={'dataset':'eth',**{k:v[k] for k in ['path','sha256']}}
e['inputs']['pair_policy']={'dataset':'eth',**{k:ref(H/'templates02/pair_policy01.json')[k] for k in ['path','sha256']}}
e['charter']={k:ref(H/'CHARTER01.md')[k] for k in ['path','sha256']};e['cumulative_budget_extension']={'extension':{k:ref(B/'EXTENSION_PROPOSED92_01.json')[k] for k in ['path','sha256']},'review':{k:ref(V/'EXTENSION92_REVIEW01.json')[k] for k in ['path','sha256']}}
e['question']='Measure the unchanged original-order1024-comparison real-scoring diagnostic after resource-owner metadata schema correction; preserve intentional incomplete outcome and original seven-full-graph MCM/GAT/attention LSTM pilot objective.';assert e['parent'] is None;g['experiments'][N]=e;assert g['families']==g0['families'] and all(g['experiments'][k]==v for k,v in g0['experiments'].items());save(H/'gate01.json',g);save(H/'ALL_INPUT_REFS01.json',e['inputs'])
b=load(O/'BINDING02.json');b['identity']=N
for role,name in [('gate','gate01.json'),('draft','INPUT_DRAFT01.json'),('preparation','PREPARATION_RESULT01.json'),('baseline','BASELINE01.json'),('transport_binding','TRANSPORT_BINDING01.json')]:b[role]=ref(H/name)
b['transport']=load(H/'INPUT_REFS01.json')['archive_transport'];b['owner_policy_source_review']=ref(V/'SOURCE_REVIEW01.json');b['metadata_identity_review']=ref(V/'METADATA_IDENTITY_REVIEW01.json');b['prior_outcome_review']=ref(F/'real-data-pilot-twentieth-outcome-review01-2026-10-08/OUTCOME_REVIEW01.json');b['prior_preservation_complete']=ref(F/'real-data-pilot-twentieth-failed-increment01-2026-10-08/FRESH_GIT_RECOVERY01.json');b['prior_recovery_review']=ref(V/'returned-failed20-recovery01/RECOVERY_REVIEW01.json');b['binding_review']=None;b['status']='DRAFT_NOT_RELEASED';save(H/'BINDING_DRAFT01.json',b)
save(H/'REGISTRATION_EXIT01.json',{'status':'DRAFT_NOT_ADMITTED','identity':N,'source_pins':len(files),'inputs':len(e['inputs']),'prior_experiments_preserved':len(g0['experiments']),'prospective_allowance':92,'claim':False,'launch':False})
print(json.dumps({'status':'DRAFT_NOT_ADMITTED','source_pins':len(files),'inputs':len(e['inputs'])}))

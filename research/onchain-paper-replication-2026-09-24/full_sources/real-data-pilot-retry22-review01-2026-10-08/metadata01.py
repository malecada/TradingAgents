import hashlib,json,subprocess,os
from pathlib import Path
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;N=F/'real-data-pilot-final22-2026-10-08';O=F/'real-data-pilot-final21-2026-10-08';ev={};checks=[]
def load(p):
 raw=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
def ck(n,v):
 assert v,n
 checks.append(n)
def renamed(x):return json.loads(json.dumps(x).replace('eth-paper-real-data-end-to-end-resource-20261008-21','eth-paper-real-data-end-to-end-resource-20261008-22').replace('ethpilot-20261008-21','ethpilot-20261008-22'))
x=load(N/'PREPARATION_EXIT01.json');d=load(N/'INPUT_DRAFT01.json');old=load(O/'INPUT_DRAFT01.json');p=load(N/'PREPARATION_RESULT01.json');op=load(O/'PREPARATION_RESULT01.json');base=load(N/'BASELINE01.json')
ck('draft_only',x['status']==p['status']=='DRAFT_NOT_REGISTERED_NOT_ADMITTED' and p['independent_approval'] is False and x['claim']==x['launch']==x['reservation']==False)
ck('scratch_explicit_pending',x['incremental_explicit_annealing_scratch_bytes']==262144 and x['scratch_registration_complete'] is False)
ck('original7graphs',d['graphs']==old['graphs'] and len(d['graphs'])==7)
newpair=load(N/'templates01/pair_policy01.json');oldpair=load(O/'templates02/pair_policy01.json');ns=newpair.pop('numerical_source');prior=oldpair.pop('numerical_source');ck('pair_method_unchanged',newpair==oldpair);ck('181same_source_names',set(ns['files'])==set(prior['files']) and len(ns['files'])==181 and ns['commit']==x['source_anchor']=='df37a86be364a5e52b1ec6a0914bcc3ad9271e8e')
request=('\n'.join(ns['commit']+':'+path for path in ns['files'])+'\n').encode();env=dict(os.environ,GIT_NO_LAZY_FETCH='1');raw=subprocess.run(['git','cat-file','--batch'],input=request,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,env=env).stdout;offset=0
for path,pin in ns['files'].items():
 end=raw.index(b'\n',offset);header=raw[offset:end].split();assert header[1]==b'blob';size=int(header[2]);offset=end+1;assert hashlib.sha256(raw[offset:offset+size]).hexdigest()==pin==hashlib.sha256((R/path).read_bytes()).hexdigest();offset+=size+1
ck('all181committed_and_installed_hashes',offset==len(raw))
changed={path:{'before':prior['files'][path],'after':pin} for path,pin in ns['files'].items() if pin!=prior['files'][path]};ck('changed_source_list_exact',changed==x['changed_source_pins'])
for name in ('job_template01.json','pilot.json','archive_policy.json','producer_plan.json'):
 a=renamed(load(O/'templates02'/name));b=load(N/'templates01'/name)
 if name=='job_template01.json':next(iter(a['payload']['representation_jobs'].values()))['descriptor']['pair_execution']['policy_sha256']=ev[str((N/'templates01/pair_policy01.json').relative_to(R))]
 if name=='producer_plan.json':
  for v in a['producers'].values():v['descriptor']['pair_execution']['policy_sha256']=ev[str((N/'templates01/pair_policy01.json').relative_to(R))]
 ck('template_exact_'+name,a==b)
for key in p['inventory']:
 if key not in ('storage_budget_unchanged','total_with_declared_baseline'):ck('unchanged_inventory_'+key,p['inventory'][key]==op['inventory'][key])
ck('only_storage_identity',p['inventory']['storage_budget_unchanged']==renamed(op['inventory']['storage_budget_unchanged']))
ck('baseline_evidence',d['protocol']['physical_baseline']['evidence']['sha256']==ev[str((N/'BASELINE01.json').relative_to(R))])
for k,field in [('logical_bytes','logical_file_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries')]:ck('baseline_'+k,d['protocol']['physical_baseline'][k]==base['result']['observation'][field])
allowed={'pair_policy','execution_job','pilot','archive_policy','producer_plan'}
ck('other_references_unchanged',all(v==old['protocol']['references'][k] for k,v in d['protocol']['references'].items() if k not in allowed))
for role in allowed:
 ref=d['protocol']['references'][role];ck('template_reference_'+role,hashlib.sha256((R/ref['path']).read_bytes()).hexdigest()==ref['sha256'])
helper=F/'real-data-pilot-storage-metadata-binding01-2026-10-08/successor04.py';ck('accepted_helper_pin',hashlib.sha256(helper.read_bytes()).hexdigest()=='0ca47a98e80cae9441c3718cdff8b5b5436ab5ab1036734c830e094c77d2dfe5')
result={'decision':'accepted-metadata-draft-only','identity':x['identity'],'source_anchor':x['source_anchor'],'evidence':ev,'checks':checks,'unregistered_scratch_bytes':262144,'pending':['Exact additional annealing scratch registration in numerical/resource capacity declarations and corresponding independent check; unchanged current inventory is not scratch admission.','Actual fresh controls/inputs/transport binding, gate, source closure, budget adoption and final combined entry/binding/release review.','Fresh public commit/recovery of final entry before any authorized native attempt.'],'qualification':'Read-only source and metadata joins; generichelper genuine preparation receipt retained but not rerun. No numerical arrays/imports/admission/claim/launch. Original solver/model/training/native caps and unchanged inventory preserved; no whole-pilot capacity proof.'}
(H/'METADATA_REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'checks':len(checks),'sha256':hashlib.sha256((H/'METADATA_REVIEW01.json').read_bytes()).hexdigest()}))

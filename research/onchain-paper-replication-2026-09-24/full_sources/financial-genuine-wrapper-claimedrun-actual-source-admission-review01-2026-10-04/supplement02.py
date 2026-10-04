import datetime,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;N=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');O=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def census(root):
 rows=[]
 def scan(d,depth):
  check(depth<=32,'finite depth')
  for p in sorted(d.iterdir()):
   rel=p.relative_to(root).as_posix();check(not any(n in {'keys','apis','.env','hf_token.txt'} or n.startswith('.env.') for n in p.relative_to(root).parts),'no forbidden credential path');s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)}
   if stat.S_ISDIR(s.st_mode):r['kind']='directory'
   elif stat.S_ISREG(s.st_mode):
    check(s.st_size<=4194304,'bounded member '+rel);raw=p.read_bytes();r.update(kind='file',bytes=len(raw),sha256=sha(raw));after=p.lstat();check((s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_mode,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'stable opaque member '+rel)
   else:raise ValueError('unexpected source type '+rel)
   rows.append(r);check(len(rows)<=32768,'finite entries')
   if r['kind']=='directory':scan(p,depth+1)
 scan(root,0);return {'root_mode':stat.S_IMODE(root.lstat().st_mode),'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])}
original=census(O);frozen=load(B/'financial-genuine-wrapper-root-recordfix-failed-scope-capture01-2026-10-04/source-manifest.json');check(original==frozen,'entire original1011 current tree equals actual failed-scope capture');check(len(original['members'])==1011,'original1011typed');new=census(N);(H/'CURRENT_TREE02.json').write_text(json.dumps(new,sort_keys=True,indent=2)+'\n')
p=N/'fixture_inputs/financial_wrapper_claimedrun01';ch=load(p/'charter.json');oldg=load(O/'fixture_inputs/financial_wrapper_recordfix01/gates.json');pid='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';oldch=load(O/oldg['experiments'][pid]['charter']['path']);ID='financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01'
phases=[]
for row in oldch['phases']:
 r=dict(row);r['proposed_identity']=ID if r['proposed_identity']=='financial-wrapper-classification-eager-interrupt1-20261003-01' else r['proposed_identity'];r['proposed_dependencies']=[ID if x=='financial-wrapper-classification-eager-interrupt1-20261003-01' else x for x in r['proposed_dependencies']];phases.append(r)
check(ch['phases']==phases,'all18 phase fields unchanged except declared first identity and DAG references');check(ch['denominator']==oldch['denominator'],'complete phase counts unchanged');check(ch['resources']==oldch['resources'],'full native policy unchanged');check(ch['unexpected_failure_policy']==oldch['unexpected_failure_policy'],'unexpected failure halt unchanged');check(ch['continuation_requires']==oldch['continuation_requires'] and ch['prediction_requires']==oldch['prediction_requires'],'authentic failedcheckpoint and COMPLETE dependencies unchanged')
names={r['proposed_identity'] for r in phases};check(len(names)==18,'18distinct finite phases')
seen=set()
while len(seen)<len(names):
 ready={r['proposed_identity'] for r in phases if set(r['proposed_dependencies'])<=seen};check(bool(ready-seen),'acyclic closed finite DAG');seen|=ready
check(all(r['actual_claim_sha256'] is None and r['actual_outcome'] is None and r['paper_fit_credit']==0 for r in phases),'no planned phases coerced completed');runtime=load(p/'runtime_mapping.json')
for r in runtime['distribution_records']:check(sha(Path(r['record']).read_bytes())==r['record_sha256'],'actual unchanged RECORD '+r['name'])
check(len(runtime['distribution_records'])==251,'all251 RECORD metadata')
report={'decision':'ACTUAL_SOURCE_SUPPLEMENT_ACCEPTED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':len(checks),'check_names':checks,'original_complete_members':1011,'original_current_matches_frozen_failed_capture':True,'current_complete_members':len(new['members']),'current_regular_files':sum(r['kind']=='file' for r in new['members']),'current_total_regular_bytes':sum(r.get('bytes',0) for r in new['members']),'new_tree_not_external_recovery':True,'full18phase_DAG_and_resource_policy_preserved':True,'actual251_RECORD_metadata_unchanged':True,'source_only':True};(H/'SUPPLEMENT02.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='check_names'}))

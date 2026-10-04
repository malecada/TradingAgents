import hashlib,json,os,stat,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sys.path.insert(0,str(P));import recovery04 as R
S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');a=json.loads((D/'ACTUAL_ADMISSION01.json').read_bytes());before=json.loads((D/'SOURCE_BEFORE01.json').read_bytes());checks=[]
def ok(v,n):assert v,n;checks.append(n)
actual=[]
for p in S.rglob('*'):
 n=p.relative_to(S).as_posix()
 if n.split('/')[0]=='.git':continue
 s=p.lstat();r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 else:b=R.read(S,n);r.update(kind='file',bytes=len(b),sha256=R.digest(b))
 actual.append(r)
actual.sort(key=lambda x:x['path']);ok(actual==before['members']and stat.S_IMODE(S.stat().st_mode)==before['root_mode'],'whole non-Git capsule before-after admission unchanged')
for r in actual:checks.append('unchanged actual byte/mode/member '+r['path'])
claims=list((S/'research_runs').glob('*/claim.json'));ok(len(claims)==2,'no new claim from readonly admission')
for p in claims:
 failed=p.parent/'failed.json';ok(failed.is_file()and not(p.parent/'complete.json').exists(),'both original terminal failures preserved');c=json.loads(p.read_bytes());f=json.loads(failed.read_bytes());ok(f['claim_sha256']==R.digest(p.read_bytes()),'original failed claim body hash')
ok(max(json.loads(p.read_bytes())['effective_attempt_budget']for p in claims)==19,'highest actual prior budget remains19')
for p in (S/'research_runs'/a['experiment_id'],S/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/a['experiment_id']):ok(not os.path.lexists(p),'unused output/claim namespace remains absent')
env=dict(os.environ);env['GIT_NO_REPLACE_OBJECTS']='1';head=subprocess.run(['git','--no-replace-objects','-C',str(S),'rev-parse','HEAD'],env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10);ok(head.returncode==0 and not head.stderr and head.stdout.decode().strip()==a['source'],'actual Source HEAD after readonly call')
inputs=a['inputs'];training=json.loads(R.read(S,inputs['training']['path']));model=json.loads(R.read(S,inputs['model']['path']));closure=json.loads(R.read(S,inputs['source_closure']['path']));runtime=json.loads(R.read(S,inputs['runtime_mapping']['path']));ok(R.digest(R.read(S,inputs['model']['path']))=='20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d','original science model20f4');ok(R.digest(R.read(S,inputs['training']['path']))=='d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0','original trainingd527');ok(len(closure['installed'])==194 and sum(n.startswith('tradingagents/')for n in closure['installed'])==149,'unchanged194 implementation149package')
for n,h in closure['installed'].items():ok(R.digest(R.read(S,n))==h,'exact installed science closure '+n)
ok(len(runtime['distribution_records'])==251,'251 genuine runtime metadata pins')
(D/'POSTCHECK01.json').write_bytes(R.encode({'checks':len(checks),'checks_detail':checks,'original_training_configuration':training,'original_model_configuration':model,'whole_source_before_after_equal':True,'new_identity_reserved':False,'actual_calls_to_job_admitted':1,'genuine_ResearchRun_start_calls':0,'new_parent':None,'source_and_caller_external_recovery':None,'new_release':None}));print(json.dumps({'checks':len(checks),'whole_source_unchanged':True,'claims':2}))

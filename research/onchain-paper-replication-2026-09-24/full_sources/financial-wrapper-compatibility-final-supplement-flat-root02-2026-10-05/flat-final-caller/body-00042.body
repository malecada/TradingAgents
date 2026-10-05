"""Read-only exact actual baseline recovery checker. No helper entry or network.
Needs genuine Root actual receipt refs supplied after the operations; absence
refuses before any verdict. Outputs only in this new review directory.
"""
from pathlib import Path
import argparse,hashlib,json,os,stat,time,io,gzip,tarfile,sys,subprocess
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B.parents[2];D=B/'financial-wrapper-compatibility-baseline-root-remote02-2026-10-05';CAP=ROOT.parent/'onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source';PARENT=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
MAIN='d15e720ff6143350052b90c563ead1f950dd8be3';SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';FILE=4194304;START=time.monotonic();cache={};pins={};treepins={};count=0;total=0
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,msg):
 global count
 if not v:raise ValueError(msg)
 count+=1
sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p,pin=None):
 global total
 p=Path(p);s=p.lstat();ok(time.monotonic()-START<180 and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE,'bounded stable regular')
 if p not in cache:
  with p.open('rb') as f:b=f.read(FILE+1)
  ok(len(b)==s.st_size and sig(s)==sig(p.lstat()),'physical read stable');cache[p]=b;pins[p]=sig(s);total+=len(b);ok(total<=64*1024**2,'64MiB total audit bytes')
 else:ok(pins[p]==sig(s),'retained exact signature');b=cache[p]
 ok(pin is None or sha(b)==pin,'exact real body hash');return b
def j(p,pin=None):return json.loads(read(p,pin))
def ref(v):
 ok(type(v)is dict and set(v)=={'path','sha256'},'literal actual evidence ref');return read(Path(v['path']),v['sha256'])
def census(root,exclude=()):
 out={};todo=[root]
 while todo:
  p=todo.pop()
  with os.scandir(p) as it:
   for e in it:
    if p==root and e.name in exclude:continue
    s=e.stat(follow_symlinks=False);ok(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode),'whole ordinary population');n=str(Path(e.path).relative_to(root));out[n]=sig(s)
    if stat.S_ISDIR(s.st_mode):todo.append(Path(e.path))
 ok(len(out)<32768,'finite population');prior=treepins.get(root);ok(prior is None or prior==(tuple(exclude),out),'unchanged whole namespace');treepins[root]=(tuple(exclude),out);return out

parser=argparse.ArgumentParser();parser.add_argument('--tool-exit',required=True,type=Path);parser.add_argument('--tool-sha256',required=True);a=parser.parse_args();tool=j(a.tool_exit,a.tool_sha256)
rootexit=j(D/'ROOT_BASELINE_FLAT01_EXIT.json','b65514ed8470d0187968ec3d46a857a5298abf16642fe1827672ef7422a47248');intent=j(D/'ROOT_BASELINE_FLAT01_INTENT.json','d663b020e004836c3b73936bafe5e06456c848993cba4be3c5b4c1fce8b4b5b3');spawn=j(D/'ROOT_BASELINE_FLAT01_SPAWN.json','0420efd074638719fb8791f9cd574732bbd9a25fefe28c95d69d06a0d939565d');innerintent=j(D/'BUNDLE_FLAT_INTENT01.json','f0b209b6567bbe8401365787c8907e5d2d8b4d2b65e5636461b3c3b87598a818')
ok(rootexit['child_exit']==-9 and rootexit['parent_failure_type']=='ValueError' and rootexit['cleanup_failures']==[] and rootexit['actual_parent_exit'] is None and rootexit['parent_fsize_readback']==[FILE,FILE],'original bounded-watch failure and actual kill/reap disposition')
ok(tool['actual_exit']==1,'separate genuine actualRoot1')
q=j(D/'ROOT_REQUEST_FLAT01.json','ca196899877c4210c5900ce55ba5dc491551e8bf58a341b3752e6135fbc50c1a');contract=j(D/'FLAT_CONTRACT01.json','caf3f63b0b665eb241cd76c27dbd07e30ea6cfdf1d791abc06b2156080ae31b6');outer=read(D/'FLAT_ENTRY_RELEASE01.json','cde65727870cbf1d86ce59a0dc7a3a393980d5c836fc9fff86392c270dc5ea91');ok(outer==read(H/'OUTER_FLAT_RELEASE01.json'),'actual literal authored outer release');ok(read(D/'INNER_FLAT_RELEASE01.json','ca25c4dcfe07e9c8c55c7b70e213d5b68855cf6d45e4f3c12ec3aa9e1c457160')==read(H/'INNER_FLAT_RELEASE01.json'),'actual literal authored inner release')
ok(intent['contract_sha256']==sha(read(D/'FLAT_CONTRACT01.json')) and intent['entry_release_sha256']==sha(outer) and intent['argv']==spawn['argv'] and innerintent['request_sha256']==sha(read(D/'ROOT_REQUEST_FLAT01.json')) and innerintent['new_claim'] is False,'actual invocation and inner intent')
for n,h in contract['helpers'].items():read(D/n,h)
read(D/'caller02.py','13548eb3206febfb13e1dff0d5f63159176fb8ba1dae819f8de89b9a499cb8b7');ok(read(D/'ROOT_BASELINE_FLAT01.stderr')==read(D/'ROOT_BASELINE_FLAT01.stdout')==b'','child stdout stderr empty; outer error is separate tool evidence')
remote=j(D/'REMOTE_RECOVERY01.json','304745e0fb0774935e154377b05c97dcc263b6ab52e689652995b93c272f233b');old=j(H/'REMOTE_READBACK01.json','d697507dbda8e7bb4411dc5d70e74874a3c30540ea2a91fb853eaaff18648aca');read(D/'ROOT_TOOL_EXIT_REMOTE01.json',old['actual_root_tool_exit_sha256']);selection=j(D/'SELECTED_BODIES01.json','74a24e7007ff058a1c14ef4d9034af9a7b1c1889b0ee60e403cf5539f2218bb6');profile=j(D/'SELECTED_MODE_PROFILE01.json','edd63f3ef43ba205eab3141e2947a2b82e46edcee1038d2138b706e7c5d7cc3d')
sys.path.insert(0,str(D/'utilities'));sys.path.insert(0,str(D));import recovery_pax01 as R;import watch01 as W
ok(R.scan(D/'selected')==profile['full_manifest'],'all complete remote selected body/mode population unchanged')
for row in remote['selected_blobs']:
 body=read(D/'selected'/row['path'],row['sha256']);ok(len(body)==row['bytes'] and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==row['git_object'],'all44 retained actual remote body/OIDs')
missing_receipts=['BUNDLE_FLAT_RECOVERY01.json','BUNDLE_FLAT_FAILED01.json','flat-baseline/body-metadata.json','flat-population-review','flat-source-parent04'];ok(all(not os.path.lexists(D/n) for n in missing_receipts),'exact absent outcome and later scopes')
bundle=q['bundles'][0];m=j(D/'selected'/bundle['manifest']['path'],bundle['manifest']['sha256']);rows=[r for r in m['members'] if r['kind']=='file'];root=D/'flat-baseline';names=sorted(census(root));ok(names==['body-'+str(i).zfill(5)+'.body' for i in range(169)],'exact retained ordered partial169body namespace');ok(stat.S_IMODE(root.stat().st_mode)==0o700,'partialroot private0700')
retained=[]
for i,n in enumerate(names):
 body=read(root/n,rows[i]['sha256']);ok(len(body)==rows[i]['bytes'] and stat.S_IMODE((root/n).stat().st_mode)==0o600,'each retained complete opaque body/private600');retained.append({'leaf':n,'original_path':rows[i]['path'],'bytes':len(body),'sha256':sha(body),'physical_mode':0o600,'original_mode':rows[i]['mode']})
ok(sum(x['bytes'] for x in retained)==6448784,'retained literal byte count')
missing={q['bundles'][0]['name']:[r['path'] for r in rows[169:]]}
for b in q['bundles'][1:]:mm=j(D/'selected'/b['manifest']['path'],b['manifest']['sha256']);missing[b['name']]=[r['path'] for r in mm['members'] if r['kind']=='file']
ok([len(missing[b['name']]) for b in q['bundles']]==[93,14,47],'all154 unavailable body cells retained explicitly')
pids=sorted(set(old['recorded_pids_currently_absent'])|{intent['parent_pid'],spawn['pid']})
for pid in pids:ok(not Path('/proc',str(pid)).exists(),'all recorded original processes now absent')
try:os.killpg(spawn['pid'],0)
except ProcessLookupError:pass
else:raise ValueError('actual child session/process group remains')
for s in rootexit['observations']:ok(0<=s['logical_bytes']<=64*1024**2 and 0<=s['allocated_bytes']<=96*1024**2 and s['seconds']<5,'only actual complete recorded samples within caps')
# Full final receiver census, including retained failed publication and opaque Git files.
rootrows=census(D);physical=[]
for n,signature in sorted(rootrows.items()):
 p=D/n;s=p.lstat();row={'path':n,'kind':'directory' if stat.S_ISDIR(s.st_mode) else 'file','mode':stat.S_IMODE(s.st_mode),'allocated_bytes':s.st_blocks*512}
 if row['kind']=='file':body=read(p);row.update(bytes=len(body),sha256=sha(body))
 physical.append(row)
now=W.census(D);v=os.statvfs(D);free=v.f_bavail*v.f_frsize;ok(free>=10*1024**3,'current actual floor')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='');head=subprocess.run(['git','rev-parse','HEAD'],cwd=CAP,env=env,check=True,capture_output=True,timeout=10).stdout.decode().strip();ok(head==SOURCE,'source32d unchanged by archival failure')
claimpins={'financial-wrapper-classification-eager-complete100-20261003-01':('2e3bbbbf786f784eadb18bc3cdfea68905610ae773bbbd748ea1b2666b9e61f1','abdaef6f01bd02614782e442e2c102c38faa57e76061cba43b69960f3e389fa6'),'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01':('d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b','4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558'),'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01':('4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450')}
ok({x.name for x in (CAP/'research_runs').iterdir() if x.is_dir()}==set(claimpins),'exactthree genuine claims/no archival newclaim')
for name,(c,f) in claimpins.items():claim=j(CAP/'research_runs'/name/'claim.json',c);failed=j(CAP/'research_runs'/name/'failed.json',f);ok(failed['claim_sha256']==c and failed['status']=='failed' and claim['effective_attempt_budget'] in (18,19),'original spent failures unchanged')
for root,(exclude,_) in list(treepins.items()):census(root,exclude)
for p,s in pins.items():ok(sig(p.lstat())==s,'final stable original/captured read signatures')
result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_BASELINE_REMOTE_AND_FAILED_FLAT_CLOSURE_ONLY','reviewer':'combined_worker_review','actual_remote_sha256':sha(read(D/'REMOTE_RECOVERY01.json')),'flat_original_exit_sha256':sha(read(D/'ROOT_BASELINE_FLAT01_EXIT.json')),'actual_flat_tool_exit':{'path':str(a.tool_exit),'sha256':a.tool_sha256},'original_parent_exit':None,'actual_root_exit':1,'actual_child_exit':-9,'actual_cleanup_failures':[],'checks':count,'files_read':len(cache),'bytes_read':total,'elapsed_seconds':time.monotonic()-START,'retained_regular_files':169,'retained_regular_bytes':6448784,'missing_regular_files':154,'missing_receipts_or_scopes':missing_receipts,'completed_flat_scopes':0,'full_recovery_proof':None,'partial_body_mapping':retained,'missing_body_mapping':missing,'current_receiver_manifest':{'root_mode':stat.S_IMODE(D.stat().st_mode),'members':physical},'current_storage':now,'current_free_bytes':free,'current_recorded_pids_absent':pids,'current_actual_child_process_group_absent':True,'historical_parent_process_group':None,'historical_native_cgroup_path':None,'cgroup_qualification':'Ordinary archival caller creates a new child process session, not a systemd/native resource scope. No historical cgroup path/census was recorded. No unsupported cgroup absence inferred.','source':SOURCE,'actual_research_failed_claims':3,'actual_highest_claim_budget':19,'numerical_authority':False}
with (H/'FAILED_FLAT_READBACK01.json').open('x') as f:json.dump(result,f,sort_keys=True,separators=(',',':'));f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('partial_body_mapping','missing_body_mapping','current_receiver_manifest','current_recorded_pids_absent','current_storage')}))

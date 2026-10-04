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
p=argparse.ArgumentParser();p.add_argument('--actual-evidence',required=True,type=Path);a=p.parse_args();ev=j(a.actual_evidence)
required={'remote_receipt','remote_tool_exit','flat_tool_exit','flat_request','mode_profile','flat_contract','flat_entry_release','remote_entry_release'};ok(set(ev)==required,'all actual prerequisite refs, no null stand-ins')
for v in ev.values():ref(v)
freeze=j(D/'ROOT_BINDING_FREEZE01.json');selection=j(D/'SELECTED_BODIES01.json',freeze['selection_sha256']);baseq=j(D/'ROOT_REQUEST_BASELINE01.json',freeze['request_sha256']);remote=json.loads(ref(ev['remote_receipt']));flat=j(D/'BUNDLE_FLAT_RECOVERY01.json');q=json.loads(ref(ev['flat_request']))
ok(freeze['main_commit']==selection['remote_commit']==baseq['actual_main_commit']==MAIN and len(selection['rows'])==44 and sum(x['bytes'] for x in selection['rows'])==6089473,'fixed44/6089473/maincontext')
for n,h in freeze['helper_pins'].items():read(D/n,h)
read(D/'caller01.py',freeze['caller_sha256']);read(D/'recover01.py','37d9900097faa07b537085e45d84b24904bd11f39619f555acd758f787c457fa')
# Pure existing receipt validator only. NEVER caller.main/recover/restore/run.
sys.path.insert(0,str(D/'utilities'));sys.path.insert(0,str(D));import receipt01 as V
expected={x['path']:{'bytes':x['bytes'],'sha256':x['sha256']} for x in selection['rows']};V.validate_remote(remote,selection,freeze['selection_sha256'],expected)
ok(remote['fresh_git_root']==str(D/'fresh-compatibility-baseline02.git') and remote['expected_operations']==132 and remote['unique_selected_objects']==34,'actual132 operations/34unique exactreceiver')
selected=D/'selected';profile=json.loads(ref(ev['mode_profile']));ok(profile['actual_selected_root']==str(selected),'actual selected mode profile root');pm=profile['full_manifest'];pr={x['path']:x for x in pm['members']};ok(set(census(selected))==set(pr) and stat.S_IMODE(selected.stat().st_mode)==pm['root_mode'],'full actual selected namespace/modes')
for n,x in pr.items():ok(stat.S_IMODE((selected/n).lstat().st_mode)==x['mode'],'original selected literal mode')
for x in remote['selected_blobs']:
 b=read(selected/x['path'],x['sha256']);ok(len(b)==x['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['git_object'],'all44 actual GitOID bytejoins')
 foriginal=read(ROOT/x['path'],x['sha256']);ok(foriginal==b,'actual local selected original unchanged')
# Later request changes only genuinely supplied receipt/profile/restore-release refs.
allowed={'actual_remote_receipt','actual_selected_mode_profile','actual_restore_release'}
ok({k:v for k,v in q.items() if k not in allowed}=={k:v for k,v in baseq.items() if k not in allowed},'all immutable baseline request fields retained')
ok(flat['request_sha256']==ev['flat_request']['sha256'] and flat['status']=='BASELINE_BYTE_ARCHIVES_RECOVERED_REQUIRES_REVIEW' and flat['numerical_authority'] is False,'actual flat receipt identity')
for field,key in [('actual_remote_receipt','remote_receipt'),('actual_selected_mode_profile','mode_profile')]:z=q[field];ok(ROOT/z['path']==Path(ev[key]['path']) and z['sha256']==ev[key]['sha256'] and len(ref(ev[key]))==z['bytes'],'actual bound request/ref '+field)
for n in ['FAILED01.json','BUNDLE_FLAT_FAILED01.json']:ok(not os.path.lexists(D/n),'no failed disposition for accepted operation')
allpids=[];root_evidence=[]
for phase,key,contract_name,release_key in [('REMOTE','remote_tool_exit','REMOTE_CONTRACT01.json','remote_entry_release'),('FLAT','flat_tool_exit',None,'flat_entry_release')]:
 prefix='ROOT_BASELINE_'+phase+'01';exitrow=j(D/(prefix+'_EXIT.json'));intent=j(D/(prefix+'_INTENT.json'));spawn=j(D/(prefix+'_SPAWN.json'));rawout=read(D/(prefix+'.stdout'));rawerr=read(D/(prefix+'.stderr'));tool=json.loads(ref(ev[key]));contract=j(D/contract_name) if contract_name else json.loads(ref(ev['flat_contract']));release=json.loads(ref(ev[release_key]));contractsha=sha(read(D/contract_name)) if contract_name else ev['flat_contract']['sha256']
 ok(tool['actual_tool_exit']==0 and exitrow['child_exit']==0 and exitrow['parent_failure_type'] is None and exitrow['cleanup_failures']==[] and exitrow['actual_parent_exit'] is None and exitrow['parent_fsize_readback']==[FILE,FILE],'actual Root0 separate from original null/child0/cleanup')
 ok(contract['phase']==phase and contract['owned_root']==str(D) and contract['main_commit']==MAIN and intent['contract_sha256']==contractsha and intent['entry_release_sha256']==ev[release_key]['sha256'],'actual exact Root contract/intent')
 ok(release=={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_BASELINE_'+phase,'contract_sha256':contractsha,'caller_sha256':freeze['caller_sha256'],'numerical_authority':False},'genuine fixed one-use entry release')
 ok(spawn['argv']==intent['argv'] and rawerr==b'','actual command and empty stderr');allpids.extend([spawn['pid'],intent['parent_pid']]);root_evidence.append({'phase':phase,'tool':ev[key],'original_exit_sha256':sha(read(D/(prefix+'_EXIT.json'))),'stdout_sha256':sha(rawout),'stderr_sha256':sha(rawerr)})
 for sample in exitrow['observations']:ok(0<=sample['logical_bytes']<=64*1024**2 and 0<=sample['allocated_bytes']<=96*1024**2 and sample['free_bytes']>=10*1024**3 and sample['seconds']<5,'all actual outer finite whole-tree samples')
allpids.extend(x['pid'] for x in remote['operations'])
for pid in set(allpids):
 ok(type(pid)is int and pid>0 and not Path('/proc',str(pid)).exists(),'recorded PID currently absent')
 try:os.killpg(pid,0)
 except ProcessLookupError:pass
 else:raise ValueError('recorded process group still present')
# Independent complete canonical comparison for all three actual flat scopes.
restored={};scope_stats=[]
for bundle in q['bundles']:
 name=bundle['name'];rec=flat['scopes'][name];manifest=json.loads(read(selected/bundle['manifest']['path'],bundle['manifest']['sha256']));archive=read(selected/bundle['archive']['path'],bundle['archive']['sha256']);root=D/('flat-'+name);ok(stat.S_IMODE(root.lstat().st_mode)==0o700 and stat.S_IMODE((root/rec['metadata_file']).lstat().st_mode)==0o600,'private actual flat directory/metadata');metadata=j(root/rec['metadata_file'],rec['metadata_sha256']);ok(metadata['manifest']==manifest,'actual full flat mode metadata');files={x['path']:x for x in manifest['members'] if x['kind']=='file'};mapping=metadata['flat_members'];ok(set(files)==set(mapping) and len(set(mapping.values()))==len(files) and set(census(root))==set(mapping.values())|{rec['metadata_file']},'actual complete bijective private flat scope');bodies={};buf=io.BytesIO()
 with tarfile.open(fileobj=buf,mode='w',format=tarfile.USTAR_FORMAT) as tar:
  for x in manifest['members']:
   info=tarfile.TarInfo(x['path']+('/' if x['kind']=='directory' else ''));info.mode=x['mode'];info.uid=info.gid=info.mtime=0;info.uname=info.gname=''
   if x['kind']=='directory':info.type=tarfile.DIRTYPE;tar.addfile(info)
   else:
    leaf=mapping[x['path']];ok(Path(leaf).name==leaf and stat.S_IMODE((root/leaf).stat().st_mode)==0o600,'flat single private leaf');body=read(root/leaf,x['sha256']);ok(len(body)==x['bytes'],'actual full flat body extent');bodies[x['path']]=body;info.size=len(body);tar.addfile(info,io.BytesIO(body))
 ok(gzip.compress(buf.getvalue(),mtime=0)==archive,'complete canonical archive from actual flat bodies');restored[name]=bodies;scope_stats.append({'name':name,'files':len(bodies),'typed':len(manifest['members']),'archive_sha256':sha(archive),'metadata_sha256':rec['metadata_sha256']})
ok([(x['files'],x['typed']) for x in scope_stats]==[(262,303),(14,16),(47,55)],'exact three wholearchive denominators')
base=restored['baseline'];delta=restored['source-parent04'];ok(all(base['delta04/snapshot/'+n]==b for n,b in delta.items()),'redundant full captured delta body agreement')
# Literal original provenance is carried as metadata; physical flat files stay private.
origins=json.loads(base['ORIGINAL_ORIGINS01.json']);scopes=json.loads(base['ORIGINAL_SCOPES01.json'])
ok(len(origins)==260 and len(scopes)==8,'full original origin and closed-scope denominators')
for row in origins:
 body=base[row['archive_path']];ok(len(body)==row['bytes'] and sha(body)==row['sha256'],'every recovered literal original body')
 original=Path(row['original_path']);ok(stat.S_IMODE(original.lstat().st_mode)==row['original_mode'] and read(original,row['sha256'])==body,'genuine current original body/mode origin')
for name,scope in scopes.items():
 root=Path(scope['root']);members={x['path']:x for x in scope['members']};ok(stat.S_IMODE(root.lstat().st_mode)==scope['original_root_mode'] and set(census(root))==set(members),'full original closed scope incl empty directories')
 for n,row in members.items():
  ok(stat.S_IMODE((root/n).lstat().st_mode)==row['mode'],'original closed scope mode preserved')
  if row['kind']=='file':ok(len(base[name+'/'+n])==row['bytes'] and sha(base[name+'/'+n])==row['sha256'],'full recovered scope body mapping')
master=json.loads(delta['CAPSULE_MASTER605.json']);rows={x['path']:x for x in master['members']};ok(len(rows)==605 and set(census(CAP,('.git',)))==set(rows),'actual full605')
for n,x in rows.items():
 p=CAP/n;ok(stat.S_IMODE(p.lstat().st_mode)==x['mode'],'current original605 modes')
 if x['kind']=='file':ok(len(read(p,x['sha256']))==x['bytes'],'all current source bytes')
idx=json.loads(delta['SOURCE_GIT407_METADATA01.json']);ok(sha(delta['SOURCE_GIT407_METADATA01.json'])=='ce48d2c2c54f0beea47617b8da113020fe64e6b0fc86e6eb35a067bd558dc8e3','accepted immutable407 index')
for x in idx['objects']:
 if x['body_basis']!='accepted-original394-composition':b=delta[x['body_basis']];ok(sha(b)==x['sha256'] and hashlib.sha1(x['type'].encode()+b' '+str(len(b)).encode()+b'\0'+b).hexdigest()==x['oid'],'13 recovered new Gitframing')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='');head=subprocess.run(['git','rev-parse','HEAD'],cwd=CAP,env=env,check=True,capture_output=True,timeout=10).stdout.decode().strip();ok(head==SOURCE,'current Source unchanged')
parentfiles={n[7:]:b for n,b in delta.items() if n.startswith('parent/')};ok(len(parentfiles)==10,'ten actual Parentdraft bodies')
for n,b in parentfiles.items():ok(read(PARENT/n)==b,'exact actual Parentdraft bytes')
draft=json.loads(parentfiles['REQUEST_DRAFT01.json']);gate=j(CAP/draft['registration'],draft['registration_sha256']);experiment=gate['experiments'][draft['identity']]
ok(draft['source']==draft['design_source']==SOURCE and len(draft['source_files'])==354 and draft['source_files']==experiment['source_files'] and len(experiment['inputs'])==11 and experiment['parent'] is None,'actual355/354/11 independent reference context')
for n,h in draft['source_files'].items():read(CAP/n,h)
for role,row in experiment['inputs'].items():read(CAP/row['path'],row['sha256'])
tracked=subprocess.run(['git','ls-tree','-r','--full-tree',SOURCE],cwd=CAP,env=env,check=True,capture_output=True,timeout=10).stdout.decode().splitlines();ok(len(tracked)==355,'actual355 committed tracked source bodies')
for line in tracked:
 meta,n=line.split('\t');mode,kind,oid=meta.split();body=read(CAP/n);ok(kind=='blob' and mode in ('100644','100755') and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==oid,'every current committed source Git blob')
ok({line.split('\t')[1] for line in tracked}==set(draft['source_files'])|{draft['registration']},'self-gate is sole source-map exclusion')
failed_pins={
 'financial-wrapper-classification-eager-complete100-20261003-01':('2e3bbbbf786f784eadb18bc3cdfea68905610ae773bbbd748ea1b2666b9e61f1','abdaef6f01bd02614782e442e2c102c38faa57e76061cba43b69960f3e389fa6'),
 'financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01':('d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b','4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558'),
 'financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01':('4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450')}
ok({p.name for p in (CAP/'research_runs').iterdir() if p.is_dir()}==set(failed_pins),'only three genuine failed claims')
budgets=[]
for name,(claim_hash,failed_hash) in failed_pins.items():
 claim=j(CAP/'research_runs'/name/'claim.json',claim_hash);failed=j(CAP/'research_runs'/name/'failed.json',failed_hash);ok(failed['status']=='failed' and failed['claim_sha256']==claim_hash and claim['experiment_id']==failed['experiment_id']==name,'original failed identities and claim joins');budgets.append(claim['effective_attempt_budget'])
ok(sorted(budgets)==[18,19,19] and not os.path.lexists(CAP/'research_runs'/draft['identity']),'highest actual19 and unused reference remain unchanged')
ok(sha(base['bridge/SOURCE_INPUT_RUNTIME_PROOF01.json'])=='ac1ed8a157d7ec113ebe1a8e2eb71a917f46572d0cc8b035c1ee850d9b10730c' and sha(base['coalesced/ORIGINAL_RECOVERY_PROOF01.json'])=='c5cf38d2a54682e9b36c0d4462cc07a611fb047cc422803b23d590552511b7a5','genuine metadata proof and original full589394 basis')
pop=json.loads(base['capture-review/MACHINE01.json']);ok(pop['current_members']==605 and pop['logical_git_objects']==407,'previous fullpopulation proof reused')
old=j(ROOT/baseq['accepted_basis_byte_review']['path'],baseq['accepted_basis_byte_review']['sha256']);ok(old['decision']=='ACCEPTED_ACTUAL_OPERATIONAL_SOURCE_POLICY_BYTE_RECOVERY','genuine old actualcomplete BYTE basis')
for root,(exclude,_) in list(treepins.items()):census(root,exclude)
for p,s in pins.items():ok(sig(p.lstat())==s,'final current read fingerprints')
result={'schema_version':1,'status':'ACTUAL_BASELINE_RECEIPTS_AND_FULL_FLAT_BYTES_VERIFIED_PENDING_AUTHORED_PROOF','checks':count,'files_read':len(cache),'bytes_read':total,'elapsed_seconds':time.monotonic()-START,'actual_evidence':ev,'main_commit':MAIN,'source':SOURCE,'selected_count':44,'selected_bytes':6089473,'operations':132,'unique_objects':34,'scopes':scope_stats,'current_members':605,'current_files':491,'reachable_git':407,'basis589394_reused':True,'parent_draft_files':10,'source_tracked':355,'source_pins':354,'input_roles':11,'actual_failed_claims':3,'highest_actual_claim_budget':19,'root_exits':root_evidence,'recorded_pids_currently_absent':sorted(set(allpids)),'future_final_request_release_proofs_excluded':True,'numerical_authority':False}
with (H/'ACTUAL_READBACK01.json').open('x') as f:f.write(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('actual_evidence','root_exits','recorded_pids_currently_absent')}))

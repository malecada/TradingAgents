"""Read-only exact actual final-supplement recovery checker. No helper entry or network.
Needs genuine Root actual receipt refs supplied after the operations; absence
refuses before any verdict. Outputs only in this new review directory.
"""
from pathlib import Path
import argparse,hashlib,json,os,stat,time,io,gzip,tarfile,sys,subprocess
H=Path(__file__).resolve().parent;B=H.parent;ROOT=B.parents[2];D=B/'financial-wrapper-compatibility-final-supplement-root02-2026-10-05';CAP=ROOT.parent/'onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source';PARENT=CAP.parent.parent/'genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01'
F=B/'financial-wrapper-compatibility-final-supplement-flat-root02-2026-10-05';PREV=B/'financial-wrapper-compatibility-baseline-recovery-review02-2026-10-05'
MAIN='fc5af68f3f0dce82390c17ce15ab5e14c997c279';SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41';FILE=4194304;START=time.monotonic();cache={};pins={};treepins={};count=0;total=0
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

# Genuine actual evidence is supplied only after both Root operations terminate.
p=argparse.ArgumentParser();p.add_argument('--actual-pins',required=True,type=Path);a=p.parse_args();ev=j(a.actual_pins)
required={'remote_receipt','remote_exit','remote_tool_exit','remote_contract','remote_entry','source_entry_review','flat_receipt','flat_exit','flat_tool_exit','flat_request','flat_contract','flat_entry','inner_release','mode_profile'}
ok(set(ev)==required,'complete actual-only evidence refs')
for v in ev.values():ref(v)
remote=json.loads(ref(ev['remote_receipt']));flat=json.loads(ref(ev['flat_receipt']));q=json.loads(ref(ev['flat_request']));profile=json.loads(ref(ev['mode_profile']));peer=json.loads(ref(ev['source_entry_review']))
freeze=j(D/'ROOT_BINDING_FREEZE01.json','56114c1c93187ea4d2d13564201d4ea334504a16697563a08cb2eda7f5095abd');selection=j(D/'SELECTED_BODIES01.json',freeze['selection']);baseq=j(D/'ROOT_REQUEST_FINAL_SUPPLEMENT01.json',freeze['request'])
read(D/'recover01.py',freeze['generated_receiver']);ok(selection['remote_commit']==MAIN and len(selection['rows'])==15 and sum(r['bytes'] for r in selection['rows'])==486217,'fixed exact15-body external selection')
for root,key in [(D,'remote_contract'),(F,'flat_contract')]:
 c=json.loads(ref(ev[key]));ok(c['owned_root']==str(root) and c['main_commit']==MAIN and c['numerical_authority'] is False,'actual exact Root contract')
 for n,h in c['helpers'].items():read(root/n,h)
# Pure recorded-receipt validator only; never invoke an operational entry.
sys.path.insert(0,str(D/'utilities'));sys.path.insert(0,str(D));import receipt01 as V;import recovery_pax01 as R
required_bodies={r['path']:{'bytes':r['bytes'],'sha256':r['sha256']} for r in selection['rows']};V.validate_remote(remote,selection,freeze['selection'],required_bodies)
ok(remote['fresh_git_root']==str(D/'fresh-compatibility-final-supplement02.git'),'actual receiver namespace')
selected=D/'selected';ok(profile['actual_selected_root']==str(selected) and R.scan(selected)==profile['full_manifest'],'all actual input modes/full population');census(selected)
for row in remote['selected_blobs']:
 data=read(selected/row['path'],row['sha256']);ok(len(data)==row['bytes'] and hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_object'],'actual selected GitOID and body')
allowed={'actual_remote_receipt','actual_selected_mode_profile','actual_restore_release'};ok({k:v for k,v in q.items() if k not in allowed}=={k:v for k,v in baseq.items() if k not in allowed},'immutable final-supplement request scope')
for k,e in [('actual_remote_receipt','remote_receipt'),('actual_selected_mode_profile','mode_profile'),('actual_restore_release','inner_release')]:r=q[k];ok(ROOT/r['path']==Path(ev[e]['path']) and r['sha256']==ev[e]['sha256'] and len(ref(ev[e]))==r['bytes'],'actual bound ref '+k)
ok(q['round']=='FINAL_SUPPLEMENT' and flat['status']=='FINAL_SUPPLEMENT_BYTE_ARCHIVES_RECOVERED_REQUIRES_REVIEW' and flat['request_sha256']==ev['flat_request']['sha256'] and flat['numerical_authority'] is False and flat['POSIX'] is False and flat['installed_runtime_bodies'] is False,'actual final flat disposition')
ok(peer['decision']=='ACCEPTED_EXACT_ONE_USE_FINAL_SUPPLEMENT_FLAT' and peer['numerical_authority'] is False and peer['actual_remote_sha256']==ev['remote_receipt']['sha256'],'genuine distinct-author entry review')
inner=json.loads(ref(ev['inner_release']));ok(inner=={'schema_version':1,'decision':'ACCEPTED_EXACT_FINAL_SUPPLEMENT_BUNDLE_FLAT','contract_sha256':sha(R.encode({k:v for k,v in q.items() if k!='actual_restore_release'})),'remote_sha256':ev['remote_receipt']['sha256'],'source_sha256':sha(read(F/'restore_bundle01.py'))},'exact inner restore release equation')
pids=[];groups=[];terminals=[]
for phase,root,prefix in [('remote',D,'ROOT_FINAL_SUPPLEMENT_REMOTE02'),('flat',F,'ROOT_FINAL_SUPPLEMENT_FLAT02')]:
 # Names must match the actual accepted caller and are finalized from real receipts.
 exitrow=json.loads(ref(ev[phase+'_exit']));tool=json.loads(ref(ev[phase+'_tool_exit']));contract=json.loads(ref(ev[phase+'_contract']));release=json.loads(ref(ev[phase+'_entry']));intent=j(root/(prefix+'_INTENT.json'));spawn=j(root/(prefix+'_SPAWN.json'))
 caller=root/('caller_remote01.py' if phase=='remote' else 'caller_flat01.py');callerhash=sha(read(caller,freeze['receiver_caller' if phase=='remote' else 'flat_caller']))
 ok(release=={'schema_version':1,'decision':'ACCEPTED_EXACT_ONE_USE_FINAL_SUPPLEMENT_'+phase.upper(),'contract_sha256':ev[phase+'_contract']['sha256'],'caller_sha256':callerhash,'numerical_authority':False},'exact outer one-use release equation')
 groups.append(spawn['pid'])
 ok(exitrow['child_exit']==0 and exitrow['parent_failure_type'] is None and exitrow['cleanup_failures']==[] and exitrow['actual_parent_exit'] is None and tool['actual_root_exit']==0,'actual clean child and separate Root0, null preserved')
 ok(exitrow['parent_fsize_readback']==[FILE,FILE] and intent['contract_sha256']==ev[phase+'_contract']['sha256'] and intent['entry_release_sha256']==ev[phase+'_entry']['sha256'] and spawn['argv']==intent['argv'],'actual exact released command/limits')
 ok(read(root/(prefix+'.stderr'))==b'','actual child stderr empty');read(root/(prefix+'.stdout'));pids.extend([intent['parent_pid'],spawn['pid']])
 for sample in exitrow['observations']:ok(sample['logical_bytes']<=64*1024**2 and sample['allocated_bytes']<=96*1024**2 and sample['seconds']<5,'actual finite complete sampled bounds')
 terminals.append({'phase':phase,'original_parent_exit':None,'actual_root_exit':0,'child_exit':0,'elapsed_seconds':exitrow['elapsed_seconds'],'observations':len(exitrow['observations'])})
for pid in pids+[r['pid'] for r in remote['operations']]:ok(not Path('/proc',str(pid)).exists(),'recorded PID currently absent')
for pg in groups+[r['pid'] for r in remote['operations']]:
 try:os.killpg(pg,0)
 except ProcessLookupError:ok(True,'recorded child process group absent')
 else:raise ValueError('recorded child process group remains')
ok(not os.path.lexists(D/'FAILED01.json') and not os.path.lexists(F/'BUNDLE_FLAT_FAILED01.json'),'no actual failed disposition')
bundle=q['bundles'][0];ok(bundle['name']=='final-caller' and len(q['bundles'])==1,'one exact final scope');manifest=j(selected/bundle['manifest']['path'],'51d4ab006ccbef80c879d45a03bf079a6be24899a5655fca8a4e79652c83b537');archive=read(selected/bundle['archive']['path'],'b8d36136e2ba42bf8015fea33cc363d5ae0c61bfbb2b9c1a174e1dc5f5203fd0');capture=j(selected/bundle['capture']['path'],'71aeb0afdd1f8dc72c650905e67a99b6f56daf98bf4f314b28320cde5407f831')
rec=flat['scopes']['final-caller'];out=F/'flat-final-caller';meta=j(out/rec['metadata_file'],rec['metadata_sha256']);files={r['path']:r for r in manifest['members'] if r['kind']=='file'};mapping=meta['flat_members'];ok(meta['manifest']==manifest and len(files)==106 and len(manifest['members'])==121 and set(files)==set(mapping) and len(set(mapping.values()))==106 and set(census(out))==set(mapping.values())|{rec['metadata_file']},'all106 actual bodies/121typed/mapping+metadata')
ok(stat.S_IMODE(out.stat().st_mode)==0o700 and stat.S_IMODE((out/rec['metadata_file']).stat().st_mode)==0o600,'private actual flat metadata/root');bodies={};buf=io.BytesIO()
with gzip.GzipFile(filename='',mode='wb',fileobj=buf,mtime=0) as gz:
 with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
  for row in manifest['members']:
   t=tarfile.TarInfo(row['path']);t.mode=row['mode'];t.uid=t.gid=t.mtime=0;t.uname=t.gname=''
   if row['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
   else:
    n=mapping[row['path']];ok(Path(n).name==n and stat.S_IMODE((out/n).stat().st_mode)==0o600,'private single flat leaf');body=read(out/n,row['sha256']);ok(len(body)==row['bytes'],'actual extent');bodies[row['path']]=body;t.size=len(body);tar.addfile(t,io.BytesIO(body))
ok(buf.getvalue()==archive,'whole actual recovered PAX canonical header/body/footer/gzip equality')
orig=json.loads(bodies['ORIGINS01.json']);ok(len(orig['origins'])==105,'complete105origins plus original-metadata table')
for row in orig['origins']:
 b=bodies[row['snapshot_path']];p=Path(row['original_path']);ok(sha(b)==row['sha256'] and len(b)==row['bytes'] and read(p,row['sha256'])==b and stat.S_IMODE(p.stat().st_mode)==row['original_mode'],'every literal current origin body/mode')
for scope,desc in orig['original_typed_scopes'].items():
 scope_origins=[r for r in orig['origins'] if r['snapshot_path'].startswith(scope+'/')];roots={Path(r['original_path']).parents[len(Path(r['snapshot_path']).parts)-2] for r in scope_origins};ok(len(roots)==1,'exact original scoped origin root');root=roots.pop();rows={r['path']:r for r in desc['members']};ok(stat.S_IMODE(root.stat().st_mode)==desc['root_mode'] and set(census(root))==set(rows),'full closed original scope population/root mode')
 for n,row in rows.items():
  ok(stat.S_IMODE((root/n).stat().st_mode)==row['mode'],'original scope modes')
  if row['kind']=='file':ok(sha(bodies[scope+'/'+n])==row['sha256'],'whole scoped original body')
parents={n[7:]:b for n,b in bodies.items() if n.startswith('parent/')};ok(len(parents)==12 and set(census(PARENT))==set(parents),'complete current final Parent12')
for n,b in parents.items():ok(read(PARENT/n)==b,'actual final Parent byte join')
finalq=json.loads(parents['REQUEST_FINAL01.json']);ok(sha(parents['REQUEST_FINAL01.json'])=='cfecfd3e12d81628b9bc6f10171dd0345ac6e62c5481edccab64e5207254e03d' and finalq['source']==finalq['design_source']==SOURCE,'exact actual source/final request')
proofs={k:sha(bodies['proofs/'+k+'.body']) for k in finalq['proofs']}
for k,r in finalq['proofs'].items():ok(read(Path(r['path']),r['sha256'])==bodies['proofs/'+k+'.body'] and proofs[k]==r['sha256'],'all actual final proof bodies')
releasebody=bodies['parent-review/FINAL_PARENT_RELEASE01.json'];release=json.loads(releasebody);ok(sha(releasebody)=='6fd92ad26db2136812db00c8302f99b639a1d24ff8202dd9c2c610f16629f86a' and read(Path(finalq['final_review']['path']),finalq['final_review']['sha256'])==releasebody,'genuine unchanged final release')
ok(release=={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':sha(R.encode({k:v for k,v in finalq.items() if k!='final_review'})),'proof_sha256':proofs,'identity':finalq['identity'],'source':SOURCE,'caller_sha256':finalq['caller_sha256']},'original genuine Parent final-release equation')
ok(proofs['full_recovery']=='02900ae11c7053a5f691ef2838fa7427b5befd86778331c19b97143e1c6c2e48' and sha(bodies['baseline-review/MACHINE01.json'])=='25d187e0b440cce9e61f0d2b2cde8c31953d16644572e33b746de992bd3dbc5e','accepted605/407 baseline reused, not rescanned')
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_ALLOW_PROTOCOL='');head=subprocess.run(['git','rev-parse','HEAD'],cwd=CAP,env=env,check=True,capture_output=True,timeout=10).stdout.decode().strip();ok(head==SOURCE and not os.path.lexists(CAP/'research_runs'/finalq['identity']),'source unchanged and reference still unclaimed')
ok(len([p for p in (CAP/'research_runs').iterdir() if p.is_dir()])==3,'three original claims remain')
for root,(exclude,_) in list(treepins.items()):census(root,exclude)
for p,s in pins.items():ok(sig(p.lstat())==s,'final current byte/provenance signatures')
result={'schema_version':1,'status':'ACTUAL_FINAL_SUPPLEMENT_VERIFIED_PENDING_AUTHORED_PROOF','actual_evidence':ev,'source':SOURCE,'main_commit':MAIN,'files':106,'typed':121,'parent_files':12,'selected_files':15,'selected_bytes':486217,'actual_operations':len(remote['operations']),'checks':count,'files_read':len(cache),'bytes_read':total,'elapsed_seconds':time.monotonic()-START,'final_request_sha256':sha(parents['REQUEST_FINAL01.json']),'release_sha256':sha(releasebody),'baseline_proof_sha256':proofs['full_recovery'],'baseline_reused_without_rescan':True,'actual_final_receipt_sha256':ev['flat_receipt']['sha256'],'terminals':terminals,'numerical_authority':False}
with (H/'ACTUAL_READBACK01.json').open('x') as f:json.dump(result,f,sort_keys=True,separators=(',',':'));f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='actual_evidence'}))

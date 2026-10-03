"""Offline full opaque byte capture audit; no imports of research or arrays."""
import gzip,hashlib,io,json,os,pathlib,stat,subprocess,tarfile,time
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
P=BASE/'held-consumer-post-outcome-root-capture01-2026-10-03';B=P/'bundle01';OUT=pathlib.Path(__file__).resolve().parent
FILE=4*1024**2;H=lambda b:hashlib.sha256(b).hexdigest();checks=0
def ok(v,msg):
 global checks
 if not v:raise AssertionError(msg)
 checks+=1
def read(p):
 p=pathlib.Path(p);s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE,'read type/path/extent')
 ok(not any(x.lower() in {'keys','apis','.env','.ssh','hf_token.txt'} or x.lower().endswith(('.key','.pem')) for x in p.parts),'protected path')
 b=p.read_bytes();ok(len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns,'stable read');return b
def js(p):return json.loads(read(p))
def enc(x):return (json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
qraw=read(P/'REQUEST01.json');q=json.loads(qraw);cr=read(B/'capture.json');c=json.loads(cr)
ok(H(qraw)=='23cf258b1f49feff79802bdfe04d0c91563ed81c6e75dfbbab0e8983b260ffe6','request exact')
ok(H(cr)=='8dda0e91ea7e70c6164139a52d96b9c056befecac28e4d86f056eb3fc3312111' and c['request_sha256']==H(qraw),'capture exact')
ok(H(enc(q['baseline']))==q['baseline_sha256']=='660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061','original baseline')
def scan(root):
 rows=[];allocated=root.stat().st_blocks*512;logical=0
 def visit(p):
  nonlocal allocated,logical
  for child in sorted(p.iterdir()):
   st=child.lstat();rel=str(child.relative_to(root));ok(len(rows)<32768 and len(child.relative_to(root).parts)<=32 and child.resolve()==child and st.st_dev==root.stat().st_dev,'scan boundary')
   r={'path':rel,'mode':stat.S_IMODE(st.st_mode)};allocated+=st.st_blocks*512
   if stat.S_ISDIR(st.st_mode):r['kind']='directory';rows.append(r);visit(child)
   else:b=read(child);logical+=len(b);r.update(kind='file',bytes=len(b),sha256=H(b));rows.append(r)
 return_rows=None
 visit(root)
 return {'schema_version':1,'root_mode':stat.S_IMODE(root.stat().st_mode),'members':sorted(rows,key=lambda x:x['path'])},logical,allocated
summaries={};maps={};opaque={}
for kind in ('capsule','external'):
 root=pathlib.Path(q['baseline'][kind+'_root']);m=q['current_manifests'][kind];old=q['baseline'][kind+'_manifest'];maps[kind]={r['path']:r for r in m['members']}
 ok(H(enc(m))==q['current_manifest_sha256'][kind]==c['archives'][kind]['manifest_sha256'],'manifest canonical hash')
 ok(read(B/(kind+'-manifest.json'))==enc(m),'captured manifest bytes')
 ok(all(maps[kind].get(r['path'])==r for r in old['members']) and m['root_mode']==old['root_mode'],'original subset exact')
 got,logical,allocated=scan(root);ok(got==m,'full actual tree equal')
 archive=read(B/(kind+'.tar.gz'));ok(H(archive)==c['archives'][kind]['sha256'] and len(archive)==c['archives'][kind]['bytes'],'archive pin')
 original_order=[];bodies={}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
  for member in tar:
   ok(member.name in maps[kind] and member.name not in original_order,'exact unique archive member');original_order.append(member.name);r=maps[kind][member.name]
   ok(member.mode==r['mode'] and member.uid==member.gid==member.mtime==0 and member.uname==member.gname=='','canonical member attributes')
   ok(member.isdir() if r['kind']=='directory' else member.isreg(),'canonical member type')
   if r['kind']=='directory':ok(member.size==0,'directory size')
   else:
    ok(member.size==r['bytes']<=FILE,'body size');f=tar.extractfile(member);body=f.read(FILE+1);f.close();ok(len(body)==r['bytes'] and H(body)==r['sha256'],'opaque archive hash');bodies[member.name]=body
 ok(original_order==[r['path'] for r in m['members']],'complete archive order')
 output=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in m['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:t.size=r['bytes'];tar.addfile(t,io.BytesIO(bodies[r['path']]))
 ok(output.getvalue()==archive,'full canonical archive recompression')
 summaries[kind]={'members':len(m['members']),'regular_files':len(bodies),'logical_bytes':logical,'allocated_bytes':allocated,'archive_sha256':H(archive),'archive_bytes':len(archive),'baseline_members':len(old['members']),'canonical_recompression_exact':True};opaque[kind]=bodies
 ok(scan(root)[0]==m,'final full tree stability')
for category,prefix,pins in [('evidence','',c['evidence_sha256']),('support_bodies','support-',c['support_sha256'])]:
 for name,r in q[category].items():
  b=read(pathlib.Path(r['path']));ok(H(b)==r['sha256']==pins[name],'actual supporting origin pin');ok(read(B/(prefix+name+'.body'))==b,'captured support exact')
capture_terminal=js(P/'ACTUAL_CAPTURE_TERMINAL01.json');ok(capture_terminal['actual_exec_session']==86910 and capture_terminal['completion_tool']=='13403e' and capture_terminal['exit']==0 and capture_terminal['capture_sha256']==H(cr),'actual capture terminal')
ok(capture_terminal['actual_remote_or_flat_recovery'] is False,'no future recovery inferred')
cap=pathlib.Path(q['baseline']['capsule_root']);parent=pathlib.Path(q['baseline']['external_root']);identity=q['identity'];source=q['baseline']['source'];reg=js(cap/q['baseline']['registration']);exp=reg['experiments'][identity]
def git(*args):
 r=subprocess.run(['git','--no-optional-locks','-C',str(cap),*args],capture_output=True,timeout=30,check=True,env={**os.environ,'GIT_NO_REPLACE_OBJECTS':'1'});ok(len(r.stdout)<1024**2 and not r.stderr,'bounded offline Git');return r.stdout
ok(git('rev-parse','HEAD').decode().strip()==source,'actual current capsule source')
tree=git('ls-tree','-r','-z',source);objects={}
for part in tree.split(b'\0'):
 if part:
  info,name=part.split(b'\t');mode,kind,oid=info.decode().split();ok(kind=='blob','tracked blob');objects[name.decode()]=(mode,oid)
ok(len(objects)==246,'tracked246')
for name,(mode,oid) in objects.items():
 b=opaque['capsule'][name];ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'tracked actual archive blob OID');ok(mode==('100755' if maps['capsule'][name]['mode']&0o111 else '100644'),'tracked executable mode')
source_pins={**exp['source_files'],q['baseline']['registration']:q['baseline']['registration_sha256']};ok(len(source_pins)==205,'source-registration205')
for name,pin in source_pins.items():ok(H(opaque['capsule'][name])==pin and name in objects,'source-registration exact')
ok(len(exp['inputs'])==33,'registered inputs33')
for item in exp['inputs'].values():ok(H(opaque['capsule'][item['path']])==item['sha256'],'registered opaque input exact')
def body_json(kind,name):return json.loads(opaque[kind][name])
run='research_runs/'+identity;claim=body_json('capsule',run+'/claim.json');failed=body_json('capsule',run+'/failed.json')
ok(failed['claim_sha256']==H(opaque['capsule'][run+'/claim.json']) and failed['status']=='failed','actual failed claim join')
ok(claim['source']==source and claim['effective_attempt_budget']==6 and claim['inputs']==exp['inputs'],'actual source/allowance/input claim')
ok(run+'/complete.json' not in maps['capsule'],'complete absent')
for output,pin in failed['output_sha256'].items():ok(H(opaque['capsule'][run+'/outputs/'+output])==pin,'failed output denominator')
ledger=body_json('capsule',run+'/outputs/cell-ledger.json');ok([x['status'] for x in ledger]==['failed','unavailable'],'failed/unavailable cell dispositions')
guard='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+identity+'/guard/'
g=body_json('capsule',guard+'final.json');child=body_json('capsule',guard+'child_exit.json')
ok(g['child_exit_code'] is None and g['cleanup_verified'] is False,'original null false preserved')
root_terminal=js(B/'terminal.body');cleanup=js(B/'cleanup.body')
ok(root_terminal['actual_guard_final_sha256']==H(opaque['capsule'][guard+'final.json']) and root_terminal['actual_failed_run_sha256']==H(opaque['capsule'][run+'/failed.json']),'root actual receipts join')
ok(root_terminal['separate_actual_child_exit_code']==125 and root_terminal['actual_root_exit']==1 and root_terminal['native_result']=='timeout','original failed result')
ok(len(cleanup['actual_pid_absence'])==10 and all(cleanup['actual_pid_absence'].values()) and not pathlib.Path(cleanup['actual_cgroup']).exists(),'additive cleanup closed')
ok(all(not pathlib.Path('/proc',pid).exists() for pid in cleanup['actual_pid_absence']),'current exact ten PIDs absent')
hist=[]
for name in reg['experiments']:
 k='research_runs/'+name
 if k+'/claim.json' in maps['capsule']:
  cl=body_json('capsule',k+'/claim.json');fl=body_json('capsule',k+'/failed.json');ok(fl['claim_sha256']==H(opaque['capsule'][k+'/claim.json']) and k+'/complete.json' not in maps['capsule'],'historical original failed join');hist.append(name)
ok(len(hist)==5,'five actual failed claims')
dependent='original-import-held-publication-failure-20261003-01'
ok(not any(('research_runs/'+dependent) in n for n in maps['capsule']) and not any(('attempt/'+dependent) in n for n in maps['external']),'dependent absent')
ok(sum(x['logical_bytes'] for x in summaries.values())<128*1024**2 and sum(x['allocated_bytes'] for x in summaries.values())<128*1024**2,'whole supplied tree bounded')

# Additive exact actual remote and flat checks follow; prior capture audit is retained verbatim.
import shutil
REMOTE=BASE/'held-consumer-post-outcome-root-remote-recovery01-2026-10-03'
FLAT_PARENT=BASE/'held-consumer-post-outcome-root-flat-recovery01-2026-10-03';FLAT=FLAT_PARENT/'flat01'
COMMIT='a000e04f692d07d826fdc6cf1800b4818489f7e3';SELECTED=REMOTE/'selected';REPO=REMOTE/'fresh-post-outcome01.git'
selection_raw=read(REMOTE/'SELECTED_BODIES01.json');selection=json.loads(selection_raw)
ok(H(selection_raw)=='fd3dfaf31b0ce9e3498fdf8ccfb7723955e69ab8b1f80bde5c615601ff535fc1' and read(OUT/'SELECTION_BODY02.json')==selection_raw,'frozen accepted exact selection')
rr=read(REMOTE/'REMOTE_RECOVERY01.json');remote=json.loads(rr)
ok(H(rr)=='9d0b9c790d148604feb49ef1137922d45781d3fda09b238c3a98dc9283ee200a','actual remote receipt pin')
ok(remote['remote_commit']==selection['remote_commit']==COMMIT and remote['selection_sha256']==H(selection_raw),'remote receipt exact commit/selection')
ok(remote['selected_count']==len(remote['selected_blobs'])==len(selection['rows'])==323 and remote['selected_logical_bytes']==10920229,'remote exact counts')
ok(remote['fresh_git_root']==str(REPO) and remote['genuine_run_or_native_started'] is False,'declared fresh Git scope')
ok(remote['free_bytes']>=10*1024**3 and 0<remote['elapsed_seconds']<600,'actual transport bounds')
ops=remote['operations'];ok(len(ops)==657==11+2*323,'all actual Git operations denominator')
ok([o['operation'] for o in ops]==['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree','fetch']+['cat-file']*646+['ls-remote'],'exact actual operation order')
for o in ops:
 ok(o['exit']==0 and o['cleanup_failures']==[] and type(o['pid']) is int and o['pid']>0,'all actual Git terminal cleanup')
 ok(not pathlib.Path('/proc',str(o['pid'])).exists(),'actual Git PID now absent')
 ok(0<=o['seconds']<=60 and 0<=o['stdout_bytes']<=FILE and 0<=o['stderr_bytes']<=FILE,'each recorded operation bounded')
remote_head=(COMMIT+'\t'+remote['branch']+'\n').encode()
for i in (1,-1):ok(ops[i]['stdout_sha256']==H(remote_head) and ops[i]['stdout_bytes']==len(remote_head),'first/final actual remote HEAD evidence')
ok(ops[7]['stdout_sha256']==H((COMMIT+'\n').encode()),'fetched actual commit receipt join')
# Explicitly disable lazy/promisor fetch and all protocols for independent offline object checks.
def offline(repo,*args):
 env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1'}
 r=subprocess.run(['git','--no-optional-locks','-c','protocol.allow=never','-C',str(repo),*args],capture_output=True,timeout=30,check=True,env=env)
 ok(len(r.stdout)<=FILE and not r.stderr,'offline local Git bounded no network');return r.stdout
names=[r['path'] for r in selection['rows']];ok(names==sorted(set(names)),'frozen sorted regular nonrecursive selection')
tree=offline(REPO,'ls-tree','-r','-z',COMMIT,'--',*names);remote_objects={}
for row in tree.split(b'\0'):
 if row:
  left,n=row.split(b'\t');mode,kind,oid=left.decode().split();remote_objects[n.decode()]=(mode,kind,oid)
ok(set(remote_objects)==set(names) and H(tree)==ops[8]['stdout_sha256'],'actual fetched tree exact literal scope and log join')
remote_rows=[]
for i,(row,got) in enumerate(zip(selection['rows'],remote['selected_blobs'])):
 name=row['path'];mode,kind,oid=remote_objects[name]
 ok(got==dict(row,git_mode=mode,git_object=oid) and mode in ('100644','100755') and kind=='blob','remote full row exact')
 body=offline(REPO,'cat-file','blob',oid);b=read(SELECTED/name)
 ok(body==b and H(b)==row['sha256'] and len(b)==row['bytes']<=FILE,'independent fetched object and selected actual body')
 ok(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'every fetched blob SHA1 identity')
 sizeop,bodyop=ops[10+2*i:12+2*i]
 ok(sizeop['stdout_sha256']==H((str(len(b))+'\n').encode()) and bodyop['stdout_sha256']==H(b) and bodyop['stdout_bytes']==len(b),'each actual transport object read log joined')
 remote_rows.append(got)
# No protocol-enabled Git call or fetching is issued by this independent reviewer.
selected_files=[]
for root,dirs,files in os.walk(SELECTED,followlinks=False):
 for name in dirs:ok(not (pathlib.Path(root)/name).is_symlink(),'selected no symlink directories')
 for name in files:selected_files.append(str((pathlib.Path(root)/name).relative_to(SELECTED)))
ok(sorted(selected_files)==names,'actual selected namespace exact no extras')
ok(sum(r['bytes'] for r in remote_rows)==10920229<64*1024**2,'actual complete selected logical denominator')
rt=js(REMOTE/'ACTUAL_REMOTE_TERMINAL01.json')
ok(rt['exit']==0 and rt['session']==35918 and rt['actual_completion_tool']=='402357' and rt['receipt_sha256']==H(rr),'recorded actual transport terminal')
ok(rt['actual_remote_first_and_final_HEAD']==COMMIT and rt['actual_all_owned_git_pids_absent'] is True,'transport terminal joins')
ok(not (REMOTE/'FAILED01.json').exists(),'transport failure receipt absent')
rb=SELECTED/B.relative_to(ROOT);rp=SELECTED/P.relative_to(ROOT)
ok(read(rp/'REQUEST01.json')==qraw and read(rb/'capture.json')==cr,'genuine fetched request capture exact')
for name in ['capsule.tar.gz','external.tar.gz','capsule-manifest.json','external-manifest.json']:
 ok(read(rb/name)==read(B/name),'complete fetched archive/manifest join '+name)
fi=js(FLAT_PARENT/'FLAT_INTENT01.json');fr=read(FLAT/'recovery.json');flat_receipt=json.loads(fr)
ok(H(fr)=='4018c09c3fc4a27d9cdd88e7cd1d7e38df0b0f0a97f542deecb6433e77d655f4','actual full flat recovery receipt')
ok(fi['actual_remote_receipt_sha256']==H(rr) and fi['actual_remote_commit']==COMMIT and fi['destination']==str(FLAT) and fi['bundle']==str(rb) and fi['request']==str(rp/'REQUEST01.json'),'actual flat fetched origin route')
fsource=pathlib.Path(fi['source']);ok(fsource.is_relative_to(SELECTED) and H(read(fsource))==fi['source_sha256']=='eca351c9bf2d12fe4ae903c9358e2d7acb9c01833bc3a826b59635130ce752ce','actual fetched recovery source exact')
ok(flat_receipt['capture_sha256']==H(cr) and flat_receipt['request_sha256']==H(qraw) and flat_receipt['reported_outcome']=='FAILED','actual flat request/capture/outcome')
for k in ['instantiated_posix_tree','recovered_tree_git_join','runtime_package_bodies_recovered','outside_stores_recovered','research_authority','scientific_representation_complete']:ok(flat_receipt[k] is False,'no widened flat authority '+k)
ok(stat.S_IMODE(FLAT.stat().st_mode)==0o700 and FLAT.stat().st_uid==os.getuid(),'actual flat private directory')
expected={'recovery.json'};flat_maps={};flat_details={};flat_data={};total_logical=0;total_allocated=FLAT.stat().st_blocks*512
for kind in ('capsule','external'):
 meta_raw=read(FLAT/(kind+'-metadata.json'));meta=json.loads(meta_raw);m=q['current_manifests'][kind];mapping=meta['flat_members'];expected.add(kind+'-metadata.json')
 ok(meta['schema_version']==1 and meta['manifest']==m and meta['archive']==c['archives'][kind],'flat complete typed metadata')
 regular={r['path']:r for r in m['members'] if r['kind']=='file'}
 ok(set(mapping)==set(regular) and len(set(mapping.values()))==len(mapping),'flat exact complete regular member mapping')
 expected.update(mapping.values());flat_maps[kind]=mapping;flat_data[kind]={}
 for name,fn in mapping.items():
  ok(pathlib.PurePosixPath(fn).name==fn and fn.startswith(kind+'-') and fn.endswith('.body'),'flat own body namespace')
  raw=read(FLAT/fn);row=regular[name]
  ok(len(raw)==row['bytes'] and H(raw)==row['sha256'] and raw==opaque[kind][name],'every flat opaque original/archive body')
  flat_data[kind][name]=raw
 result=flat_receipt['results'][kind]
 ok(result['metadata_sha256']==H(meta_raw) and result['manifest_sha256']==H(enc(m)) and result['archive_sha256']==c['archives'][kind]['sha256'],'flat actual result pins')
 ok(result['members']==len(m['members']) and result['regular_bodies']==len(regular) and result['root_mode']==m['root_mode'],'flat actual full denominators')
 # Rebuild the entire canonical archive using recovered flat bytes and retained POSIX metadata.
 out=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for row in m['members']:
    t=tarfile.TarInfo(row['path']);t.mode=row['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if row['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tar.addfile(t)
    else:t.size=row['bytes'];tar.addfile(t,io.BytesIO(flat_data[kind][row['path']]))
 ok(out.getvalue()==read(rb/(kind+'.tar.gz')),'full flat-to-actual-remote canonical archive byte reconstruction')
 flat_details[kind]={'members':len(m['members']),'regular_bodies':len(regular),'original_members':len(q['baseline'][kind+'_manifest']['members']),'metadata_sha256':H(meta_raw),'canonical_full_archive_reconstruction_exact':True,'archive_sha256':H(out.getvalue())}
for category,prefix in [('evidence',''),('support_bodies','support-')]:
 for name,ref in q[category].items():
  fn=prefix+name+'.body';expected.add(fn);ok(read(FLAT/fn)==read(rb/fn)==read(pathlib.Path(ref['path'])) and H(read(FLAT/fn))==ref['sha256'],'flat remote original complete evidence/support chain')
actual=set()
for f in FLAT.iterdir():
 st=f.lstat();ok(stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and st.st_uid==os.getuid(),'all actual flat bodies single-link private600')
 actual.add(f.name);total_logical+=st.st_size;total_allocated+=st.st_blocks*512
ok(actual==expected and len(actual)==763==747+2+3+10+1,'whole actual flat namespace763 complete no extras')
ok(total_logical<128*1024**2 and total_allocated<128*1024**2,'whole flat logical/allocated bounds')
for name,pin in source_pins.items():ok(H(flat_data['capsule'][name])==pin and flat_data['capsule'][name]==opaque['capsule'][name],'205 original source-registration actual flat+remote joins')
for inp in exp['inputs'].values():ok(H(flat_data['capsule'][inp['path']])==inp['sha256'],'33 original opaque inputs actual flat+remote joins')
for name,(mode,oid) in objects.items():
 raw=flat_data['capsule'][name];ok(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'246 original tracked actual flat+remote OID joins')
ft=js(FLAT_PARENT/'ACTUAL_FLAT_TERMINAL01.json');ok(ft['exit']==0 and ft['session']==77199 and ft['completion_tool']=='2ffafc' and ft['recovery_sha256']==H(fr) and ft['actual_remote_receipt_sha256']==H(rr),'actual flat terminal identities')
ok(ft['actual_flat_regular_files']==len(actual) and ft['results']==flat_receipt['results'] and ft['subset']==flat_receipt['subset'],'actual flat terminal full result join')
ok(flat_receipt['subset']==c['subset'] and flat_receipt['support_sha256']==c['support_sha256'],'flat exact subset and support denominators')
# Preserve all previous review bodies, failures and historical null fields exactly.
old_manifest=read(OUT/'MANIFEST02.json');ok(H(old_manifest)=='8d61bf382d830d104057b9264a043844118364fa2771e9bbad51b13d82e9d8e1','previous review manifest pin')
for row in json.loads(old_manifest)['members']:
 raw=read(OUT/row['path']);ok(H(raw)==row['sha256'] and len(raw)==row['bytes'] and stat.S_IMODE((OUT/row['path']).stat().st_mode)==row['mode'],'all previous review evidence preserved')
prior=js(OUT/'SELECTION_REVIEW02.json');ok(prior['actual_flat_receipt'] is None and prior['actual_transport_receipt'] is None and prior['actual_remote_HEAD_verified'] is False,'prior unverified historical fields unchanged')
postfetch=[REMOTE/'SELECTED_BODIES01.json',REMOTE/'REMOTE_RECOVERY01.json',REMOTE/'ACTUAL_REMOTE_TERMINAL01.json',FLAT_PARENT/'ACTUAL_FLAT_TERMINAL01.json',FLAT/'recovery.json',OUT/'SELECTION_REVIEW02.md',OUT/'MANIFEST02.json']
for p in postfetch:ok(str(p.relative_to(ROOT)) not in names,'later local receipt outside actual fetched scope')
free=shutil.disk_usage(FLAT).free;ok(free>=10*1024**3,'actual final local10GiB floor')
result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_REMOTE_AND_FRESH_FLAT_ARCHIVAL_RECOVERY_ONLY','assertions':checks,'remote_commit':COMMIT,'selection_sha256':H(selection_raw),'actual_remote_receipt_sha256':H(rr),'actual_flat_receipt_sha256':H(fr),'capture_sha256':H(cr),'request_sha256':H(qraw),'selected_count':323,'selected_bytes':10920229,'root_recorded_git_operations':657,'root_transport_elapsed_seconds':remote['elapsed_seconds'],'all_recorded_git_pids_currently_absent':True,'actual_flat_regular_files':len(actual),'flat_logical_bytes':total_logical,'flat_allocated_bytes':total_allocated,'flat_trees':flat_details,'source_join':{'source':source,'source_registration':205,'opaque_inputs':33,'tracked_blobs':246},'original_failed_claims':hist,'original_guard':{'child_exit_code':g['child_exit_code'],'cleanup_verified':g['cleanup_verified']},'separate_child_exit':125,'dependent':'UNAVAILABLE_UNCLAIMED','highest_adopted_original_allowance':6,'actual_remote_rows':remote_rows,'local_postfetch_not_in_selected_commit':[str(p.relative_to(ROOT)) for p in postfetch],'previous_review_manifest_sha256':H(old_manifest),'observed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'local_free_bytes':free,'network_called_by_reviewer':False,'native_or_numerical_execution':False,'runtime_store_POSIX_scientific_C6_claim':False,'fd_visibility':'Prior three unrelated inaccessible-process FD limit preserved; no universal census performed','root_push_readback_evidence':'Root reports push18998/tool e44113 and readback36955/tool209a0a exit0; independently joined actual recorded transport first/final remote HEAD and fetched objects, no second network operation'}
save('ACTUAL_RECOVERY_CHECKS03.json',result)
print(json.dumps({'checks':checks,'remote_count':323,'remote_bytes':10920229,'operations':657,'flat_files':len(actual),'flat_logical':total_logical,'flat_allocated':total_allocated,'full_flat_canonical_reconstruction':True,'source_registration':205,'opaque_inputs':33,'tracked':246,'free':free}))

import hashlib,json,os,stat,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;MAIN=B.parents[2];COMMIT='a9b219042109be78498185cc6539c1454736e3eb';count=0;calls=0;observed=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def ck(v,n):
 global count
 assert v,n;count+=1
def read(p):
 s=p.lstat();ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and p.resolve()==p and s.st_size<=4194304,'ordinary bounded body');b=p.read_bytes();e=p.lstat();ck((s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(e.st_dev,e.st_ino,e.st_mode,e.st_size,e.st_mtime_ns,e.st_ctime_ns),'stable body read');return b
def doc(p,pin=None):
 b=read(p);ck(pin is None or sha(b)==pin,'exact evidence pin');return json.loads(b)
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
def git(root,args,data=None):
 global calls
 p=subprocess.run(['git','-c','protocol.allow=never',*args],cwd=root,env=env,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20);calls+=1;ck(p.returncode==0 and len(p.stdout)<=8*1024**2 and len(p.stderr)<=65536,'bounded local immutable Git');return p.stdout
prior=B/'financial-genuine-wrapper-claimedrun-final-committed-selections-review01-2026-10-04';proof=doc(prior/'MACHINE01.json','3d3bfd78cff58862e733a68b3651ac3df35290500a0e08dfcf61a78f465160c8');doc(prior/'MANIFEST01.json','b6edb5734391e40b6dd0ca7acdc35d3db1835434cdb45a149b12f796b7427211');original_oids=doc(prior/'COMMITTED_BLOBS01.json');census=doc(B/'financial-genuine-wrapper-claimedrun-final-selected-closure-census02-2026-10-04/CANDIDATE_ROWS02.json','70ff2feb00e4d334a14897a87222077b943643d96bff087a275bbcdd3b43569f')['rows'];cb={r['path']:r for r in census}
ck(git(MAIN,['rev-parse','HEAD']).decode().strip()==COMMIT,'unchanged Main before')
rootnames=['financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04','financial-genuine-wrapper-root-claimedrun-helper-raw-remote01-2026-10-04'];receiptpins=['ec84e55cfeae3da74557341d3395a84ce5fe4c0a2f187eaec89acc1ded212440','7518301a0862c314c05c379c4f30f249481351a397bcc0e55cfd3c8e91264a30'];selectionpins=['28f95d42e6f53c243d31ed9867724fedd89b04cb601b63de199ac2616c0f49c9','c8dd51669514a49a1c75ad6e74572579d1a0590bad8c1da0d44d70245c54c4ea'];tools=[{'session':82113,'start_chunk':'089680','completion_chunk':'4e1790','exit_code':0},{'session':42309,'start_chunk':'75eb72','completion_chunk':'e05865','exit_code':0}];allpids=set();allgroups=set();sets=[];physical=0;records=[]
for i,name in enumerate(rootnames):
 root=B/name;q=doc(root/'SELECTED_BODIES01.json',selectionpins[i]);r=doc(root/'REMOTE_RECOVERY01.json',receiptpins[i]);terminal=doc(root/'ACTUAL_TOOL_TERMINAL02.json');intent=doc(root/'INTENT01.json');repo=Path(r['fresh_git_root']);ck(repo==root/'fresh-recordfix-source325-01.git' and repo.resolve()==repo,'fresh owned Git root');ck(sha(read(root/'recover01.py'))=='0b397ccd0a014f60a414ce79d67dfd53c58a0fb61ca616a6576cc43da4bbf0aa','unchanged transport');ck(r['remote_commit']==q['remote_commit']==COMMIT and r['selection_sha256']==selectionpins[i] and r['status']=='fresh-actual-remote-recordfix-source325-recovered' and r['genuine_run_or_native_started'] is False,'literal inherited receipt status with exact commit selection');rr=r['selected_blobs'];ck([{k:x[k] for k in ('path','bytes','sha256')} for x in rr]==q['rows'],'all selected receipt rows exact original selection');ck(len(rr)==r['selected_count'] and sum(x['bytes'] for x in rr)==r['selected_logical_bytes'],'actual complete denominators');names=[x['path'] for x in rr];ck(names==sorted(set(names)),'sorted unique physical rows');sets.append(set(names));physical+=len(rr)
 # Saved complete physical set: no unlisted regulars or lexical targets.
 actual=[]
 for p,ds,fs in os.walk(root/'selected',followlinks=False):
  for d in ds:ck(not (Path(p)/d).is_symlink(),'no selected directory symlink')
  for f in fs:actual.append((Path(p)/f).relative_to(root/'selected').as_posix())
 ck(set(actual)==set(names),'saved selected namespace no extras/missing')
 tree=git(repo,['ls-tree','-r','-z',COMMIT,'--',*names]);objects={}
 for item in tree.split(b'\0'):
  if not item:continue
  a,n=item.split(b'\t',1);mode,kind,oid=a.decode().split();ck(kind=='blob' and mode in ('100644','100755'),'fresh regular Git blob');objects[n.decode()]={'mode':mode,'oid':oid}
 ck(set(objects)==set(names),'fresh immutable complete tree scope');unique={}
 for row in rr:
  n=row['path'];p=root/'selected'/n;body=read(p);c=cb[n];ck(stat.S_IMODE(p.lstat().st_mode)==384,'saved private0600');ck(len(body)==row['bytes']==c['bytes'] and sha(body)==row['sha256']==c['sha256'] and body==read(MAIN/n),'all physical selected original bodies');ck(stat.S_IMODE((MAIN/n).lstat().st_mode)==c['mode'],'current original literal mode');ck(objects[n]==original_oids[n]=={'mode':row['git_mode'],'oid':row['git_object']} and hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()==row['git_object'],'fresh/original immutable OID+mode');unique.setdefault(row['git_object'],[]).append(row)
 chunks=[];part=[];size=0
 for oid,rs in unique.items():
  n=rs[0]['bytes']+128
  if part and size+n>6*1024**2:chunks.append(part);part=[];size=0
  part.append(oid);size+=n
 if part:chunks.append(part)
 for group in chunks:
  b=git(repo,['cat-file','--batch'],(''.join(o+'\n' for o in group)).encode());off=0
  for oid in group:
   end=b.index(b'\n',off);got,kind,sz=b[off:end].decode().split();sz=int(sz);ck(got==oid and kind=='blob' and sz<=4194304,'actual fresh object header');body=b[end+1:end+1+sz];ck(b[end+1+sz:end+2+sz]==b'\n','exact batch delimiter');off=end+2+sz
   for row in unique[oid]:ck(len(body)==row['bytes'] and sha(body)==row['sha256'] and body==read(root/'selected'/row['path']),'every fresh Git object saved body match')
  ck(off==len(b),'no extra immutable Git response')
 ops=r['operations'];ck(len(ops)==11+2*len(rr) and len(ops)<=1024,'actual finite operation count');ck([o['operation'] for o in ops[:10]]==['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree','fetch'] and ops[-1]['operation']=='ls-remote','actual expected original Git sequence');remote_line=(COMMIT+'\t'+r['branch']+'\n').encode()
 for op in (ops[1],ops[-1]):ck(op['stdout_bytes']==len(remote_line) and op['stdout_sha256']==sha(remote_line),'both actual remoteHEAD result hashes')
 ck(ops[7]['stdout_sha256']==sha((COMMIT+'\n').encode()) and ops[8]['stdout_sha256']==sha(tree) and ops[8]['stdout_bytes']==len(tree),'original fetched commit/tree stdout exact joins')
 for j,row in enumerate(rr):
  szop,bodyop=ops[10+2*j:12+2*j];ck(szop['operation']==bodyop['operation']=='cat-file' and szop['stdout_sha256']==sha((str(row['bytes'])+'\n').encode()) and bodyop['stdout_bytes']==row['bytes'] and bodyop['stdout_sha256']==row['sha256'],'every actual perbody operation hash joins')
 for op in ops:
  ck(op['exit']==0 and op['cleanup_failures']==[] and 0<=op['seconds']<60 and op['stderr_bytes']<=65536 and op['stdout_bytes']<=4194304,'all original operation outcomes/bounds');allpids.add(op['pid']);allgroups.add(op['pid'])
 ck(terminal['actual_tool']==tools[i] and terminal['actual_intent']==intent and terminal['actual_receipt']=={'bytes':len(read(root/'REMOTE_RECOVERY01.json')),'sha256':receiptpins[i]},'original tool terminal intent receipt joins');ck(intent['selection_sha256']==selectionpins[i] and intent['remote_commit']==COMMIT and intent['genuine_exact_scope_review_sha256']=='3d3bfd78cff58862e733a68b3651ac3df35290500a0e08dfcf61a78f465160c8','actual beforeexec intent release binding')
 for stream,key in [('out','stdout'),('err','stderr')]:
  b=read(root/('ACTUAL_RECOVERY01.'+stream));ck(terminal[key]=={'bytes':len(b),'sha256':sha(b)},'actual outer raw stream joins')
 ck(read(root/'ACTUAL_RECOVERY01.err')==b'','actual outer stderr empty');stdout=json.loads(read(root/'ACTUAL_RECOVERY01.out'));ck(all(stdout[k]==r[k] for k in stdout),'actual outer stdout receipt fields');ck(intent['free_before']>=10737418240 and r['free_bytes']>=10737418240 and terminal['free_bytes']>=10737418240 and r['elapsed_seconds']<600,'recorded resource observations');allpids.add(intent['actual_pid']);allgroups.add(intent['actual_pgid']);ck(type(intent['actual_start_ticks'])is int and intent['actual_start_ticks']>0,'original startticks recorded')
 records.append({'role':'primary' if i==0 else 'supplemental','receipt_sha256':receiptpins[i],'terminal_sha256':sha(read(root/'ACTUAL_TOOL_TERMINAL02.json')),'selected_paths':len(rr),'selected_bytes':r['selected_logical_bytes'],'actual_operations':len(ops),'elapsed_seconds':r['elapsed_seconds'],'original_root_pid':intent['actual_pid'],'original_root_start_ticks':intent['actual_start_ticks'],'original_root_group':intent['actual_pgid'],'freshGit_unique_blobs':len(unique)})
ck(physical==695 and len(sets[0]|sets[1])==689 and len(sets[0]&sets[1])==6 and sets[0]|sets[1]==set(cb),'all actual physical and distinct complete role union')
# Current process observations, never a continuous/history or unknown-descendant claim.
current=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  s=(p/'stat').read_text();v=s[s.rfind(')')+2:].split();pid=int(p.name);pg=int(v[2])
  if pid in allpids or pg in allgroups:current.append({'pid':pid,'pgid':pg})
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
ck(not current,'all recorded Root/Git PID and own groups currently absent');ck(len(allpids)==1414,'1412 actual Git identities plus2 Roots');ck(git(MAIN,['rev-parse','HEAD']).decode().strip()==COMMIT,'Main current unchanged after')
for name,pin in zip(rootnames,receiptpins):ck(sha(read(B/name/'REMOTE_RECOVERY01.json'))==pin,'actual original receipts unchanged')
out={'schema_version':1,'decision':'accepted-actual-two-batch-external-selected-byte-union','commit':COMMIT,'selection_release_sha256':'3d3bfd78cff58862e733a68b3651ac3df35290500a0e08dfcf61a78f465160c8','checks':count,'bounded_local_git_calls':calls,'batches':records,'physical_saved_bodies':695,'distinct_paths':689,'distinct_bytes':52795748,'shared_safety_anchor_paths':6,'actual_operations':1412,'current_recorded_pid_group_matches':current,'observed_recorded_pid_count':len(allpids),'scope_literal_links_as_metadata':45,'complete_own_raw_bodies':330,'original_receipt_status_retained':'fresh-actual-remote-recordfix-source325-recovered','actual_flat_recovery':False,'native_or_numerical_authority':False,'qualification':'Both original external selected-body outcomes independently joined to genuine exact selections, immutable Git blobs and complete accepted scope. Inherited Source325 status is historical wording, not current scope authority. Current recorded PID/group absence is not continuous or unrecorded-descendant history. Whole fresh flat recovery and exact contracts remain separate.'}
(H/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');(H/'PROCESS_READBACK01.json').write_text(json.dumps({'recorded_pids':sorted(allpids),'recorded_groups':sorted(allgroups),'current_matches':current},sort_keys=True,indent=2)+'\n');print('PASS',count,'localGit',calls)

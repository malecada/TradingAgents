import ast,datetime,hashlib,json,os,resource,signal,stat,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];F=P.parent;A=F/'xsect-posix-recovery-entry01-2026-10-09';began=time.monotonic()
os.nice(10);os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]));resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
def alarm(s,f):raise TimeoutError('bounded180second streaming review')
signal.signal(signal.SIGALRM,alarm);signal.alarm(180);evidence={}
def read(p):
 raw=p.read_bytes();assert len(raw)<=4*1024**2;evidence[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();return raw
def load(p):return json.loads(read(p))
c=load(A/'CONTRACT_FINAL01.json');release=load(A/'RELEASE01.json');assert release['contract_sha256']==evidence[str((A/'CONTRACT_FINAL01.json').relative_to(R))];source=read(A/'restore.py');assert hashlib.sha256(source).hexdigest()==release['source_sha256']=='f3b1f132a9474c8e3f5df7eb30e885b465bd75e65930a063bfbd634d0da49dad'
ns={'__file__':str(A/'restore.py'),'__name__':'review_only'};exec(compile(source,str(A/'restore.py'),'exec'),ns);rows,dirs,selection=ns['validate_selection'](c)
complete=load(A/'COMPLETE01.json');terminal=load(A/'ROOT_TERMINAL01.json');assert terminal['actual_root_exit_code']==0 and terminal['exec_session']==94965 and terminal['actual_exit_tool_chunk']=='57b817';assert terminal['complete_sha256']==evidence[str((A/'COMPLETE01.json').relative_to(R))];assert not Path('/proc',str(terminal['original_driver_pid'])).exists();assert not (A/'FAILED01.json').exists();assert complete['status']=='complete' and len(complete['batches'])==29 and complete['deletion_authorized'] is False
receipts=[]
for (batch,original,manifest),saved in zip(selection,complete['batches'],strict=True):
 base=A/'downloads'/f"batch-{batch['index']:04d}";restored=load(base/'RESTORED01.json');assert saved=={'index':batch['index'],'result':restored['result']};assert restored['fresh_remote_bytes_verified'] and restored['originals_preserved'];expected={'files':original['files'],'raw_bytes':original['raw_bytes'],'start':batch['start'],'stop':batch['stop'],'archive_sha256':original['archive_sha256'],'originals_opened':False};assert restored['result']==expected;assert not (base/'bundle.tar').exists()
 assert load(base/'manifest.json')==manifest
 for name,size in [('manifest.json',c['selection'][batch['index']]['manifest_ref']['bytes']),('bundle.tar',original['archive_bytes'])]:
  q=load(base/(name+'.transport.json'));assert q['status']=='complete' and q['error_type'] is None and q['returncode']==0 and q['received_bytes']==q['expected_bytes']==size;cl=q['owned_cleanup'];assert cl['direct_child_reaped'] and cl['owned_group_absent'];assert not Path('/proc',str(q['pid'])).exists()
  try:os.killpg(q['pid'],0)
  except ProcessLookupError:pass
  else:raise AssertionError('transport group present')
  receipts.append(q['pid'])
assert len(receipts)==58
# Reuse accepted helper; current inode is observed now, not invented historically.
hpath=R/c['recovery_ref']['path'];hraw=read(hpath);assert hashlib.sha256(hraw).hexdigest()=='dcd7e1ca1e7017541ad3635bc229d7bd9d6326ad819bb6762958f9e6df008d3a';helper={};vpath=R/'tradingagents/research/onchain_replication/preservation.py';exec(compile(read(vpath),str(vpath),'exec'),helper);tree=ast.parse(hraw);tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module=='tradingagents.research.onchain_replication.preservation')];exec(compile(tree,str(hpath),'exec'),helper)
target=Path(c['target_root']);st=target.lstat();current_pin=(st.st_dev,st.st_ino);verify=helper['verify_new_tree'](target,rows,dirs,original_root=c['original_root'],root_pin=current_pin,max_files=c['expected_files'],max_total_bytes=c['expected_raw_bytes'],max_file_bytes=c['max_file_bytes'],restore_directories=False)
root_record=load(A/'ROOT_PIN01.json');assert root_record['target_root']==str(target);root_record_matches=tuple(root_record['root_pin'])==current_pin
# Current original inventory/content: bounded opaque streams, exact snapshot stat
# fields, no symlinks followed, before/after descriptor and pathname signatures.
origin=Path(c['original_root']);expected_files={x['relative_path']:x for x in rows};expected_dirs={x['relative_path']:x for x in dirs};seen_files=set();seen_dirs=set();total=0;stack=[origin]
def sig(x):return (x.st_dev,x.st_ino,x.st_mode,x.st_nlink,x.st_size,x.st_mtime_ns,x.st_ctime_ns)
def metadata(path,row,info):
 assert info.st_dev==row['device'] and info.st_ino==row['inode'] and info.st_mode==row['mode'] and info.st_nlink==row['nlink'] and info.st_mtime_ns==row['mtime_ns'] and info.st_ctime_ns==row['ctime_ns'],str(path)
while stack:
 directory=stack.pop();relative=str(directory.relative_to(origin));info=directory.lstat();assert stat.S_ISDIR(info.st_mode) and relative in expected_dirs;metadata(directory,expected_dirs[relative],info);seen_dirs.add(relative)
 with os.scandir(directory) as iterator:
  for entry in iterator:
   path=Path(entry.path);name=str(path.relative_to(origin));observed=entry.stat(follow_symlinks=False)
   if stat.S_ISDIR(observed.st_mode):assert name in expected_dirs;stack.append(path);continue
   assert name in expected_files and stat.S_ISREG(observed.st_mode) and observed.st_nlink==1;row=expected_files[name];metadata(path,row,observed);assert observed.st_size==row['bytes'];fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
   try:
    before=os.fstat(fd);assert sig(before)==sig(observed);left=row['bytes'];h=hashlib.sha256()
    while left:
     block=os.read(fd,min(1024*1024,left));assert block;left-=len(block);h.update(block)
    assert not os.read(fd,1) and h.hexdigest()==row['expected_sha256'];assert sig(os.fstat(fd))==sig(before)==sig(path.lstat())
   finally:os.close(fd)
   seen_files.add(name);total+=row['bytes']
assert seen_files==expected_files.keys() and seen_dirs==expected_dirs.keys()
# Recheck original directories after complete scan for detectable namespace edits.
for name,row in expected_dirs.items():metadata(origin/name,row,(origin/name).lstat())
assert not any(x in sys.modules for x in ['numpy','torch','scipy'])
result={'decision':'accepted_sampled_recovery_and_original_currentness','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'recovered_tree':verify,'fresh_current_root_pin':current_pin,'existing_ROOT_PIN01_record_matches_current':root_record_matches,'root_pin_qualification':'Existing ROOT_PIN01 body is observed/pinned separately; independent whole-tree verification used freshly observed current device/inode.','original_current_files':len(seen_files),'original_current_directories':len(seen_dirs),'original_current_raw_bytes':total,'original_hashes_and_snapshot_stat_fields_match':True,'restored_batches':len(selection),'fresh_transport_receipts':len(receipts),'generated_bundle_archives_absent':True,'actual_driver_absent':True,'originals_not_deleted':True,'writer_exclusion_proved':False,'retirement_authorized':False,'elapsed_seconds':time.monotonic()-began,'actual_affinity':sorted(os.sched_getaffinity(0)),'evidence':evidence,'qualification':'Opaque streaming hash and sampled metadata only; no semantic/scientific computation. No content copies. Independent currentness is not writer exclusion; originals remain intact.'};(P/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');signal.alarm(0);print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))

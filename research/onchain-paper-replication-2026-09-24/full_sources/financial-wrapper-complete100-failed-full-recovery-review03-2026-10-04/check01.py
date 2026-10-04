from pathlib import Path
import json,hashlib,stat,os,io,gzip,tarfile,subprocess
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';T=F/'financial-wrapper-complete100-failed-root-remote03-2026-10-04';C=F/'financial-wrapper-complete100-failed-outcome-capture02-2026-10-04';O=F/'financial-wrapper-complete100-failed-full-recovery-review03-2026-10-04';O.mkdir(mode=0o700);S=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());flat=J(T/'FLAT_RECOVERY01.json');cap=J(C/'CAPTURE01.json');remote=J(T/'REMOTE_RECOVERY01.json')
assert h((T/'FLAT_RECOVERY01.json').read_bytes())=='7f806b4a71a15128accc699f221441305bfbfa56eeff48179e9cd96d44ba6c17';assert flat['remote_receipt_sha256']==h((T/'REMOTE_RECOVERY01.json').read_bytes())=='33c0a82e29d16415e233d51c32196fab850fedff9239e77b7dd64088b61b3cf9';assert flat['capture_sha256']==h((C/'CAPTURE01.json').read_bytes())
def git(args,cwd):return subprocess.run(['git','--no-replace-objects',*args],cwd=cwd,capture_output=True,check=True,timeout=20).stdout
# Every physical selected body rejoins original and fetched actual Git objects.
selected=[];repo=Path(remote['fresh_git_root']);commit=remote['remote_commit']
assert git(['cat-file','-t',commit],repo)==b'commit\n'
for x in remote['selected_blobs']:
 n=x['path'];b=(T/'selected'/n).read_bytes();assert b==(R/n).read_bytes() and h(b)==x['sha256'] and len(b)==x['bytes']
 assert git(['cat-file','blob',x['git_object']],repo)==b
 line=git(['ls-tree',commit,'--',n],repo).decode().strip();meta,path=line.split('\t');assert path==n and meta.split()==[x['git_mode'],'blob',x['git_object']]
 selected.append({'path':n,'sha256':x['sha256'],'git_object':x['git_object'],'bytes':x['bytes']})
assert len(selected)==35
recovered={};physical=[];scopejoins=[];master=J(C/'CAPSULE_MASTER_MANIFEST01.json');capsrows={x['path']:x for x in master['members']};file_scopes={};dirrows={}
for role,item in flat['scopes'].items():
 p=T/('flat-'+role+'01');assert stat.S_IMODE(p.stat().st_mode)==0o700 and p.resolve()==p
 mp=p/item['metadata_file'];assert h(mp.read_bytes())==item['metadata_sha256'];md=J(mp);m=J(C/(role.upper()+'_MANIFEST01.json'));assert md['manifest']==m and md['archive']==cap['scopes'][role]['archive'];assert h((C/(role.upper()+'_MANIFEST01.json')).read_bytes())==item['manifest_sha256'];mapping=md['flat_members'];rs=m['members'];assert list(mapping)==sorted(mapping) and set(mapping)=={x['path'] for x in rs if x['kind']=='file'} and len(set(mapping.values()))==len(mapping)
 assert set(x.name for x in p.iterdir())==set(mapping.values())|{item['metadata_file']}
 for fp in p.iterdir():
  st=fp.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and st.st_size<=4*1024**2;physical.append({'path':str(fp),'bytes':st.st_size,'sha256':h(fp.read_bytes()),'inode':st.st_ino,'mode':384})
 raw=(C/('complete-'+role+'01.tar.gz')).read_bytes();assert h(raw)==item['archive_sha256'];sink=io.BytesIO();bodies={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tar:
  ts=tar.getmembers();assert [x.name for x in ts]==[x['path'] for x in rs]
  for ti,row in zip(ts,rs):
   assert ti.mode==row['mode'];n=row['path']
   if row['kind']=='file':
    b=(p/mapping[n]).read_bytes();assert ti.isfile() and tar.extractfile(ti).read()==b and len(b)==row['bytes'] and h(b)==row['sha256'];bodies[n]=b;recovered[(role,n)]=p/mapping[n]
   else:assert ti.isdir() and ti.size==0
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for row in rs:
    ti=tarfile.TarInfo(row['path']);ti.mode=row['mode'];ti.uid=ti.gid=ti.mtime=0;ti.uname=ti.gname=''
    if row['kind']=='directory':ti.type=tarfile.DIRTYPE;tar.addfile(ti)
    else:ti.size=row['bytes'];tar.addfile(ti,io.BytesIO(bodies[row['path']]))
 assert sink.getvalue()==raw
 snap=Path(cap['scopes'][role]['snapshot'])
 for row in rs:
  original=snap/row['path'];st=original.lstat();assert stat.S_IMODE(st.st_mode)==row['mode']
  if row['kind']=='file':assert original.read_bytes()==bodies[row['path']]
 if role.startswith('capsule'):
  for row in rs:
   assert capsrows[row['path']]==row
   if row['kind']=='file':assert row['path'] not in file_scopes;file_scopes[row['path']]=role
   else:dirrows[row['path']]=row
 scopejoins.append({'role':role,'typed':len(rs),'files':len(mapping),'logical':sum(x.get('bytes',0) for x in rs),'archive_sha256':h(raw),'metadata_sha256':h(mp.read_bytes()),'canonical_from_actual_flat':True})
assert len(capsrows)==588 and len(file_scopes)==475 and len(dirrows)==113 and sum(x.get('bytes',0) for x in master['members'])==23015911
index=J(C/'CAPSULE_SHARD_INDEX01.json');assert len(index['file_mapping'])==475
for x in index['file_mapping']:assert file_scopes[x['path']]==x['scope'] and capsrows[x['path']]['sha256']==x['sha256'] and capsrows[x['path']]['bytes']==x['bytes']
# Current complete nonGit source snapshot vs every recovered original.
current=[]
for root,ds,fs in os.walk(S,followlinks=False):
 if Path(root)==S:ds.remove('.git')
 for name in ds+fs:current.append(str((Path(root)/name).relative_to(S)))
assert sorted(current)==sorted(capsrows)
for n,row in capsrows.items():
 st=(S/n).lstat();assert stat.S_IMODE(st.st_mode)==row['mode']
 if row['kind']=='file':assert (S/n).read_bytes()==recovered[(file_scopes[n],n)].read_bytes()
 else:assert stat.S_ISDIR(st.st_mode)
# Parent exact complete current tree.
P=Path(cap['scopes']['parent']['original']);pm=J(C/'PARENT_MANIFEST01.json');assert sorted(str(p.relative_to(P)) for p in P.rglob('*'))==sorted(x['path'] for x in pm['members'])
for x in pm['members']:
 p=P/x['path'];assert stat.S_IMODE(p.lstat().st_mode)==x['mode']
 if x['kind']=='file':assert p.read_bytes()==recovered[('parent',x['path'])].read_bytes()
# Full original compound support mapping, all actual Root receipt modes retained.
roots=J(C/'SUPPORT_ROOTS01.json');evidence=J(C/'ROOT_EVIDENCE_PATHS01.json');emap={x['support_path']:Path(x['original']) for x in evidence};sm=J(C/'SUPPORT_MANIFEST01.json')
for x in sm['members']:
 n=x['path'];parts=Path(n).parts
 if parts[0]=='original-final-contract':p=Path(roots['contract_original']).joinpath(*parts[1:])
 elif parts[0]==Path(roots['review_original']).name:p=Path(roots['review_original']).joinpath(*parts[1:])
 elif n in emap:p=emap[n]
 elif n=='root-failed-evidence':continue
 else:raise AssertionError(n)
 assert stat.S_IMODE(p.lstat().st_mode)==x['mode']
 if x['kind']=='file':assert p.read_bytes()==recovered[('support',n)].read_bytes()
# Current tracked source and registration inputs are opaque exact original bytes.
assert git(['rev-parse','HEAD'],S).decode().strip()==flat['source'];tracked=git(['ls-tree','-rz','HEAD'],S).split(b'\0');assert tracked[-1]==b'' and len(tracked)-1==339
for line in tracked[:-1]:
 meta,n=line.split(b'\t');mode,kind,oid=meta.split();n=n.decode();assert kind==b'blob' and n in file_scopes and git(['cat-file','blob',oid.decode()],S)==recovered[(file_scopes[n],n)].read_bytes()
gate=J(S/'fixture_inputs/financial_wrapper_claimedrun01/gates.json');exp=gate['experiments'][flat['identity']];assert len(exp['source_files'])==338 and len(exp['inputs'])==8
for n,pin in exp['source_files'].items():assert h(recovered[(file_scopes[n],n)].read_bytes())==pin
for info in exp['inputs'].values():assert h(recovered[(file_scopes[info['path']],info['path'])].read_bytes())==info['sha256']
closure=J(S/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json');assert len(closure['installed'])==194 and sum(n.startswith('tradingagents/') for n in closure['installed'])==149
for n,pin in closure['installed'].items():assert h(recovered[(file_scopes[n],n)].read_bytes())==pin
runtime=J(S/'fixture_inputs/financial_wrapper_claimedrun01/runtime_mapping.json');assert len(runtime['distribution_records'])==251
# Lifecycle JSON only. No state.pt/NPY/torch decoding.
claims=[]
for p in sorted((S/'research_runs').glob('*/claim.json')):
 q=J(p);failed=p.parent/'failed.json';assert failed.is_file() and not (p.parent/'complete.json').exists();claims.append({'identity':p.parent.name,'claim_sha256':h(p.read_bytes()),'failed_sha256':h(failed.read_bytes()),'budget':q.get('effective_attempt_budget',q['family']['attempt_budget'])})
assert len(claims)==3 and max(x['budget'] for x in claims)==19
assert any(x['claim_sha256']==cap['historical_claim_sha256'] and x['failed_sha256']==cap['historical_failed_sha256'] for x in claims)
fit=S/'research_artifacts/onchain_fit_cells/c03aeddda6f73d8ab5313451b54bc536acb329400b9bec2c77ad9c4ba88e71da'/flat['identity'];assert not (fit/'complete.json').exists();cp=list(fit.glob('checkpoints/*/state.pt'));epochs=list(fit.glob('epoch*.json'));print('journal patterns',len(cp),len(epochs),[p.name for p in fit.iterdir()][:12]);assert len(cp)==29
# Genuine actual Root terminal/intent/raw stream joins and current absence.
exitrow=J(T/'ROOT_FLAT03_EXIT01.json');intent=J(T/'ROOT_FLAT03_INTENT01.json');spawn=J(T/'ROOT_FLAT03_SPAWN01.json');assert exitrow['actual_root_exit']==0 and intent['actual_remote_sha256']==flat['remote_receipt_sha256'];assert not Path('/proc',str(spawn['actual_root_child_pid'])).exists()
f=spawn['procstat'].split(') ',1)[1].split();pg=int(f[2])
try:os.killpg(pg,0)
except ProcessLookupError:pass
else:raise AssertionError('flat group alive')
for stream in ['stdout','stderr']:
 b=(T/('ROOT_FLAT03.'+stream)).read_bytes();assert len(b)==exitrow[stream+'_bytes'] and h(b)==exitrow[stream+'_sha256']
assert all(x['free_bytes']>=10*1024**3 for x in flat['floor_observations'])
for sample in [intent['initial_complete_sampled_owned_root'],exitrow['final_complete_sampled_owned_root']]:assert sample['logical_bytes']<=64*1024**2 and sample['allocated_bytes']<=96*1024**2 and sample['members']<=32768
for c in remote['operations']:
 assert c['exit']==c['actual_reaped_exit']==0 and c['actual_child_limits']=={'pid':c['pid'],'fsize':[4194304,4194304]} and not c['cleanup_failures'] and not Path('/proc',str(c['pid'])).exists()
 try:os.killpg(c['pid'],0)
 except ProcessLookupError:pass
 else:raise AssertionError('Git group alive')
assert len(remote['operations'])==109
out={'schema_version':1,'receipt_sha256':h((T/'FLAT_RECOVERY01.json').read_bytes()),'remote_sha256':flat['remote_receipt_sha256'],'capture_sha256':flat['capture_sha256'],'scopes':scopejoins,'selected_git_joins':selected,'flat_physical_files':physical,'capsule_typed':588,'capsule_files':475,'capsule_logical':23015911,'claims':claims,'opaque_checkpoint_count':len(cp),'source_tracked':339,'source_pins':338,'implementation_paths':194,'package_paths':149,'input_roles':8,'runtime_record_metadata':251,'actual_root_exit':exitrow,'original_root_spawn':spawn,'floor_observations':flat['floor_observations'],'current_complete_originals_unchanged':True,'metadata_only_no_checkpoint_deserialization':True}
(O/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');(O/'check01.py').write_bytes(Path('/tmp/actual_failed_flat03.py').read_bytes());print('PASS',len(physical))

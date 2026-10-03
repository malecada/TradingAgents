from pathlib import Path
import hashlib,importlib.util,json,os,stat,sys,time
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-final-composition-root-preparation01-2026-10-03';P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01');C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALLOW_PROTOCOL']=''
assert H((A/'MANIFEST01.json').read_bytes())=='4d6fcd343d680ef576779a70b755bf5f3b0c3c797b993b540073d2d8bea0f7df'
m=J(A/'MANIFEST01.json');assert {p.name for p in A.iterdir()}=={r['path'] for r in m['files']}|{'MANIFEST01.json'}
for r in m['files']:
 p=A/r['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==r['links'] and stat.S_IMODE(s.st_mode)==r['mode'];b=p.read_bytes();assert len(b)==r['bytes'] and H(b)==r['sha256']
def scan(root,expected):
 start=time.monotonic();rows=[];allocated=root.lstat().st_blocks*512;logical=0
 assert stat.S_IMODE(root.lstat().st_mode)==expected['root_mode'] and root.resolve()==root
 for parent,dirs,files in os.walk(root,followlinks=False):
  for name in sorted(dirs+files):
   p=Path(parent)/name;s=p.lstat();assert p.resolve()==p and len(rows)<32768 and time.monotonic()-start<120
   row={'path':p.relative_to(root).as_posix(),'mode':stat.S_IMODE(s.st_mode)};allocated+=s.st_blocks*512
   if stat.S_ISDIR(s.st_mode):row['kind']='directory'
   else:
    assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304
    # Opaque byte hashing, no deserialization of numeric inputs or Git objects.
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC);hash=hashlib.sha256();n=0
    try:
     before=os.fstat(fd);assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
     while True:
      part=os.read(fd,min(65536,s.st_size-n+1))
      if not part:break
      n+=len(part);assert n<=s.st_size;hash.update(part)
     assert n==s.st_size
     after=os.fstat(fd);again=p.lstat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)==(again.st_dev,again.st_ino,again.st_size,again.st_mtime_ns,again.st_ctime_ns)
    finally:os.close(fd)
    row.update(bytes=n,sha256=hash.hexdigest(),kind='file');logical+=n
   rows.append(row)
 assert sorted(rows,key=lambda r:r['path'])==expected['members']
 return {'files':sum(r['kind']=='file' for r in rows),'directories_excluding_root':sum(r['kind']=='directory' for r in rows),'logical':logical,'allocated_including_root':allocated,'nonGit_files':sum(r['kind']=='file' and not r['path'].startswith('.git/') for r in rows)}
parent=scan(P,J(A/'ACTUAL_PARENT_BASELINE01.json'));capsule=scan(C,J(A/'CAPSULE_BASELINE_OBSERVATION01.json'));assert parent['files']==10 and parent['directories_excluding_root']==2;assert capsule['files']==663 and capsule['nonGit_files']==288 and capsule['logical']==6782177 and capsule['allocated_including_root']==9543680
for row in J(A/'ACTUAL_PARENT_COMPOSITION02.json')['copied_members']:
 original=Path(row['original_path']);actual=P/row['path'];assert original.read_bytes()==actual.read_bytes() and H(actual.read_bytes())==row['sha256'] and stat.S_IMODE(actual.lstat().st_mode)==row['mode']
assert H((P/'launch_success01.py').read_bytes())=='7a197e2f57db3fff44fce453356d187f62dce5f119125e6814831eb6008f38dc';assert H((P/'held_outcome02.py').read_bytes())=='95affaa3867b0f50dedc706121b47304126c6def39715133414ef149b9eae153'
actual=J(P/'release-unreleased01.json');request=J(P/'request-unreleased01.json');proposed=J(A/'NATIVE_CONTRACT_PROPOSAL01.json')
assert actual['status']=='UNRELEASED-investigation-template' and request['status']=='UNRELEASED-parent-preparation';assert proposed['status']=='released-native-engineering' and proposed['remaining']==[]
proofs=('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256')
assert all(proposed[k] is None and actual[k] is None for k in proofs)
assert {k:v for k,v in actual.items() if k not in ('status','remaining')}=={k:v for k,v in proposed.items() if k not in ('status','remaining')}
contract=H(json.dumps({k:v for k,v in proposed.items() if k not in proofs},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode());assert contract=='17e513bb0fa4ae667c822d80118578ae487138a3c6ad1cdd1123b7d68c435110'
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
semantic=load(P/'held_outcome02.py','composition_semantic');reader=semantic.Reader(C);reg=semantic.sources(reader,actual)
assert reg['program_id']==actual['program_id'] and len(actual['source_files'])==204 and set(actual['cases'])=={'success','second_target_publication_failure'}
case_results={}
for case,entry in actual['cases'].items():
 exp=reg['experiments'][entry['identity']];assert exp==entry['experiment'];assert reg['families'][exp['family']]==actual['family'];assert exp['parent'] is None and len(exp['inputs'])==33 and len(exp['outputs'])==6
 for name in exp['inputs']:semantic.input_body(reader,exp,name)
 job=json.loads(semantic.input_body(reader,exp,'execution_job'));assert entry['job_resources']==job['resources'];p=job['resources'];G=1024**3
 assert p['memory_max_bytes']==p['memory_high_bytes']==3*G and p['reserve_bytes']==3*G and p['start_reserve_bytes']==6*G and p['wall_seconds']==1800 and p['disk_floor_bytes']==10*G and p['disk_paths']==[str(C)] and p['native_unit_limits']=={'file_size_bytes':4*1024**2}
 assert p['storage_budget']=={'root':str(C),'limits':{'max_allocated_bytes':G,'max_logical_bytes':G,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}
 ext=exp['cumulative_budget_extension'];eb=reader.body(ext['extension']['path']);review=reader.body(ext['review']['path']);assert H(eb)==ext['extension']['sha256']=='b1d56965524c870c3233e828cc94f28402c4d9b0cffe82f4d87bf090cbe3ce1c';assert H(review)==ext['review']['sha256']=='e317a6e59b79036376dc055c8aa42db6366bf230b151b1cd66404576752e58f7'
 for base in ('research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(C/base/entry['identity'])
 case_results[case]={'identity':entry['identity'],'inputs':len(exp['inputs']),'outputs':exp['outputs'],'job_resources':p,'extension_sha256':H(eb),'review_sha256':H(review)}
assert actual['family']['attempt_budget']==2 and actual['family']['prior_attempts']==0
runtimepath=C/'fixture_tools/runtime_gate01.py';assert H(runtimepath.read_bytes())==actual['source_files']['fixture_tools/runtime_gate01.py'];runtime=load(runtimepath,'composition_runtime');os.chdir(C);runtime_result=runtime.check(C,actual['runtime']);os.chdir(R)
reader.recheck();assert len(actual['runtime']['distribution_records'])==251
assert not os.path.lexists(P/'attempt');assert b'ValueError: unreleased or different finite parent' in (A/'DEFAULT_UNRELEASED_CHECK01.stderr').read_bytes()
selected=[]
for d in Path('/proc').iterdir():
 if not d.name.isdecimal() or int(d.name)==os.getpid():continue
 try:args=(d/'cmdline').read_bytes().split(b'\0')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if b'tradingagents.research.onchain_replication.job' in args or any(Path(a.decode('utf8','replace')).name in ('outer_controller01.py','launch_success01.py') for a in args if a):selected.append(int(d.name))
assert not selected;assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
# Complete post-read membership is rejoined rather than assuming no side effects.
assert scan(P,J(A/'ACTUAL_PARENT_BASELINE01.json'))==parent;assert scan(C,J(A/'CAPSULE_BASELINE_OBSERVATION01.json'))==capsule
out={'schema_version':1,'decision':'accepted_draft_composition_and_baseline_scope_only','author_manifest_sha256':H((A/'MANIFEST01.json').read_bytes()),'parent':parent,'capsule':capsule,'current_committed_source_registration_bodies':205,'cases':case_results,'contract_sha256':contract,'runtime_records':251,'runtime_metadata_observation':runtime_result,'selected_process_pids':selected,'actual_native_release':False,'actual_recovery':False,'genuine_claim_or_admission':False,'qualification':'Original and final body/mode membership; opaque inputs only; named RECORD metadata, not installed dependency-body backup; no launch or native enforcement proof.'}
(R/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print('PASS full parent10files2dirs/capsule663files262dirs current-body+mode membership twice;205Git bodies/both33inputs/sixoutputs;251runtime metadata; draft-only exact contract, no claim/attempt/process.')

import hashlib,json,os,shutil,stat,time
from pathlib import Path
from datetime import datetime,timezone
B=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources');D=B/'held-consumer-final-composition-root-preparation01-2026-10-03';assert not D.exists();D.mkdir()
CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');start=time.monotonic();rows=[];total=allocated=0;H=lambda b:hashlib.sha256(b).hexdigest()
protected={'.env','.ssh','keys','apis','hf_token.txt'}
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def visit(root):
 global total,allocated
 assert root.resolve()==root and root.lstat().st_dev==CAP.lstat().st_dev
 before=root.lstat();allocated+=before.st_blocks*512
 for p in sorted(root.iterdir(),key=lambda p:p.name):
  assert time.monotonic()-start<120 and len(rows)<32768
  relative=str(p.relative_to(CAP));assert len(relative.encode())<=2048 and len(p.relative_to(CAP).parts)<=32 and not any(x.lower() in protected or x.lower().endswith(('.pem','.key')) for x in p.relative_to(CAP).parts)
  s=p.lstat();r={'path':relative,'mode':stat.S_IMODE(s.st_mode)};assert p.resolve()==p
  if stat.S_ISDIR(s.st_mode):r['kind']='directory';rows.append(r);visit(p)
  else:
   assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304
   fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
   try:
    assert signature(os.fstat(fd))==signature(s);hash=hashlib.sha256();n=0
    while True:
     data=os.read(fd,min(65536,s.st_size-n+1))
     if not data:break
     n+=len(data);assert n<=s.st_size;hash.update(data)
    assert n==s.st_size and signature(os.fstat(fd))==signature(s)==signature(p.lstat())
   finally:os.close(fd)
   r.update(kind='file',bytes=n,sha256=hash.hexdigest());total+=n;allocated+=s.st_blocks*512;rows.append(r)
  assert total<=128*1024**2 and allocated<=128*1024**2
 assert signature(root.lstat())==signature(before)
visit(CAP);rows.sort(key=lambda r:r['path']);manifest={'schema_version':1,'root_mode':stat.S_IMODE(CAP.lstat().st_mode),'members':rows};raw=(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode();(D/'CAPSULE_BASELINE_OBSERVATION01.json').write_bytes(raw)
assert len([r for r in rows if r['kind']=='file' and not r['path'].startswith('.git/')])==288
ids=['original-import-held-success-20261003-01','original-import-held-publication-failure-20261003-01'];namespaces=[]
for identity in ids:
 for path in (CAP/'research_runs'/identity,CAP/'fixture_outer'/identity,CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity):namespaces.append({'path':str(path),'lexists':os.path.lexists(path)})
selected=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal() or int(p.name)==os.getpid():continue
 try:
  args=(p/'cmdline').read_bytes().split(b'\0')
  if b'tradingagents.research.onchain_replication.job' in args or any(Path(x.decode('utf-8','replace')).name in ('outer_controller01.py','launch_success01.py') for x in args if x):selected.append(int(p.name))
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
receipt={'schema_version':1,'observed_utc':datetime.now(timezone.utc).isoformat(),'scope':'read-only full capsule baseline observation; not capture or release','capsule_root':str(CAP),'expected_source':'d443208795f59292c156c5b81b687594efacea4d','manifest_sha256':H(raw),'file_count':sum(r['kind']=='file' for r in rows),'directory_count':sum(r['kind']=='directory' for r in rows),'nonGit_file_count':288,'logical_file_bytes':total,'allocated_root_and_member_bytes':allocated,'all_members_regular_or_directory':True,'single_link_files':True,'per_file_bytes_limit':4194304,'fresh_namespaces':namespaces,'selected_process_pids':selected,'mem_available_bytes':mem,'disk_free_bytes':shutil.disk_usage(CAP).free,'physical_ram_ceiling_bytes':16135790592,'disk_floor_bytes':10737418240,'source_capacity_or_native_release_proved':False,'complete_external_current_scope_recovery':False}
(D/'READBACK01.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n');print('capsule observation',H(raw),sum(r['kind']=='file' for r in rows),total,allocated,'mem',mem,'free',receipt['disk_free_bytes'],'selected',selected)

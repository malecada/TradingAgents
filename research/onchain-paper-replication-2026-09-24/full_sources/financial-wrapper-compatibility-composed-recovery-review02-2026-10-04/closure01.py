from pathlib import Path
import os,stat,json,hashlib,time
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-wrapper-compatibility-composed-recovery-correction02-2026-10-04';D=B/'financial-wrapper-compatibility-composed-recovery-root02-2026-10-04';checks=[];reads={};start=time.monotonic()
sha=lambda b:hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,pin=None):
 p=Path(p);s=p.lstat();sig=lambda z:(z.st_dev,z.st_ino,z.st_mode,z.st_nlink,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 ok(p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded regular '+str(p));b=p.read_bytes();ok(sig(s)==sig(p.lstat()),'stable read');ok(pin is None or sha(b)==pin,'pin '+str(p));reads[str(p)]=(sig(s),sha(b),len(b));ok(sum(x[2] for x in reads.values())<64*1024**2 and time.monotonic()-start<120,'finite review');return b
def j(p,pin=None):return json.loads(read(p,pin))
manifest=j(A/'MANIFEST01.json','7770b127e03f3c6ef0a3169844c6cb8bccba3a7eada3f401d2f88487434cc76e');names=[];todo=[A]
while todo:
 p=todo.pop()
 with os.scandir(p) as it:
  for e in it:
   n=Path(e.path).relative_to(A).as_posix()
   if n=='MANIFEST01.json':continue
   names.append(n)
   if e.is_dir(follow_symlinks=False):todo.append(Path(e.path))
ok(sorted(names)==sorted(x['path'] for x in manifest['members']),'complete author scope exact no extra');special=[]
for x in manifest['members']:
 p=A/x['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==x['mode'],'literal author mode')
 if x['kind']=='file':
  ok(stat.S_ISREG(s.st_mode) and s.st_size==x['bytes'],'author regular extent')
  if s.st_nlink==1 and s.st_size<=4194304:read(p,x['sha256'])
  else:special.append({'path':x['path'],'kind':x['kind'],'bytes':s.st_size,'nlink':s.st_nlink,'metadata_only':True})
 elif x['kind']=='directory':ok(stat.S_ISDIR(s.st_mode),'literal dir')
 elif x['kind']=='fifo':ok(stat.S_ISFIFO(s.st_mode),'literal fifo');special.append({'path':x['path'],'kind':'fifo','metadata_only':True})
 elif x['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(p)==x['target'],'literal link');special.append({'path':x['path'],'kind':'symlink','target':x['target'],'metadata_only':True})
 else:raise AssertionError(x)
measured=j(D/'MEASURED02.stdout','87d9be65addeb2f43f96606f6d0b5daf4e8ad787b40db395de0f141d7b8299d3');terminal=j(D/'ROOT_MEASUREMENT02.json','f5f39af820922a2bb4b38762bd9f4a2218790c52504a67eee4b8620494deecf7');ok(terminal['actual_root_observed_child_exit']==0 and not Path('/proc',str(terminal['child_pid'])).exists(),'real completed child absent');ok(read(D/'MEASURED02.stderr')==b'' and terminal['stdout_sha256']==sha(read(D/'MEASURED02.stdout')),'raw stdout stderr joins');ok(measured['files_read']==1727 and measured['bytes_read']==84824406 and measured['highest_actual_allowance']==19 and measured['numerical_authority'] is False,'actual count and boundary')
cfg=j(A/'INPUTS01.json');P={k:Path(v) for k,v in cfg['paths'].items()};receipt=j(P['receiver']/'FLAT_RECOVERY01.json')
for role,key,out in [('delta','restored','flat-operational-delta01'),('failed_delta','failed_restored','flat-failed-remote02-01')]:
 rec=receipt[key];md=j(P['receiver']/out/rec['metadata_file'],rec['metadata_sha256'])
 for row in md['manifest']['members']:
  if row['kind']=='file':ok(read(P[role]/'snapshot'/row['path'],row['sha256'])==read(P['receiver']/out/md['flat_members'][row['path']],row['sha256']),'every new flat/snapshot join')
failed=j(P['failed_delta']/'ORIGINAL_FAILED_ROOT_SCOPE43.json');fr=Path(failed['root']);seen=[];todo=[fr]
while todo:
 p=todo.pop()
 with os.scandir(p) as it:
  for e in it:
   seen.append(Path(e.path).relative_to(fr).as_posix())
   if e.is_dir(follow_symlinks=False):todo.append(Path(e.path))
ok(set(seen)=={x['path'] for x in failed['members'] if x['path']!='.'},'complete failed actual root43')
for x in failed['members']:
 p=fr if x['path']=='.' else fr/x['path'];ok(stat.S_IMODE(p.lstat().st_mode)==x['mode'],'failed original literal mode')
 if x['kind']=='file':read(p,x['sha256'])
fc=j(P['failed_delta']/'CAPTURE01.json');ok(fc['Root_outer_exit']==1 and fc['original_init_observed_exit'] is None and fc['separate_init_actual_reaped_exit']==0 and fc['historical_changed_directory_path_or_field'] is None and fc['actual_external_or_flat_receipt'] is None,'preserved raw unknowns and original failure')
for x in j(P['delta']/'ORIGIN_MAP01.json')['origins']:
 p=Path(x['original']);ok(read(p,x['sha256'])==read(P['delta']/'snapshot'/x['path']) and stat.S_IMODE(p.lstat().st_mode)==x['original_mode'],'all genuine delta origin body/mode')
# Literal receipt copying only after original content authentication. Copy mode is private;
# original modes are separately recorded, never claimed to be restored POSIX modes.
(H/'receipts').mkdir(mode=0o700);(H/'evidence').mkdir(mode=0o700);provenance=[];refs=[]
originals=[Path(x['path']) for x in measured['recovery_receipts']]+[D/'ROOT_MEASUREMENT02.json',D/'MEASURED02.stdout',D/'MEASURED02.stderr']
ok(len(set(originals))==len(originals),'unique genuine receipt paths')
for i,p in enumerate(originals):
 b=read(p);q=H/'receipts'/('%03d-'%i+p.name);q.write_bytes(b);q.chmod(0o600);refs.append({'path':str(q),'sha256':sha(b)});provenance.append({'path':str(q),'original_path':str(p),'original_mode':stat.S_IMODE(p.lstat().st_mode),'copy_mode':0o600,'bytes':len(b),'sha256':sha(b)})
prior=B/'financial-wrapper-compatibility-composed-recovery-review01-2026-10-04'
for i,p in enumerate([A/'verify02.py',A/'owned_io.py',A/'INVERSE01.json',A/'INPUTS01.json',A/'MANIFEST01.json',A/'MACHINE01.json',A/'REPORT01.md',prior/'MANIFEST01.json',prior/'MACHINE01.json',prior/'WITNESS01.json',prior/'WITNESS02.json',prior/'witness01.py',prior/'witness02.py']):
 b=read(p);q=H/'evidence'/('%02d-'%i+p.name);q.write_bytes(b);q.chmod(0o600);provenance.append({'path':str(q),'original_path':str(p),'original_mode':stat.S_IMODE(p.lstat().st_mode),'copy_mode':0o600,'bytes':len(b),'sha256':sha(b)})
for p,(ss,h,n) in reads.items():
 s=Path(p).lstat();ok((s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==ss,'whole final literal read signature')
result={'assertions':len(checks),'checks':checks,'author_typed_members':len(names),'special_negative_controls_metadata_only':special,'actual_receipts':refs,'receipt_original_count':len(measured['recovery_receipts']),'actual_receipt_copies':len(refs),'provenance':provenance,'actual_measurement_files':1727,'actual_measurement_bytes':84824406,'independent_additional_files':len(reads),'independent_additional_bytes':sum(x[2] for x in reads.values()),'numerical_authority':False}
(H/'CLOSURE01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','provenance','actual_receipts','special_negative_controls_metadata_only']}))

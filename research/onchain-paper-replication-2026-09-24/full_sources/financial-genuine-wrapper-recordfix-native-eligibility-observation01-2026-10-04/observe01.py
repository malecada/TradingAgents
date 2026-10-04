import ast,datetime,hashlib,json,os,shutil,stat,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;MAIN=BASE.parents[2]
INV=BASE/'financial-genuine-wrapper-recordfix-launch-command-investigation01-2026-10-04'
checks=[];operations=[];begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def command(argv,cwd=None):
 start=time.monotonic();p=subprocess.run(argv,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15,check=False);row={'argv':argv,'cwd':str(cwd) if cwd else None,'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'seconds':time.monotonic()-start};operations.append(row);return row
m=load(INV/'MANIFEST01.json');check(sha((INV/'MANIFEST01.json').read_bytes()).startswith('198764'),'actual command investigation manifest198764')
for r in m['members']:
 p=INV/r['path'];s=p.lstat();check(stat.S_IMODE(s.st_mode)==r['mode'],'command evidence mode '+r['path'])
 if r['kind']=='file':check(s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256'],'command evidence body '+r['path'])
cmd=load(INV/'COMMAND01.json');check(sha((INV/'COMMAND01.json').read_bytes())=='ade454808a2a5a435e6c0eee6e42ae4d4fbc84adb38ecf2b796ae2bdb11b0cc1','command pin')
qpath=Path(cmd['argv'][4]);q=load(qpath);CAP=Path(q['capsule_root']);PARENT=Path(q['parent_root']);identity=q['identity'];pre=load(INV/'PRELAUNCH_READBACK_TEMPLATE01.json')
check(sha(qpath.read_bytes())=='28f2ae5340d38ac71450c8947c5b1ad30ac4192481da81596684445c9cf9b52e','current final Q28f')
check(cmd['argv'][2]==str(PARENT/'parent01.py') and cmd['cwd']==str(PARENT) and cmd['argv'][6]==sha(qpath.read_bytes()) and cmd['argv'][7]=='--launch','actual outer command metadata')
for r in load(INV/'SOURCE_READBACK01.json')['source_pins']:
 p=Path(r['origin']);check(p.resolve()==p and p.is_file() and sha(p.read_bytes())==r['sha256'] and p.stat().st_size==r['bytes'],'actual installed source/proof '+p.name)
regpath=CAP/q['registration'];check(sha(regpath.read_bytes())==q['registration_sha256']=='4474df26460aab41281bfdcc311129b613a90d76963e853858841200d9faa69a','actual fixed gate')
g=load(regpath);exp=g['experiments'][identity];family=g['families'][exp['family']];check(family['attempt_budget']==18 and family['prior_attempts']==0,'numerical18 prior0')
check(exp['source_files']==q['source_files'] and len(q['source_files'])==324,'324 exact source map')
for rel,h in q['source_files'].items():
 p=CAP/rel;check(p.resolve()==p and stat.S_ISREG(p.lstat().st_mode) and sha(p.read_bytes())==h,'source '+rel)
for role,ref in exp['inputs'].items():check(sha((CAP/ref['path']).read_bytes())==ref['sha256']==q['input_hashes'][role],'eight role '+role)
closure=load(CAP/exp['inputs']['source_closure']['path']);check(len(closure['installed'])==194,'scientific closure194')
for rel,h in closure['installed'].items():check(sha((CAP/rel).read_bytes())==h,'implementation '+rel)
head=command(['git','rev-parse','HEAD'],CAP);check(head['exit']==0 and head['stdout'].strip()==q['source']=='649fb8a11089524aaef7843dffeeb90a3a55ca17','actual source HEAD649')
tree=command(['git','ls-tree','-r','--full-tree','HEAD'],CAP);check(tree['exit']==0,'actual git tree read');gitrows=[]
for line in tree['stdout'].splitlines():
 left,rel=line.split('\t');mode,kind,oid=left.split();p=CAP/rel;b=p.read_bytes();check(kind=='blob' and mode in ('100644','100755') and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'actual Git blob '+rel);check(('100755' if p.stat().st_mode&0o111 else '100644')==mode,'actual Git mode '+rel);gitrows.append({'path':rel,'mode':mode,'oid':oid,'sha256':sha(b)})
check(len(gitrows)==325,'actual all325tracked')
# Exact fixed five namespaces, no traversal of numerical bodies.
namespaces=[]
for name,r in pre['namespace_requirements'].items():
 p=Path(r['path']);namespaces.append({'name':name,'path':str(p),'lexically_present':os.path.lexists(p),'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
# Only current and original failed financial research_runs directory metadata.
claimroots=[]
for cap in (CAP,Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')):
 root=cap/'research_runs';entries=[]
 if os.path.lexists(root):
  check(root.resolve()==root and root.is_dir(),'canonical claim root')
  for p in sorted(root.iterdir()):
   check(len(entries)<512,'bounded claim namespaces');entries.append({'name':p.name,'kind':'directory' if stat.S_ISDIR(p.lstat().st_mode) else 'other','claim_present':os.path.lexists(p/'claim.json'),'terminal_present':os.path.lexists(p/'terminal.json')})
 claimroots.append({'root':str(root),'lexically_present':os.path.lexists(root),'entries':entries})
oldroot=BASE/'financial-genuine-wrapper-first-attempt-closure-review01-2026-10-04';old=load(oldroot/'READBACK01.json');oldsummary={k:old.get(k) for k in ('decision','identity','claim_count','checkpoint_available','numerical_claim_spent','actual_parent_exit','native_noncreation')};oldsummary.update(receipt_sha256=sha((oldroot/'READBACK01.json').read_bytes()),historical_receipt_not_current_reclassification=True,old_outer_identity_permanently_reserved=True)
# /proc argv is parsed for exact module tokens. Unmatched command lines are never retained.
proc_begin=datetime.datetime.now(datetime.timezone.utc).isoformat();matches=[];races=[];denied=[];scanned=0
module='tradingagents.research.onchain_replication.job';study=('/home/malecada/master_thesis/onchain-financial-isolation/','/home/malecada/master_thesis/onchain-fixture-isolation/')
for p in sorted(Path('/proc').iterdir(),key=lambda p:p.name):
 if not p.name.isdigit():continue
 try:
  scanned+=1;raw=(p/'cmdline').read_bytes();check(len(raw)<=1024**2,'bounded proc cmdline '+p.name);argv=[x.decode(errors='replace') for x in raw.split(b'\0') if x];cg=(p/'cgroup').read_text();exactmodule=any(argv[i]=='-m' and argv[i+1]==module for i in range(max(0,len(argv)-1)));script=next((a for a in argv[1:3] if a.startswith(study) and Path(a).name in ('parent01.py','supervisor01.py')),None);native='onchain-replication-' in cg
  if exactmodule or script or native:
   rawstat=(p/'stat').read_text();parts=rawstat[rawstat.rfind(')')+2:].split();cwd=os.readlink(p/'cwd');matches.append({'pid':int(p.name),'start_ticks':parts[19],'state':parts[0],'ppid':int(parts[1]),'pgid':int(parts[2]),'sid':int(parts[3]),'exact_job_module':exactmodule,'study_parent_script':script,'native_cgroup':native,'cwd':cwd,'cgroup':cg,'argv':argv if exactmodule or script else None})
 except (FileNotFoundError,ProcessLookupError):races.append(int(p.name))
 except PermissionError:denied.append(int(p.name))
proc_end=datetime.datetime.now(datetime.timezone.utc).isoformat()
units=command(['systemctl','--user','list-units','--all','--type=service','--plain','--no-legend','--no-pager','onchain-replication-*.service']);failed=command(['systemctl','--user','list-units','--state=failed','--all','--plain','--no-legend','--no-pager']);unitrows=[]
if units['exit']==0:
 for line in units['stdout'].splitlines():
  fields=line.split()
  if not fields:continue
  if fields[0]=='●':fields=fields[1:]
  check(len(unitrows)<128,'bounded selected unit census');unitrows.append({'unit':fields[0],'load':fields[1],'active':fields[2],'sub':fields[3]})
mem={}
for line in Path('/proc/meminfo').read_text().splitlines():
 k,v=line.split(':',1)
 if k in ('MemTotal','MemAvailable','SwapTotal','SwapFree'):mem[k+'_bytes']=int(v.split()[0])*1024
resources={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),**mem,'cpu_affinity':sorted(os.sched_getaffinity(0)),'logical_cpu_count':os.cpu_count(),'disks':{str(p):dict(zip(('total','used','free'),shutil.disk_usage(p))) for p in (CAP,PARENT,MAIN)}}
# Metadata-only complete current Source and Parent storage census, includes .git.
storage=[]
for root in (CAP,PARENT):
 start=time.monotonic();entries=0;logical=allocated=0;maxdepth=0
 def walk(p,depth):
  global entries,logical,allocated,maxdepth
  s=p.lstat();entries+=1;allocated+=s.st_blocks*512;maxdepth=max(maxdepth,depth);check(entries<=32768 and depth<=32 and time.monotonic()-start<10,'bounded storage metadata')
  if stat.S_ISDIR(s.st_mode):
   for child in p.iterdir():walk(child,depth+1)
  elif stat.S_ISREG(s.st_mode):logical+=s.st_size
  else:raise ValueError('unexpected storage type '+str(p))
 walk(root,0);storage.append({'root':str(root),'entries_including_root':entries,'logical_file_bytes':logical,'allocated_bytes_including_directories':allocated,'max_depth':maxdepth,'seconds':time.monotonic()-start})
end=datetime.datetime.now(datetime.timezone.utc).isoformat();out={'schema_version':1,'decision':'READ_ONLY_CURRENT_OBSERVATIONS_NO_LAUNCH_AUTHORITY','begin':begin,'end':end,'checks':len(checks),'check_names':checks,'command_manifest_sha256':sha((INV/'MANIFEST01.json').read_bytes()),'command_sha256':sha((INV/'COMMAND01.json').read_bytes()),'source_head':q['source'],'source_git_rows':gitrows,'identity':identity,'numerical_family':family,'fixed_namespaces':namespaces,'claim_namespace_census':claimroots,'historical_reserved_outer':oldsummary,'proc':{'begin':proc_begin,'end':proc_end,'scanned':scanned,'matches':matches,'vanished_races':races,'permission_denied':denied,'qualification':'point-in-time observable process census; unmatched argv not retained; no continuous or privileged completeness claim'},'selected_systemd_units':unitrows,'resources':resources,'whole_storage_metadata':storage,'read_only_commands':operations,'native_creation_or_mutation':False,'admission_or_preflight_calls':0,'numerical_imports':False,'fresh_native_unit':None,'dispatch_authority':False,'measured_numerical_capacity':None,'must_observe_again_at_dispatch':True}
with (HERE/'OBSERVATION01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'begin':begin,'end':end,'checks':len(checks),'fixed_namespaces':namespaces,'proc_matches':matches,'proc_denied':denied,'selected_units':unitrows,'resources':resources,'storage':storage,'claimroots':claimroots}))

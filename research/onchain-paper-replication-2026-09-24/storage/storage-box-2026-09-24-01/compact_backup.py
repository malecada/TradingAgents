"""One bounded snapshot upload and full byte round-trip; no raw-data relocation."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, tarfile
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent
from tradingagents.research.onchain_replication.resources import guarded_run,assert_guarded_worker
from tradingagents.research.lifecycle import _immutable
GIB=1024**3
CONNECTION_BYTES=(HERE/'connection.json').read_bytes()
CONNECTION=json.loads(CONNECTION_BYTES)
KEY=CONNECTION['public_key_path'].removesuffix('.pub')
KNOWN_HOSTS=str(Path(KEY).parent/('known_hosts_storagebox_'+CONNECTION['user']))
SSH=['ssh','-p',str(CONNECTION['port']),'-i',KEY,'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','UserKnownHostsFile='+KNOWN_HOSTS,'-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2']
HOST=CONNECTION['user']+'@'+CONNECTION['host']
SCP=['scp','-q','-P',str(CONNECTION['port']),*SSH[3:]]
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while chunk:=f.read(1024**2):h.update(chunk)
 return h.hexdigest()
def call(args,**kwargs):return subprocess.run(args,check=True,timeout=180,**kwargs)
def worker():
 assert_guarded_worker(HERE/'compact-guard',sys.orig_argv,required_paths=[ROOT],wall_seconds=900,memory_max_bytes=512*1024**2,memory_high_bytes=384*1024**2)
 contract_bytes=(HERE/'contract.json').read_bytes()
 c=json.loads(contract_bytes)
 assert hashlib.sha256(CONNECTION_BYTES).hexdigest()==c['input_sha256']['connection.json']
 assert sha(__file__)==c['script_sha256']
 assert sha(ROOT/'tradingagents/research/onchain_replication/resources.py')==c['resource_guard_sha256']
 for name,h in c['input_sha256'].items():assert sha(HERE/name)==h
 _immutable(HERE/'intent.json',{'contract_sha256':hashlib.sha256(contract_bytes).hexdigest(),'scope':c['scope'],'remote':c['remote']})
 env=dict(os.environ,GIT_NO_LAZY_FETCH='1')
 try:
  names=subprocess.check_output(['git','ls-tree','-r','--name-only',c['commit'],'--',*c['prefixes']],cwd=ROOT,env=env,text=True).splitlines()
  assert 0<len(names)<=30000
  assert all(not any(part in ('keys','apis','.git','.venv','node_modules') or part.startswith('.env') for part in Path(n).parts) for n in names)
  archive=HERE/'compact.tar.gz'
  proc=subprocess.Popen(['git','archive','--format=tar.gz',c['commit'],'--',*c['prefixes']],cwd=ROOT,env=env,stdout=subprocess.PIPE)
  try:
   total=0
   with archive.open('xb') as f:
    while chunk:=proc.stdout.read(1024**2):
     total+=len(chunk)
     if total>128*1024**2:raise ValueError('compact archive exceeds bound')
     f.write(chunk)
   if proc.wait(timeout=60):raise ValueError('Git archive failed')
  finally:
   if proc.poll() is None:proc.kill();proc.wait()
  members={};unpacked=0
  with tarfile.open(archive,'r:gz') as tar:
   for m in tar:
    if m.isdir():continue
    if not m.isfile() or m.name not in names or m.name in members:raise ValueError('unexpected archive member')
    unpacked+=m.size
    if unpacked>256*1024**2:raise ValueError('uncompressed snapshot exceeds bound')
    h=hashlib.sha256()
    with tar.extractfile(m) as f:
     while chunk:=f.read(1024**2):h.update(chunk)
    members[m.name]={'bytes':m.size,'sha256':h.hexdigest()}
  if set(members)!=set(names):raise ValueError('Git/archive membership differs')
  _immutable(HERE/'snapshot-manifest.json',{'commit':c['commit'],'members':members,'member_count':len(members),'total_bytes':unpacked,'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'scope':c['scope']})
  call([*SSH,HOST,'mkdir','-p',c['remote_parent']],capture_output=True)
  call([*SSH,HOST,'mkdir',c['remote']],capture_output=True)
  files=['compact.tar.gz','snapshot-manifest.json','raw-source-inventory.json.gz','inventory-summary.json','connection.json','contract.json']
  dest=HERE/'recovered';dest.mkdir(exist_ok=False);receipts=[]
  for number,name in enumerate(files):
   p=HERE/name;before=sha(p);n=p.stat().st_size
   if n>128*1024**2:raise ValueError('upload member exceeds bound')
   call([*SCP,str(p),HOST+':'+c['remote']+'/'+name])
   call([*SCP,HOST+':'+c['remote']+'/'+name,str(dest/name)])
   if (dest/name).stat().st_size!=n or sha(dest/name)!=before or sha(p)!=before:raise ValueError('round-trip mismatch')
   receipt={'name':name,'bytes':n,'sha256':before,'upload_and_download_verified':True}
   _immutable(HERE/f'receipt-{number:02d}.json',receipt);receipts.append(receipt)
  record={'status':'complete','source_commit':c['commit'],'snapshot_members':len(members),'snapshot_uncompressed_bytes':unpacked,'roundtrip_files':receipts,'remote':c['remote'],'transaction_raw_files_uploaded':0,'raw_transaction_backup_verified':False,'originals_preserved':True,'scope':c['scope']}
  _immutable(HERE/'completion-payload.json',record)
  call([*SCP,str(HERE/'completion-payload.json'),HOST+':'+c['remote']+'/complete.json'])
  call([*SCP,HOST+':'+c['remote']+'/complete.json',str(dest/'complete.json')])
  if sha(dest/'complete.json')!=sha(HERE/'completion-payload.json'):raise ValueError('completion marker round-trip mismatch')
  _immutable(HERE/'complete.json',record)
  print(json.dumps({k:v for k,v in record.items() if k!='roundtrip_files'}),flush=True);return 0
 except BaseException as error:
  _immutable(HERE/'failed.json',{'status':'failed','error':type(error).__name__+': '+str(error),'remote':c['remote'],'no_automatic_retry':True});raise
if __name__=='__main__':
 if sys.argv[1:]==['--worker']:raise SystemExit(worker())
 if sys.argv[1:]:raise ValueError('unexpected argument')
 x=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker'],cwd=ROOT,receipt_dir=HERE/'compact-guard',memory_max_bytes=512*1024**2,memory_high_bytes=384*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=int(3.5*GIB),disk_paths=[ROOT],disk_floor_bytes=20*GIB,wall_seconds=900)
 print(json.dumps({k:x.get(k) for k in ('phase','child_exit_code','elapsed_seconds','peak_sampled_memory_current_bytes','cleanup_verified','limit_reason')}))
 raise SystemExit(0 if x.get('phase')=='complete' and x.get('child_exit_code')==0 and x.get('cleanup_verified') else 1)

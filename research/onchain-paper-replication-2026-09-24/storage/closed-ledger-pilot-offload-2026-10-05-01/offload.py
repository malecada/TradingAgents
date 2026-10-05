"""Preserve one closed SQLite ledger byte-for-byte; never opens it as SQLite."""
from pathlib import Path
import importlib.util
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
OLD=ROOT/'research/onchain-paper-replication-2026-09-24/storage/cold-offload-2026-09-29-03/offload.py'
spec=importlib.util.spec_from_file_location('retained_offload',OLD);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
GIB=1024**3


def eligibility(root,c):
 row=c['files'][0];source=root/row['path']
 expected='research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-graph-resource-20260930-10/aggregation/ledger.sqlite'
 if len(c['files'])!=1 or row['path']!=expected or not 0<row['bytes']<=4*GIB or c['total_bytes']!=row['bytes']:raise ValueError('exact closed-ledger scope differs')
 for name,ref in c['closure'].items():
  path=root/ref['path']
  if old.sha(path)!=ref['sha256']:raise ValueError('closure binding differs: '+name)
 guard=json.loads((root/c['closure']['guard']['path']).read_bytes());owner=json.loads((root/c['closure']['owner']['path']).read_bytes())
 terminal=json.loads((root/c['closure']['terminal']['path']).read_bytes());claim=json.loads((root/c['closure']['claim']['path']).read_bytes())
 index=json.loads((root/c['closure']['artifact_index']['path']).read_bytes())
 if guard['phase']!='complete' or guard['cleanup_verified'] is not True or Path(guard['cgroup']).exists():raise ValueError('original guard not closed')
 if Path('/proc',str(owner['monitor_pid'])).exists():raise ValueError('original monitor PID present; manual exact reconciliation required')
 if terminal['status']!='complete' or terminal['experiment_id']!=claim['experiment_id'] or terminal['claim_sha256']!=c['closure']['claim']['sha256']:raise ValueError('closed claim differs')
 if terminal['output_sha256']['artifact-index.json']!=c['closure']['artifact_index']['sha256'] or index[row['path']]!={'bytes':row['bytes'],'sha256':row['sha256']}:raise ValueError('ledger artifact binding differs')
 if owner['experiment']!=claim['experiment_id'] or guard['owner_identity']!=owner:raise ValueError('guard owner differs')
 if source.is_symlink() or source.stat().st_nlink!=1 or old.identity(source.stat())!=row['stat_identity']:raise ValueError('ledger stat differs')
 if any(source.with_name(source.name+s).exists() for s in ('-wal','-shm','-journal','.remote.json')):raise ValueError('sidecar/SQLite transient state requires reconciliation')
 if subprocess.check_output(['git','ls-files','--',row['path']],cwd=root):raise ValueError('tracked ledger refused')
 for p in (root/'research_runs').glob('*/claim.json'):
  if not (p.parent/'complete.json').exists() and not (p.parent/'failed.json').exists():
   active=json.loads(p.read_bytes())
   for info in active['experiment']['inputs'].values():
    target=(root/info['path']).resolve()
    if target==source.resolve() or (target.is_dir() and source.resolve().is_relative_to(target)):raise ValueError('active claim directly references ledger')
 return row


def verify_saved_graph(c):
 refs=c['accepted_saved_array_verification']
 for ref in [*refs.values(),c['producer_closure_review']]:
  if old.sha(ROOT/ref['path'])!=ref['sha256']:raise ValueError('accepted graph closure changed')
 result=json.loads((ROOT/refs['result.json']['path']).read_bytes())
 closure=json.loads((ROOT/refs['closure01.json']['path']).read_bytes())
 guard=json.loads((ROOT/refs['guard01/final.json']['path']).read_bytes())
 if result['status']!='complete' or result['source_claim']!='eth-paper-graph-resource-20260930-10' or closure['result']!=result:raise ValueError('saved graph verification differs')
 if result['claim_sha256']!=c['closure']['claim']['sha256'] or result['terminal_sha256']!=c['closure']['terminal']['sha256']:raise ValueError('saved graph closure identity differs')
 if guard['phase']!='complete' or guard['child_exit_code']!=0 or guard['cleanup_verified'] is not True or Path(guard['cgroup']).exists() or Path('/proc',str(guard['monitor_pid'])).exists():raise ValueError('saved graph verification remains owned')


def entry_bindings():
 bindings=json.loads((HERE/'bindings.json').read_bytes())
 release=json.loads((HERE/'release-bindings01.json').read_bytes())
 required_release={str((HERE/name).relative_to(ROOT)) for name in ('RELEASE_REVIEW.json','RELEASE_REVIEW.md','bindings.json')}
 if type(release) is not dict or set(release)!=required_release:raise ValueError('exact review/report/bindings release pins required')
 for path,h in {**bindings,**release}.items():
  if path in bindings and path in release and bindings[path]!=release[path]:raise ValueError('release binding conflicts')
  if old.sha(ROOT/path)!=h:raise ValueError('entry binding changed: '+path)
 review=json.loads((HERE/'RELEASE_REVIEW.json').read_bytes())
 if review['decision']!='accepted' or review['manifest_sha256']!=old.sha(HERE/'manifest.json') or review['worker_sha256']!=old.sha(HERE/'offload.py') or review['transport_sha256']!=old.sha(HERE/'transport.py') or review['bindings_sha256']!=old.sha(HERE/'bindings.json'):raise ValueError('exact independent release review required')
 return {**bindings,**release}


def preflight():
 bindings=entry_bindings();c=json.loads((HERE/'manifest.json').read_bytes())
 source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
 if branch!='research/onchain-paper-replication-2026-09-24':raise ValueError('unexpected source branch')
 remote=subprocess.check_output(['git','ls-remote','--exit-code','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]
 if remote!=source:raise ValueError('source not externally committed')
 release_path=str((HERE/'release-bindings01.json').relative_to(ROOT))
 if subprocess.check_output(['git','show',source+':'+release_path],cwd=ROOT)!=(HERE/'release-bindings01.json').read_bytes():raise ValueError('release table not committed')
 for path,h in bindings.items():
  if path==c['connection_path']:
   if subprocess.check_output(['git','ls-files','--',path],cwd=ROOT):raise ValueError('connection metadata must remain untracked')
  elif hashlib.sha256(subprocess.check_output(['git','show',source+':'+path],cwd=ROOT)).hexdigest()!=h:raise ValueError('binding not committed: '+path)
 for name in ('intent.json','complete.json','failed.json','guard01','preflight01.json'):
  if (HERE/name).exists() or (HERE/name).is_symlink():raise FileExistsError('identity reserved: '+name)
 units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True)
 if units.strip():raise ValueError('another native replication owner is active')
 row=eligibility(ROOT,c);verify_saved_graph(c)
 from tradingagents.research.onchain_replication.resources import mem_available
 available=mem_available();free=shutil.disk_usage(ROOT).free
 if available<int(3.5*GIB) or free<10*GIB+row['bytes']+16*1024**2:raise ValueError('startup RAM or full recovery scratch unavailable')
 old.publish(HERE/'preflight01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':source,'bindings_verified':len(bindings),'source_ledger_body_read':False,'workspace_free_bytes':free,'full_recovery_scratch_required_bytes':10*GIB+row['bytes']+16*1024**2,'mem_available_bytes':available,'source_stat_identity':row['stat_identity'],'no_active_unit':True,'no_retry':True})


def worker():
 from tradingagents.research.onchain_replication.resources import assert_guarded_worker
 for path,h in json.loads((HERE/'bindings.json').read_bytes()).items():
  if old.sha(ROOT/path)!=h:raise ValueError('source binding differs')
 c=json.loads((HERE/'manifest.json').read_bytes())
 entry_bindings();verify_saved_graph(c)
 pre=json.loads((HERE/'preflight01.json').read_bytes())
 if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=pre['head']:raise ValueError('source changed since preflight')
 policy=ROOT/c['disk_policy']
 if old.sha(policy)!=c['disk_policy_sha256'] or json.loads(policy.read_bytes())['disk_floor_bytes']!=10*GIB:raise ValueError('disk policy differs')
 assert_guarded_worker(HERE/'guard01',sys.orig_argv,required_paths=[ROOT],wall_seconds=14400,memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,disk_floor_bytes=10*GIB)
 row=eligibility(ROOT,c)
 if shutil.disk_usage(ROOT).free<10*GIB+row['bytes']+16*1024**2:raise ValueError('round-trip scratch unavailable')
 for kind in ('connection','transport'):
  if old.sha(ROOT/c[kind+'_path'])!=c[kind+'_sha256']:raise ValueError('transport binding differs')
 spec=importlib.util.spec_from_file_location('retained_transport',ROOT/c['transport_path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 transport=module.Transport(json.loads((ROOT/c['connection_path']).read_bytes()),rate=262144,maximum_payload_bytes=8*GIB)
 if transport.available()<row['bytes']+GIB:raise ValueError('remote capacity unavailable')
 old.publish(HERE/'intent.json',{'manifest_sha256':old.sha(HERE/'manifest.json'),'remote':c['remote'],'bytes':row['bytes'],'no_automatic_retry':True})
 try:
  transport.mkdir(c['remote'])
  transport.put(HERE/'manifest.json',c['remote']+'/manifest.json');transport.get(c['remote']+'/manifest.json',HERE/'recovered-manifest.json')
  if old.sha(HERE/'manifest.json')!=old.sha(HERE/'recovered-manifest.json'):raise ValueError('manifest roundtrip differs')
  record=old.offload_one(ROOT,HERE,row,0,c['remote'],transport)
  old.finish(HERE,{'files':[record],'bytes_moved':row['bytes'],'after_disk_free_bytes':shutil.disk_usage(ROOT).free,'qualification':'Closed graph10 ledger only, byte-roundtrip verified remote preservation; restore hash-verified bytes before any historical local-path verification. No rerun or graph/raw eviction.'},c['remote'],transport)
 except BaseException as e:
  old.publish(HERE/'failed.json',{'error':type(e).__name__+': '+str(e),'no_automatic_retry':True,'action':'Reconcile retained receipts and remote sidecar; preserve original and failed scratch. Never relaunch this identity.'});raise

if __name__=='__main__':
 sys.path.insert(0,str(ROOT))
 if sys.argv[1:]==['--worker']:worker()
 elif sys.argv[1:]:raise ValueError('unexpected argument')
 else:
  old.publish(HERE/'launch-attempt01.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':sys.orig_argv,'no_automatic_retry':True})
  try:
   preflight()
   from tradingagents.research.onchain_replication.resources import guarded_run
   r=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker'],cwd=ROOT,receipt_dir=HERE/'guard01',memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=int(3.5*GIB),disk_paths=[ROOT],disk_floor_bytes=10*GIB,wall_seconds=14400)
   code=0 if r['phase']=='complete' and r['cleanup_verified'] and r['child_exit_code']==0 else 1
   result={k:r.get(k) for k in ('phase','child_exit_code','cleanup_verified','limit_reason')}
   old.publish(HERE/'outer-exit01.json',{'actual_outer_exit':code,**result})
   print(json.dumps(result),flush=True)
  except BaseException as error:
   old.publish(HERE/'outer-exit01.json',{'actual_outer_exit':1,'error_type':type(error).__name__,'error':str(error),'no_automatic_retry':True});raise
  sys.exit(code)

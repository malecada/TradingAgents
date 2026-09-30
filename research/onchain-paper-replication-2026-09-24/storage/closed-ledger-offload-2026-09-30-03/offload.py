"""Preserve one closed SQLite ledger byte-for-byte; never opens it as SQLite."""
from pathlib import Path
import importlib.util
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
 expected='research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-graph-resource-20260930-05/aggregation/ledger.sqlite'
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


def worker():
 from tradingagents.research.onchain_replication.resources import assert_guarded_worker
 for path,h in json.loads((HERE/'bindings.json').read_bytes()).items():
  if old.sha(ROOT/path)!=h:raise ValueError('source binding differs')
 c=json.loads((HERE/'manifest.json').read_bytes())
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
  old.finish(HERE,{'files':[record],'bytes_moved':row['bytes'],'after_disk_free_bytes':shutil.disk_usage(ROOT).free,'qualification':'Closed graph05 ledger only, byte-roundtrip verified remote preservation; restore hash-verified bytes before any historical local-path verification. No rerun or graph/raw eviction.'},c['remote'],transport)
 except BaseException as e:
  old.publish(HERE/'failed.json',{'error':type(e).__name__+': '+str(e),'no_automatic_retry':True,'action':'Reconcile retained receipts and remote sidecar; preserve original and failed scratch. Never relaunch this identity.'});raise

if __name__=='__main__':
 sys.path.insert(0,str(ROOT))
 if sys.argv[1:]==['--worker']:worker()
 elif sys.argv[1:]:raise ValueError('unexpected argument')
 else:
  from tradingagents.research.onchain_replication.resources import guarded_run
  r=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker'],cwd=ROOT,receipt_dir=HERE/'guard01',memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=int(3.5*GIB),disk_paths=[ROOT],disk_floor_bytes=10*GIB,wall_seconds=14400)
  print(json.dumps({k:r.get(k) for k in ('phase','child_exit_code','cleanup_verified','limit_reason')}),flush=True)
  sys.exit(0 if r['phase']=='complete' and r['cleanup_verified'] and r['child_exit_code']==0 else 1)

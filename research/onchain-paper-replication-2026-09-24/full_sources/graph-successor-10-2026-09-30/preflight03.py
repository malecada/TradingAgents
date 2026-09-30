"""Fresh metadata/resource/ownership admission; no empirical body read or launch."""
from pathlib import Path
from previous_graph_requirement import verify as verify_previous_graph
from verification_requirement import verify as verify_offline_package
from preservation_requirement import verify_chain as verify_preservation
from types import SimpleNamespace
import datetime
import json
import shutil
import subprocess
import time
from tradingagents.research.onchain_replication.job import _admitted,workspace_binding,PREFIX
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.resources import mem_available,GIB
root=Path.cwd();directory=Path(__file__).resolve().parent
name='eth-paper-graph-resource-20260930-10';gate=str((directory/'gate-v3.json').relative_to(root))
preservation=verify_preservation(root)
previous_graph=verify_previous_graph(root)
package_verification=verify_offline_package(root)
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
a,job=_admitted(SimpleNamespace(root=root,registration=gate,experiment=name,source=source))
assert a.ready and a.effective_attempt_budget==60
for path,h in a.experiment['source_files'].items():assert file_hash(root/path)==h,path
for info in a.inputs.values():
 path=root/info['path'];assert path.stat().st_size<2_000_000
 assert file_hash(path)==info['sha256'],info['path']
assert inventory(root)==json.loads((directory/'environment.json').read_bytes())
assert workspace_binding(root)==json.loads((directory/'workspace.json').read_bytes())
for path in (root/'research_runs'/name,root/PREFIX/'runs'/name,root/PREFIX/'sources'/name):
 assert not path.exists() and not path.is_symlink(),str(path)
 ancestor=path.parent
 while not ancestor.exists():ancestor=ancestor.parent
 assert ancestor.resolve().is_relative_to(root) and ancestor.stat().st_dev==root.stat().st_dev
units=subprocess.check_output(['systemctl','--user','list-units','--state=active','--no-legend','onchain-replication-*.service'],text=True)
assert not units.strip(),units
final=json.loads((directory/'temp-check02/final.json').read_bytes())
assert final['phase']=='complete' and final['child_exit_code']==0 and final['cleanup_verified']
assert final['cwd']==str(root) and not Path(final['cgroup']).exists() and not Path('/proc',str(final['monitor_pid'])).exists()
assert 0<=time.monotonic()-final['monotonic_seconds']<=300,'temp check stale'
temp=json.loads((directory/'temp-check02/child.log').read_bytes())
assert temp['all_writable_candidates_on_guarded_volume'] and temp['workspace_device']==root.stat().st_dev
projection=json.loads((directory/'storage-projection.json').read_bytes());free=shutil.disk_usage(root).free;available=mem_available()
assert free>=job['resources']['disk_floor_bytes']+projection['projected_incremental_disk_requirement_bytes']
assert available>=job['resources']['start_reserve_bytes']+128*1024**2,'extra startup headroom unavailable'
stat=json.loads((directory/'metadata-preparation.json').read_bytes());spans=0
for day in stat['days']:
 path=root/day['mapping']['path'];assert file_hash(path)==day['mapping']['sha256']
 for span in json.loads(path.read_bytes())['spans']:
  body=Path(span['path']);assert body.is_file() and not body.is_symlink() and body.stat().st_size==span['stored_bytes'];spans+=1
r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'experiment':name,'registration_sha256':file_hash(directory/'gate-v3.json'),'effective_attempt_budget':60,'ready':True,'preservation_prerequisite':preservation,'previous_graph_prerequisite':previous_graph,'package_verification':package_verification,'source_pins_verified':len(a.experiment['source_files']),'compact_input_pins_verified':len(a.inputs),'raw_spans_stat_only':spans,'host_mem_available_bytes':available,'workspace_free_bytes':free,'planning_free_requirement_bytes':job['resources']['disk_floor_bytes']+projection['projected_incremental_disk_requirement_bytes'],'temp_check_final_sha256':file_hash(directory/'temp-check02/final.json'),'extra_startup_headroom_bytes':128*1024**2,'identity_absent':True,'active_units':0,'qualification':'No raw body, graph array or SQLite opened; no empirical claim or launch.'}
with (directory/'execution-preflight03.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
print(json.dumps(r,indent=2))

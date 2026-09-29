"""Read-only finite graph release preflight; never launches or claims a run.

Run after the named offline suite and independent release review close, and after
committing/pushing the exact gate/source. A fresh guarded temp-volume check is a
separate prerequisite. This check opens only registered compact metadata/source.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

from tradingagents.research.onchain_replication.job import _admitted, PREFIX
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.resources import mem_available

parser=argparse.ArgumentParser()
parser.add_argument('--temp-check',required=True,type=Path)
args=parser.parse_args()
root=Path.cwd()
directory=Path(__file__).resolve().parent
source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
name='eth-paper-graph-resource-20260929-03'
gate=directory/'gate-v2.json'
admission,job=_admitted(SimpleNamespace(root=root,registration=str(gate.relative_to(root)),
                                     experiment=name,source=source))
assert admission.ready and admission.effective_attempt_budget==52
for p in (root/'research_runs'/name,root/PREFIX/'runs'/name,root/PREFIX/'sources'/name):
    assert not p.exists(), 'exclusive identity already reserved: '+str(p)
for info in admission.inputs.values():
    assert file_hash(root/info['path'])==info['sha256'], 'registered metadata drift'
assert inventory(root)==json.loads((directory/'environment.json').read_bytes())
projection=json.loads((root/admission.inputs['storage_projection']['path']).read_bytes())
policy=job['resources']
free=shutil.disk_usage(root).free
required=policy['disk_floor_bytes']+projection['projected_incremental_disk_requirement_bytes']
assert free>=required, f'workspace free {free} below reviewed planning requirement {required}'
available=mem_available()
assert available>=policy['start_reserve_bytes'], 'startup memory reserve unavailable'
final=json.loads((args.temp_check/'final.json').read_bytes())
assert final['phase']=='complete' and final['child_exit_code']==0 and final['cleanup_verified']
temp=json.loads((args.temp_check/'child.log').read_bytes())
assert temp['all_writable_candidates_on_guarded_volume'] and temp['workspace_device']==root.stat().st_dev
assert final['cwd']==str(root)
value={'source':source,'experiment':name,'registration_sha256':file_hash(gate),
       'effective_attempt_budget':52,'ready':True,'host_mem_available_bytes':available,
       'workspace_free_bytes':free,'planning_free_requirement_bytes':required,
       'temp_check':str(args.temp_check),'temp_check_final_sha256':file_hash(args.temp_check/'final.json'),
       'qualification':'Metadata/resource preflight only; no claim/launch. Freshness and final release evidence require independent operator review.'}
print(json.dumps(value,indent=2))

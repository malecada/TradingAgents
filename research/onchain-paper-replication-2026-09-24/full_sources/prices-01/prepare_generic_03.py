"""Freeze generic owned price jobs; metadata preparation, never an execution."""
from pathlib import Path
import copy,json,sys,subprocess
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tradingagents.research.onchain_replication.job import required_sources,resource_policy,job_schema
from tradingagents.research.onchain_replication.provenance import file_hash,canonical_bytes


def main():
    destination=Path('/tmp/onchain-paper-prices-checkout-20260924-01')
    common=subprocess.check_output(['git','rev-parse','--git-common-dir'],cwd=ROOT,text=True).strip()
    layout={'root':str(destination),'ledger':str((ROOT/'research_runs').resolve()),
            'artifacts':str((ROOT/'research_artifacts').resolve()),'git_common':str((ROOT/common).resolve())}
    with (HERE/'workspace-03.json').open('xb') as out:out.write(canonical_bytes(layout))
    old=json.loads((HERE/'gate-v2.json').read_bytes());gate=copy.deepcopy(old)
    charter=HERE/'CHARTER-generic-03.md'
    with charter.open('x') as out:
        out.write((HERE/'CHARTER.md').read_text())
        out.write('\n## Execution-only refinement before any price request\n\nThe reviewed generic owned supervisor/worker/observer replaces the earlier dedicated price controller. Resource, data, dates, provider, single-request policy and cumulative budget are unchanged. Both old gates and controller sources remain preserved. Every exact transitive package/runtime source is pinned. Live owner PID/start ticks protect active jobs; terminal lifecycle and guard identity, output/cell denominator, cgroup death and retained observer evidence are verified.\n\nExecution uses the exact separately registered sparse worktree and physical shared ledger/artifact paths in workspace-03.json. The shared lock and all cumulative claims remain authoritative. The active resource pilot checkout HEAD and its sources remain unchanged. BTC and ETH run sequentially once each. Shared path mapping is checked before launch/worker admission; changing it requires a new prospective configuration, never an empty replacement ledger.\n')
    for asset in ('BTC','ETH'):
        experiment=gate['experiments']['paper-prices-'+asset.lower()+'-20260924']
        policy={'memory_max_bytes':512*1024**2,'memory_high_bytes':384*1024**2,
            'reserve_bytes':3*1024**3,'start_reserve_bytes':3584*1024**2,
            'disk_floor_bytes':20*1024**3,'disk_paths':[str(destination)],'wall_seconds':300}
        job={'schema_version':1,'kind':'prices','resources':policy,'environment_input':'environment','payload':{'asset':asset}}
        job_schema(job)
        name=asset+'-job-03.json'
        with (HERE/name).open('xb') as out:out.write(canonical_bytes(job))
        experiment['source_files']={p:file_hash(ROOT/p) for p in sorted(required_sources())}
        experiment['charter']={'path':str(charter.relative_to(ROOT)),'sha256':file_hash(charter)}
        for key,path in [('execution_job',HERE/name),('execution_workspace',HERE/'workspace-03.json')]:
            experiment['inputs'][key]={'path':str(path.relative_to(ROOT)),'sha256':file_hash(path),'dataset':asset.lower()}
    with (HERE/'gate-v3.json').open('xb') as out:out.write(canonical_bytes(gate))
    print(json.dumps({'gate_sha256':file_hash(HERE/'gate-v3.json'),'source_files':len(experiment['source_files']),'inputs_per_asset':len(experiment['inputs']),'workspace':layout}))


if __name__=='__main__':main()

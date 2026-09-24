"""One admitted price request per asset; retain the full daily denominator."""
import argparse,json,signal,sys,time
from pathlib import Path
from tradingagents.research import ResearchRun
from tradingagents.research.onchain_replication import resources
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.price_source import capture_admitted_prices
from tradingagents.research.onchain_replication.provenance import file_hash

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
GIB=1024**3


def check_guard(command,asset):
    guard=ROOT/('research_artifacts/onchain-paper-replication-2026-09-24/source-prices-01-'+asset.lower()+'-guard')
    live=json.loads((guard/'live.json').read_bytes())
    if live['command']!=command or live['phase']!='running':raise ValueError('price guard command mismatch')
    if live['owner_identity']['asset']!=asset:raise ValueError('price guard asset mismatch')
    if not json.loads((guard/'release.json').read_bytes())['kernel_controls_verified']:raise ValueError('guard unreleased')
    if live['boot_id']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():raise ValueError('guard boot differs')
    if not 0<=time.monotonic()-live['monotonic_seconds']<=live['lease_seconds']:raise ValueError('expired guard lease')
    if str(resources._own_cgroup())!=live['cgroup']:raise ValueError('guard containment mismatch')
    resources._verify_controls(resources._read_controls(resources._own_cgroup()),512*1024**2,384*1024**2,0)
    resources.verify_cpu_tree(resources._own_cgroup(),live['cpus'])
    if len(live['cpus'])!=2 or live['reserve_bytes']<3*GIB or live['disk_floor_bytes']<20*GIB or live['wall_seconds']!=300:raise ValueError('price resource bounds differ')
    if ROOT.stat().st_dev not in {Path(p).stat().st_dev for p in live['disk_paths']}:raise ValueError('guard volume missing')


def worker(source,asset):
    command=[sys.executable,'-B',str(HERE/'worker.py'),'--source',source,'--asset',asset]
    check_guard(command,asset)
    def interrupted(signum,frame):raise SystemExit('price worker interrupted; never relaunch')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    if inventory(ROOT)!=json.loads((HERE/'environment.json').read_bytes()):raise ValueError('price environment differs')
    experiment='paper-prices-'+asset.lower()+'-20260924'
    with ResearchRun.start(root=ROOT,registration=str((HERE/'gate-v2.json').relative_to(ROOT)),experiment=experiment,source=source) as run:
        cells,summary,directory=capture_admitted_prices(run,asset)
        run.write_json('cell-ledger.json',cells)
        run.write_json('source-summary.json',summary)
        run.write_json('artifact-index.json',{str(p.relative_to(ROOT)):{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in directory.rglob('*') if p.is_file()})
        run.finish(cells)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--asset',required=True,choices=('BTC','ETH'));args=parser.parse_args();worker(args.source,args.asset)

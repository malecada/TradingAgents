"""One metadata-only claim; exclusive guard, durable per-cell evidence, no retry."""
import argparse,json,os,signal,subprocess,sys,time,uuid
from pathlib import Path
from types import SimpleNamespace
from tradingagents.research import ResearchRun
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication import resources
from tradingagents.research.onchain_replication.provenance import digest,file_hash,durable_mkdir
from tradingagents.research.onchain_replication.source_inventory import capture_catalogue,FIELDS,required_dates
from tradingagents.research.onchain_replication.source_footers import capture_footer,select_objects

ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXPERIMENT='paper-full-source-metadata-20260924'
BASE=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24'
GUARD=BASE/'source-metadata-01-guard';ARTIFACTS=BASE/'sources'/EXPERIMENT
GIB=1024**3


def check_guard(command):
    live=json.loads((GUARD/'live.json').read_bytes())
    if live['command']!=command or live['phase']!='running':raise ValueError('metadata guard command mismatch')
    if not json.loads((GUARD/'release.json').read_bytes())['kernel_controls_verified']:raise ValueError('guard unreleased')
    if live['boot_id']!=Path('/proc/sys/kernel/random/boot_id').read_text().strip():raise ValueError('guard boot differs')
    if not 0<=time.monotonic()-live['monotonic_seconds']<=live['lease_seconds']:raise ValueError('expired guard lease')
    if str(resources._own_cgroup())!=live['cgroup']:raise ValueError('guard containment mismatch')
    resources._verify_controls(resources._read_controls(resources._own_cgroup()),GIB,768*1024**2,0)
    resources.verify_cpu_tree(resources._own_cgroup(),live['cpus'])
    if len(live['cpus'])!=2 or live['reserve_bytes']<3*GIB or live['disk_floor_bytes']<20*GIB or live['wall_seconds']!=1800:raise ValueError('metadata resource bounds differ')
    if ROOT.stat().st_dev not in {Path(p).stat().st_dev for p in live['disk_paths']}:raise ValueError('guard volume missing')


def worker(source):
    command=[sys.executable,'-B',str(HERE/'worker.py'),'--source',source]
    check_guard(command)
    def interrupted(signum,frame):raise SystemExit('metadata worker interrupted; never relaunch')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    from tradingagents.research.onchain_replication.environment import inventory
    if inventory(ROOT)!=json.loads((HERE/'environment.json').read_bytes()):raise ValueError('metadata environment differs')
    with ResearchRun.start(root=ROOT,registration=str((HERE/'gate-v3.json').relative_to(ROOT)),experiment=EXPERIMENT,source=source) as run:
        durable_mkdir(ARTIFACTS);cells=[];catalogues={}
        def retain(row):
            _immutable(ARTIFACTS/(row['id']+'.json'),row);cells.append(row)
        for asset in ('BTC','ETH'):
            for year in range(2016,2025):
                name=asset+'-'+str(year);directory=ARTIFACTS/name
                catalogue=capture_catalogue(run,asset,year,output_directory=directory,source_policy_input=name)
                catalogues[name]=catalogue
                catalogue_sha=file_hash(directory/'catalogue.json')
                retain({'id':name+'-catalogue','status':'complete' if catalogue['listing_complete'] else 'unavailable','reason':catalogue['reason'] or 'current object listing only; values not admitted','catalogue_sha256':catalogue_sha})
                selected=select_objects(catalogue)
                for slot in range(3):
                    identity=name+'-footer-'+str(slot)
                    if slot>=len(selected):
                        retain({'id':identity,'status':'unavailable','reason':'no distinct object in frozen sample, or incomplete listing'});continue
                    item=selected[slot]
                    result=capture_footer(run,asset,year,item,directory=directory/'footers'/digest(item['key'].encode()),catalogue_sha256=catalogue_sha)
                    retain({'id':identity,**result})
        run.write_json('cell-ledger.json',cells)
        run.write_json('source-coverage.json',{'required_cells':85488,'calendar_years':list(range(2016,2025)),
            'fields':{a:[*FIELDS[a],'price.Close'] for a in FIELDS},'catalogues':catalogues,
            'default_value_cell_status':'unavailable','default_value_cell_reason':'metadata stage does not acquire or admit transaction values or prices',
            'transaction_data_admitted':False,'price_data_admitted':False})
        index={str(p.relative_to(ROOT)):{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in ARTIFACTS.rglob('*') if p.is_file()}
        run.write_json('artifact-index.json',index)
        run.write_json('storage-summary.json',{'listed_object_bytes':{k:v['listed_object_bytes'] for k,v in catalogues.items()},'listing_complete':{k:v['listing_complete'] for k,v in catalogues.items()},'retained_artifact_bytes':sum(v['bytes'] for v in index.values()),'qualification':'current object sizes; whole training/raw/backup feasibility not established'})
        run.finish(cells)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args();worker(args.source)

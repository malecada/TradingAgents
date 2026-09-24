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
    command=[sys.executable,'-B',str(HERE/'launch.py'),'--worker','--source',source]
    check_guard(command)
    def interrupted(signum,frame):raise RuntimeError('metadata worker interrupted; never relaunch')
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    with ResearchRun.start(root=ROOT,registration=str((HERE/'gate.json').relative_to(ROOT)),experiment=EXPERIMENT,source=source) as run:
        durable_mkdir(ARTIFACTS);cells=[];catalogues={}
        def retain(row):
            _immutable(ARTIFACTS/(row['id']+'.json'),row);cells.append(row)
        for asset in ('BTC','ETH'):
            for year in range(2016,2025):
                name=asset+'-'+str(year);directory=ARTIFACTS/name
                catalogue=capture_catalogue(run,asset,year,output_directory=directory,source_policy_input=name)
                catalogues[name]=catalogue
                retain({'id':name+'-catalogue','status':'complete' if catalogue['listing_complete'] else 'unavailable','reason':catalogue['reason'] or 'current object listing only; values not admitted','catalogue_sha256':file_hash(directory/'catalogue.json')})
                selected=select_objects(catalogue)
                for slot in range(3):
                    identity=name+'-footer-'+str(slot)
                    if slot>=len(selected):
                        retain({'id':identity,'status':'unavailable','reason':'no distinct object in frozen sample, or incomplete listing'});continue
                    item=selected[slot]
                    result=capture_footer(run,asset,year,item,directory=directory/'footers'/digest(item['key'].encode()))
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


def reconcile(source,identity):
    live=json.loads((GUARD/'live.json').read_bytes())
    if live.get('owner_identity')!=identity:raise ValueError('metadata observer ownership differs')
    cgroup=Path(live['cgroup']) if live.get('cgroup') else None
    if cgroup and cgroup.exists() and 'populated 1' in (cgroup/'cgroup.events').read_text():raise ValueError('metadata workload still active; observer refused')
    final=json.loads((GUARD/'final.json').read_bytes()) if (GUARD/'final.json').exists() else {}
    directory=ROOT/'research_runs'/EXPERIMENT
    result={'source':source,'cgroup_empty':True,'guard_phase':final.get('phase'),'status':'not_admitted'}
    if (directory/'claim.json').exists():
        if cgroup is None:raise ValueError('no admitted cgroup death proof')
        claim=json.loads((directory/'claim.json').read_bytes())
        if claim['source']!=source or claim['registration_sha256']!=file_hash(HERE/'gate.json'):raise ValueError('metadata claim observer mismatch')
        if (directory/'complete.json').exists():
            verified=final.get('phase')=='complete' and final.get('cleanup_verified') is True and final.get('child_exit_code')==0 and final.get('limit_reason') is None
            result['status']='complete' if verified else 'resource_verification_failed'
        else:
            ledger=[]
            for cell in claim['experiment']['cells']:
                path=ARTIFACTS/(cell+'.json')
                ledger.append(json.loads(path.read_bytes()) if path.exists() else {'id':cell,'status':'unavailable','reason':'interrupted before durable result; no retry'})
            path=ARTIFACTS/'interrupted-cell-ledger.json'
            if not path.exists():_immutable(path,ledger)
            run=ResearchRun(SimpleNamespace(root=ROOT,experiment_id=EXPERIMENT));run._claim_sha256=file_hash(directory/'claim.json')
            if not (directory/'failed.json').exists():run.fail('metadata observer verified workload death; interrupted source attempt; denominator retained')
            result['status']='failed'
    result['guard_hashes']={p.name:file_hash(p) for p in GUARD.iterdir() if p.is_file() and p.name!='observer.json'}
    _immutable(GUARD/'observer.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--worker',action='store_true');parser.add_argument('--source');args=parser.parse_args()
    if args.worker:
        if not args.source:raise ValueError('source required')
        worker(args.source)
    else:
        source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        identity={'nonce':uuid.uuid4().hex,'monitor_pid':os.getpid(),'monitor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
        result=resources.guarded_run([sys.executable,'-B',str(HERE/'launch.py'),'--worker','--source',source],cwd=ROOT,receipt_dir=GUARD,
            memory_max_bytes=GIB,memory_high_bytes=768*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,
            disk_paths=[ROOT],wall_seconds=1800,owner_identity=identity)
        observed=reconcile(source,identity)
        print(observed['status'],flush=True)
        raise SystemExit(0 if observed['status']=='complete' else 1)

"""One exclusive, registered resource attempt. Never resumes or refits a terminal claim."""
from pathlib import Path
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from tradingagents.research import ResearchRun
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.provenance import file_hash,durable_mkdir,sync_directory
from tradingagents.research.onchain_replication.resources import assert_guarded_worker,_atomic

ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
EXPERIMENT='eth-paper-resource-pilot-20260924-02'
ARTIFACTS=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02'
PHASES=('decode_graph','neighborhoods','matching','neural_checkpoint','dictionary','mcm')


def phase_inventory(index):
    return [(week,phase) for week in index['weeks'] for phase in PHASES if phase!='dictionary' or week=='2022-01-03']


def dependencies(week,phase):
    if phase=='decode_graph':return []
    if phase in ('matching','dictionary'):return [(week,'neighborhoods')]
    if phase=='mcm':return [(week,'decode_graph'),('2022-01-03','dictionary')]
    return [(week,'decode_graph')]


def forecast(cells,index):
    complete=[c for c in cells if c['status']=='complete' and c['phase']=='decode_graph']
    # Calendar bound for16 consecutive decisions, each28-day history:43 days <=7 weeks.
    neural=[c for c in cells if c['status']=='complete' and c['phase']=='neural_checkpoint']
    return {'margin':1.5,'unique_week_bound':7,'qualification':'Extrapolation only; no demonstrated multiweek training batch. Scalar dictionary timeout does not establish intrinsic method infeasibility.',
            'completed_whole_weeks':len(complete),'required_pilot_weeks':len(index['weeks']),
            'declared_source_rows':index['total_rows'],'graph_bytes_max':max((c['details']['graph_bytes'] for c in complete),default=None),
            'graph_seconds_max':max((c['elapsed_seconds'] for c in complete),default=None),
            'conservative_multigraph_rss_forecast_bytes':None if not neural else int(max(c['peak_worker_rss_bytes'] for c in neural)*7*1.5),
            'financial_run_admitted':False,'full_history_dictionary':'unmeasured: global training graph membership and sampling weights require separate forecast',
            'paper_fits_pending':1400,'diagnostic_fits_pending':20,
            'missing_components':[c['id'] for c in cells if c['status']!='complete']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--guard',required=True);args=parser.parse_args()
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'--source',args.source,'--guard',args.guard]
    limits=json.loads((HERE/'resource-contract-v4.json').read_bytes())
    assert_guarded_worker(args.guard,command,required_paths=[ROOT,Path('/home/malecada/Data')],wall_seconds=28800,
        memory_max_bytes=limits['memory_max_bytes'],memory_high_bytes=limits['memory_high_bytes'])
    os.environ['PAPER_SOURCE_COMMIT']=args.source
    begin=time.monotonic();active=None;stopping=[False]
    def stop(signum,frame):
        stopping[0]=True
        if active is not None and active.poll() is None:active.terminate()
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    registration=str((HERE/'gate-v3.json').relative_to(ROOT))
    from tradingagents.research.onchain_replication.environment import inventory
    if inventory(ROOT,include_torch=True)!=json.loads((HERE/'environment.json').read_bytes()):raise ValueError('pinned pilot runtime differs')
    with ResearchRun.start(root=ROOT,registration=registration,experiment=EXPERIMENT,source=args.source) as run:
        index=json.loads(run.read_input('source_index'));durable_mkdir(ARTIFACTS.parent);ARTIFACTS.mkdir(exist_ok=False);sync_directory(ARTIFACTS.parent)
        cells=[];results={};artifacts={}
        for week,phase in phase_inventory(index):
            run._check_source();cell_id=phase+'-'+week;directory=ARTIFACTS/week/phase
            reason=None
            if stopping[0] or time.monotonic()-begin>=28600:reason='total registered resource budget or shutdown reached before phase'
            for dep in dependencies(week,phase):
                if results.get(dep,{}).get('status')!='complete':reason='unavailable prerequisite: '+ '/'.join(dep)
            if reason is not None:
                result={'phase':phase,'week':week,'status':'unavailable','reason':reason}
            else:
                durable_mkdir(directory.parent);directory.mkdir(exist_ok=False);sync_directory(directory.parent);bindings={str(ROOT/info['path']):info['sha256'] for info in run.admission.inputs.values()}
                for dep in dependencies(week,phase):bindings.update(artifacts[dep])
                # Sample bytes, graph manifest and array hashes are chained to completed phases.
                intent=directory/'intent.json';worker=[sys.executable,'-B',str(HERE/'phase.py'),'--intent',str(intent)]
                _immutable(intent,{'owner_pid':os.getpid(),'phase':phase,'week':week,'artifacts':str(ARTIFACTS),'guard_receipt':args.guard,'guard_command':command,'worker_command':worker,'bindings':bindings,'source_commit':args.source})
                start=time.monotonic();deadline=min(3600,28600-(start-begin));peak=0;interrupted=False
                with (directory/'worker.log').open('xb') as log:
                    active=subprocess.Popen(worker,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
                    while active.poll() is None:
                        if stopping[0] or time.monotonic()-start>=deadline:
                            interrupted=True;active.terminate()
                            try:active.wait(timeout=10)
                            except subprocess.TimeoutExpired:active.kill();active.wait(timeout=10)
                            break
                        live=json.loads((Path(args.guard)/'live.json').read_bytes());peak=max(peak,live.get('memory_current_bytes',0))
                        _atomic(ARTIFACTS/'progress.json',{'run':EXPERIMENT,'pid':os.getpid(),'worker_pid':active.pid,'phase':phase,'week':week,'elapsed_seconds':time.monotonic()-start,'completed_cells':len(cells)})
                        time.sleep(1)
                    log.flush();os.fsync(log.fileno())
                returncode=active.returncode;active=None
                if (directory/'result.json').exists():result=json.loads((directory/'result.json').read_bytes())
                else:
                    result={'phase':phase,'week':week,'status':'unavailable' if interrupted else 'failed','reason':'worker ended without phase receipt; exit '+str(returncode),'elapsed_seconds':time.monotonic()-start}
                    _immutable(directory/'external-stop.json',result)
                result['peak_sampled_cgroup_bytes']=peak;result['worker_exit_code']=returncode
                if result['status']=='complete' and returncode!=0:result.update(status='failed',reason='complete result with nonzero exit')
                artifacts[(week,phase)]={str(p):file_hash(p) for p in directory.rglob('*') if p.is_file() and not p.name.endswith(('.sqlite','.sqlite-journal'))}
            result['id']=cell_id;cells.append(result);results[(week,phase)]=result
            _immutable(ARTIFACTS/('cell-'+str(len(cells)).zfill(3)+'.json'),result)
        # Each source-day denominator is retained; complete only after full week decode succeeds.
        for week,info in index['weeks'].items():
            parent=results[(week,'decode_graph')]
            for member in info['members']:
                cells.append({'id':'source-'+member['start_utc'][:10],'status':'complete' if parent['status']=='complete' else 'unavailable','reason':'whole-week count/hash validation '+parent['status'],'rows_declared':member['expected_rows'],'source_map_sha256':member['sha256'],'week':week})
        run.write_json('cell-ledger.json',cells)
        run.write_json('artifact-index.json',{'artifacts':{path:sha for values in artifacts.values() for path,sha in values.items()},'artifact_root':str(ARTIFACTS),'guard_receipt':args.guard})
        run.write_json('capacity-forecast.json',forecast([c for c in cells if 'phase' in c],index))
        if any(c['status']=='failed' for c in cells):run.fail('unexpected phase failure; all independent phases attempted within total budget');return 1
        run.finish(cells)
    return 0

if __name__=='__main__':raise SystemExit(main())

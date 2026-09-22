"""One offline continuation of the frozen seven-day numerical pilot."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

from tradingagents.research import ResearchRun
from admission import admit_pilot

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
EXPERIMENT='eth-seven-day-offline-pilot-20260922'
REGISTRATION='research/onchain-graph-2026-09-16/pilot2/gates.json'
sys.path.insert(0,str(HERE.parent/'pilot'))
spec=importlib.util.spec_from_file_location('retained_pilot_runner',HERE.parent/'pilot/run.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
from storage import atomic_json


def execute(plan,run):
    artifacts=HERE/'artifacts';artifacts.mkdir(exist_ok=False)
    results=artifacts/'results';results.mkdir()
    cells=[];stopped=None
    def child(mode,date,**extra):
        nonlocal stopped
        result_path=results/f'{mode}-{date}.json'
        if shutil.disk_usage(ROOT).free < plan['limits']['min_free_bytes']:
            stopped='free disk below frozen20GiB floor'
        allocated=sum(p.stat().st_blocks*512 for p in artifacts.rglob('*') if p.is_file())
        if allocated > plan['limits']['max_derived_bytes']:
            stopped='derived artifact allocation exceeds8GiB phase boundary'
        if stopped:
            value=dict(mode=mode,date=date,status='unavailable',reason=stopped,events=[],prefix=[],transaction_hashes=[],artifacts=[],requests=0,raw_bytes=0,denied=False,plan_sha256=prior.sha_file(HERE/'plan.json'))
            atomic_json(result_path,value)
        else:
            command=[sys.executable,'-B',str(HERE/'day.py'),'--root',str(ROOT),'--plan',str((HERE/'plan.json').relative_to(ROOT)),
                     '--mode',mode,'--date',date,'--result',str(result_path)]
            for key,value in extra.items():command.extend(['--'+key.replace('_','-'),str(value)])
            print(json.dumps(dict(phase=mode,date=date,status='starting')),flush=True)
            subprocess.run(command,check=True)
            value=json.loads(result_path.read_bytes())
        print(json.dumps(dict(phase=mode,date=date,status=value['status'],reason=value.get('reason'))),flush=True)
        return value,result_path
    def publish(name,value,cell):
        run.write_json(name,value)
        item=dict(id=cell,status=value['status'])
        if item['status']!='complete':item['reason']=value.get('reason') or 'prerequisite unavailable'
        cells.append(item)
    context,context_path=child('context','2024-01-01');publish('context.json',context,'context')
    closing,_=child('boundary','2024-01-09');publish('boundary.json',closing,'boundary')
    sources={};paths={}
    for date in plan['dates']:
        sources[date],paths[date]=child('source',date);publish(f'source-{date}.json',sources[date],'source-'+date)
    uniqueness=prior.unique_transactions(ROOT,[context,*sources.values()])
    if not uniqueness['all_eight_sources_checked']:
        uniqueness.update(status='unavailable',reason='not all eight required source days passed')
    publish('cross-day-integrity.json',uniqueness,'uniqueness')
    features=[]
    for i,date in enumerate(plan['dates']):
        previous=context if i==0 else sources[plan['dates'][i-1]]
        following=closing if i==6 else sources[plan['dates'][i+1]]
        try:
            if uniqueness['status']!='complete':raise ValueError(uniqueness['reason'])
            links=prior.linkage(previous,sources[date],following)
        except ValueError as exc:value=dict(date=date,status='unavailable',reason=str(exc))
        else:
            prev_path=context_path if i==0 else paths[plan['dates'][i-1]]
            value,_=child('count',date,current_result=paths[date].relative_to(ROOT),previous_result=prev_path.relative_to(ROOT),
                          current_sha256=prior.sha_file(paths[date]),previous_sha256=prior.sha_file(prev_path))
            value['boundary_admission']=links
        publish(f'features-{date}.json',value,'motifs-'+date)
        features.append({k:v for k,v in value.items() if k not in {'counts','artifacts','checks'}})
    manifest=prior.validate_artifacts(ROOT,artifacts)
    run.write_json('manifest.json',dict(files=manifest,bytes=sum(r['bytes'] for r in manifest)))
    run.write_json('features.json',dict(days=features,historical_publication_verified=False,prices_or_targets_opened=False))
    run.write_json('summary.json',dict(cells=cells,requests=0,raw_bytes=0,denied=False,network_allowed=False,
        complete_motif_days=sum(c['status']=='complete' for c in cells if c['id'].startswith('motifs-')),
        artifact_bytes=sum(r['bytes'] for r in manifest),artifact_files=len(manifest),stopped=stopped,
        qualification='Retrospective seven-day engineering only. Independent numerical closure separately required.'))
    return cells


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    admit_pilot(ROOT,args.source)
    # Defense in depth: the adapter has the same prohibition in every child.
    def offline(event,args):
        if event in {'socket.connect','socket.getaddrinfo','socket.sendto'}:raise RuntimeError('network prohibited by offline pilot')
    sys.addaudithook(offline)
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        run.finish(execute(json.loads(run.read_input('plan')),run))

if __name__=='__main__':main()

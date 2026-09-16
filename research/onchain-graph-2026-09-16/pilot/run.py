"""Frozen seven-day source, boundary, motif and lossless-storage engineering pilot."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from tradingagents.research import ResearchRun
from storage import atomic_json, read_blob

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
EXPERIMENT='eth-seven-day-pilot-20260916'
REGISTRATION='research/onchain-graph-2026-09-16/pilot/gates.json'


def sha_file(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def linkage(previous,current,following):
    for row in (previous,current,following):
        if row['status']!='complete':raise ValueError('adjacent source or boundary unavailable')
    for left,right in ((previous,current),(current,following)):
        a,b=left['integrity']['last_block'],right['integrity']['first_block']
        if b[0]!=a[0]+1 or b[2].lower()!=a[1].lower() or b[3]<=a[3]:
            raise ValueError('cross-day block height, parent hash or clock discontinuity')
    return {'prior_and_next_block_links':'passed','independent_canonical_chain_verified':False}


def validate_artifacts(root,artifacts):
    """Require every stored body to have a checked metadata binding and every intent a receipt."""
    bound=set();manifest=[]
    def metadata(value,parent):
        if isinstance(value,dict):
            if {'path','raw_bytes','stored_bytes','raw_sha256','stored_sha256','codec','level'}<=value.keys():
                path=(parent/value['path'] if '/' not in value['path'] else root/value['path']).resolve()
                path.relative_to(artifacts.resolve())
                read_blob(path,value);bound.add(path)
            for item in value.values():metadata(item,parent)
        elif isinstance(value,list):
            for item in value:metadata(item,parent)
    paths=sorted(p for p in artifacts.rglob('*') if p.is_file())
    for path in paths:
        if path.suffix=='.json':
            metadata(json.loads(path.read_bytes()),path.parent)
            if path.name.endswith('-intent.json') and not path.with_name(path.name.replace('-intent.json','.json')).is_file():
                raise ValueError('unresolved acquisition intent: '+str(path))
        manifest.append({'path':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':sha_file(path)})
    blobs={p.resolve() for p in paths if p.suffix=='.zst'}
    if blobs!=bound:raise ValueError('unbound/orphan compressed artifact')
    return manifest


def unique_transactions(root,rows):
    """Cross-day exact 32-byte transaction identity check, including retained context."""
    seen=set();duplicates=set();total=0
    for row in rows:
        if row['status']!='complete':continue
        own=0
        for meta in row['transaction_hashes']:
            raw=read_blob(root/meta['path'],meta)
            if len(raw)!=32*meta['hashes']:raise ValueError('transaction identity shard length differs')
            for i in range(0,len(raw),32):
                identity=raw[i:i+32]
                if identity in seen:duplicates.add(row['date'])
                seen.add(identity);own+=1
        if own!=row['integrity']['rows']:raise ValueError('transaction identity denominator differs')
        total+=own
    return {'status':'complete' if not duplicates else 'unavailable','rows':total,'unique_hashes':len(seen),
            'covered_days':[r['date'] for r in rows if r['status']=='complete'],'unavailable_days':[r['date'] for r in rows if r['status']!='complete'],
            'all_eight_sources_checked':len(rows)==8 and all(r['status']=='complete' for r in rows),'duplicate_days':sorted(duplicates),'reason':None if not duplicates else 'duplicate transaction hash across days'}


def execute(plan,run):
    artifacts=HERE/'artifacts';artifacts.mkdir(exist_ok=False)
    results=artifacts/'results';results.mkdir()
    total_requests=0;total_bytes=0;denied=False;cells=[]
    def child(mode,day,**extra):
        nonlocal total_requests,total_bytes,denied
        result_path=results/f'{mode}-{day}.json'
        if mode in {'source','boundary'} and (denied or total_requests>=plan['limits']['max_requests'] or total_bytes>=plan['limits']['max_total_bytes']-1):
            value={'date':day,'status':'unavailable','reason':'global source denial or acquisition budget exhausted',
                   'requests':0,'raw_bytes':0,'denied':denied}
            atomic_json(result_path,value)
        else:
            command=[sys.executable,'-B',str(HERE/'day.py'),'--root',str(ROOT),'--plan',str(HERE/'plan.json'),
                     '--mode',mode,'--date',day,'--result',str(result_path),
                     '--max-requests',str(plan['limits']['max_requests']-total_requests),
                     '--max-bytes',str(plan['limits']['max_total_bytes']-total_bytes)]
            for key,value in extra.items():command.extend(['--'+key.replace('_','-'),str(value)])
            print(json.dumps({'phase':mode,'date':day,'status':'starting'}),flush=True)
            subprocess.run(command,check=True)  # Inherit process group, affinity and aggregate RSS guard.
            value=json.loads(result_path.read_bytes())
        total_requests+=value.get('requests',0);total_bytes+=value.get('raw_bytes',0);denied|=value.get('denied',False)
        if total_requests>plan['limits']['max_requests'] or total_bytes>plan['limits']['max_total_bytes']:
            raise ValueError('aggregate acquisition budget exceeded')
        return value,result_path
    def publish(name,value,cell):
        run.write_json(name,value)
        item={'id':cell,'status':value['status']}
        if item['status']!='complete':item['reason']=value.get('reason','prerequisite unavailable')
        cells.append(item)
    context,context_path=child('context','2024-01-01');publish('context.json',context,'context')
    closing,closing_path=child('boundary','2024-01-09');publish('boundary.json',closing,'boundary')
    sources={};paths={}
    for day in plan['dates']:
        sources[day],paths[day]=child('source',day);publish(f'source-{day}.json',sources[day],'source-'+day)
    uniqueness=unique_transactions(ROOT,[context,*sources.values()])
    run.write_json('cross-day-integrity.json',uniqueness)
    features=[]
    for i,day in enumerate(plan['dates']):
        previous=context if i==0 else sources[plan['dates'][i-1]]
        following=closing if i==len(plan['dates'])-1 else sources[plan['dates'][i+1]]
        try:
            if uniqueness['status']!='complete':raise ValueError(uniqueness['reason'])
            links=linkage(previous,sources[day],following)
        except ValueError as exc:
            value={'date':day,'status':'unavailable','reason':str(exc)}
        else:
            prior_path=context_path if i==0 else paths[plan['dates'][i-1]]
            value,_=child('count',day,current_result=paths[day],previous_result=prior_path,
                          current_sha256=sha_file(paths[day]),previous_sha256=sha_file(prior_path))
            value['boundary_admission']=links
        publish(f'features-{day}.json',value,'motifs-'+day)
        features.append({k:v for k,v in value.items() if k not in {'counts','artifacts','checks'}})
    benchmark=context.get('benchmark',{'status':'unavailable','reason':'context/storage unavailable'})
    if 'status' not in benchmark:benchmark['status']='complete'
    publish('storage-benchmark.json',benchmark,'storage')
    manifest=validate_artifacts(ROOT,artifacts)
    run.write_json('manifest.json',{'files':manifest,'bytes':sum(r['bytes'] for r in manifest),
        'contract':'Immutable intents, lossless raw bodies, receipts, derived shards and phase results. Manifest complements lifecycle JSON validation.'})
    run.write_json('features.json',{'days':features,'historical_publication_verified':False,'prices_or_targets_opened':False})
    run.write_json('summary.json',{'requests':total_requests,'raw_bytes':total_bytes,'denied':denied,'cells':cells,
        'complete_motif_days':sum(c['status']=='complete' for c in cells if c['id'].startswith('motifs-')),
        'artifact_bytes':sum(r['bytes'] for r in manifest),'artifact_files':len(manifest),
        'qualification':'Retrospective engineering only; no forecasting, financial inference or canonical-chain/publication-time admission.'})
    return cells


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    with ResearchRun.start(root=ROOT,registration=REGISTRATION,experiment=EXPERIMENT,source=args.source) as run:
        plan=json.loads(run.read_input('plan'))
        run.finish(execute(plan,run))


if __name__=='__main__':main()

"""Chronological compact panel with audited temporary-array release."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tradingagents.research import ResearchRun
from admission import admit_panel,EXPERIMENT,BASE
import hash_audit
from source import storage,old
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def allocated(path):return sum(p.stat().st_blocks*512 for p in path.rglob('*') if p.is_file())

def preflight(root,plan,artifacts):
    for volume in [root,Path(plan['hash_root']).parent]:
        if shutil.disk_usage(volume).free<plan['limits']['min_free_bytes']:raise OSError('free-space floor reached: '+str(volume))
    if artifacts.exists():
        scratch=artifacts/'scratch';temporary=allocated(scratch) if scratch.exists() else 0
        if temporary>plan['limits']['max_scratch_bytes']:raise OSError('daily scratch ceiling exceeded')
        lifecycle=root/'research_runs'/EXPERIMENT
        retained=allocated(artifacts)-temporary+(allocated(lifecycle) if lifecycle.exists() else 0)
        retained+=sum(p.stat().st_blocks*512 for p in (root/BASE).glob('*') if p.is_file() and p.name in {'resource.json','compute.log','hash-owner.json'})
        if retained>plan['limits']['max_derived_bytes']:raise OSError('retained derived ceiling exceeded')
    hashes=Path(plan['hash_root'])
    if hashes.exists() and allocated(hashes)>plan['limits']['max_hash_bytes']:raise OSError('hash scratch ceiling exceeded')

def cleanup_day(root,scratch,manifest):
    scratch=Path(scratch);expected=root/BASE/'artifacts/scratch'/scratch.name
    if scratch.resolve()!=expected.resolve() or scratch.is_symlink():raise ValueError('cleanup outside declared day scratch')
    actual=[p for p in scratch.rglob('*') if p.is_file()]
    if {str(p.relative_to(root)) for p in actual}!={m['path'] for m in manifest}:raise ValueError('scratch membership differs before release')
    for item in manifest:
        p=root/item['path']
        if p.is_symlink() or p.stat().st_size!=item['bytes'] or sha(p)!=item['sha256']:raise ValueError('scratch changed before release')
    shutil.rmtree(scratch)

def panel_row(day,value,globally_admitted):
    source=value.get('source',{});count=value.get('count',{});checked=value.get('independent',{})
    source_ok=globally_admitted and source.get('status')=='complete' and checked.get('passed') is True
    graph_ok=source_ok and count.get('status')=='complete' and checked.get('count_verified') is True
    row=dict(day=day,source_admitted=source_ok,graph_admitted=graph_ok,available_at=None,historical_availability_verified=False,
             source_status=source.get('status','unavailable'),graph_status=count.get('status','unavailable'),reason=count.get('reason') or source.get('reason'))
    if source.get('status')=='complete':
        row.update({k:source['activity'][k] for k in ['events','nodes','directed_pairs']});row['transactions']=source['integrity']['rows']
    if count.get('status')=='complete':
        f=count['features'];v=f['local40_sums'];row.update(stars=sum(v[:24]),dyads=sum(v[24:32])//2,triangles=sum(v[32:])//3,overlap_nodes=f['overlap_node_count'],nonzero_nodes=f['nonzero_nodes'],local40=f)
    return row

def execute(root,plan,run):
    here=root/BASE;artifacts=here/'artifacts';artifacts.mkdir(exist_ok=False)
    hashroot=Path(plan['hash_root']);hashroot.mkdir(exist_ok=False)
    storage.atomic_json(here/'hash-owner.json',dict(experiment=EXPERIMENT,hash_root=str(hashroot),purpose='new recomputable exact identity audit scratch; old evidence excluded'))
    previous=None;cells=[];results=[];stopped=None;hashdays={}
    for index,date in enumerate(plan['dates']):
        name='day-'+date+'.json';phase_rel=Path(BASE)/'artifacts/scratch'/date/'phase.json';audit_rel=Path(BASE)/'artifacts/checks'/(date+'.json')
        if stopped:
            value=dict(date=date,source=dict(status='unavailable',reason=stopped),count=dict(status='unavailable',reason=stopped),independent=None)
        else:
            try:
                preflight(root,plan,artifacts)
                command=[sys.executable,'-B',str(here/'day.py'),'--root',str(root),'--plan',BASE+'plan.json','--date',date,'--phase',str(phase_rel)]
                if previous:command+=['--previous',str(previous.relative_to(root)),'--previous-sha256',sha(previous)]
                print(json.dumps(dict(date=date,phase='extract',status='starting')),flush=True)
                subprocess.run(command,check=True,cwd=root)
                phase=json.loads((root/phase_rel).read_bytes())
                if phase['source']['status']!='complete':raise ValueError('source unavailable: '+str(phase['source'].get('reason')))
                # Independent full raw reconstruction precedes hash admission or scratch release.
                (root/audit_rel).parent.mkdir(parents=True,exist_ok=True)
                preflight(root,plan,artifacts)
                subprocess.run([sys.executable,'-B',str(here/'check_day.py'),'--root',str(root),'--plan',BASE+'plan.json','--phase',str(phase_rel),'--report',str(root/audit_rel)],check=True,cwd=root)
                report=json.loads((root/audit_rel).read_bytes())
                if report['passed'] is not True or report['phase_sha256']!=sha(root/phase_rel) or report['source_rows']!=plan['expected_rows'][date] or (phase['count']['status']=='complete' and not report['count_verified']):raise ValueError('daily independent identity differs')
                def hashes():
                    for meta in phase['source']['transaction_hashes']:yield storage.read_blob(root/meta['path'],meta)
                appended=hash_audit.append_day(hashroot,hashes(),index,max_total_bytes=plan['limits']['max_hash_bytes'])
                if appended['stream_sha256']!=report['source_hash_digest'] or appended['rows']!=report['source_rows']:raise ValueError('independent hashes differ from appended stream')
                for suffix in ['.json','.intent.json']:
                    origin=hashroot/f'day-{index:04d}{suffix}';target=artifacts/'hash-receipts'/origin.name;target.parent.mkdir(exist_ok=True)
                    with target.open('xb') as stream:stream.write(origin.read_bytes())
                hashdays[index]=report['source_rows']
                scratch=root/phase_rel.parent;manifest=old.artifact_manifest(root,scratch)
                value=dict(phase,independent=report,audit=dict(path=str(audit_rel),sha256=sha(root/audit_rel)),hash_append=appended,
                           scratch_manifest=manifest,scratch_retention='recomputable arrays released only after published daily output, independent check and exact-hash append receipt')
                run.write_json(name,value)
                previous=run.directory/'outputs'/name
                # Immutable scientific summaries and digests are now durable.
                if phase['count']['status']!='complete' and date not in plan['expected_graph_unavailable']:
                    stopped='unexpected graph unavailability on '+date+': '+str(phase['count'].get('reason'))
                else:
                    cleanup_day(root,scratch,manifest)
                storage.atomic_json(artifacts/'cleanup'/(date+'.json'),dict(date=date,released=not scratch.exists(),daily_output_sha256=sha(previous),files=len(manifest),bytes=sum(m['bytes'] for m in manifest),reason=stopped or 'independent per-day check and hash append durable; reproducible from immutable retained raw'))
                preflight(root,plan,artifacts)
            except Exception as exc:
                stopped=f'{type(exc).__name__}: {exc}'
                # Preserve any already-published successful day; never replace it.
                if (run.directory/'outputs'/name).exists():
                    value=json.loads((run.directory/'outputs'/name).read_bytes())
                else:
                    value=dict(date=date,source=dict(status='unavailable',reason=stopped),count=dict(status='unavailable',reason=stopped),independent=None,
                               preserved_phase=str(phase_rel) if (root/phase_rel).exists() else None,preserved_audit=str(audit_rel) if (root/audit_rel).exists() else None)
        if not (run.directory/'outputs'/name).exists():run.write_json(name,value)
        results.append(value)
        for kind,key in [('source','source'),('graph','count')]:
            status=value[key]['status'];cell=dict(id=kind+'-'+date,status=status)
            if status!='complete':cell['reason']=value[key].get('reason') or 'independent check unavailable'
            cells.append(cell)
        print(json.dumps(dict(date=date,source=value['source']['status'],graph=value['count']['status'],completed_days=len(hashdays),stopped=stopped)),flush=True)
    if stopped or len(hashdays)!=len(plan['dates']):
        audit=dict(status='unavailable',admitted=False,reason=stopped or 'incomplete day population',checked_days=len(hashdays))
    else:
        preflight(root,plan,artifacts);audit=hash_audit.audit(hashroot,{i:plan['expected_rows'][d] for i,d in enumerate(plan['dates'])})
        if audit['rows']!=plan['expected_total_rows'] or audit['input_bytes']!=plan['expected_hash_bytes']:raise ValueError('global expected population differs')
    run.write_json('hash-audit.json',audit)
    admitted=audit.get('admitted') is True
    cells.append(dict(id='global-uniqueness',status='complete' if admitted else 'unavailable',**({} if admitted else dict(reason=audit.get('reason','duplicate transactions detected')))))
    panel=[panel_row(date,value,admitted) for date,value in zip(plan['dates'],results,strict=True)]
    run.write_json('panel.json',dict(days=panel,global_uniqueness_admitted=admitted,historical_availability_verified=False,prices_or_models_opened=False))
    expected_edges=set(plan['expected_graph_unavailable']);unavailable=[r['day'] for r in panel if not r['graph_admitted']]
    run.write_json('summary.json',dict(cells=cells,dates=len(panel),source_days=sum(r['source_admitted'] for r in panel),graph_days=sum(r['graph_admitted'] for r in panel),unavailable_graph_days=unavailable,
        expected_boundary_only=set(unavailable)==expected_edges and admitted,requests=0,stopped=stopped,raw_capture_modified=False,hash_scratch_retained=str(hashroot),
        qualification='Retrospective numerical panel only. Global hash scratch retained for independent closure; no prices, labels, model or historical publication admission.'))
    return cells

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    admit_panel(ROOT,args.source)
    def offline(event,args):
        if event.startswith(('socket.','http.client.','urllib.')):raise RuntimeError('offline panel network prohibited')
    sys.addaudithook(offline)
    with ResearchRun.start(root=ROOT,registration=BASE+'gates.json',experiment=EXPERIMENT,source=args.source) as run:
        run.finish(execute(ROOT,json.loads(run.read_input('plan')),run))
if __name__=='__main__':main()

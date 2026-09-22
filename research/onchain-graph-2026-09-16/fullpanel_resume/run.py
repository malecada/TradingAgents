"""Immutable seed reuse followed by the unchanged chronological daily pipeline.

Execution admission and the kernel memory guard belong to the caller. This
runner performs no network requests, seed source reconstruction, or old scratch
mutation. All global identity occurrences remain in the union denominator.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tradingagents.research import ResearchRun

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE='research/onchain-graph-2026-09-16/fullpanel/'
RESUME_BASE='research/onchain-graph-2026-09-16/fullpanel_resume/'
EXPERIMENT='eth-full-history-feature-panel-resume-20260922'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


source=load('resume_runner_original_source',HERE.parent/'fullpanel/source.py')
storage,old=source.storage,source.old
hash_union=load('resume_runner_hash_union',HERE/'hash_union.py')
hash_audit=hash_union.frozen


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def inside(root,relative):
    relative=Path(relative)
    if relative.is_absolute() or '..' in relative.parts:raise ValueError('path outside declared namespace')
    path=root/relative
    for item in [path,*path.parents]:
        if item.is_symlink():raise ValueError('symlink in declared namespace')
        if item==root:break
    return path


def allocated(path):
    return sum(p.stat().st_blocks*512 for p in path.rglob('*') if p.is_file()) if path.exists() else 0


def read_numerical_plan(root,resume):
    ref=resume['numerical_plan'];path=inside(root,ref['path'])
    if ref['path']!=BASE+'plan.json' or sha(path)!=ref['sha256']:raise ValueError('frozen numerical plan differs')
    plan=json.loads(path.read_bytes());count=resume['seed_count']
    if type(count) is not int or not 0<count<len(plan['dates']):raise ValueError('invalid seed count')
    if resume['dates']!=plan['dates'] or resume['seed_dates']!=plan['dates'][:count] or resume['remaining_dates']!=plan['dates'][count:]:raise ValueError('continuation calendar differs')
    if resume['limits']!=plan['limits']:raise ValueError('continuation limits differ')
    if [item['day_indices'] for item in resume['hash_roots']]!=[list(range(count)),list(range(count,len(plan['dates'])))]:raise ValueError('hash namespace date assignment differs')
    return plan


def preflight(root,resume,artifacts):
    limits=resume['limits']
    roots=[Path(item['path']) for item in resume['hash_roots']]
    for volume in [root,*[p.parent for p in roots]]:
        if shutil.disk_usage(volume).free<limits['min_free_bytes']:raise OSError('free-space floor reached: '+str(volume))
    temporary=allocated(artifacts/'scratch')
    if temporary>limits['max_scratch_bytes']:raise OSError('daily scratch ceiling exceeded')
    # Includes seed archive, resource logs/receipts, lifecycle and new artifacts.
    retained=allocated(artifacts)-temporary+allocated(root/'research_runs'/EXPERIMENT)+allocated(root/RESUME_BASE)
    if retained>limits['max_derived_bytes']:raise OSError('retained derived ceiling exceeded')
    if sum(allocated(p) for p in roots)>limits['max_hash_bytes']:raise OSError('combined hash scratch ceiling exceeded')


def restore_seed(root,resume,plan,run):
    archive=inside(root,resume['archive_root'])
    output_prefix=f"research_runs/{resume['prior_run_id']}/outputs/"
    expected_outputs={output_prefix+'day-'+d+'.json' for d in resume['seed_dates']}
    actual_outputs={p for p in resume['seed_files'] if p.startswith(output_prefix)}
    if actual_outputs!=expected_outputs:raise ValueError('seed output population differs')
    values={}
    for relative,meta in sorted(resume['seed_files'].items()):
        origin=inside(archive,relative)
        if not origin.is_file() or origin.stat().st_size!=meta['bytes'] or sha(origin)!=meta['sha256']:raise ValueError('seed bytes differ: '+relative)
        if relative in expected_outputs:
            value=json.loads(origin.read_bytes());date=Path(relative).name[4:-5]
            report=value.get('independent') or {}
            if value.get('date')!=date or value.get('source',{}).get('status')!='complete' or report.get('passed') is not True or report.get('source_rows')!=plan['expected_rows'][date]:raise ValueError('seed independent population differs')
            if value['hash_append']['rows']!=report['source_rows'] or value['hash_append']['stream_sha256']!=report['source_hash_digest']:raise ValueError('seed stream attribution differs')
            run.write_json(Path(relative).name,value)
            if sha(run.directory/'outputs'/Path(relative).name)!=meta['sha256']:raise ValueError('republished seed is not byte-identical')
            values[date]=value
        else:
            prefix=BASE+'artifacts/'
            if not relative.startswith(prefix):raise ValueError('unassigned seed artifact')
            parts=Path(relative[len(prefix):]).parts
            permitted=(len(parts)==3 and parts[0]=='prefixes' and parts[1] in resume['seed_dates'])
            permitted|=(len(parts)==2 and parts[0] in {'checks','cleanup'} and parts[1] in {d+'.json' for d in resume['seed_dates']})
            permitted|=(len(parts)==2 and parts[0]=='hash-receipts' and parts[1] in {f'day-{i:04d}'+suffix for i in range(resume['seed_count']) for suffix in ['.json','.intent.json']})
            if not permitted:raise ValueError('unassigned seed artifact')
            target=inside(root,relative);target.parent.mkdir(parents=True,exist_ok=True)
            with origin.open('rb') as source_stream,target.open('xb') as destination:
                shutil.copyfileobj(source_stream,destination)
            if target.stat().st_size!=meta['bytes'] or sha(target)!=meta['sha256']:raise ValueError('restored seed bytes differ')
    preflight(root,resume,root/BASE/'artifacts')
    return values


def bounded_hashes(chunks,combined):
    """Check the complete next chunk against old+new bucket limits before yield."""
    sizes=list(combined)
    for raw in chunks:
        if not isinstance(raw,bytes) or len(raw)%32 or len(raw)>hash_audit.MAX_CHUNK_BYTES:raise ValueError('hash chunk bound differs')
        leading=hash_audit.np.frombuffer(raw,dtype=hash_audit.np.uint8)[::32]
        counts=hash_audit.np.bincount(leading,minlength=256)
        updated=[size+int(count)*32 for size,count in zip(sizes,counts)]
        if any(size>hash_union.MAX_BUCKET_BYTES for size in updated):raise ValueError('combined bucket exceeds reviewed memory ceiling')
        del leading,counts
        sizes=updated
        yield raw


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

def execute(root,resume,run):
    root=Path(root)
    plan=read_numerical_plan(root,resume)
    here=root/BASE;artifacts=here/'artifacts'
    roots=[Path(item['path']) for item in resume['hash_roots']]
    if len(roots)!=2 or roots[0].resolve()==roots[1].resolve():raise ValueError('two distinct hash namespaces required')
    if not roots[0].is_dir() or roots[1].exists():raise ValueError('old hash root missing or continuation root already exists')
    preflight(root,resume,artifacts)
    artifacts.mkdir(exist_ok=False)
    roots[1].mkdir(exist_ok=False)
    hashroot=roots[1]
    storage.atomic_json(root/RESUME_BASE/'hash-owner.json',dict(experiment=EXPERIMENT,hash_roots=[str(p) for p in roots],writable_hash_root=str(hashroot),purpose='new continuation namespace; original hash scratch immutable'))
    seeded=restore_seed(root,resume,plan,run)
    inventory=hash_union.inventory(roots)
    if inventory['roots'][0]['days']!=list(range(resume['seed_count'])) or inventory['roots'][1]['days']:raise ValueError('hash namespace seed population differs')
    for index,date in enumerate(resume['seed_dates']):
        for suffix in ['.json','.intent.json']:
            name=f'day-{index:04d}{suffix}'
            copied=artifacts/'hash-receipts'/name
            if sha(roots[0]/name)!=sha(copied):raise ValueError('original and preserved hash receipts differ')
        receipt=json.loads((artifacts/'hash-receipts'/f'day-{index:04d}.json').read_bytes())
        if receipt!=seeded[date]['hash_append']:raise ValueError('seed output hash receipt differs')
    old_bytes=inventory['roots'][0]['input_bytes']
    previous=run.directory/'outputs'/('day-'+resume['seed_dates'][-1]+'.json') if seeded else None
    cells=[];results=[];stopped=None
    hashdays={i:seeded[d]['independent']['source_rows'] for i,d in enumerate(resume['seed_dates'])}
    hashstreams={i:seeded[d]['independent']['source_hash_digest'] for i,d in enumerate(resume['seed_dates'])}
    for index,date in enumerate(plan['dates']):
        name='day-'+date+'.json';phase_rel=Path(BASE)/'artifacts/scratch'/date/'phase.json';audit_rel=Path(BASE)/'artifacts/checks'/(date+'.json')
        if index < resume['seed_count']:
            value=seeded[date]
        elif stopped:
            value=dict(date=date,source=dict(status='unavailable',reason=stopped),count=dict(status='unavailable',reason=stopped),independent=None)
        else:
            try:
                preflight(root,resume,artifacts)
                command=[sys.executable,'-B',str(here/'day.py'),'--root',str(root),'--plan',BASE+'plan.json','--date',date,'--phase',str(phase_rel)]
                if previous:command+=['--previous',str(previous.relative_to(root)),'--previous-sha256',sha(previous)]
                print(json.dumps(dict(date=date,phase='extract',status='starting')),flush=True)
                subprocess.run(command,check=True,cwd=root)
                phase=json.loads((root/phase_rel).read_bytes())
                if phase['source']['status']!='complete':raise ValueError('source unavailable: '+str(phase['source'].get('reason')))
                # Independent full raw reconstruction precedes hash admission or scratch release.
                (root/audit_rel).parent.mkdir(parents=True,exist_ok=True)
                preflight(root,resume,artifacts)
                subprocess.run([sys.executable,'-B',str(here/'check_day.py'),'--root',str(root),'--plan',BASE+'plan.json','--phase',str(phase_rel),'--report',str(root/audit_rel)],check=True,cwd=root)
                report=json.loads((root/audit_rel).read_bytes())
                if report['passed'] is not True or report['phase_sha256']!=sha(root/phase_rel) or report['source_rows']!=plan['expected_rows'][date] or (phase['count']['status']=='complete' and not report['count_verified']):raise ValueError('daily independent identity differs')
                combined=hash_union.inventory(roots)['bucket_bytes']
                chunks=(storage.read_blob(root/meta['path'],meta) for meta in phase['source']['transaction_hashes'])
                appended=hash_audit.append_day(hashroot,bounded_hashes(chunks,combined),index,max_total_bytes=plan['limits']['max_hash_bytes']-old_bytes)
                if appended['stream_sha256']!=report['source_hash_digest'] or appended['rows']!=report['source_rows']:raise ValueError('independent hashes differ from appended stream')
                for suffix in ['.json','.intent.json']:
                    origin=hashroot/f'day-{index:04d}{suffix}';target=artifacts/'hash-receipts'/origin.name;target.parent.mkdir(exist_ok=True)
                    with target.open('xb') as stream:stream.write(origin.read_bytes())
                hashdays[index]=report['source_rows']
                hashstreams[index]=report['source_hash_digest']
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
                preflight(root,resume,artifacts)
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
        preflight(root,resume,artifacts);audit=hash_union.audit(roots,{i:plan['expected_rows'][d] for i,d in enumerate(plan['dates'])},expected_day_stream_sha256=hashstreams)
        if audit['rows']!=plan['expected_total_rows'] or audit['input_bytes']!=plan['expected_hash_bytes']:raise ValueError('global expected population differs')
    run.write_json('hash-audit.json',audit)
    admitted=audit.get('admitted') is True
    cells.append(dict(id='global-uniqueness',status='complete' if admitted else 'unavailable',**({} if admitted else dict(reason=audit.get('reason','duplicate transactions detected')))))
    panel=[panel_row(date,value,admitted) for date,value in zip(plan['dates'],results,strict=True)]
    run.write_json('panel.json',dict(days=panel,global_uniqueness_admitted=admitted,historical_availability_verified=False,prices_or_models_opened=False))
    expected_edges=set(plan['expected_graph_unavailable']);unavailable=[r['day'] for r in panel if not r['graph_admitted']]
    run.write_json('summary.json',dict(cells=cells,dates=len(panel),source_days=sum(r['source_admitted'] for r in panel),graph_days=sum(r['graph_admitted'] for r in panel),unavailable_graph_days=unavailable,
        expected_boundary_only=set(unavailable)==expected_edges and admitted,requests=0,stopped=stopped,raw_capture_modified=False,hash_scratch_retained=[str(p) for p in roots],
        qualification='Retrospective numerical panel only. Global hash scratch retained for independent closure; no prices, labels, model or historical publication admission.'))
    return cells

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    admission=load('resume_runner_admission',HERE/'admission.py')
    if admission.EXPERIMENT!=EXPERIMENT:raise ValueError('continuation identity differs')
    admission.admit_resume(ROOT,args.source)
    guard=load('resume_runner_memory_guard',HERE/'memory_guard.py')
    guard.assert_guarded_worker(ROOT,args.source)
    def offline(event,args):
        if event.startswith(('socket.','http.client.','urllib.')):raise RuntimeError('offline continuation network prohibited')
    sys.addaudithook(offline)
    with ResearchRun.start(root=ROOT,registration=RESUME_BASE+'gates.json',experiment=EXPERIMENT,source=args.source) as run:
        run.finish(execute(ROOT,json.loads(run.read_input('plan')),run))


if __name__=='__main__':main()

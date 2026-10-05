"""One-use entry for exact closed-array preservation; ordinary storage operation."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,sys
from tradingagents.research.onchain_replication.resources import guarded_run,mem_available
from offload import ID,checked,metadata,selected_rows,verify_metadata,MAX_BODY,GIB
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent

def write(name,value):
    with (HERE/name).open('x') as stream:
        json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush()
        import os
        os.fsync(stream.fileno())

def preflight():
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    config=json.loads(metadata(HERE/'manifest.json')); digest=hashlib.sha256(metadata(HERE/'manifest.json')).hexdigest()
    review=json.loads(metadata(HERE/'RELEASE_REVIEW.json'))
    if review.get('decision')!='accepted' or review['manifest_sha256']!=digest:raise ValueError('exact accepted release missing')
    if review['worker_sha256']!=hashlib.sha256(metadata(HERE/'offload.py')).hexdigest() or review['entry_sha256']!=hashlib.sha256(metadata(__file__)).hexdigest():raise ValueError('released entry/worker changed')
    for rel in [str((HERE/n).relative_to(ROOT)) for n in ('manifest.json','RELEASE_REVIEW.json')]:
        if subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)!=(ROOT/rel).read_bytes():raise ValueError('exact config/review not committed')
    subprocess.run(['git','merge-base','--is-ancestor',config['source_commit'],head],cwd=ROOT,check=True)
    for rel,sha in {**config['source_files'],**review['evidence']}.items():
        if hashlib.sha256(metadata(ROOT/rel)).hexdigest()!=sha:raise ValueError('released body changed: '+rel)
        if hashlib.sha256(subprocess.check_output(['git','show',head+':'+rel],cwd=ROOT)).hexdigest()!=sha:raise ValueError('released body uncommitted: '+rel)
    for rel,sha in config['source_files'].items():
        if hashlib.sha256(subprocess.check_output(['git','show',config['source_commit']+':'+rel],cwd=ROOT)).hexdigest()!=sha:raise ValueError('source anchor body changed')
    from tradingagents.research.onchain_replication.environment import inventory
    if inventory(ROOT)!=json.loads(checked(ROOT,config['environment'])):raise ValueError('installed runtime inventory differs')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch!='research/onchain-paper-replication-2026-09-24':raise ValueError('source branch differs')
    if subprocess.check_output(['git','ls-remote','--exit-code','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]!=head:raise ValueError('actual remote source differs')
    for name in ('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json'):
        if (HERE/name).exists() or (HERE/name).is_symlink():raise FileExistsError('fixed namespace reserved: '+name)
    units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True)
    if units.strip():raise ValueError('another native replication job is active')
    draft=json.loads(checked(ROOT,config['draft']));rows=selected_rows(draft)
    if config['identity']!=ID or config['dictionary_sources_reviewed'] is not True:raise ValueError('scope/protection is not reviewed')
    for ref in config['protected_metadata']:checked(ROOT,ref)
    verify_metadata(ROOT,draft,[(ROOT/p).resolve() for p in config['protected_roots']])
    for row in rows:
        p=ROOT/row['path']
        if p.is_symlink() or not p.is_file() or p.with_name(p.name+'.remote.json').exists():raise ValueError('source absent/retired: '+row['path'])
    available=mem_available();free=shutil.disk_usage(ROOT).free
    if available<int(3.5*GIB) or free<10*GIB+MAX_BODY+16*1024**2:raise ValueError('full recovery scratch/native startup unavailable')
    expected={'root':str(HERE),'limits':{'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':4096,'max_depth':16,'max_scan_seconds':5}}
    if config['storage_budget']!=expected:raise ValueError('whole writable-tree policy differs')
    return config,digest,{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':ID,'manifest_sha256':digest,'head':head,'source_anchor':config['source_commit'],'mem_available_bytes':available,'free_disk_bytes':free,'files':len(rows),'source_bodies_read':False,'qualification':'Actual read-only committed release/process/resource check; byte verification is performed inside the guarded transfer worker.'}

if __name__=='__main__':
    if sys.argv[1:]:raise ValueError('unexpected arguments')
    config,digest,observation=preflight()
    write('preflight01.json',observation)
    write('launch-attempt01.json',observation)
    result=None;selected=1;fatal=None
    try:
        result=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(HERE/'offload.py'),'--worker',str(HERE/'manifest.json'),digest],cwd=ROOT,receipt_dir=HERE/'guard01',memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=int(3.5*GIB),disk_paths=[ROOT],disk_floor_bytes=10*GIB,wall_seconds=14400,storage_budget=config['storage_budget'])
        selected=0 if result['phase']=='complete' and result['cleanup_verified'] is True and result['child_exit_code']==0 else 1
    except BaseException as error:
        fatal=error
    finally:
        write('outer-exit01.json',{'identity':ID,'entry_selected_exit_code':selected,'guard_phase':None if result is None else result.get('phase'),'guard_child_exit_code':None if result is None else result.get('child_exit_code'),'cleanup_verified':None if result is None else result.get('cleanup_verified'),'fatal_type':None if fatal is None else type(fatal).__name__,'qualification':'Actual returned guard fields; null preserves unknown. Shell/tool exit is a separate actual observation. Never relaunch this identity.'})
    if fatal is not None:raise fatal
    raise SystemExit(selected)

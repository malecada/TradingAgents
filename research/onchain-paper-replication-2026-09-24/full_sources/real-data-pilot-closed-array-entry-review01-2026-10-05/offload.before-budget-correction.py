"""One fresh bounded storage worker. No automatic launcher or retry."""
import hashlib,importlib.util,json,os,shutil,stat,subprocess,sys
from pathlib import Path
ID='closed-array-pilot-offload-2026-10-05-01'
GIB=1024**3
COUNT=30
TOTAL=3021553488
MAX_BODY=387431648
DRAFT_SHA='a8ba604f921a6a20d6bdac379c84c464aed6d5fc0a6ec68a92300fce3a8dd37c'


def require(ok,message):
    if not ok:raise ValueError(message)

def metadata(path):
    p=Path(path);s=p.lstat();require(stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_size<=4*1024**2,'bounded metadata required')
    return p.read_bytes()

def checked(root,ref):
    p=root/ref['path'];require(not Path(ref['path']).is_absolute() and p.resolve().is_relative_to(root),'registered path outside root')
    b=metadata(p);require(hashlib.sha256(b).hexdigest()==ref['sha256'],'metadata binding differs: '+ref['path']);return b

def load(root,ref,name):
    checked(root,ref);spec=importlib.util.spec_from_file_location(name,root/ref['path']);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def selected_rows(draft):
    rows=draft['files'];require(len(rows)==COUNT and sum(r['bytes'] for r in rows)==TOTAL and max(r['bytes'] for r in rows)==MAX_BODY,'exact30-array selection differs')
    require(len({r['path'] for r in rows})==COUNT,'duplicate selection')
    require(all(r['path'].endswith('.npy') and '/pilot-02/' not in r['path'] and '2022-06-13' not in r['path'] for r in rows),'protected/non-array member')
    return rows

def verify_metadata(root,draft,protected):
    for path,ref in draft['metadata_pins'].items():checked(root,{'path':path,'sha256':ref['sha256']})
    for closure in draft['closures']:
        experiment=closure['experiment'];d=root/'research_runs'/experiment
        t=json.loads(metadata(d/'complete.json'));require(t['status']=='complete' and not (d/'failed.json').exists(),'original parent not exclusively complete')
        g=json.loads(metadata(root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/experiment/'guard/final.json'))
        require(g['phase']=='complete' and g['child_exit_code']==0 and g['cleanup_verified'] is True and not Path(g['cgroup']).exists() and not Path('/proc',str(g['monitor_pid'])).exists(),'original producer remains owned')
    rows=selected_rows(draft)
    for row in rows:
        p=(root/row['path']).resolve()
        require(not any(p==q or p.is_relative_to(q) for q in protected),'protected pilot/dictionary source overlap')
    # Newly active claims invalidate retirement when referencing a graph or body.
    for p in (root/'research_runs').glob('*/claim.json'):
        if p.with_name('complete.json').exists() or p.with_name('failed.json').exists():continue
        claim=json.loads(metadata(p))
        for info in claim['experiment']['inputs'].values():
            q=(root/info['path']).resolve()
            require(not any(q==(root/r['path']).resolve() or q.parent==(root/r['path']).parent or (root/r['path']).resolve().is_relative_to(q) for r in rows),'active consumer references selected graph')
    require(not subprocess.check_output(['git','ls-files','--',*[r['path'] for r in rows]],cwd=root),'tracked array retirement forbidden')

def move_rows(rows, *, before, move, publish):
    """Finite fail-stop ordering; injected only for offline control tests."""
    records=[]
    for i,row in enumerate(rows):
        try:
            publish(f'{i:02d}-attempted.json',{'path':row['path'],'status':'attempted'})
            before(row)
            record=move(row,i);records.append(record)
        except BaseException as error:
            pending=[(f'{i:02d}-failed.json',{'path':row['path'],'status':'failed','error_type':type(error).__name__})]
            pending += [(f'{j:02d}-skipped.json',{'path':later['path'],'status':'skipped','reason':'prior row failed; no retry'}) for j,later in enumerate(rows[i+1:],start=i+1)]
            for name,value in pending:
                try:publish(name,value)
                except BaseException as receipt_error:error.add_note('receipt failure '+name+': '+type(receipt_error).__name__)
            raise
    return records

def verify_source(root,here,c,config_sha):
    """Committed code ancestry plus the actual one-use entry observation."""
    anchor=c['source_commit']
    require(isinstance(anchor,str) and len(anchor)==40 and all(x in '0123456789abcdef' for x in anchor),'full source commit required')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    preflight=json.loads(metadata(here/'preflight01.json'))
    require(isinstance(preflight,dict) and preflight.get('identity')==ID and preflight.get('manifest_sha256')==config_sha and preflight.get('head')==head and preflight.get('source_anchor')==anchor,'actual preflight/source binding differs')
    require(subprocess.run(['git','merge-base','--is-ancestor',anchor,head],cwd=root,check=False).returncode==0,'source anchor is not an ancestor')
    require(isinstance(c['source_files'],dict) and c['source_files'],'source closure missing')
    for path,h in c['source_files'].items():
        checked(root,{'path':path,'sha256':h})
        obj=anchor+':'+path
        require(subprocess.check_output(['git','cat-file','-t',obj],cwd=root,text=True).strip()=='blob','source object is not a blob')
        require(int(subprocess.check_output(['git','cat-file','-s',obj],cwd=root,text=True))<=4*1024**2,'source object exceeds metadata bound')
        require(hashlib.sha256(subprocess.check_output(['git','cat-file','blob',obj],cwd=root)).hexdigest()==h,'source anchor body differs')

def worker(config_path,config_sha):
    here=Path(__file__).resolve().parent
    root=next(p for p in here.parents if (p/'tradingagents/research/onchain_replication/resources.py').is_file())
    require(here==root/'research/onchain-paper-replication-2026-09-24/storage'/ID,'fresh fixed storage directory required')
    require(Path(config_path).resolve()==here/'manifest.json','exact configuration location required')
    raw=metadata(config_path);require(hashlib.sha256(raw).hexdigest()==config_sha,'reviewed config hash differs');c=json.loads(raw)
    require(c['identity']==ID and c['remote']=='research-backups/onchain-paper-replication-2026-09-24/'+ID,'fresh exact storage identity required')
    require(c['source_files'][str(Path(__file__).relative_to(root))]==hashlib.sha256(metadata(__file__)).hexdigest(),'caller source binding differs')
    verify_source(root,here,c,config_sha)
    draft=json.loads(checked(root,c['draft']));require(c['draft']['sha256']==DRAFT_SHA,'original sealed selection differs')
    rows=selected_rows(draft)
    protected=[(root/p).resolve() for p in c['protected_roots']]
    require(c['dictionary_sources_reviewed'] is True and protected,'dictionary-source protection must be independently frozen')
    require(any('pilot-02' in str(p) and '2022-06-13' in str(p) for p in protected),'June13 protection missing')
    require(any('pilot-02' in str(p) and '2022-01-03' in str(p) for p in protected),'original dictionary graph protection missing')
    require(any('eth-paper-graph-resource-20260929-03' in str(p) for p in protected),'July25 protection missing')
    for ref in c['protected_metadata']:checked(root,ref)
    from tradingagents.research.onchain_replication.resources import assert_guarded_worker
    live=assert_guarded_worker(here/'guard01',sys.orig_argv,required_paths=[root],wall_seconds=14400,memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,disk_floor_bytes=10*GIB)
    require(live['memory_swap_max_bytes']==0 and live['reserve_bytes']==3*GIB and live['start_reserve_bytes']==int(3.5*GIB),'fixed native reserve differs')
    old=load(root,c['offload_source'],'reviewed_cold_offload')
    verify_metadata(root,draft,protected)
    require(not any(here.glob('*-attempted.json')) and not any(here.glob('*-verified.json')),'attempted namespace cannot resume')
    for row in rows:require((root/row['path']).is_file() and not (root/row['path']).with_name(Path(row['path']).name+'.remote.json').exists(),'prior retirement requires reconciliation')
    old.publish(here/'intent.json',{'identity':ID,'manifest_sha256':config_sha,'files':COUNT,'bytes':TOTAL,'retry':False})
    try:
        # Connection metadata is only consumed in the actually released worker.
        module=load(root,c['transport_source'],'reviewed_array_transport')
        transport=module.Transport(json.loads(checked(root,c['connection'])),rate=262144,maximum_payload_bytes=MAX_BODY)
        require(transport.available()>=TOTAL+GIB,'remote capacity unavailable')
        transport.mkdir(c['remote']);transport.put(here/'manifest.json',c['remote']+'/manifest.json');transport.get(c['remote']+'/manifest.json',here/'recovered-manifest.json')
        require(old.sha(here/'manifest.json')==old.sha(here/'recovered-manifest.json'),'configuration roundtrip differs')
        def before(row):
            verify_metadata(root,draft,protected)
            require(shutil.disk_usage(root).free>=10*GIB+row['bytes']+16*1024**2,'full recovery scratch unavailable')
        records=move_rows(rows,before=before,move=lambda row,i:old.offload_one(root,here,row,i,c['remote'],transport),publish=lambda n,v:old.publish(here/n,v))
        old.finish(here,{'identity':ID,'files':records,'bytes_moved':TOTAL,'no_automatic_retry':True,'restoration_required_before_future_local_array_use':True},c['remote'],transport)
    except BaseException as error:
        receipts=[('failed.json',{'identity':ID,'status':'failed','error_type':type(error).__name__,'no_automatic_retry':True})]
        receipts += [(f'{i:02d}-skipped.json',{'path':row['path'],'status':'skipped','reason':'operation failed before row attempt'}) for i,row in enumerate(rows) if not (here/f'{i:02d}-attempted.json').exists() and not (here/f'{i:02d}-skipped.json').exists()]
        for name,value in receipts:
            try:old.publish(here/name,value)
            except BaseException as later:error.add_note('failure receipt '+name+': '+type(later).__name__)
        raise

if __name__=='__main__':
    require(len(sys.argv)==4 and sys.argv[1]=='--worker','only explicitly guarded worker entry is available')
    worker(sys.argv[2],sys.argv[3])

"""Metadata-only prospective pilot ledger selection; no transfer authority."""
import hashlib,json,stat,subprocess,sys
from datetime import datetime,timedelta
from pathlib import Path
WEEKS=('2022-05-02','2022-05-09','2022-05-16','2022-05-23','2022-05-30','2022-06-06')
PREFIX='research_artifacts/onchain-paper-replication-2026-09-24/sources/'

def require(ok,why):
    if not ok:raise ValueError(why)

def sha(body):return hashlib.sha256(body).hexdigest()

def closed(claim,terminal,claim_hash,guard,owner,cells):
    require(terminal['status']=='complete' and terminal['experiment_id']==claim['experiment_id'] and terminal['claim_sha256']==claim_hash,'exclusive COMPLETE parent required')
    require(terminal['source']==claim['source'] and terminal['registration_sha256']==claim['registration_sha256'],'source/registration closure differs')
    require(terminal['cells']==cells and terminal['cell_count']==len(cells) and terminal['unavailable_count']==0 and [x['id'] for x in cells]==claim['experiment']['cells'] and all(x['status']=='complete' for x in cells),'complete exact component denominator required')
    require(guard['phase']=='complete' and guard['child_exit_code']==0 and guard['cleanup_verified'] is True and guard.get('limit_reason') is None,'producer guard incomplete')
    require(guard['owner_identity']==owner and owner['experiment']==claim['experiment_id'] and owner['source_commit']==claim['source'],'producer owner differs')

def active_reference(root,rows,inputs,producer):
    for info in inputs.values():
        q=(root/info['path']).resolve()
        require(not q.is_relative_to(producer) and not any(p==q or p.is_relative_to(q) or p.parent==q.parent for p in rows),'active consumer references ledger/producer directory')

def select(root,experiment):
    root=Path(root).resolve();dates={f'eth-paper-real-pilot-graph-{w.replace("-","")}-20261005-01':w for w in WEEKS}
    require(experiment in dates,'only six fresh pilot build identities; legacy/dictionary/June13 refused')
    week=dates[experiment];pins={}
    def read(rel,expected=None):
        p=root/rel;require(not Path(rel).is_absolute() and p.resolve().is_relative_to(root),'metadata outside root')
        s=p.lstat();require(stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_size<=4*1024**2,'bounded regular metadata required')
        body=p.read_bytes();h=sha(body);require(expected is None or h==expected,'metadata hash differs: '+str(rel))
        pins[str(rel)]={'sha256':h,'bytes':len(body)};return json.loads(body)
    run='research_runs/'+experiment+'/';base=PREFIX+experiment+'/'
    require(not (root/run/'failed.json').exists(),'FAILED parent cannot qualify')
    c=read(run+'claim.json');t=read(run+'complete.json');ch=pins[run+'claim.json']['sha256']
    require(c['experiment_id']==experiment,'claim identity differs')
    gate=read(c['registration'],c['registration_sha256']);require(gate['experiments'][experiment]==c['experiment'],'claim registration differs')
    inputs=c['experiment']['inputs']
    def inp(role):return read(inputs[role]['path'],inputs[role]['sha256'])
    job=inp('execution_job');require(job['kind']=='graphs','original graph producer required')
    plan=inp(job['payload']['plan_input']);ph=inputs[job['payload']['plan_input']]['sha256']
    require(plan['schema_version']==1 and plan['mode']=='build' and plan['asset']=='ETH' and plan['expected_weeks']==[week+'T00:00:00Z'] and plan['source_inputs']==['weekly_source'],'one full pilot week build required')
    cells=read(run+'outputs/cell-ledger.json',t['output_sha256']['cell-ledger.json'])
    index=read(run+'outputs/artifact-index.json',t['output_sha256']['artifact-index.json'])
    summary=read(run+'outputs/source-summary.json',t['output_sha256']['source-summary.json'])
    guardbase='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+experiment+'/'
    guard=read(guardbase+'guard/final.json');owner=read(guardbase+'owner.json')
    closed(c,t,ch,guard,owner,cells)
    require(not Path(guard['cgroup']).exists() and not Path('/proc',str(owner['monitor_pid'])).exists(),'producer ownership remains present')
    require([x['id'] for x in cells]==['source-000000','graph-'+week],'single source/graph denominator differs')
    def artifact(rel):return read(rel,index[rel]['sha256'])
    intent=artifact(base+'intent.json')
    require(intent['claim_sha256']==ch and intent['source_commit']==c['source'] and intent['plan_sha256']==ph and intent['cells']==c['experiment']['cells'],'producer intent differs')
    require(artifact(base+'result.json')==summary and summary['reason'] is None and summary['workspace']==base+'aggregation' and summary['plan_sha256']==ph and summary['expected_weeks']==plan['expected_weeks'],'producer result differs')
    source=inp('weekly_source');require(source['status']=='complete' and source['expected_members']==7==len(source['members']) and source['expected_rows']==sum(m['expected_rows'] for m in source['members'])==cells[0]['rows'] and cells[0]['manifest_sha256']==inputs['weekly_source']['sha256'],'source inventory/component differs')
    start=datetime.fromisoformat(week);end=(start+timedelta(days=7)).date().isoformat()+'T00:00:00Z'
    require(source['start_utc']==week+'T00:00:00Z' and source['end_utc']==end and plan['coverage']==[[source['start_utc'],end]],'full week interval differs')
    members=[]
    for i,member in enumerate(source['members']):
        require(member['start_utc']==(start+timedelta(days=i)).date().isoformat()+'T00:00:00Z' and member['end_utc']==(start+timedelta(days=i+1)).date().isoformat()+'T00:00:00Z','consecutive daily source intervals required')
        role=inputs['daily_map_'+str(i).zfill(2)];require(role['sha256']==member['sha256'] and (root/role['path']).resolve()==Path(member['path']).resolve(),'declared source map differs')
        inp('daily_map_'+str(i).zfill(2))
        members.append({k:member[k] for k in ('start_utc','end_utc','sha256','expected_rows')} | {'source_input':'weekly_source','source_manifest_sha256':inputs['weekly_source']['sha256']})
    require(len({m['sha256'] for m in members})==7,'duplicate source member')
    require(artifact(base+'source-coverage.json')=={'plan_sha256':ph,'members':members},'produced source inventory differs')
    graph=cells[1];require(artifact(base+'graph-'+week+'.json')==graph,'graph component differs')
    require(graph['manifest_path']==base+'graph-'+week+'/manifest.json','graph path differs')
    manifest=artifact(graph['manifest_path']);require(pins[graph['manifest_path']]['sha256']==graph['manifest_sha256'],'graph manifest join differs')
    coverage=artifact(graph['coverage_path']);require(coverage['schema_version']==1 and coverage['claim_sha256']==ch and coverage['plan_sha256']==ph and coverage['graph_manifest_sha256']==graph['manifest_sha256'] and coverage['week']==plan['expected_weeks'][0],'modern graph coverage join differs')
    require(pins[graph['coverage_path']]['sha256']==graph['coverage_sha256'] and coverage['members']==members,'coverage body differs')
    require(summary['graphs']=={week+'T00:00:00Z':{k:v for k,v in graph.items() if k not in ('id','status')}},'graph summary/component differs')
    require(manifest['metadata']['asset']=='ETH' and manifest['metadata']['start_utc']==week+'T00:00:00Z' and manifest['metadata']['end_utc']==end and manifest['metadata']['source_hashes']==graph['source_hashes'],'retained graph source differs')
    require(set(manifest['arrays'])=={'node_ids','node_features','edge_index','edge_features','edge_aggregates'},'original array roster differs')
    for ref in manifest['arrays'].values():
        require(Path(ref['path']).name==ref['path'],'array path must remain graph-local')
        arr=str(Path(graph['manifest_path']).parent/ref['path']);a=root/arr;st=a.lstat()
        require(index[arr]=={'bytes':ref['bytes'],'sha256':ref['sha256']} and stat.S_ISREG(st.st_mode) and not a.is_symlink() and st.st_size==ref['bytes'] and not a.with_name(a.name+'.remote.json').exists(),'downstream array not retained locally')
    rel=base+'aggregation/ledger.sqlite';require([p for p in index if p.endswith('ledger.sqlite')]==[rel],'ambiguous produced ledger')
    row={'path':rel,**index[rel]};p=root/rel;s=p.lstat()
    require(stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink==1 and s.st_size==row['bytes']>0 and len(row['sha256'])==64,'original ledger stat/hash metadata differs')
    require(not any(p.with_name(p.name+suffix).exists() for suffix in ('-wal','-shm','-journal','.remote.json')),'ledger transient/retired state')
    require(not subprocess.check_output(['git','ls-files','--',rel],cwd=root),'tracked ledger refused')
    for active in (root/'research_runs').glob('*/claim.json'):
        if active.with_name('complete.json').exists() or active.with_name('failed.json').exists():continue
        a=read(str(active.relative_to(root)));active_reference(root,[p.resolve()],a['experiment']['inputs'],(root/base).resolve())
    row['stat_identity']=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
    return {'schema_version':1,'status':'DRAFT','experiment':experiment,'files':[row],'total_bytes':s.st_size,'metadata_pins':pins,'source_commit':c['source'],'source_files':c['experiment']['source_files'],'retained_graph_manifest':graph['manifest_path'],'array_retirement':False,'ledger_body_read':False,'launch_authority':False,'required_before_release':'Independent closure and fresh exact storage config/native entry/recovery review; rerun selection before transfer.'}

if __name__=='__main__':
    require(len(sys.argv)==3,'usage: select01.py ROOT EXPERIMENT')
    print(json.dumps(select(sys.argv[1],sys.argv[2]),sort_keys=True,indent=2))

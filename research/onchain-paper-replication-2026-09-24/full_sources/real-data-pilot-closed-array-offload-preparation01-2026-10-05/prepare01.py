"""Metadata/stat-only draft for closed arrays; never hash/open/transfer array bodies."""
import hashlib,json,stat
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
IDS=('04','05','06','07','08','10')
PROTECTED_WEEK='2022-06-13T00:00:00Z'
MAX_BODY=512*1024**2

def require(value,message):
    if not value:raise ValueError(message)

def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]

def eligible(claim,terminal,claim_sha,guard,owner,week):
    require(terminal['status']=='complete','failed/unfinished parent requires separate explicit component review; not eligible here')
    require(claim['experiment_id']==terminal['experiment_id'] and terminal['claim_sha256']==claim_sha,'closed parent join differs')
    require(week!=PROTECTED_WEEK,'pilot June13 graph protected')
    require(guard['phase']=='complete' and guard['child_exit_code']==0 and guard['cleanup_verified'] is True and guard['limit_reason'] is None,'producer guard not cleanly terminal')
    require(guard['owner_identity']==owner and owner['experiment']==claim['experiment_id'],'guard/owner join differs')

def prepare():
    pins={};files=[];closures=[];excluded=[]
    def raw(p):
        require(p.suffix in ('.json','.md','.py') and p.stat().st_size<=4*1024**2,'bounded metadata required')
        b=p.read_bytes();pins[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
    def read(p):return json.loads(raw(p))
    def digest(p):return pins[str(p.relative_to(ROOT))]['sha256']
    # Only active claim metadata is inspected, never their data bodies.
    active=[]
    for p in (ROOT/'research_runs').glob('*/claim.json'):
        if not p.with_name('complete.json').exists() and not p.with_name('failed.json').exists():active.append(read(p))
    for n in IDS:
        experiment='eth-paper-graph-resource-20260930-'+n
        run=ROOT/'research_runs'/experiment;source=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/experiment
        manifests=list(source.glob('graph-*/manifest.json'));require(len(manifests)==1,'one graph manifest required');mp=manifests[0];m=read(mp)
        claim=read(run/'claim.json');terminal=read(run/'complete.json');require(not (run/'failed.json').exists(),'contradictory failed terminal')
        guardroot=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/experiment
        guard=read(guardroot/'guard/final.json');owner=read(guardroot/'owner.json')
        eligible(claim,terminal,digest(run/'claim.json'),guard,owner,m['metadata']['start_utc'])
        require(not Path(guard['cgroup']).exists() and not Path('/proc',str(guard['monitor_pid'])).exists(),'producer process/cgroup still present')
        idx=read(run/'outputs/artifact-index.json');require(digest(run/'outputs/artifact-index.json')==terminal['output_sha256']['artifact-index.json'],'terminal artifact-index hash differs')
        require(idx[str(mp.relative_to(ROOT))]==pins[str(mp.relative_to(ROOT))],'graph manifest journal differs')
        cells=read(run/'outputs/cell-ledger.json');require(digest(run/'outputs/cell-ledger.json')==terminal['output_sha256']['cell-ledger.json'],'cell journal hash differs')
        graphcell=[c for c in cells if c['id']=='graph-'+m['metadata']['start_utc'][:10]]
        require(len(graphcell)==1 and graphcell[0]['status']=='complete','graph component not complete')
        review=F/f'graph-successor-{n}-2026-09-30/CLOSURE_REVIEW.md';text=raw(review).decode();require('Accept' in text or 'accept' in text,'independent closure review missing acceptance')
        require(digest(run/'complete.json') in text,'independent closure review lacks exact terminal pin')
        for a in active:
            for info in a.get('inputs',{}).values():
                q=(ROOT/info['path']).resolve()
                require(q!=mp.resolve() and not mp.resolve().is_relative_to(q),'active claim references selected graph')
        require(set(m['arrays'])=={'node_ids','node_features','edge_index','edge_features','edge_aggregates'},'exact original five arrays required')
        for name,ref in sorted(m['arrays'].items()):
            p=mp.parent/ref['path'];require(p.parent==mp.parent and ref['path']==name+'.npy','direct array member required')
            s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink(),'exclusive regular array required')
            require(s.st_size==ref['bytes'] and 0<s.st_size<=MAX_BODY,'array extent/scratch bound differs')
            require(not p.with_name(p.name+'.remote.json').exists(),'prior offload sidecar requires reconciliation')
            key=str(p.relative_to(ROOT));require(idx[key]=={'sha256':ref['sha256'],'bytes':ref['bytes']},'array journal/manifest identity differs')
            files.append({'path':key,'bytes':s.st_size,'sha256':ref['sha256'],'stat_identity':identity(s),'allocated_bytes':s.st_blocks*512,'experiment':experiment,'graph_manifest_sha256':digest(mp)})
        closures.append({'experiment':experiment,'week':m['metadata']['start_utc'],'claim_sha256':digest(run/'claim.json'),'terminal_sha256':digest(run/'complete.json'),'artifact_index_sha256':digest(run/'outputs/artifact-index.json'),'independent_closure_review_sha256':digest(review)})
    require(len(files)==30 and len({(r['stat_identity'][0],r['stat_identity'][1]) for r in files})==30,'distinct physical target denominator')
    return {'schema_version':1,'status':'DRAFT_METADATA_ONLY_NOT_RELEASED','scope':'30 arrays from six genuinely COMPLETE modern graph jobs; June13 legacy and all failed parents excluded','files':files,'total_bytes':sum(r['bytes'] for r in files),'total_allocated_bytes':sum(r['allocated_bytes'] for r in files),'max_recovery_body_bytes':max(r['bytes'] for r in files),'closures':closures,'metadata_pins':pins,'remote':None,'new_storage_identity':None,'transfer_executed':False,'body_hashes_recomputed':False,'retirement_authorized':False,'required_before_retirement':['Fresh exact guarded transport registration and independent review','Current identity + full source hash before upload using accepted offload_one','Full fresh downloaded body hash plus roundtripped durable restoration metadata before unlink','Current active-consumer and protected-graph recheck','Preserve source/failed recovery scratch on any failure; no identity retry']}

def verify_draft(path):
    original=json.loads(Path(path).read_bytes())
    require(prepare()==original,'reviewed draft changed; fresh reconciliation required')
    return {'status':'metadata_and_stat_draft_unchanged','files':len(original['files'])}

if __name__=='__main__':
    import sys
    print(json.dumps(verify_draft(sys.argv[1]) if len(sys.argv)==2 else prepare(),sort_keys=True,indent=2))

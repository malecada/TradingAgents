"""Fixed single historical July25 ledger recovery gate; no payload reads."""
from pathlib import Path
import hashlib,json,os,stat,subprocess
ROOT=Path(__file__).resolve().parents[4]
ID='real-pilot-july25-ledger-relocation-20261006-01'
GRAPH='eth-paper-resource-pilot-20260924-02'
BACKUP='research/onchain-paper-replication-2026-09-24/storage/real-pilot-july25-ledger-preservation-20261006-02'
ORIGINAL_PARENT='research_artifacts/onchain-paper-replication-2026-09-24/pilot-02'
ORIGINAL='research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/2022-07-25/decode_graph/weekly-g_35n27n/events.sqlite'
SHA='ef3dd69023de071cdaec0780b2fbd35463f2832c816ad204aa07cf2c88594235'
SIZE=3755212800
CLAIM_SHA='05d769f6f50a65c2cf3eeed569077eb84e3871b1e7c23ad3504eed461a0565ca'
FAILED_SHA='3d318717ff7adecb0f07b9db6f3d1bd2e24e0c77705c3e07062cd4b075f8d7f2'
SOURCE='c6b568d4b1c177ab94ac37fbad462c2decc721c0'

def require(ok,message):
    if not ok:raise ValueError(message)

def metadata(root,relative,pin=None):
    q=Path(relative);p=root/q
    require(not q.is_absolute() and '..' not in q.parts and p.resolve(strict=True)==p,'canonical relative metadata required')
    s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'bounded metadata required')
    raw=p.read_bytes();require(identity(s)==identity(p.lstat()),'metadata changed')
    require(pin is None or hashlib.sha256(raw).hexdigest()==pin,'pinned metadata differs')
    return raw

def identity(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]

def current(root,row):
    q=Path(row['path']);p=root/q
    require(not q.is_absolute() and '..' not in q.parts and p.resolve(strict=True)==p,'canonical selected original/get required')
    s=p.lstat();require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and identity(s)==row['stat_identity']
        and s.st_size==row['bytes'] and stat.S_IMODE(s.st_mode)==row['mode'],'selected stat/mode/nlink differs')
    return p

def inactive():
    require(not subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True).strip(),'native process remains active')
    for claim in (ROOT/'research_runs').glob('*/claim.json'):
        if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists():continue
        body=json.loads(metadata(ROOT,str(claim.relative_to(ROOT))))
        require(body.get('program_id')!='onchain-paper-replication-2026-09-24','replication claim remains active')
        for ref in body.get('experiment',{}).get('inputs',{}).values():
            path=(ROOT/ref['path']).resolve()
            require(not path.is_relative_to(ROOT/BACKUP) and not path.is_relative_to(ROOT/ORIGINAL_PARENT),'active registered consumer references selected scope')

def recovery(root,c):
    require(c['identity']==ID and c['schema_version']==1 and c['count']==1 and len(c['rows'])==1,'fixed single July25 ledger selection required')
    row=c['rows'][0];original=row['original'];recovered=row['recovered']
    require(row['index']==0 and (original['path'],original['bytes'],original['sha256'])==(ORIGINAL,SIZE,SHA),'fixed July25 original differs')
    require(recovered['path']==BACKUP+'/00-recovered.bin' and recovered['bytes']==SIZE and recovered['sha256']==SHA and row['kept']==BACKUP+'/00-kept.json','fixed single recovered body differs')
    basis=c['recovery_basis']
    require(type(basis) is dict and set(basis)=={'outcome_review','recovered_body_proof'},'actual recovery basis required')
    def bound(ref):
        require(type(ref) is dict and set(ref)=={'path','sha256'} and type(ref['sha256']) is str and len(ref['sha256'])==64 and c['evidence'].get(ref['path'])==ref['sha256'],'actual pinned recovery ref required')
        return json.loads(metadata(root,ref['path'],ref['sha256']))
    def receipt(path):return bound({'path':path,'sha256':c['evidence'].get(path)})
    outcome=bound(basis['outcome_review'])
    require(outcome['decision']=='accepted' and outcome['identity']==Path(BACKUP).name and outcome['full_scope_byte_recovery'] is True,'actual one-body recovery acceptance required')
    joined=[BACKUP+'/'+n for n in ('selection01.json','complete.json','recovered-complete.json','guard01/final.json','outer-exit01.json','ROOT_TERMINAL01.json','00-kept.json')]
    joined += ['research_runs/'+GRAPH+'/claim.json','research_runs/'+GRAPH+'/failed.json',basis['recovered_body_proof']['path']]
    for path in joined:
        require(path in c['evidence'] and outcome['evidence'].get(path)==c['evidence'][path],'independent recovery evidence join differs')
    require(c['evidence']['research_runs/'+GRAPH+'/claim.json']==CLAIM_SHA and c['evidence']['research_runs/'+GRAPH+'/failed.json']==FAILED_SHA,'historical immutable pins differ')
    failed=receipt('research_runs/'+GRAPH+'/failed.json')
    require(failed['status']=='failed' and failed['experiment_id']==GRAPH and not (root/'research_runs'/GRAPH/'complete.json').exists(),'original failed disposition differs')
    receipt('research_runs/'+GRAPH+'/claim.json')
    complete=receipt(BACKUP+'/complete.json');selection=receipt(BACKUP+'/selection01.json');kept=receipt(row['kept'])
    require(complete==receipt(BACKUP+'/recovered-complete.json') and complete['identity']==Path(BACKUP).name and complete['count']==selection['count']==1 and complete['files']==[kept] and complete['selection']==selection and complete['bytes_preserved']==SIZE and complete['originals_retained'] is True and complete['recoveries_retained'] is True,'single-body completion differs')
    require(selection['identity']==Path(BACKUP).name and selection['files']==[original] and selection['total_bytes']==selection['max_body_bytes']==SIZE,'single original selection differs')
    require(all(kept[k]==original[k] for k in ('path','bytes','sha256','stat_identity','mode')) and all(kept[k] is True for k in ('body_roundtrip_verified','original_retained','recovered_body_retained')),'kept original join differs')
    root_exit=receipt(BACKUP+'/ROOT_TERMINAL01.json');native=receipt(BACKUP+'/guard01/final.json');outer=receipt(BACKUP+'/outer-exit01.json')
    require(root_exit['actual_root_tool_exit_code']==0 and root_exit['actual_parent_exit_code']==0 and root_exit['complete_sha256']==c['evidence'][BACKUP+'/complete.json'] and root_exit['actual_current_cgroup_absent'] is True and root_exit['selected_recorded_pids_absent'] is True,'actual backup Root zero/cleanup required')
    pids=root_exit['selected_recorded_pids']
    require(type(pids) is list and pids and all(type(p) is int and p>0 and not Path('/proc',str(p)).exists() for p in pids),'recorded backup PID remains or unknown')
    require(native['phase']=='complete' and native['child_exit_code']==0 and native['cleanup_verified'] is True and not Path(native['cgroup']).exists() and not Path('/proc',str(native['monitor_pid'])).exists() and outer['entry_selected_exit_code']==0 and not (root/BACKUP/'failed.json').exists(),'actual backup native/outer cleanup required')
    proof=bound(basis['recovered_body_proof'])
    require(proof['decision']=='pass' and proof['total_bytes']==SIZE and proof['selection_sha256']==c['evidence'][BACKUP+'/selection01.json'] and len(proof['files'])==1,'actual single-body proof scope differs')
    pr=proof['files'][0]
    require(pr['index']==0 and pr['original_path']==ORIGINAL and pr['recovered_path']==recovered['path'] and all(pr[k]==recovered[k] for k in ('bytes','sha256','mode','stat_identity')),'actual recovered byte/stat proof join differs')
    current(root,original);current(root,recovered)

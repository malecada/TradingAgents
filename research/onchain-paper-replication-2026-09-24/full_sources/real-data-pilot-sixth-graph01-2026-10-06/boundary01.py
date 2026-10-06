"""Fixed June6 predecessor boundary; compact metadata/stat only, no authority grant."""
from pathlib import Path
import hashlib,json,os,stat,sys,tempfile
ROOT=Path(__file__).resolve().parents[4]
B='research/onchain-paper-replication-2026-09-24';F=B+'/full_sources/'
NAME='eth-paper-real-pilot-graph-20220606-20261005-01'
CONT='eth-paper-real-pilot-may30-ledger-continuation-20261006-01'
OLD='eth-paper-real-pilot-graph-20220530-20261005-01'
DATA=Path('/home/malecada/Data');TARGET=DATA/'onchain-pilot-retained-ledgers'/OLD/'ledger.sqlite'
FIXED={
'relocation_receipt':{'path':F+'real-data-pilot-may30-ledger-relocation01-2026-10-06/relocation-receipt01.json','sha256':'c66ac207901db2c2eff695114fa31db22827ef01fc48bd8286abedf644237472'},
'relocation_review':{'path':F+'real-data-pilot-may30-ledger-relocation-review01-2026-10-06/relocation-final-outcome01/RELOCATION_REVIEW01.json','sha256':'03a17103e4931eb90bbf2845751127a8814243400317add0626de8b8a5f73fdf'},
'failed_recovery_review':{'path':F+'real-data-pilot-fifth-graph-failed-preservation-outcome-review01-2026-10-06/REVIEW01.json','sha256':'c6edefef9784b60ea8ad1ba331f0d12e7f6dea9add644517969f0800fc68a785'}}
FUTURE=('continuation_claim','continuation_terminal','continuation_native','continuation_root','continuation_outer','continuation_outcome_review','continuation_recovery_review','post_continuation_accounting','basis_gate')
def need(ok,message):
    if not ok:raise ValueError(message)
def read(ref):
    need(type(ref) is dict and set(ref)>={'path','sha256'} and type(ref['path']) is str and type(ref['sha256']) is str and len(ref['sha256'])==64,'actual compact dependency missing; null draft refuses')
    q=Path(ref['path']);p=ROOT/q;s=p.lstat()
    need(not q.is_absolute() and '..' not in q.parts and p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'canonical bounded dependency required')
    raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'] and p.stat()==s,'dependency changed');return json.loads(raw)
def pins_join(review,refs):
    need(type(review.get('evidence')) is dict,'independent evidence map required')
    for ref in refs:need(review['evidence'].get(ref['path'])==ref['sha256'],'independent evidence join differs')
def check(binding):
    need(binding.get('identity')==NAME and binding.get('parent') is None and binding.get('schema_version')==1,'fixed unused June6 identity required')
    refs=binding['dependencies']
    need(set(refs)==set(FIXED)|set(FUTURE),'exact predecessor dependency slots required')
    # Refuse missing future evidence before touching stores or taking a baseline.
    for key in FUTURE:need(type(refs[key]) is dict,'actual '+key+' absent; preparation not released')
    for key,ref in FIXED.items():need(refs[key]==ref,'fixed historical proof differs')
    docs={key:read(ref) for key,ref in refs.items()}
    claim=docs['continuation_claim'];terminal=docs['continuation_terminal'];native=docs['continuation_native'];root=docs['continuation_root'];outer=docs['continuation_outer'];outcome=docs['continuation_outcome_review'];recovery=docs['continuation_recovery_review']
    need(refs['continuation_claim']['path']=='research_runs/'+CONT+'/claim.json' and refs['continuation_terminal']['path']=='research_runs/'+CONT+'/complete.json','exact current continuation namespace required')
    need(claim['experiment_id']==terminal['experiment_id']==CONT and terminal['claim_sha256']==refs['continuation_claim']['sha256'] and terminal['source']==claim['source'],'current continuation source/claim differs')
    need(terminal['status']=='complete' and terminal['unavailable_count']==0 and terminal['cell_count']==1 and len(terminal['cells'])==1 and terminal['cells'][0]['id']=='graph-2022-05-30' and terminal['cells'][0]['status']=='complete','continuation is incomplete/failed/unavailable; no next release')
    need(not (ROOT/'research_runs'/CONT/'failed.json').exists(),'continuation has a failed marker')
    need(outcome['decision']=='accepted' and outcome['experiment']==CONT and outcome['source']==claim['source'] and outcome['claim_sha256']==refs['continuation_claim']['sha256'],'actual continuation outcome review required')
    pins_join(outcome,[refs[k] for k in ('continuation_claim','continuation_terminal','continuation_native','continuation_root','continuation_outer')])
    need(recovery['decision']=='accepted' and recovery['full_scope_byte_recovery'] is True,'actual continuation full BYTE recovery required')
    pins_join(recovery,[refs['continuation_terminal'],refs['continuation_outcome_review']])
    need(native['phase']=='complete' and native['child_exit_code']==0 and native['cleanup_verified'] is True and not Path(native['cgroup']).exists() and not Path('/proc',str(native['monitor_pid'])).exists(),'continuation native cleanup absent or failed')
    need(root['identity']==CONT and root['actual_root_tool_exit_code']==0 and root['original_outer_exit_code']==0 and root['guard_final_sha256']==refs['continuation_native']['sha256'] and root['cgroup_present'] is False and root['source_commit']==claim['source'] and outer['experiment']==CONT and outer['source']==claim['source'] and outer['exit_code']==0,'actual continuation Root/outer zero required')
    pids=root.get('actual_selected_recorded_pids',root.get('selected_recorded_pids'))
    need(type(pids) is list and pids and all(type(p) is int and p>0 and not Path('/proc',str(p)).exists() for p in pids),'known continuation PIDs remain/unknown')
    account=docs['post_continuation_accounting']
    need(account['decision']=='accepted' and account['identity']==NAME and account['parent'] is None and account['effective_attempt_budget']==72 and account['original_allowance_retained'] is True and account['transfer_or_refund'] is False,'accepted original June6 allowance accounting required')
    pins_join(account,[refs['continuation_terminal'],refs['basis_gate']])
    gate=docs['basis_gate'];need(CONT in gate['experiments'],'actual current continuation basis gate required')
    relocation=docs['relocation_receipt'];rr=docs['relocation_review'];old=docs['failed_recovery_review']
    need(rr['decision']=='accepted' and rr['relocation_receipt_sha256']==refs['relocation_receipt']['sha256'] and rr['complete_copy_recovery_and_retirement'] is True and relocation['original_retired'] is True and relocation['predecessor']==OLD and relocation['identity']==CONT,'accepted actual relocation required')
    proof=relocation['retirement_evidence'];pins_join(rr,[proof]);retired=read(proof);need(retired['source_retired'] is True and not os.path.lexists(ROOT/relocation['original']['path']),'original ledger retirement differs')
    need(old['decision']=='accepted' and old['full_scope_byte_recovery'] is True and old['original_failed_parent']['status']=='failed','historical failed-parent recovery required')
    for name in ('claim.json','failed.json'):
        path='research_runs/'+OLD+'/'+name
        value=read({'path':path,'sha256':old['evidence'][path]})
        need(value['experiment_id']==OLD,'historical failed identity changed')
        if name=='failed.json':need(value['status']=='failed' and value['output_sha256']=={},'old failure upgraded')
    temporary=temporary_file_basis()
    t=relocation['target'];s=TARGET.lstat()
    need(t['path']==str(TARGET) and t['device']==66307 and t['bytes']==3189231616 and t['sha256']=='e870a85f607afdfe44338f1e6f38a57c347a26a9c9385d8482ec92a2fd321bf3' and DATA.resolve()==DATA and DATA.stat().st_dev==66307 and ROOT.stat().st_dev!=66307 and TARGET.resolve()==TARGET and stat.S_ISREG(s.st_mode) and [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]==t['stat_identity'],'separately retained Data identity changed')
    need(set(p.name for p in TARGET.parent.iterdir())=={'ledger.sqlite'},'Data retained store membership differs')
    for n in (23,24):
        row=old['rows'][n];p=ROOT/row['path'];s=p.lstat();need(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==row['original_stat_identity'] and stat.S_IMODE(s.st_mode)==row['original_mode'],'failed partial array changed')
    need(__import__('shutil').disk_usage(DATA).free>=10*1024**3+64*1024**2,'retained Data floor unavailable')
    return {'continuation':CONT,'continuation_source':claim['source'],'terminal_status':'complete','effective_attempt_budget':72,'original_allowance_retained':True,'transfer_or_refund':False,'historical_failed_parent':OLD,'historical_status':'failed','retained_data':t,'projected_parquet_temporary_file':temporary,'data_floor_bytes':10*1024**3,'data_reserve_bytes':64*1024**2,'two_failed_partial_arrays_retained':True,'old_root_ledger_absent':True,'recovery_is_historical_not_current_remote_availability':True}


def temporary_file_basis():
    expected='f5f65fbf68d675c49018b79f1e3cd4b1401ad0f0edeb6225e570912a376ad6fb'
    p=Path(tempfile.__file__).resolve()
    need(os.name=='posix' and sys.platform=='linux' and sys.version_info[:3]==(3,13,13),'pinned Linux TemporaryFile runtime required')
    need(p.stat().st_size<=1024**2 and hashlib.sha256(p.read_bytes()).hexdigest()==expected,'unnamed temporary-file source changed')
    return {'path':str(p),'sha256':expected,'allocation':'O_TMPFILE or unlink-before-return; projected writes begin only after return','watch':'unnamed extents excluded from sources pathname scan; physical Root floor still covers them'}

def storage_scopes(projection):
    # Keep the second ledger: it reserves a named rollback journal beside the main ledger.
    ledger=projection['density_projected_ledger_bytes'];arrays=projection['density_projected_arrays_bytes']
    parquet=projection['largest_projected_parquet_logical_bytes'];margin=projection['scratch_margin_bytes']
    need(all(type(n) is int and n>0 for n in (ledger,arrays,parquet,margin)),'finite source projection required')
    physical=2*ledger+arrays+parquet+margin;named=2*ledger+arrays+margin
    need(physical==projection['prospective_growth_estimate_bytes'] and physical+10*1024**3==projection['prospective_startup_free_bytes'],'original full physical projection changed')
    return {'schema_version':1,'physical_root_growth_bytes':physical,'named_sources_growth_bytes':named,'unnamed_projected_parquet_bytes':parquet,'named_rollback_journal_allowance_bytes':ledger,'physical_startup_free_bytes':projection['prospective_startup_free_bytes'],'qualification':'Density estimates, not hard bounds. Named rollback reserve retained. Projected Parquet is materialized on Root as an unnamed file, not treated as read-only Data capacity. SQLite external/unnamed scratch remains covered by original whole-volume reservation/floor; no source ceiling increased.'}

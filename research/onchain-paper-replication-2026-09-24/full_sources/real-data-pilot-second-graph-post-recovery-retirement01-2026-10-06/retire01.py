"""Retire only the verified second graph ledger and its successful get scratch."""
from pathlib import Path
import fcntl, hashlib, importlib.util, json, os, subprocess, sys
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
ID='real-pilot-second-graph-ledger-retirement-20261006-01'
GRAPH='eth-paper-real-pilot-graph-20220509-20261005-01'
BACKUP=ROOT/'research/onchain-paper-replication-2026-09-24/storage/real-pilot-second-graph-preservation-20261006-01'
SELECTOR='research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-incremental-graph-retention02-2026-10-05/select01.py'
COLD='research/onchain-paper-replication-2026-09-24/storage/cold-offload-2026-09-29-03/offload.py'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as s:
        while b:=s.read(1024**2):h.update(b)
    return h.hexdigest()

def module(relative,pin,name):
    p=ROOT/relative;raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('accepted source differs')
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec)
    exec(compile(raw,str(p),'exec'),vars(m));return m

def execute(review_path,review_sha):
    if digest(review_path)!=review_sha:raise ValueError('exact independent review differs')
    review=json.loads(Path(review_path).read_bytes())
    if (review['decision']!='accepted' or review['retirement_identity']!=ID
            or review['entry_sha256']!=digest(__file__) or review['full_scope_byte_recovery'] is not True
            or review['retire_only_second_graph_ledger_and_successful_get'] is not True):
        raise ValueError('exact outcome/retirement release required')
    for relative,pin in review['evidence'].items():
        q=Path(relative);p=ROOT/q
        if q.is_absolute() or '..' in q.parts or p.resolve(strict=True)!=p or not p.is_file() or p.is_symlink() or p.stat().st_size>4*1024**2:
            raise ValueError('canonical bounded review evidence required')
        if digest(p)!=pin:raise ValueError('reviewed evidence changed: '+relative)
    final=json.loads((BACKUP/'guard01/final.json').read_bytes())
    outer=json.loads((BACKUP/'outer-exit01.json').read_bytes())
    if ((BACKUP/'failed.json').exists() or final['phase']!='complete' or final['child_exit_code']!=0
            or final['cleanup_verified'] is not True or Path(final['cgroup']).exists()
            or Path('/proc',str(final['monitor_pid'])).exists() or outer['entry_selected_exit_code']!=0):
        raise ValueError('actual preservation parent/native cleanup differs')
    if subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True).strip():
        raise ValueError('native process remains active')
    cold=module(COLD,'0d507711644d962e494e659987ba0a6d479304af7092ba15315630d0b68e1a84','retirement_cold03')
    selector=module(SELECTOR,'d9d63840c8f4510ac4e1b784ab31762d91f74c4de8d2258bdd7011823f921205','retirement_selector02')
    selection=selector.select(ROOT,GRAPH);row=selection['files'][0]
    original=ROOT/row['path'];selected=json.loads((BACKUP/'selection01.json').read_bytes())
    indices=[i for i,r in enumerate(selected['files']) if r['path']==row['path']]
    if len(indices)!=1:raise ValueError('exact preserved original missing')
    n=indices[0];kept=json.loads((BACKUP/f'{n:02d}-kept.json').read_bytes())
    if any(kept[k]!=row[k] for k in ['path','bytes','sha256','stat_identity']):raise ValueError('original recovery join differs')
    if not kept['body_roundtrip_verified'] or not kept['original_retained'] or not kept['recovered_body_retained']:raise ValueError('full successful recovery missing')
    recovered=BACKUP/f'{n:02d}-recovered.bin'
    sidecar=original.with_name(original.name+'.remote.json')
    recovered_identity=cold.identity(recovered.lstat())
    cold.validate_source(original,row)
    if recovered.is_symlink() or recovered.stat().st_nlink!=1 or recovered.stat().st_size!=row['bytes'] or digest(recovered)!=row['sha256']:
        raise ValueError('actual successful recovery changed')
    if recovered.resolve(strict=True)!=recovered:raise ValueError('noncanonical recovery')
    cold.publish(HERE/'attempt01.json',{'identity':ID,'row':row,'review_sha256':review_sha,'no_retry':True})
    removed=[]
    try:
        with os.fdopen(os.open(original,os.O_RDONLY|os.O_NOFOLLOW),'rb') as held:
            fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if cold.identity(os.fstat(held.fileno()))!=row['stat_identity']:raise ValueError('original opened identity differs')
            cold.publish(sidecar,kept)
            cold.validate_source(original,row)
            if cold.identity(os.fstat(held.fileno()))!=row['stat_identity']:raise ValueError('original drifted')
            original.unlink();removed.append(str(original.relative_to(ROOT)));cold.sync_directory(original.parent)
        if cold.identity(recovered.lstat())!=recovered_identity:raise ValueError('recovery changed before retirement')
        recovered.unlink();removed.append(str(recovered.relative_to(ROOT)));cold.sync_directory(BACKUP)
        cold.publish(HERE/'complete01.json',{'identity':ID,'removed':removed,'payload_bytes_retired':2*row['bytes'],'remote_restore':kept,'arrays_retained':True,'all_other_originals_and_recoveries_retained':True,'no_retry':True})
    except BaseException as error:
        try:
            cold.publish(HERE/'failed01.json',{'identity':ID,'removed':removed,'error_type':type(error).__name__,'no_retry':True})
        except BaseException as evidence_error:
            try:error.add_note('Retirement failure evidence unavailable: '+repr(evidence_error))
            except BaseException:pass
        raise

if __name__=='__main__':
    if len(sys.argv)!=3:raise ValueError('exact review path and SHA required')
    execute(Path(sys.argv[1]),sys.argv[2])

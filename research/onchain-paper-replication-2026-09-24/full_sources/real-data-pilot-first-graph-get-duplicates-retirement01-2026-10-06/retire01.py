"""One-use retirement of exactly five verified May2 array get duplicates; never originals."""
from pathlib import Path
import fcntl, hashlib, importlib.util, json, os, stat, subprocess, sys
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
ID='real-pilot-first-graph-get-duplicates-retirement-20261006-01'
BACKUP='research/onchain-paper-replication-2026-09-24/storage/real-pilot-first-graph-preservation-20261006-01'
COLD='research/onchain-paper-replication-2026-09-24/storage/cold-offload-2026-09-29-03/offload.py'
COLD_SHA='0d507711644d962e494e659987ba0a6d479304af7092ba15315630d0b68e1a84'
INDICES=(21,22,23,25,26)
ORIGINAL_PARENT='research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220502-20261005-01/graph-2022-05-02'


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


def selected(root,c):
    require(c['identity']==ID and c['schema_version']==1 and c['count']==5
        and c['retire_bytes']==509060512 and len(c['rows'])==5,'fixed selection differs')
    require(tuple(r['index'] for r in c['rows'])==INDICES,'fixed five indices differ')
    originals=[];gets=[]
    for row in c['rows']:
        original,get=row['original'],row['recovered'];n=row['index']
        require(Path(original['path']).parent==Path(ORIGINAL_PARENT) and original['path'].endswith('.npy')
            and get['path']==BACKUP+f'/{n:02d}-recovered.bin','only exact array gets allowed')
        require(get['sha256']==original['sha256'] and get['bytes']==original['bytes'],'original/get content join differs')
        require(row['kept']==BACKUP+f'/{n:02d}-kept.json' and row['kept'] in c['evidence'],'kept evidence missing')
        kept=json.loads(metadata(root,row['kept'],c['evidence'][row['kept']]))
        require(all(kept[k]==original[k] for k in ('path','bytes','sha256','stat_identity','mode'))
            and all(kept[k] is True for k in ('body_roundtrip_verified','original_retained','recovered_body_retained')),'full recovery original join differs')
        originals.append(current(root,original));gets.append(current(root,get))
    require(len(set(originals))==len(set(gets))==5 and not set(originals)&set(gets),'duplicate/overlap selection')
    require(sum(r['recovered']['bytes'] for r in c['rows'])==c['retire_bytes'],'retirement total differs')
    return originals,gets


def inactive():
    require(not subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True).strip(),'native process remains active')
    for claim in (ROOT/'research_runs').glob('*/claim.json'):
        if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists():continue
        body=json.loads(metadata(ROOT,str(claim.relative_to(ROOT))))
        require(body.get('program_id')!='onchain-paper-replication-2026-09-24','replication claim remains active')
        for ref in body.get('experiment',{}).get('inputs',{}).values():
            path=(ROOT/ref['path']).resolve()
            require(not path.is_relative_to(ROOT/BACKUP) and not path.is_relative_to(ROOT/ORIGINAL_PARENT),'active registered consumer references selected scope')


def execute(review_path,review_sha):
    review_path=Path(review_path).resolve(strict=True)
    review=json.loads(metadata(ROOT,str(review_path.relative_to(ROOT)),review_sha))
    require(review['decision']=='accepted' and review['retirement_identity']==ID
        and review['entry_sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        and review['retire_only_five_verified_array_get_duplicates'] is True,'exact independent release required')
    ref=review['selection'];c=json.loads(metadata(ROOT,ref['path'],ref['sha256']))
    require(c['status']=='FROZEN_FOR_REVIEW','draft selection cannot execute')
    for relative,pin in c['evidence'].items():metadata(ROOT,relative,pin)
    for relative,pin in review['evidence'].items():metadata(ROOT,relative,pin)
    for relative in c['removed_ledger_paths']:require(not os.path.lexists(ROOT/relative),'retired ledger reappeared')
    final=json.loads(metadata(ROOT,BACKUP+'/guard01/final.json'))
    outer=json.loads(metadata(ROOT,BACKUP+'/outer-exit01.json'))
    require(final['phase']=='complete' and final['child_exit_code']==0 and final['cleanup_verified'] is True
        and not Path(final['cgroup']).exists() and not Path('/proc',str(final['monitor_pid'])).exists()
        and outer['entry_selected_exit_code']==0 and not (ROOT/BACKUP/'failed.json').exists(),'original preservation cleanup differs')
    for name in ('attempt01.json','complete01.json','failed01.json'):require(not os.path.lexists(HERE/name),'one-use identity already reserved')
    inactive();originals,gets=selected(ROOT,c)
    raw=metadata(ROOT,COLD,COLD_SHA);spec=importlib.util.spec_from_file_location('retirement_cold03',ROOT/COLD)
    cold=importlib.util.module_from_spec(spec);exec(compile(raw,str(ROOT/COLD),'exec'),vars(cold))
    cold.publish(HERE/'attempt01.json',{'identity':ID,'selection':ref,'review_sha256':review_sha,'no_retry':True})
    removed=[];attempted=[];held=[];error=None
    try:
        for row in c['rows']:
            for item in (row['original'],row['recovered']):
                path=current(ROOT,item);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW);held.append(fd)
                fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                require(identity(os.fstat(fd))==item['stat_identity'],'opened descriptor differs')
        inactive();selected(ROOT,c)
        for n,row in enumerate(c['rows']):
            current(ROOT,row['original']);path=current(ROOT,row['recovered'])
            require(identity(os.fstat(held[2*n]))==row['original']['stat_identity']
                and identity(os.fstat(held[2*n+1]))==row['recovered']['stat_identity'],'held source/get drifted')
            attempted.append(row['recovered']['path'])
            path.unlink();removed.append(row['recovered']['path']);cold.sync_directory(path.parent)
        for row in c['rows']:current(ROOT,row['original'])
    except BaseException as caught:error=caught
    finally:
        for fd in reversed(held):
            try:os.close(fd)
            except BaseException as close_error:
                if error is None:error=close_error
                else:error.add_note('Additional descriptor close failure: '+repr(close_error))
    if error is not None:
        try:cold.publish(HERE/'failed01.json',{'identity':ID,'unlink_attempted':attempted,'removed':removed,'error_type':type(error).__name__,'ambiguous_attempts':[p for p in attempted if p not in removed],'no_retry':True})
        except BaseException as evidence_error:error.add_note('Retirement failure evidence unavailable: '+repr(evidence_error))
        raise error
    try:
        cold.publish(HERE/'complete01.json',{'identity':ID,'removed':removed,'payload_bytes_retired':c['retire_bytes'],'original_arrays_retained':True,'all_other_recoveries_retained':True,'remote_disposition':c['remote_disposition'],'no_retry':True})
    except BaseException as completion_error:
        try:cold.publish(HERE/'failed01.json',{'identity':ID,'removed':removed,'error_type':type(completion_error).__name__,'no_retry':True})
        except BaseException as evidence_error:completion_error.add_note('Retirement failure evidence unavailable: '+repr(evidence_error))
        raise


if __name__=='__main__':
    require(len(sys.argv)==3,'exact independent release path and SHA required')
    execute(sys.argv[1],sys.argv[2])
